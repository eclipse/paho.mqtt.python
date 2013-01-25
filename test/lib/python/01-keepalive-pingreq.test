#!/usr/bin/python

import os
import subprocess
import socket
import sys
import time
from struct import *

import mosquitto


def on_connect(mosq, obj, rc):
    if rc != 0:
        exit(rc)

run = -1
mosq = mosquitto.Mosquitto("01-keepalive-pingreq")
mosq.on_connect = on_connect

mosq.connect("localhost", 1888, 4)
while run == -1:
    mosq.loop()

exit(run)
