#!/usr/bin/env python

import time

import context
import paho_test
from paho_test import ssl

context.check_ssl()

ssock = paho_test.create_server_socket_ssl(cert_reqs=ssl.CERT_REQUIRED)

client = context.start_client()

try:
    (conn, address) = ssock.accept()

    conn.close()
except ssl.SSLError:
    # Expected error due to ca certs not matching.
    pass
finally:
    time.sleep(1.0)
    client.terminate()
    client.wait()
    ssock.close()

if client.returncode == 0:
    exit(0)
else:
    exit(1)
