#!/usr/bin/env python3

# Test whether a client sends a correct PUBLISH to a topic with QoS 1, then responds correctly to a disconnect.

import context
import paho_test

rc = 1
keepalive = 60
connect_packet = paho_test.gen_connect(
    "publish-qos1-test", keepalive=keepalive, clean_session=False,
)
connack_packet = paho_test.gen_connack(rc=0)

disconnect_packet = paho_test.gen_disconnect()

mid = 1
publish_packet = paho_test.gen_publish(
    u"pub/qos1/test", qos=1, mid=mid, payload="message")
publish_packet_dup = paho_test.gen_publish(
    u"pub/qos1/test", qos=1, mid=mid, payload="message", dup=True)
puback_packet = paho_test.gen_puback(mid)

sock = paho_test.create_server_socket()

client = context.start_client()

try:
    (conn, address) = sock.accept()
    conn.settimeout(15)

    paho_test.expect_packet(conn, "connect", connect_packet)
    conn.send(connack_packet)

    paho_test.expect_packet(conn, "publish", publish_packet)
    # Disconnect client. It should reconnect.
    conn.close()

    (conn, address) = sock.accept()
    conn.settimeout(15)

    paho_test.expect_packet(conn, "connect", connect_packet)
    conn.send(connack_packet)

    paho_test.expect_packet(conn, "retried publish", publish_packet_dup)
    conn.send(puback_packet)

    paho_test.expect_packet(conn, "disconnect", disconnect_packet)
    rc = 0

    conn.close()
finally:
    client.terminate()
    client.wait()
    sock.close()

exit(rc)
