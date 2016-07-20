#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2016 Roger Light <roger@atchoo.org>
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

# This shows an example of using the subscribe.simple helper function.

import context  # Ensures paho is in PYTHONPATH
import paho.mqtt.subscribe as subscribe

topics = ['#']

m = subscribe.simple(topics, hostname="iot.eclipse.org", retained=False, msg_count=2)
for a in m:
    print(a.topic)
    print(a.payload)
