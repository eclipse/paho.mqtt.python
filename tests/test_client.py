import os
import sys
import inspect
from collections import OrderedDict

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
class TestWebsocketHeaders(object):
    def setup(self):
        # A good response from the server
        self.response_headers = OrderedDict({
            "Upgrade": "websocket",
            "Connection": "Upgrade",
            # This is wrong, but tests should override it
            "Sec-WebSocket-Accept": "3tkwofepkwfpoek",
            "Sec-WebSocket-Protocol": "chat",
        })

    def _get_response_headers(self):
        """ Get a websocket response header from the self.response_headers """

        # From client.py
        header = "\r\n".join([
            "HTTP/1.1 101 Switching Protocols",
            "\r\n".join("{}: {}".format(i, j) for i, j in self.response_headers.items()),
            "\r\n",
        ]).encode("utf8")

        return header

    def test_unexpected_response(self, proto_ver, proto_name, fake_websocket_broker):
        """ Server doesn't respond with expected headers """

        mqttc = client.Client(
            "test_unexpected_response",
            protocol=proto_ver,
            transport="websockets"
            )

        mqttc.ws_set_options(
            headers={"Authorization": "test123"},
        )

        with fake_websocket_broker.serve("not real\n"):
            with pytest.raises(WebsocketConnectionError) as exc:
                mqttc.connect("localhost", 1888, keepalive=10)

        assert str(exc.value) == "WebSocket handshake error"

    def test_no_upgrade(self, proto_ver, proto_name, fake_websocket_broker):
        """ Server doesn't respond with 'connection: upgrade' """

        mqttc = client.Client(
            "test_no_upgrade",
            protocol=proto_ver,
            transport="websockets"
            )

        mqttc.ws_set_options(
            headers={"Authorization": "test123"},
        )

        self.response_headers["Connection"] = "bad"
        response = self._get_response_headers()

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

        mqttc.ws_set_options(
            headers={"Authorization": "test123"},
        )

        response = self._get_response_headers()

        with fake_websocket_broker.serve(response):
            with pytest.raises(WebsocketConnectionError) as exc:
                mqttc.connect("localhost", 1888, keepalive=10)

        assert str(exc.value) == "WebSocket handshake error, invalid secret key"

    # TODO test bad path, with normally successful connection
