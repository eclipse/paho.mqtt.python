#!/usr/bin/env python3

# Test the reconnect_on_failure = False mode

import context
import paho_test

rc = 1
keepalive = 60
connect_packet = paho_test.gen_connect("01-reconnect-on-failure", keepalive=keepalive)
connack_packet_ok = paho_test.gen_connack(rc=0)
connack_packet_failure = paho_test.gen_connack(rc=1) # CONNACK_REFUSED_PROTOCOL_VERSION

publish_packet = paho_test.gen_publish(
    u"reconnect/test", qos=0, payload="message")

sock = paho_test.create_server_socket()

client = context.start_client()

try:
    (conn, address) = sock.accept()
    conn.settimeout(10)

    paho_test.expect_packet(conn, "connect", connect_packet)
    conn.send(connack_packet_ok)

    # Connection is a success, so we expect a publish
    paho_test.expect_packet(conn, "publish", publish_packet)
    conn.close()
    # Expect the client to quit here due to socket being closed
    client.wait(1)
    if client.returncode == 42:
        # Repeat the test, but with a bad connack code
        client = context.start_client()
        (conn, address) = sock.accept()
        conn.settimeout(10)

        paho_test.expect_packet(conn, "connect", connect_packet)
        conn.send(connack_packet_failure)
        # Expect the client to quit here due to socket being closed
        client.wait(1)
        if client.returncode == 42:
            rc = 0

    conn.close()
finally:
    client.terminate()
    client.wait()
    sock.close()

exit(rc)

