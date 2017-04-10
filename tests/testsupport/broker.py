import socket

import pytest


class FakeBroker:
    def __init__(self):
        # Bind to "localhost" for maximum performance, as described in:
        # http://docs.python.org/howto/sockets.html#ipc
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(30)
        sock.bind(("localhost", 1888))
        sock.listen(1)

        self._sock = sock
        self._conn = None

    def start(self):
        if self._sock is None:
            raise ValueError('Socket is not open')

        (conn, address) = self._sock.accept()
        conn.settimeout(10)
        self._conn = conn

    def finish(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def expect_packet(self, packet_expected):
        if self._conn is None:
            raise ValueError('Connection is not open')

        packet_in = self._conn.recv(len(packet_expected))
        if not packet_in:
            raise RuntimeError('Connection was closed')
        assert packet_in == packet_expected

    def send_packet(self, packet_out):
        if self._conn is None:
            raise ValueError('Connection is not open')

        count = self._conn.send(packet_out)
        if not count:
            raise RuntimeError('Connection was closed')


@pytest.fixture
def fake_broker():
    # print('Setup server')
    server = FakeBroker()

    yield server

    # print('Teardown server')
    server.finish()
