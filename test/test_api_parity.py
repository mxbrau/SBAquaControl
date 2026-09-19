#!/usr/bin/env python3
"""
Route/contract parity guard for the SBAquaControl mock server.

The mock (test/mock_server.py) is the only way to develop the web UI without
hardware, so it has to stay in step with the firmware. This script:

  1. parses the firmware route table (src/AquaControl.cpp, _Server.on(...))
  2. parses the mock route table (test/mock_server.py, @app.route(...))
  3. fails if the firmware exposes a route the mock does not

With --live it also exercises a running mock and checks response status codes
and field names against the firmware contract.

Usage:
    uv run python test/test_api_parity.py                    # static check only
    uv run python test/test_api_parity.py --live             # + smoke test :5000
    uv run python test/test_api_parity.py --live --base-url http://127.0.0.1:5000

Tracked fixture files that the mock rewrites during --live are snapshotted and
restored, so running this never leaves the repo dirty.
"""

import argparse
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FIRMWARE = os.path.join(REPO, "src", "AquaControl.cpp")
MOCK = os.path.join(HERE, "mock_server.py")

# Files the mock writes to; restored after --live so the working tree stays clean.
# schedules.json is the tracked read-only seed - the mock persists to the
# git-ignored runtime file next to it.
FIXTURES = [
    os.path.join(HERE, "data", "schedules.runtime.json"),
    *[os.path.join(REPO, "extras", "SDCard", "config", f"ledch_{i:02d}.cfg") for i in range(6)],
]
# Files the mock may create from scratch; removed after --live if they did not exist.
CREATED = [os.path.join(REPO, "extras", "SDCard", "config", "channels.cfg")]


def parse_firmware_routes(path):
    """(method, uri) pairs from the firmware route table."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()
    routes = set()
    pattern = re.compile(
        r'_Server\.on\(\s*"([^"]+)"\s*(?:,\s*(HTTP_[A-Z]+))?', re.MULTILINE
    )
    for uri, method in pattern.findall(source):
        if method in ("HTTP_GET", "HTTP_POST"):
            routes.add((method.replace("HTTP_", ""), uri))
        else:  # on(uri, handler) registers HTTP_ANY - the mock serves it as GET
            routes.add(("GET", uri))
    return routes


def parse_mock_routes(path):
    """(method, uri) pairs from the Flask route decorators."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()
    routes = set()
    pattern = re.compile(
        r'@app\.route\(\s*"([^"]+)"\s*(?:,\s*methods=\s*\[([^\]]*)\])?', re.MULTILINE
    )
    for uri, methods in pattern.findall(source):
        found = re.findall(r'"([A-Z]+)"', methods) or ["GET"]
        for method in found:
            routes.add((method, uri))
    return routes


def check_route_parity():
    firmware = parse_firmware_routes(FIRMWARE)
    mock = parse_mock_routes(MOCK)
    missing = sorted(firmware - mock)
    extra = sorted(mock - firmware)

    print("=" * 66)
    print("Static route parity: firmware (src/AquaControl.cpp) vs mock")
    print("=" * 66)
    for method, uri in sorted(firmware):
        mark = "ok " if (method, uri) in mock else "MISSING"
        print(f"  [{mark:>7}] {method:5} {uri}")
    if extra:
        print("\n  Mock-only routes (fine if intentional):")
        for method, uri in extra:
            print(f"            {method:5} {uri}")
    return missing


# === Live smoke test ===


def request(method, url, body=None, files=None):
    """Return (status, parsed_json_or_text)."""
    data = None
    headers = {}
    if files is not None:
        boundary = uuid.uuid4().hex
        parts = []
        for name, (filename, content) in files.items():
            parts.append(f"--{boundary}\r\n".encode())
            parts.append(
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
            )
            parts.append(b"Content-Type: application/octet-stream\r\n\r\n")
            parts.append(content + b"\r\n")
        for name, value in (body or {}).items():
            parts.append(f"--{boundary}\r\n".encode())
            parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
            parts.append(f"{value}\r\n".encode())
        parts.append(f"--{boundary}--\r\n".encode())
        data = b"".join(parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8", "replace")
            status = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        status = e.code
    try:
        return status, json.loads(raw)
    except json.JSONDecodeError:
        return status, raw


def live_checks():
    """(label, method, path, body, expected_status, required_keys)."""
    return [
        ("status", "GET", "/api/status", None, 200,
         ["test_mode", "time", "current_seconds", "time_source", "rtc_present",
          "time_valid", "needs_time_sync", "last_sync_ts", "temperature",
          "wifi_connected", "sd_card_ok", "uptime", "macro_active"]),
        ("schedule/get valid", "GET", "/api/schedule/get?channel=0", None, 200,
         ["channel", "targets"]),
        ("schedule/get rejects ch=6", "GET", "/api/schedule/get?channel=6", None, 400, ["error"]),
        ("schedule/all", "GET", "/api/schedule/all", None, 200, ["schedules"]),
        ("schedule/save", "POST", "/api/schedule/save",
         {"channel": 0, "targets": [{"time": 3600, "value": 50}]}, 200,
         ["status", "channel", "target_count"]),
        ("schedule/target/add", "POST", "/api/schedule/target/add",
         {"channel": 1, "time": 7200, "value": 42}, 200, ["success"]),
        ("schedule/target/delete", "POST", "/api/schedule/target/delete",
         {"channel": 1, "time": 7200}, 200, ["status"]),
        ("schedule/clear", "POST", "/api/schedule/clear", {}, 200, ["status", "message"]),
        ("test/start", "POST", "/api/test/start", {}, 200, ["status", "test_mode"]),
        ("test/update values[]", "POST", "/api/test/update", {"values": [1, 2, 3]}, 200, ["status"]),
        ("test/update single ch", "POST", "/api/test/update", {"channel": 2, "value": 77}, 200,
         ["status"]),
        ("test/exit", "POST", "/api/test/exit", {}, 200, ["status", "test_mode"]),
        ("macro/list", "GET", "/api/macro/list", None, 200, ["macros"]),
        ("macro/get", "GET", "/api/macro/get?id=macro_001", None, 200,
         ["id", "name", "duration", "channels"]),
        ("macro/get without id", "GET", "/api/macro/get", None, 400, ["error"]),
        ("macro/activate", "POST", "/api/macro/activate", {"id": "macro_001", "duration": 600},
         200, ["status", "expires_in"]),
        ("status shows macro_id/expires_in", "GET", "/api/status", None, 200,
         ["macro_active", "macro_id", "macro_expires_in"]),
        ("macro/stop", "POST", "/api/macro/stop", {}, 200, ["status"]),
        ("macro/stop with none active", "POST", "/api/macro/stop", {}, 400, ["error"]),
        ("macro/save", "POST", "/api/macro/save",
         {"name": "Parity Test", "duration": 1200,
          "channels": [{"channel": 0, "targets": [{"time": 0, "value": 10}]}]},
         200, ["status", "id", "name", "duration"]),
        ("macro/delete unknown id", "POST", "/api/macro/delete", {"id": "macro_999"}, 200,
         ["status"]),
        ("macro/delete without id", "POST", "/api/macro/delete", {}, 400, ["error"]),
        ("reboot", "POST", "/api/reboot", {}, 200, ["status"]),
        ("debug", "GET", "/api/debug", None, 200,
         ["free_heap", "max_free_block", "heap_fragmentation", "uptime_ms",
          "vcc_voltage_mv", "cpu_freq_mhz", "macros"]),
        ("time/set", "POST", "/api/time/set", {"hour": 12, "minute": 30, "second": 0}, 200,
         ["status", "time"]),
        ("time/set rejects hour=99", "POST", "/api/time/set", {"hour": 99, "minute": 0, "second": 0},
         400, ["error"]),
        ("config/channels get", "GET", "/api/config/channels", None, 200, ["channels"]),
    ]


def snapshot(paths):
    """Remember file contents so the live run leaves no trace."""
    state = {}
    for path in paths:
        if os.path.exists(path):
            with open(path, "rb") as f:
                state[path] = f.read()
        else:
            state[path] = None
    return state


def restore(state):
    changed = []
    for path, content in state.items():
        if content is None:
            if os.path.exists(path):
                os.remove(path)
                changed.append(path)
            continue
        current = None
        if os.path.exists(path):
            with open(path, "rb") as f:
                current = f.read()
        if current != content:
            with open(path, "wb") as w:
                w.write(content)
            changed.append(path)
    return changed


def run_live(base):
    print()
    print("=" * 66)
    print(f"Live contract checks against {base}")
    print("=" * 66)

    state = snapshot(FIXTURES + CREATED)
    failures = []
    try:
        for label, method, path, body, expected, keys in live_checks():
            status, payload = request(method, base + path, body)
            problems = []
            if status != expected:
                problems.append(f"status {status}, expected {expected}")
            if isinstance(payload, dict):
                missing = [k for k in keys if k not in payload]
                if missing:
                    problems.append(f"missing keys {missing}")
            elif expected == 200:
                problems.append("response was not JSON")
            if problems:
                failures.append((label, problems))
                print(f"  [  FAIL] {method:5} {path:32} {'; '.join(problems)}")
            else:
                print(f"  [    ok] {method:5} {path:32} {status}")

        # /upload needs multipart; go through the request helper directly.
        status, payload = request(
            "POST", base + "/upload",
            body={"path": "data/__parity_upload.tmp"},
            files={"file": ("__parity_upload.tmp", b"parity")},
        )
        if status == 200 and isinstance(payload, dict) and payload.get("success") is True:
            print(f"  [    ok] POST  /upload                           {status}")
            uploaded = os.path.join(REPO, "extras", "SDCard", "data", "__parity_upload.tmp")
            if os.path.exists(uploaded):
                os.remove(uploaded)
            parent = os.path.dirname(uploaded)
            if os.path.isdir(parent) and not os.listdir(parent):
                os.rmdir(parent)
        else:
            failures.append(("upload", [f"status {status}, payload {payload}"]))
            print(f"  [  FAIL] POST  /upload                           {status} {payload}")
    finally:
        touched = restore(state)
        if touched:
            print(f"\n  Restored {len(touched)} fixture file(s) touched by the live run.")

    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="also smoke-test a running mock server")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    args = parser.parse_args()

    missing = check_route_parity()
    failures = []
    if args.live:
        failures = run_live(args.base_url.rstrip("/"))

    print()
    if missing or failures:
        if missing:
            print(f"FAIL: {len(missing)} firmware route(s) missing from the mock:")
            for method, uri in missing:
                print(f"  - {method} {uri}")
        if failures:
            print(f"FAIL: {len(failures)} live check(s) failed.")
        return 1

    suffix = " and live contract checks" if args.live else ""
    print(f"PASS: route parity{suffix} verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
