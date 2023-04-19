"""
Copyright (c) 2012-2019 Roger Light and others

All rights reserved. This program and the accompanying materials
are made available under the terms of the Eclipse Public License v2.0
and Eclipse Distribution License v1.0 which accompany this distribution.

The Eclipse Public License is available at
    http://www.eclipse.org/legal/epl-v10.html
and the Eclipse Distribution License is available at
    http://www.eclipse.org/org/documents/edl-v10.php.

Contributors:
    Roger Light - initial API and implementation
    Ian Craggs - MQTT V5 support
"""

import socket
import string
from .matcher import MQTTMatcher

def base62(num, base=string.digits + string.ascii_letters, padding=1):
    """
    Convert a number to base-62 representation.
    """

    assert num >= 0
    digits = []
    while num:
        num, rest = divmod(num, 62)
        digits.append(base[rest])
    digits.extend(base[0] for _ in range(len(digits), padding))
    return "".join(reversed(digits))


def topic_matches_sub(sub, topic):
    """Check whether a topic matches a subscription.

    For example:

    foo/bar would match the subscription foo/# or +/bar
    non/matching would not match the subscription non/+/+
    """

    matcher = MQTTMatcher()
    matcher[sub] = True
    try:
        next(matcher.iter_match(topic))
        return True
    except StopIteration:
        return False


def _socketpair_compat():
    """
    TCP/IP socketpair including Windows support.
    """

    listensock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_IP)
    listensock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listensock.bind(("127.0.0.1", 0))
    listensock.listen(1)

    _, port = listensock.getsockname()
    sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_IP)
    sock1.setblocking(0)
    try:
        sock1.connect(("127.0.0.1", port))
    except BlockingIOError:
        pass
    sock2, _ = listensock.accept()
    sock2.setblocking(0)
    listensock.close()
    return (sock1, sock2)
