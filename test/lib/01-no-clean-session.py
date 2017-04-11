#!/usr/bin/env python

# Test whether a client produces a correct connect with clean session not set.

# The client should connect to port 1888 with keepalive=60, clean session not
# set, and client id 01-no-clean-session.

import context
import paho_test

rc = 1
keepalive = 60
connect_packet = paho_test.gen_connect("01-no-clean-session", clean_session=False, keepalive=keepalive)

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

