#!/usr/bin/env python

# Test whether a client produces a correct connect and subsequent disconnect.

# The client should connect to port 1888 with keepalive=60, clean session set,
# and client id 01-con-discon-success
# The test will send a CONNACK message to the client with rc=0. Upon receiving
# the CONNACK and verifying that rc=0, the client should send a DISCONNECT
# message. If rc!=0, the client should exit with an error.

import context
import paho_test

rc = 1
keepalive = 60
connect_packet = paho_test.gen_connect("01-con-discon-success", keepalive=keepalive, proto_name="MQTT", proto_ver=4)
connack_packet = paho_test.gen_connack(rc=0)

disconnect_packet = paho_test.gen_disconnect()

sock = paho_test.create_server_socket()

client = context.start_client()

try:
    (conn, address) = sock.accept()
    conn.settimeout(10)

    if paho_test.expect_packet(conn, "connect", connect_packet):
        conn.send(connack_packet)

        if paho_test.expect_packet(conn, "disconnect", disconnect_packet):
            rc = 0

    conn.close()
finally:
    client.terminate()
    client.wait()
    sock.close()

exit(rc)

