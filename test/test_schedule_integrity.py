"""Schedule target integrity: issues #29 and #40 (fast, always run).

These are the two halves of the fix that the C++ host tests cannot cover on
their own. test_pwm_logic.cpp exercises the pure maths in
test/support/aqua_logic.h (addTarget's insert order, the proceedCycle target
search, the interpolation). What it cannot see is the WIRING - whether the
firmware source and the Flask mock still agree on that contract after a change.

So this module pins the two things that actually let #29/#40 reach a tank:

1. Source guards on the firmware, in the spirit of test_regressions.py. The
   ordering bug was a disagreement between two functions, and a comment does not
   hold a line in place - a well-meaning edit to either side silently reinstates
   it. These checks fail loudly if the shared-key invariant or the build-then-swap
   in the save handler is undone.

2. Behavioural tests driving the real mock over HTTP, asserting the contract the
   firmware now implements: unique ascending times, last-edit-wins, a 400 for an
   over-long list instead of a silent truncation, and a rejected save leaving the
   stored schedule intact.

The mock half is deliberately also the subject of a separate issue (#41): a mock
can only prove the FIRMWARE matches the MOCK when both are checked against one
shared, readable statement of the rules. Here the rules are spelled out inline so
a divergence is caught as a test failure rather than discovered on hardware.
"""

import json
import os
import re
import urllib.error
import urllib.request

import pytest
from conftest import REPO

AQUA = os.path.join(REPO, "src", "AquaControl.cpp")
AQUA_H = os.path.join(REPO, "src", "AquaControl.h")
FIRMWARE = os.path.join(REPO, "src", "Webserver.cpp")
APP_JS = os.path.join(REPO, "extras", "SDCard", "js", "app.js")

MAX_TARGETS = 32  # MAX_TARGET_COUNT_PER_CHANNEL, ESP8266 branch
END_OF_DAY = 86400


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _body(src, start_marker, end_marker="\n}"):
    start = src.index(start_marker)
    end = src.index(end_marker, start)
    return src[start:end]


# --- 1. Firmware source guards --------------------------------------------


def test_addtarget_does_not_sort_on_modulo():
    """addTarget must NOT order targets on (Time % SECS_PER_DAY).

    This is the exact defect from issue #40. The old insert used
    `elapsedSecsToday(t.Time)` - a TimeLib macro for `t % 86400` - while
    proceedCycle()'s search compared the raw `Targets[t].Time`. A Time of 86400
    therefore sorted to the FRONT of the array yet still compared greater than
    every "now", so the search selected it all day and flattened the channel to a
    constant value (0%, i.e. lights off, for any schedule ending in darkness).

    Sorting on the modulo key is not merely suboptimal, it is the bug: it makes
    the insert order and the search order two different orderings.
    """
    add = _body(_read(AQUA), "uint8_t PwmChannel::addTarget(Target t)")
    assert "elapsedSecsToday" not in add, (
        "PwmChannel::addTarget orders targets on elapsedSecsToday(t.Time), i.e. "
        "t % 86400, while proceedCycle()'s search compares the raw "
        "Targets[t].Time. The two orderings disagree, and a Time of 86400 (the "
        "end-of-day target the web UI appends on every render) then sorts to "
        "index 0 while still comparing greater than every now - which flattened "
        "the whole day to a constant and blacked out the tank on every save "
        "(issue #40). Order on the raw Time, the same key the search uses."
    )


def test_target_search_uses_raw_time():
    """proceedCycle's search must compare the raw Time field.

    The other half of the #40 disagreement. If this ever becomes a modulo or any
    other transform while addTarget orders on the raw Time, the invariant is
    broken again - so pin the comparison itself.
    """
    cyc = _body(_read(AQUA), "void PwmChannel::proceedCycle(")
    assert re.search(r"if \(Targets\[t\]\.Time > CurrentSecOfDay\)", cyc), (
        "the target search in PwmChannel::proceedCycle must test "
        "Targets[t].Time > CurrentSecOfDay on the RAW Time, matching the "
        "ordering addTarget() maintains (issue #40)"
    )


def test_addtarget_replaces_duplicate_time_in_place():
    """A repeated Time must update the existing entry, not append (issue #29).

    Also pins the '>=' detail: scanning for the first entry strictly GREATER than
    the new Time steps past an exact match and inserts a duplicate. That bug
    shipped in the first cut of this fix and was caught by
    test_addtarget_replaces_duplicate_time in test_pwm_logic.cpp.
    """
    add = _body(_read(AQUA), "uint8_t PwmChannel::addTarget(Target t)")
    assert re.search(
        r"while \(pos < TargetCount && Targets\[pos\]\.Time < t\.Time\)", add
    ), (
        "addTarget must scan with 'Targets[pos].Time < t.Time' so the loop stops "
        "ON an exact match. With '<=' (or '>') it steps past the matching entry "
        "and inserts a duplicate time instead of replacing it (issue #29)"
    )
    assert re.search(
        r"if \(pos < TargetCount && Targets\[pos\]\.Time == t\.Time\)", add
    ), (
        "addTarget must detect the exact-match case and replace that entry's "
        "Value in place, so Targets[] cannot contain two entries for the same "
        "second (issue #29)"
    )


def test_addtarget_capacity_check_precedes_the_shift():
    """The MAX_TARGET_COUNT_PER_CHANNEL guard must come before the shift loop.

    The shift writes Targets[TargetCount], which is one past the last valid index
    once the channel is full - so the check has to gate it. A full channel must
    return ADD_TARGET_FULL without touching memory.
    """
    add = _body(_read(AQUA), "uint8_t PwmChannel::addTarget(Target t)")
    guard = add.index("TargetCount >= MAX_TARGET_COUNT_PER_CHANNEL")
    shift = add.index("for (uint8_t n = TargetCount; n > pos; n--)")
    assert guard < shift, (
        "the capacity guard must precede the shift loop in addTarget: the shift "
        "writes Targets[TargetCount], which is out of bounds when the channel "
        "already holds MAX_TARGET_COUNT_PER_CHANNEL entries (issue #40)"
    )


def test_capacity_is_checked_after_the_duplicate_replace():
    """Replacing an existing Time must work even on a full channel.

    A replace stores no new slot, so the capacity guard must not run first -
    otherwise a full channel would refuse to update a timepoint it already has,
    and the UI's "set this timepoint" flow would break on a dense schedule.
    """
    add = _body(_read(AQUA), "uint8_t PwmChannel::addTarget(Target t)")
    replace = add.index("Targets[pos].Value = t.Value")
    guard = add.index("TargetCount >= MAX_TARGET_COUNT_PER_CHANNEL")
    assert replace < guard, (
        "addTarget must handle the same-Time replace before the capacity guard. "
        "A replace adds no slot, so a full channel must still accept it; testing "
        "capacity first makes a full channel reject edits to times it already "
        "holds (issue #40)"
    )


def test_schedule_save_does_not_clear_before_parsing():
    """The save handler must not destroy the live channel before rebuilding it.

    handleApiScheduleSave used to run removeTargetAt(0) in a loop up front and
    then re-add whatever the ad-hoc parser recovered. TargetCount == 0 is an
    explicit lights-off state in proceedCycle(), so any parse shortfall blacked
    out a channel that had a working schedule - while still answering
    200 {"status":"ok"} (issue #40). Parsing must target a scratch channel.
    """
    handler = _body(_read(FIRMWARE), "void handleApiScheduleSave()")
    assert "PwmChannel parsed" in handler, (
        "handleApiScheduleSave must parse into a scratch PwmChannel and commit "
        "only on success. Clearing the live channel first means any parse "
        "shortfall leaves TargetCount == 0, which proceedCycle() drives to 0% - "
        "a blackout of a working schedule, reported as success (issue #40)"
    )
    # The pre-emptive clear loop must be gone from the handler entirely.
    assert "removeTargetAt(0)" not in handler, (
        "handleApiScheduleSave still contains the up-front "
        "removeTargetAt(0) clear loop. Parse into a scratch channel and swap it "
        "in only after the body is fully read (issue #40)"
    )


def test_schedule_save_reports_persist_failure():
    """A failed SD write must not be reported as success (issue #40)."""
    handler = _body(_read(FIRMWARE), "void handleApiScheduleSave()")
    assert "if (!_aqc->writeLedConfig(channel))" in handler, (
        "handleApiScheduleSave must check writeLedConfig()'s return value. It was "
        "discarded, so a failed SD write (card full, removed, locked) still "
        "answered 200 and the change was silently lost on the next boot (issue #40)"
    )


def test_webui_target_cap_matches_firmware():
    """The UI's MAX_TARGETS must equal the firmware cap (issue #40).

    It was 128 with the comment "align with ESP8266 firmware cap" - stale from
    when the cap really was 128. The UI POSTed 128 targets, addTarget refused
    everything past 32, and the surplus was dropped silently: the day was
    truncated to ~05:10 with a success message.
    """
    js = _read(APP_JS)
    m = re.search(r"const MAX_TARGETS = (\d+);", js)
    assert m, "could not find MAX_TARGETS in extras/SDCard/js/app.js"
    assert int(m.group(1)) == MAX_TARGETS, (
        f"app.js MAX_TARGETS is {m.group(1)} but MAX_TARGET_COUNT_PER_CHANNEL is "
        f"{MAX_TARGETS} on ESP8266 (src/AquaControl_config.h). Any excess is "
        "refused by the firmware, so a mismatched cap silently truncates the "
        "schedule (issue #40)"
    )


def test_firmware_writes_end_of_day_as_24_00():
    """Time 86400 must persist as 24:00, not 00:00 (issue #40).

    hour() cannot return 24, so the end-of-day target used to be written as
    00:00 and reloaded as a Time 0 target - turning "hold this value until
    midnight" into "start the day at this value" and colliding with a genuine
    midnight target. readLedConfig already parses 24:00 back into 86400.
    """
    writer = _body(_read(AQUA), "bool AquaControl::writeTargetsToFile(")
    assert 'sprintf(timeBuf, "24:00")' in writer, (
        "writeTargetsToFile must write 24:00 for a Time of 86400 or more. "
        "hour() cannot express it, so it lands on disk as 00:00 and comes back "
        "as a midnight target, corrupting the day boundary on every boot "
        "(issue #40)"
    )


# --- 2. Mock behaviour over HTTP ------------------------------------------
#
# Drives the real Flask mock so the CONTRACT is exercised end to end. These
# assertions are the readable statement of the rules that both the firmware and
# the mock must satisfy.


def _post(base, path, payload):
    req = urllib.request.Request(
        base + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        try:
            return exc.code, json.loads(body)
        except json.JSONDecodeError:
            return exc.code, {"raw": body}


def _get(base, path):
    with urllib.request.urlopen(base + path, timeout=10) as resp:
        return json.loads(resp.read().decode())


@pytest.fixture
def clean_channel(mock_server):
    """Yield the base URL with every channel's schedule emptied."""
    base = mock_server
    _post(base, "/api/schedule/clear", {})
    yield base
    _post(base, "/api/schedule/clear", {})


def test_save_sorts_and_dedupes_by_time(clean_channel):
    """Targets arrive in any order; storage must be ascending and unique (#29).

    Deliberately unsent, with a duplicate and the 86340/85800 pair from #29's
    field report.
    """
    status, body = _post(
        clean_channel,
        "/api/schedule/save",
        {
            "channel": 0,
            "targets": [
                {"time": 85800, "value": 2},
                {"time": 86340, "value": 0},
                {"time": 25200, "value": 0},
                {"time": 0, "value": 0},
                {"time": 0, "value": 0},  # duplicate midnight
            ],
        },
    )
    assert status == 200, body

    times = [
        t["time"] for t in _get(clean_channel, "/api/schedule/get?channel=0")["targets"]
    ]
    assert times == sorted(times), f"targets not ascending: {times}"
    assert len(times) == len(set(times)), f"duplicate times stored: {times}"
    assert 0 in times and 25200 in times and 85800 in times and 86340 in times


def test_duplicate_time_keeps_last_value(clean_channel):
    """A repeated Time collapses to one entry holding the later value (#29)."""
    _post(
        clean_channel,
        "/api/schedule/save",
        {
            "channel": 0,
            "targets": [{"time": 3600, "value": 10}, {"time": 3600, "value": 90}],
        },
    )
    targets = _get(clean_channel, "/api/schedule/get?channel=0")["targets"]
    assert len(targets) == 1, f"expected the duplicate to collapse, got {targets}"
    assert targets[0]["value"] == 90, f"last edit must win, got {targets[0]}"


def test_end_of_day_target_sorts_last(clean_channel):
    """A Time of 86400 must be retained and sort AFTER real times (#40).

    This is the sentinel the chart appends on every render. Clamping it away, or
    letting it sort to the front, is what blacked out the tank.
    """
    status, _ = _post(
        clean_channel,
        "/api/schedule/save",
        {
            "channel": 0,
            "targets": [
                {"time": 86400, "value": 0},
                {"time": 0, "value": 0},
                {"time": 28800, "value": 50},
                {"time": 43200, "value": 100},
            ],
        },
    )
    assert status == 200
    targets = _get(clean_channel, "/api/schedule/get?channel=0")["targets"]
    times = [t["time"] for t in targets]
    assert END_OF_DAY in times, f"end-of-day target was dropped: {times}"
    assert times == sorted(times), f"targets not ascending: {times}"
    assert times[-1] == END_OF_DAY, f"86400 must sort last, got {times}"


def test_end_of_day_target_persists_as_24_00(clean_channel):
    """86400 must round-trip through the .cfg file as 24:00 (#40)."""
    _post(
        clean_channel,
        "/api/schedule/save",
        {
            "channel": 0,
            "targets": [
                {"time": 28800, "value": 50},
                {"time": 86400, "value": 42},
            ],
        },
    )
    from conftest import REPO as _REPO

    cfg = os.path.join(_REPO, "extras", "SDCard", "config", "ledch_00.cfg")
    with open(cfg, encoding="utf-8") as fh:
        text = fh.read()
    assert "24:00;42" in text, (
        f"end-of-day target not written as 24:00;42, file was:\n{text!r}. It must "
        "survive a reboot, and readLedConfig maps 24:00 back to 86400 (issue #40)"
    )
    assert "00:00;42" not in text, (
        "the end-of-day target was written as 00:00, which reloads as a midnight "
        "target and collides with a genuine one (issue #40)"
    )


def test_over_long_list_is_rejected_not_truncated(clean_channel):
    """More targets than the cap must 400, not silently shorten the day (#40).

    The 128-vs-32 mismatch posted 128 targets and got a success response for the
    32 that happened to be kept - the user lost everything after ~05:10.
    """
    targets = [{"time": i * 600, "value": 50} for i in range(MAX_TARGETS + 5)]
    status, body = _post(
        clean_channel, "/api/schedule/save", {"channel": 0, "targets": targets}
    )
    assert status == 400, (
        f"expected 400 for {len(targets)} targets, got {status}: {body}"
    )
    assert "error" in body, f"rejection must carry an error message, got {body}"


def test_exactly_at_the_cap_is_accepted(clean_channel):
    """The boundary case must still succeed - the cap is inclusive."""
    targets = [{"time": i * 600, "value": 50} for i in range(MAX_TARGETS)]
    status, body = _post(
        clean_channel, "/api/schedule/save", {"channel": 0, "targets": targets}
    )
    assert status == 200, (
        f"{MAX_TARGETS} targets must be accepted, got {status}: {body}"
    )
    assert body["target_count"] == MAX_TARGETS


def test_rejected_save_leaves_schedule_intact(clean_channel):
    """A rejected save must not damage the schedule already on the device.

    This is the blackout: the old handler cleared the channel first, so any
    rejection left TargetCount == 0 and proceedCycle() forced the output to 0%.
    """
    good = [{"time": 28800, "value": 50}, {"time": 43200, "value": 100}]
    status, _ = _post(
        clean_channel, "/api/schedule/save", {"channel": 0, "targets": good}
    )
    assert status == 200

    # An over-long list is rejected...
    status, _ = _post(
        clean_channel,
        "/api/schedule/save",
        {
            "channel": 0,
            "targets": [{"time": i * 600, "value": 10} for i in range(MAX_TARGETS + 5)],
        },
    )
    assert status == 400

    # ...and the working schedule is still there.
    after = _get(clean_channel, "/api/schedule/get?channel=0")["targets"]
    assert len(after) == len(good), f"rejected save damaged the schedule: {after}"
    assert [t["time"] for t in after] == [28800, 43200]


def test_unparseable_targets_leave_schedule_intact(clean_channel):
    """Objects present but unusable must 400 and change nothing (#40)."""
    good = [{"time": 28800, "value": 50}, {"time": 43200, "value": 100}]
    _post(clean_channel, "/api/schedule/save", {"channel": 0, "targets": good})

    status, body = _post(
        clean_channel,
        "/api/schedule/save",
        {"channel": 0, "targets": [{"nope": 1}, {"also": "wrong"}]},
    )
    assert status == 400, f"expected 400 for unparseable targets, got {status}: {body}"
    after = _get(clean_channel, "/api/schedule/get?channel=0")["targets"]
    assert len(after) == len(good), f"unparseable save damaged the schedule: {after}"


def test_empty_target_list_clears_the_channel(clean_channel):
    """An explicitly empty list is a legitimate clear, not a parse failure."""
    _post(
        clean_channel,
        "/api/schedule/save",
        {"channel": 0, "targets": [{"time": 3600, "value": 50}]},
    )
    status, body = _post(
        clean_channel, "/api/schedule/save", {"channel": 0, "targets": []}
    )
    assert status == 200, (
        f"an empty list must be accepted as a clear, got {status}: {body}"
    )
    assert body["target_count"] == 0
    assert _get(clean_channel, "/api/schedule/get?channel=0")["targets"] == []


def test_values_are_clamped_to_the_documented_range(clean_channel):
    """Values outside 0-100 are clamped, not truncated into the uint8_t."""
    _post(
        clean_channel,
        "/api/schedule/save",
        {
            "channel": 0,
            "targets": [{"time": 3600, "value": 250}, {"time": 7200, "value": -5}],
        },
    )
    values = {
        t["time"]: t["value"]
        for t in _get(clean_channel, "/api/schedule/get?channel=0")["targets"]
    }
    assert values[3600] == 100, f"250 must clamp to 100, got {values[3600]}"
    assert values[7200] == 0, f"-5 must clamp to 0, got {values[7200]}"


def test_target_add_replaces_existing_time(clean_channel):
    """POST target/add must update, not duplicate (issue #29)."""
    _post(
        clean_channel,
        "/api/schedule/target/add",
        {"channel": 0, "time": 3600, "value": 20},
    )
    _post(
        clean_channel,
        "/api/schedule/target/add",
        {"channel": 0, "time": 3600, "value": 70},
    )
    targets = _get(clean_channel, "/api/schedule/get?channel=0")["targets"]
    assert len(targets) == 1, f"target/add duplicated the time: {targets}"
    assert targets[0]["value"] == 70


def test_target_add_on_a_full_channel_is_rejected(clean_channel):
    """A 33rd distinct timepoint must be refused, not dropped silently (#40)."""
    for i in range(MAX_TARGETS):
        status, _ = _post(
            clean_channel,
            "/api/schedule/target/add",
            {"channel": 0, "time": i * 60, "value": 10},
        )
        assert status == 200, f"target {i} should have been accepted"

    status, body = _post(
        clean_channel,
        "/api/schedule/target/add",
        {"channel": 0, "time": 86399, "value": 10},
    )
    assert status == 400, f"expected 400 on a full channel, got {status}: {body}"
    stored = _get(clean_channel, "/api/schedule/get?channel=0")["targets"]
    assert len(stored) == MAX_TARGETS, f"stored count changed: {len(stored)}"
