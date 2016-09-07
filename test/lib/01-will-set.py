#!/usr/bin/env python

# Test whether a client produces a correct connect with a will.
# Will QoS=1, will retain=1.

# The client should connect to port 1888 with keepalive=60, clean session set,
# client id 01-will-set will topic set to topic/on/unexpected/disconnect , will
# payload set to "will message", will qos set to 1 and will retain set.

import context
import paho_test

rc = 1
keepalive = 60
connect_packet = paho_test.gen_connect(
    "01-will-set", keepalive=keepalive, will_topic="topic/on/unexpected/disconnect",
    will_qos=1, will_retain=True, will_payload="will message".encode('utf-8'))

sock = paho_test.create_server_socket()

client = context.start_client()

try:
    (conn, address) = sock.accept()
    conn.settimeout(10)

    if paho_test.expect_packet(conn, "connect", connect_packet):
        rc = 0

    conn.close()
finally:
    client.terminate()
    client.wait()
    sock.close()

exit(rc)

