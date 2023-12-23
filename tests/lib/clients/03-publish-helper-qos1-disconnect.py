import paho.mqtt.publish

from tests.paho_test import wait_for_keyboard_interrupt

with wait_for_keyboard_interrupt():
    paho.mqtt.publish.single(
        "pub/qos1/test",
        "message",
        qos=1,
        hostname="localhost",
        port=1888,
        client_id="publish-helper-qos1-disconnect-test",
    )
