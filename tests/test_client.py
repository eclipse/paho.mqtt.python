import os
import sys
import inspect

import paho.mqtt.client as client

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
from testsupport.broker import fake_broker


class Test_connect(object):
    """
    Tests on connect/disconnect behaviour of the client
    """

    def test_01_con_discon_success(self, fake_broker):
        mqttc = client.Client(
            "01-con-discon-success", protocol=client.MQTTv31)

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
                proto_name="MQIsdp", proto_ver=3)
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

    def test_01_con_failure_rc(self, fake_broker):
        mqttc = client.Client(
            "01-con-failure-rc", protocol=client.MQTTv31)

        def on_connect(mqttc, obj, flags, rc):
            assert rc == 1

        mqttc.on_connect = on_connect

        mqttc.connect_async("localhost", 1888)
        mqttc.loop_start()

        try:
            fake_broker.start()

            connect_packet = paho_test.gen_connect(
                "01-con-discon-failure-rc", keepalive=60,
                proto_name="MQIsdp", proto_ver=3)
            packet_in = fake_broker.receive_packet(1000)
            assert packet_in  # Check connection was not closed
            assert packet_in == connect_packet

            connack_packet = paho_test.gen_connack(rc=1)
            count = fake_broker.send_packet(connack_packet)
            assert count  # Check connection was not closed
            assert count == len(connack_packet)

        finally:
            mqttc.loop_stop()

        packet_in = fake_broker.receive_packet(1)
        assert not packet_in  # Check connection is closed
