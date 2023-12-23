import os

import paho.mqtt.client as mqtt

from tests.paho_test import loop_until_keyboard_interrupt


def on_connect(mqttc, obj, flags, rc):
    assert rc == 0, f"Connect failed ({rc})"
    mqttc.disconnect()


mqttc = mqtt.Client("08-ssl-connect-crt-auth-pw")
mqttc.tls_set(
    os.path.join(os.environ["PAHO_SSL_PATH"], "all-ca.crt"),
    os.path.join(os.environ["PAHO_SSL_PATH"], "client-pw.crt"),
    os.path.join(os.environ["PAHO_SSL_PATH"], "client-pw.key"),
    keyfile_password="password",
)
mqttc.on_connect = on_connect

mqttc.connect("localhost", 1888)
loop_until_keyboard_interrupt(mqttc)
