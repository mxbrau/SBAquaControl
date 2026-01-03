# Testing the Hybrid Time Sync Implementation

## Overview
This document provides test cases for the hybrid time sync feature implemented with TDD principles. The feature adds:
- NTP time sync (when `USE_NTP` is enabled)
- RTC fallback sync
- Browser API fallback via `/api/time/set`
- Time sync status reporting via `/api/status`

## Prerequisites
- ESP8266 device with SBAquaControl firmware flashed
- DS3231 RTC module connected (optional but recommended)
- Device connected to WiFi network
- Internet access (for NTP tests)
- curl or Postman for API testing

---

## Test Cases

### Test 1: RTC Sync on Boot (Default Configuration)
**Description**: Verify that device syncs time from RTC on boot when `USE_NTP` is not enabled.

**Configuration**:
- `USE_RTC_DS3231` defined
- `USE_NTP` not defined

**Steps**:
1. Flash firmware to device
2. Reboot device
3. Monitor serial output at 19200 baud
4. Call `/api/status`

**Expected Serial Output**:
```
Initializing RTC DS3231... Done.
```

**Expected API Response**:
```json
{
  "time_source": "rtc",
  "rtc_present": true,
  "time_valid": true,
  "last_sync_ts": 1735862400,
  "current_time": "14:30:45"
}
```

**Validation**:
- [ ] Serial shows successful RTC initialization
- [ ] `time_source` is `"rtc"`
- [ ] `rtc_present` is `true`
- [ ] `time_valid` is `true`
- [ ] `last_sync_ts` is a valid Unix timestamp
- [ ] Current time matches RTC time

---

### Test 2: NTP Sync on Boot (USE_NTP Enabled)
**Description**: Verify that device syncs time from NTP server when `USE_NTP` is enabled.

**Configuration**:
- `USE_RTC_DS3231` defined
- `USE_NTP` defined
- WiFi connected with internet access

**Steps**:
1. Enable `USE_NTP` in `src/AquaControl_config.h`:
   ```cpp
   #define USE_NTP
   ```
2. Flash firmware to device
3. Reboot device
4. Monitor serial output
5. Call `/api/status`

**Expected Serial Output**:
```
Attempting NTP time sync...
Sending NTP request to 192.168.103.1
NTP response received
 Success!
NTP time: 14:30:45
Updating RTC with NTP time... Done.
```

**Expected API Response**:
```json
{
  "time_source": "ntp",
  "rtc_present": true,
  "time_valid": true,
  "last_sync_ts": 1735862445
}
```

**Validation**:
- [ ] Serial shows NTP sync attempt
- [ ] NTP response received
- [ ] RTC updated with NTP time
- [ ] `time_source` is `"ntp"`
- [ ] `time_valid` is `true`
- [ ] Time is accurate (within 1 second of actual time)

---

### Test 3: NTP Failure Falls Back to RTC
**Description**: Verify that device falls back to RTC when NTP sync fails.

**Configuration**:
- `USE_RTC_DS3231` defined
- `USE_NTP` defined
- WiFi connected but NO internet access (or invalid NTP server)

**Steps**:
1. Enable `USE_NTP` in configuration
2. Disconnect internet or modify NTP server to invalid address
3. Flash and reboot device
4. Monitor serial output
5. Call `/api/status`

**Expected Serial Output**:
```
Attempting NTP time sync...
Sending NTP request to 192.168.103.1
NTP request timeout
 Failed.
Initializing RTC DS3231... Done.
```

**Expected API Response**:
```json
{
  "time_source": "rtc",
  "rtc_present": true,
  "time_valid": true
}
```

**Validation**:
- [ ] Serial shows NTP timeout
- [ ] Serial shows fallback to RTC
- [ ] `time_source` is `"rtc"` (fallback)
- [ ] `time_valid` is `true`
- [ ] Device continues operating normally

---

### Test 4: No Time Source Available
**Description**: Verify status when both NTP and RTC fail.

**Configuration**:
- `USE_RTC_DS3231` not defined (or RTC disconnected)
- `USE_NTP` not defined

**Steps**:
1. Disconnect RTC module
2. Flash firmware without `USE_NTP`
3. Reboot device
4. Monitor serial output
5. Call `/api/status`

**Expected Serial Output**:
```
WARNING: No time source available. Time sync via /api/time/set required.
```

**Expected API Response**:
```json
{
  "time_source": "unknown",
  "rtc_present": false,
  "time_valid": false,
  "last_sync_ts": 0
}
```

**Validation**:
- [ ] Serial shows warning message
- [ ] `time_source` is `"unknown"`
- [ ] `time_valid` is `false`
- [ ] UI should prompt user to set time manually

---

### Test 5: Manual Time Set via API
**Description**: Verify that `/api/time/set` updates sync source to `"api"`.

**Steps**:
1. Boot device with any configuration
2. Call `/api/time/set` to set time:
   ```bash
   curl -X POST http://192.168.0.8/api/time/set \
     -H "Content-Type: application/json" \
     -d '{"hour": 16, "minute": 45, "second": 30}'
   ```
3. Call `/api/status` immediately after

**Expected API Response** (from `/api/time/set`):
```json
{
  "status": "ok",
  "time": "16:45:30"
}
```

**Expected API Response** (from `/api/status`):
```json
{
  "time_source": "api",
  "rtc_present": true,
  "time_valid": true,
  "current_time": "16:45:31"
}
```

**Expected Serial Output**:
```
✅ Time set to: 16:45:30
Time sync source: API
```

**Validation**:
- [ ] `/api/time/set` returns success
- [ ] `time_source` changes to `"api"`
- [ ] `time_valid` is `true`
- [ ] `last_sync_ts` updated to current time
- [ ] Serial shows sync source change

---

### Test 6: Time Sync Persistence Across Reboot
**Description**: Verify that RTC-based time persists across reboot.

**Steps**:
1. Set time via API:
   ```bash
   curl -X POST http://192.168.0.8/api/time/set \
     -H "Content-Type: application/json" \
     -d '{"hour": 10, "minute": 0, "second": 0}'
   ```
2. Verify `/api/status` shows `time_source: "api"`
3. Wait 30 seconds
4. Reboot device
5. After boot, call `/api/status` again

**Expected Result**:
- After reboot, `time_source` should be `"rtc"`
- Time should be approximately 10:00:30 (or slightly more)
- Time should NOT reset to default or compile time

**Validation**:
- [ ] Time persists across reboot
- [ ] `time_source` changes from `"api"` to `"rtc"` after reboot
- [ ] Time continues from where it was set

---

### Test 7: NTP Updates RTC
**Description**: Verify that NTP sync updates RTC hardware.

**Configuration**:
- `USE_RTC_DS3231` defined
- `USE_NTP` defined

**Steps**:
1. Boot device with internet access
2. Verify NTP sync succeeds
3. Disconnect internet
4. Reboot device
5. Check time source

**Expected Result**:
- First boot: `time_source: "ntp"`
- Second boot (no internet): `time_source: "rtc"`
- Time should be accurate on second boot (RTC was updated by NTP)

**Validation**:
- [ ] NTP updates RTC hardware
- [ ] RTC retains NTP-synced time after reboot
- [ ] Device can operate without internet after initial NTP sync

---

### Test 8: Status Fields Format Validation
**Description**: Verify that all new status fields have correct format.

**Steps**:
1. Call `/api/status`
2. Parse JSON response
3. Validate field types

**Expected Fields**:
```json
{
  "time_source": "string (ntp|rtc|api|unknown)",
  "rtc_present": "boolean",
  "time_valid": "boolean",
  "last_sync_ts": "number (Unix timestamp)"
}
```

**Validation**:
- [ ] `time_source` is a string with valid enum value
- [ ] `rtc_present` is a boolean
- [ ] `time_valid` is a boolean
- [ ] `last_sync_ts` is a number >= 0
- [ ] `needs_time_sync` is a boolean

---

### Test 9: Browser Auto-Sync When NTP Fails
**Description**: Verify that browser automatically syncs time when NTP fails.

**Configuration**:
- `USE_NTP` defined
- `USE_RTC_DS3231` defined (optional)
- Router NTP disabled or invalid NTP server

**Steps**:
1. Ensure router NTP is disabled or NTP server is unreachable
2. Flash and boot device
3. Monitor serial output
4. Call `/api/status` and verify `needs_time_sync: true`
5. Implement browser auto-sync JavaScript (see `docs/status/BROWSER_AUTO_SYNC.md`)
6. Open web UI in browser
7. Wait 10 seconds
8. Call `/api/status` again

**Expected Serial Output**:
```
Attempting NTP time sync...
Sending NTP request to 192.168.103.1
NTP request timeout
 Failed.
Initializing RTC DS3231... Done.
```
(Then after browser sync):
```
Time set request body: {"hour":14,"minute":30,"second":45}
✅ Time set to: 14:30:45
Time sync source: API
```

**Expected API Response (before browser sync)**:
```json
{
  "time_source": "rtc",
  "rtc_present": true,
  "time_valid": true,
  "needs_time_sync": true,
  "last_sync_ts": 1735862400
}
```

**Expected API Response (after browser sync)**:
```json
{
  "time_source": "api",
  "rtc_present": true,
  "time_valid": true,
  "needs_time_sync": false,
  "last_sync_ts": 1735862445
}
```

**Validation**:
- [ ] NTP sync fails and sets `needs_time_sync: true`
- [ ] Browser detects the flag
- [ ] Browser automatically POSTs time to `/api/time/set`
- [ ] `needs_time_sync` changes to `false` after sync
- [ ] `time_source` changes to `"api"`
- [ ] No user intervention required

---

## Manual Testing Checklist

### Basic Functionality
- [ ] Test 1: RTC Sync on Boot
- [ ] Test 2: NTP Sync on Boot
- [ ] Test 3: NTP Failure Falls Back to RTC
- [ ] Test 4: No Time Source Available
- [ ] Test 5: Manual Time Set via API
- [ ] Test 6: Time Sync Persistence Across Reboot
- [ ] Test 7: NTP Updates RTC
- [ ] Test 8: Status Fields Format Validation
- [ ] Test 9: Browser Auto-Sync When NTP Fails

### Edge Cases
- [ ] WiFi disconnect during NTP sync
- [ ] RTC battery dead (reset to default)
- [ ] Multiple rapid `/api/time/set` calls
- [ ] Time set near midnight (date rollover)

### Memory Safety
- [ ] Device runs for 1 hour without crashes
- [ ] Monitor serial for heap warnings
- [ ] Verify no memory leaks (uptime increases continuously)

---

## Build Verification

### ESP8266 Build
```bash
pio run -e esp8266
```
**Expected**: Clean build with no errors

### ESP8266 OTA Build
```bash
pio run -e esp8266_ota
```
**Expected**: Clean build with no errors

---

## Serial Monitor Commands

Connect at 19200 baud:
```bash
pio device monitor
```

**Key Serial Messages to Observe**:
- `Attempting NTP time sync...` (if `USE_NTP` enabled)
- `NTP response received` (successful NTP)
- `NTP request timeout` (NTP failed)
- `Initializing RTC DS3231...` (RTC sync)
- `✅ Time set to: HH:MM:SS` (API time set)
- `Time sync source: API` (after API call)
- `WARNING: No time source available` (no sync source)

---

## Success Criteria

### Functional Requirements
- ✅ NTP sync works when `USE_NTP` is enabled and internet available
- ✅ RTC fallback works when NTP fails
- ✅ API fallback works for manual time setting
- ✅ Status endpoint reports correct sync source
- ✅ Time persists across reboots (via RTC)

### Non-Functional Requirements
- ✅ No memory leaks (char buffers only, no String concatenation)
- ✅ Boot time not significantly increased
- ✅ NTP timeout bounded to 2 seconds max
- ✅ All serial messages use `F()` macro for flash storage

---

## Troubleshooting

### NTP Always Times Out
- Check WiFi connection: `curl http://192.168.0.8/api/status` should show `"wifi_connected": true`
- Verify router NTP is enabled: ping `192.168.103.1` from your network
- Check firewall: UDP port 123 must be allowed

### RTC Sync Fails
- Verify RTC module connected to I2C pins (SDA/SCL)
- Check RTC battery (CR2032)
- Use I2C scanner to verify RTC address (0x68)

### Time Source Shows "unknown"
- Both NTP and RTC failed
- Use `/api/time/set` to manually set time
- Check serial output for error messages

---

## Notes

- Replace `192.168.0.8` with your device's actual IP
- All times are in 24-hour format
- NTP uses router at `192.168.103.1` by default (local network NTP)
- Time sync happens once at boot, not continuously
- RTC hardware persists time across power loss
- Memory usage: ~200 bytes additional for state tracking and NTP buffers
