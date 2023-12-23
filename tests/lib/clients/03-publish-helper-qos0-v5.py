import paho.mqtt.client
import paho.mqtt.publish

from tests.paho_test import wait_for_keyboard_interrupt

with wait_for_keyboard_interrupt():
    paho.mqtt.publish.single(
        "pub/qos0/test",
        "message",
        qos=0,
        hostname="localhost",
        port=1888,
        client_id="publish-helper-qos0-test",
        protocol=paho.mqtt.client.MQTTv5,
    )
