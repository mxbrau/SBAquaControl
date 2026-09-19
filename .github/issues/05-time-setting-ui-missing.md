---
title: Time-setting API exists but the web UI cannot set the clock
labels: ui, enhancement
---

## Symptom

The firmware implements `POST /api/time/set` (registered in
`src/AquaControl.cpp:813`, handler `handleApiTimeSet()` in
`src/Webserver.cpp:1862-1948`), which writes the DS3231 RTC and marks the sync
source as `api`. **No UI element calls it.** The endpoint map in
`extras/SDCard/js/config.js` lists every other route the app uses but has no
`timeSet` entry, and `extras/SDCard/js/app.js` never posts to it.

Consequence: `docs/status/FIRMWARE_STATUS.md` and `README.md` both advertise
"Time-setting API (`/api/time/set`)" as a feature, but the only way to use it is
`curl`:

```bash
curl -X POST http://192.168.103.8/api/time/set \
  -H "Content-Type: application/json" -d '{"hour":14,"minute":30,"second":0}'
```

`docs/status/TESTING_GUIDE.md` documents exactly this curl as the workaround.

## Why it matters

The RTC drifts and there is no NTP fallback on a network without internet
(`USE_NTP` exists, but a failed NTP sync currently leaves the user with no way to
correct the time short of a curl command). `GET /api/status` already returns
`time_source` / `time_valid` / `needs_time_sync` / `rtc_present`, so the UI could
show *that* the clock is wrong, yet offers no way to fix it.

History: the UI half was implemented on `copilot/implement-time-settings-api` and
then deliberately reverted ("Revert UI changes: remove time-setting modal and
keep only API"), so the API shipped without its UI.

## Proposed approach

- Add the endpoint to `CONFIG.api` in `extras/SDCard/js/config.js` (it is the
  single place the UI's routes are declared).
- Add a small "set clock" control near the existing time display: prefill from
  the browser clock, allow hour/minute/second (the API takes no date), POST, then
  refresh status.
- Show the sync state from `/api/status` next to it (`time_source`, `time_valid`,
  `needs_time_sync`) so a silent RTC problem is visible.

## Acceptance criteria

- [ ] The UI can set the device clock without curl
- [ ] Wrong input (hour > 23, minute > 59) surfaces the API's 400 rather than failing silently
- [ ] A contract check for `POST /api/time/set` stays green in `uv run python test/run_checks.py`
      (the mock already implements it)
- [ ] `docs/status/FIRMWARE_STATUS.md` and the README describe the UI, not just the endpoint
