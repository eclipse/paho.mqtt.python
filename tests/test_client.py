import os
import sys
import inspect

import paho.mqtt.client as mqtt

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


class Test_connect:
    def test_01_con_discon_success(self, fake_broker):
        mqttc = mqtt.Client(
            "01-con-discon-success", protocol=mqtt.MQTTv31)

        def on_connect(mqttc, obj, flags, rc):
            assert rc == 0
            mqttc.disconnect()

        mqttc.on_connect = on_connect

        mqttc.connect_async("localhost", 1888)
        mqttc.loop_start()

        fake_broker.start()

        connect_packet = paho_test.gen_connect(
            "01-con-discon-success", keepalive=60,
            proto_name="MQIsdp", proto_ver=3)
        fake_broker.expect_packet(connect_packet)

        connack_packet = paho_test.gen_connack(rc=0)
        fake_broker.send_packet(connack_packet)

        disconnect_packet = paho_test.gen_disconnect()
        fake_broker.expect_packet(disconnect_packet)

        mqttc.loop_stop()
