import socket
import sys

if sys.version_info < (3, 0):
    from mock import Mock
else:
    from unittest.mock import Mock

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
            for i in "\r\n".join(response).encode("utf8"):
                yield i

            for i in "\r\n".encode("utf8"):
                yield i

        it = iter_response()

        def fakerecv(*args):
            if sys.version_info < (3, 0):
                return next(it)
            else:
                return bytes([next(it)])

        mocksock = Mock(
            spec_set=socket.socket,
            recv=fakerecv,
            send=Mock(),
        )

        wargs = {
            "host": "testhost.com",
            "port": 1234,
            "path": "/mqtt",
            "extra_headers": None,
            "is_ssl": True,
            "socket": mocksock,
        }

        with pytest.raises(WebsocketConnectionError) as exc:
            WebsocketWrapper(**wargs)

        # We're not creating the response hash properly so it should raise this
        # error
        assert str(exc.value) == "WebSocket handshake error, invalid secret key"

        expected_sent = [i.format(**wargs) for i in [
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
            assert i in mocksock.send.call_args[0][0].decode("utf8")
