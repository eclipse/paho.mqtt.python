import paho.mqtt.client as mqtt

from tests.paho_test import loop_until_keyboard_interrupt

mqttc = mqtt.Client("01-no-clean-session", clean_session=False)

mqttc.connect("localhost", 1888)
loop_until_keyboard_interrupt(mqttc)
