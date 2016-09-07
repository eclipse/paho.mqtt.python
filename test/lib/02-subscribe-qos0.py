#!/usr/bin/env python

# Test whether a client sends a correct SUBSCRIBE to a topic with QoS 0.

# The client should connect to port 1888 with keepalive=60, clean session set,
# and client id subscribe-qos0-test
# The test will send a CONNACK message to the client with rc=0. Upon receiving
# the CONNACK and verifying that rc=0, the client should send a SUBSCRIBE
# message to subscribe to topic "qos0/test" with QoS=0. If rc!=0, the client
# should exit with an error.
# Upon receiving the correct SUBSCRIBE message, the test will reply with a
# SUBACK message with the accepted QoS set to 0. On receiving the SUBACK
# message, the client should send a DISCONNECT message.

import context
import paho_test

rc = 1
keepalive = 60
connect_packet = paho_test.gen_connect("subscribe-qos0-test", keepalive=keepalive)
connack_packet = paho_test.gen_connack(rc=0)

disconnect_packet = paho_test.gen_disconnect()

mid = 1
subscribe_packet = paho_test.gen_subscribe(mid, "qos0/test", 0)
suback_packet = paho_test.gen_suback(mid, 0)

sock = paho_test.create_server_socket()

client = context.start_client()

try:
    (conn, address) = sock.accept()
    conn.settimeout(10)

    if paho_test.expect_packet(conn, "connect", connect_packet):
        conn.send(connack_packet)

        if paho_test.expect_packet(conn, "subscribe", subscribe_packet):
            conn.send(suback_packet)

            if paho_test.expect_packet(conn, "disconnect", disconnect_packet):
                rc = 0

    conn.close()
finally:
    client.terminate()
    client.wait()
    sock.close()

exit(rc)
