import os
import signal
import subprocess
import sys

import pytest

from tests.consts import ssl_path, tests_path
from tests.paho_test import create_server_socket, create_server_socket_ssl

clients_path = tests_path / "lib" / "clients"


@pytest.fixture()
def server_socket(monkeypatch):
    sock, port = create_server_socket()
    monkeypatch.setenv("PAHO_SERVER_PORT", str(port))
    try:
        yield sock
    finally:
        sock.close()


@pytest.fixture()
def ssl_server_socket(monkeypatch):
    sock, port = create_server_socket_ssl()
    monkeypatch.setenv("PAHO_SERVER_PORT", str(port))
    try:
        yield sock
    finally:
        sock.close()


def stop_process(proc: subprocess.Popen) -> None:
    if sys.platform == "win32":
        proc.send_signal(signal.CTRL_C_EVENT)
    else:
        proc.send_signal(signal.SIGINT)
    try:
        proc.wait(5)
    except subprocess.TimeoutExpired:
        proc.terminate()


@pytest.fixture()
def start_client(request: pytest.FixtureRequest):
    def starter(name: str, expected_returncode: int = 0) -> None:
        client_path = clients_path / name
        if not client_path.exists():
            raise FileNotFoundError(client_path)
        env = dict(
            os.environ,
            PAHO_SSL_PATH=str(ssl_path),
            PYTHONPATH=f"{tests_path}{os.pathsep}{os.environ.get('PYTHONPATH', '')}",
        )
        assert 'PAHO_SERVER_PORT' in env, "PAHO_SERVER_PORT must be set in the environment when starting a client"
        # TODO: it would be nice to run this under `coverage` too!
        proc = subprocess.Popen([  # noqa: S603
            sys.executable,
            str(client_path),
        ], env=env)

        def fin():
            stop_process(proc)
            if proc.returncode != expected_returncode:
                raise RuntimeError(f"Client {name} exited with code {proc.returncode}, expected {expected_returncode}")

        request.addfinalizer(fin)
        return proc

    return starter
