"""Contract checks against the mock server.

Each row of `live_checks()` in test_api_parity.py becomes one test:
status code plus required JSON fields, exactly as src/Webserver.cpp
defines them. The `mock_server` fixture starts a private mock instance
per session (localhost only - never the real device); `clean_tree`
restores every file it touches.

These always run: the mock starts in a fraction of a second and needs
no toolchain.
"""

import os

import pytest

import test_api_parity as parity


def _check(label, method, path, body, expected, keys, base):
    status, payload = parity.request(method, base + path, body)
    assert status == expected, (
        f"{label}: {method} {path} returned status {status}, expected {expected} "
        f"(payload {payload!r})"
    )
    if isinstance(payload, dict):
        missing = [k for k in keys if k not in payload]
        assert not missing, f"{label}: response is missing keys {missing} ({payload!r})"
    elif expected == 200:
        pytest.fail(f"{label}: response was not JSON ({payload!r})")


@pytest.mark.parametrize(
    "label,method,path,body,expected,keys", parity.live_checks()
)
def test_endpoint(label, method, path, body, expected, keys, mock_server, clean_tree):
    _check(label, method, path, body, expected, keys, mock_server)


def test_upload(mock_server, clean_tree):
    """/upload needs multipart, so it goes through the helper directly."""
    status, payload = parity.request(
        "POST",
        mock_server + "/upload",
        body={"path": "data/__pytest_upload.tmp"},
        files={"file": ("__pytest_upload.tmp", b"pytest")},
    )
    assert status == 200 and isinstance(payload, dict) and payload.get("success") is True, (
        f"upload failed: status {status}, payload {payload!r}"
    )
    uploaded = os.path.join(parity.REPO, "extras", "SDCard", "data", "__pytest_upload.tmp")
    if os.path.exists(uploaded):
        os.remove(uploaded)
    parent = os.path.dirname(uploaded)
    if os.path.isdir(parent) and not os.listdir(parent):
        os.rmdir(parent)
