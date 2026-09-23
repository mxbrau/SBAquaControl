# SBAquaControl test harness

Two halves: **automated, offline checks** (here) and the **manual hardware
checklist** in [`docs/status/TESTING_GUIDE.md`](../docs/status/TESTING_GUIDE.md).

## Run everything automated

```bash
uv run pytest test/                  # everything
uv run pytest test/ -m "not build"   # everything except the slow firmware build
uv run pytest test/ -m build         # only the firmware build + budget check
uv run pytest test/test_parity.py    # only the fast static checks (no toolchain)
```

| What runs | What it proves | Needs |
|---|---|---|
| Route parity (always) | Every route in `src/AquaControl.cpp` also exists in the mock (one test per route) | — |
| Mock contract tests (always) | A freshly started mock answers all endpoints with the firmware's status codes and field names | — |
| Host unit tests (always) | The firmware scheduling maths (interpolation, slew limiter, time parsing) passes on the PC | PlatformIO (`env:test`, native) |
| `build` marker | Firmware compiles for `env:esp8266` and stays inside the RAM/Flash budget | PlatformIO |

`build` is the only marker (registered in `pyproject.toml` under
`[tool.pytest.ini_options]`): it selects the slow firmware compile, so the
normal loop is `pytest -m "not build"`. Everything else always runs — the
static checks parse files in milliseconds, the mock starts in a fraction of
a second, and only the host unit layer needs PlatformIO beyond that.

The mock server starts on a private localhost port, so it never collides with a
dev server you have running and never touches the real device; it is stopped
again afterwards (`mock_server` fixture in `conftest.py`). Every file it touches
is snapshotted and restored (`clean_tree` fixture) — the working tree is
unchanged after a run, so the result is always `git status`-verifiable.

What is **not** automated (real hardware required): LED output and PWM/PCA9685
behaviour, DS18B20 readings, OTA updates, WiFi reachability, 24-hour soak.

## Pieces

| File | Purpose |
|---|---|
| `mock_server.py` | Flask stand-in for the ESP8266 webserver. Its contract mirrors `src/Webserver.cpp` one-to-one — treat a divergence as a bug in one of the two. |
| `test_api_parity.py` | Route/contract library (imported by the tests). Static: parses `_Server.on(...)` vs `@app.route(...)`. Standalone: `--live` smoke-tests a running mock. |
| `conftest.py` | `mock_server` fixture (private-port mock per session), `clean_tree` fixture (snapshot/restore), `pio_command()` helper. |
| `test_parity.py` | Always run: one test per firmware route — fails if the mock lacks it. |
| `test_live_contract.py` | Always run: one test per `live_checks()` row plus the multipart `/upload` check. |
| `test_firmware_build.py` | `build`: `pio run -e esp8266 -t size` plus the RAM/Flash budget asserts. |
| `test_host_unit.py` | Always run: executes `pio test -e test`, asserts every case passed. |
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
The parametrized contract tests and the standalone script pick it up automatically.

If the firmware gains an endpoint, add it to the mock **and** to `live_checks()` —
the parity tests will fail until you do.

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
