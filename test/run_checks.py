#!/usr/bin/env python3
"""
One-command check runner for SBAquaControl - the automated part of the test plan.

Runs, in order:
  1. BUILD   firmware compiles for env:esp8266 (RAM/Flash reported, budget checked)
  2. PARITY  every firmware route exists in the mock (static, no server needed)
  3. LIVE    mock server is started on a private port, all endpoints are exercised
             against the firmware contract, then the server is stopped again

Everything it touches is restored, so the working tree is unchanged afterwards.

Usage:
    uv run python test/run_checks.py                 # full run
    uv run python test/run_checks.py --skip-build    # fast: parity + live only
    uv run python test/run_checks.py --only live

Not covered here (needs real hardware - see docs/status/TESTING_GUIDE.md):
LED output, PWM/PCA9685 behaviour, DS18B20, OTA, 24h soak.
"""

import argparse
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import test_api_parity as parity  # noqa: E402  (lives next to this file)

# Compile-time budgets (docs/status/FIRMWARE_STATUS.md); a change beyond these
# should be a deliberate decision, not an accident.
# Figures come from the linker size table: RAM = data + bss, flash = text.
RAM_BUDGET_PCT = 70.0
FLASH_BUDGET_PCT = 80.0
RAM_TOTAL_BYTES = 81920  # ESP8266 DRAM available to the sketch
FLASH_TOTAL_BYTES = 1044464  # sketch space on a 4M/1M-SPIFFS layout


def section(title):
    print()
    print("=" * 66)
    print(title)
    print("=" * 66)


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def pio_command():
    """Prefer a pio on PATH, else fall back to the uv-managed one."""
    if shutil.which("pio"):
        return ["pio"]
    if shutil.which("uv"):
        return ["uv", "run", "pio"]
    return None


def check_build():
    # '-t size' always prints the memory table, even when nothing needed rebuilding
    cmd = pio_command()
    if cmd is None:
        return "SKIP", "neither 'pio' nor 'uv' available - build not verified"

    print(f"$ {' '.join(cmd)} run -e esp8266 -t size")
    proc = subprocess.run(
        cmd + ["run", "-e", "esp8266", "-t", "size"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    out = proc.stdout + proc.stderr
    tail = "\n".join(out.strip().splitlines()[-10:])
    print(tail)

    if proc.returncode != 0 or "SUCCESS" not in out:
        return "FAIL", "firmware build failed"

    # Linker size table: "text data bss dec hex filename" (present on every run)
    size_line = None
    for line in out.splitlines():
        if "firmware.elf" in line and re.match(r"\s*\d+\s+\d+\s+\d+\s+\d+\s+[0-9a-fA-F]+\s", line):
            size_line = line
    if size_line is None:
        return "FAIL", "could not find the firmware.elf size line in the build output"

    text, data, bss = (int(v) for v in size_line.split()[:3])
    ram_bytes, flash_bytes = data + bss, text
    ram_pct = 100.0 * ram_bytes / RAM_TOTAL_BYTES
    flash_pct = 100.0 * flash_bytes / FLASH_TOTAL_BYTES

    detail = (
        f"static RAM {ram_pct:.1f}% ({ram_bytes}B data+bss), "
        f"flash {flash_pct:.1f}% ({flash_bytes}B)"
    )
    if ram_pct > RAM_BUDGET_PCT or flash_pct > FLASH_BUDGET_PCT:
        return "FAIL", f"{detail} - exceeds budget RAM<={RAM_BUDGET_PCT}% Flash<={FLASH_BUDGET_PCT}%"
    return "PASS", detail


def check_parity():
    missing = parity.check_route_parity()
    if missing:
        return "FAIL", f"{len(missing)} firmware route(s) missing from the mock"
    return "PASS", "all firmware routes present in the mock"


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


def check_live():
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    env = dict(os.environ, MOCK_PORT=str(port), MOCK_DEBUG="0")
    log = open(os.path.join(REPO, "test", ".mock_server.log"), "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "mock_server.py")],
        cwd=REPO,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    try:
        if not wait_for_server(base):
            return "FAIL", f"mock server did not come up on {base} (see test/.mock_server.log)"
        failures = parity.run_live(base)
        if failures:
            return "FAIL", f"{len(failures)} live check(s) failed"
        return "PASS", f"{len(parity.live_checks())} endpoint checks + upload"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        log.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-build", action="store_true", help="skip the firmware build")
    parser.add_argument(
        "--only", choices=["build", "parity", "live"], help="run a single layer"
    )
    args = parser.parse_args()

    steps = [
        ("BUILD   firmware compiles (env:esp8266)", "build", check_build),
        ("PARITY  mock mirrors the firmware routes", "parity", check_parity),
        ("LIVE    endpoints match the firmware contract", "live", check_live),
    ]

    results = []
    for label, key, fn in steps:
        if args.only and args.only != key:
            continue
        if key == "build" and args.skip_build:
            results.append((label, "SKIP", "--skip-build"))
            continue
        section(label)
        started = time.time()
        try:
            status, detail = fn()
        except Exception as exc:  # a broken harness must not look like a pass
            status, detail = "FAIL", f"{type(exc).__name__}: {exc}"
        elapsed = time.time() - started
        print(f"\n  -> {status} ({elapsed:.1f}s) {detail}")
        results.append((label, status, detail))

    section("SUMMARY")
    for label, status, detail in results:
        print(f"  [{status:>4}] {label:45} {detail}")

    failed = [r for r in results if r[1] == "FAIL"]
    skipped = [r for r in results if r[1] == "SKIP"]
    print()
    if failed:
        print(f"RESULT: FAILED ({len(failed)} layer(s))")
        return 1
    if skipped:
        print(f"RESULT: PASSED with {len(skipped)} skipped layer(s)")
        return 0
    print("RESULT: ALL AUTOMATED LAYERS PASSED")
    print("Remaining: hardware checks in docs/status/TESTING_GUIDE.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
