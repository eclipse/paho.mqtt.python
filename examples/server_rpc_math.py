#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright (c) 2020 Frank Pagliughi <fpagliughi@mindspring.com>
# All rights reserved. 
# 
# This program and the accompanying materials are made available 
# under the terms of the Eclipse Distribution License v1.0
# which accompanies this distribution.
#
# The Eclipse Distribution License is available at
#   http://www.eclipse.org/org/documents/edl-v10.php.
#
# Contributors:
#   Frank Pagliughi - initial implementation
#

# This shows an example of an MQTTv5 Remote Procedure Call (RPC) server.

import json

import context  # Ensures paho is in PYTHONPATH

import paho.mqtt.client as mqtt
from paho.mqtt.packettypes import PacketTypes

# The math functions exported

def add(nums):
    sum = 0
    for x in nums:
        sum += x
    return sum

def mult(nums):
    prod = 1
    for x in nums:
        prod *= x
    return prod

# Remember that the MQTTv5 callback takes the additional 'props' parameter.
def on_connect(mqttc, userdata, flags, rc, props):
    print("Connected: '"+str(flags)+"', '"+str(rc)+"', '"+str(props))
    if not flags["session present"]:
        print("Subscribing to math requests")
        mqttc.subscribe("requests/math/#")

# Each incoming message should be an RPC request on the 
# 'requests/math/#' topic.
def on_message(mqttc, userdata, msg):
    print(msg.topic + "  " + str(msg.payload))

    # Get the response properties, abort if they're not given
    props = msg.properties
    if not hasattr(props, 'ResponseTopic') or not hasattr(props, 'CorrelationData'):
        print("No reply requested")
        return

    corr_id = props.CorrelationData
    reply_to = props.ResponseTopic

    # The command parameters are in the payload
    nums = json.loads(msg.payload)

    # The requested command is at the end of the topic
    res = 0
    if msg.topic.endswith("add"):
        res = add(nums)
    elif msg.topic.endswith("mult"):
        res = mult(nums)

    # Now we have the result, res, so send it back on the 'reply_to'
    # topic using the same correlation ID as the request.
    print("Sending response "+str(res)+" on '"+reply_to+"': "+str(corr_id))
    props = mqtt.Properties(PacketTypes.PUBLISH)
    props.CorrelationData = corr_id

    payload = json.dumps(res)
    mqttc.publish(reply_to, payload, qos=1, properties=props)

def on_log(mqttc, obj, level, string):
    print(string)


# Typically with an RPC service, you want to make sure that you're the only
# client answering requests for specific topics. Using a known client ID 
# might help.
mqttc = mqtt.Client(client_id="paho_rpc_math_srvr", protocol=mqtt.MQTTv5)
mqttc.on_message = on_message
mqttc.on_connect = on_connect

# Uncomment to enable debug messages
#mqttc.on_log = on_log

#mqttc.connect("mqtt.eclipseprojects.io", 1883, 60)
mqttc.connect(host="localhost", clean_start=False)
mqttc.loop_forever()
