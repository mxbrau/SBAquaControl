"""Static route-parity checks.

Every route the firmware registers (`_Server.on(...)` in
src/AquaControl.cpp) must also exist in the mock
(`@app.route(...)` in test/mock_server.py) - the mock is the only way
to develop the web UI without hardware, so a divergence is a bug in
one of the two.

Fast: pure file parsing, no server, no toolchain. Always run.
"""

import pytest
import test_api_parity as parity


def _firmware_routes():
    return sorted(parity.parse_firmware_routes(parity.FIRMWARE))


def _mock_routes():
    return parity.parse_mock_routes(parity.MOCK)


def test_parsers_find_routes():
    """Guard against a parser silently matching nothing (vacuous pass)."""
    assert _firmware_routes(), f"no routes parsed from {parity.FIRMWARE}"
    assert _mock_routes(), f"no routes parsed from {parity.MOCK}"


@pytest.mark.parametrize("method,uri", _firmware_routes())
def test_firmware_route_exists_in_mock(method, uri):
    assert (method, uri) in _mock_routes(), (
        f"{method} {uri} is served by the firmware but missing from the mock - "
        "add it to test/mock_server.py"
    )
