import paho.mqtt.client as mqtt

from tests.paho_test import loop_until_keyboard_interrupt


def on_connect(mqttc, obj, flags, rc):
    assert rc == 0, f"Connect failed ({rc})"
    mqttc.publish("retain/qos0/test", "retained message", 0, True)


mqttc = mqtt.Client("retain-qos0-test", clean_session=True)
mqttc.on_connect = on_connect

mqttc.connect("localhost", 1888)
loop_until_keyboard_interrupt(mqttc)
