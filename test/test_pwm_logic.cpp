// test_pwm_logic.cpp - host unit tests for the firmware scheduling maths.
//
// Mirrors src/AquaControl.cpp PwmChannel::proceedCycle (interpolation +
// slew-rate limiter) and src/Webserver.cpp parseTimeToSeconds via the
// dependency-free mirror in ../support/aqua_logic.h (approach 2 of
// GitHub issue #10). If the firmware changes,
// update the mirror and these expectations together.
//
// Build/run:  pio test -e test        (no hardware needed)
//             pio run -e test         (must also succeed: empty src filter)

#include <unity.h>

#include "aqua_logic.h"

// Native PWM constants (src/AquaControl.h, non-AVR/non-ESP8266 branch).
static const uint16_t PWM_MAX_NATIVE = 255;
static const int16_t PWM_STEP_NATIVE = 1;

void setUp(void) {}
void tearDown(void) {}

// --- Linear interpolation -------------------------------------------------

// Midpoint of a 0% -> 100% ramp over 100 s is 50% -> 127 counts.
void test_interpolation_midpoint(void) {
    float vx = aqc::interpolatePercent(0, 0, 100, 100, 50, 0);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 50.0f, vx);
    TEST_ASSERT_EQUAL_UINT16(127, aqc::percentToPwm(vx, PWM_MAX_NATIVE));
}

// Millisecond resolution: halfway between whole seconds.
void test_interpolation_subsecond(void) {
    float vx = aqc::interpolatePercent(0, 0, 100, 100, 50, 500);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 50.5f, vx);
}

// Past the end of a falling ramp the value clamps to the target, never below.
void test_interpolation_clamps_at_target(void) {
    float vx = aqc::interpolatePercent(0, 100, 100, 20, 150, 0);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 20.0f, vx);
}

// Past the end of a rising ramp the value clamps to the target, never above.
void test_interpolation_clamps_rising(void) {
    float vx = aqc::interpolatePercent(0, 0, 100, 80, 200, 0);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 80.0f, vx);
}

// Midnight rollover: last target 23:00 @80%, next-day target 01:00 @20%,
// evaluated at 23:30 -> 65%. The next-day target is expressed in the
// last-anchored frame (+86400, cf. the target search in src/AquaControl.cpp),
// so the ramp spans dt = 7200 s and 1800 s in gives 80 - 60*1800/7200 = 65%.
void test_interpolation_midnight_rollover(void) {
    const long last = 23 * 3600;              // 82800
    const long wrappedCurrent = last + 7200;  // next-day 01:00 as 90000
    float vx = aqc::interpolatePercent(last, 80, wrappedCurrent, 20,
                                       23 * 3600 + 1800, 0);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 65.0f, vx);
}

// --- Slew-rate limiter ----------------------------------------------------

// Small gaps step by exactly PWM_STEP per cycle.
void test_slew_steps_up_by_single_step(void) {
    TEST_ASSERT_EQUAL_INT16(11, aqc::slewStep(50, 10, PWM_STEP_NATIVE));
}

// Large gaps (>100 counts) take a double step per cycle (fast fade).
void test_slew_double_steps_on_large_gap(void) {
    TEST_ASSERT_EQUAL_INT16(12, aqc::slewStep(200, 10, PWM_STEP_NATIVE));
    TEST_ASSERT_EQUAL_INT16(198, aqc::slewStep(10, 200, PWM_STEP_NATIVE));
}

// Overshoot snaps to the target instead of oscillating around it.
void test_slew_snaps_on_overshoot(void) {
    TEST_ASSERT_EQUAL_INT16(50, aqc::slewStep(50, 49, 5));
    TEST_ASSERT_EQUAL_INT16(50, aqc::slewStep(50, 51, 5));
}

// Dim-to-off boundary (suspected cause of #1): from a low value the channel
// must walk down to exactly 0 and stay there - no wrap, no stuck-at-1.
void test_slew_dim_to_off_reaches_zero(void) {
    int16_t v = 3;
    v = aqc::slewStep(0, v, PWM_STEP_NATIVE);
    TEST_ASSERT_EQUAL_INT16(2, v);
    v = aqc::slewStep(0, v, PWM_STEP_NATIVE);
    TEST_ASSERT_EQUAL_INT16(1, v);
    v = aqc::slewStep(0, v, PWM_STEP_NATIVE);
    TEST_ASSERT_EQUAL_INT16(0, v);
    // Settled: further cycles are a no-op (HasToWritePwm stays false).
    TEST_ASSERT_EQUAL_INT16(0, aqc::slewStep(0, v, PWM_STEP_NATIVE));
}

// Equal target and value: no step at all.
void test_slew_holds_when_settled(void) {
    TEST_ASSERT_EQUAL_INT16(100, aqc::slewStep(100, 100, PWM_STEP_NATIVE));
}

// The PWM_MIN clamp passes 0 through (off stays off) - with PWM_MIN == 1
// there is no integer between 0 and 1, so only 0 and >=1 occur.
void test_min_clamp_off_stays_off(void) {
    TEST_ASSERT_EQUAL_UINT16(0, aqc::applyMinClamp(0));
    TEST_ASSERT_EQUAL_UINT16(1, aqc::applyMinClamp(1));
    TEST_ASSERT_EQUAL_UINT16(255, aqc::applyMinClamp(255));
}

// --- Time-string parsing --------------------------------------------------

void test_parse_hh_mm(void) {
    TEST_ASSERT_EQUAL_INT32(8 * 3600 + 30 * 60, aqc::parseTimeToSeconds("08:30"));
}

void test_parse_midnight_and_end_of_day(void) {
    TEST_ASSERT_EQUAL_INT32(0, aqc::parseTimeToSeconds("00:00"));
    TEST_ASSERT_EQUAL_INT32(23 * 3600 + 59 * 60, aqc::parseTimeToSeconds("23:59"));
}

// First field >= 24 means MM:SS (macro durations), not HH:MM.
void test_parse_mm_ss_branch(void) {
    TEST_ASSERT_EQUAL_INT32(90 * 60, aqc::parseTimeToSeconds("90:00"));
}

// Plain digits are already seconds.
void test_parse_plain_seconds(void) {
    TEST_ASSERT_EQUAL_INT32(3600, aqc::parseTimeToSeconds("3600"));
    TEST_ASSERT_EQUAL_INT32(0, aqc::parseTimeToSeconds("0"));
}

int main(void) {
    UNITY_BEGIN();
    RUN_TEST(test_interpolation_midpoint);
    RUN_TEST(test_interpolation_subsecond);
    RUN_TEST(test_interpolation_clamps_at_target);
    RUN_TEST(test_interpolation_clamps_rising);
    RUN_TEST(test_interpolation_midnight_rollover);
    RUN_TEST(test_slew_steps_up_by_single_step);
    RUN_TEST(test_slew_double_steps_on_large_gap);
    RUN_TEST(test_slew_snaps_on_overshoot);
    RUN_TEST(test_slew_dim_to_off_reaches_zero);
    RUN_TEST(test_slew_holds_when_settled);
    RUN_TEST(test_min_clamp_off_stays_off);
    RUN_TEST(test_parse_hh_mm);
    RUN_TEST(test_parse_midnight_and_end_of_day);
    RUN_TEST(test_parse_mm_ss_branch);
    RUN_TEST(test_parse_plain_seconds);
    return UNITY_END();
}
