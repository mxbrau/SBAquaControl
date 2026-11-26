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

// --- Target storage: issues #29 + #40 -------------------------------------
//
// The bug these cover lived in the DISAGREEMENT between addTarget()'s insert
// order and proceedCycle()'s search order, so each test drives both.

// Regression for the blackout in issue #40: the web UI appends an end-of-day
// sentinel at time 86400 on every render (chart-manager.js). The old addTarget
// sorted on (Time % 86400), which put that sentinel at index 0 while it still
// compared greater than every "now" - so the search picked it 86400 times a
// second and interpolated it against its neighbour. Both endpoints held the same
// value, so the whole day flattened to a constant, and for a schedule that ends
// with the lights off that constant was 0%: the tank went dark on every save.
static void addDayNightWithEndOfDaySentinel(aqc::TargetList &list) {
    // Control points 08:00->50, 12:00->100, 18:00->80, 22:00->0, plus the two
    // boundary sentinels the chart injects (x=0 and x=86400, both carrying
    // last.y = 0).
    list.addTarget({0, 0});
    list.addTarget({86400, 0});
    list.addTarget({8 * 3600, 50});
    list.addTarget({12 * 3600, 100});
    list.addTarget({18 * 3600, 80});
    list.addTarget({22 * 3600, 0});
}

void test_addtarget_keeps_86400_sentinel_sorted_last(void) {
    aqc::TargetList list;
    addDayNightWithEndOfDaySentinel(list);

    // 6 targets stored (none collapsed), strictly ascending by raw Time.
    TEST_ASSERT_EQUAL_INT(6, list.count);
    TEST_ASSERT_TRUE(list.isSortedUnique());
    // The 86400 sentinel must be LAST, not first - that ordering is the fix.
    TEST_ASSERT_EQUAL_INT32(86400, list.targets[5].Time);
    TEST_ASSERT_EQUAL_INT32(0, list.targets[0].Time);
}

void test_end_of_day_sentinel_does_not_blackout_the_day(void) {
    aqc::TargetList list;
    addDayNightWithEndOfDaySentinel(list);

    // Midday must interpolate to roughly full brightness, not 0.
    float noon = aqc::targetSearchAndInterpolate(list, 12 * 3600);
    TEST_ASSERT_TRUE(noon > 90.0f);

    // Morning ramp is alive.
    float morning = aqc::targetSearchAndInterpolate(list, 10 * 3600);
    TEST_ASSERT_TRUE(morning > 40.0f && morning < 90.0f);

    // Evening ramp descends towards off.
    float evening = aqc::targetSearchAndInterpolate(list, 21 * 3600);
    TEST_ASSERT_TRUE(evening < 30.0f);

    // Night is genuinely off.
    float night = aqc::targetSearchAndInterpolate(list, 23 * 3600);
    TEST_ASSERT_TRUE(night < 1.0f);

    // The old bug returned 0.0 at EVERY one of these samples.
}

void test_same_schedule_without_sentinel_matches(void) {
    // The same schedule minus the boundary sentinels must produce the same
    // daytime curve - i.e. the sentinel is now inert rather than destructive.
    aqc::TargetList withSentinel;
    addDayNightWithEndOfDaySentinel(withSentinel);
    aqc::TargetList without;
    without.addTarget({8 * 3600, 50});
    without.addTarget({12 * 3600, 100});
    without.addTarget({18 * 3600, 80});
    without.addTarget({22 * 3600, 0});

    long probes[] = {9 * 3600, 11 * 3600, 13 * 3600, 17 * 3600, 19 * 3600};
    for (unsigned i = 0; i < sizeof(probes) / sizeof(probes[0]); i++) {
        TEST_ASSERT_FLOAT_WITHIN(
            0.5f, aqc::targetSearchAndInterpolate(without, probes[i]),
            aqc::targetSearchAndInterpolate(withSentinel, probes[i]));
    }
}

// Issue #29: two targets for the same second collapse to one, last edit wins.
void test_addtarget_replaces_duplicate_time(void) {
    aqc::TargetList list;
    list.addTarget({3600, 10});
    list.addTarget({7200, 20});
    TEST_ASSERT_EQUAL_INT(2, list.count);

    int pos = list.addTarget({3600, 99});
    TEST_ASSERT_EQUAL_INT(2, list.count);              // no third entry
    TEST_ASSERT_EQUAL_INT(0, pos);                     // replaced in place
    TEST_ASSERT_EQUAL_INT32(3600, list.targets[0].Time);
    TEST_ASSERT_EQUAL_INT(99, list.targets[0].Value);  // later value wins
    TEST_ASSERT_TRUE(list.isSortedUnique());
}

// Issue #29: the UI sends targets in whatever order it holds them; the stored
// array must come out ascending regardless of insertion order.
void test_addtarget_sorts_unsorted_insertion_order(void) {
    aqc::TargetList list;
    list.addTarget({85800, 2});   // 23:50 - arrives FIRST on the wire
    list.addTarget({86340, 0});   // 23:59 - arrives second: was the unsorted tail
    list.addTarget({25200, 0});   // 07:00
    list.addTarget({0, 0});       // 00:00

    TEST_ASSERT_EQUAL_INT(4, list.count);
    TEST_ASSERT_TRUE(list.isSortedUnique());
    TEST_ASSERT_EQUAL_INT32(0, list.targets[0].Time);
    TEST_ASSERT_EQUAL_INT32(25200, list.targets[1].Time);
    TEST_ASSERT_EQUAL_INT32(85800, list.targets[2].Time);
    TEST_ASSERT_EQUAL_INT32(86340, list.targets[3].Time);
}

// Issue #29's reported data had two entries at time 0.
void test_duplicate_midnight_collapses(void) {
    aqc::TargetList list;
    list.addTarget({0, 0});
    list.addTarget({0, 0});
    list.addTarget({25200, 0});
    TEST_ASSERT_EQUAL_INT(2, list.count);
    TEST_ASSERT_TRUE(list.isSortedUnique());
}

// Inserting between neighbours shifts the tail and keeps the order.
void test_addtarget_inserts_in_middle(void) {
    aqc::TargetList list;
    list.addTarget({0, 0});
    list.addTarget({7200, 30});
    int pos = list.addTarget({3600, 15});
    TEST_ASSERT_EQUAL_INT(1, pos);
    TEST_ASSERT_EQUAL_INT(3, list.count);
    TEST_ASSERT_EQUAL_INT32(0, list.targets[0].Time);
    TEST_ASSERT_EQUAL_INT32(3600, list.targets[1].Time);
    TEST_ASSERT_EQUAL_INT32(7200, list.targets[2].Time);
}

// A full channel refuses further targets and says so, instead of dropping them
// silently (issue #40) - the UI used to send 128 against a 32 cap.
void test_addtarget_reports_full_channel(void) {
    aqc::TargetList list;
    for (int i = 0; i < aqc::MAX_TARGET_COUNT; i++) {
        TEST_ASSERT_NOT_EQUAL(aqc::ADD_TARGET_FULL, list.addTarget({i * 60, 50}));
    }
    TEST_ASSERT_EQUAL_INT(aqc::MAX_TARGET_COUNT, list.count);
    // One past the cap: refused, count unchanged.
    TEST_ASSERT_EQUAL_INT(aqc::ADD_TARGET_FULL, list.addTarget({86399, 10}));
    TEST_ASSERT_EQUAL_INT(aqc::MAX_TARGET_COUNT, list.count);
}

// Replacing a time at the cap must still work - it stores nothing new.
void test_addtarget_replace_still_works_when_full(void) {
    aqc::TargetList list;
    for (int i = 0; i < aqc::MAX_TARGET_COUNT; i++) {
        list.addTarget({i * 60, 50});
    }
    int pos = list.addTarget({600, 77});  // same second as an existing entry
    TEST_ASSERT_EQUAL_INT(10, pos);
    TEST_ASSERT_EQUAL_INT(aqc::MAX_TARGET_COUNT, list.count);
    TEST_ASSERT_EQUAL_INT(77, list.targets[10].Value);
}

void test_remove_target_preserves_order(void) {
    aqc::TargetList list;
    list.addTarget({0, 0});
    list.addTarget({3600, 10});
    list.addTarget({7200, 20});
    TEST_ASSERT_TRUE(list.removeTargetAt(1));
    TEST_ASSERT_EQUAL_INT(2, list.count);
    TEST_ASSERT_TRUE(list.isSortedUnique());
    TEST_ASSERT_EQUAL_INT32(0, list.targets[0].Time);
    TEST_ASSERT_EQUAL_INT32(7200, list.targets[1].Time);
    // Out of range is a no-op.
    TEST_ASSERT_FALSE(list.removeTargetAt(5));
    TEST_ASSERT_EQUAL_INT(2, list.count);
}

// An empty channel is an explicit "off" state - the reason a failed save used to
// black out a working schedule (issue #40).
void test_empty_channel_is_off(void) {
    aqc::TargetList list;
    TEST_ASSERT_EQUAL_FLOAT(-1.0f, aqc::targetSearchAndInterpolate(list, 3600));
}

// A single target holds its value across the whole day.
void test_single_target_is_constant_all_day(void) {
    aqc::TargetList list;
    list.addTarget({3600, 60});
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 60.0f,
                             aqc::targetSearchAndInterpolate(list, 0));
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 60.0f,
                             aqc::targetSearchAndInterpolate(list, 43200));
}

// Past the last target the curve ramps into the next day's first target.
void test_day_wrap_into_next_day_first_target(void) {
    aqc::TargetList list;
    list.addTarget({3600, 0});    // 01:00 -> 0
    list.addTarget({82800, 80});  // 23:00 -> 80
    // 23:30 sits between the last target (23:00, 80%) and tomorrow's first
    // (01:00+24h, 0%): a 2 h ramp, half elapsed, so 80 - 80*0.5 = 40%...
    // the ramp runs 23:00 -> 01:00, i.e. dt = 7200 s, and 1800 s in gives
    // 80 - 80*(1800/7200) = 60%.
    float vx = aqc::targetSearchAndInterpolate(list, 23 * 3600 + 1800);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 60.0f, vx);
}

// The end-of-day sentinel holds the schedule's final value until midnight
// instead of ramping into the next day - which is what makes it safe to send.
void test_end_of_day_sentinel_holds_final_value(void) {
    aqc::TargetList list;
    list.addTarget({3600, 0});
    list.addTarget({82800, 80});
    list.addTarget({86400, 80});  // hold 80% to midnight

    float vx = aqc::targetSearchAndInterpolate(list, 23 * 3600 + 3600);  // 00:00
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 80.0f, vx);
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
    RUN_TEST(test_addtarget_keeps_86400_sentinel_sorted_last);
    RUN_TEST(test_end_of_day_sentinel_does_not_blackout_the_day);
    RUN_TEST(test_same_schedule_without_sentinel_matches);
    RUN_TEST(test_addtarget_replaces_duplicate_time);
    RUN_TEST(test_addtarget_sorts_unsorted_insertion_order);
    RUN_TEST(test_duplicate_midnight_collapses);
    RUN_TEST(test_addtarget_inserts_in_middle);
    RUN_TEST(test_addtarget_reports_full_channel);
    RUN_TEST(test_addtarget_replace_still_works_when_full);
    RUN_TEST(test_remove_target_preserves_order);
    RUN_TEST(test_empty_channel_is_off);
    RUN_TEST(test_single_target_is_constant_all_day);
    RUN_TEST(test_day_wrap_into_next_day_first_target);
    RUN_TEST(test_end_of_day_sentinel_holds_final_value);
    return UNITY_END();
}
