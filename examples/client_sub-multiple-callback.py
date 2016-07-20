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
# All rights reserved.

# This shows a simple example of an MQTT subscriber using a per-subscription message handler.

import context  # Ensures paho is in PYTHONPATH
import paho.mqtt.client as mqtt


def on_message_msgs(mosq, obj, msg):
    # This callback will only be called for messages with topics that match
    # $SYS/broker/messages/#
    print("MESSAGES: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


def on_message_bytes(mosq, obj, msg):
    # This callback will only be called for messages with topics that match
    # $SYS/broker/bytes/#
    print("BYTES: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


def on_message(mosq, obj, msg):
    # This callback will be called for messages that we receive that do not
    # match any patterns defined in topic specific callbacks, i.e. in this case
    # those messages that do not have topics $SYS/broker/messages/# nor
    # $SYS/broker/bytes/#
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


mqttc = mqtt.Client()

# Add message callbacks that will only trigger on a specific subscription match.
mqttc.message_callback_add("$SYS/broker/messages/#", on_message_msgs)
mqttc.message_callback_add("$SYS/broker/bytes/#", on_message_bytes)
mqttc.on_message = on_message
mqttc.connect("iot.eclipse.org", 1883, 60)
mqttc.subscribe("$SYS/#", 0)

mqttc.loop_forever()
