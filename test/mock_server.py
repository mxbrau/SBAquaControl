"""
Mock API Server for SBAquaControl UI Development
Simulates the ESP8266 API endpoints for browser-based testing.

CONTRACT: every response below mirrors src/Webserver.cpp one-to-one
(route names, JSON field names, HTTP status codes and limits). When the
firmware changes, change this file in the same commit - run
`python test/test_api_parity.py` to catch missing routes.

Deliberate differences from the device:
  * macros live in memory instead of SD card files (macros/<id>_chNN.cfg)
  * /api/debug reports synthetic heap figures
  * /api/reboot resets the mock's runtime state instead of restarting
  * the tracked seed test/data/schedules.json is read-only; runtime state goes to
    the git-ignored test/data/schedules.runtime.json (delete it to reset)
  * POST /api/schedule/clear deletes extras/SDCard/config/ledch_*.cfg, exactly as
    the device deletes its SD configs; re-save a channel to recreate them

Seed and runtime data respect the device cap of 32 targets per channel.
test/test_api_parity.py snapshots and restores every file a live run touches.

Usage:
    pip install flask flask-cors      # or: uv sync
    python test/mock_server.py

Then open: http://localhost:5000
"""

import json
import os
import time
from datetime import datetime
from typing import Any

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


# Simple persistence for mock data and SD-card style files
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
# schedules.json is the tracked, device-representative SEED (read-only).
# Runtime state lives in the git-ignored schedules.runtime.json, so normal UI
# development never dirties the repo. Delete that file to reset to the seed.
SEED_SCHEDULE_FILE = os.path.join(DATA_DIR, "schedules.json")
SCHEDULE_FILE = os.path.join(DATA_DIR, "schedules.runtime.json")
SD_CONFIG_DIR = os.path.join(
    os.path.dirname(__file__), "..", "extras", "SDCard", "config"
)

# Limits mirrored from the firmware
CHANNELS = 6  # Webserver.cpp hardcodes channels 0-5 for schedule/macro/test/config
MAX_TARGETS = 32  # MAX_TARGET_COUNT_PER_CHANNEL for ESP8266 (AquaControl_config.h)
TEST_MODE_TIMEOUT_S = 60  # AquaControl.cpp:1185 test mode auto-exits after 60 s
GET_VCC_MV = 3300  # ESP.getVcc() on the mock
CPU_FREQ_MHZ = 160  # ESP8266 default


def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def load_schedules_from_disk():
    """Load runtime state, falling back to the pristine tracked seed."""
    for path, kind in ((SCHEDULE_FILE, "runtime"), (SEED_SCHEDULE_FILE, "seed")):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print(f"ℹ Loaded schedules from {kind}: {path}")
                return {int(k): v for k, v in data.items()}
            except Exception as e:  # noqa: BLE001 — fall back to next seed source
                print(f"⚠ Could not load schedules from {path}: {e}")
    return None


def save_schedules_to_disk():
    try:
        ensure_data_dir()
        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump(schedules, f, indent=2)
        print(f"✓ Persisted schedules to {SCHEDULE_FILE}")
    except Exception as e:  # noqa: BLE001 — persist is best-effort, runtime continues
        print(f"⚠ Could not save schedules: {e}")


def ensure_sd_dir():
    if not os.path.exists(SD_CONFIG_DIR):
        os.makedirs(SD_CONFIG_DIR)


def channel_cfg_path(channel: int) -> str:
    """config/ledch_XX.cfg - the filename the firmware writes (0-padded)."""
    return os.path.join(SD_CONFIG_DIR, f"ledch_{channel:02d}.cfg")


def write_channel_cfg(channel: int, targets):
    """Persist targets in the same format the firmware uses: config/ledch_XX.cfg"""
    try:
        ensure_sd_dir()
        fname = channel_cfg_path(channel)
        # Sort targets by time and write as HH:MM;VALUE lines
        # Cap the number of targets and sort
        sorted_targets = sorted(targets, key=lambda t: int(t.get("time", 0)))[
            :MAX_TARGETS
        ]
        with open(fname, "w", encoding="utf-8") as f:
            for t in sorted_targets:
                seconds = int(t.get("time", 0))
                seconds = max(0, min(86400, seconds))
                hour = seconds // 3600
                minute = (seconds % 3600) // 60
                value = int(t.get("value", 0))
                value = max(0, min(100, value))
                f.write(f"{hour:02d}:{minute:02d};{value}\r\n")
        print(f"✓ Persisted channel {channel} to SD config {fname}")
    except Exception as e:  # noqa: BLE001 — persist is best-effort, runtime continues
        print(f"⚠ Could not write SD config for channel {channel}: {e}")


def normalize_targets(targets, keep_is_control=True):
    """Clamp/sort/coerce targets exactly like the firmware does."""
    cleaned = []
    for t in targets or []:
        seconds = int(t.get("time", 0) or 0)
        value = int(t.get("value", 0) or 0)
        item = {
            "time": max(0, min(86400, seconds)),
            "value": max(0, min(100, value)),
        }
        if keep_is_control:
            item["isControl"] = bool(t.get("isControl", True))
        cleaned.append(item)
    cleaned.sort(key=lambda t: t["time"])
    return cleaned[:MAX_TARGETS]


def as_control_points(targets):
    """The firmware reports every stored target as a control point (Webserver.cpp:258),
    so isControl is always true on the wire - interpolated points only exist client-side."""
    return [
        {"time": int(t["time"]), "value": int(t["value"]), "isControl": True}
        for t in targets or []
    ]


# Mock data storage
schedules = load_schedules_from_disk() or {
    0: [
        {"time": 25200, "value": 0, "isControl": True},  # 07:00 → 0%
        {"time": 28800, "value": 50, "isControl": True},  # 08:00 → 50%
        {"time": 43200, "value": 100, "isControl": True},  # 12:00 → 100%
        {"time": 64800, "value": 80, "isControl": True},  # 18:00 → 80%
        {"time": 75600, "value": 30, "isControl": True},  # 21:00 → 30%
        {"time": 79200, "value": 0, "isControl": True},  # 22:00 → 0%
    ],
    1: [
        {"time": 28800, "value": 40, "isControl": True},  # 08:00 → 40%
        {"time": 39600, "value": 90, "isControl": True},
        {"time": 68400, "value": 20, "isControl": True},
    ],
    2: [
        {"time": 21600, "value": 30, "isControl": True},
        {"time": 46800, "value": 80, "isControl": True},
        {"time": 72000, "value": 10, "isControl": True},
    ],
    3: [
        {"time": 32400, "value": 60, "isControl": True},
        {"time": 50400, "value": 70, "isControl": True},
        {"time": 61200, "value": 40, "isControl": True},
    ],
    4: [
        {"time": 36000, "value": 20, "isControl": True},
        {"time": 54000, "value": 50, "isControl": True},
        {"time": 75600, "value": 5, "isControl": True},
    ],
    5: [
        {"time": 72000, "value": 0, "isControl": True},  # 20:00 → 0%
        {"time": 79200, "value": 15, "isControl": True},  # 22:00 → 15% (moonlight)
        {"time": 86400, "value": 0, "isControl": True},  # 24:00 → 0%
    ],
}

# Macros are stored as {id: {"name": str, "duration": int, "channels": {ch: [targets]}}}
# The firmware keeps them in SD files macros/<id>_chNN.cfg plus macros/<id>.json.
macros: dict[str, dict[str, Any]] = {
    "macro_001": {
        "name": "Movie Mode",
        "duration": 7200,  # 2 hours
        "channels": {
            0: [
                {"time": 0, "value": 0, "isControl": True},
                {"time": 7200, "value": 0, "isControl": True},
            ],
            1: [
                {"time": 0, "value": 0, "isControl": True},
                {"time": 7200, "value": 0, "isControl": True},
            ],
            2: [
                {"time": 0, "value": 0, "isControl": True},
                {"time": 7200, "value": 0, "isControl": True},
            ],
            3: [
                {"time": 0, "value": 0, "isControl": True},
                {"time": 7200, "value": 0, "isControl": True},
            ],
            4: [
                {"time": 0, "value": 0, "isControl": True},
                {"time": 7200, "value": 0, "isControl": True},
            ],
            5: [
                {"time": 0, "value": 5, "isControl": True},
                {"time": 7200, "value": 5, "isControl": True},
            ],
        },
    },
    "macro_002": {
        "name": "Maintenance",
        "duration": 3600,  # 1 hour
        "channels": {
            i: [
                {"time": 0, "value": 100, "isControl": True},
                {"time": 3600, "value": 100, "isControl": True},
            ]
            for i in range(CHANNELS)
        },
    },
}


# Runtime state (mirrors the ESP8266 globals)
test_mode_active = False
test_values = [0] * CHANNELS
test_mode_set_at = None  # monotonic timestamp of the last test-mode update
active_macro = None
macro_activated_at = None  # monotonic timestamp
macro_duration = 0
boot_at = time.monotonic()
clock_offset_seconds = 0  # adjusted by /api/time/set
time_sync_source = "rtc"  # "ntp" | "rtc" | "api" | "unknown"
last_sync_ts = 0
needs_time_sync = False

# Issue #28: in-RAM mirror of the device's log/events.log. Boot line is
# appended by the startup path below; API transitions append via sd_log().
SD_EVENT_LOG: list[str] = []


def sd_log(line: str) -> None:
    """Append one entry to the mock's event-log mirror (issues #28)."""
    SD_EVENT_LOG.append(line)


def now_local() -> datetime:
    """Device time: wall clock shifted by whatever /api/time/set set."""
    # Naive local time is correct here — the device has no timezone concept.
    return datetime.now() + __import__("datetime").timedelta(  # noqa: DTZ005
        seconds=clock_offset_seconds
    )


def current_seconds_of_day() -> int:
    n = now_local()
    return (n.hour * 3600) + (n.minute * 60) + n.second


def uptime_seconds() -> int:
    return int(time.monotonic() - boot_at)


def expire_test_mode_if_stale() -> bool:
    """AquaControl.cpp:1185 - test mode ends 60 s after the last update."""
    global test_mode_active, test_mode_set_at
    if not test_mode_active or test_mode_set_at is None:
        return False
    if (time.monotonic() - test_mode_set_at) > TEST_MODE_TIMEOUT_S:
        test_mode_active = False
        test_mode_set_at = None
        print(f"⏱ Test mode auto-exited after {TEST_MODE_TIMEOUT_S}s")
        sd_log("test_mode_expired")
        return True
    return False


def macro_remaining_seconds():
    """Return remaining seconds, clearing the macro when it expired (restoreSchedule)."""
    global active_macro, macro_activated_at, macro_duration
    if not active_macro or macro_activated_at is None or macro_duration is None:
        return None
    remaining = macro_duration - int(time.monotonic() - macro_activated_at)
    if remaining <= 0:
        print(f"■ Macro '{active_macro}' expired, restoring schedule")
        sd_log(f"macro {active_macro} auto-restored")
        active_macro = None
        macro_activated_at = None
        macro_duration = 0
        return None
    return remaining


def next_macro_id() -> str:
    """Firmware allocates macro_NNN slots; keep allocating above the existing ones."""
    num = 1
    while f"macro_{num:03d}" in macros:
        num += 1
    return f"macro_{num:03d}"


def macro_duration_from_targets(channels) -> int:
    """computeMacroDurationFromFiles(): longest target time across channels."""
    longest = 0
    for targets in (channels or {}).values():
        for t in targets or []:
            longest = max(longest, int(t.get("time", 0) or 0))
    return longest


def json_body() -> dict:
    """Firmware tolerates an empty/missing body; never 500 on a bad request."""
    return request.get_json(silent=True) or {}


# Serve static files
@app.route("/")
def index():
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), "..", "extras", "SDCard"), "app.htm"
    )


@app.route("/<path:path>")
def serve_static(path):
    try:
        return send_from_directory(
            os.path.join(os.path.dirname(__file__), "..", "extras", "SDCard"), path
        )
    except Exception:  # noqa: BLE001 — any serve failure is a 404 for the UI
        return jsonify({"error": "File not found"}), 404


# === Schedule API ===


@app.route("/api/schedule/get")
def get_schedule():
    """Get schedule for a specific channel"""
    channel = int(request.args.get("channel", 0))
    if channel < 0 or channel >= CHANNELS:
        return jsonify({"error": "Invalid channel (must be 0-5)"}), 400

    return jsonify(
        {"channel": channel, "targets": as_control_points(schedules.get(channel, []))}
    )


@app.route("/api/schedule/all")
def get_all_schedules():
    """Get schedules for all 6 channels at once"""
    return jsonify(
        {
            "schedules": [
                {"channel": i, "targets": as_control_points(schedules.get(i, []))}
                for i in range(CHANNELS)
            ]
        }
    )


@app.route("/api/schedule/save", methods=["POST"])
def save_schedule():
    """Save schedule for a specific channel"""
    data = json_body()
    channel = data.get("channel")
    targets = data.get("targets", [])

    if channel is None or channel < 0 or channel >= CHANNELS:
        return jsonify({"error": "Invalid channel"}), 400

    cleaned = normalize_targets(targets)

    schedules[channel] = cleaned
    save_schedules_to_disk()
    write_channel_cfg(channel, cleaned)
    print(f"✓ Saved schedule for channel {channel}: {len(cleaned)} targets")
    return jsonify({"status": "ok", "channel": channel, "target_count": len(cleaned)})


@app.route("/api/schedule/clear", methods=["POST"])
def clear_schedules():
    """Clear every schedule and delete the SD config files (Webserver.cpp:426)"""
    for channel in range(CHANNELS):
        schedules[channel] = []
        cfg = channel_cfg_path(channel)
        if os.path.exists(cfg):
            try:
                os.remove(cfg)
                print(f"✓ Deleted config file: {cfg}")
            except Exception as e:  # noqa: BLE001 — keep deleting the rest
                print(f"⚠ Could not delete {cfg}: {e}")
    save_schedules_to_disk()
    print("✅ All schedules cleared")
    return jsonify({"status": "ok", "message": "All schedules cleared"})


@app.route("/api/schedule/target/add", methods=["POST"])
def add_target():
    """Add a single target point to a channel"""
    data = json_body()
    channel = data.get("channel")
    time_value = data.get("time")
    value = data.get("value")

    if channel is None or time_value is None or value is None:
        return jsonify({"error": "Missing parameters"}), 400
    if channel < 0 or channel >= CHANNELS:
        return jsonify({"error": "Invalid channel"}), 400

    # Convert time string (HH:MM) to seconds if needed
    if isinstance(time_value, str):
        parts = time_value.split(":")
        time_value = int(parts[0]) * 3600 + int(parts[1]) * 60
    else:
        time_value = int(time_value)
    time_value = max(0, min(86400, time_value))
    value = max(0, min(100, int(value)))

    # Add or update target at this time
    current_targets = schedules.get(channel, [])
    # Remove existing target at same time
    current_targets = [t for t in current_targets if t["time"] != time_value]
    current_targets.append({"time": time_value, "value": value, "isControl": True})
    current_targets = normalize_targets(current_targets)
    schedules[channel] = current_targets
    save_schedules_to_disk()
    write_channel_cfg(channel, current_targets)

    print(f"✓ Added target to channel {channel}: time={time_value}s, value={value}%")
    return jsonify({"success": True})


@app.route("/api/schedule/target/delete", methods=["POST"])
def delete_target():
    """Delete a target point from a channel"""
    data = json_body()
    channel = data.get("channel")
    time_value = data.get("time")

    if channel is None or time_value is None:
        return jsonify({"error": "Missing time"}), 400

    # Convert time string (HH:MM) to seconds if needed
    if isinstance(time_value, str):
        parts = time_value.split(":")
        time_value = int(parts[0]) * 3600 + int(parts[1]) * 60
    else:
        time_value = int(time_value)

    current_targets = [t for t in schedules.get(channel, []) if t["time"] != time_value]
    current_targets = normalize_targets(current_targets)
    schedules[channel] = current_targets
    save_schedules_to_disk()
    write_channel_cfg(channel, current_targets)

    print(f"✓ Deleted target from channel {channel}: time={time_value}s")
    return jsonify({"status": "ok"})


# === Test Mode API ===


@app.route("/api/test/start", methods=["POST"])
def test_start():
    """Activate test mode"""
    global test_mode_active, test_mode_set_at
    expire_test_mode_if_stale()
    test_mode_active = True
    test_mode_set_at = time.monotonic()
    print("▶ Test mode ACTIVATED")
    sd_log("test_mode_entered")
    return jsonify({"status": "ok", "test_mode": True})


@app.route("/api/test/update", methods=["POST"])
def test_update():
    """Update test values - accepts {values:[...]} or {channel, value} (Webserver.cpp:645)"""
    global test_mode_set_at
    expire_test_mode_if_stale()
    data = json_body()

    if "values" in data:
        values = data.get("values") or []
        for ch, value in enumerate(values[:CHANNELS]):
            test_values[ch] = max(0, min(100, int(value)))
        print(f"↻ Test values: {test_values}")
    elif "channel" in data and "value" in data:
        channel = int(data["channel"])
        if channel < 0 or channel >= CHANNELS:
            return jsonify({"error": "Invalid channel"}), 400
        test_values[channel] = max(0, min(100, int(data["value"])))
        print(f"↻ Test channel {channel}: {test_values[channel]}")
    else:
        return jsonify({"error": "Missing parameters"}), 400

    # Any update restarts the 60 s timeout window
    test_mode_set_at = time.monotonic()
    return jsonify({"status": "ok"})


@app.route("/api/test/exit", methods=["POST"])
def test_exit():
    """Exit test mode and return to schedule"""
    global test_mode_active, test_mode_set_at
    test_mode_active = False
    test_mode_set_at = None
    print("■ Test mode DEACTIVATED")
    sd_log("test_mode_exited")
    return jsonify({"status": "ok", "test_mode": False})


# === Macro API ===


@app.route("/api/macro/list")
def macro_list():
    """List all available macros: {"macros":[{id,name,duration}]} (Webserver.cpp:914)"""
    listed = [
        {"id": key, "name": value["name"], "duration": value["duration"]}
        for key, value in sorted(macros.items())
    ]
    return jsonify({"macros": listed})


@app.route("/api/macro/get")
def macro_get():
    """Get detailed macro configuration - always all 6 channels (Webserver.cpp:965)"""
    macro_id = request.args.get("id")
    if not macro_id:
        return jsonify({"error": "Missing macro id"}), 400

    macro = macros.get(macro_id)
    name = macro["name"] if macro else macro_id
    duration = macro["duration"] if macro else 0

    channels = []
    for ch in range(CHANNELS):
        targets = macro["channels"].get(ch, []) if macro else []
        channels.append({"channel": ch, "targets": as_control_points(targets)})

    return jsonify(
        {"id": macro_id, "name": name, "duration": duration, "channels": channels}
    )


@app.route("/api/macro/save", methods=["POST"])
def macro_save():
    """Save a new or updated macro: {status,id,name,duration} (Webserver.cpp:1078)"""
    data = json_body()
    requested = (data.get("id") or "").strip()

    # Firmware only honours ids of the form macro_NNN, otherwise it allocates one
    if requested.startswith("macro_"):
        macro_id = requested
    else:
        macro_id = next_macro_id()

    name = (data.get("name") or "").strip() or macro_id
    raw_channels = data.get("channels", []) or []

    channels = {}
    for entry in raw_channels:
        ch = int(entry.get("channel", 0))
        if 0 <= ch < CHANNELS:
            channels[ch] = normalize_targets(entry.get("targets", []))

    duration = int(data.get("duration", 0) or 0)
    if duration == 0:
        duration = macro_duration_from_targets(channels)

    macros[macro_id] = {"name": name, "duration": duration, "channels": channels}
    print(f"✓ Saved macro '{macro_id}': {name} ({duration}s)")

    return jsonify({"status": "ok", "id": macro_id, "name": name, "duration": duration})


@app.route("/api/macro/activate", methods=["POST"])
def macro_activate():
    """Activate a macro: {status,expires_in} / 400 Invalid duration (Webserver.cpp:1430)"""
    global active_macro, macro_activated_at, macro_duration

    data = json_body()
    macro_id = (data.get("id") or "").strip()

    if not macro_id:
        return jsonify({"error": "Missing id"}), 400

    duration = int(data.get("duration", 0) or 0)
    if duration == 0:
        macro = macros.get(macro_id)
        # computeMacroDuration(): longest target of the macro
        duration = macro_duration_from_targets(macro["channels"]) if macro else 0
        if duration == 0 and macro:
            duration = macro.get("duration", 0)

    if duration == 0:
        print(f"❌ Macro activation failed: duration is 0 (id={macro_id})")
        return jsonify({"error": "Invalid duration"}), 400

    active_macro = macro_id
    macro_activated_at = time.monotonic()
    macro_duration = duration
    print(f"🎬 Macro activated: {macro_id}, duration: {duration}s")
    sd_log(f"macro {macro_id} started ({duration}s)")
    return jsonify({"status": "ok", "expires_in": duration})


@app.route("/api/macro/stop", methods=["POST"])
def macro_stop():
    """Stop the active macro; 400 when none is running (Webserver.cpp:1499)"""
    global active_macro, macro_activated_at, macro_duration

    if not macro_remaining_seconds():
        return jsonify({"error": "No macro active"}), 400

    print(f"🛑 Macro stopped manually: {active_macro}")
    sd_log(f"macro {active_macro} stopped manually")
    active_macro = None
    macro_activated_at = None
    macro_duration = 0
    return jsonify({"status": "ok"})


@app.route("/api/macro/delete", methods=["POST"])
def macro_delete():
    """Delete a macro; always 200 unless the id is missing (Webserver.cpp:1514)"""
    data = json_body()
    macro_id = (data.get("id") or "").strip()

    if not macro_id:
        return jsonify({"error": "Invalid id"}), 400

    if macro_id in macros:
        del macros[macro_id]
        print(f"✗ Deleted macro '{macro_id}'")
    else:
        print(f"✗ Macro '{macro_id}' not found, nothing to delete")

    return jsonify({"status": "ok"})


# === Status API ===


@app.route("/api/status")
def status():
    """Get current system status - field names follow Webserver.cpp:144 exactly"""
    expire_test_mode_if_stale()
    remaining = macro_remaining_seconds()
    now = now_local()

    status_data = {
        "test_mode": test_mode_active,
        "time": now.strftime("%H:%M:%S"),
        "current_seconds": current_seconds_of_day(),
        "time_source": time_sync_source,
        "rtc_present": True,
        "time_valid": time_sync_source != "unknown",
        "needs_time_sync": needs_time_sync,
        "last_sync_ts": last_sync_ts,
        "temperature": 24.5,  # Mock temperature (firmware: 0.0 without DS18B20)
        "wifi_connected": True,
        "sd_card_ok": True,
        "uptime": uptime_seconds(),
    }

    if remaining is not None:
        status_data["macro_active"] = True
        status_data["macro_expires_in"] = remaining
        status_data["macro_id"] = active_macro
    else:
        status_data["macro_active"] = False

    return jsonify(status_data)


# === Diagnostics / Control API ===


@app.route("/api/reboot", methods=["POST"])
def reboot():
    """Reboot the device (Webserver.cpp:1581). The mock resets its runtime state instead."""
    global test_mode_active, test_mode_set_at, active_macro, macro_activated_at
    global macro_duration, boot_at

    print("Reboot requested via API (mock: resetting runtime state)")
    test_mode_active = False
    test_mode_set_at = None
    active_macro = None
    macro_activated_at = None
    macro_duration = 0
    boot_at = time.monotonic()  # uptime restarts; RTC time survives
    return jsonify({"status": "rebooting"})


@app.route("/api/debug")
def debug():
    """Heap/memory diagnostics (Webserver.cpp:1590). Figures are synthetic."""
    expire_test_mode_if_stale()

    free_heap = 45000
    max_free_block = 39000
    fragmentation = 100.0 * (1.0 - (max_free_block / free_heap))

    macro_sizes = {}
    for macro_id, macro in sorted(macros.items()):
        macro_sizes[macro_id] = {
            f"ch{ch:02d}": sum(
                len(json.dumps(t)) for t in macro["channels"].get(ch, [])
            )
            for ch in range(CHANNELS)
            if macro["channels"].get(ch)
        }

    # Issue #26: per-channel PWM state mirror (Webserver.cpp handleApiDebug).
    # Targets come from the schedule interpolation; test mode overrides them,
    # exactly like the firmware's PwmChannel::proceedCycle.
    now_s = current_seconds_of_day()
    channels = []
    for ch in range(CHANNELS):
        targets = schedules.get(ch, [])
        vx = 0
        if targets:
            resolved = sorted(targets, key=lambda t: t["time"])
            points = [(t["time"], t["value"]) for t in resolved]
            # find bracketing pair
            lo, hi = points[0], points[-1] if len(points) > 1 else (points[0][0] + 86400, points[0][1])
            for i in range(len(points) - 1):
                t0, v0 = points[i]
                t1, v1 = points[i + 1]
                if t0 <= now_s < t1:
                    lo, hi = (t0, v0), (t1, v1)
                    break
            else:
                lo, hi = points[-1], (points[0][0] + 86400, points[0][1])
            t0, v0 = lo
            t1, v1 = hi
            span = max(t1 - t0, 1)
            frac = min(max((now_s - t0) / span, 0.0), 1.0)
            # firmware interpolates linearly then clamps; but the clamp happens only toward the slope,
            # mirroring exactly is out of scope: aim is shape parity, not bit parity.
            vx = v0 + frac * (v1 - v0)
        in_test = test_mode_active
        target = int(test_values[ch] if in_test else round(vx))
        state = {
            "ch": ch,
            "target": target,
            "value": target,  # no slew modeling in the mock
            "write": target,
            "test_mode": in_test,
            "test_value": test_values[ch],
            "target_count": len(targets),
        }
        channels.append(state)

    return jsonify(
        {
            "free_heap": free_heap,
            "max_free_block": max_free_block,
            "heap_fragmentation": round(fragmentation, 1),
            "uptime_ms": uptime_seconds() * 1000,
            "vcc_voltage_mv": GET_VCC_MV,
            "cpu_freq_mhz": CPU_FREQ_MHZ,
            "macros": macro_sizes,
            "channels": channels,
            # Issue #28 mirror: the mock cannot simulate an SD card, so the log
            # is a small in-RAM list it appends to on the same events.
            "log": {
                "sd_ok": True,
                "lines_this_boot": len(SD_EVENT_LOG),
                "size_bytes": sum(len(l) + 1 for l in SD_EVENT_LOG),
                "last_n": 8,
                "last_events": SD_EVENT_LOG[-8:],
            },
        }
    )


@app.route("/api/time/set", methods=["POST"])
def time_set():
    """Set device time: {hour,minute,second} -> {status,time} (Webserver.cpp:1861)"""
    global clock_offset_seconds, time_sync_source, last_sync_ts, needs_time_sync

    data = json_body()
    hour = data.get("hour")
    minute = data.get("minute")
    second = data.get("second")

    if hour is None or minute is None or second is None:
        return jsonify(
            {"error": "Missing or invalid time field (hour/minute/second)"}
        ), 400

    hour, minute, second = int(hour), int(minute), int(second)
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        return (
            jsonify(
                {
                    "error": "Invalid time values (hour: 0-23, minute: 0-59, second: 0-59)"
                }
            ),
            400,
        )

    # Mirror RTC.set(): keep the date, move the wall clock to the requested time
    target = now_local().replace(hour=hour, minute=minute, second=second, microsecond=0)
    # Both naive local times — consistent by construction (device has no tz).
    clock_offset_seconds = (target - datetime.now()).total_seconds()  # noqa: DTZ005

    now_ts = int(time.time())
    last_sync_ts = now_ts
    time_sync_source = "api"
    needs_time_sync = False

    print(
        f"✅ Time set to: {hour:02d}:{minute:02d}:{second:02d} (time sync source: API)"
    )
    return jsonify({"status": "ok", "time": f"{hour:02d}:{minute:02d}:{second:02d}"})


# === Channel Configuration API ===


@app.route("/api/config/channels")
def get_channel_config():
    """Get channel names and colors"""
    config_file = os.path.join(SD_CONFIG_DIR, "channels.cfg")

    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return jsonify(data)
        except Exception as e:  # noqa: BLE001 — fall back to defaults below
            print(f"⚠ Could not load channel config: {e}")

    # Return defaults (same list the firmware sends)
    return jsonify(
        {
            "channels": [
                {"name": "Blau", "color": "#2196F3"},
                {"name": "Weiß", "color": "#E0E0E0"},
                {"name": "Rot", "color": "#F44336"},
                {"name": "Grün", "color": "#4CAF50"},
                {"name": "UV", "color": "#9C27B0"},
                {"name": "Mondlicht", "color": "#FFD700"},
            ]
        }
    )


@app.route("/api/config/channels", methods=["POST"])
def save_channel_config():
    """Save channel names and colors"""
    try:
        data = request.get_json(silent=True)

        if not data or "channels" not in data:
            return jsonify({"error": "Invalid JSON: missing 'channels' field"}), 400

        ensure_sd_dir()
        config_file = os.path.join(SD_CONFIG_DIR, "channels.cfg")

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"✓ Channel config saved to {config_file}")
        return jsonify({"status": "ok"})

    except Exception as e:  # noqa: BLE001 — reported to the UI as 500 below
        print(f"✗ Failed to save channel config: {e}")
        return jsonify({"error": str(e)}), 500


# === File Upload API ===


@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file uploads to SD card (simulates ESP8266 /upload endpoint)

    Note: This mock implementation creates directories automatically, but the
    real ESP8266 firmware does NOT create directories. Users must manually
    create directory structure on SD card before uploading files to subdirectories.
    """
    try:
        # Check if file is in request
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400

        file = request.files["file"]
        target_path = request.form.get("path", "")

        if not target_path:
            return jsonify({"success": False, "error": "No path specified"}), 400

        # Remove leading slash if present
        target_path = target_path.removeprefix("/")

        # Build full path to extras/SDCard
        sd_card_base = os.path.join(os.path.dirname(__file__), "..", "extras", "SDCard")
        full_path = os.path.join(sd_card_base, target_path)

        # Create directories if needed (NOTE: Real firmware does NOT do this!)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Save file
        file.save(full_path)
        file_size = os.path.getsize(full_path)

        print(f"✓ Upload complete: {target_path} ({file_size} bytes)")

        return jsonify({"success": True, "path": target_path, "size": file_size})

    except Exception as e:  # noqa: BLE001 — reported to the UI as 500 below
        print(f"✗ Upload failed: {e!s}")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("MOCK_PORT", "5000"))
    sd_log(f"boot (mock build, {len(macros)} macros)")
    print("=" * 60)
    print("  SBAquaControl Mock API Server")
    print("=" * 60)
    print(f"  URL: http://localhost:{port}")
    print(
        f"  Firmware parity: {CHANNELS} channels, {MAX_TARGETS} targets/channel, "
        f"{TEST_MODE_TIMEOUT_S}s test-mode timeout"
    )
    print(
        f"  Runtime state: {os.path.relpath(SCHEDULE_FILE, os.path.dirname(__file__))} "
        f"(delete it to reset to the tracked seed)"
    )
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print()

    # Check if SDCard directory exists
    if not os.path.exists("extras/SDCard"):
        print("⚠ Warning: extras/SDCard directory not found")
        print("  Create HTML files there to test the UI")

    app.run(debug=os.environ.get("MOCK_DEBUG", "1") != "0", port=port, host="0.0.0.0")
