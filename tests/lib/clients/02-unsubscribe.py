import paho.mqtt.client as mqtt

from tests.paho_test import loop_until_keyboard_interrupt


def on_connect(mqttc, obj, flags, rc):
    assert rc == 0, f"Connect failed ({rc})"
    mqttc.unsubscribe("unsubscribe/test")


def on_unsubscribe(mqttc, obj, mid):
    mqttc.disconnect()


mqttc = mqtt.Client("unsubscribe-test", clean_session=True)
mqttc.on_connect = on_connect
mqttc.on_unsubscribe = on_unsubscribe

mqttc.connect("localhost", 1888)
loop_until_keyboard_interrupt(mqttc)
