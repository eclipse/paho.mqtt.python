#!/usr/bin/env python

# Test whether a client sends a pingreq after the keepalive time

# The client should connect to port 1888 with keepalive=4, clean session set,
# and client id 01-keepalive-pingreq
# The client should send a PINGREQ message after the appropriate amount of time
# (4 seconds after no traffic).

import time

import context
import paho_test

rc = 1
keepalive = 4
connect_packet = paho_test.gen_connect("01-keepalive-pingreq", keepalive=keepalive)
connack_packet = paho_test.gen_connack(rc=0)

pingreq_packet = paho_test.gen_pingreq()
pingresp_packet = paho_test.gen_pingresp()

sock = paho_test.create_server_socket()

client = context.start_client()

try:
    (conn, address) = sock.accept()
    conn.settimeout(keepalive+10)

    if paho_test.expect_packet(conn, "connect", connect_packet):
        conn.send(connack_packet)

        if paho_test.expect_packet(conn, "pingreq", pingreq_packet):
            time.sleep(1.0)
            conn.send(pingresp_packet)

            if paho_test.expect_packet(conn, "pingreq", pingreq_packet):
                rc = 0

    conn.close()
finally:
    client.terminate()
    client.wait()
    sock.close()

exit(rc)

