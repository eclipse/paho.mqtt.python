# Copyright (c) 2012-2014 Roger Light <roger@atchoo.org>
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# and Eclipse Distribution License v1.0 which accompany this distribution.
#
# The Eclipse Public License is available at
#    http://www.eclipse.org/legal/epl-v10.html
# and the Eclipse Distribution License is available at
#   http://www.eclipse.org/org/documents/edl-v10.php.
#
# Contributors:
#    Roger Light - initial API and implementation

"""
This is an MQTT v3.1 client module. MQTT is a lightweight pub/sub messaging
protocol that is easy to implement and suitable for low powered devices.
"""
import collections
import errno
import platform
import random
import select
import socket

try:
    import ssl
except ImportError:
    ssl = None

import struct
import sys
import threading

import time
import uuid
import base64
import string
import hashlib
import logging

try:
    # Use monotonic clock if available
    time_func = time.monotonic
except AttributeError:
    time_func = time.time

try:
    import dns.resolver
except ImportError:
    HAVE_DNS = False
else:
    HAVE_DNS = True

from .matcher import MQTTMatcher

if platform.system() == 'Windows':
    EAGAIN = errno.WSAEWOULDBLOCK
else:
    EAGAIN = errno.EAGAIN

MQTTv31 = 3
MQTTv311 = 4

if sys.version_info[0] >= 3:
    # define some alias for python2 compatibility
    unicode = str
    basestring = str

# Message types
CONNECT = 0x10
CONNACK = 0x20
PUBLISH = 0x30
PUBACK = 0x40
PUBREC = 0x50
PUBREL = 0x60
PUBCOMP = 0x70
SUBSCRIBE = 0x80
SUBACK = 0x90
UNSUBSCRIBE = 0xA0
UNSUBACK = 0xB0
PINGREQ = 0xC0
PINGRESP = 0xD0
DISCONNECT = 0xE0

# Log levels
MQTT_LOG_INFO = 0x01
MQTT_LOG_NOTICE = 0x02
MQTT_LOG_WARNING = 0x04
MQTT_LOG_ERR = 0x08
MQTT_LOG_DEBUG = 0x10
LOGGING_LEVEL = {
    MQTT_LOG_DEBUG: logging.DEBUG,
    MQTT_LOG_INFO: logging.INFO,
    MQTT_LOG_NOTICE: logging.INFO,  # This has no direct equivalent level
    MQTT_LOG_WARNING: logging.WARNING,
    MQTT_LOG_ERR: logging.ERROR,
}

# CONNACK codes
CONNACK_ACCEPTED = 0
CONNACK_REFUSED_PROTOCOL_VERSION = 1
CONNACK_REFUSED_IDENTIFIER_REJECTED = 2
CONNACK_REFUSED_SERVER_UNAVAILABLE = 3
CONNACK_REFUSED_BAD_USERNAME_PASSWORD = 4
CONNACK_REFUSED_NOT_AUTHORIZED = 5

# Connection state
mqtt_cs_new = 0
mqtt_cs_connected = 1
mqtt_cs_disconnecting = 2
mqtt_cs_connect_async = 3

# Message state
mqtt_ms_invalid = 0
mqtt_ms_publish = 1
mqtt_ms_wait_for_puback = 2
mqtt_ms_wait_for_pubrec = 3
mqtt_ms_resend_pubrel = 4
mqtt_ms_wait_for_pubrel = 5
mqtt_ms_resend_pubcomp = 6
mqtt_ms_wait_for_pubcomp = 7
mqtt_ms_send_pubrec = 8
mqtt_ms_queued = 9

# Error values
MQTT_ERR_AGAIN = -1
MQTT_ERR_SUCCESS = 0
MQTT_ERR_NOMEM = 1
MQTT_ERR_PROTOCOL = 2
MQTT_ERR_INVAL = 3
MQTT_ERR_NO_CONN = 4
MQTT_ERR_CONN_REFUSED = 5
MQTT_ERR_NOT_FOUND = 6
MQTT_ERR_CONN_LOST = 7
MQTT_ERR_TLS = 8
MQTT_ERR_PAYLOAD_SIZE = 9
MQTT_ERR_NOT_SUPPORTED = 10
MQTT_ERR_AUTH = 11
MQTT_ERR_ACL_DENIED = 12
MQTT_ERR_UNKNOWN = 13
MQTT_ERR_ERRNO = 14
MQTT_ERR_QUEUE_SIZE = 15

sockpair_data = b"0"


class WebsocketConnectionError(ValueError):
    pass


def error_string(mqtt_errno):
    """Return the error string associated with an mqtt error number."""
    if mqtt_errno == MQTT_ERR_SUCCESS:
        return "No error."
    elif mqtt_errno == MQTT_ERR_NOMEM:
        return "Out of memory."
    elif mqtt_errno == MQTT_ERR_PROTOCOL:
        return "A network protocol error occurred when communicating with the broker."
    elif mqtt_errno == MQTT_ERR_INVAL:
        return "Invalid function arguments provided."
    elif mqtt_errno == MQTT_ERR_NO_CONN:
        return "The client is not currently connected."
    elif mqtt_errno == MQTT_ERR_CONN_REFUSED:
        return "The connection was refused."
    elif mqtt_errno == MQTT_ERR_NOT_FOUND:
        return "Message not found (internal error)."
    elif mqtt_errno == MQTT_ERR_CONN_LOST:
        return "The connection was lost."
    elif mqtt_errno == MQTT_ERR_TLS:
        return "A TLS error occurred."
    elif mqtt_errno == MQTT_ERR_PAYLOAD_SIZE:
        return "Payload too large."
    elif mqtt_errno == MQTT_ERR_NOT_SUPPORTED:
        return "This feature is not supported."
    elif mqtt_errno == MQTT_ERR_AUTH:
        return "Authorisation failed."
    elif mqtt_errno == MQTT_ERR_ACL_DENIED:
        return "Access denied by ACL."
    elif mqtt_errno == MQTT_ERR_UNKNOWN:
        return "Unknown error."
    elif mqtt_errno == MQTT_ERR_ERRNO:
        return "Error defined by errno."
    else:
        return "Unknown error."


def connack_string(connack_code):
    """Return the string associated with a CONNACK result."""
    if connack_code == CONNACK_ACCEPTED:
        return "Connection Accepted."
    elif connack_code == CONNACK_REFUSED_PROTOCOL_VERSION:
        return "Connection Refused: unacceptable protocol version."
    elif connack_code == CONNACK_REFUSED_IDENTIFIER_REJECTED:
        return "Connection Refused: identifier rejected."
    elif connack_code == CONNACK_REFUSED_SERVER_UNAVAILABLE:
        return "Connection Refused: broker unavailable."
    elif connack_code == CONNACK_REFUSED_BAD_USERNAME_PASSWORD:
        return "Connection Refused: bad user name or password."
    elif connack_code == CONNACK_REFUSED_NOT_AUTHORIZED:
        return "Connection Refused: not authorised."
    else:
        return "Connection Refused: unknown reason."


def base62(num, base=string.digits + string.ascii_letters, padding=1):
    """Convert a number to base-62 representation."""
    assert num >= 0
    digits = []
    while num:
        num, rest = divmod(num, 62)
        digits.append(base[rest])
    digits.extend(base[0] for _ in range(len(digits), padding))
    return ''.join(reversed(digits))


def topic_matches_sub(sub, topic):
    """Check whether a topic matches a subscription.

    For example:

    foo/bar would match the subscription foo/# or +/bar
    non/matching would not match the subscription non/+/+
    """
    matcher = MQTTMatcher()
    matcher[sub] = True
    try:
        next(matcher.iter_match(topic))
        return True
    except StopIteration:
        return False


def _socketpair_compat():
    """TCP/IP socketpair including Windows support"""
    listensock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_IP)
    listensock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listensock.bind(("127.0.0.1", 0))
    listensock.listen(1)

    iface, port = listensock.getsockname()
    sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_IP)
    sock1.setblocking(0)
    try:
        sock1.connect(("127.0.0.1", port))
    except socket.error as err:
        if err.errno != errno.EINPROGRESS and err.errno != errno.EWOULDBLOCK and err.errno != EAGAIN:
            raise
    sock2, address = listensock.accept()
    sock2.setblocking(0)
    listensock.close()
    return (sock1, sock2)


class MQTTMessageInfo(object):
    """This is a class returned from Client.publish() and can be used to find
    out the mid of the message that was published, and to determine whether the
    message has been published, and/or wait until it is published.
    """

    __slots__ = 'mid', '_published', '_condition', 'rc', '_iterpos'

    def __init__(self, mid):
        self.mid = mid
        self._published = False
        self._condition = threading.Condition()
        self.rc = 0
        self._iterpos = 0

    def __str__(self):
        return str((self.rc, self.mid))

    def __iter__(self):
        self._iterpos = 0
        return self

    def __next__(self):
        return self.next()

    def next(self):
        if self._iterpos == 0:
            self._iterpos = 1
            return self.rc
        elif self._iterpos == 1:
            self._iterpos = 2
            return self.mid
        else:
            raise StopIteration

    def __getitem__(self, index):
        if index == 0:
            return self.rc
        elif index == 1:
            return self.mid
        else:
            raise IndexError("index out of range")

    def _set_as_published(self):
        with self._condition:
            self._published = True
            self._condition.notify()

    def wait_for_publish(self):
        """Block until the message associated with this object is published."""
        if self.rc == MQTT_ERR_QUEUE_SIZE:
            raise ValueError('Message is not queued due to ERR_QUEUE_SIZE')
        with self._condition:
            while not self._published:
                self._condition.wait()

    def is_published(self):
        """Returns True if the message associated with this object has been
        published, else returns False."""
        if self.rc == MQTT_ERR_QUEUE_SIZE:
            raise ValueError('Message is not queued due to ERR_QUEUE_SIZE')
        with self._condition:
            return self._published


class MQTTMessage(object):
    """ This is a class that describes an incoming or outgoing message. It is
    passed to the on_message callback as the message parameter.

    Members:

    topic : String/bytes. topic that the message was published on.
    payload : String/bytes the message payload.
    qos : Integer. The message Quality of Service 0, 1 or 2.
    retain : Boolean. If true, the message is a retained message and not fresh.
    mid : Integer. The message id.

    On Python 3, topic must be bytes.
    """

    __slots__ = 'timestamp', 'state', 'dup', 'mid', '_topic', 'payload', 'qos', 'retain', 'info'

    def __init__(self, mid=0, topic=b""):
        self.timestamp = 0
        self.state = mqtt_ms_invalid
        self.dup = False
        self.mid = mid
        self._topic = topic
        self.payload = b""
        self.qos = 0
        self.retain = False
        self.info = MQTTMessageInfo(mid)

    def __eq__(self, other):
        """Override the default Equals behavior"""
        if isinstance(other, self.__class__):
            return self.mid == other.mid
        return False

    def __ne__(self, other):
        """Define a non-equality test"""
        return not self.__eq__(other)

    @property
    def topic(self):
        return self._topic.decode('utf-8')

    @topic.setter
    def topic(self, value):
        self._topic = value


class Client(object):
    """MQTT version 3.1/3.1.1 client class.

    This is the main class for use communicating with an MQTT broker.

    General usage flow:

    * Use connect()/connect_async() to connect to a broker
    * Call loop() frequently to maintain network traffic flow with the broker
    * Or use loop_start() to set a thread running to call loop() for you.
    * Or use loop_forever() to handle calling loop() for you in a blocking
    * function.
    * Use subscribe() to subscribe to a topic and receive messages
    * Use publish() to send messages
    * Use disconnect() to disconnect from the broker

    Data returned from the broker is made available with the use of callback
    functions as described below.

    Callbacks
    =========

    A number of callback functions are available to receive data back from the
    broker. To use a callback, define a function and then assign it to the
    client:

    def on_connect(client, userdata, flags, rc):
        print("Connection returned " + str(rc))

    client.on_connect = on_connect

    All of the callbacks as described below have a "client" and an "userdata"
    argument. "client" is the Client instance that is calling the callback.
    "userdata" is user data of any type and can be set when creating a new client
    instance or with user_data_set(userdata).

    The callbacks:

    on_connect(client, userdata, flags, rc): called when the broker responds to our connection
      request.
      flags is a dict that contains response flags from the broker:
        flags['session present'] - this flag is useful for clients that are
            using clean session set to 0 only. If a client with clean
            session=0, that reconnects to a broker that it has previously
            connected to, this flag indicates whether the broker still has the
            session information for the client. If 1, the session still exists.
      The value of rc determines success or not:
        0: Connection successful
        1: Connection refused - incorrect protocol version
        2: Connection refused - invalid client identifier
        3: Connection refused - server unavailable
        4: Connection refused - bad username or password
        5: Connection refused - not authorised
        6-255: Currently unused.

    on_disconnect(client, userdata, rc): called when the client disconnects from the broker.
      The rc parameter indicates the disconnection state. If MQTT_ERR_SUCCESS
      (0), the callback was called in response to a disconnect() call. If any
      other value the disconnection was unexpected, such as might be caused by
      a network error.

    on_message(client, userdata, message): called when a message has been received on a
      topic that the client subscribes to. The message variable is a
      MQTTMessage that describes all of the message parameters.

    on_publish(client, userdata, mid): called when a message that was to be sent using the
      publish() call has completed transmission to the broker. For messages
      with QoS levels 1 and 2, this means that the appropriate handshakes have
      completed. For QoS 0, this simply means that the message has left the
      client. The mid variable matches the mid variable returned from the
      corresponding publish() call, to allow outgoing messages to be tracked.
      This callback is important because even if the publish() call returns
      success, it does not always mean that the message has been sent.

    on_subscribe(client, userdata, mid, granted_qos): called when the broker responds to a
      subscribe request. The mid variable matches the mid variable returned
      from the corresponding subscribe() call. The granted_qos variable is a
      list of integers that give the QoS level the broker has granted for each
      of the different subscription requests.

    on_unsubscribe(client, userdata, mid): called when the broker responds to an unsubscribe
      request. The mid variable matches the mid variable returned from the
      corresponding unsubscribe() call.

    on_log(client, userdata, level, buf): called when the client has log information. Define
      to allow debugging. The level variable gives the severity of the message
      and will be one of MQTT_LOG_INFO, MQTT_LOG_NOTICE, MQTT_LOG_WARNING,
      MQTT_LOG_ERR, and MQTT_LOG_DEBUG. The message itself is in buf.

    """

    def __init__(self, client_id="", clean_session=True, userdata=None,
            protocol=MQTTv311, transport="tcp"):
        """client_id is the unique client id string used when connecting to the
        broker. If client_id is zero length or None, then the behaviour is
        defined by which protocol version is in use. If using MQTT v3.1.1, then
        a zero length client id will be sent to the broker and the broker will
        generate a random for the client. If using MQTT v3.1 then an id will be
        randomly generated. In both cases, clean_session must be True. If this
        is not the case a ValueError will be raised.

        clean_session is a boolean that determines the client type. If True,
        the broker will remove all information about this client when it
        disconnects. If False, the client is a persistent client and
        subscription information and queued messages will be retained when the
        client disconnects.
        Note that a client will never discard its own outgoing messages on
        disconnect. Calling connect() or reconnect() will cause the messages to
        be resent.  Use reinitialise() to reset a client to its original state.

        userdata is user defined data of any type that is passed as the "userdata"
        parameter to callbacks. It may be updated at a later point with the
        user_data_set() function.

        The protocol argument allows explicit setting of the MQTT version to
        use for this client. Can be paho.mqtt.client.MQTTv311 (v3.1.1) or
        paho.mqtt.client.MQTTv31 (v3.1), with the default being v3.1.1 If the
        broker reports that the client connected with an invalid protocol
        version, the client will automatically attempt to reconnect using v3.1
        instead.

        Set transport to "websockets" to use WebSockets as the transport
        mechanism. Set to "tcp" to use raw TCP, which is the default.
        """
        if not clean_session and (client_id == "" or client_id is None):
            raise ValueError('A client id must be provided if clean session is False.')

        self._transport = transport
        self._protocol = protocol
        self._userdata = userdata
        self._sock = None
        self._sockpairR, self._sockpairW = _socketpair_compat()
        self._keepalive = 60
        self._message_retry = 20
        self._last_retry_check = 0
        self._clean_session = clean_session

        # [MQTT-3.1.3-4] Client Id must be UTF-8 encoded string.
        if client_id == "" or client_id is None:
            if protocol == MQTTv31:
                self._client_id = base62(uuid.uuid4().int, padding=22)
            else:
                self._client_id = b""
        else:
            self._client_id = client_id
        if isinstance(self._client_id, unicode):
            self._client_id = self._client_id.encode('utf-8')

        self._username = None
        self._password = None
        self._in_packet = {
            "command": 0,
            "have_remaining": 0,
            "remaining_count": [],
            "remaining_mult": 1,
            "remaining_length": 0,
            "packet": b"",
            "to_process": 0,
            "pos": 0}
        self._out_packet = collections.deque()
        self._current_out_packet = None
        self._last_msg_in = time_func()
        self._last_msg_out = time_func()
        self._reconnect_min_delay = 1
        self._reconnect_max_delay = 120
        self._reconnect_delay = None
        self._ping_t = 0
        self._last_mid = 0
        self._state = mqtt_cs_new
        self._out_messages = []
        self._in_messages = []
        self._max_inflight_messages = 20
        self._inflight_messages = 0
        self._max_queued_messages = 0
        self._will = False
        self._will_topic = b""
        self._will_payload = b""
        self._will_qos = 0
        self._will_retain = False
        self._on_message_filtered = MQTTMatcher()
        self._host = ""
        self._port = 1883
        self._bind_address = ""
        self._in_callback = threading.Lock()
        self._callback_mutex = threading.RLock()
        self._out_packet_mutex = threading.Lock()
        self._current_out_packet_mutex = threading.RLock()
        self._msgtime_mutex = threading.Lock()
        self._out_message_mutex = threading.RLock()
        self._in_message_mutex = threading.Lock()
        self._reconnect_delay_mutex = threading.Lock()
        self._thread = None
        self._thread_terminate = False
        self._ssl = False
        self._ssl_context = None
        self._tls_insecure = False  # Only used when SSL context does not have check_hostname attribute
        self._logger = None
        # No default callbacks
        self._on_log = None
        self._on_connect = None
        self._on_subscribe = None
        self._on_message = None
        self._on_publish = None
        self._on_unsubscribe = None
        self._on_disconnect = None
        self._websocket_path = "/mqtt"
        self._websocket_extra_headers = None

    def __del__(self):
        pass

    def reinitialise(self, client_id="", clean_session=True, userdata=None):
        if self._sock:
            self._sock.close()
            self._sock = None
        if self._sockpairR:
            self._sockpairR.close()
            self._sockpairR = None
        if self._sockpairW:
            self._sockpairW.close()
            self._sockpairW = None

        self.__init__(client_id, clean_session, userdata)

    def ws_set_options(self, path="/mqtt", headers=None):
        """ Set the path and headers for a websocket connection

        path is a string starting with / which should be the endpoint of the
        mqtt connection on the remote server

        headers can be either a dict or a callable object. If it is a dict then
        the extra items in the dict are added to the websocket headers. If it is
        a callable, then the default websocket headers are passed into this
        function and the result is used as the new headers.
        """
        self._websocket_path = path

        if headers is not None:
            if isinstance(headers, dict) or callable(headers):
                self._websocket_extra_headers = headers
            else:
                raise ValueError("'headers' option to ws_set_options has to be either a dictionary or callable")

    def tls_set_context(self, context=None):
        """Configure network encryption and authentication context. Enables SSL/TLS support.

        context : an ssl.SSLContext object. By default this is given by
        `ssl.create_default_context()`, if available.

        Must be called before connect() or connect_async()."""
        if self._ssl_context is not None:
            raise ValueError('SSL/TLS has already been configured.')

        # Assume that have SSL support, or at least that context input behaves like ssl.SSLContext
        # in current versions of Python

        if context is None:
            if hasattr(ssl, 'create_default_context'):
                context = ssl.create_default_context()
            else:
                raise ValueError('SSL/TLS context must be specified')

        self._ssl = True
        self._ssl_context = context

        # Ensure _tls_insecure is consistent with check_hostname attribute
        if hasattr(context, 'check_hostname'):
            self._tls_insecure = not context.check_hostname

    def tls_set(self, ca_certs=None, certfile=None, keyfile=None, cert_reqs=None, tls_version=None, ciphers=None):
        """Configure network encryption and authentication options. Enables SSL/TLS support.

        ca_certs : a string path to the Certificate Authority certificate files
        that are to be treated as trusted by this client. If this is the only
        option given then the client will operate in a similar manner to a web
        browser. That is to say it will require the broker to have a
        certificate signed by the Certificate Authorities in ca_certs and will
        communicate using TLS v1, but will not attempt any form of
        authentication. This provides basic network encryption but may not be
        sufficient depending on how the broker is configured.
        By default, on Python 2.7.9+ or 3.4+, the default certification
        authority of the system is used. On older Python version this parameter
        is mandatory.

        certfile and keyfile are strings pointing to the PEM encoded client
        certificate and private keys respectively. If these arguments are not
        None then they will be used as client information for TLS based
        authentication.  Support for this feature is broker dependent. Note
        that if either of these files in encrypted and needs a password to
        decrypt it, Python will ask for the password at the command line. It is
        not currently possible to define a callback to provide the password.

        cert_reqs allows the certificate requirements that the client imposes
        on the broker to be changed. By default this is ssl.CERT_REQUIRED,
        which means that the broker must provide a certificate. See the ssl
        pydoc for more information on this parameter.

        tls_version allows the version of the SSL/TLS protocol used to be
        specified. By default TLS v1 is used. Previous versions (all versions
        beginning with SSL) are possible but not recommended due to possible
        security problems.

        ciphers is a string specifying which encryption ciphers are allowable
        for this connection, or None to use the defaults. See the ssl pydoc for
        more information.

        Must be called before connect() or connect_async()."""
        if ssl is None:
            raise ValueError('This platform has no SSL/TLS.')

        if not hasattr(ssl, 'SSLContext'):
            # Require Python version that has SSL context support in standard library
            raise ValueError('Python 2.7.9 and 3.2 are the minimum supported versions for TLS.')

        if ca_certs is None and not hasattr(ssl.SSLContext, 'load_default_certs'):
            raise ValueError('ca_certs must not be None.')

        # Create SSLContext object
        if tls_version is None:
            tls_version = ssl.PROTOCOL_TLSv1
            # If the python version supports it, use highest TLS version automatically
            if hasattr(ssl, "PROTOCOL_TLS"):
                tls_version = ssl.PROTOCOL_TLS
        context = ssl.SSLContext(tls_version)

        # Configure context
        if certfile is not None:
            context.load_cert_chain(certfile, keyfile)

        if cert_reqs == ssl.CERT_NONE and hasattr(context, 'check_hostname'):
            context.check_hostname = False

        context.verify_mode = ssl.CERT_REQUIRED if cert_reqs is None else cert_reqs

        if ca_certs is not None:
            context.load_verify_locations(ca_certs)
        else:
            context.load_default_certs()

        if ciphers is not None:
            context.set_ciphers(ciphers)

        self.tls_set_context(context)

        if cert_reqs != ssl.CERT_NONE:
            # Default to secure, sets context.check_hostname attribute
            # if available
            self.tls_insecure_set(False)
        else:
            # But with ssl.CERT_NONE, we can not check_hostname
            self.tls_insecure_set(True)

    def tls_insecure_set(self, value):
        """Configure verification of the server hostname in the server certificate.

        If value is set to true, it is impossible to guarantee that the host
        you are connecting to is not impersonating your server. This can be
        useful in initial server testing, but makes it possible for a malicious
        third party to impersonate your server through DNS spoofing, for
        example.

        Do not use this function in a real system. Setting value to true means
        there is no point using encryption.

        Must be called before connect() and after either tls_set() or
        tls_set_context()."""

        if self._ssl_context is None:
            raise ValueError('Must configure SSL context before using tls_insecure_set.')

        self._tls_insecure = value

        # Ensure check_hostname is consistent with _tls_insecure attribute
        if hasattr(self._ssl_context, 'check_hostname'):
            # Rely on SSLContext to check host name
            # If verify_mode is CERT_NONE then the host name will never be checked
            self._ssl_context.check_hostname = not value

    def enable_logger(self, logger=None):
        if not logger:
            if self._logger:
                # Do not replace existing logger
                return
            logger = logging.getLogger(__name__)
        self._logger = logger

    def disable_logger(self):
        self._logger = None

    def connect(self, host, port=1883, keepalive=60, bind_address=""):
        """Connect to a remote broker.

        host is the hostname or IP address of the remote broker.
        port is the network port of the server host to connect to. Defaults to
        1883. Note that the default port for MQTT over SSL/TLS is 8883 so if you
        are using tls_set() the port may need providing.
        keepalive: Maximum period in seconds between communications with the
        broker. If no other messages are being exchanged, this controls the
        rate at which the client will send ping messages to the broker.
        """
        self.connect_async(host, port, keepalive, bind_address)
        return self.reconnect()

    def connect_srv(self, domain=None, keepalive=60, bind_address=""):
        """Connect to a remote broker.

        domain is the DNS domain to search for SRV records; if None,
        try to determine local domain name.
        keepalive and bind_address are as for connect()
        """

        if HAVE_DNS is False:
            raise ValueError('No DNS resolver library found, try "pip install dnspython" or "pip3 install dnspython3".')

        if domain is None:
            domain = socket.getfqdn()
            domain = domain[domain.find('.') + 1:]

        try:
            rr = '_mqtt._tcp.%s' % domain
            if self._ssl:
                # IANA specifies secure-mqtt (not mqtts) for port 8883
                rr = '_secure-mqtt._tcp.%s' % domain
            answers = []
            for answer in dns.resolver.query(rr, dns.rdatatype.SRV):
                addr = answer.target.to_text()[:-1]
                answers.append((addr, answer.port, answer.priority, answer.weight))
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            raise ValueError("No answer/NXDOMAIN for SRV in %s" % (domain))

        # FIXME: doesn't account for weight
        for answer in answers:
            host, port, prio, weight = answer

            try:
                return self.connect(host, port, keepalive, bind_address)
            except:
                pass

        raise ValueError("No SRV hosts responded")

    def connect_async(self, host, port=1883, keepalive=60, bind_address=""):
        """Connect to a remote broker asynchronously. This is a non-blocking
        connect call that can be used with loop_start() to provide very quick
        start.

        host is the hostname or IP address of the remote broker.
        port is the network port of the server host to connect to. Defaults to
        1883. Note that the default port for MQTT over SSL/TLS is 8883 so if you
        are using tls_set() the port may need providing.
        keepalive: Maximum period in seconds between communications with the
        broker. If no other messages are being exchanged, this controls the
        rate at which the client will send ping messages to the broker.
        """
        if host is None or len(host) == 0:
            raise ValueError('Invalid host.')
        if port <= 0:
            raise ValueError('Invalid port number.')
        if keepalive < 0:
            raise ValueError('Keepalive must be >=0.')
        if bind_address != "" and bind_address is not None:
            if (sys.version_info[0] == 2 and sys.version_info[1] < 7) or (
                        sys.version_info[0] == 3 and sys.version_info[1] < 2):
                raise ValueError('bind_address requires Python 2.7 or 3.2.')

        self._host = host
        self._port = port
        self._keepalive = keepalive
        self._bind_address = bind_address

        self._state = mqtt_cs_connect_async

    def reconnect_delay_set(self, min_delay=1, max_delay=120):
        """ Configure the exponential reconnect delay

            When connection is lost, wait initially min_delay seconds and
            double this time every attempt. The wait is capped at max_delay.
            Once the client is fully connected (e.g. not only TCP socket, but
            received a success CONNACK), the wait timer is reset to min_delay.
        """
        with self._reconnect_delay_mutex:
            self._reconnect_min_delay = min_delay
            self._reconnect_max_delay = max_delay
            self._reconnect_delay = None

    def reconnect(self):
        """Reconnect the client after a disconnect. Can only be called after
        connect()/connect_async()."""
        if len(self._host) == 0:
            raise ValueError('Invalid host.')
        if self._port <= 0:
            raise ValueError('Invalid port number.')

        self._in_packet = {
            "command": 0,
            "have_remaining": 0,
            "remaining_count": [],
            "remaining_mult": 1,
            "remaining_length": 0,
            "packet": b"",
            "to_process": 0,
            "pos": 0}

        with self._out_packet_mutex:
            self._out_packet = collections.deque()

        with self._current_out_packet_mutex:
            self._current_out_packet = None

        with self._msgtime_mutex:
            self._last_msg_in = time_func()
            self._last_msg_out = time_func()

        self._ping_t = 0
        self._state = mqtt_cs_new

        if self._sock:
            self._sock.close()
            self._sock = None

        # Put messages in progress in a valid state.
        self._messages_reconnect_reset()

        try:
            if (sys.version_info[0] == 2 and sys.version_info[1] < 7) or (
                        sys.version_info[0] == 3 and sys.version_info[1] < 2):
                sock = socket.create_connection((self._host, self._port))
            else:
                sock = socket.create_connection((self._host, self._port), source_address=(self._bind_address, 0))
        except socket.error as err:
            if err.errno != errno.EINPROGRESS and err.errno != errno.EWOULDBLOCK and err.errno != EAGAIN:
                raise

        if self._ssl:
            # SSL is only supported when SSLContext is available (implies Python >= 2.7.9 or >= 3.2)

            verify_host = not self._tls_insecure
            try:
                # Try with server_hostname, even it's not supported in certain scenarios
                sock = self._ssl_context.wrap_socket(
                    sock,
                    server_hostname=self._host,
                    do_handshake_on_connect=False,
                )
            except ssl.CertificateError:
                # CertificateError is derived from ValueError
                raise
            except ValueError:
                # Python version requires SNI in order to handle server_hostname, but SNI is not available
                sock = self._ssl_context.wrap_socket(
                    sock,
                    do_handshake_on_connect=False,
                )
            else:
                # If SSL context has already checked hostname, then don't need to do it again
                if (hasattr(self._ssl_context, 'check_hostname') and
                        self._ssl_context.check_hostname):
                    verify_host = False

            sock.settimeout(self._keepalive)
            sock.do_handshake()

            if verify_host:
                ssl.match_hostname(sock.getpeercert(), self._host)

        if self._transport == "websockets":
            sock.settimeout(self._keepalive)
            sock = WebsocketWrapper(sock, self._host, self._port, self._ssl,
                self._websocket_path, self._websocket_extra_headers)

        self._sock = sock
        self._sock.setblocking(0)

        return self._send_connect(self._keepalive, self._clean_session)

    def loop(self, timeout=1.0, max_packets=1):
        """Process network events.

        This function must be called regularly to ensure communication with the
        broker is carried out. It calls select() on the network socket to wait
        for network events. If incoming data is present it will then be
        processed. Outgoing commands, from e.g. publish(), are normally sent
        immediately that their function is called, but this is not always
        possible. loop() will also attempt to send any remaining outgoing
        messages, which also includes commands that are part of the flow for
        messages with QoS>0.

        timeout: The time in seconds to wait for incoming/outgoing network
          traffic before timing out and returning.
        max_packets: Not currently used.

        Returns MQTT_ERR_SUCCESS on success.
        Returns >0 on error.

        A ValueError will be raised if timeout < 0"""
        if timeout < 0.0:
            raise ValueError('Invalid timeout.')

        with self._current_out_packet_mutex:
            with self._out_packet_mutex:
                if self._current_out_packet is None and len(self._out_packet) > 0:
                    self._current_out_packet = self._out_packet.popleft()

                if self._current_out_packet:
                    wlist = [self._sock]
                else:
                    wlist = []

        # used to check if there are any bytes left in the (SSL) socket
        pending_bytes = 0
        if hasattr(self._sock, 'pending'):
            pending_bytes = self._sock.pending()

        # if bytes are pending do not wait in select
        if pending_bytes > 0:
            timeout = 0.0

        # sockpairR is used to break out of select() before the timeout, on a
        # call to publish() etc.
        rlist = [self._sock, self._sockpairR]
        try:
            socklist = select.select(rlist, wlist, [], timeout)
        except TypeError:
            # Socket isn't correct type, in likelihood connection is lost
            return MQTT_ERR_CONN_LOST
        except ValueError:
            # Can occur if we just reconnected but rlist/wlist contain a -1 for
            # some reason.
            return MQTT_ERR_CONN_LOST
        except KeyboardInterrupt:
            # Allow ^C to interrupt
            raise
        except:
            return MQTT_ERR_UNKNOWN

        if self._sock in socklist[0] or pending_bytes > 0:
            rc = self.loop_read(max_packets)
            if rc or self._sock is None:
                return rc

        if self._sockpairR in socklist[0]:
            # Stimulate output write even though we didn't ask for it, because
            # at that point the publish or other command wasn't present.
            socklist[1].insert(0, self._sock)
            # Clear sockpairR - only ever a single byte written.
            try:
                self._sockpairR.recv(1)
            except socket.error as err:
                if err.errno != EAGAIN:
                    raise

        if self._sock in socklist[1]:
            rc = self.loop_write(max_packets)
            if rc or self._sock is None:
                return rc

        return self.loop_misc()

    def publish(self, topic, payload=None, qos=0, retain=False):
        """Publish a message on a topic.

        This causes a message to be sent to the broker and subsequently from
        the broker to any clients subscribing to matching topics.

        topic: The topic that the message should be published on.
        payload: The actual message to send. If not given, or set to None a
        zero length message will be used. Passing an int or float will result
        in the payload being converted to a string representing that number. If
        you wish to send a true int/float, use struct.pack() to create the
        payload you require.
        qos: The quality of service level to use.
        retain: If set to true, the message will be set as the "last known
        good"/retained message for the topic.

        Returns a MQTTMessageInfo class, which can be used to determine whether
        the message has been delivered (using info.is_published()) or to block
        waiting for the message to be delivered (info.wait_for_publish()). The
        message ID and return code of the publish() call can be found at
        info.mid and info.rc.

        For backwards compatibility, the MQTTMessageInfo class is iterable so
        the old construct of (rc, mid) = client.publish(...) is still valid.

        rc is MQTT_ERR_SUCCESS to indicate success or MQTT_ERR_NO_CONN if the
        client is not currently connected.  mid is the message ID for the
        publish request. The mid value can be used to track the publish request
        by checking against the mid argument in the on_publish() callback if it
        is defined.

        A ValueError will be raised if topic is None, has zero length or is
        invalid (contains a wildcard), if qos is not one of 0, 1 or 2, or if
        the length of the payload is greater than 268435455 bytes."""
        if topic is None or len(topic) == 0:
            raise ValueError('Invalid topic.')

        topic = topic.encode('utf-8')

        if self._topic_wildcard_len_check(topic) != MQTT_ERR_SUCCESS:
            raise ValueError('Publish topic cannot contain wildcards.')

        if qos < 0 or qos > 2:
            raise ValueError('Invalid QoS level.')

        if isinstance(payload, unicode):
            local_payload = payload.encode('utf-8')
        elif isinstance(payload, (bytes, bytearray)):
            local_payload = payload
        elif isinstance(payload, (int, float)):
            local_payload = str(payload).encode('ascii')
        elif payload is None:
            local_payload = b''
        else:
            raise TypeError('payload must be a string, bytearray, int, float or None.')

        if len(local_payload) > 268435455:
            raise ValueError('Payload too large.')

        local_mid = self._mid_generate()

        if qos == 0:
            info = MQTTMessageInfo(local_mid)
            rc = self._send_publish(local_mid, topic, local_payload, qos, retain, False, info)
            info.rc = rc
            return info
        else:
            message = MQTTMessage(local_mid, topic)
            message.timestamp = time_func()
            message.payload = local_payload
            message.qos = qos
            message.retain = retain
            message.dup = False

            with self._out_message_mutex:
                if self._max_queued_messages > 0 and len(self._out_messages) >= self._max_queued_messages:
                    message.info.rc = MQTT_ERR_QUEUE_SIZE
                    return message.info

                self._out_messages.append(message)
                if self._max_inflight_messages == 0 or self._inflight_messages < self._max_inflight_messages:
                    self._inflight_messages += 1
                    if qos == 1:
                        message.state = mqtt_ms_wait_for_puback
                    elif qos == 2:
                        message.state = mqtt_ms_wait_for_pubrec

                    rc = self._send_publish(message.mid, topic, message.payload, message.qos, message.retain,
                                            message.dup)

                    # remove from inflight messages so it will be send after a connection is made
                    if rc is MQTT_ERR_NO_CONN:
                        self._inflight_messages -= 1
                        message.state = mqtt_ms_publish

                    message.info.rc = rc
                    return message.info
                else:
                    message.state = mqtt_ms_queued
                    message.info.rc = MQTT_ERR_SUCCESS
                    return message.info

    def username_pw_set(self, username, password=None):
        """Set a username and optionally a password for broker authentication.

        Must be called before connect() to have any effect.
        Requires a broker that supports MQTT v3.1.

        username: The username to authenticate with. Need have no relationship to the client id. Must be unicode    
            [MQTT-3.1.3-11].
        password: The password to authenticate with. Optional, set to None if not required. If it is unicode, then it 
            will be encoded as UTF-8.
        """

        # [MQTT-3.1.3-11] User name must be UTF-8 encoded string
        self._username = username.encode('utf-8')
        self._password = password
        if isinstance(self._password, unicode):
            self._password = self._password.encode('utf-8')

    def disconnect(self):
        """Disconnect a connected client from the broker."""
        self._state = mqtt_cs_disconnecting

        if self._sock is None:
            return MQTT_ERR_NO_CONN

        return self._send_disconnect()

    def subscribe(self, topic, qos=0):
        """Subscribe the client to one or more topics.

        This function may be called in three different ways:

        Simple string and integer
        -------------------------
        e.g. subscribe("my/topic", 2)

        topic: A string specifying the subscription topic to subscribe to.
        qos: The desired quality of service level for the subscription.
             Defaults to 0.

        String and integer tuple
        ------------------------
        e.g. subscribe(("my/topic", 1))

        topic: A tuple of (topic, qos). Both topic and qos must be present in
               the tuple.
        qos: Not used.

        List of string and integer tuples
        ------------------------
        e.g. subscribe([("my/topic", 0), ("another/topic", 2)])

        This allows multiple topic subscriptions in a single SUBSCRIPTION
        command, which is more efficient than using multiple calls to
        subscribe().

        topic: A list of tuple of format (topic, qos). Both topic and qos must
               be present in all of the tuples.
        qos: Not used.

        The function returns a tuple (result, mid), where result is
        MQTT_ERR_SUCCESS to indicate success or (MQTT_ERR_NO_CONN, None) if the
        client is not currently connected.  mid is the message ID for the
        subscribe request. The mid value can be used to track the subscribe
        request by checking against the mid argument in the on_subscribe()
        callback if it is defined.

        Raises a ValueError if qos is not 0, 1 or 2, or if topic is None or has
        zero string length, or if topic is not a string, tuple or list.
        """
        topic_qos_list = None

        if isinstance(topic, tuple):
            topic, qos = topic

        if isinstance(topic, basestring):
            if qos < 0 or qos > 2:
                raise ValueError('Invalid QoS level.')
            if topic is None or len(topic) == 0:
                raise ValueError('Invalid topic.')
            topic_qos_list = [(topic.encode('utf-8'), qos)]
        elif isinstance(topic, list):
            topic_qos_list = []
            for t, q in topic:
                if q < 0 or q > 2:
                    raise ValueError('Invalid QoS level.')
                if t is None or len(t) == 0 or not isinstance(t, basestring):
                    raise ValueError('Invalid topic.')
                topic_qos_list.append((t.encode('utf-8'), q))

        if topic_qos_list is None:
            raise ValueError("No topic specified, or incorrect topic type.")

        if any(self._filter_wildcard_len_check(topic) != MQTT_ERR_SUCCESS for topic, _ in topic_qos_list):
            raise ValueError('Invalid subscription filter.')

        if self._sock is None:
            return (MQTT_ERR_NO_CONN, None)

        return self._send_subscribe(False, topic_qos_list)

    def unsubscribe(self, topic):
        """Unsubscribe the client from one or more topics.

        topic: A single string, or list of strings that are the subscription
               topics to unsubscribe from.

        Returns a tuple (result, mid), where result is MQTT_ERR_SUCCESS
        to indicate success or (MQTT_ERR_NO_CONN, None) if the client is not
        currently connected.
        mid is the message ID for the unsubscribe request. The mid value can be
        used to track the unsubscribe request by checking against the mid
        argument in the on_unsubscribe() callback if it is defined.

        Raises a ValueError if topic is None or has zero string length, or is
        not a string or list.
        """
        topic_list = None
        if topic is None:
            raise ValueError('Invalid topic.')
        if isinstance(topic, basestring):
            if len(topic) == 0:
                raise ValueError('Invalid topic.')
            topic_list = [topic.encode('utf-8')]
        elif isinstance(topic, list):
            topic_list = []
            for t in topic:
                if len(t) == 0 or not isinstance(t, basestring):
                    raise ValueError('Invalid topic.')
                topic_list.append(t.encode('utf-8'))

        if topic_list is None:
            raise ValueError("No topic specified, or incorrect topic type.")

        if self._sock is None:
            return (MQTT_ERR_NO_CONN, None)

        return self._send_unsubscribe(False, topic_list)

    def loop_read(self, max_packets=1):
        """Process read network events. Use in place of calling loop() if you
        wish to handle your client reads as part of your own application.

        Use socket() to obtain the client socket to call select() or equivalent
        on.

        Do not use if you are using the threaded interface loop_start()."""
        if self._sock is None:
            return MQTT_ERR_NO_CONN

        max_packets = len(self._out_messages) + len(self._in_messages)
        if max_packets < 1:
            max_packets = 1

        for _ in range(0, max_packets):
            if self._sock is None:
                return MQTT_ERR_NO_CONN
            rc = self._packet_read()
            if rc > 0:
                return self._loop_rc_handle(rc)
            elif rc == MQTT_ERR_AGAIN:
                return MQTT_ERR_SUCCESS
        return MQTT_ERR_SUCCESS

    def loop_write(self, max_packets=1):
        """Process write network events. Use in place of calling loop() if you
        wish to handle your client writes as part of your own application.

        Use socket() to obtain the client socket to call select() or equivalent
        on.

        Use want_write() to determine if there is data waiting to be written.

        Do not use if you are using the threaded interface loop_start()."""
        if self._sock is None:
            return MQTT_ERR_NO_CONN

        max_packets = len(self._out_packet) + 1
        if max_packets < 1:
            max_packets = 1

        for _ in range(0, max_packets):
            rc = self._packet_write()
            if rc > 0:
                return self._loop_rc_handle(rc)
            elif rc == MQTT_ERR_AGAIN:
                return MQTT_ERR_SUCCESS
        return MQTT_ERR_SUCCESS

    def want_write(self):
        """Call to determine if there is network data waiting to be written.
        Useful if you are calling select() yourself rather than using loop().
        """
        if self._current_out_packet or len(self._out_packet) > 0:
            return True
        else:
            return False

    def loop_misc(self):
        """Process miscellaneous network events. Use in place of calling loop() if you
        wish to call select() or equivalent on.

        Do not use if you are using the threaded interface loop_start()."""
        if self._sock is None:
            return MQTT_ERR_NO_CONN

        now = time_func()
        self._check_keepalive()
        if self._last_retry_check + 1 < now:
            # Only check once a second at most
            self._message_retry_check()
            self._last_retry_check = now

        if self._ping_t > 0 and now - self._ping_t >= self._keepalive:
            # client->ping_t != 0 means we are waiting for a pingresp.
            # This hasn't happened in the keepalive time so we should disconnect.
            if self._sock:
                self._sock.close()
                self._sock = None

            if self._state == mqtt_cs_disconnecting:
                rc = MQTT_ERR_SUCCESS
            else:
                rc = 1

            with self._callback_mutex:
                if self.on_disconnect:
                    with self._in_callback:
                        self.on_disconnect(self, self._userdata, rc)

            return MQTT_ERR_CONN_LOST

        return MQTT_ERR_SUCCESS

    def max_inflight_messages_set(self, inflight):
        """Set the maximum number of messages with QoS>0 that can be part way
        through their network flow at once. Defaults to 20."""
        if inflight < 0:
            raise ValueError('Invalid inflight.')
        self._max_inflight_messages = inflight

    def max_queued_messages_set(self, queue_size):
        """Set the maximum number of messages in the outgoing message queue.
        0 means unlimited."""
        if queue_size < 0:
            raise ValueError('Invalid queue size.')
        if not isinstance(queue_size, int):
            raise ValueError('Invalid type of queue size.')
        self._max_queued_messages = queue_size
        return self

    def message_retry_set(self, retry):
        """Set the timeout in seconds before a message with QoS>0 is retried.
        20 seconds by default."""
        if retry < 0:
            raise ValueError('Invalid retry.')

        self._message_retry = retry

    def user_data_set(self, userdata):
        """Set the user data variable passed to callbacks. May be any data type."""
        self._userdata = userdata

    def will_set(self, topic, payload=None, qos=0, retain=False):
        """Set a Will to be sent by the broker in case the client disconnects unexpectedly.

        This must be called before connect() to have any effect.

        topic: The topic that the will message should be published on.
        payload: The message to send as a will. If not given, or set to None a
        zero length message will be used as the will. Passing an int or float
        will result in the payload being converted to a string representing
        that number. If you wish to send a true int/float, use struct.pack() to
        create the payload you require.
        qos: The quality of service level to use for the will.
        retain: If set to true, the will message will be set as the "last known
        good"/retained message for the topic.

        Raises a ValueError if qos is not 0, 1 or 2, or if topic is None or has
        zero string length.
        """
        if topic is None or len(topic) == 0:
            raise ValueError('Invalid topic.')

        if qos < 0 or qos > 2:
            raise ValueError('Invalid QoS level.')

        if isinstance(payload, unicode):
            self._will_payload = payload.encode('utf-8')
        elif isinstance(payload, (bytes, bytearray)):
            self._will_payload = payload
        elif isinstance(payload, (int, float)):
            self._will_payload = str(payload).encode('ascii')
        elif payload is None:
            self._will_payload = b""
        else:
            raise TypeError('payload must be a string, bytearray, int, float or None.')

        self._will = True
        self._will_topic = topic.encode('utf-8')
        self._will_qos = qos
        self._will_retain = retain

    def will_clear(self):
        """ Removes a will that was previously configured with will_set().

        Must be called before connect() to have any effect."""
        self._will = False
        self._will_topic = b""
        self._will_payload = b""
        self._will_qos = 0
        self._will_retain = False

    def socket(self):
        """Return the socket or ssl object for this client."""
        return self._sock

    def loop_forever(self, timeout=1.0, max_packets=1, retry_first_connection=False):
        """This function call loop() for you in an infinite blocking loop. It
        is useful for the case where you only want to run the MQTT client loop
        in your program.

        loop_forever() will handle reconnecting for you. If you call
        disconnect() in a callback it will return.


        timeout: The time in seconds to wait for incoming/outgoing network
          traffic before timing out and returning.
        max_packets: Not currently used.
        retry_first_connection: Should the first connection attempt be retried on failure.

        Raises socket.error on first connection failures unless retry_first_connection=True
        """

        run = True

        while run:
            if self._thread_terminate is True:
                break

            if self._state == mqtt_cs_connect_async:
                try:
                    self.reconnect()
                except (socket.error, WebsocketConnectionError):
                    if not retry_first_connection:
                        raise
                    self._easy_log(MQTT_LOG_DEBUG, "Connection failed, retrying")
                    self._reconnect_wait()
            else:
                break

        while run:
            rc = MQTT_ERR_SUCCESS
            while rc == MQTT_ERR_SUCCESS:
                rc = self.loop(timeout, max_packets)
                # We don't need to worry about locking here, because we've
                # either called loop_forever() when in single threaded mode, or
                # in multi threaded mode when loop_stop() has been called and
                # so no other threads can access _current_out_packet,
                # _out_packet or _messages.
                if (self._thread_terminate is True
                    and self._current_out_packet is None
                    and len(self._out_packet) == 0
                    and len(self._out_messages) == 0):
                    rc = 1
                    run = False


            def should_exit():
                return self._state == mqtt_cs_disconnecting or run is False or self._thread_terminate is True

            if should_exit():
                run = False
            else:
                self._reconnect_wait()

                if should_exit():
                    run = False
                else:
                    try:
                        self.reconnect()
                    except (socket.error, WebsocketConnectionError):
                        pass

        return rc

    def loop_start(self):
        """This is part of the threaded client interface. Call this once to
        start a new thread to process network traffic. This provides an
        alternative to repeatedly calling loop() yourself.
        """
        if self._thread is not None:
            return MQTT_ERR_INVAL

        self._thread_terminate = False
        self._thread = threading.Thread(target=self._thread_main)
        self._thread.daemon = True
        self._thread.start()

    def loop_stop(self, force=False):
        """This is part of the threaded client interface. Call this once to
        stop the network thread previously created with loop_start(). This call
        will block until the network thread finishes.

        The force parameter is currently ignored.
        """
        if self._thread is None:
            return MQTT_ERR_INVAL

        self._thread_terminate = True
        if threading.current_thread() != self._thread:
            self._thread.join()
            self._thread = None

    @property
    def on_log(self):
        """If implemented, called when the client has log information.
        Defined to allow debugging."""
        return self._on_log

    @on_log.setter
    def on_log(self, func):
        """ Define the logging callback implementation.

        Expected signature is:
            log_callback(client, userdata, level, buf)

        client:     the client instance for this callback
        userdata:   the private user data as set in Client() or userdata_set()
        level:      gives the severity of the message and will be one of
                    MQTT_LOG_INFO, MQTT_LOG_NOTICE, MQTT_LOG_WARNING,
                    MQTT_LOG_ERR, and MQTT_LOG_DEBUG.
        buf:        the message itself
        """
        self._on_log = func

    @property
    def on_connect(self):
        """If implemented, called when the broker responds to our connection
        request."""
        return self._on_connect

    @on_connect.setter
    def on_connect(self, func):
        """ Define the connect callback implementation.

        Expected signature is:
            connect_callback(client, userdata, flags, rc)

        client:     the client instance for this callback
        userdata:   the private user data as set in Client() or userdata_set()
        flags:      response flags sent by the broker
        rc:         the connection result

        flags is a dict that contains response flags from the broker:
            flags['session present'] - this flag is useful for clients that are
                using clean session set to 0 only. If a client with clean
                session=0, that reconnects to a broker that it has previously
                connected to, this flag indicates whether the broker still has the
                session information for the client. If 1, the session still exists.

        The value of rc indicates success or not:
            0: Connection successful
            1: Connection refused - incorrect protocol version
            2: Connection refused - invalid client identifier
            3: Connection refused - server unavailable
            4: Connection refused - bad username or password
            5: Connection refused - not authorised
            6-255: Currently unused.
        """
        with self._callback_mutex:
            self._on_connect = func

    @property
    def on_subscribe(self):
        """If implemented, called when the broker responds to a subscribe
        request."""
        return self._on_subscribe

    @on_subscribe.setter
    def on_subscribe(self, func):
        """ Define the suscribe callback implementation.

        Expected signature is:
            subscribe_callback(client, userdata, mid, granted_qos)

        client:         the client instance for this callback
        userdata:       the private user data as set in Client() or userdata_set()
        mid:            matches the mid variable returned from the corresponding
                        subscribe() call.
        granted_qos:    list of integers that give the QoS level the broker has
                        granted for each of the different subscription requests.
        """
        with self._callback_mutex:
            self._on_subscribe = func

    @property
    def on_message(self):
        """If implemented, called when a message has been received on a topic
        that the client subscribes to.

        This callback will be called for every message received. Use
        message_callback_add() to define multiple callbacks that will be called
        for specific topic filters."""
        return self._on_message

    @on_message.setter
    def on_message(self, func):
        """ Define the message received callback implementation.

        Expected signature is:
            on_message_callback(client, userdata, message)

        client:     the client instance for this callback
        userdata:   the private user data as set in Client() or userdata_set()
        message:    an instance of MQTTMessage.
                    This is a class with members topic, payload, qos, retain.
        """
        with self._callback_mutex:
            self._on_message = func

    @property
    def on_publish(self):
        """If implemented, called when a message that was to be sent using the
        publish() call has completed transmission to the broker.

        For messages with QoS levels 1 and 2, this means that the appropriate
        handshakes have completed. For QoS 0, this simply means that the message
        has left the client.
        This callback is important because even if the publish() call returns
        success, it does not always mean that the message has been sent."""
        return self._on_publish

    @on_publish.setter
    def on_publish(self, func):
        """ Define the published message callback implementation.

        Expected signature is:
            on_publish_callback(client, userdata, mid)

        client:     the client instance for this callback
        userdata:   the private user data as set in Client() or userdata_set()
        mid:        matches the mid variable returned from the corresponding
                    publish() call, to allow outgoing messages to be tracked.
        """
        with self._callback_mutex:
            self._on_publish = func

    @property
    def on_unsubscribe(self):
        """If implemented, called when the broker responds to an unsubscribe
        request."""
        return self._on_unsubscribe

    @on_unsubscribe.setter
    def on_unsubscribe(self, func):
        """ Define the unsubscribe callback implementation.

        Expected signature is:
            unsubscribe_callback(client, userdata, mid)

        client:     the client instance for this callback
        userdata:   the private user data as set in Client() or userdata_set()
        mid:        matches the mid variable returned from the corresponding
                    unsubscribe() call.
        """
        with self._callback_mutex:
            self._on_unsubscribe = func

    @property
    def on_disconnect(self):
        """If implemented, called when the client disconnects from the broker.
        """
        return self._on_disconnect

    @on_disconnect.setter
    def on_disconnect(self, func):
        """ Define the disconnect callback implementation.

        Expected signature is:
            disconnect_callback(client, userdata, self)

        client:     the client instance for this callback
        userdata:   the private user data as set in Client() or userdata_set()
        rc:         the disconnection result
                    The rc parameter indicates the disconnection state. If
                    MQTT_ERR_SUCCESS (0), the callback was called in response to
                    a disconnect() call. If any other value the disconnection
                    was unexpected, such as might be caused by a network error.
        """
        with self._callback_mutex:
            self._on_disconnect = func

    def message_callback_add(self, sub, callback):
        """Register a message callback for a specific topic.
        Messages that match 'sub' will be passed to 'callback'. Any
        non-matching messages will be passed to the default on_message
        callback.

        Call multiple times with different 'sub' to define multiple topic
        specific callbacks.

        Topic specific callbacks may be removed with
        message_callback_remove()."""
        if callback is None or sub is None:
            raise ValueError("sub and callback must both be defined.")

        with self._callback_mutex:
            self._on_message_filtered[sub] = callback

    def message_callback_remove(self, sub):
        """Remove a message callback previously registered with
        message_callback_add()."""
        if sub is None:
            raise ValueError("sub must defined.")

        with self._callback_mutex:
            try:
                del self._on_message_filtered[sub]
            except KeyError:  # no such subscription
                pass

    # ============================================================
    # Private functions
    # ============================================================

    def _loop_rc_handle(self, rc):
        if rc:
            if self._sock:
                self._sock.close()
                self._sock = None

            if self._state == mqtt_cs_disconnecting:
                rc = MQTT_ERR_SUCCESS

            with self._callback_mutex:
                if self.on_disconnect:
                    with self._in_callback:
                        self.on_disconnect(self, self._userdata, rc)
        return rc

    def _packet_read(self):
        # This gets called if pselect() indicates that there is network data
        # available - ie. at least one byte.  What we do depends on what data we
        # already have.
        # If we've not got a command, attempt to read one and save it. This should
        # always work because it's only a single byte.
        # Then try to read the remaining length. This may fail because it is may
        # be more than one byte - will need to save data pending next read if it
        # does fail.
        # Then try to read the remaining payload, where 'payload' here means the
        # combined variable header and actual payload. This is the most likely to
        # fail due to longer length, so save current data and current position.
        # After all data is read, send to _mqtt_handle_packet() to deal with.
        # Finally, free the memory and reset everything to starting conditions.
        if self._in_packet['command'] == 0:
            try:
                command = self._sock.recv(1)
            except socket.error as err:
                if self._ssl and (err.errno == ssl.SSL_ERROR_WANT_READ or err.errno == ssl.SSL_ERROR_WANT_WRITE):
                    return MQTT_ERR_AGAIN
                if err.errno == EAGAIN:
                    return MQTT_ERR_AGAIN
                print(err)
                return 1
            else:
                if len(command) == 0:
                    return 1
                command, = struct.unpack("!B", command)
                self._in_packet['command'] = command

        if self._in_packet['have_remaining'] == 0:
            # Read remaining
            # Algorithm for decoding taken from pseudo code at
            # http://publib.boulder.ibm.com/infocenter/wmbhelp/v6r0m0/topic/com.ibm.etools.mft.doc/ac10870_.htm
            while True:
                try:
                    byte = self._sock.recv(1)
                except socket.error as err:
                    if self._ssl and (err.errno == ssl.SSL_ERROR_WANT_READ or err.errno == ssl.SSL_ERROR_WANT_WRITE):
                        return MQTT_ERR_AGAIN
                    if err.errno == EAGAIN:
                        return MQTT_ERR_AGAIN
                    print(err)
                    return 1
                else:
                    if len(byte) == 0:
                        return 1
                    byte, = struct.unpack("!B", byte)
                    self._in_packet['remaining_count'].append(byte)
                    # Max 4 bytes length for remaining length as defined by protocol.
                    # Anything more likely means a broken/malicious client.
                    if len(self._in_packet['remaining_count']) > 4:
                        return MQTT_ERR_PROTOCOL

                    self._in_packet['remaining_length'] += (byte & 127) * self._in_packet['remaining_mult']
                    self._in_packet['remaining_mult'] = self._in_packet['remaining_mult'] * 128

                if (byte & 128) == 0:
                    break

            self._in_packet['have_remaining'] = 1
            self._in_packet['to_process'] = self._in_packet['remaining_length']

        while self._in_packet['to_process'] > 0:
            try:
                data = self._sock.recv(self._in_packet['to_process'])
            except socket.error as err:
                if self._ssl and (err.errno == ssl.SSL_ERROR_WANT_READ or err.errno == ssl.SSL_ERROR_WANT_WRITE):
                    return MQTT_ERR_AGAIN
                if err.errno == EAGAIN:
                    return MQTT_ERR_AGAIN
                print(err)
                return 1
            else:
                if len(data) == 0:
                    return 1
                self._in_packet['to_process'] -= len(data)
                self._in_packet['packet'] += data

        # All data for this packet is read.
        self._in_packet['pos'] = 0
        rc = self._packet_handle()

        # Free data and reset values
        self._in_packet = {
            'command': 0,
            'have_remaining': 0,
            'remaining_count': [],
            'remaining_mult': 1,
            'remaining_length': 0,
            'packet': b"",
            'to_process': 0,
            'pos': 0}

        with self._msgtime_mutex:
            self._last_msg_in = time_func()
        return rc

    def _packet_write(self):
        self._current_out_packet_mutex.acquire()

        while self._current_out_packet:
            packet = self._current_out_packet

            try:
                write_length = self._sock.send(packet['packet'][packet['pos']:])
            except (AttributeError, ValueError):
                self._current_out_packet_mutex.release()
                return MQTT_ERR_SUCCESS
            except socket.error as err:
                self._current_out_packet_mutex.release()
                if self._ssl and (err.errno == ssl.SSL_ERROR_WANT_READ or err.errno == ssl.SSL_ERROR_WANT_WRITE):
                    return MQTT_ERR_AGAIN
                if err.errno == EAGAIN:
                    return MQTT_ERR_AGAIN
                print(err)
                return 1

            if write_length > 0:
                packet['to_process'] -= write_length
                packet['pos'] += write_length

                if packet['to_process'] == 0:
                    if (packet['command'] & 0xF0) == PUBLISH and packet['qos'] == 0:
                        with self._callback_mutex:
                            if self.on_publish:
                                with self._in_callback:
                                    self.on_publish(self, self._userdata, packet['mid'])

                        packet['info']._set_as_published()

                    if (packet['command'] & 0xF0) == DISCONNECT:
                        self._current_out_packet_mutex.release()

                        with self._msgtime_mutex:
                            self._last_msg_out = time_func()

                        with self._callback_mutex:
                            if self.on_disconnect:
                                with self._in_callback:
                                    self.on_disconnect(self, self._userdata, 0)

                        if self._sock:
                            self._sock.close()
                            self._sock = None
                        return MQTT_ERR_SUCCESS

                    with self._out_packet_mutex:
                        if len(self._out_packet) > 0:
                            self._current_out_packet = self._out_packet.popleft()
                        else:
                            self._current_out_packet = None
            else:
                break

        self._current_out_packet_mutex.release()

        with self._msgtime_mutex:
            self._last_msg_out = time_func()

        return MQTT_ERR_SUCCESS

    def _easy_log(self, level, fmt, *args):
        if self.on_log:
            buf = fmt % args
            self.on_log(self, self._userdata, level, buf)
        if self._logger:
            level_std = LOGGING_LEVEL[level]
            self._logger.log(level_std, fmt, *args)

    def _check_keepalive(self):
        if self._keepalive == 0:
            return MQTT_ERR_SUCCESS

        now = time_func()

        with self._msgtime_mutex:
            last_msg_out = self._last_msg_out
            last_msg_in = self._last_msg_in

        if self._sock is not None and (now - last_msg_out >= self._keepalive or now - last_msg_in >= self._keepalive):
            if self._state == mqtt_cs_connected and self._ping_t == 0:
                self._send_pingreq()
                with self._msgtime_mutex:
                    self._last_msg_out = now
                    self._last_msg_in = now
            else:
                if self._sock:
                    self._sock.close()
                    self._sock = None

                if self._state == mqtt_cs_disconnecting:
                    rc = MQTT_ERR_SUCCESS
                else:
                    rc = 1
                with self._callback_mutex:
                    if self.on_disconnect:
                        with self._in_callback:
                            self.on_disconnect(self, self._userdata, rc)

    def _mid_generate(self):
        self._last_mid += 1
        if self._last_mid == 65536:
            self._last_mid = 1
        return self._last_mid

    @staticmethod
    def _topic_wildcard_len_check(topic):
        # Search for + or # in a topic. Return MQTT_ERR_INVAL if found.
        # Also returns MQTT_ERR_INVAL if the topic string is too long.
        # Returns MQTT_ERR_SUCCESS if everything is fine.
        if b'+' in topic or b'#' in topic or len(topic) == 0 or len(topic) > 65535:
            return MQTT_ERR_INVAL
        else:
            return MQTT_ERR_SUCCESS

    @staticmethod
    def _filter_wildcard_len_check(sub):
        if (len(sub) == 0 or len(sub) > 65535
            or any(b'+' in p or b'#' in p for p in sub.split(b'/') if len(p) > 1)
            or b'#/' in sub):
            return MQTT_ERR_INVAL
        else:
            return MQTT_ERR_SUCCESS

    def _send_pingreq(self):
        self._easy_log(MQTT_LOG_DEBUG, "Sending PINGREQ")
        rc = self._send_simple_command(PINGREQ)
        if rc == MQTT_ERR_SUCCESS:
            self._ping_t = time_func()
        return rc

    def _send_pingresp(self):
        self._easy_log(MQTT_LOG_DEBUG, "Sending PINGRESP")
        return self._send_simple_command(PINGRESP)

    def _send_puback(self, mid):
        self._easy_log(MQTT_LOG_DEBUG, "Sending PUBACK (Mid: %d)", mid)
        return self._send_command_with_mid(PUBACK, mid, False)

    def _send_pubcomp(self, mid):
        self._easy_log(MQTT_LOG_DEBUG, "Sending PUBCOMP (Mid: %d)", mid)
        return self._send_command_with_mid(PUBCOMP, mid, False)

    def _pack_remaining_length(self, packet, remaining_length):
        remaining_bytes = []
        while True:
            byte = remaining_length % 128
            remaining_length = remaining_length // 128
            # If there are more digits to encode, set the top bit of this digit
            if remaining_length > 0:
                byte |= 0x80

            remaining_bytes.append(byte)
            packet.append(byte)
            if remaining_length == 0:
                # FIXME - this doesn't deal with incorrectly large payloads
                return packet

    def _pack_str16(self, packet, data):
        if isinstance(data, unicode):
            data = data.encode('utf-8')
        packet.extend(struct.pack("!H", len(data)))
        packet.extend(data)

    def _send_publish(self, mid, topic, payload=b'', qos=0, retain=False, dup=False, info=None):
        # we assume that topic and payload are already properly encoded
        assert not isinstance(topic, unicode) and not isinstance(payload, unicode) and payload is not None

        if self._sock is None:
            return MQTT_ERR_NO_CONN

        command = PUBLISH | ((dup & 0x1) << 3) | (qos << 1) | retain
        packet = bytearray()
        packet.append(command)

        payloadlen = len(payload)
        remaining_length = 2 + len(topic) + payloadlen

        if payloadlen == 0:
            self._easy_log(
                MQTT_LOG_DEBUG,
                "Sending PUBLISH (d%d, q%d, r%d, m%d), '%s' (NULL payload)",
                dup, qos, retain, mid, topic
            )
        else:
            self._easy_log(
                MQTT_LOG_DEBUG,
                "Sending PUBLISH (d%d, q%d, r%d, m%d), '%s', ... (%d bytes)",
                dup, qos, retain, mid, topic, payloadlen
            )

        if qos > 0:
            # For message id
            remaining_length += 2

        self._pack_remaining_length(packet, remaining_length)
        self._pack_str16(packet, topic)

        if qos > 0:
            # For message id
            packet.extend(struct.pack("!H", mid))

        packet.extend(payload)

        return self._packet_queue(PUBLISH, packet, mid, qos, info)

    def _send_pubrec(self, mid):
        self._easy_log(MQTT_LOG_DEBUG, "Sending PUBREC (Mid: %d)", mid)
        return self._send_command_with_mid(PUBREC, mid, False)

    def _send_pubrel(self, mid, dup=False):
        self._easy_log(MQTT_LOG_DEBUG, "Sending PUBREL (Mid: %d)", mid)
        return self._send_command_with_mid(PUBREL | 2, mid, dup)

    def _send_command_with_mid(self, command, mid, dup):
        # For PUBACK, PUBCOMP, PUBREC, and PUBREL
        if dup:
            command |= 0x8

        remaining_length = 2
        packet = struct.pack('!BBH', command, remaining_length, mid)
        return self._packet_queue(command, packet, mid, 1)

    def _send_simple_command(self, command):
        # For DISCONNECT, PINGREQ and PINGRESP
        remaining_length = 0
        packet = struct.pack('!BB', command, remaining_length)
        return self._packet_queue(command, packet, 0, 0)

    def _send_connect(self, keepalive, clean_session):
        proto_ver = self._protocol
        protocol = b"MQTT" if proto_ver >= MQTTv311 else b"MQIsdp"  # hard-coded UTF-8 encoded string

        remaining_length = 2 + len(protocol) + 1 + 1 + 2 + 2 + len(self._client_id)

        connect_flags = 0
        if clean_session:
            connect_flags |= 0x02

        if self._will:
            remaining_length += 2 + len(self._will_topic) + 2 + len(self._will_payload)
            connect_flags |= 0x04 | ((self._will_qos & 0x03) << 3) | ((self._will_retain & 0x01) << 5)

        if self._username is not None:
            remaining_length += 2 + len(self._username)
            connect_flags |= 0x80
            if self._password is not None:
                connect_flags |= 0x40
                remaining_length += 2 + len(self._password)

        command = CONNECT
        packet = bytearray()
        packet.append(command)

        self._pack_remaining_length(packet, remaining_length)
        packet.extend(struct.pack("!H" + str(len(protocol)) + "sBBH", len(protocol), protocol, proto_ver, connect_flags,
                                  keepalive))

        self._pack_str16(packet, self._client_id)

        if self._will:
            self._pack_str16(packet, self._will_topic)
            self._pack_str16(packet, self._will_payload)

        if self._username is not None:
            self._pack_str16(packet, self._username)

            if self._password is not None:
                self._pack_str16(packet, self._password)

        self._keepalive = keepalive
        self._easy_log(
            MQTT_LOG_DEBUG,
            "Sending CONNECT (u%d, p%d, wr%d, wq%d, wf%d, c%d, k%d) client_id=%s",
            (connect_flags & 0x80) >> 7,
            (connect_flags & 0x40) >> 6,
            (connect_flags & 0x20) >> 5,
            (connect_flags & 0x18) >> 3,
            (connect_flags & 0x4) >> 2,
            (connect_flags & 0x2) >> 1,
            keepalive,
            self._client_id
        )
        return self._packet_queue(command, packet, 0, 0)

    def _send_disconnect(self):
        self._easy_log(MQTT_LOG_DEBUG, "Sending DISCONNECT")
        return self._send_simple_command(DISCONNECT)

    def _send_subscribe(self, dup, topics):
        remaining_length = 2
        for t, _ in topics:
            remaining_length += 2 + len(t) + 1

        command = SUBSCRIBE | (dup << 3) | 0x2
        packet = bytearray()
        packet.append(command)
        self._pack_remaining_length(packet, remaining_length)
        local_mid = self._mid_generate()
        packet.extend(struct.pack("!H", local_mid))
        for t, q in topics:
            self._pack_str16(packet, t)
            packet.append(q)

        self._easy_log(MQTT_LOG_DEBUG, "Sending SUBSCRIBE (d%d) %s", dup, topics)
        return (self._packet_queue(command, packet, local_mid, 1), local_mid)

    def _send_unsubscribe(self, dup, topics):
        remaining_length = 2
        for t in topics:
            remaining_length += 2 + len(t)

        command = UNSUBSCRIBE | (dup << 3) | 0x2
        packet = bytearray()
        packet.append(command)
        self._pack_remaining_length(packet, remaining_length)
        local_mid = self._mid_generate()
        packet.extend(struct.pack("!H", local_mid))
        for t in topics:
            self._pack_str16(packet, t)

        # topics_repr = ", ".join("'"+topic.decode('utf8')+"'" for topic in topics)
        self._easy_log(MQTT_LOG_DEBUG, "Sending UNSUBSCRIBE (d%d) %s", dup, topics)
        return (self._packet_queue(command, packet, local_mid, 1), local_mid)

    def _message_retry_check_actual(self, messages, mutex):
        with mutex:
            now = time_func()
            for m in messages:
                if m.timestamp + self._message_retry < now:
                    if m.state == mqtt_ms_wait_for_puback or m.state == mqtt_ms_wait_for_pubrec:
                        m.timestamp = now
                        m.dup = True
                        self._send_publish(
                            m.mid,
                            m.topic.encode('utf-8'),
                            m.payload,
                            m.qos,
                            m.retain,
                            m.dup
                        )
                    elif m.state == mqtt_ms_wait_for_pubrel:
                        m.timestamp = now
                        m.dup = True
                        self._send_pubrec(m.mid)
                    elif m.state == mqtt_ms_wait_for_pubcomp:
                        m.timestamp = now
                        m.dup = True
                        self._send_pubrel(m.mid, True)

    def _message_retry_check(self):
        self._message_retry_check_actual(self._out_messages, self._out_message_mutex)
        self._message_retry_check_actual(self._in_messages, self._in_message_mutex)

    def _messages_reconnect_reset_out(self):
        with self._out_message_mutex:
            self._inflight_messages = 0
            for m in self._out_messages:
                m.timestamp = 0
                if self._max_inflight_messages == 0 or self._inflight_messages < self._max_inflight_messages:
                    if m.qos == 0:
                        m.state = mqtt_ms_publish
                    elif m.qos == 1:
                        # self._inflight_messages = self._inflight_messages + 1
                        if m.state == mqtt_ms_wait_for_puback:
                            m.dup = True
                        m.state = mqtt_ms_publish
                    elif m.qos == 2:
                        # self._inflight_messages = self._inflight_messages + 1
                        if m.state == mqtt_ms_wait_for_pubcomp:
                            m.state = mqtt_ms_resend_pubrel
                            m.dup = True
                        else:
                            if m.state == mqtt_ms_wait_for_pubrec:
                                m.dup = True
                            m.state = mqtt_ms_publish
                else:
                    m.state = mqtt_ms_queued

    def _messages_reconnect_reset_in(self):
        with self._in_message_mutex:
            for m in self._in_messages:
                m.timestamp = 0
                if m.qos != 2:
                    self._in_messages.pop(self._in_messages.index(m))
                else:
                    # Preserve current state
                    pass

    def _messages_reconnect_reset(self):
        self._messages_reconnect_reset_out()
        self._messages_reconnect_reset_in()

    def _packet_queue(self, command, packet, mid, qos, info=None):
        mpkt = {
            'command': command,
            'mid': mid,
            'qos': qos,
            'pos': 0,
            'to_process': len(packet),
            'packet': packet,
            'info': info}

        with self._out_packet_mutex:
            self._out_packet.append(mpkt)
            if self._current_out_packet_mutex.acquire(False):
                if self._current_out_packet is None and len(self._out_packet) > 0:
                    self._current_out_packet = self._out_packet.popleft()
                self._current_out_packet_mutex.release()

        # Write a single byte to sockpairW (connected to sockpairR) to break
        # out of select() if in threaded mode.
        try:
            self._sockpairW.send(sockpair_data)
        except socket.error as err:
            if err.errno != EAGAIN:
                raise

        if self._thread is None:
            if self._in_callback.acquire(False):
                self._in_callback.release()
                return self.loop_write()

        return MQTT_ERR_SUCCESS

    def _packet_handle(self):
        cmd = self._in_packet['command'] & 0xF0
        if cmd == PINGREQ:
            return self._handle_pingreq()
        elif cmd == PINGRESP:
            return self._handle_pingresp()
        elif cmd == PUBACK:
            return self._handle_pubackcomp("PUBACK")
        elif cmd == PUBCOMP:
            return self._handle_pubackcomp("PUBCOMP")
        elif cmd == PUBLISH:
            return self._handle_publish()
        elif cmd == PUBREC:
            return self._handle_pubrec()
        elif cmd == PUBREL:
            return self._handle_pubrel()
        elif cmd == CONNACK:
            return self._handle_connack()
        elif cmd == SUBACK:
            return self._handle_suback()
        elif cmd == UNSUBACK:
            return self._handle_unsuback()
        else:
            # If we don't recognise the command, return an error straight away.
            self._easy_log(MQTT_LOG_ERR, "Error: Unrecognised command %s", cmd)
            return MQTT_ERR_PROTOCOL

    def _handle_pingreq(self):
        if self._in_packet['remaining_length'] != 0:
            return MQTT_ERR_PROTOCOL

        self._easy_log(MQTT_LOG_DEBUG, "Received PINGREQ")
        return self._send_pingresp()

    def _handle_pingresp(self):
        if self._in_packet['remaining_length'] != 0:
            return MQTT_ERR_PROTOCOL

        # No longer waiting for a PINGRESP.
        self._ping_t = 0
        self._easy_log(MQTT_LOG_DEBUG, "Received PINGRESP")
        return MQTT_ERR_SUCCESS

    def _handle_connack(self):
        if self._in_packet['remaining_length'] != 2:
            return MQTT_ERR_PROTOCOL

        (flags, result) = struct.unpack("!BB", self._in_packet['packet'])
        if result == CONNACK_REFUSED_PROTOCOL_VERSION and self._protocol == MQTTv311:
            self._easy_log(
                MQTT_LOG_DEBUG,
                "Received CONNACK (%s, %s), attempting downgrade to MQTT v3.1.",
                flags, result
            )
            # Downgrade to MQTT v3.1
            self._protocol = MQTTv31
            return self.reconnect()
        elif (result == CONNACK_REFUSED_IDENTIFIER_REJECTED
                and self._client_id == b''):
            self._easy_log(
                MQTT_LOG_DEBUG,
                "Received CONNACK (%s, %s), attempting to use non-empty CID",
                flags, result,
            )
            self._client_id = base62(uuid.uuid4().int, padding=22)
            return self.reconnect()

        if result == 0:
            self._state = mqtt_cs_connected
            self._reconnect_delay = None

        self._easy_log(MQTT_LOG_DEBUG, "Received CONNACK (%s, %s)", flags, result)

        with self._callback_mutex:
            if self.on_connect:
                flags_dict = {}
                flags_dict['session present'] = flags & 0x01
                with self._in_callback:
                    self.on_connect(self, self._userdata, flags_dict, result)

        if result == 0:
            rc = 0
            with self._out_message_mutex:
                for m in self._out_messages:
                    m.timestamp = time_func()
                    if m.state == mqtt_ms_queued:
                        self.loop_write()  # Process outgoing messages that have just been queued up
                        return MQTT_ERR_SUCCESS

                    if m.qos == 0:
                        with self._in_callback:  # Don't call loop_write after _send_publish()
                            rc = self._send_publish(
                                m.mid,
                                m.topic.encode('utf-8'),
                                m.payload,
                                m.qos,
                                m.retain,
                                m.dup,
                            )
                        if rc != 0:
                            return rc
                    elif m.qos == 1:
                        if m.state == mqtt_ms_publish:
                            self._inflight_messages += 1
                            m.state = mqtt_ms_wait_for_puback
                            with self._in_callback:  # Don't call loop_write after _send_publish()
                                rc = self._send_publish(
                                    m.mid,
                                    m.topic.encode('utf-8'),
                                    m.payload,
                                    m.qos,
                                    m.retain,
                                    m.dup,
                                )
                            if rc != 0:
                                return rc
                    elif m.qos == 2:
                        if m.state == mqtt_ms_publish:
                            self._inflight_messages += 1
                            m.state = mqtt_ms_wait_for_pubrec
                            with self._in_callback:  # Don't call loop_write after _send_publish()
                                rc = self._send_publish(
                                    m.mid,
                                    m.topic.encode('utf-8'),
                                    m.payload,
                                    m.qos,
                                    m.retain,
                                    m.dup,
                                )
                            if rc != 0:
                                return rc
                        elif m.state == mqtt_ms_resend_pubrel:
                            self._inflight_messages += 1
                            m.state = mqtt_ms_wait_for_pubcomp
                            with self._in_callback:  # Don't call loop_write after _send_publish()
                                rc = self._send_pubrel(m.mid, m.dup)
                            if rc != 0:
                                return rc
                    self.loop_write()  # Process outgoing messages that have just been queued up

            return rc
        elif result > 0 and result < 6:
            return MQTT_ERR_CONN_REFUSED
        else:
            return MQTT_ERR_PROTOCOL

    def _handle_suback(self):
        self._easy_log(MQTT_LOG_DEBUG, "Received SUBACK")
        pack_format = "!H" + str(len(self._in_packet['packet']) - 2) + 's'
        (mid, packet) = struct.unpack(pack_format, self._in_packet['packet'])
        pack_format = "!" + "B" * len(packet)
        granted_qos = struct.unpack(pack_format, packet)

        with self._callback_mutex:
            if self.on_subscribe:
                with self._in_callback:  # Don't call loop_write after _send_publish()
                    self.on_subscribe(self, self._userdata, mid, granted_qos)

        return MQTT_ERR_SUCCESS

    def _handle_publish(self):
        rc = 0

        header = self._in_packet['command']
        message = MQTTMessage()
        message.dup = (header & 0x08) >> 3
        message.qos = (header & 0x06) >> 1
        message.retain = (header & 0x01)

        pack_format = "!H" + str(len(self._in_packet['packet']) - 2) + 's'
        (slen, packet) = struct.unpack(pack_format, self._in_packet['packet'])
        pack_format = '!' + str(slen) + 's' + str(len(packet) - slen) + 's'
        (topic, packet) = struct.unpack(pack_format, packet)

        if len(topic) == 0:
            return MQTT_ERR_PROTOCOL

        # Handle topics with invalid UTF-8
        # This replaces an invalid topic with a message and the hex
        # representation of the topic for logging. When the user attempts to
        # access message.topic in the callback, an exception will be raised.
        if sys.version_info[0] >= 3:
            try:
                print_topic = topic.decode('utf-8')
            except UnicodeDecodeError:
                print_topic = "TOPIC WITH INVALID UTF-8: " + str(topic)
        else:
            print_topic = topic

        message.topic = topic

        if message.qos > 0:
            pack_format = "!H" + str(len(packet) - 2) + 's'
            (message.mid, packet) = struct.unpack(pack_format, packet)

        message.payload = packet

        self._easy_log(
            MQTT_LOG_DEBUG,
            "Received PUBLISH (d%d, q%d, r%d, m%d), '%s', ...  (%d bytes)",
            message.dup, message.qos, message.retain, message.mid,
            print_topic, len(message.payload)
        )

        message.timestamp = time_func()
        if message.qos == 0:
            self._handle_on_message(message)
            return MQTT_ERR_SUCCESS
        elif message.qos == 1:
            rc = self._send_puback(message.mid)
            self._handle_on_message(message)
            return rc
        elif message.qos == 2:
            rc = self._send_pubrec(message.mid)
            message.state = mqtt_ms_wait_for_pubrel
            with self._in_message_mutex:
                if message not in self._in_messages:
                    self._in_messages.append(message)
            return rc
        else:
            return MQTT_ERR_PROTOCOL

    def _handle_pubrel(self):
        if self._in_packet['remaining_length'] != 2:
            return MQTT_ERR_PROTOCOL

        mid, = struct.unpack("!H", self._in_packet['packet'])
        self._easy_log(MQTT_LOG_DEBUG, "Received PUBREL (Mid: %d)", mid)

        with self._in_message_mutex:
            for i in range(len(self._in_messages)):
                if self._in_messages[i].mid == mid:

                    # Only pass the message on if we have removed it from the queue - this
                    # prevents multiple callbacks for the same message.
                    self._handle_on_message(self._in_messages[i])
                    self._in_messages.pop(i)
                    self._inflight_messages -= 1
                    if self._max_inflight_messages > 0:
                        with self._out_message_mutex:
                            rc = self._update_inflight()
                        if rc != MQTT_ERR_SUCCESS:
                            return rc

                    return self._send_pubcomp(mid)

        return MQTT_ERR_SUCCESS

    def _update_inflight(self):
        # Dont lock message_mutex here
        for m in self._out_messages:
            if self._inflight_messages < self._max_inflight_messages:
                if m.qos > 0 and m.state == mqtt_ms_queued:
                    self._inflight_messages += 1
                    if m.qos == 1:
                        m.state = mqtt_ms_wait_for_puback
                    elif m.qos == 2:
                        m.state = mqtt_ms_wait_for_pubrec
                    rc = self._send_publish(
                        m.mid,
                        m.topic.encode('utf-8'),
                        m.payload,
                        m.qos,
                        m.retain,
                        m.dup,
                    )
                    if rc != 0:
                        return rc
            else:
                return MQTT_ERR_SUCCESS
        return MQTT_ERR_SUCCESS

    def _handle_pubrec(self):
        if self._in_packet['remaining_length'] != 2:
            return MQTT_ERR_PROTOCOL

        mid, = struct.unpack("!H", self._in_packet['packet'])
        self._easy_log(MQTT_LOG_DEBUG, "Received PUBREC (Mid: %d)", mid)

        with self._out_message_mutex:
            for m in self._out_messages:
                if m.mid == mid:
                    m.state = mqtt_ms_wait_for_pubcomp
                    m.timestamp = time_func()
                    return self._send_pubrel(mid, False)

        return MQTT_ERR_SUCCESS

    def _handle_unsuback(self):
        if self._in_packet['remaining_length'] != 2:
            return MQTT_ERR_PROTOCOL

        mid, = struct.unpack("!H", self._in_packet['packet'])
        self._easy_log(MQTT_LOG_DEBUG, "Received UNSUBACK (Mid: %d)", mid)
        with self._callback_mutex:
            if self.on_unsubscribe:
                with self._in_callback:
                    self.on_unsubscribe(self, self._userdata, mid)
        return MQTT_ERR_SUCCESS

    def _do_on_publish(self, idx, mid):
        with self._callback_mutex:
            if self.on_publish:
                with self._in_callback:
                    self.on_publish(self, self._userdata, mid)

        msg = self._out_messages.pop(idx)
        if msg.qos > 0:
            self._inflight_messages -= 1
            if self._max_inflight_messages > 0:
                rc = self._update_inflight()
                if rc != MQTT_ERR_SUCCESS:
                    return rc
        msg.info._set_as_published()
        return MQTT_ERR_SUCCESS

    def _handle_pubackcomp(self, cmd):
        if self._in_packet['remaining_length'] != 2:
            return MQTT_ERR_PROTOCOL

        mid, = struct.unpack("!H", self._in_packet['packet'])
        self._easy_log(MQTT_LOG_DEBUG, "Received %s (Mid: %d)", cmd, mid)

        with self._out_message_mutex:
            for i in range(len(self._out_messages)):
                try:
                    if self._out_messages[i].mid == mid:
                        # Only inform the client the message has been sent once.
                        rc = self._do_on_publish(i, mid)
                        return rc
                except IndexError:
                    # Have removed item so i>count.
                    # Not really an error.
                    pass

        return MQTT_ERR_SUCCESS

    def _handle_on_message(self, message):
        matched = False
        with self._callback_mutex:
            try:
                topic = message.topic
            except UnicodeDecodeError:
                topic = None

            if topic is not None:
                for callback in self._on_message_filtered.iter_match(message.topic):
                    with self._in_callback:
                        callback(self, self._userdata, message)
                    matched = True

            if matched == False and self.on_message:
                with self._in_callback:
                    self.on_message(self, self._userdata, message)

    def _thread_main(self):
        self.loop_forever(retry_first_connection=True)

    def _reconnect_wait(self):
        # See reconnect_delay_set for details
        now = time_func()
        with self._reconnect_delay_mutex:
            if self._reconnect_delay is None:
                self._reconnect_delay = self._reconnect_min_delay
            else:
                self._reconnect_delay = min(
                    self._reconnect_delay * 2,
                    self._reconnect_max_delay,
                )

            target_time = now + self._reconnect_delay

        remaining = target_time - now
        while (self._state != mqtt_cs_disconnecting
                and not self._thread_terminate
                and remaining > 0):

            time.sleep(min(remaining, 1))
            remaining = target_time - time_func()


# Compatibility class for easy porting from mosquitto.py.
class Mosquitto(Client):
    def __init__(self, client_id="", clean_session=True, userdata=None):
        super(Mosquitto, self).__init__(client_id, clean_session, userdata)


class WebsocketWrapper(object):
    OPCODE_CONTINUATION = 0x0
    OPCODE_TEXT = 0x1
    OPCODE_BINARY = 0x2
    OPCODE_CONNCLOSE = 0x8
    OPCODE_PING = 0x9
    OPCODE_PONG = 0xa

    def __init__(self, socket, host, port, is_ssl, path, extra_headers):

        self.connected = False

        self._ssl = is_ssl
        self._host = host
        self._port = port
        self._socket = socket
        self._path = path

        self._sendbuffer = bytearray()
        self._readbuffer = bytearray()

        self._requested_size = 0
        self._payload_head = 0
        self._readbuffer_head = 0

        self._do_handshake(extra_headers)

    def __del__(self):

        self._sendbuffer = None
        self._readbuffer = None

    def _do_handshake(self, extra_headers):

        sec_websocket_key = uuid.uuid4().bytes
        sec_websocket_key = base64.b64encode(sec_websocket_key)

        websocket_headers = {
            "Host": "{self._host:s}:{self._port:d}".format(self=self),
            "Upgrade": "websocket",
            "Connection": "Upgrade",
            "Origin": "https://{self._host:s}:{self._port:d}".format(self=self),
            "Sec-WebSocket-Key": sec_websocket_key.decode("utf8"),
            "Sec-Websocket-Version": "13",
            "Sec-Websocket-Protocol": "mqtt",
        }

        # This is checked in ws_set_options so it will either be None, a
        # dictionary, or a callable
        if isinstance(extra_headers, dict):
            websocket_headers.update(extra_headers)
        elif callable(extra_headers):
            websocket_headers = extra_headers(websocket_headers)

        header = "\r\n".join([
            "GET {self._path} HTTP/1.1".format(self=self),
            "\r\n".join("{}: {}".format(i, j) for i, j in websocket_headers.items()),
            "\r\n",
        ]).encode("utf8")

        self._socket.send(header)

        has_secret = False
        has_upgrade = False

        while True:
            # read HTTP response header as lines
            byte = self._socket.recv(1)

            self._readbuffer.extend(byte)

            # line end
            if byte == b"\n":
                if len(self._readbuffer) > 2:
                    # check upgrade
                    if b"connection" in str(self._readbuffer).lower().encode('utf-8'):
                        if b"upgrade" not in str(self._readbuffer).lower().encode('utf-8'):
                            raise WebsocketConnectionError("WebSocket handshake error, connection not upgraded")
                        else:
                            has_upgrade = True

                    # check key hash
                    if b"sec-websocket-accept" in str(self._readbuffer).lower().encode('utf-8'):
                        GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

                        server_hash = self._readbuffer.decode('utf-8').split(": ", 1)[1]
                        server_hash = server_hash.strip().encode('utf-8')

                        client_hash = sec_websocket_key.decode('utf-8') + GUID
                        client_hash = hashlib.sha1(client_hash.encode('utf-8'))
                        client_hash = base64.b64encode(client_hash.digest())

                        if server_hash != client_hash:
                            raise WebsocketConnectionError("WebSocket handshake error, invalid secret key")
                        else:
                            has_secret = True
                else:
                    # ending linebreak
                    break

                # reset linebuffer
                self._readbuffer = bytearray()

            # connection reset
            elif not byte:
                raise WebsocketConnectionError("WebSocket handshake error")

        if not has_upgrade or not has_secret:
            raise WebsocketConnectionError("WebSocket handshake error")

        self._readbuffer = bytearray()
        self.connected = True

    def _create_frame(self, opcode, data, do_masking=1):

        header = bytearray()
        length = len(data)
        mask_key = bytearray(
            [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)])
        mask_flag = do_masking

        # 1 << 7 is the final flag, we don't send continuated data
        header.append(1 << 7 | opcode)

        if length < 126:
            header.append(mask_flag << 7 | length)

        elif length < 32768:
            header.append(mask_flag << 7 | 126)
            header += struct.pack("!H", length)

        elif length < 0x8000000000000001:
            header.append(mask_flag << 7 | 127)
            header += struct.pack("!Q", length)

        else:
            raise ValueError("Maximum payload size is 2^63")

        if mask_flag == 1:
            for index in range(length):
                data[index] ^= mask_key[index % 4]
            data = mask_key + data

        return header + data

    def _buffered_read(self, length):

        # try to recv and strore needed bytes
        wanted_bytes = length - (len(self._readbuffer) - self._readbuffer_head)
        if wanted_bytes > 0:

            data = self._socket.recv(wanted_bytes)

            if not data:
                raise socket.error(errno.ECONNABORTED, 0)
            else:
                self._readbuffer.extend(data)

            if len(data) < wanted_bytes:
                raise socket.error(errno.EAGAIN, 0)

        self._readbuffer_head += length
        return self._readbuffer[self._readbuffer_head - length:self._readbuffer_head]

    def _recv_impl(self, length):

        # try to decode websocket payload part from data
        try:

            self._readbuffer_head = 0

            result = None

            chunk_startindex = self._payload_head
            chunk_endindex = self._payload_head + length

            header1 = self._buffered_read(1)
            header2 = self._buffered_read(1)

            opcode = (header1[0] & 0x0f)
            maskbit = (header2[0] & 0x80) == 0x80
            lengthbits = (header2[0] & 0x7f)
            payload_length = lengthbits
            mask_key = None

            # read length
            if lengthbits == 0x7e:

                value = self._buffered_read(2)
                payload_length, = struct.unpack("!H", value)

            elif lengthbits == 0x7f:

                value = self._buffered_read(8)
                payload_length, = struct.unpack("!Q", value)

            # read mask
            if maskbit:
                mask_key = self._buffered_read(4)

            # if frame payload is shorter than the requested data, read only the possible part
            readindex = chunk_endindex
            if payload_length < readindex:
                readindex = payload_length

            if readindex > 0:
                # get payload chunk
                payload = self._buffered_read(readindex)

                # unmask only the needed part
                if maskbit:
                    for index in range(chunk_startindex, readindex):
                        payload[index] ^= mask_key[index % 4]

                result = payload[chunk_startindex:readindex]
                self._payload_head = readindex
            else:
                payload = bytearray()

            # check if full frame arrived and reset readbuffer and payloadhead if needed
            if readindex == payload_length:
                self._readbuffer = bytearray()
                self._payload_head = 0

                # respond to non-binary opcodes, their arrival is not guaranteed beacause of non-blocking sockets
                if opcode == WebsocketWrapper.OPCODE_CONNCLOSE:
                    frame = self._create_frame(WebsocketWrapper.OPCODE_CONNCLOSE, payload, 0)
                    self._socket.send(frame)

                if opcode == WebsocketWrapper.OPCODE_PING:
                    frame = self._create_frame(WebsocketWrapper.OPCODE_PONG, payload, 0)
                    self._socket.send(frame)

            if opcode == WebsocketWrapper.OPCODE_BINARY:
                return result
            else:
                raise socket.error(errno.EAGAIN, 0)

        except socket.error as err:

            if err.errno == errno.ECONNABORTED:
                self.connected = False
                return b''
            else:
                # no more data
                raise

    def _send_impl(self, data):

        # if previous frame was sent successfully
        if len(self._sendbuffer) == 0:
            # create websocket frame
            frame = self._create_frame(WebsocketWrapper.OPCODE_BINARY, bytearray(data))
            self._sendbuffer.extend(frame)
            self._requested_size = len(data)

        # try to write out as much as possible
        length = self._socket.send(self._sendbuffer)

        self._sendbuffer = self._sendbuffer[length:]

        if len(self._sendbuffer) == 0:
            # buffer sent out completely, return with payload's size
            return self._requested_size
        else:
            # couldn't send whole data, request the same data again with 0 as sent length
            return 0

    def recv(self, length):
        return self._recv_impl(length)

    def read(self, length):
        return self._recv_impl(length)

    def send(self, data):
        return self._send_impl(data)

    def write(self, data):
        return self._send_impl(data)

    def close(self):
        self._socket.close()

    def fileno(self):
        return self._socket.fileno()

    def pending(self):
        # Fix for bug #131: a SSL socket may still have data available
        # for reading without select() being aware of it.
        if self._ssl:
            return self._socket.pending()
        else:
            # normal socket rely only on select()
            return 0

    def setblocking(self, flag):
        self._socket.setblocking(flag)
