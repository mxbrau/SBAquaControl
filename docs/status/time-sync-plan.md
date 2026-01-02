---
title: Hybrid Time Sync (RTC + Browser Fallback)
version: 1.0
date_created: 2026-01-03
last_updated: 2026-01-03
---

# Implementation Plan: Hybrid Time Sync (RTC + Browser Fallback)

## Overview
Finalize automatic time synchronization: keep RTC as primary source, add optional NTP (compile-time flag) ahead of RTC when enabled, and rely on the already merged browser `/api/time/set` endpoint as a fallback when the device clock needs manual alignment. This removes the need for SD-based overrides while keeping the firmware self-contained.

---

## Requirements

### Functional Requirements
- On boot, attempt time sync without user interaction (NTP when `USE_NTP` is compiled in, otherwise RTC). If RTC sync fails, continue running but expose status so UI can prompt a browser-driven `/api/time/set` call.
- `/api/time/set` must set RTC time (if present) and update system time immediately; return JSON status.
- Status endpoint should expose current time, last sync source, and whether RTC is available so UI can decide when to prompt the user.
- No SD-configurable NTP override is required; firmware defaults are sufficient.

### Non-Functional Requirements
- Memory: keep added RAM usage negligible (<2 KB); avoid `String` concatenation, use char buffers/streaming.
- Non-blocking: no new long delays in the main loop; any network retries must be bounded.
- Footprint: reuse existing includes/flags; keep OTA/webserver behavior unchanged.

---

## Architecture and Design

### High-Level Design
- **Time sync flow**: `initTimeKeeper()` first tries NTP (if `USE_NTP`), then RTC; on failure, system runs unsynced until UI sets time via `/api/time/set`.
- **State tracking**: add a lightweight enum + timestamp for `lastTimeSyncSource` (e.g., `Ntp`, `Rtc`, `Api`) stored on `AquaControl`; update on each successful sync.
- **Web API**: `/api/time/set` already present in [src/Webserver.cpp#L1322-L1385](src/Webserver.cpp#L1322-L1385); extend to flag `lastTimeSyncSource = Api` after RTC write.
- **Status payload**: extend `handleApiStatus()` to emit `time_source`, `rtc_present`, and `time_valid` so UI can prompt manual sync when needed.

### Key Algorithms
- RTC sync loop (already present) in [src/AquaControl.cpp#L430-L485](src/AquaControl.cpp#L430-L485).
- JSON streaming pattern in `handleApiStatus()` (use char buffers) in [src/Webserver.cpp#L190-L245](src/Webserver.cpp#L190-L245).

### Design Decisions
- Prefer RTC and optional NTP to minimize manual steps; browser `/api/time/set` is fallback for first boot or RTC drift.
- No SD-configured NTP override; compile-time defaults are acceptable per decision.
- Stream JSON to avoid RAM spikes on ESP8266; avoid new `String` concatenations.

---

## Implementation Tasks

### Phase 1: Time Source State
- [ ] Add `enum class TimeSyncSource { Unknown, Ntp, Rtc, Api };` and `time_t _LastTimeSync = 0; TimeSyncSource _LastTimeSyncSource = TimeSyncSource::Unknown;` to `AquaControl` in [src/AquaControl.h#L120-L190](src/AquaControl.h#L120-L190); initialize in constructor.

### Phase 2: Boot Sync Flow
- [ ] Replace `#error "Not yet implemented"` with NTP sync routine in `initTimeKeeper()` guarded by `USE_NTP`, falling back to RTC on failure in [src/AquaControl.cpp#L430-L485](src/AquaControl.cpp#L430-L485).
- [ ] After a successful RTC or NTP sync, set `_LastTimeSync` and `_LastTimeSyncSource` accordingly in [src/AquaControl.cpp#L430-L485](src/AquaControl.cpp#L430-L485).

### Phase 3: Browser Fallback
- [ ] In `/api/time/set`, set `_LastTimeSync` and `_LastTimeSyncSource = TimeSyncSource::Api` after successful RTC write in [src/Webserver.cpp#L1322-L1385](src/Webserver.cpp#L1322-L1385).

### Phase 4: Status Reporting
- [ ] Extend `/api/status` response with `"time_source"`, `"rtc_present"`, and `"time_valid"` flags using streaming buffers in [src/Webserver.cpp#L190-L245](src/Webserver.cpp#L190-L245).
- [ ] Optionally include `"last_sync_ts"` (seconds since epoch) for UI diagnostics.

### Phase 5: Tests
- [ ] Build check: `pio run -e esp8266`.
- [ ] Manual: cold boot with RTC present → status shows `time_source: rtc` and valid time.
- [ ] Manual: force RTC failure (disconnect) → status shows `time_valid: false`; call `/api/time/set` → time valid, source `api`.
- [ ] If `USE_NTP` enabled: boot on WiFi with internet → status `time_source: ntp`; disconnect internet and reboot → falls back to RTC.

---

## Testing Strategy
- **Manual**: Verify status payload changes with different sync paths; set time via UI and confirm RTC retains time after reboot.
- **Build**: `pio run -e esp8266` for regressions.
- **(Optional) Integration**: enable `USE_NTP` and observe first-sync success/fallback behaviors on device logs.

---

## Open Questions
- None. NTP server override via SD/config is out of scope per decision; firmware defaults suffice.
