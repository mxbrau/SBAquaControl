// aqua_logic.h - dependency-free mirror of SBAquaControl's pure scheduling maths.
//
// Approach 2 from GitHub issue #10: the firmware
// sources (src/AquaControl.cpp, src/Webserver.cpp) cannot compile on the host
// because they drag in <Arduino.h>, ESP8266/SD/TimeLib headers, so the pure
// logic is mirrored here function-for-function with NO Arduino dependencies.
// Every function cites the exact firmware lines it mirrors. If the firmware
// changes, update the mirror AND the tests together.
//
// Native-build constants (src/AquaControl.h, non-AVR/non-ESP8266 branch):
//   PWM_STEP 1, PWM_MAX 255, PWM_CHANNELS 4, PWM_MIN 1 (AquaControl.cpp).

#pragma once

#include <stdint.h>
#include <stdlib.h>
#include <string>

namespace aqc {

// --- Target storage: PwmChannel, src/AquaControl.h ------------------------
//
// Mirrors the fixed PwmChannel (issues #29 + #40). MAX_TARGET_COUNT is 32 on
// ESP8266 (src/AquaControl_config.h); the host tests use the same number so the
// cap behaviour is exercised rather than assumed.

static const int MAX_TARGET_COUNT = 32;
static const int SECS_PER_DAY = 86400;
static const int ADD_TARGET_FULL = 0xFF;  // PwmChannel::ADD_TARGET_FULL

struct Target {
    long Time;   // seconds since midnight, [0, 86400]; 86400 == end of day
    int Value;   // percent, 0-100
};

// Mirror of PwmChannel's schedule array + addTarget()/removeTargetAt().
//
// INVARIANT (issues #29 + #40): targets[0..count) is strictly ascending by the
// RAW Time, no two entries share a Time, and addTarget() is the only supported
// mutator. The invariant is the whole point of the fix: the insert order and
// the order proceedCycle() searches must be the SAME key.
struct TargetList {
    Target targets[MAX_TARGET_COUNT];
    int count;

    TargetList() : count(0) {}

    // PwmChannel::addTarget, src/AquaControl.cpp.
    //
    // Position is the first index whose Time is >= t.Time, so an exact match
    // lands ON that entry and replaces its Value (last edit wins). Note the
    // ">=" : scanning for the first entry strictly greater steps past an exact
    // match and would insert a duplicate instead.
    //
    // Order of the two checks is load-bearing and mirrors the firmware: the
    // replace is tested FIRST because it stores no new slot, so a channel that
    // is exactly full must still accept an edit to a second it already holds
    // (the UI's "set this timepoint" flow depends on that). The capacity check
    // then guards only the genuinely-new-slot path - it must come before the
    // shift, which writes targets[count].
    int addTarget(Target t) {
        int pos = 0;
        while (pos < count && targets[pos].Time < t.Time) {
            pos++;
        }
        if (pos < count && targets[pos].Time == t.Time) {
            targets[pos].Value = t.Value;
            return pos;
        }
        if (count >= MAX_TARGET_COUNT) {
            return ADD_TARGET_FULL;
        }
        for (int n = count; n > pos; n--) {
            targets[n] = targets[n - 1];
        }
        targets[pos] = t;
        count++;
        return pos;
    }

    // PwmChannel::removeTargetAt, src/AquaControl.cpp
    bool removeTargetAt(int pos) {
        if (pos < 0 || pos >= count) {
            return false;
        }
        for (int i = pos; i < count - 1; i++) {
            targets[i] = targets[i + 1];
        }
        count--;
        return true;
    }

    bool isSortedUnique() const {
        for (int i = 1; i < count; i++) {
            if (targets[i - 1].Time >= targets[i].Time) {
                return false;
            }
        }
        return true;
    }
};

// --- Interpolation: PwmChannel::proceedCycle, src/AquaControl.cpp --------
//   int16_t dv = currentTarget.Value - lastTarget.Value;
//   int32_t dt = (int32_t)(currentTarget.Time - lastTarget.Time);
//   if (dt <= 0) { dt = 1; dv = 0; }        // issue #7 guard
//   float m = ((float)dv) / ((float)dt) / 1000.0;
//   float n = ((float)lastTarget.Value);
//   float deltaNow = ((float)(CurrentSecOfDay - lastTarget.Time) * 1000.0)
//                  + (float)CurrentMilli;
//   float vx = (m * deltaNow) + n;
//   clamp vx towards currentTarget.Value ...
//   _PwmTarget = (uint16_t)(((float)PWM_MAX * vx) / 100.0);
//
// Returns the interpolated brightness in percent (vx after clamping).
//
// Issue #40 note: dt is SIGNED and the dt <= 0 guard is present, matching the
// firmware. The previous mirror used `unsigned long dt` with no guard, so it
// tested different maths than the device runs - the mirror had drifted.
inline float interpolatePercent(long lastTime, int lastValue, long currentTime,
                                int currentValue, long nowSec, long nowMilli) {
    int16_t dv = (int16_t)(currentValue - lastValue);
    int32_t dt = (int32_t)(currentTime - lastTime);
    if (dt <= 0) {  // issue #7: a degenerate pair holds the last value
        dt = 1;
        dv = 0;
    }
    float m = ((float)dv) / ((float)dt) / 1000.0f;
    float n = ((float)lastValue);
    float deltaNow = ((float)(nowSec - lastTime) * 1000.0f) + (float)nowMilli;
    float vx = (m * deltaNow) + n;
    if (m > 0.0f) {
        if (vx > (float)currentValue) {
            vx = (float)currentValue;
        }
    } else {
        if (vx < (float)currentValue) {
            vx = (float)currentValue;
        }
    }
    return vx;
}

// --- Target selection: PwmChannel::proceedCycle, src/AquaControl.cpp ------
//
// The half of proceedCycle() that issues #29/#40 turned on: find the first
// target whose RAW Time is greater than now, take its predecessor as the anchor
// (wrapping to yesterday's last target when the match is the first entry), and
// interpolate. Reproduced here because the bug lived in the DISAGREEMENT between
// this search and addTarget()'s insert order - neither half is wrong alone, so
// only a test that runs both can catch it.
//
// Returns the interpolated percent, or -1.0 for a channel with no targets
// (the firmware's TargetCount == 0 branch, which forces the output to 0).
inline float targetSearchAndInterpolate(const TargetList &list, long nowSec,
                                        long nowMilli = 0) {
    if (list.count == 0) {
        return -1.0f;  // proceedCycle else-branch: forced off
    }

    Target currentTarget;
    Target lastTarget;

    if (list.count == 1) {
        // Constant value across the whole day.
        currentTarget.Time = SECS_PER_DAY;
        currentTarget.Value = lastTarget.Value = list.targets[0].Value;
        lastTarget.Time = 0;
    } else {
        bool found = false;
        for (int t = 0; t < list.count; t++) {
            if (list.targets[t].Time > nowSec) {  // RAW Time - same key as addTarget
                currentTarget = list.targets[t];
                found = true;
                if (t == 0) {
                    // First event of the day: anchor on yesterday's last target,
                    // expressed as a negative offset.
                    lastTarget.Time =
                        0 - (SECS_PER_DAY - list.targets[list.count - 1].Time);
                    lastTarget.Value = list.targets[list.count - 1].Value;
                } else {
                    lastTarget = list.targets[t - 1];
                }
                break;
            }
        }
        if (!found) {
            // Past the last target: ramp into the next day's first target.
            currentTarget = list.targets[0];
            lastTarget = list.targets[list.count - 1];
            currentTarget.Time = list.targets[0].Time + SECS_PER_DAY;
        }
    }

    return interpolatePercent(lastTarget.Time, lastTarget.Value, currentTarget.Time,
                              currentTarget.Value, nowSec, nowMilli);
}

// Percent -> device PWM counts, same formula as _PwmTarget above.
inline uint16_t percentToPwm(float vxPercent, uint16_t pwmMax) {
    return (uint16_t)(((float)pwmMax * vxPercent) / 100.0f);
}

// --- Slew-rate limiter: same function, one step ---------------------------
//   if (_PwmTarget > _PwmValue) { _PwmValue += PWM_STEP;
//       if (_PwmTarget > _PwmValue + 100) _PwmValue += PWM_STEP;
//       if (_PwmValue > _PwmTarget) _PwmValue = _PwmTarget; }
//   else { mirror image with -= }
// _PwmValue is int16_t in firmware, so stepping below zero cannot wrap;
// the overshoot snap pins it to the target instead.
inline int16_t slewStep(int16_t target, int16_t value, int16_t step) {
    if (target > value) {
        value += step;
        if (target > value + 100) {
            value += step;
        }
        if (value > target) {
            value = target;
        }
    } else if (target < value) {
        value -= step;
        if (target < value - 100) {
            value -= step;
        }
        if (value < target) {
            value = target;
        }
    }
    return value;
}

// --- Dim-to-off clamp: same function ---------------------------------------
//   CurrentWriteValue = _PwmValue;
//   if (CurrentWriteValue > 0 && CurrentWriteValue < PWM_MIN)
//       CurrentWriteValue = PWM_MIN;            // PWM_MIN == 1
inline uint16_t applyMinClamp(int16_t pwmValue) {
    uint16_t w = (uint16_t)pwmValue;
    if (w > 0 && w < 1) {
        w = 1;
    }
    return w;
}

// --- Time-string parsing: parseTimeToSeconds, src/Webserver.cpp:120 -------
//   "HH:MM" when the first field < 24, else "MM:SS"; plain digits = seconds.
// Arduino String::toInt() parses a leading integer (stops at first
// non-digit); strtol has the same behaviour, so it is used here. Note the
// firmware narrows both fields to int8_t, so values >= 128 would overflow
// there but not here; all schedule/macro values stay well below that, and
// so do these tests.
inline long parseTimeToSeconds(const std::string &timeStr) {
    std::string::size_type colon = timeStr.find(':');
    if (colon != std::string::npos) {
        long first = strtol(timeStr.substr(0, colon).c_str(), NULL, 10);
        long second = strtol(timeStr.substr(colon + 1).c_str(), NULL, 10);
        if (first >= 24) {
            return (first * 60) + second;  // MM:SS
        } else {
            return (first * 3600) + (second * 60);  // HH:MM
        }
    } else {
        return strtol(timeStr.c_str(), NULL, 10);
    }
}

}  // namespace aqc
