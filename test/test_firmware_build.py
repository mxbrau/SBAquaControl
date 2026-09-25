"""Firmware build check (marker: `build`).

Compiles env:esp8266 and asserts the image stays inside the RAM/Flash
budgets (docs/status/FIRMWARE_STATUS.md) - a change beyond these should
be a deliberate decision, not an accident. Figures come from the linker
size table: RAM = data + bss, flash = text.

Slow: needs PlatformIO plus the ESP8266 toolchain (skipped if neither
`pio` nor `uv` is available).
Run: `uv run pytest test/ -m build`
"""

import os
import re
import subprocess

import pytest
from conftest import REPO, pio_command

pytestmark = pytest.mark.build

# Compile-time budgets; change deliberately, not accidentally.
RAM_BUDGET_PCT = 70.0
FLASH_BUDGET_PCT = 80.0
RAM_TOTAL_BYTES = 81920  # ESP8266 DRAM available to the sketch
FLASH_TOTAL_BYTES = 1044464  # sketch space on a 4M/1M-SPIFFS layout


def test_firmware_compiles_within_budget():
    cmd = pio_command()
    if cmd is None:
        pytest.skip("neither 'pio' nor 'uv' available - build not verified")
    if not os.path.exists(os.path.join(REPO, "secrets.ini")):
        pytest.skip(
            "secrets.ini (git-ignored, OTA_PASSWORD=...) not present - "
            "the firmware cannot compile without it"
        )

    # '-t size' always prints the memory table, even with nothing to rebuild.
    proc = subprocess.run(
        cmd + ["run", "-e", "esp8266", "-t", "size"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,  # returncode is asserted below
    )
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0 and "SUCCESS" in out, (
        "firmware build failed:\n" + "\n".join(out.strip().splitlines()[-10:])
    )

    # Linker size table: "text data bss dec hex filename" (present on every run).
    size_line = next(
        (
            line
            for line in out.splitlines()
            if "firmware.elf" in line
            and re.match(r"\s*\d+\s+\d+\s+\d+\s+\d+\s+[0-9a-fA-F]+\s", line)
        ),
        None,
    )
    assert size_line is not None, (
        "could not find the firmware.elf size line in the build output"
    )

    text, data, bss = (int(v) for v in size_line.split()[:3])
    ram_pct = 100.0 * (data + bss) / RAM_TOTAL_BYTES
    flash_pct = 100.0 * text / FLASH_TOTAL_BYTES
    print(
        f"\nstatic RAM {ram_pct:.1f}% ({data + bss}B data+bss), "
        f"flash {flash_pct:.1f}% ({text}B)"
    )
    assert ram_pct <= RAM_BUDGET_PCT, (
        f"static RAM {ram_pct:.1f}% exceeds {RAM_BUDGET_PCT}% budget"
    )
    assert flash_pct <= FLASH_BUDGET_PCT, (
        f"flash {flash_pct:.1f}% exceeds {FLASH_BUDGET_PCT}% budget"
    )
