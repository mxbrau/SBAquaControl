# SBAquaControl test harness

Two halves: **automated, offline checks** (here) and the **manual hardware
checklist** in [`docs/status/TESTING_GUIDE.md`](../docs/status/TESTING_GUIDE.md).

## Run everything automated

```bash
uv run python test/run_checks.py               # build + parity + live contract checks + host unit tests
uv run python test/run_checks.py --skip-build  # fast loop while working on the UI
uv run python test/run_checks.py --only live
uv run python test/run_checks.py --only unit
```

| Layer | What it proves | Needs |
|---|---|---|
| `BUILD` | Firmware compiles for `env:esp8266` and stays inside the RAM/Flash budget | PlatformIO |
| `PARITY` | Every route in `src/AquaControl.cpp` also exists in the mock | — |
| `LIVE` | A freshly started mock answers all endpoints with the firmware's status codes and field names | — |
| `UNIT` | The firmware scheduling maths (interpolation, slew limiter, time parsing) passes on the PC | PlatformIO (`env:test`, native) |

`LIVE` starts its own mock server on a private port, so it never collides with a
dev server you have running, and it stops it again. Every file it touches is
snapshotted and restored — the working tree is unchanged after a run, so the
result is always `git status`-verifiable.

What is **not** automated (real hardware required): LED output and PWM/PCA9685
behaviour, DS18B20 readings, OTA updates, WiFi reachability, 24-hour soak.

## Pieces

| File | Purpose |
|---|---|
| `mock_server.py` | Flask stand-in for the ESP8266 webserver. Its contract mirrors `src/Webserver.cpp` one-to-one — treat a divergence as a bug in one of the two. |
| `test_api_parity.py` | Route/contract guard. Static: parses `_Server.on(...)` vs `@app.route(...)`. `--live`: exercises a running mock. |
| `run_checks.py` | Runs all three layers and prints a summary. |
| `gen_schedule_fixture.py` | Regenerates `data/schedules.json`, the realistic seed data. |
| `data/schedules.json` | Tracked, read-only seed: 6 channels, realistic photoperiod curves, max 32 targets (the device limit), plus edge cases (plateau, 32-point cap, midnight wrap). |
| `data/schedules.runtime.json` | Git-ignored runtime state the mock saves to. Delete it to reset to the seed. |

## Developing the UI

```bash
uv run python test/mock_server.py      # http://localhost:5000
```

Edit files in `extras/SDCard/` and reload. Changes you make in the UI persist to
`schedules.runtime.json`, never to the tracked seed.

## Adding a check

Add a row to `live_checks()` in `test_api_parity.py`:
`(label, method, path, body, expected_status, required_fields)`.
The runner and the standalone script pick it up automatically.

If the firmware gains an endpoint, add it to the mock **and** to `live_checks()` —
`BUILD`-time parity will fail until you do.

## Adding a firmware test

`src/` cannot compile on the PC (it needs `<Arduino.h>` and the ESP8266/SD
stack), so `env:test` excludes it (`build_src_filter = -<*>` in
`platformio.ini`) and tests the dependency-free mirror instead:

- `test/support/aqua_logic.h` — the pure logic, function-for-function against
  `src/AquaControl.cpp` (`PwmChannel::proceedCycle`: interpolation, slew-rate
  limiter, `PWM_MIN` clamp) and `src/Webserver.cpp` (`parseTimeToSeconds`).
  Each function cites the firmware lines it mirrors.
- `test/test_pwm_logic.cpp` — the Unity tests. Add a `void test_<what>(void)`
  plus a `RUN_TEST(test_<what>);` line in `main()`.

```bash
pio test -e test     # run the host unit tests (no hardware needed)
```

If the firmware maths changes, update the mirror **and** the expectations
together — a test that no longer matches `src/` is a bug in the test.

## Known deviations of the mock

Listed in the module docstring of `mock_server.py` (macros in memory, synthetic
heap figures, `reboot` resets state instead of restarting, `clear` deletes the
SD configs just like the device does).
