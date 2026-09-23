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

// --- Interpolation: PwmChannel::proceedCycle, src/AquaControl.cpp --------
//   unsigned long dt = currentTarget.Time - lastTarget.Time;
//   int16_t dv = currentTarget.Value - lastTarget.Value;
//   float m = ((float)dv) / ((float)dt) / 1000.0;
//   float n = ((float)lastTarget.Value);
//   float deltaNow = ((float)(CurrentSecOfDay - lastTarget.Time) * 1000.0)
//                  + (float)CurrentMilli;
//   float vx = (m * deltaNow) + n;
//   clamp vx towards currentTarget.Value ...
//   _PwmTarget = (uint16_t)(((float)PWM_MAX * vx) / 100.0);
//
// Returns the interpolated brightness in percent (vx after clamping).
inline float interpolatePercent(long lastTime, int lastValue, long currentTime,
                                int currentValue, long nowSec, long nowMilli) {
    unsigned long dt = (unsigned long)(currentTime - lastTime);
    int16_t dv = (int16_t)(currentValue - lastValue);
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
