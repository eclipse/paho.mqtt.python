# helpers

This module provides some helper functions to allow straightforward publishing
of messages in a one-shot manner. In other words, they are useful for the
situation where you have a single/multiple messages you want to publish to a
broker, then disconnect and nothing else is required.

### paho.mqtt.publish.multiple(msgs: MessagesList, hostname: str = 'localhost', port: int = 1883, client_id: str = '', keepalive: int = 60, will: MessageDict | None = None, auth: AuthParameter | None = None, tls: TLSParameter | None = None, protocol: int = MQTTProtocolVersion.MQTTv311, transport: Literal['tcp', 'websockets'] = 'tcp', proxy_args: Any | None = None)

Publish multiple messages to a broker, then disconnect cleanly.

This function creates an MQTT client, connects to a broker and publishes a
list of messages. Once the messages have been delivered, it disconnects
cleanly from the broker.

* **Parameters:**
  * **msgs** – 

    a list of messages to publish. Each message is either a dict or a
    tuple.

    If a dict, only the topic must be present. Default values will be
    used for any missing arguments. The dict must be of the form:

    msg = {‘topic’:”<topic>”, ‘payload’:”<payload>”, ‘qos’:<qos>,
    ‘retain’:<retain>}
    topic must be present and may not be empty.
    If payload is “”, None or not present then a zero length payload
    will be published.
    If qos is not present, the default of 0 is used.
    If retain is not present, the default of False is used.

    If a tuple, then it must be of the form:
    (“<topic>”, “<payload>”, qos, retain)
  * **hostname** (*str*) – the address of the broker to connect to.
    Defaults to localhost.
  * **port** (*int*) – the port to connect to the broker on. Defaults to 1883.
  * **client_id** (*str*) – the MQTT client id to use. If “” or None, the Paho library will
    generate a client id automatically.
  * **keepalive** (*int*) – the keepalive timeout value for the client. Defaults to 60
    seconds.
  * **will** – a dict containing will parameters for the client: will = {‘topic’:
    “<topic>”, ‘payload’:”<payload”>, ‘qos’:<qos>, ‘retain’:<retain>}.
    Topic is required, all other parameters are optional and will
    default to None, 0 and False respectively.
    Defaults to None, which indicates no will should be used.
  * **auth** – a dict containing authentication parameters for the client:
    auth = {‘username’:”<username>”, ‘password’:”<password>”}
    Username is required, password is optional and will default to None
    if not provided.
    Defaults to None, which indicates no authentication is to be used.
  * **tls** – a dict containing TLS configuration parameters for the client:
    dict = {‘ca_certs’:”<ca_certs>”, ‘certfile’:”<certfile>”,
    ‘keyfile’:”<keyfile>”, ‘tls_version’:”<tls_version>”,
    ‘ciphers’:”<ciphers”>, ‘insecure’:”<bool>”}
    ca_certs is required, all other parameters are optional and will
    default to None if not provided, which results in the client using
    the default behaviour - see the paho.mqtt.client documentation.
    Alternatively, tls input can be an SSLContext object, which will be
    processed using the tls_set_context method.
    Defaults to None, which indicates that TLS should not be used.
  * **transport** (*str*) – set to “tcp” to use the default setting of transport which is
    raw TCP. Set to “websockets” to use WebSockets as the transport.
  * **proxy_args** – a dictionary that will be given to the client.

### paho.mqtt.publish.single(topic: str, payload: paho.PayloadType = None, qos: int = 0, retain: bool = False, hostname: str = 'localhost', port: int = 1883, client_id: str = '', keepalive: int = 60, will: MessageDict | None = None, auth: AuthParameter | None = None, tls: TLSParameter | None = None, protocol: int = MQTTProtocolVersion.MQTTv311, transport: Literal['tcp', 'websockets'] = 'tcp', proxy_args: Any | None = None)

Publish a single message to a broker, then disconnect cleanly.

This function creates an MQTT client, connects to a broker and publishes a
single message. Once the message has been delivered, it disconnects cleanly
from the broker.

* **Parameters:**
  * **topic** (*str*) – the only required argument must be the topic string to which the
    payload will be published.
  * **payload** – the payload to be published. If “” or None, a zero length payload
    will be published.
  * **qos** (*int*) – the qos to use when publishing,  default to 0.
  * **retain** (*bool*) – set the message to be retained (True) or not (False).
  * **hostname** (*str*) – the address of the broker to connect to.
    Defaults to localhost.
  * **port** (*int*) – the port to connect to the broker on. Defaults to 1883.
  * **client_id** (*str*) – the MQTT client id to use. If “” or None, the Paho library will
    generate a client id automatically.
  * **keepalive** (*int*) – the keepalive timeout value for the client. Defaults to 60
    seconds.
  * **will** – a dict containing will parameters for the client: will = {‘topic’:
    “<topic>”, ‘payload’:”<payload”>, ‘qos’:<qos>, ‘retain’:<retain>}.
    Topic is required, all other parameters are optional and will
    default to None, 0 and False respectively.
    Defaults to None, which indicates no will should be used.
  * **auth** – a dict containing authentication parameters for the client:
    Username is required, password is optional and will default to None
    auth = {‘username’:”<username>”, ‘password’:”<password>”}
    if not provided.
    Defaults to None, which indicates no authentication is to be used.
  * **tls** – a dict containing TLS configuration parameters for the client:
    dict = {‘ca_certs’:”<ca_certs>”, ‘certfile’:”<certfile>”,
    ‘keyfile’:”<keyfile>”, ‘tls_version’:”<tls_version>”,
    ‘ciphers’:”<ciphers”>, ‘insecure’:”<bool>”}
    ca_certs is required, all other parameters are optional and will
    default to None if not provided, which results in the client using
    the default behaviour - see the paho.mqtt.client documentation.
    Defaults to None, which indicates that TLS should not be used.
    Alternatively, tls input can be an SSLContext object, which will be
    processed using the tls_set_context method.
  * **transport** – set to “tcp” to use the default setting of transport which is
    raw TCP. Set to “websockets” to use WebSockets as the transport.
  * **proxy_args** – a dictionary that will be given to the client.

<a id="module-paho.mqtt.subscribe"></a>

This module provides some helper functions to allow straightforward subscribing
to topics and retrieving messages. The two functions are simple(), which
returns one or messages matching a set of topics, and callback() which allows
you to pass a callback for processing of messages.

### paho.mqtt.subscribe.callback(callback, topics, qos=0, userdata=None, hostname='localhost', port=1883, client_id='', keepalive=60, will=None, auth=None, tls=None, protocol=MQTTProtocolVersion.MQTTv311, transport='tcp', clean_session=True, proxy_args=None)

Subscribe to a list of topics and process them in a callback function.

This function creates an MQTT client, connects to a broker and subscribes
to a list of topics. Incoming messages are processed by the user provided
callback.  This is a blocking function and will never return.

* **Parameters:**
  * **callback** – function with the same signature as [`on_message`](client.md#paho.mqtt.client.Client.on_message) for
    processing the messages received.
  * **topics** – either a string containing a single topic to subscribe to, or a
    list of topics to subscribe to.
  * **qos** (*int*) – the qos to use when subscribing. This is applied to all topics.
  * **userdata** – passed to the callback
  * **hostname** (*str*) – the address of the broker to connect to.
    Defaults to localhost.
  * **port** (*int*) – the port to connect to the broker on. Defaults to 1883.
  * **client_id** (*str*) – the MQTT client id to use. If “” or None, the Paho library will
    generate a client id automatically.
  * **keepalive** (*int*) – the keepalive timeout value for the client. Defaults to 60
    seconds.
  * **will** – 

    a dict containing will parameters for the client: will = {‘topic’:
    “<topic>”, ‘payload’:”<payload”>, ‘qos’:<qos>, ‘retain’:<retain>}.
    Topic is required, all other parameters are optional and will
    default to None, 0 and False respectively.

    Defaults to None, which indicates no will should be used.
  * **auth** – a dict containing authentication parameters for the client:
    auth = {‘username’:”<username>”, ‘password’:”<password>”}
    Username is required, password is optional and will default to None
    if not provided.
    Defaults to None, which indicates no authentication is to be used.
  * **tls** – a dict containing TLS configuration parameters for the client:
    dict = {‘ca_certs’:”<ca_certs>”, ‘certfile’:”<certfile>”,
    ‘keyfile’:”<keyfile>”, ‘tls_version’:”<tls_version>”,
    ‘ciphers’:”<ciphers”>, ‘insecure’:”<bool>”}
    ca_certs is required, all other parameters are optional and will
    default to None if not provided, which results in the client using
    the default behaviour - see the paho.mqtt.client documentation.
    Alternatively, tls input can be an SSLContext object, which will be
    processed using the tls_set_context method.
    Defaults to None, which indicates that TLS should not be used.
  * **transport** (*str*) – set to “tcp” to use the default setting of transport which is
    raw TCP. Set to “websockets” to use WebSockets as the transport.
  * **clean_session** – a boolean that determines the client type. If True,
    the broker will remove all information about this client
    when it disconnects. If False, the client is a persistent
    client and subscription information and queued messages
    will be retained when the client disconnects.
    Defaults to True.
  * **proxy_args** – a dictionary that will be given to the client.

### paho.mqtt.subscribe.simple(topics, qos=0, msg_count=1, retained=True, hostname='localhost', port=1883, client_id='', keepalive=60, will=None, auth=None, tls=None, protocol=MQTTProtocolVersion.MQTTv311, transport='tcp', clean_session=True, proxy_args=None)

Subscribe to a list of topics and return msg_count messages.

This function creates an MQTT client, connects to a broker and subscribes
to a list of topics. Once “msg_count” messages have been received, it
disconnects cleanly from the broker and returns the messages.

* **Parameters:**
  * **topics** – either a string containing a single topic to subscribe to, or a
    list of topics to subscribe to.
  * **qos** (*int*) – the qos to use when subscribing. This is applied to all topics.
  * **msg_count** (*int*) – the number of messages to retrieve from the broker.
    if msg_count == 1 then a single MQTTMessage will be returned.
    if msg_count > 1 then a list of MQTTMessages will be returned.
  * **retained** (*bool*) – If set to True, retained messages will be processed the same as
    non-retained messages. If set to False, retained messages will
    be ignored. This means that with retained=False and msg_count=1,
    the function will return the first message received that does
    not have the retained flag set.
  * **hostname** (*str*) – the address of the broker to connect to.
    Defaults to localhost.
  * **port** (*int*) – the port to connect to the broker on. Defaults to 1883.
  * **client_id** (*str*) – the MQTT client id to use. If “” or None, the Paho library will
    generate a client id automatically.
  * **keepalive** (*int*) – the keepalive timeout value for the client. Defaults to 60
    seconds.
  * **will** – a dict containing will parameters for the client: will = {‘topic’:
    “<topic>”, ‘payload’:”<payload”>, ‘qos’:<qos>, ‘retain’:<retain>}.
    Topic is required, all other parameters are optional and will
    default to None, 0 and False respectively.
    Defaults to None, which indicates no will should be used.
  * **auth** – a dict containing authentication parameters for the client:
    auth = {‘username’:”<username>”, ‘password’:”<password>”}
    Username is required, password is optional and will default to None
    if not provided.
    Defaults to None, which indicates no authentication is to be used.
  * **tls** – a dict containing TLS configuration parameters for the client:
    dict = {‘ca_certs’:”<ca_certs>”, ‘certfile’:”<certfile>”,
    ‘keyfile’:”<keyfile>”, ‘tls_version’:”<tls_version>”,
    ‘ciphers’:”<ciphers”>, ‘insecure’:”<bool>”}
    ca_certs is required, all other parameters are optional and will
    default to None if not provided, which results in the client using
    the default behaviour - see the paho.mqtt.client documentation.
    Alternatively, tls input can be an SSLContext object, which will be
    processed using the tls_set_context method.
    Defaults to None, which indicates that TLS should not be used.
  * **protocol** – the MQTT protocol version to use. Defaults to MQTTv311.
  * **transport** – set to “tcp” to use the default setting of transport which is
    raw TCP. Set to “websockets” to use WebSockets as the transport.
  * **clean_session** – a boolean that determines the client type. If True,
    the broker will remove all information about this client
    when it disconnects. If False, the client is a persistent
    client and subscription information and queued messages
    will be retained when the client disconnects.
    Defaults to True. If protocol is MQTTv50, clean_session
    is ignored.
  * **proxy_args** – a dictionary that will be given to the client.
