#!/usr/bin/env python

# Test whether a client responds correctly to a PUBLISH with QoS 1.

# The client should connect to port 1888 with keepalive=60, clean session set,
# and client id publish-qos1-test
# The test will send a CONNACK message to the client with rc=0. Upon receiving
# the CONNACK the client should verify that rc==0.
# The test will send the client a PUBLISH message with topic
# "pub/qos1/receive", payload of "message", QoS=1 and mid=123. The client
# should handle this as per the spec by sending a PUBACK message.
# The client should then exit with return code==0.

import time

import context
import paho_test

rc = 1
keepalive = 60
connect_packet = paho_test.gen_connect("publish-qos1-test", keepalive=keepalive)
connack_packet = paho_test.gen_connack(rc=0)

disconnect_packet = paho_test.gen_disconnect()

mid = 123
publish_packet = paho_test.gen_publish(
    u"pub/qos1/receive", qos=1, mid=mid, payload="message".encode('utf-8'))
puback_packet = paho_test.gen_puback(mid)

sock = paho_test.create_server_socket()

client = context.start_client()

try:
    (conn, address) = sock.accept()
    conn.settimeout(10)

    if paho_test.expect_packet(conn, "connect", connect_packet):
        conn.send(connack_packet)
        conn.send(publish_packet)

        if paho_test.expect_packet(conn, "puback", puback_packet):
            rc = 0

    conn.close()
finally:
    for i in range(0, 5):
        if client.returncode != None:
            break
        time.sleep(0.1)

    client.terminate()
    client.wait()
    sock.close()
    if client.returncode != 0:
        exit(1)

exit(rc)
