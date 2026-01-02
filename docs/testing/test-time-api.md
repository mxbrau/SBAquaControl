# Testing the Time-Setting API

## Overview
This document provides test cases for the POST `/api/time/set` endpoint implemented in Step 5.

## Prerequisites
- ESP8266 device with SBAquaControl firmware flashed
- DS3231 RTC module connected
- Device connected to network (WiFi)
- curl or Postman for API testing

## Test Cases

### Test 1: Valid Time - Mid-day
**Description**: Set time to 14:30:00

**Request**:
```bash
curl -X POST http://192.168.0.8/api/time/set \
  -H "Content-Type: application/json" \
  -d '{"hour": 14, "minute": 30, "second": 0}'
```

**Expected Response**:
```json
{"status":"ok","time":"14:30:00"}
```

**HTTP Status**: 200 OK

**Verification**:
- Serial output shows: `✅ Time set to: 14:30:00`
- GET `/api/status` should show `"time":"14:30:XX"` (where XX is seconds elapsed)

---

### Test 2: Valid Time - Midnight
**Description**: Set time to 00:00:00

**Request**:
```bash
curl -X POST http://192.168.0.8/api/time/set \
  -H "Content-Type: application/json" \
  -d '{"hour": 0, "minute": 0, "second": 0}'
```

**Expected Response**:
```json
{"status":"ok","time":"00:00:00"}
```

**HTTP Status**: 200 OK

---

### Test 3: Valid Time - End of Day
**Description**: Set time to 23:59:59

**Request**:
```bash
curl -X POST http://192.168.0.8/api/time/set \
  -H "Content-Type: application/json" \
  -d '{"hour": 23, "minute": 59, "second": 59}'
```

**Expected Response**:
```json
{"status":"ok","time":"23:59:59"}
```

**HTTP Status**: 200 OK

---

### Test 4: Invalid Hour (Too High)
**Description**: Attempt to set hour to 25

**Request**:
```bash
curl -X POST http://192.168.0.8/api/time/set \
  -H "Content-Type: application/json" \
  -d '{"hour": 25, "minute": 30, "second": 0}'
```

**Expected Response**:
```json
{"error":"Invalid time values (hour: 0-23, minute: 0-59, second: 0-59)"}
```

**HTTP Status**: 400 Bad Request

---

### Test 5: Invalid Minute (Too High)
**Description**: Attempt to set minute to 60

**Request**:
```bash
curl -X POST http://192.168.0.8/api/time/set \
  -H "Content-Type: application/json" \
  -d '{"hour": 14, "minute": 60, "second": 0}'
```

**Expected Response**:
```json
{"error":"Invalid time values (hour: 0-23, minute: 0-59, second: 0-59)"}
```

**HTTP Status**: 400 Bad Request

---

### Test 6: Invalid Second (Too High)
**Description**: Attempt to set second to 60

**Request**:
```bash
curl -X POST http://192.168.0.8/api/time/set \
  -H "Content-Type: application/json" \
  -d '{"hour": 14, "minute": 30, "second": 60}'
```

**Expected Response**:
```json
{"error":"Invalid time values (hour: 0-23, minute: 0-59, second: 0-59)"}
```

**HTTP Status**: 400 Bad Request

---

### Test 7: Missing Hour Parameter
**Description**: Send request without hour field

**Request**:
```bash
curl -X POST http://192.168.0.8/api/time/set \
  -H "Content-Type: application/json" \
  -d '{"minute": 30, "second": 0}'
```

**Expected Response**:
```json
{"error":"Missing hour"}
```

**HTTP Status**: 400 Bad Request

---

### Test 8: Missing Minute Parameter
**Description**: Send request without minute field

**Request**:
```bash
curl -X POST http://192.168.0.8/api/time/set \
  -H "Content-Type: application/json" \
  -d '{"hour": 14, "second": 0}'
```

**Expected Response**:
```json
{"error":"Missing minute"}
```

**HTTP Status**: 400 Bad Request

---

### Test 9: Missing Second Parameter
**Description**: Send request without second field

**Request**:
```bash
curl -X POST http://192.168.0.8/api/time/set \
  -H "Content-Type: application/json" \
  -d '{"hour": 14, "minute": 30}'
```

**Expected Response**:
```json
{"error":"Missing second"}
```

**HTTP Status**: 400 Bad Request

---

### Test 10: RTC Persistence Across Reboot
**Description**: Verify RTC maintains time after device reboot

**Steps**:
1. Set time to known value (e.g., 10:00:00):
   ```bash
   curl -X POST http://192.168.0.8/api/time/set \
     -H "Content-Type: application/json" \
     -d '{"hour": 10, "minute": 0, "second": 0}'
   ```
2. Wait 30 seconds
3. Reboot device:
   ```bash
   curl -X POST http://192.168.0.8/api/reboot
   ```
4. Wait for device to boot (30-60 seconds)
5. Check time:
   ```bash
   curl http://192.168.0.8/api/status
   ```

**Expected Result**:
- Time should be approximately 10:00:30 to 10:01:30 (depending on reboot duration)
- Time should NOT reset to 00:00:00 or previous compile time
- RTC hardware persists time across power cycles

---

### Test 11: Date Preservation
**Description**: Verify that setting time does not change the current date

**Steps**:
1. Note current date and time from `/api/status`
2. Set time to different hour:
   ```bash
   curl -X POST http://192.168.0.8/api/time/set \
     -H "Content-Type: application/json" \
     -d '{"hour": 12, "minute": 0, "second": 0}'
   ```
3. Check `/api/status` again

**Expected Result**:
- Time should be updated to 12:00:00
- Date (day/month/year) should remain unchanged from step 1

---

### Test 12: System Time Sync
**Description**: Verify system time is synchronized with RTC after setting

**Steps**:
1. Set time:
   ```bash
   curl -X POST http://192.168.0.8/api/time/set \
     -H "Content-Type: application/json" \
     -d '{"hour": 15, "minute": 45, "second": 30}'
   ```
2. Immediately check status:
   ```bash
   curl http://192.168.0.8/api/status
   ```

**Expected Result**:
- `current_time` field in status response should show approximately 15:45:30
- Time should continue incrementing normally from this point

---

## Manual Testing Checklist

- [ ] Test 1: Valid time mid-day
- [ ] Test 2: Valid time midnight
- [ ] Test 3: Valid time end of day
- [ ] Test 4: Invalid hour (too high)
- [ ] Test 5: Invalid minute (too high)
- [ ] Test 6: Invalid second (too high)
- [ ] Test 7: Missing hour parameter
- [ ] Test 8: Missing minute parameter
- [ ] Test 9: Missing second parameter
- [ ] Test 10: RTC persistence across reboot
- [ ] Test 11: Date preservation
- [ ] Test 12: System time sync

---

## Serial Monitor Output

When testing, monitor the serial output at 19200 baud to observe:
- JSON body received: `Time set request body: {"hour":14,"minute":30,"second":0}`
- Success confirmation: `✅ Time set to: 14:30:00`
- Any error messages if RTC sync fails

---

## Notes

- Replace `192.168.0.8` with your device's actual IP address
- All times are in 24-hour format
- The endpoint only sets time, not date (day/month/year are preserved)
- RTC write is persistent - time survives power loss
- Memory usage: approximately 60 bytes for char buffers (well under 100-byte budget)
