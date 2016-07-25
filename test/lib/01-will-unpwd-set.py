#!/usr/bin/env python

# Test whether a client produces a correct connect with a will, username and password.

# The client should connect to port 1888 with keepalive=60, clean session set,
# client id 01-will-unpwd-set , will topic set to "will-topic", will payload
# set to "will message", will qos=2, will retain not set, username set to
# "oibvvwqw" and password set to "#'^2hg9a&nm38*us".

import context
import paho_test

rc = 1
keepalive = 60
connect_packet = paho_test.gen_connect("01-will-unpwd-set",
        keepalive=keepalive, username="oibvvwqw", password="#'^2hg9a&nm38*us",
        will_topic="will-topic", will_qos=2, will_payload="will message".encode('utf-8'))

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

