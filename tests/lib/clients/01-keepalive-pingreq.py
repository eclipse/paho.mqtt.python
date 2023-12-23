import paho.mqtt.client as mqtt

from tests.paho_test import loop_until_keyboard_interrupt


def on_connect(mqttc, obj, flags, rc):
    assert rc == 0, f"Connect failed ({rc})"


mqttc = mqtt.Client("01-keepalive-pingreq")
mqttc.on_connect = on_connect

mqttc.connect("localhost", 1888, keepalive=4)
loop_until_keyboard_interrupt(mqttc)
