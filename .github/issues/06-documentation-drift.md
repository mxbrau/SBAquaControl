---
title: Documentation drift - memory figures, duplicated roadmap phases, stale testing claims
labels: docs
---

## Symptom

Several status documents contradict the code they describe. Each item below was
verified against the current tree.

### 1. Memory figures are understated

`docs/status/FIRMWARE_STATUS.md` states "SRAM Usage: ~50-55% at compile time",
"Compile-time RAM: 50-55% (normal)" and "RAM usage: 50-55% (healthy)".

Actual build:

```
$ uv run python test/run_checks.py --only build
  [PASS] BUILD ... static RAM 56.3% (46156B data+bss), flash 38.9% (406008B)
```

(the linker's `data+bss` figure; PlatformIO's IDE-style metric reports 62.8% /
51416 B). Either way it is above the documented 50-55%. The
`MAX_TARGET_COUNT_PER_CHANNEL` 128→32 reduction that bought that headroom is real,
but the figure quoted in the docs is stale.

### 2. `ROADMAP.md` has two different "Phase 4" sections

- `## Phase 4: Enhanced Visualization (Q1 2026) - NEXT`
- `## Phase 4: Seasonal & Environmental Profiles (Q2 2026)`

and the "Timeline Summary" lists `Q1 2026: Phase 4 ... (NEXT)` *before*
`Q1-Q2 2026: Phase 3 - COMPLETED`, so the numbering and the ordering contradict
each other. All dates are in the past (it is 2026-09).

### 3. The testing documentation claims there are no known issues

`docs/status/TESTING_GUIDE.md` ends with "Known Issues (v0.5.001): No issues
reported yet", while three investigated bugs exist (LED dim-down blink, WiFi
reachability from phones, macro list latency). Its checklist has never been
executed - every hardware item (test mode, save/load via UI, DS18B20, OTA,
24-hour soak) is still unchecked, and that guide never mentions the automated
layers that now exist (`uv run python test/run_checks.py`, see `test/README.md`).

### 4. Status docs carry per-session logs

`FIRMWARE_STATUS.md` has a "Files Modified This Session" section listing line
numbers from a work session months ago, and a "Testing Checklist" whose state
cannot be trusted. Status documents should describe the *current* state, not a
session.

### 5. Timezone claim contradicts the config

`README.md` lists "No timezone/DST support (UTC only)" as a known limitation,
while `src/AquaControl_config.h` defines `TIMEZONE_OFFSET_HOURS` (default +1,
CET) and `initTimeKeeper()` applies it to NTP results. Whether the limitation is
"no DST" or "no timezone handling at all" needs one answer in both places.

### 6. `.github/scripts/create-issues.sh` was a broken stub

Hardcoded `REPO="yourusername/SBAquaControl"` and created 4 of the 15 issues the
Step 7 plan describes. Replaced by `.github/scripts/create_issues.py` +
`.github/issues/*.md` (done as part of opening these issues).

## Proposed approach

- Put the authoritative resource figures in **one** place and have the docs quote
  that (or simply link to `uv run python test/run_checks.py --only build`).
- Renumber the roadmap phases once, drop the duplicated "Phase 4", and move the
  timeline to relative milestones ("next", "after v0.5.x hardening") instead of
  fixed quarters that silently expire.
- Replace "Known Issues: none" with a link to the issue tracker, and rewrite the
  testing checklist so it covers only what automation cannot (LEDs, DS18B20,
  OTA, soak) with a pointer to the automated layers.
- Link `test/README.md` from `DOCUMENTATION_INDEX.md`.

## Acceptance criteria

- [ ] No status document states a memory figure that disagrees with a fresh build
- [ ] Roadmap phases are unique and the timeline is not self-contradictory
- [ ] Testing docs list what is automated, what needs hardware, and where bugs are tracked
- [ ] No session logs inside status documents
- [ ] README and `AquaControl_config.h` agree on timezone behaviour
