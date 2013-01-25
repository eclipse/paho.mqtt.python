#!/usr/bin/python

import mosquitto

mosq = mosquitto.Mosquitto("01-unpwd-set")

run = -1
mosq.username_pw_set("uname", ";'[08gn=#")
mosq.connect("localhost", 1888)
while run == -1:
    mosq.loop()

exit(run)
