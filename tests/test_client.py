import os
import sys
import base64
import re
import inspect
import hashlib
from collections import OrderedDict
from six.moves import socketserver

import pytest
import paho.mqtt.client as client
from paho.mqtt.client import WebsocketConnectionError

# From http://stackoverflow.com/questions/279237/python-import-a-module-from-a-folder
cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(
                inspect.getfile(inspect.currentframe()))[0],
            '..', 'test')))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)
import paho_test

# Import test fixture
from testsupport.broker import fake_broker, fake_websocket_broker


@pytest.mark.parametrize("proto_ver,proto_name", [
    (client.MQTTv31, "MQIsdp"),
    (client.MQTTv311, "MQTT"),
])
class Test_connect(object):
    """
    Tests on connect/disconnect behaviour of the client
    """

    def test_01_con_discon_success(self, proto_ver, proto_name, fake_broker):
        mqttc = client.Client(
            "01-con-discon-success", protocol=proto_ver)

        def on_connect(mqttc, obj, flags, rc):
            assert rc == 0
            mqttc.disconnect()

        mqttc.on_connect = on_connect

        mqttc.connect_async("localhost", 1888)
        mqttc.loop_start()

        try:
            fake_broker.start()

            connect_packet = paho_test.gen_connect(
                "01-con-discon-success", keepalive=60,
                proto_name=proto_name, proto_ver=proto_ver)
            packet_in = fake_broker.receive_packet(1000)
            assert packet_in  # Check connection was not closed
            assert packet_in == connect_packet

            connack_packet = paho_test.gen_connack(rc=0)
            count = fake_broker.send_packet(connack_packet)
            assert count  # Check connection was not closed
            assert count == len(connack_packet)

            disconnect_packet = paho_test.gen_disconnect()
            packet_in = fake_broker.receive_packet(1000)
            assert packet_in  # Check connection was not closed
            assert packet_in == disconnect_packet

        finally:
            mqttc.loop_stop()

        packet_in = fake_broker.receive_packet(1)
        assert not packet_in  # Check connection is closed

    def test_01_con_failure_rc(self, proto_ver, proto_name, fake_broker):
        mqttc = client.Client(
            "01-con-failure-rc", protocol=proto_ver)

        def on_connect(mqttc, obj, flags, rc):
            assert rc == 1
            mqttc.disconnect()

        mqttc.on_connect = on_connect

        mqttc.connect_async("localhost", 1888)
        mqttc.loop_start()

        try:
            fake_broker.start()

            connect_packet = paho_test.gen_connect(
                "01-con-failure-rc", keepalive=60,
                proto_name=proto_name, proto_ver=proto_ver)
            packet_in = fake_broker.receive_packet(1000)
            assert packet_in  # Check connection was not closed
            assert packet_in == connect_packet

            connack_packet = paho_test.gen_connack(rc=1)
            count = fake_broker.send_packet(connack_packet)
            assert count  # Check connection was not closed
            assert count == len(connack_packet)

            packet_in = fake_broker.receive_packet(1)
            assert not packet_in  # Check connection is closed

        finally:
            mqttc.loop_stop()


class TestPublishBroker2Client(object):

    @pytest.mark.skipif(sys.version_info < (3, 0), reason="Need Python3")
    def test_invalid_utf8_topic(self, fake_broker):
        mqttc = client.Client("client-id")

        def on_message(client, userdata, msg):
            with pytest.raises(UnicodeDecodeError):
                msg.topic
            client.disconnect()

        mqttc.on_message = on_message

        mqttc.connect_async("localhost", 1888)
        mqttc.loop_start()

        try:
            fake_broker.start()

            connect_packet = paho_test.gen_connect("client-id")
            packet_in = fake_broker.receive_packet(len(connect_packet))
            assert packet_in  # Check connection was not closed
            assert packet_in == connect_packet

            connack_packet = paho_test.gen_connack(rc=0)
            count = fake_broker.send_packet(connack_packet)
            assert count  # Check connection was not closed
            assert count == len(connack_packet)

            publish_packet = paho_test.gen_publish(b"\xff", qos=0)
            count = fake_broker.send_packet(publish_packet)
            assert count  # Check connection was not closed
            assert count == len(publish_packet)

            disconnect_packet = paho_test.gen_disconnect()
            packet_in = fake_broker.receive_packet(len(disconnect_packet))
            assert packet_in  # Check connection was not closed
            assert packet_in == disconnect_packet

        finally:
            mqttc.loop_stop()

        packet_in = fake_broker.receive_packet(1)
        assert not packet_in  # Check connection is closed


@pytest.mark.parametrize("proto_ver,proto_name", [
    (client.MQTTv31, "MQIsdp"),
    (client.MQTTv311, "MQTT"),
])
class TestInvalidWebsocketResponse(object):
    def test_unexpected_response(self, proto_ver, proto_name, fake_websocket_broker):
        """ Server responds with a valid code, but it's not what the client expected """

        mqttc = client.Client(
            "test_unexpected_response",
            protocol=proto_ver,
            transport="websockets"
            )

        with fake_websocket_broker.serve("200 OK\n"):
            with pytest.raises(WebsocketConnectionError) as exc:
                mqttc.connect("localhost", 1888, keepalive=10)

        assert str(exc.value) == "WebSocket handshake error"


@pytest.mark.parametrize("proto_ver,proto_name", [
    (client.MQTTv31, "MQIsdp"),
    (client.MQTTv311, "MQTT"),
])
class TestBadWebsocketHeaders(object):
    """ Testing for basic functionality in checking for headers """

    def setup(self):
        # A good response from the server
        self.response_headers = OrderedDict([
            ("Upgrade", "websocket"),
            ("Connection", "Upgrade"),
            ("Sec-WebSocket-Accept", "badwebsocketkey"),
            ("Sec-WebSocket-Protocol", "chat"),
        ])

    def _get_basic_handler(self):
        """ Get a basic BaseRequestHandler which returns the information in
        self._response_headers
        """

        # From client.py
        response = "\r\n".join([
            "HTTP/1.1 101 Switching Protocols",
            "\r\n".join("{}: {}".format(i, j) for i, j in self.response_headers.items()),
            "\r\n",
        ]).encode("utf8")

        class WebsocketHandler(socketserver.BaseRequestHandler):
            def handle(_self):
                self.data = _self.request.recv(1024).strip()
                print("Received '{:s}'".format(self.data.decode("utf8")))
                # Respond with data passed in to serve()
                _self.request.sendall(response)

        return WebsocketHandler

    def test_no_upgrade(self, proto_ver, proto_name, fake_websocket_broker):
        """ Server doesn't respond with 'connection: upgrade' """

        mqttc = client.Client(
            "test_no_upgrade",
            protocol=proto_ver,
            transport="websockets"
            )

        self.response_headers["Connection"] = "bad"
        response = self._get_basic_handler()

        with fake_websocket_broker.serve(response):
            with pytest.raises(WebsocketConnectionError) as exc:
                mqttc.connect("localhost", 1888, keepalive=10)

        assert str(exc.value) == "WebSocket handshake error, connection not upgraded"

    def test_bad_secret_key(self, proto_ver, proto_name, fake_websocket_broker):
        """ Server doesn't give anything after connection: upgrade """

        mqttc = client.Client(
            "test_bad_secret_key",
            protocol=proto_ver,
            transport="websockets"
            )

        response = self._get_basic_handler()

        with fake_websocket_broker.serve(response):
            with pytest.raises(WebsocketConnectionError) as exc:
                mqttc.connect("localhost", 1888, keepalive=10)

        assert str(exc.value) == "WebSocket handshake error, invalid secret key"


@pytest.mark.parametrize("proto_ver,proto_name", [
    (client.MQTTv31, "MQIsdp"),
    (client.MQTTv311, "MQTT"),
])
class TestValidHeaders(object):
    """ Testing for functionality in request/response headers """

    def setup(self):
        # A good response from the server
        self.response_headers = OrderedDict([
            ("Upgrade", "websocket"),
            ("Connection", "Upgrade"),
            ("Sec-WebSocket-Accept", "testwebsocketkey"),
            ("Sec-WebSocket-Protocol", "chat"),
        ])

    def _get_callback_handler(self, check_request=None):
        """ Get a basic BaseRequestHandler which returns the information in
        self._response_headers
        """

        class WebsocketHandler(socketserver.BaseRequestHandler):
            def handle(_self):
                self.data = _self.request.recv(1024).strip()
                print("Received '{:s}'".format(self.data.decode("utf8")))

                decoded = self.data.decode("utf8")

                if check_request is not None:
                    check_request(decoded)

                # Create server hash
                GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
                key = re.search("sec-websocket-key: ([A-Za-z0-9+/=]*)", decoded, re.IGNORECASE).group(1)

                to_hash = "{:s}{:s}".format(key, GUID)
                hashed = hashlib.sha1(to_hash.encode("utf8"))
                encoded = base64.b64encode(hashed.digest()).decode("utf8")

                self.response_headers["Sec-WebSocket-Accept"] = encoded

                # Respond with the correct hash
                response = "\r\n".join([
                    "HTTP/1.1 101 Switching Protocols",
                    "\r\n".join("{}: {}".format(i, j) for i, j in self.response_headers.items()),
                    "\r\n",
                ]).encode("utf8")

                _self.request.sendall(response)

        return WebsocketHandler

    def test_successful_connection(self, proto_ver, proto_name, fake_websocket_broker):
        """ Connect successfully, on correct path """

        mqttc = client.Client(
            "test_successful_connection",
            protocol=proto_ver,
            transport="websockets"
            )

        response = self._get_callback_handler()

        with fake_websocket_broker.serve(response):
            mqttc.connect("localhost", 1888, keepalive=10)

            mqttc.disconnect()

    @pytest.mark.parametrize("mqtt_path", [
        "/mqtt"
        "/special",
        None,
    ])
    def test_correct_path(self, proto_ver, proto_name, fake_websocket_broker, mqtt_path):
        """ Make sure it can connect on user specified paths """

        mqttc = client.Client(
            "test_correct_path",
            protocol=proto_ver,
            transport="websockets"
            )

        mqttc.ws_set_options(
            path=mqtt_path,
        )

        def create_response_hash(decoded):
            # Make sure it connects to the right path
            assert re.search("GET {:s} HTTP/1.1".format(mqtt_path), decoded, re.IGNORECASE) is not None

        response = self._get_callback_handler()

        with fake_websocket_broker.serve(response):
            mqttc.connect("localhost", 1888, keepalive=10)

            mqttc.disconnect()

    @pytest.mark.parametrize("auth_headers", [
        {"Authorization": "test123"},
        {"Authorization": "test123", "auth2": "abcdef"},
        None,
    ])
    def test_correct_auth(self, proto_ver, proto_name, fake_websocket_broker, auth_headers):
        """ Make sure it can connect on user specified paths """

        mqttc = client.Client(
            "test_correct_path",
            protocol=proto_ver,
            transport="websockets"
            )

        mqttc.ws_set_options(
            headers=auth_headers,
        )

        def create_response_hash(decoded):
            # Make sure it connects to the right path
            for h in auth_headers:
                assert re.search("{:s}: {:s}".format(h, auth_headers[h]), decoded, re.IGNORECASE) is not None

        response = self._get_callback_handler()

        with fake_websocket_broker.serve(response):
            mqttc.connect("localhost", 1888, keepalive=10)

            mqttc.disconnect()
