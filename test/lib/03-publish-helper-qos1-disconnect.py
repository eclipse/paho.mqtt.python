#!/usr/bin/env python

# Test whether a client sends a correct PUBLISH to a topic with QoS 1,
# then responds correctly to a disconnect.
# Use paho.mqtt.publish helper for that.

import context
import paho_test

rc = 1
keepalive = 60
connect_packet = paho_test.gen_connect(
    "publish-helper-qos1-disconnect-test", keepalive=keepalive,
)
connack_packet = paho_test.gen_connack(rc=0)

mid = 1
publish_packet = paho_test.gen_publish(
    u"pub/qos1/test", qos=1, mid=mid, payload="message".encode('utf-8'),
)
publish_packet_dup = paho_test.gen_publish(
    u"pub/qos1/test", qos=1, mid=mid, payload="message".encode('utf-8'),
    dup=True,
)
puback_packet = paho_test.gen_puback(mid)

disconnect_packet = paho_test.gen_disconnect()

sock = paho_test.create_server_socket()

client = context.start_client()

try:
    (conn, address) = sock.accept()
    conn.settimeout(10)

    if paho_test.expect_packet(conn, "connect", connect_packet):
        conn.send(connack_packet)

        if paho_test.expect_packet(conn, "publish", publish_packet):
            # Disconnect client. It should reconnect.
            conn.close()

            (conn, address) = sock.accept()
            conn.settimeout(15)

            if paho_test.expect_packet(conn, "connect", connect_packet):
                conn.send(connack_packet)

                if paho_test.expect_packet(conn, "retried publish", publish_packet_dup):
                    conn.send(puback_packet)

                    if paho_test.expect_packet(conn, "disconnect", disconnect_packet):
                        rc = 0

    conn.close()
finally:
    client.terminate()
    client.wait()
    sock.close()

exit(rc)
