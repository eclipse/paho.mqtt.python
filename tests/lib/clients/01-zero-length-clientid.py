import paho.mqtt.client as mqtt

from tests.paho_test import loop_until_keyboard_interrupt


def on_connect(mqttc, obj, flags, rc):
    assert rc == 0, f"Connect failed ({rc})"
    mqttc.disconnect()


def on_disconnect(mqttc, obj, rc):
    mqttc.loop()


mqttc = mqtt.Client("", clean_session=True, protocol=mqtt.MQTTv311)
mqttc.on_connect = on_connect
mqttc.on_disconnect = on_disconnect

mqttc.connect("localhost", 1888)
loop_until_keyboard_interrupt(mqttc)
