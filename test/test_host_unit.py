"""Host unit tests for the firmware scheduling maths.

Runs `pio test -e test`: env:test excludes src/ (it cannot compile on
the PC - Arduino/ESP8266 headers) and builds only the dependency-free
mirror in test/support/ plus the Unity tests in test/test_pwm_logic.cpp.

These always run. Needs PlatformIO with the native toolchain (skipped
if neither `pio` nor `uv` is available).
"""

import re
import subprocess

import pytest
from conftest import REPO, pio_command


def test_host_unit_tests_pass():
    cmd = pio_command()
    if cmd is None:
        pytest.skip("neither 'pio' nor 'uv' available - unit tests not verified")

    proc = subprocess.run(
        cmd + ["test", "-e", "test"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,  # returncode is asserted below
    )
    out = proc.stdout + proc.stderr
    passed = len(re.findall(r": (test_\w+)\s+\[PASSED\]", out))
    assert proc.returncode == 0 and "FAILED" not in out, (
        "host unit tests failed:\n" + "\n".join(out.strip().splitlines()[-10:])
    )
    assert passed > 0, "no unit tests ran (expected test/test_*.cpp cases)"
    print(f"\n{passed} host unit test(s) passed")
