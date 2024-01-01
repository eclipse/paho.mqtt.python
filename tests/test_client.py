import time
import unicodedata

import paho.mqtt.client as client
import pytest
from paho.mqtt.reasoncodes import ReasonCodes

import tests.paho_test as paho_test

# Import test fixture
from tests.testsupport.broker import fake_broker  # noqa: F401


@pytest.mark.parametrize("proto_ver", [
    (client.MQTTv31),
    (client.MQTTv311),
])
class Test_connect:
    """
    Tests on connect/disconnect behaviour of the client
    """

    def test_01_con_discon_success(self, proto_ver, fake_broker):
        mqttc = client.Client(
            "01-con-discon-success", protocol=proto_ver)

        def on_connect(mqttc, obj, flags, rc):
            assert rc == 0
            mqttc.disconnect()

        mqttc.on_connect = on_connect

        mqttc.connect_async("localhost", fake_broker.port)
        mqttc.loop_start()

        try:
            fake_broker.start()

            connect_packet = paho_test.gen_connect(
                "01-con-discon-success", keepalive=60,
                proto_ver=proto_ver)
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

    def test_01_con_failure_rc(self, proto_ver, fake_broker):
        mqttc = client.Client(
            "01-con-failure-rc", protocol=proto_ver)

        def on_connect(mqttc, obj, flags, rc):
            assert rc == 1

        mqttc.on_connect = on_connect

        mqttc.connect_async("localhost", fake_broker.port)
        mqttc.loop_start()

        try:
            fake_broker.start()

            connect_packet = paho_test.gen_connect(
                "01-con-failure-rc", keepalive=60,
                proto_ver=proto_ver)
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


class Test_connect_v5:
    """
    Tests on connect/disconnect behaviour of the client with MQTTv5
    """

    def test_01_broker_no_support(self, fake_broker):
        mqttc = client.Client(
            "01-broker-no-support", protocol=client.MQTTv5)

        def on_connect(mqttc, obj, flags, reason, properties):
            assert reason == 132
            assert reason == ReasonCodes(client.CONNACK >> 4, aName="Unsupported protocol version")
            mqttc.disconnect()

        mqttc.on_connect = on_connect

        mqttc.connect_async("localhost", fake_broker.port)
        mqttc.loop_start()

        try:
            fake_broker.start()

            # Can't test the connect_packet, we can't yet generate MQTTv5 packet.
            # connect_packet = paho_test.gen_connect(
            #     "01-con-discon-success", keepalive=60,
            #     proto_ver=client.MQTTv311)
            packet_in = fake_broker.receive_packet(1000)
            assert packet_in  # Check connection was not closed
            # assert packet_in == connect_packet

            # The reply packet is a MQTTv3 connack. But that the propose of this test,
            # ensure client convert it to a reason code 132 "Unsupported protocol version"
            connack_packet = paho_test.gen_connack(rc=1)
            count = fake_broker.send_packet(connack_packet)
            assert count  # Check connection was not closed
            assert count == len(connack_packet)

            packet_in = fake_broker.receive_packet(1)
            assert not packet_in  # Check connection is closed

        finally:
            mqttc.loop_stop()


class TestPublishBroker2Client:

    def test_invalid_utf8_topic(self, fake_broker):
        mqttc = client.Client("client-id")

        def on_message(client, userdata, msg):
            with pytest.raises(UnicodeDecodeError):
                assert msg.topic
            client.disconnect()

        mqttc.on_message = on_message

        mqttc.connect_async("localhost", fake_broker.port)
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

    def test_valid_utf8_topic_recv(self, fake_broker):
        mqttc = client.Client("client-id")

        # It should be non-ascii multi-bytes character
        topic = unicodedata.lookup('SNOWMAN')

        def on_message(client, userdata, msg):
            assert msg.topic == topic
            client.disconnect()

        mqttc.on_message = on_message

        mqttc.connect_async("localhost", fake_broker.port)
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

            publish_packet = paho_test.gen_publish(
                topic.encode('utf-8'), qos=0
            )
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

    def test_valid_utf8_topic_publish(self, fake_broker):
        mqttc = client.Client("client-id")

        # It should be non-ascii multi-bytes character
        topic = unicodedata.lookup('SNOWMAN')

        mqttc.connect_async("localhost", fake_broker.port)
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

            mqttc.publish(topic, None, 0)
            # Small sleep needed to avoid connection reset.
            time.sleep(0.3)

            publish_packet = paho_test.gen_publish(
                topic.encode('utf-8'), qos=0
            )
            packet_in = fake_broker.receive_packet(len(publish_packet))
            assert packet_in  # Check connection was not closed
            assert packet_in == publish_packet

            mqttc.disconnect()

            disconnect_packet = paho_test.gen_disconnect()
            packet_in = fake_broker.receive_packet(len(disconnect_packet))
            assert packet_in  # Check connection was not closed
            assert packet_in == disconnect_packet

        finally:
            mqttc.loop_stop()

        packet_in = fake_broker.receive_packet(1)
        assert not packet_in  # Check connection is closed

    def test_message_callback(self, fake_broker):
        mqttc = client.Client("client-id")
        userdata = {
            'on_message': 0,
            'callback1': 0,
            'callback2': 0,
        }
        mqttc.user_data_set(userdata)

        def on_message(client, userdata, msg):
            assert msg.topic == 'topic/value'
            userdata['on_message'] += 1

        def callback1(client, userdata, msg):
            assert msg.topic == 'topic/callback/1'
            userdata['callback1'] += 1

        def callback2(client, userdata, msg):
            assert msg.topic in ('topic/callback/3', 'topic/callback/1')
            userdata['callback2'] += 1

        mqttc.on_message = on_message
        mqttc.message_callback_add('topic/callback/1', callback1)
        mqttc.message_callback_add('topic/callback/+', callback2)

        mqttc.connect_async("localhost", fake_broker.port)
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

            publish_packet = paho_test.gen_publish(b"topic/value", qos=1, mid=1)
            count = fake_broker.send_packet(publish_packet)
            assert count  # Check connection was not closed
            assert count == len(publish_packet)

            publish_packet = paho_test.gen_publish(b"topic/callback/1", qos=1, mid=2)
            count = fake_broker.send_packet(publish_packet)
            assert count  # Check connection was not closed
            assert count == len(publish_packet)

            publish_packet = paho_test.gen_publish(b"topic/callback/3", qos=1, mid=3)
            count = fake_broker.send_packet(publish_packet)
            assert count  # Check connection was not closed
            assert count == len(publish_packet)


            puback_packet = paho_test.gen_puback(mid=1)
            packet_in = fake_broker.receive_packet(len(puback_packet))
            assert packet_in  # Check connection was not closed
            assert packet_in == puback_packet

            puback_packet = paho_test.gen_puback(mid=2)
            packet_in = fake_broker.receive_packet(len(puback_packet))
            assert packet_in  # Check connection was not closed
            assert packet_in == puback_packet

            puback_packet = paho_test.gen_puback(mid=3)
            packet_in = fake_broker.receive_packet(len(puback_packet))
            assert packet_in  # Check connection was not closed
            assert packet_in == puback_packet

            mqttc.disconnect()

            disconnect_packet = paho_test.gen_disconnect()
            packet_in = fake_broker.receive_packet(len(disconnect_packet))
            assert packet_in  # Check connection was not closed
            assert packet_in == disconnect_packet

        finally:
            mqttc.loop_stop()

        packet_in = fake_broker.receive_packet(1)
        assert not packet_in  # Check connection is closed

        assert userdata['on_message'] == 1
        assert userdata['callback1'] == 1
        assert userdata['callback2'] == 2


class TestCompatibility:
    """
    Some tests for backward compatibility
    """

    def test_change_error_code_to_enum(self):
        """Make sure code don't break after MQTTErrorCode enum introduction"""
        rc_ok = client.MQTTErrorCode.MQTT_ERR_SUCCESS
        rc_again = client.MQTTErrorCode.MQTT_ERR_AGAIN
        rc_err = client.MQTTErrorCode.MQTT_ERR_NOMEM

        # Access using old name still works
        assert rc_ok == client.MQTT_ERR_SUCCESS

        # User might compare to 0 to check for success
        assert rc_ok == 0
        assert not rc_err == 0
        assert not rc_again == 0
        assert not rc_ok != 0
        assert rc_err != 0
        assert rc_again != 0

        # User might compare to specific code
        assert rc_again == -1
        assert rc_err == 1

        # User might just use "if rc:"
        assert not rc_ok
        assert rc_err
        assert rc_again

        # User might do inequality with 0 (like "if rc > 0")
        assert not (rc_ok > 0)
        assert rc_err > 0
        assert rc_again < 0

        # This might probably not be done: User might use rc as number in
        # operation
        assert rc_ok + 1 == 1
