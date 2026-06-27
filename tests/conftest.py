"""Pytest configuration for offline-by-default tests."""

from __future__ import annotations

import os
import socket

import pytest


_ORIGINAL_SOCKET_CONNECT = socket.socket.connect
_ORIGINAL_CREATE_CONNECTION = socket.create_connection


def _network_allowed(request: pytest.FixtureRequest) -> bool:
    return bool(request.node.get_closest_marker("allow_network")) or os.getenv(
        "PORTFOLIO_TRACKER_ALLOW_NETWORK"
    ) == "1"


@pytest.fixture(autouse=True)
def block_live_network(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch):
    """Block outbound socket connections unless explicitly enabled.

    Tests can opt in with ``@pytest.mark.allow_network`` or by setting
    ``PORTFOLIO_TRACKER_ALLOW_NETWORK=1`` for rare live integration checks.
    """

    if _network_allowed(request):
        return

    def guarded_connect(self: socket.socket, address):  # noqa: ANN001
        raise RuntimeError(
            "Live network access is blocked during tests. "
            "Use @pytest.mark.allow_network or PORTFOLIO_TRACKER_ALLOW_NETWORK=1 "
            "only for intentional live integration tests."
        )

    def guarded_create_connection(*args, **kwargs):  # noqa: ANN002, ANN003
        raise RuntimeError(
            "Live network access is blocked during tests. "
            "Use @pytest.mark.allow_network or PORTFOLIO_TRACKER_ALLOW_NETWORK=1 "
            "only for intentional live integration tests."
        )

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket, "create_connection", guarded_create_connection)


@pytest.fixture
def original_socket_connect():
    """Expose the unpatched socket connect for tests that verify the guard."""

    return _ORIGINAL_SOCKET_CONNECT


@pytest.fixture
def original_create_connection():
    """Expose the unpatched create_connection for tests that verify the guard."""

    return _ORIGINAL_CREATE_CONNECTION
