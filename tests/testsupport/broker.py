import socket
from six.moves import socketserver
import threading
import contextlib

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

    def receive_packet(self, num_bytes):
        if self._conn is None:
            raise ValueError('Connection is not open')

        packet_in = self._conn.recv(num_bytes)
        return packet_in

    def send_packet(self, packet_out):
        if self._conn is None:
            raise ValueError('Connection is not open')

        count = self._conn.send(packet_out)
        return count


@pytest.fixture
def fake_broker():
    # print('Setup broker')
    broker = FakeBroker()

    yield broker

    # print('Teardown broker')
    broker.finish()


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class FakeWebsocketBroker(threading.Thread):
    def __init__(self):
        super(FakeWebsocketBroker, self).__init__()

        self.host = "localhost"
        self.port = 1888

        self._server = None
        self._running = True
        self.handler_cls = False

    @contextlib.contextmanager
    def serve(self, tcphandler):
        self._server = ThreadedTCPServer((self.host, self.port), tcphandler)

        try:
            self.start()

            if not self._running:
                raise RuntimeError("Error starting server")
            yield
        finally:
            if self._server:
                self._server.shutdown()
                self._server.server_close()

    def run(self):
        self._running = True
        self._server.serve_forever()


@pytest.fixture
def fake_websocket_broker():
    socketserver.TCPServer.allow_reuse_address = True

    broker = FakeWebsocketBroker()

    yield broker
