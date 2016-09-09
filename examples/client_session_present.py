#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2014 Roger Light <roger@atchoo.org>
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Distribution License v1.0
# which accompanies this distribution.
#
# The Eclipse Distribution License is available at
#   http://www.eclipse.org/org/documents/edl-v10.php.
#
# Contributors:
#    Roger Light - initial implementation
# Copyright (c) 2014 Roger Light <roger@atchoo.org>
# All rights reserved.

# This demonstrates the session present flag when connecting.

import context  # Ensures paho is in PYTHONPATH
import paho.mqtt.client as mqtt


def on_connect(mqttc, obj, flags, rc):
    if obj == 0:
        print("First connection:")
    elif obj == 1:
        print("Second connection:")
    elif obj == 2:
        print("Third connection (with clean session=True):")
    print("    Session present: " + str(flags['session present']))
    print("    Connection result: " + str(rc))
    mqttc.disconnect()


def on_disconnect(mqttc, obj, rc):
    mqttc.user_data_set(obj + 1)
    if obj == 0:
        mqttc.reconnect()


def on_log(mqttc, obj, level, string):
    print(string)


mqttc = mqtt.Client(client_id="asdfj", clean_session=False)
mqttc.on_connect = on_connect
mqttc.on_disconnect = on_disconnect
# Uncomment to enable debug messages
# mqttc.on_log = on_log
mqttc.user_data_set(0)
mqttc.connect("test.mosquitto.org", 1883, 60)

mqttc.loop_forever()

# Clear session
mqttc = mqtt.Client(client_id="asdfj", clean_session=True)
mqttc.on_connect = on_connect
mqttc.user_data_set(2)
mqttc.connect("test.mosquitto.org", 1883, 60)
mqttc.loop_forever()
