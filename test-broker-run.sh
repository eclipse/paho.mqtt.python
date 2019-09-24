#!/bin/bash

git clone https://github.com/eclipse/paho.mqtt.testing.git
cd paho.mqtt.testing/interoperability
python3 startbroker.py -c localhost_testing.conf > test_broker.out 2> test_broker.err &
cd ../..
