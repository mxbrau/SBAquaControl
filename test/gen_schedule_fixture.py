#!/usr/bin/env python3
"""Regenerate test/data/schedules.json - the realistic seed data for the mock.

Produces an aquarium photoperiod for the 6 UI channels inside the device limit
(MAX_TARGET_COUNT_PER_CHANNEL = 32 on ESP8266) and deliberately covers the edge
cases in the manual test guide:

  ch0 Blau      - full photoperiod ramp up/down
  ch1 Weiss     - narrower midday peak
  ch2 Rot       - sunrise/sunset warm accents
  ch3 Gruen     - plateau: identical consecutive values
  ch4 UV        - exactly 32 points = at the device cap
  ch5 Mondlicht - spans midnight (23:59 -> 00:00 wrap)

Every target is a control point (isControl true), sorted by time, 0..86400s.

Usage:
    uv run python test/gen_schedule_fixture.py
"""

import json
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "schedules.json")

H = 3600
M = 60
MAX_TARGETS = 32


def hm(h, m=0):
    return h * H + m * M


# ch0 Blau: smooth blue ramp, on ~07:30-21:00
CH0_BLAU = [
    (hm(7, 30), 0), (hm(8, 0), 5), (hm(8, 30), 20), (hm(9, 0), 40),
    (hm(10, 0), 65), (hm(11, 0), 80), (hm(12, 0), 90), (hm(14, 0), 95),
    (hm(15, 0), 90), (hm(16, 0), 80), (hm(17, 0), 65), (hm(18, 0), 45),
    (hm(19, 0), 22), (hm(20, 0), 6), (hm(21, 0), 0), (hm(22, 30), 0),
]

# ch1 Weiss: narrower, brighter peak around midday
CH1_WEISS = [
    (hm(8, 30), 0), (hm(9, 30), 12), (hm(10, 30), 35), (hm(11, 30), 60),
    (hm(12, 30), 78), (hm(13, 30), 85), (hm(14, 30), 78), (hm(15, 30), 58),
    (hm(16, 30), 32), (hm(17, 30), 12), (hm(18, 30), 0), (hm(20, 0), 0),
]

# ch2 Rot: warm sunrise/sunset accents, low all day
CH2_ROT = [
    (hm(7, 0), 0), (hm(7, 30), 18), (hm(8, 0), 30), (hm(8, 30), 22),
    (hm(12, 0), 10), (hm(16, 0), 12), (hm(18, 0), 25), (hm(18, 30), 40),
    (hm(19, 0), 48), (hm(19, 30), 35), (hm(20, 0), 18), (hm(20, 30), 6),
    (hm(21, 0), 0), (hm(23, 0), 0),
]

# ch3 Gruen: plateau (identical consecutive values) with gentle shoulders
CH3_GRUEN = [
    (hm(9, 0), 0), (hm(10, 0), 25), (hm(11, 0), 50), (hm(12, 0), 50),
    (hm(13, 0), 50), (hm(14, 0), 50), (hm(15, 0), 35), (hm(16, 0), 18),
    (hm(17, 0), 5), (hm(18, 0), 0), (hm(19, 0), 0), (hm(20, 0), 0),
]

# ch4 UV: exactly 32 points (device cap) - gaussian-ish midday bump
CH4_UV = []
for _i in range(32):
    _t = hm(8, 0) + _i * 900  # 08:00 .. 15:45, 15 min apart
    _x = (_t - hm(12, 0)) / (3.2 * H)
    CH4_UV.append((_t, round(35 * pow(2.718281828, -(_x * _x)))))

# ch5 Mondlicht: spans midnight (23:59 -> 00:00), the rollover edge case
CH5_MOND = [
    (hm(0, 0), 12), (hm(2, 0), 15), (hm(4, 0), 15), (hm(5, 30), 8),
    (hm(6, 30), 0), (hm(20, 0), 0), (hm(20, 30), 6), (hm(21, 0), 10),
    (hm(21, 30), 14), (hm(22, 30), 15), (hm(23, 0), 15), (hm(23, 30), 14),
    (hm(23, 59), 12),
]

CHANNELS = {
    0: CH0_BLAU,
    1: CH1_WEISS,
    2: CH2_ROT,
    3: CH3_GRUEN,
    4: CH4_UV,
    5: CH5_MOND,
}


def build():
    data = {}
    problems = []
    for ch, points in CHANNELS.items():
        targets = sorted(
            ({"time": int(t), "value": int(v), "isControl": True} for t, v in points),
            key=lambda x: x["time"],
        )
        if len(targets) > MAX_TARGETS:
            problems.append(f"ch{ch}: {len(targets)} targets exceeds cap {MAX_TARGETS}")
        for t in targets:
            if not 0 <= t["time"] <= 86400:
                problems.append(f"ch{ch}: time out of range {t['time']}")
            if not 0 <= t["value"] <= 100:
                problems.append(f"ch{ch}: value out of range {t['value']}")
        times = [t["time"] for t in targets]
        if times != sorted(times) or len(set(times)) != len(times):
            problems.append(f"ch{ch}: times not strictly ascending")
        data[str(ch)] = targets
    if problems:
        raise SystemExit("fixture invalid:\n  " + "\n  ".join(problems))
    return data


def main():
    data = build()
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"Wrote {OUT}")
    for ch in sorted(data):
        ts = [t["time"] for t in data[ch]]
        print(
            f"  channel {ch}: {len(data[ch]):2d} targets, "
            f"{min(ts) // 3600:02d}:{min(ts) % 3600 // 60:02d} .. "
            f"{max(ts) // 3600:02d}:{max(ts) % 3600 // 60:02d}, "
            f"peak {max(t['value'] for t in data[ch])}%"
        )


if __name__ == "__main__":
    main()
