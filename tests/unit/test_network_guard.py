import socket

import pytest


def test_network_guard_blocks_socket_connections():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(RuntimeError, match="Live network access is blocked"):
            sock.connect(("93.184.216.34", 80))
    finally:
        sock.close()


def test_network_guard_blocks_create_connection():
    with pytest.raises(RuntimeError, match="Live network access is blocked"):
        socket.create_connection(("93.184.216.34", 80), timeout=0.01)


@pytest.mark.allow_network
def test_network_guard_marker_restores_socket_patch(original_socket_connect):
    assert socket.socket.connect is original_socket_connect
