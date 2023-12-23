import paho.mqtt.client as mqtt

from tests.paho_test import wait_for_keyboard_interrupt


def on_connect(mqttc, obj, flags, rc):
    mqttc.publish("reconnect/test", "message")


mqttc = mqtt.Client("01-reconnect-on-failure", reconnect_on_failure=False)
mqttc.on_connect = on_connect

with wait_for_keyboard_interrupt():
    mqttc.connect("localhost", 1888)
    mqttc.loop_forever()
    exit(42)  # this is expected by the test case
