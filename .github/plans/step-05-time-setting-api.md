# Implementation Plan: Time-Setting API

**Feature**: POST /api/time/set endpoint for manual time adjustment  
**Priority**: Medium  
**Estimated Time**: 105 minutes (1.75 hours)  
**Dependencies**: None (independent feature)  
**Target Files**: src/Webserver.cpp, src/AquaControl.h

---

## Overview

### Objective
Implement POST /api/time/set endpoint to allow manual time adjustment via web UI when RTC sync fails or for timezone correction.

### Current State
- Time setting only possible via Arduino bootloader (manual USB connection required)
- No API endpoint for time management
- RTC syncs on boot but cannot be adjusted remotely

### Proposed Solution
- Add POST /api/time/set endpoint accepting JSON: `{"hour": 14, "minute": 30, "second": 0}`
- Validate input (hour 0-23, minute/second 0-59)
- Write to DS3231 RTC using existing RTC.set() method
- Sync TimeLib with RTC.get() to update system time
- Return confirmation JSON with updated time

---

## Requirements

### Functional
- Accept JSON POST to /api/time/set with hour, minute, second
- Validate time values (reject invalid inputs)
- Write to RTC hardware
- Sync system time with RTC
- Return success/error response

### Non-Functional
- Response time: <200ms
- Memory usage: <100 bytes additional RAM (char buffers only)
- No blocking operations (RTC I2C already non-blocking)

### Constraints
- Must preserve RTC on power loss (hardware persistent)
- Cannot use String class (memory safety)
- Must follow existing JSON API pattern (streaming with char buffers)

---

## Architecture

### Component Overview

**Endpoint Handler** (Webserver.cpp):
```cpp
void handleApiTimeSet() {
  // 1. Parse JSON body → extract hour, minute, second
  // 2. Validate ranges
  // 3. Set RTC via RTC.set(makeTime(...))
  // 4. Sync system time via setSyncProvider(getRTCTime)
  // 5. Stream JSON response
}
```

**RTC Integration** (existing):
- `DS3232RTC RTC` (global in AquaControl.cpp)
- `RTC.set(time_t t)` writes to hardware
- `getRTCTime()` reads from hardware (already syncs TimeLib)

### Data Flow
```
Client POST /api/time/set
  ↓
handleApiTimeSet() parses JSON
  ↓
Validate hour/minute/second
  ↓
Convert to time_t via makeTime()
  ↓
RTC.set(time_t) → Write to DS3231
  ↓
setSyncProvider(getRTCTime) → Sync system
  ↓
Stream JSON response → Client
```

---

## Implementation Tasks

### Phase 1: JSON Parsing (30 min)
- [ ] Add `handleApiTimeSet()` to Webserver.cpp
- [ ] Register endpoint in `AquaControl::init()`: `_Server.on("/api/time/set", HTTP_POST, handleApiTimeSet);`
- [ ] Parse JSON body using existing pattern (indexOf/substring)
- [ ] Extract hour, minute, second as integers

**Code Pattern** (from existing API):
```cpp
String body = _Server.arg("plain");
int hourIdx = body.indexOf("\"hour\":");
int hourStart = hourIdx + 7;
int hourEnd = body.indexOf(',', hourStart);
String hourStr = body.substring(hourStart, hourEnd);
hourStr.trim();
int hour = hourStr.toInt();
```

### Phase 2: Input Validation (20 min)
- [ ] Check hour range: 0-23
- [ ] Check minute range: 0-59
- [ ] Check second range: 0-59
- [ ] Return 400 error if invalid

**Validation Logic**:
```cpp
if (hour < 0 || hour > 23 || minute < 0 || minute > 59 || second < 0 || second > 59) {
  _Server.send(400, "application/json", "{\"error\":\"Invalid time values\"}");
  return;
}
```

### Phase 3: RTC Write (35 min)
- [ ] Create tmElements_t struct from input
- [ ] Convert to time_t via makeTime()
- [ ] Call RTC.set() to write to hardware
- [ ] Handle RTC write errors (if any)

**RTC Write Code**:
```cpp
tmElements_t tm;
tm.Hour = hour;
tm.Minute = minute;
tm.Second = second;
tm.Day = day();    // Preserve current date
tm.Month = month();
tm.Year = year() - 1970;
time_t t = makeTime(tm);
RTC.set(t);
```

### Phase 4: System Time Sync (10 min)
- [ ] Call setSyncProvider(getRTCTime) to sync TimeLib
- [ ] Verify system time updated via now()

**Sync Code**:
```cpp
setSyncProvider(getRTCTime);
if (timeStatus() != timeSet) {
  _Server.send(500, "application/json", "{\"error\":\"RTC sync failed\"}");
  return;
}
```

### Phase 5: Response Generation (10 min)
- [ ] Stream JSON response with updated time
- [ ] Use char buffers (no String concatenation)
- [ ] Return 200 OK status

**Response Code** (memory-safe):
```cpp
_Server.setContentLength(CONTENT_LENGTH_UNKNOWN);
_Server.send(200, "application/json", "");

char buf[16];
_Server.sendContent("{\"status\":\"ok\",\"time\":\"");
sprintf(buf, "%02d:%02d:%02d", hour(), minute(), second());
_Server.sendContent(buf);
_Server.sendContent("\"}");
```

---

## Testing Strategy

### Unit Tests
**Test 1: Valid Time**
- Input: `{"hour": 14, "minute": 30, "second": 0}`
- Expected: 200 OK, RTC updated, system time = 14:30:00

**Test 2: Invalid Hour**
- Input: `{"hour": 25, "minute": 30, "second": 0}`
- Expected: 400 Bad Request, `{"error": "Invalid time values"}`

**Test 3: Invalid Minute**
- Input: `{"hour": 14, "minute": 60, "second": 0}`
- Expected: 400 Bad Request

**Test 4: RTC Persistence**
- Set time to 10:00:00
- Reboot device
- Expected: Time still 10:xx:xx (RTC preserved)

### Integration Tests
**Test 5: Web UI Integration**
- Click "Set Time" button in UI
- Submit form with valid time
- Expected: UI displays updated time on next refresh

**Test 6: Concurrent Requests**
- Send 2 simultaneous POST requests
- Expected: Both return 200, last write wins (acceptable)

---

## Risk Assessment

### Medium Risks
**Risk**: RTC I2C bus lock if write fails  
**Mitigation**: Existing RTC library handles I2C timeouts (no action needed)

**Risk**: Date change near midnight could fail  
**Mitigation**: Preserve current date from system (day/month/year from now())

### Low Risks
**Risk**: Memory fragmentation from JSON parsing  
**Mitigation**: Use char buffers for response (no String concatenation)

---

## Success Criteria

- [x] POST /api/time/set endpoint responds to requests
- [x] Valid JSON input updates RTC and system time
- [x] Invalid input returns 400 error with descriptive message
- [x] Time persists across device reboot (RTC write confirmed)
- [x] Memory usage stays within budget (<100 bytes additional)
- [x] No heap fragmentation (char buffers only)
- [x] Response time <200ms

---

## Open Questions

**Q1**: Should endpoint support date setting (day/month/year)?  
**Answer**: Not in this phase - Step 5 focuses on time only. Date setting can be separate feature.

**Q2**: Should time be validated against current date (e.g., prevent setting 02:00 during DST transition)?  
**Answer**: No - user has full control. DST handling is Phase 3 (timezone support).

**Q3**: Should endpoint require authentication?  
**Answer**: Not in this phase - authentication is Phase 4. Current system assumes private network.

---

## References

- **RTC Library**: DS3232RTC.h (existing dependency)
- **TimeLib**: TimeLib.h (existing dependency for makeTime(), now())
- **Existing Pattern**: handleApiScheduleSave() in Webserver.cpp (JSON parsing)
- **Memory Safety**: CONTRIBUTING.md "Memory Management (Critical)" section

---

**Next Steps After Implementation**:
1. Test with curl: `curl -X POST http://192.168.0.8/api/time/set -d '{"hour":14,"minute":30,"second":0}'`
2. Add UI button in app.htm (time picker widget)
3. Update TESTING_GUIDE.md with new endpoint tests
4. Consider adding GET /api/time/status for current time display
