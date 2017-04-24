#!/usr/bin/env python

# Test whether a client sends a correct PUBLISH to a topic with QoS 2 and responds to a disconnect.

import context
import paho_test

rc = 1
keepalive = 60
connect_packet = paho_test.gen_connect("publish-qos2-test", keepalive=keepalive)
connack_packet = paho_test.gen_connack(rc=0)

disconnect_packet = paho_test.gen_disconnect()

mid = 1
publish_packet = paho_test.gen_publish(
    u"pub/qos2/test", qos=2, mid=mid, payload="message".encode('utf-8'))
publish_dup_packet = paho_test.gen_publish(
    u"pub/qos2/test", qos=2, mid=mid, payload="message".encode('utf-8'), dup=True)
pubrec_packet = paho_test.gen_pubrec(mid)
pubrel_packet = paho_test.gen_pubrel(mid)
pubrel_dup_packet = paho_test.gen_pubrel(mid, dup=True)
pubcomp_packet = paho_test.gen_pubcomp(mid)

sock = paho_test.create_server_socket()

client = context.start_client()

try:
    (conn, address) = sock.accept()
    conn.settimeout(5)

    if paho_test.expect_packet(conn, "connect", connect_packet):
        conn.send(connack_packet)

        if paho_test.expect_packet(conn, "publish", publish_packet):
            # Disconnect client. It should reconnect.
            conn.close()

            (conn, address) = sock.accept()
            conn.settimeout(15)

            if paho_test.expect_packet(conn, "connect", connect_packet):
                conn.send(connack_packet)

                if paho_test.expect_packet(conn, "retried publish", publish_dup_packet):
                    conn.send(pubrec_packet)

                    if paho_test.expect_packet(conn, "pubrel", pubrel_packet):
                        # Disconnect client. It should reconnect.
                        conn.close()

                        (conn, address) = sock.accept()
                        conn.settimeout(15)

                        # Complete connection and message flow.
                        if paho_test.expect_packet(conn, "connect", connect_packet):
                            conn.send(connack_packet)

                            if paho_test.expect_packet(conn, "retried pubrel", pubrel_dup_packet):
                                conn.send(pubcomp_packet)

                                if paho_test.expect_packet(conn, "disconnect", disconnect_packet):
                                    rc = 0

    conn.close()
finally:
    client.terminate()
    client.wait()
    sock.close()

exit(rc)
