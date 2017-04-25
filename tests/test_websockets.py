import base64
import re
import hashlib
from collections import OrderedDict

from six.moves import socketserver
import pytest
import paho.mqtt.client as client

from paho.mqtt.client import WebsocketConnectionError
from testsupport.broker import fake_websocket_broker


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

