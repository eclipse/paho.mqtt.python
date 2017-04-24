#!/usr/bin/env python

# Test whether a client sends a correct retained PUBLISH to a topic with QoS 0.

import context
import paho_test

rc = 1
keepalive = 60
mid = 16
connect_packet = paho_test.gen_connect("retain-qos0-test", keepalive=keepalive)
connack_packet = paho_test.gen_connack(rc=0)

publish_packet = paho_test.gen_publish(
    u"retain/qos0/test", qos=0, payload="retained message".encode('utf-8'), retain=True)

sock = paho_test.create_server_socket()

client = context.start_client()

try:
    (conn, address) = sock.accept()
    conn.settimeout(10)

    if paho_test.expect_packet(conn, "connect", connect_packet):
        conn.send(connack_packet)

        if paho_test.expect_packet(conn, "publish", publish_packet):
            rc = 0

    conn.close()
finally:
    client.terminate()
    client.wait()
    sock.close()

exit(rc)
