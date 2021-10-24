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

# This shows an example of an MQTTv5 Remote Procedure Call (RPC) client.

import json
import sys
import time

import context  # Ensures paho is in PYTHONPATH

import paho.mqtt.client as mqtt
from paho.mqtt.packettypes import PacketTypes

# These will be updated with the server-assigned Client ID
client_id = "mathcli"
reply_to = ""

# This correlates the outbound request with the returned reply
corr_id = b"1"

# This is sent in the message callback when we get the respone
reply = None

# The MQTTv5 callback takes the additional 'props' parameter.
def on_connect(mqttc, userdata, flags, rc, props):
    global client_id, reply_to

    print("Connected: '"+str(flags)+"', '"+str(rc)+"', '"+str(props))
    if hasattr(props, 'AssignedClientIdentifier'):
        client_id = props.AssignedClientIdentifier
    reply_to = "replies/math/" + client_id
    mqttc.subscribe(reply_to)


# An incoming message should be the reply to our request
def on_message(mqttc, userdata, msg):
    global reply

    print(msg.topic+" "+str(msg.payload)+"  "+str(msg.properties))
    props = msg.properties
    if not hasattr(props, 'CorrelationData'):
        print("No correlation ID")

    # Match the response to the request correlation ID.
    if props.CorrelationData == corr_id:
        reply = msg.payload


if len(sys.argv) < 3:
    print("USAGE: client_rpc_math.py [add|mult] n1 n2 ...")
    sys.exit(1)

mqttc = mqtt.Client(client_id="", protocol=mqtt.MQTTv5)
mqttc.on_message = on_message
mqttc.on_connect = on_connect

mqttc.connect(host='localhost', clean_start=True)
mqttc.loop_start()

# Wait for connection to set `client_id`, etc.
while not mqttc.is_connected():
    time.sleep(0.1)

# Properties for the request specify the ResponseTopic and CorrelationData
props = mqtt.Properties(PacketTypes.PUBLISH)
props.CorrelationData = corr_id
props.ResponseTopic = reply_to

# Uncomment to see what got set
#print("Client ID: "+client_id)
#print("Reply To: "+reply_to)
#print(props)

# The requested operation, 'add' or 'mult'
func = sys.argv[1]

# Gather the numeric parameters as an array of numbers
# These can be int's or float's
args = []
for s in sys.argv[2:]:
    args.append(float(s))

# Send the request
topic = "requests/math/" + func 
payload = json.dumps(args)
mqttc.publish(topic, payload, qos=1, properties=props)

# Wait for the reply
while reply is None:
    time.sleep(0.1)

# Extract the response and print it.
rsp = json.loads(reply)
print("Response: "+str(rsp))

mqttc.loop_stop()

