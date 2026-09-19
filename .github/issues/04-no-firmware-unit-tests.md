---
title: No automated tests for firmware logic - env:test does not even compile
labels: testing, tooling
---

## Symptom

`platformio.ini` advertises a PC-side test environment, but it cannot build:

```
$ uv run pio run -e test
src/main.cpp:20:10: fatal error: Arduino.h: No such file or directory
*** [/opt/.../build/test/src/AquaControl.o] Error 1
*** [/opt/.../build/test/src/Webserver.o] Error 1
========================== [FAILED] Took 2.55 seconds ==========================
```

`env:test` (`platform=native`, `test_framework=unity`) pulls in no Arduino
framework, yet `src/main.cpp`, `src/AquaControl.cpp` and `src/Webserver.cpp` all
include `<Arduino.h>`. There are also **no C++ test files anywhere** in the
repo, so even a working environment would run zero tests.

## Impact

The arithmetic that decides LED brightness - linear interpolation between
targets, the slew-rate limiter, `parseTimeToSeconds()`, midnight rollover - is
exactly the kind of pure logic that unit tests cover cheaply, and it is the code
the reported LED-blink and macro-latency bugs live in (#1, #3). Today the only
way to catch a regression there is to flash hardware and watch.

## Evidence

```bash
uv run pio run -e test        # FAILED, as above
grep -rl "TEST_ASSERT\|TEST_CASE" src test examples   # no matches
```

The offline suite that *does* work today covers the HTTP contract and the build:
`uv run python test/run_checks.py` (build + route parity + endpoint checks). It
does not execute a single line of firmware logic.

## Proposed approach (pick one)

1. **Host-compiled unit tests with a minimal Arduino stub.** Add a small
   `test/stubs/Arduino.h` (millis(), pinMode(), etc. - only what the tested
   translation units touch) and let `env:test` compile *only* the pure-logic
   files (e.g. via `build_src_filter`), so `PwmChannel::proceedCycle()` and
   `parseTimeToSeconds()` can be tested on the PC.
2. **Extract the pure logic** into a header with no Arduino dependencies and
   test that; the firmware keeps including `<Arduino.h>` around it.

Either way, the first tests should be the interpolation maths, the slew-rate
limiter at the dim-to-off boundary (the suspected cause of #1) and time-string
parsing.

## Acceptance criteria

- [ ] `uv run pio run -e test` / `pio test -e test` succeeds on a machine with no hardware
- [ ] At least the interpolation + dim-to-off boundary cases are covered
- [ ] The command is added to `test/run_checks.py` as a fourth layer
- [ ] `test/README.md` documents how to add a firmware test

## Notes

Do not "fix" this by deleting `env:test` - the gap is real, it just needs the
stub or an extraction first.
