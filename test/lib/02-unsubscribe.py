#!/usr/bin/env python

# Test whether a client sends a correct UNSUBSCRIBE packet.

import context
import paho_test

rc = 1
keepalive = 60
connect_packet = paho_test.gen_connect("unsubscribe-test", keepalive=keepalive)
connack_packet = paho_test.gen_connack(rc=0)

disconnect_packet = paho_test.gen_disconnect()

mid = 1
unsubscribe_packet = paho_test.gen_unsubscribe(mid, "unsubscribe/test")
unsuback_packet = paho_test.gen_unsuback(mid)

sock = paho_test.create_server_socket()

client = context.start_client()

try:
    (conn, address) = sock.accept()
    conn.settimeout(10)

    if paho_test.expect_packet(conn, "connect", connect_packet):
        conn.send(connack_packet)

        if paho_test.expect_packet(conn, "unsubscribe", unsubscribe_packet):
            conn.send(unsuback_packet)

            if paho_test.expect_packet(conn, "disconnect", disconnect_packet):
                rc = 0

    conn.close()
finally:
    client.terminate()
    client.wait()
    sock.close()

exit(rc)
