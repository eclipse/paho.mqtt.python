#!/usr/bin/env python

# Test whether a client sends a correct PUBLISH to a topic with QoS 2 and responds to a disconnect.

import inspect
import os
import subprocess
import socket
import sys
import time

# From http://stackoverflow.com/questions/279237/python-import-a-module-from-a-folder
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"..")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

import paho_test

rc = 1
keepalive = 60
connect_packet = paho_test.gen_connect("publish-qos2-test", keepalive=keepalive)
connack_packet = paho_test.gen_connack(rc=0)

disconnect_packet = paho_test.gen_disconnect()

mid = 1
publish_packet = paho_test.gen_publish("pub/qos2/test", qos=2, mid=mid, payload="message")
publish_dup_packet = paho_test.gen_publish("pub/qos2/test", qos=2, mid=mid, payload="message", dup=True)
pubrec_packet = paho_test.gen_pubrec(mid)
pubrel_packet = paho_test.gen_pubrel(mid)
pubrel_dup_packet = paho_test.gen_pubrel(mid, dup=True)
pubcomp_packet = paho_test.gen_pubcomp(mid)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.settimeout(10)
sock.bind(('', 1888))
sock.listen(5)

client_args = sys.argv[1:]
env = dict(os.environ)
try:
    pp = env['PYTHONPATH']
except KeyError:
    pp = ''
env['PYTHONPATH'] = '../../src:'+pp
client = subprocess.Popen(client_args, env=env)

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
