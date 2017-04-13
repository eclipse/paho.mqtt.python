#!/usr/bin/env python

# Test whether a client produces a correct connect with a unicode username and password.

# The client should connect to port 1888 with keepalive=60, clean session set,
# client id 01-unpwd-unicode-set, username and password from corresponding variables

from __future__ import unicode_literals

import context
import paho_test

rc = 1
keepalive = 60
username = "\u00fas\u00e9rn\u00e1m\u00e9-h\u00e9ll\u00f3"
password = "h\u00e9ll\u00f3"
connect_packet = paho_test.gen_connect(
    "01-unpwd-unicode-set", keepalive=keepalive, username=username, password=password)

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
