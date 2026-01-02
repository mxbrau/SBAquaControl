"""
Mock API Server for SBAquaControl UI Development
Simulates ESP8266 API endpoints for browser-based testing

Usage:
    pip install flask flask-cors
    python test/mock_server.py

Then open: http://localhost:5000
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)


# Simple persistence for mock data and SD-card style files
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SCHEDULE_FILE = os.path.join(DATA_DIR, "schedules.json")
SD_CONFIG_DIR = os.path.join(
    os.path.dirname(__file__), "..", "extras", "SDCard", "config"
)
MAX_TARGETS = 128  # mirror ESP8266 limit


def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def load_schedules_from_disk():
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"ℹ Loaded schedules from {SCHEDULE_FILE}")
                return {int(k): v for k, v in data.items()}
        except Exception as e:
            print(f"⚠ Could not load schedules: {e}")
    return None


def save_schedules_to_disk():
    try:
        ensure_data_dir()
        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump(schedules, f, indent=2)
        print(f"✓ Persisted schedules to {SCHEDULE_FILE}")
    except Exception as e:
        print(f"⚠ Could not save schedules: {e}")


def ensure_sd_dir():
    if not os.path.exists(SD_CONFIG_DIR):
        os.makedirs(SD_CONFIG_DIR)


def write_channel_cfg(channel: int, targets):
    """Persist targets in the same format the firmware uses: config/ledch_XX.cfg"""
    try:
        ensure_sd_dir()
        fname = os.path.join(SD_CONFIG_DIR, f"ledch_{channel:02d}.cfg")
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
    except Exception as e:
        print(f"⚠ Could not write SD config for channel {channel}: {e}")


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

macros = {
    "movie": {
        "name": "Movie Mode",
        "duration": 7200,  # 2 hours
        "description": "Dims all lights for movie watching",
        "channels": [
            {
                "channel": 0,
                "targets": [{"time": 0, "value": 0}, {"time": 7200, "value": 0}],
            },
            {
                "channel": 1,
                "targets": [{"time": 0, "value": 0}, {"time": 7200, "value": 0}],
            },
            {
                "channel": 2,
                "targets": [{"time": 0, "value": 0}, {"time": 7200, "value": 0}],
            },
            {
                "channel": 3,
                "targets": [{"time": 0, "value": 0}, {"time": 7200, "value": 0}],
            },
            {
                "channel": 4,
                "targets": [{"time": 0, "value": 0}, {"time": 7200, "value": 0}],
            },
            {
                "channel": 5,
                "targets": [{"time": 0, "value": 5}, {"time": 7200, "value": 5}],
            },  # Dim moonlight
        ],
    },
    "maintenance": {
        "name": "Maintenance",
        "duration": 3600,  # 1 hour
        "description": "All channels at 100% for tank maintenance",
        "channels": [
            {
                "channel": i,
                "targets": [{"time": 0, "value": 100}, {"time": 3600, "value": 100}],
            }
            for i in range(6)
        ],
    },
}

# Test mode state
test_mode_active = False
test_values = [0, 0, 0, 0, 0, 0]
active_macro = None
macro_activation_time = None


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
    except:
        return jsonify({"error": "File not found"}), 404


# === Schedule API ===


@app.route("/api/schedule/get")
def get_schedule():
    """Get schedule for a specific channel"""
    channel = int(request.args.get("channel", 0))
    if channel < 0 or channel >= 6:
        return jsonify({"error": "Invalid channel (must be 0-5)"}), 400

    return jsonify({"channel": channel, "targets": schedules.get(channel, [])})


@app.route("/api/schedule/all")
def get_all_schedules():
    """Get schedules for all 6 channels at once"""
    return jsonify(
        {
            "schedules": [
                {"channel": i, "targets": schedules.get(i, [])} for i in range(6)
            ]
        }
    )


@app.route("/api/schedule/save", methods=["POST"])
def save_schedule():
    """Save schedule for a specific channel"""
    data = request.json
    channel = data.get("channel")
    targets = data.get("targets", [])

    if channel is None or channel < 0 or channel >= 6:
        return jsonify({"error": "Invalid channel"}), 400

    # Cap to MAX_TARGETS and coerce types, preserve isControl flag if provided
    cleaned = []
    for t in targets:
        seconds = int(t.get("time", 0))
        value = int(t.get("value", 0))
        is_control = bool(t.get("isControl", False))
        cleaned.append(
            {
                "time": max(0, min(86400, seconds)),
                "value": max(0, min(100, value)),
                "isControl": is_control,
            }
        )
    cleaned.sort(key=lambda t: t["time"])
    cleaned = cleaned[:MAX_TARGETS]

    schedules[channel] = cleaned
    save_schedules_to_disk()
    write_channel_cfg(channel, cleaned)
    print(f"✓ Saved schedule for channel {channel}: {len(cleaned)} targets")
    return jsonify({"status": "ok", "channel": channel, "target_count": len(targets)})


@app.route("/api/schedule/target/add", methods=["POST"])
def add_target():
    """Add a single target point to a channel"""
    try:
        data = request.json
        print(f"DEBUG add_target: received data = {data}")
        channel = data.get("channel")
        time = data.get("time")
        value = data.get("value")
        print(f"DEBUG add_target: channel={channel}, time={time}, value={value}")

        if channel is None or time is None or value is None:
            return jsonify({"error": "Missing required fields"}), 400

        # Convert time string (HH:MM) to seconds if needed
        if isinstance(time, str):
            parts = time.split(":")
            time = int(parts[0]) * 3600 + int(parts[1]) * 60
        else:
            time = int(time)

        value = int(value)

        # Add or update target at this time
        current_targets = schedules.get(channel, [])

        # Remove existing target at same time
        current_targets = [t for t in current_targets if t["time"] != time]

        # Add new target (control point) and sort by time
        current_targets.append({"time": time, "value": value, "isControl": True})
        current_targets.sort(key=lambda t: t["time"])

        # Sanitize, cap, and persist
        current_targets = [
            {
                "time": max(0, min(86400, int(t["time"]))),
                "value": max(0, min(100, int(t["value"]))),
                "isControl": bool(t.get("isControl", False)),
            }
            for t in current_targets
        ]
        current_targets = current_targets[:MAX_TARGETS]
        schedules[channel] = current_targets
        save_schedules_to_disk()
        write_channel_cfg(channel, current_targets)

        print(f"✓ Added target to channel {channel}: time={time}s, value={value}%")

        return jsonify(
            {
                "success": True,
                "channel": channel,
                "time": time,
                "value": value,
                "targets": current_targets,
            }
        )
    except Exception as e:
        print(f"✗ Error in add_target: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/schedule/target/delete", methods=["POST"])
def delete_target():
    """Delete a target point from a channel"""
    data = request.json
    channel = data.get("channel")
    time = data.get("time")

    if channel is None or time is None:
        return jsonify({"error": "Missing required fields"}), 400

    # Convert time string (HH:MM) to seconds if needed
    if isinstance(time, str):
        parts = time.split(":")
        time = int(parts[0]) * 3600 + int(parts[1]) * 60
    else:
        time = int(time)

    current_targets = schedules.get(channel, [])
    current_targets = [t for t in current_targets if t["time"] != time]
    # Persist with sanitization and cap
    current_targets = [
        {
            "time": max(0, min(86400, int(t["time"]))),
            "value": max(0, min(100, int(t["value"]))),
        }
        for t in current_targets
    ]
    current_targets = current_targets[:MAX_TARGETS]
    schedules[channel] = current_targets
    save_schedules_to_disk()
    write_channel_cfg(channel, current_targets)

    print(f"✓ Deleted target from channel {channel}: time={time}s")
    return jsonify({"status": "ok", "targets": current_targets})


# === Test Mode API ===


@app.route("/api/test/start", methods=["POST"])
def test_start():
    """Activate test mode"""
    global test_mode_active
    test_mode_active = True
    print("▶ Test mode ACTIVATED")
    return jsonify({"status": "ok", "test_mode": True})


@app.route("/api/test/update", methods=["POST"])
def test_update():
    """Update test mode values in real-time"""
    global test_values
    data = request.json
    values = data.get("values", [])

    if len(values) != 6:
        return jsonify({"error": "Must provide exactly 6 channel values"}), 400

    test_values = values
    print(f"↻ Test values: {values}")
    return jsonify({"status": "ok", "values": test_values})


@app.route("/api/test/exit", methods=["POST"])
def test_exit():
    """Exit test mode and return to schedule"""
    global test_mode_active
    test_mode_active = False
    print("■ Test mode DEACTIVATED")
    return jsonify({"status": "ok", "test_mode": False})


# === Macro API ===


@app.route("/api/macro/list")
def macro_list():
    """List all available macros"""
    macro_list = [
        {
            "id": key,
            "name": value["name"],
            "duration": value["duration"],
            "description": value.get("description", ""),
        }
        for key, value in macros.items()
    ]
    return jsonify({"macros": macro_list})


@app.route("/api/macro/get")
def macro_get():
    """Get detailed macro configuration"""
    macro_id = request.args.get("id")
    if macro_id not in macros:
        return jsonify({"error": "Macro not found"}), 404

    return jsonify(macros[macro_id])


@app.route("/api/macro/save", methods=["POST"])
def macro_save():
    """Save a new or updated macro"""
    data = request.json
    macro_id = data.get("id", "").lower().replace(" ", "_")

    if not macro_id:
        return jsonify({"error": "Macro ID required"}), 400

    macros[macro_id] = {
        "name": data.get("name", "Untitled"),
        "duration": data.get("duration", 3600),
        "description": data.get("description", ""),
        "channels": data.get("channels", []),
    }

    print(f"✓ Saved macro '{macro_id}': {macros[macro_id]['name']}")
    return jsonify({"status": "ok", "id": macro_id})


@app.route("/api/macro/activate", methods=["POST"])
def macro_activate():
    """Activate a macro (temporarily override schedule)"""
    global active_macro, macro_activation_time

    data = request.json
    macro_id = data.get("id") or data.get("name")

    # Try to find by ID first, then by display name
    if macro_id not in macros:
        # Try to match by display name
        macro_id = next((k for k, v in macros.items() if v["name"] == macro_id), None)

    if not macro_id or macro_id not in macros:
        return jsonify({"error": "Macro not found"}), 404

    active_macro = macro_id
    macro_activation_time = datetime.now()

    print(f"▶ Activated macro '{macros[macro_id]['name']}'")
    print(f"  Duration: {macros[macro_id]['duration']}s")

    return jsonify(
        {
            "status": "ok",
            "macro": macros[macro_id]["name"],
            "activation_time": macro_activation_time.isoformat(),
            "end_time": (
                macro_activation_time + timedelta(seconds=macros[macro_id]["duration"])
            ).isoformat(),
        }
    )


@app.route("/api/macro/delete", methods=["POST"])
def macro_delete():
    """Delete a macro"""
    data = request.json
    macro_id = data.get("id") or data.get("name")

    # Try to find by ID first, then by display name
    if macro_id not in macros:
        macro_id = next((k for k, v in macros.items() if v["name"] == macro_id), None)

    if macro_id and macro_id in macros:
        del macros[macro_id]
        print(f"✗ Deleted macro '{macro_id}'")
        return jsonify({"status": "ok"})

    return jsonify({"error": "Macro not found"}), 404


@app.route("/api/macro/stop", methods=["POST"])
def macro_stop():
    """Stop active macro and return to schedule"""
    global active_macro, macro_activation_time

    if active_macro:
        print(f"■ Stopped macro '{macros[active_macro]['name']}'")
        active_macro = None
        macro_activation_time = None

    return jsonify({"status": "ok"})


# === Status API ===


@app.route("/api/status")
def status():
    """Get current system status"""
    global active_macro, macro_activation_time
    now = datetime.now()

    status_data = {
        "test_mode": test_mode_active,
        "test_values": test_values if test_mode_active else None,
        "current_time": now.strftime("%H:%M:%S"),
        "current_seconds": (now.hour * 3600) + (now.minute * 60) + now.second,
        "temperature": 24.5,  # Mock temperature
        "wifi_connected": True,
        "sd_card_ok": True,
        "uptime": 12345,  # Mock uptime in seconds
    }

    if active_macro:
        elapsed = (now - macro_activation_time).total_seconds()
        duration = macros[active_macro]["duration"]
        remaining = max(0, duration - elapsed)

        status_data["macro_active"] = True
        status_data["macro_name"] = macros[active_macro]["name"]
        status_data["macro_elapsed"] = int(elapsed)
        status_data["macro_remaining"] = int(remaining)
        status_data["macro_duration"] = duration

        # Auto-stop if expired (simulates ESP8266 timeout)
        if remaining <= 0:
            active_macro = None
            macro_activation_time = None
            status_data["macro_active"] = False
    else:
        status_data["macro_active"] = False

    return jsonify(status_data)


# === File Upload API ===


@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file uploads to SD card (simulates ESP8266 /upload endpoint)"""
    try:
        # Check if file is in request
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400

        file = request.files["file"]
        target_path = request.form.get("path", "")

        if not target_path:
            return jsonify({"success": False, "error": "No path specified"}), 400

        # Remove leading slash if present
        if target_path.startswith("/"):
            target_path = target_path[1:]

        # Build full path to extras/SDCard
        sd_card_base = os.path.join(
            os.path.dirname(__file__), "..", "extras", "SDCard"
        )
        full_path = os.path.join(sd_card_base, target_path)

        # Create directories if needed
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Save file
        file.save(full_path)
        file_size = os.path.getsize(full_path)

        print(f"✓ Upload complete: {target_path} ({file_size} bytes)")

        return jsonify({"success": True, "path": target_path, "size": file_size})

    except Exception as e:
        print(f"✗ Upload failed: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 60)
    print("  SBAquaControl Mock API Server")
    print("=" * 60)
    print(f"  URL: http://localhost:5000")
    print(f"  Press Ctrl+C to stop")
    print("=" * 60)
    print()

    # Check if SDCard directory exists
    if not os.path.exists("extras/SDCard"):
        print("⚠ Warning: extras/SDCard directory not found")
        print("  Create HTML files there to test the UI")

    app.run(debug=True, port=5000, host="0.0.0.0")
