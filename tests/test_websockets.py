import socket
import sys
import contextlib

if sys.version_info < (3, 0):
    from mock import patch, Mock
else:
    from unittest.mock import patch, Mock

import pytest
from paho.mqtt.client import WebsocketWrapper, WebsocketConnectionError


class TestHeaders(object):
    """ Make sure headers are used correctly """

    def test_normal_headers(self):
        """ Normal headers as specified in RFC 6455 """

        response = [
            "HTTP/1.1 101 Switching Protocols",
            "Upgrade: websocket",
            "Connection: Upgrade",
            "Sec-WebSocket-Accept: badreturnvalue=",
            "Sec-WebSocket-Protocol: chat",
            "\r\n",
        ]

        def iter_response():
            for i in "\r\n".join(response):
                yield i

        it = iter_response()

        def fakerecv(*args):
            return next(it)

        mocksock = Mock(
            spec_set=socket.socket,
            recv=fakerecv,
            send=Mock(),
        )
        host = "testhost.com"
        port = 1234
        path = "/mqtt"
        extra_headers = None
        is_ssl = True

        with pytest.raises(WebsocketConnectionError) as exc:
            w = WebsocketWrapper(mocksock, host, port, is_ssl, path, extra_headers)

        # We're not creating the response hash properly so it should raise this
        # error
        assert str(exc.value) == "WebSocket handshake error, invalid secret key"

        expected_sent = [i.format(**locals()) for i in [
            "GET {path:s} HTTP/1.1",
            "Host: {host:s}",
            "Upgrade: websocket",
            "Connection: Upgrade",
            "Sec-Websocket-Protocol: mqtt",
            "Sec-Websocket-Version: 13",
            "Origin: https://{host:s}:{port:d}",
        ]]

        # Only sends the header once
        assert mocksock.send.call_count == 1

        for i in expected_sent:
            assert i in mocksock.send.call_args[0][0]
