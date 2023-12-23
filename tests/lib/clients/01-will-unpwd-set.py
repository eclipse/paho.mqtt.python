import paho.mqtt.client as mqtt

from tests.paho_test import loop_until_keyboard_interrupt

mqttc = mqtt.Client("01-will-unpwd-set")

mqttc.username_pw_set("oibvvwqw", "#'^2hg9a&nm38*us")
mqttc.will_set("will-topic", "will message", 2, False)
mqttc.connect("localhost", 1888)
loop_until_keyboard_interrupt(mqttc)
