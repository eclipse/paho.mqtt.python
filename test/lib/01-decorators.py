#!/usr/bin/env python3

# Test whether callback decorators work

import context
import paho_test

rc = 1
keepalive = 60
connect_packet = paho_test.gen_connect("decorators-test", keepalive=keepalive)
connack_packet = paho_test.gen_connack(rc=0)

subscribe_packet = paho_test.gen_subscribe(mid=1, topic=u"sub-test", qos=1)
suback_packet = paho_test.gen_suback(mid=1, qos=1)

unsubscribe_packet = paho_test.gen_unsubscribe(mid=2, topic=u"unsub-test")
unsuback_packet = paho_test.gen_unsuback(mid=2)

publish_packet = paho_test.gen_publish(u"b2c", qos=0, payload="msg")

publish_packet_in = paho_test.gen_publish(u"decorators", qos=1, mid=3, payload="message")
puback_packet_in = paho_test.gen_puback(mid=3)

disconnect_packet = paho_test.gen_disconnect()

sock = paho_test.create_server_socket()

client = context.start_client()

try:
    (conn, address) = sock.accept()
    conn.settimeout(10)

    paho_test.expect_packet(conn, "connect", connect_packet)
    conn.send(connack_packet)

    paho_test.expect_packet(conn, "subscribe", subscribe_packet)
    conn.send(suback_packet)

    paho_test.expect_packet(conn, "unsubscribe", unsubscribe_packet)
    conn.send(unsuback_packet)
    conn.send(publish_packet)

    paho_test.expect_packet(conn, "publish", publish_packet_in)
    conn.send(puback_packet_in)

    paho_test.expect_packet(conn, "disconnect", disconnect_packet)
    rc = 0

    conn.close()
finally:
    client.terminate()
    client.wait()
    sock.close()

exit(rc)
