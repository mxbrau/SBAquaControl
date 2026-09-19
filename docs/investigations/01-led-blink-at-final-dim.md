# Bug investigation 01 — LEDs blink (~1 Hz) instead of fading smoothly off

**Status:** root cause identified in firmware, mechanism verified by simulation of the exact
arithmetic. Fix proposed, **not yet compiled or flashed** (no PlatformIO toolchain on the
investigating machine — see "Verification status").
**Issue:** [#7](https://github.com/mxbrau/SBAquaControl/issues/7) (analysis only - fix pending)
**Affected:** `src/AquaControl.cpp` — `AquaControl::proceedCycle()` (L869-923) and
`PwmChannel::proceedCycle()` (L1103-1242), `src/AquaControl.h` (L199-227, L91)

---

## 1. Reported symptom

> When the aquarium gets dimmed down — in the evening, or when a movie-mode macro is
> activated — during the very last part of the dim (roughly the last few percent) the LEDs
> start to **blink with a frequency of about 1 s** instead of smoothly dimming off.

Reproducible in two independent situations (scheduled evening fade, macro fade), which is a
strong hint that the mechanism is in the *common* fade code, not in the macro or the schedule
logic.

## 2. Where the dimming is produced

Two mechanisms cooperate:

| Step | Code | Purpose |
|---|---|---|
| 1 | `PwmChannel::proceedCycle()` L1116-1179 | Linear interpolation between the two schedule targets that bracket the current time of day → `vx` (0..100 %) |
| 2 | `PwmChannel::proceedCycle()` L1192 | `_PwmTarget = (uint16_t)(PWM_MAX * vx / 100.0)` → 0..4095 counts |
| 3 | `PwmChannel::proceedCycle()` L1197-1234 | Slew-rate limiter: walk `_PwmValue` toward `_PwmTarget` in `PWM_STEP` (=5) increments, at most once per *loop iteration* |
| 4 | `AquaControl::proceedCycle()` L898-905 | Write `CurrentWriteValue` to the PCA9685 whenever `HasToWritePwm` is set |

The PCA9685 holds its output autonomously — **the LEDs can only change brightness when the
firmware writes a new value.** So a *blink* is always the result of `CurrentWriteValue`
alternating between 0 and a non-zero value.

## 3. Root cause

### 3.1 The fade time base is built from two unsynchronised clocks

`AquaControl::proceedCycle()` L872-873:

```cpp
CurrentSecOfDay = elapsedSecsToday(now());   // from TimeLib (RTC-anchored seconds)
CurrentMilli    = millis() % 1000;           // from the Arduino runtime's millisecond counter
```

`PwmChannel::proceedCycle()` L1164 combines them into one "milliseconds since midnight"-like
value:

```cpp
float deltaNow = ((float)(CurrentSecOfDay - lastTarget.Time) * 1000.0) + (float)CurrentMilli;
```

**These two clocks are not phase-locked**, and they cannot be:

* `now()` (TimeLib `Time.cpp`) is a staircase: `sysTime` is incremented in steps of 1000 ms
  relative to a *private* anchor `prevMillis`:
  `while (millis() - prevMillis >= 1000) { sysTime++; prevMillis += 1000; }`
  That anchor is only touched by `setTime()`, which does `prevMillis = millis();`
  This firmware calls `setSyncProvider(getRTCTime)` (L624) and `setTime()` (L590, L1911), so
  the anchor is reset at boot, on every 300 s re-sync (`syncInterval` default) and on every
  manual `/api/time/set`.
* `CurrentMilli = millis() % 1000` always wraps at `millis() % 1000 == 0`.

So the `now()` second edge sits at some phase `p = prevMillis % 1000` which is essentially
arbitrary and changes on every re-sync, while the millisecond term always wraps at 0. The
consequence, once per second:

* at `millis() % 1000 == p`  → `CurrentSecOfDay` jumps `+1`, `deltaNow` **jumps by +1000 ms**
* at `millis() % 1000 == 0`  → `CurrentMilli` drops 999→0, `deltaNow` **drops by 999 ms**

`deltaNow` therefore has a **~1 Hz sawtooth of ±1000 ms** riding on top of the intended
monotonic ramp. The interpolated value inherits it:

```
Δvx   = |m| · 1000 ms
ΔPWM  = PWM_MAX · Δvx / 100        counts
m     = dv / dt / 1000             %/ms
```

For a full-scale fade (dv = 100 %) the jitter amplitude is:

| fade duration | m (%/ms) | Δvx (%) | ΔPWM (counts, PCA9685 12-bit) |
|---|---|---|---|
| 2 min | 8.33e-4 | 0.83 | 34 |
| 5 min | 3.33e-4 | 0.33 | 14 |
| 30 min | 5.56e-5 | 0.056 | 2.3 |
| 120 min | 1.39e-5 | 0.014 | 0.6 |

Mid-fade this is invisible (±14 of 4095 ≈ 0.3 %). **At the bottom of the fade it is fatal:**
once the smooth value falls below the jitter amplitude, `_PwmTarget` alternates between `0`
and a small positive number, and because the slew limiter re-writes on *every* difference
(L1197 `if (_PwmTarget != _PwmValue)`), `CurrentWriteValue` alternates between **0 (LED off)**
and **~10 counts (faintly on)** — at exactly the sawtooth frequency, i.e. ~1 Hz.

That is the reported blink: not a failure to reach zero, but a *toggling* between zero and
"just barely on" for the last sliver of the fade, instead of a monotone fade-out.

### 3.2 Simulated proof

The exact algorithm (TimeLib `now()` staircase + `setTime()` re-anchoring, `millis() % 1000`,
the interpolation, the `unsigned long dt` cast, the slew limiter) was ported 1:1 and driven
with the repository's real channel config `extras/SDCard/config/ledch_05.cfg` (which fades
`21:30;100` → `22:00;0`), loop period 4 ms, `prevMillis` phase p = 250.

A 5-minute full-scale fade is the clearest demonstration (this is the "movie mode"-like case).
Last 24 values actually written to the PCA9685:

```
current code:    25 24 23 18 13 10 9 8 7 6 5 4 3 2 1 0 | 5 10 13 12 11 10 5 0
                                                        ^
                                    reached full off, then climbed back to 13 counts
fixed time base: 23 22 21 20 19 18 17 16 15 14 13 12 11 10 9 ... 4 3 2 1 0
```

Instead of one monotone fade-out, the last sliver goes **off → dim → off → dim** at the
~1 Hz sawtooth frequency. The re-light reaches ~13 of 4095 counts (0.3 % of full scale), which
on a bright LED string is plainly visible in a dark room — it reads as a blink, not as a fade.

Direction reversals counted over the whole fade:

| fade duration | reversals (current code) | reversals (monotonic time base) | jitter amplitude (counts) |
|---|---|---|---|
| 2 min | 241 | 1 | 34 |
| 5 min | 601 | 1 | 14 |
| 30 min | 3601 | 1 | 2.3 |
| 120 min | 8191 | 1 | 0.6 |

The reversal *count* is not the severity metric (a smaller amplitude produces more ±1-count
micro-reversals); the *amplitude* is: only when the smooth value falls below the amplitude does
the output start crossing the on/off boundary, and that is why the symptom appears at the very
end of the fade and nowhere else.

### 3.3 Contributing factor — the "minimum light value" guard is dead code

L1102 and L1229-1233:

```cpp
#define PWM_MIN 1
...
CurrentWriteValue = _PwmValue;
// Thins defines a minimum light value
if (CurrentWriteValue > 0 && CurrentWriteValue < PWM_MIN)
{
    CurrentWriteValue = PWM_MIN;
}
```

`CurrentWriteValue` is `uint16_t` (AquaControl.h L209) and `PWM_MIN` is `1`, so
`x > 0 && x < 1` is **unsatisfiable**. The clamp never fires. Whatever hysteresis the author
originally intended to keep the LED from chattering around off is not in effect. (The
original upstream code carried the same defect — `git blame` shows these lines are Marcel
Schulz 2017 apart from re-indentation in `b0c15431`.)

### 3.4 Contributing factor — the slew limiter is per-iteration, not per-time

`_PwmValue += PWM_STEP` happens once per `proceedCycle()` call. `proceedCycle()` is called as
fast as `loop()` spins (thousands of times/s when idle, ~100-500 times/s while the PCA9685 is
being written and the web server is serviced). The effective fade *rate* therefore depends on
CPU load / I2C traffic / HTTP load rather than on time, and it also means every 1-count
difference in `_PwmTarget` produces an I2C transaction (L1017-1024). During a fade, 6
channels × ~200 writes/s ≈ 1200 I2C writes/s at the default 100 kHz `Wire` clock — a large
fraction of the bus, and the DS3231 RTC shares that bus.

## 4. Secondary defect found in the same code (fix together, it affects the same evening dim)

`PwmChannel::proceedCycle()` L1148-1156 — after the last target of the day:

```cpp
currentTarget = Targets[0];
lastTarget    = Targets[TargetCount - 1];
currentTarget.Time = currentTarget.Time + (60 * 60 * 24) - lastTarget.Time;   // becomes a DURATION
...
unsigned long dt = currentTarget.Time - lastTarget.Time;                     // mixes duration - absolute
```

`currentTarget.Time` is overwritten with a *duration* while `lastTarget.Time` stays an
*absolute* time of day, so

```
dt = (Targets[0].Time + 86400 - lastTarget.Time) - lastTarget.Time
```

* If the last target is late in the day (`lastTarget.Time > (Targets[0].Time + 86400)/2`, e.g.
  last target 22:00, first target 08:00) `dt` goes **negative** and, being converted to
  `unsigned long`, becomes ≈4.29e9. `m` collapses to ≈0 and the channel **freezes at
  `lastTarget.Value` for the rest of the night** instead of ramping toward the morning value;
  then at 00:00 the `t == 0` branch starts the correct ramp, producing a **step** at midnight
  (e.g. 5 % → 20 % in one tick).
* If it comes out positive it does so by accident and with a wrong slope.

The repository's sample channel `ledch_05.cfg` ends with `23:59;0`, which accidentally hides
this (dt = 60 s, all values 0). Channels without a late end-of-day target are affected.

## 5. Proposed fix

Three independent changes; (1) removes the cause, (2) and (3) make the output robust even if a
time glitch happens again.

### (1) Single monotonic time base (removes the 1 Hz sawtooth)

Derive the sub-second part from the *same* clock as the second, re-anchoring only when the
second actually changes, so `secOfDay*1000 + milliOfSec` becomes monotonic:

```cpp
// AquaControl.h, new private members
time_t   _lastSod      = -1;
uint32_t _sodEdgeMilli = 0;

// AquaControl.cpp, proceedCycle() replaces L872-873
time_t   t   = now();
uint32_t ms  = millis();
time_t   sod = elapsedSecsToday(t);
if (sod != _lastSod) {          // second changed -> re-anchor the millisecond phase here
    _lastSod      = sod;
    _sodEdgeMilli = ms;
}
CurrentSecOfDay = sod;
CurrentMilli    = (ms - _sodEdgeMilli > 999) ? 999 : (ms - _sodEdgeMilli);
```

Now the second edge and the millisecond zero are captured at the same instant, so `deltaNow`
has no sawtooth. (A genuine `setTime()`/RTC correction still produces a ≤1 s step every
300 s — 300× less often and invisible compared to the LED's resolution.)

### (2) Snap to off / write hysteresis (kills the on-off chatter)

```cpp
// AquaControl_config.h
#define PWM_OFF_SNAP_COUNTS 8   // <= 8/4095 = 0.2 %: treat as "off"

// PwmChannel::proceedCycle(), replacing L1195-1234 fading block
if (_PwmTarget <= PWM_OFF_SNAP_COUNTS) { _PwmTarget = 0; }   // do not hover at "just on"
if (_PwmTarget != _PwmValue)
{
    ...
    CurrentWriteValue = _PwmValue;
    // real minimum level (fixes the unsatisfiable guard); PWM_MIN must be > PWM_OFF_SNAP_COUNTS
    if (CurrentWriteValue != 0 && CurrentWriteValue < PWM_MIN) CurrentWriteValue = PWM_MIN;
}
```
`PWM_MIN` must be redefined to a meaningful level (e.g. `8`) *and* the unsatisfiable
`> 0 &&` half of the condition dropped — otherwise it stays dead code. Choosing
`PWM_OFF_SNAP_COUNTS` is a hardware decision: it is the smallest duty cycle at which the
Meanwell LDD still visibly lights the LEDs.

Optionally also add a write dead-band so the PCA9685 is not re-written for every single count
(compare against the value that was actually written, `CurrentWriteValue`, not against
`_PwmValue`, otherwise the guard is trivially true inside this branch):

```cpp
if (abs((int)_PwmTarget - (int)CurrentWriteValue) >= PWM_WRITE_DEADBAND) { /* write */ }
```

### (3) Fix the day-wrap interpolation (`dt`)

```cpp
// L1148-1160, wrap branch
if (!bTargetFound)
{
    currentTarget      = Targets[0];
    lastTarget         = Targets[TargetCount - 1];
    currentTarget.Time = Targets[0].Time + (60 * 60 * 24);   // keep it an ABSOLUTE time
}
```
and make `dt` signed so a bad pair cannot silently become 4.29e9:

```cpp
int32_t dt = (int32_t)(currentTarget.Time - lastTarget.Time);
if (dt <= 0) { dt = 1; }        // guard
```

## 6. What needs the user / hardware (cannot be done from the repository alone)

1. **Confirm the on/off threshold on the real hardware.** `PWM_OFF_SNAP_COUNTS` (and the new
   `PWM_MIN`) depend on the LED driver + LED string: at which PWM count the light actually
   goes visibly dark. Requires flashing and observing the tank at night.
2. **Serial log while reproducing.** Needed to confirm which branch fires and to see the PCA9685
   write pattern (see the instrumentation below). Requires USB/OTA access to the device.
3. **Decision on the intended end behaviour:** hard off at the end of the ramp vs. a permanent
   dim "moonlight" floor. The original `PWM_MIN` comment ("defines a minimum light value")
   suggests a floor was once intended; if a moonlight floor is wanted, set `PWM_MIN` to that
   level and it will hold — but then the LEDs will never go dark.
4. **I2C clock check.** If `Wire.setClock()` is never called (it is not, in this firmware), the
   bus runs at 100 kHz. Raising it to 400 kHz would cut the write-storm factor ~4×; needs
   verification that the DS3231 and PCA9685 are happy on the installed wiring.

## 7. Troubleshooting plan

### 7.1 Instrument (temporary serial debug, one channel is enough)

```cpp
// in PwmChannel::proceedCycle(), just before the fade block
static uint32_t _dbgLast = 0;
if (millis() - _dbgLast >= 100) {
    _dbgLast = millis();
    Serial.printf("ch=%u sod=%ld mi=%ld vx=%.3f tgt=%d val=%d\n",
                  ChannelAddress, (long)currentSecOfDay, (long)currentMilliOfSec,
                  vx, _PwmTarget, _PwmValue);
}
```

### 7.2 Decision tree

1. **Reproduce with a debug schedule.** Set one channel to `21:30;100` / `21:36;0` (a 6-minute
   fade to zero, much faster to iterate than a real evening ramp). Watch the tank for the blink
   in the last 5 seconds.
2. **Read the serial log during the last 10 s of the fade.**
   * `vx` and `tgt` **non-monotonic** in the last seconds, `tgt` hitting 0 and coming back to
     1-15 → **confirms §3.1**; apply fix (1) + (2).
   * `vx` monotonic and reaching 0, but `val`/`CurrentWriteValue` still toggling → the jitter
     comes from somewhere else (e.g. `TestMode` left armed, or a second writer) → check
     `/api/status` for `test_mode: true` (fix: `POST /api/test/exit`).
   * `vx` **frozen** at a constant value during the evening/night → that is §4 (the `dt` wrap
     bug) → apply fix (3).
   * Nothing changes in `vx`/`tgt` but the light blinks anyway → the firmware is not the cause;
     look at the hardware (see 7.3).
3. **Separate firmware from hardware by holding a static low value.** `POST /api/test/start`
   then `POST /api/test/update {"channel":0,"value":1}` (≈41 counts) and let it sit. `TestMode`
   expires after 60 s (L1185), re-send every 30 s.
   * Steady light → the PCA9685 path and the LEDs are fine; the blink is in the fade logic.
   * Blinking at ~1 Hz **even with no writes at all** → the PCA9685 is being disturbed
     (I2C noise, shared bus with the DS3231, power rail dip) or the LED driver's PWM input is
     marginal at low duty — hardware/wiring investigation, not firmware.
4. **Cross-check the time base.** `GET /api/status` returns `time`, `current_seconds`,
   `time_source`. Poll it once per second for a minute and check that `current_seconds`
   increases by exactly 1 each time and never stalls or jumps. A stall/jump points at the RTC
   (DS3231) or the 300 s re-sync, and would also widen the second-order effects in §3.1.
5. **Rule out macro-specific behaviour.** Activate the movie-mode macro and watch `/api/status`
   (`macro_active`, `macro_expires_in`). If the blink starts **before** the macro's final
   target time, the fade maths is to blame (§3); if it starts exactly when the macro expires
   and `restoreSchedule()` runs, the problem is in the macro teardown path instead.

### 7.3 If it turns out to be hardware

* Drive an oscilloscope / logic analyser on one PCA9685 output while the fade runs — this
  distinguishes "the firmware really is writing 0/non-zero" from "the driver is chopping".
* Check the PCA9685 VCC decoupling and the I2C pull-ups; a shared bus with the DS3231 plus
  ~1200 writes/s is a plausible source of corrupted register writes.
* Confirm the Meanwell LDD's minimum duty behaviour — some drivers become unstable below ~1 %
  duty and can pulse at low frequency, which would mimic a firmware blink.

## 8. Verification status

* Root cause: derived from the source and **reproduced in a 1:1 simulation** of the exact
  arithmetic (`PwmChannel::proceedCycle()` + TimeLib `now()`/`setTime()` semantics). The
  simulation is the only executed evidence; no hardware was available.
* The fix in §5 is a **proposal** and has **not been compiled or flashed** — PlatformIO is not
  installed on the machine that produced this document. Compile with
  `pio run -e esp8266` and verify with §7 before trusting it.
* The numbers in §3.1 are arithmetic consequences of `PWM_MAX=4095`, `dv` and `dt`, not
  measurements.

## 9. References

* `src/AquaControl.cpp` L869-923 (`AquaControl::proceedCycle`), L1017-1024 (`writePwmToDevice`),
  L1103-1242 (`PwmChannel::proceedCycle`), L577-670 (`initTimeKeeper`), L715-850 (`init`)
* `src/AquaControl.h` L199-227 (`PwmChannel`, `_PwmValue = 1`), L91 (`PWM_STEP 5`),
  L180-184 (`Target`: `uint8_t Value`)
* TimeLib (`PaulStoffregen/Time`) `Time.cpp`: `now()`, `setTime()`, `setSyncProvider()`,
  `syncInterval = 300`
* `extras/SDCard/config/ledch_05.cfg` (real config used for the simulation)
