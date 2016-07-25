#!/usr/bin/env python

# Test whether a client connects correctly with a zero length clientid.

import context
import paho_test

rc = 1
keepalive = 60
connect_packet = paho_test.gen_connect("", keepalive=keepalive, proto_name="MQTT", proto_ver=4)
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

