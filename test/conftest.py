"""Shared pytest fixtures for the SBAquaControl host test-suite.

Fixtures:
  mock_server  session-scoped Flask mock on a private port (mirrors the
               old run_checks.py LIVE layer: start, wait, yield base URL,
               terminate). The port is private so it never collides with a
               dev server, and MOCK_DEBUG=0 keeps the log quiet.
  clean_tree   session-scoped snapshot/restore of every file the mock
               writes to, so a live run leaves the working tree unchanged
               (result stays `git status`-verifiable).

Helpers (pio_command) live here so the build/unit modules stay thin.
"""

import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

import pytest
import test_api_parity as parity

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def pio_command():
    """Prefer a pio on PATH, else fall back to the uv-managed one."""
    if shutil.which("pio"):
        return ["pio"]
    if shutil.which("uv"):
        return ["uv", "run", "pio"]
    return None


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_server(base, timeout=25):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(base + "/api/status", timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            time.sleep(0.4)
    return False


@pytest.fixture(scope="session")
def mock_server():
    """Start test/mock_server.py on a private port; yield its base URL."""
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    env = dict(os.environ, MOCK_PORT=str(port), MOCK_DEBUG="0")
    # Closed in the fixture's finally block (must outlive Popen) — noqa: SIM115
    log = open(  # noqa: SIM115
        os.path.join(HERE, ".mock_server.log"), "w", encoding="utf-8"
    )
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "mock_server.py")],
        cwd=REPO,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    try:
        if not wait_for_server(base):
            pytest.fail(
                f"mock server did not come up on {base} (see test/.mock_server.log)"
            )
        yield base
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        log.close()


@pytest.fixture(scope="session")
def clean_tree():
    """Snapshot fixture files before the live run, restore them after."""
    state = parity.snapshot(parity.FIXTURES + parity.CREATED)
    yield
    touched = parity.restore(state)
    if touched:
        print(f"\nRestored {len(touched)} fixture file(s) touched by the live run.")
