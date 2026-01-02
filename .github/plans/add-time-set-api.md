---
title: Add /api/time/set Endpoint for DS3231 RTC Time Configuration
version: 1.0
date_created: 2026-01-02
last_updated: 2026-01-02
---

# Implementation Plan: /api/time/set RTC Time-Setting Endpoint

## Overview
This plan adds a `/api/time/set` JSON endpoint that allows users to set the DS3231 real-time clock (RTC) via the web UI. Currently, RTC initialization syncs only on boot ([AquaControl.cpp#L490](../../src/AquaControl.cpp#L490)), forcing manual RTC adjustment with external tools. This endpoint will enable user-friendly time setting directly from the web interface, with validation and confirmation feedback.

**Impact**: Closes a critical UX gap, making the system self-service for time configuration and eliminating need for specialized hardware programmers.

---

## Requirements

### Functional Requirements
1. **POST `/api/time/set`** endpoint accepts JSON body: `{"hour": 14, "minute": 23, "second": 45}`
   - Validates time ranges: hour (0-23), minute (0-59), second (0-59)
   - Parses optional timezone/DST fields (future-proofing, not required for v1)
   - Returns confirmation with new time applied

2. **RTC Update** writes validated time to DS3231 hardware
   - Uses `RTC.set()` from DS3232RTC library (synchronized with TimeLib)
   - Updates system time (`setSyncProvider()` re-reads immediately)
   - Persists across power loss (RTC is hardware-backed)

3. **Success Response** includes formatted confirmation:
   ```json
   {
     "status": "ok",
     "message": "Time set successfully",
     "new_time": "14:23:45",
     "timestamp": 51825
   }
   ```

4. **Error Responses** handle invalid input gracefully:
   - Missing parameters: `{"error": "Missing hour field"}`
   - Out-of-range values: `{"error": "Hour must be 0-23"}`
   - RTC write failure: `{"error": "RTC update failed"}`

### Non-Functional Requirements
- **Memory**: Endpoint implementation <2KB stack/heap
- **Response time**: <100ms endpoint execution (RTC write ~10-20ms)
- **Platform**: ESP8266 only (requires `USE_RTC_DS3231` compiled)
- **Security**: No authentication (assumes private network per ARCHITECTURE.md)
- **Error handling**: Graceful fallback if RTC not available

---

## Architecture and Design

### High-Level Design

**New Method: `AquaControl::setRTCTime(uint8_t h, uint8_t m, uint8_t s)`**
```cpp
// In AquaControl.h (around line 200):
bool setRTCTime(uint8_t hour, uint8_t minute, uint8_t second);

// In AquaControl.cpp:
bool AquaControl::setRTCTime(uint8_t hour, uint8_t minute, uint8_t second) {
    #if defined(USE_RTC_DS3231)
    time_t newTime = ...build time from components...
    RTC.set(newTime);  // Write to hardware
    setSyncProvider(getRTCTime);  // Re-sync TimeLib
    return true;
    #else
    return false;  // RTC not compiled in
    #endif
}
```

**New Handler: `handleApiTimeSet()`** in [Webserver.cpp](../../src/Webserver.cpp) (add after ~line 725, after other `/api/` handlers)
```cpp
void handleApiTimeSet() {
    String body = _Server.arg("plain");
    // Parse JSON: {"hour": 14, "minute": 23, "second": 45}
    // Validate ranges
    // Call _aqc->setRTCTime()
    // Return formatted JSON response
}
```

**Route Registration** in [AquaControl.cpp#L650](../../src/AquaControl.cpp#L650):
```cpp
_Server.on("/api/time/set", HTTP_POST, handleApiTimeSet);
```

**Forward Declaration** in [AquaControl.h#L60](../../src/AquaControl.h#L60):
```cpp
void handleApiTimeSet();
```

### TimeLib Integration Pattern
- TimeLib uses `time_t` (32-bit Unix timestamp, seconds since 1970-01-01)
- DS3232RTC library provides `RTC.set(time_t)` to write to hardware
- `setSyncProvider(getRTCTime)` re-syncs system clock after hardware update
- `now()` will immediately reflect new time on next call

### Time Component Conversion
```cpp
// Convert hour/minute/second to Unix timestamp (simplified):
time_t newTime = makeTime(TimeElements {
    second: second,
    minute: minute,
    hour: hour,
    wday: weekday(now()),  // Keep current day-of-week
    mday: day(now()),       // Keep current date
    month: month(now()),
    year: year(now()) - 1970  // TimeLib expects year offset
});
```

### JSON Parsing Pattern
Follows existing pattern from [handleApiScheduleSave()](../../src/Webserver.cpp#L250):
```cpp
int hourIdx = body.indexOf("\"hour\":");
if (hourIdx == -1) {
    _Server.send(400, "application/json", "{\"error\":\"Missing hour field\"}");
    return;
}
// Extract, validate, use
```

### Design Decisions
- **Why build time from components?** User sends human-readable time (14:23:45), simpler than Unix timestamp
- **Why re-sync TimeLib?** Ensures `now()`, `hour()`, `minute()` etc. immediately reflect new RTC value
- **Why compile-gated?** System may use NTP (future) instead of RTC; feature gracefully disabled
- **Why no seconds in UI?** Schedule system works in minutes (hour:minute format); seconds added for completeness
- **Why no date/timezone?** Scope limitation; time-of-day only for now (aquarium schedules repeat daily)

---

## Implementation Tasks

### Phase 1: Core Time-Setting Method
**Estimated: 20 minutes**

- [ ] Add method declaration to [AquaControl.h](../../src/AquaControl.h) (after line 200)
  ```cpp
  #if defined(USE_RTC_DS3231)
  bool setRTCTime(uint8_t hour, uint8_t minute, uint8_t second);
  #endif
  ```

- [ ] Implement `AquaControl::setRTCTime()` in [AquaControl.cpp](../../src/AquaControl.cpp) (after `initTimeKeeper()` at ~line 520)
  - Build `time_t` from hour/minute/second components using TimeLib's `makeTime()`
  - Keep current date (year/month/day unchanged)
  - Call `RTC.set(newTime)` to write to DS3231 hardware
  - Call `setSyncProvider(getRTCTime)` to re-sync system time
  - Validate: hour ∈ [0,23], minute ∈ [0,59], second ∈ [0,59]
  - Log result to Serial
  - Return `bool` (success/failure)

**Test checkpoint**: Compile without errors (`pio run -e esp8266`)

### Phase 2: JSON API Handler
**Estimated: 30 minutes**

- [ ] Add forward declaration to [AquaControl.h](../../src/AquaControl.h#L60) (in webserver handlers section)
  ```cpp
  void handleApiTimeSet();
  ```

- [ ] Implement `handleApiTimeSet()` in [Webserver.cpp](../../src/Webserver.cpp) (after `handleApiStatus()` at ~line 725)
  - Read request body with `String body = _Server.arg("plain");`
  - Parse JSON for three fields: `hour`, `minute`, `second`
  - Use `indexOf()` pattern from [handleApiTargetAdd()](../../src/Webserver.cpp#L415) as reference
  - Validate each field exists and in valid range
  - Extract integers using `.toInt()` and `substring()`
  - Call `_aqc->setRTCTime(hour, minute, second)`
  - If validation fails: send `400` status with error JSON
  - If success: send `200` status with confirmation JSON including new time formatted as "HH:MM:SS"
  - Use `sprintf()` with buffers for formatting (no String concatenation per memory guidelines)

**Key validation checks**:
```cpp
if (hour < 0 || hour > 23) { /* error */ }
if (minute < 0 || minute > 59) { /* error */ }
if (second < 0 || second > 59) { /* error */ }
```

**Success response format**:
```cpp
char buf[128];
sprintf(buf, "{\"status\":\"ok\",\"message\":\"Time set successfully\",\"new_time\":\"%02d:%02d:%02d\",\"timestamp\":%lu}",
        hour, minute, second, (unsigned long)now());
_Server.send(200, "application/json", buf);
```

**Test checkpoint**: Verify endpoint is callable, returns correct JSON format

### Phase 3: Route Registration
**Estimated: 10 minutes**

- [ ] Register endpoint in [AquaControl.cpp](../../src/AquaControl.cpp#L650) (in `init()` method, near other API routes)
  ```cpp
  _Server.on("/api/time/set", HTTP_POST, handleApiTimeSet);
  ```
  - Add after existing `/api/` routes (around line 653)
  - Ensure `HTTP_POST` method (not GET)

- [ ] Verify web server initialization completes without errors
  - Check serial output during boot for "Initializing Webserver... Done."

**Test checkpoint**: HTTP POST requests reach handler (check Serial debug output)

### Phase 4: Integration Testing
**Estimated: 30 minutes**

- [ ] Compile and upload firmware
  ```
  pio run -e esp8266 --target upload
  pio device monitor
  ```

- [ ] Test valid time update via curl or Postman:
  ```bash
  curl -X POST http://192.168.0.1/api/time/set \
    -H "Content-Type: application/json" \
    -d '{"hour": 14, "minute": 23, "second": 45}'
  ```
  - Verify response: `{"status":"ok","message":"Time set successfully","new_time":"14:23:45",...}`
  - Check Serial output: confirmation logged
  - Verify `/api/status` endpoint now reports updated time

- [ ] Test validation errors:
  ```bash
  # Missing field
  curl -X POST http://192.168.0.1/api/time/set -d '{"hour": 14, "minute": 23}'
  # Expected: {"error":"Missing second field"}
  
  # Invalid hour (out of range)
  curl -X POST http://192.168.0.1/api/time/set -d '{"hour": 25, "minute": 23, "second": 45}'
  # Expected: {"error":"Hour must be 0-23"}
  
  # Invalid minute
  curl -X POST http://192.168.0.1/api/time/set -d '{"hour": 14, "minute": 75, "second": 45}'
  # Expected: {"error":"Minute must be 0-59"}
  
  # Invalid second
  curl -X POST http://192.168.0.1/api/time/set -d '{"hour": 14, "minute": 23, "second": 95}'
  # Expected: {"error":"Second must be 0-59"}
  ```

- [ ] Test edge cases:
  - Midnight: `{"hour": 0, "minute": 0, "second": 0}`
  - End of day: `{"hour": 23, "minute": 59, "second": 59}`
  - Mid-day: `{"hour": 12, "minute": 30, "second": 15}`

- [ ] Verify schedule execution not disrupted:
  - Set time to within active schedule range
  - Observe LEDs respond to current time interpolation
  - Set time forward 30 minutes
  - Verify LEDs smoothly transition to new schedule targets

- [ ] Test RTC persistence:
  - Set time to `14:23:45`
  - Power off ESP8266 for 5 seconds
  - Power on, wait for boot
  - Verify `/api/status` shows time approximately `14:23:45 + elapsed_boot_time`

**Test checkpoint**: All validation tests pass, time persists across power loss

### Phase 5: Documentation & Cleanup
**Estimated: 15 minutes**

- [ ] Update [QUICK_REFERENCE.md](../../QUICK_REFERENCE.md) (or equivalent API docs):
  - Add `/api/time/set` endpoint description
  - Include JSON request/response examples
  - Document validation rules

- [ ] Add code comments in [Webserver.cpp](../../src/Webserver.cpp) (handleApiTimeSet function):
  - Explain parsing flow
  - Reference TimeLib documentation
  - Note RTC hardware requirements

- [ ] Review [AquaControl.cpp](../../src/AquaControl.cpp#L490-L510) for any RTC-related comments
  - Confirm `initTimeKeeper()` documentation is accurate
  - Add cross-reference to new `setRTCTime()` method

- [ ] Build final time to ensure no compiler warnings:
  ```
  pio run -e esp8266 --target clean
  pio run -e esp8266
  ```

**Test checkpoint**: No compiler warnings, documentation complete

---

## Testing Strategy

### Unit Tests (Manual, no test framework currently)
1. **Time component validation**
   - Test boundary values: 0, 23, 59 (valid); -1, 24, 60 (invalid)
   - Verify error messages are distinct per field

2. **TimeLib integration**
   - Verify `makeTime()` correctly converts hour/minute/second to `time_t`
   - Verify `now()` reflects new time immediately after `setRTCTime()`

3. **JSON parsing**
   - Malformed JSON: `{"hour": "abc"}` (non-numeric)
   - Extra fields: `{"hour": 14, "minute": 23, "second": 45, "junk": "ignored"}`
   - Missing fields in various combinations

### Integration Tests
1. **End-to-end workflow**
   - Set time via `/api/time/set`
   - Query time via `/api/status`
   - Verify `/api/schedule/*` endpoints work with new time

2. **Schedule interaction**
   - Set time within schedule range
   - Observe schedule targets execute
   - Set time to future/past values
   - Verify smooth transitions (interpolation still works)

3. **Edge cases**
   - Set time at day boundary (23:59:59 → 00:00:00)
   - Set time during active schedule transition
   - Set time to same value twice (idempotent)
   - Rapid successive calls (should not corrupt state)

### Manual Tests (Hardware on ESP8266)
1. **Serial monitor validation**
   - Boot ESP8266
   - Initial time displays (e.g., "14:23:45")
   - Call `/api/time/set` with new time
   - Verify "Time set successfully" logged
   - Reboot, verify new time persists

2. **Web UI integration** (when UI adds time-picker)
   - Visual time display updates immediately
   - LED schedule responds to new time
   - No flicker or interruption in LED transitions

3. **RTC Hardware confirmation**
   - Use external RTC reader (optional)
   - Confirm DS3231 internal register updated
   - Verify battery-backed time persists across power cycle

### Edge Case Testing
- **Timezone handling** (future-proofing): Currently time is always UTC; document this
- **DST transitions** (future-proofing): Not supported in v1; store in comments
- **Invalid hardware state** (RTC not responding): `setRTCTime()` returns false, handler sends error
- **System time drift**: Not addressed (NTP sync phase will handle)

---

## Success Criteria

✅ **Functional**
- [ ] `/api/time/set` POST endpoint implemented and accessible via HTTP
- [ ] Accepts JSON with `hour`, `minute`, `second` fields
- [ ] Validates all inputs; rejects out-of-range values
- [ ] Writes valid time to DS3231 RTC hardware
- [ ] Returns JSON confirmation with new time formatted as "HH:MM:SS"
- [ ] Returns appropriate error JSON for validation failures
- [ ] Updated time persists across power loss

✅ **Non-Functional**
- [ ] No compiler errors or warnings (`pio run -e esp8266` clean)
- [ ] Endpoint responds in <100ms (measured via curl timing)
- [ ] Code uses char buffers for JSON formatting (no String concatenation)
- [ ] Memory footprint <2KB additional heap/stack
- [ ] Function only compiles if `USE_RTC_DS3231` is defined

✅ **Code Quality**
- [ ] Follows existing naming conventions (camelCase, `handle*` prefix)
- [ ] Uses `Serial.print(F("..."))` for debugging (flash string macro)
- [ ] Comments explain TimeLib/RTC integration
- [ ] References to related code via file paths and line numbers

✅ **Testing**
- [ ] All validation tests pass (in-range, out-of-range, missing fields)
- [ ] Integration test: time change → schedule execution verification
- [ ] Edge case tests: midnight, end-of-day, rapid calls
- [ ] Power-loss persistence test (RTC survives power cycle)

✅ **Documentation**
- [ ] API documentation updated (QUICK_REFERENCE.md or equivalent)
- [ ] Code comments added to `handleApiTimeSet()` and `setRTCTime()`
- [ ] Notes on TimeLib usage and RTC requirements

✅ **Handoff Readiness**
- [ ] Ready for code review (no blocking issues)
- [ ] Can be merged to main branch without breaking existing functionality
- [ ] Passes all integration tests on ESP8266 hardware

---

## Open Questions

1. **Date handling**: Should `/api/time/set` also accept `month`, `day`, `year` fields?
   - **Recommendation**: Not in v1. Aquarium schedules repeat daily; date rarely changes. Add if future feature requires it.
   - **Future**: Add optional date fields, document as "advanced" mode.

2. **Timezone/DST support**: Should endpoint understand timezone abbreviations (e.g., `"timezone": "CET"`)?
   - **Recommendation**: Not in v1. System currently time-agnostic (all times UTC). NTP sync phase will address regional time.
   - **Future**: Add `timezone` field to support offset calculation.

3. **Response format for `timestamp` field**: Should this be Unix timestamp or seconds-of-day?
   - **Recommendation**: Unix timestamp (`now()`) for consistency with TimeLib. Web UI can format as human-readable.

4. **Error cases**: What happens if RTC hardware is not responding during `RTC.set()`?
   - **Recommendation**: `setRTCTime()` returns false; handler sends `{"error": "RTC update failed"}`. User retries.

5. **Access control**: Should this endpoint require authentication (future)?
   - **Recommendation**: Not in v1 (per ARCHITECTURE.md, system assumes private network). Add authentication framework later if needed.

---

## Dependencies & Blockers

**Dependencies**:
- Existing: DS3232RTC library (already included in platformio.ini)
- Existing: TimeLib.h (already included)
- Existing: ESP8266WebServer (already initialized in `init()`)

**Blockers**: None. All required libraries and infrastructure already present.

**Unblocks**:
- Web UI time-picker component (calls `/api/time/set` endpoint)
- NTP time-sync API (can be alternative to manual setting)
- Timezone/DST support (builds on RTC write capability)

---

## Implementation Notes

- **TimeLib Documentation**: The `makeTime()` function constructs a `time_t` from `TimeElements` struct:
  ```cpp
  struct TimeElements {
    uint8_t second;
    uint8_t minute;
    uint8_t hour;
    uint8_t wday;    // 1 (Sunday) to 7 (Saturday)
    uint8_t mday;    // 1 to 31 (day of month)
    uint8_t month;   // 1 to 12
    int8_t year;     // Years since 1970
  };
  ```

- **RTC Write Cycle**: DS3231 I2C write (~20ms), then TimeLib re-syncs (~5ms). Total <50ms latency.

- **Daily Schedule Wrapping**: Existing `elapsedSecsToday()` function converts any `time_t` to seconds-within-day (0-86399). Setting time anywhere within day correctly triggers interpolation.

- **Serial Debugging**: Enable by calling `Serial.println()` with RTC operations. Check monitor output during testing:
  ```
  RTC.set() writing to DS3231...
  setSyncProvider() syncing TimeLib...
  New time: 14:23:45
  ```

- **Future Enhancement**: When web UI gains time-picker component, it will POST to this endpoint and display the response message.

---

## Related Code References

- [AquaControl.h](../../src/AquaControl.h): Main header; TimeLib includes at line 48
- [AquaControl.cpp#L490](../../src/AquaControl.cpp#L490): `initTimeKeeper()` - RTC boot sequence
- [AquaControl.cpp#L610](../../src/AquaControl.cpp#L610): `now()` calls in `proceedCycle()` - shows where time is used
- [Webserver.cpp#L150](../../src/Webserver.cpp#L150): `handleApiStatus()` - existing time response pattern
- [Webserver.cpp#L250](../../src/Webserver.cpp#L250): `handleApiScheduleSave()` - JSON parsing reference
- [Webserver.cpp#L415](../../src/Webserver.cpp#L415): `handleApiTargetAdd()` - validation error handling reference
- [ARCHITECTURE.md#L109](../../ARCHITECTURE.md#L109): "Time & RTC Handling" section
- [AquaControl_config.h](../../src/AquaControl_config.h): Check `USE_RTC_DS3231` flag

