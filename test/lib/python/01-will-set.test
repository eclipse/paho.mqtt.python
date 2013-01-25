#!/usr/bin/python

import mosquitto

mosq = mosquitto.Mosquitto("01-will-set")

run = -1
mosq.will_set("topic/on/unexpected/disconnect", "will message", 1, True)
mosq.connect("localhost", 1888)
while run == -1:
    mosq.loop()

exit(run)
