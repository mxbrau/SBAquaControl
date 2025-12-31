# SBAquaControl v0.5.001 - Comprehensive Testing Guide

**Date**: 2025-12-30  
**Firmware Version**: 0.5.001  
**Target**: Full feature validation with linear interpolation

---

## Pre-Testing Setup

### Requirements
- ✅ Firmware flashed to ESP8266
- ✅ SD card with web UI files (`app.htm`, `js/`, `css/`, config files)
- ✅ PCA9685 PWM controller connected and working
- ✅ Browser with Chart.js support (Chrome, Firefox, Edge, Safari)
- ✅ Optional: Temperature sensor (DS18B20) for full feature test

### Network Setup
1. Power on device
2. Connect to SSID `SBAQC_WIFI` (password: `sbaqc12345`)
3. Navigate to `http://192.168.103.8`
4. Should see modern web dashboard with chart

### Expected Status
```
Device Status:
- Free Heap: 60-80 KB ✅ (healthy)
- Compile-time RAM: 50-55% ✅ (normal)
- Boot Time: <5 seconds ✅
- API Response: <100ms ✅
```

---

## Test Suite 1: UI Visualization (Linear Interpolation)

### Test 1.1: Chart Display - Empty State
**Objective**: Verify chart renders correctly with no data

**Steps**:
1. Open `http://192.168.103.8`
2. Look at "📊 Tagesablauf" section
3. Verify chart is visible with:
   - Horizontal axis labeled "Zeit" (0:00 to 23:59)
   - Vertical axis labeled "Helligkeit" (0% to 100%)
   - 6 empty datasets (one per channel)

**Expected Result**:
- [ ] Chart displays
- [ ] Axes properly labeled
- [ ] Legend shows all 6 channels
- [ ] No errors in browser console

---

### Test 1.2: Load Schedule - Verify Linear Display
**Objective**: Confirm loaded schedules show as straight lines (not curves)

**Steps**:
1. Create a simple test schedule via API or form
2. Schedule: 08:00→0%, 12:00→100%, 18:00→50%, 23:00→0%
3. Load page and observe chart

**Expected Result**:
- [ ] Chart shows 4 control points
- [ ] Lines are **perfectly straight** between points
- [ ] No smooth curves or S-shapes visible
- [ ] Points appear as markers (○) on the line
- [ ] Tooltip shows correct time and value

**Visual Example**:
```
100% ┌────────────┐  
     │            │
  80%│          ╱ │ ╲
  60%│        ╱   │   ╲
  40%│      ╱     │     ╲___
  20%│    ╱       │         ╲
   0%│__╱_________|___________|
    08:00        12:00       18:00  23:00
```

---

### Test 1.3: Chart Interaction - Click to Add Point
**Objective**: Verify point addition creates straight line to neighbors

**Steps**:
1. In "➕ Zeitpunkt hinzufügen" section, set time to 14:00
2. Set all channels to 75%
3. Click "Aktuelle Werte zu dieser Zeit speichern"
4. Observe chart update

**Expected Result**:
- [ ] New point appears at 14:00 on chart
- [ ] Lines from previous points to 14:00 are **straight**
- [ ] Lines from 14:00 to next points are **straight**
- [ ] No curves introduced
- [ ] Point is editable (can drag or click to delete)

---

### Test 1.4: Multiple Channels - Different Curves
**Objective**: Verify each channel renders independently

**Procedure**:
1. Create different schedules for channels 1, 2, 3:
   - Channel 1 (Red): Linear rise 08:00→100%, constant at night
   - Channel 2 (Green): Gradual rise all day
   - Channel 3 (Blue): Rapid on/off pattern
2. Load chart and observe all 3

**Expected Result**:
- [ ] Each channel shows different curve
- [ ] All curves are **straight line segments** (no smoothing)
- [ ] Colors match legend
- [ ] No overlap or confusion

---

### Test 1.5: Point Deletion - Chart Redraws
**Objective**: Verify deleting a point causes clean line reconnection

**Steps**:
1. Have schedule with 4+ points
2. Click on a middle point (hold cursor over point)
3. Confirm deletion
4. Observe chart update

**Expected Result**:
- [ ] Point removed instantly
- [ ] Neighbors reconnect with **straight line**
- [ ] No graphical artifacts
- [ ] Chart remains valid

---

## Test Suite 2: Backend API (Data Persistence)

### Test 2.1: Schedule Load - API Response Format
**Objective**: Verify API returns correct data structure

**Procedure**:
1. Open browser Developer Tools (F12)
2. Go to Network tab
3. Reload page
4. Look for request: `GET /api/schedule/all`
5. View response JSON

**Expected Response**:
```json
{
  "schedules": [
    {
      "channel": 0,
      "targets": [
        {"time": 28800, "value": 0, "isControl": true},
        {"time": 43200, "value": 100, "isControl": true},
        {"time": 64800, "value": 50, "isControl": true},
        {"time": 82800, "value": 0, "isControl": true}
      ]
    },
    ...
  ]
}
```

**Validation**:
- [ ] 6 schedules returned (one per channel)
- [ ] Each has `channel`, `targets` fields
- [ ] `isControl` flag present (all `true` = user points)
- [ ] Times in seconds (0-86400)
- [ ] Values 0-100
- [ ] No spline intermediate points

---

### Test 2.2: Save Schedule - Persist and Reload
**Objective**: Verify save/load cycle works correctly

**Steps**:
1. Clear all points from a channel
2. Add 3 new points: 06:00→10%, 14:00→90%, 20:00→30%
3. Click "💾 Zeitplan speichern"
4. Hard-refresh page (Ctrl+F5)
5. Verify schedule reloaded correctly

**Expected Result**:
- [ ] Save completes without error
- [ ] Page refresh loads same schedule
- [ ] Chart displays same points
- [ ] No data loss or corruption
- [ ] Times and values correct

---

### Test 2.3: Max Targets Enforcement
**Objective**: Verify 32-target limit is enforced

**Procedure**:
1. Try to add 35+ points to a single channel
2. Observe behavior

**Expected Result**:
- [ ] UI prevents adding beyond 32 points OR
- [ ] API rejects addition OR
- [ ] Device firmware rejects on save
- [ ] User gets clear error message
- [ ] No crash or data corruption

---

## Test Suite 3: Hardware Synchronization (Live PWM)

### Test 3.1: Visual Schedule Execution
**Objective**: Verify chart predicts device behavior accurately

**Procedure**:
1. Create simple schedule: 08:00→0%, 16:00→100%
2. Note current time on device
3. Watch LED brightness over time
4. Compare to chart prediction

**Expected Result**:
- [ ] LED fades smoothly from 0→100%
- [ ] Fade rate matches linear interpolation
- [ ] Chart shows what device is actually doing
- [ ] No mismatch between visual and actual behavior

**Calculation Check**:
```
Schedule: 08:00→0%, 16:00→100%
Duration: 8 hours = 28800 seconds
Fade rate: 100% / 28800 = 0.00347% per second

At 12:00 (4 hours = 14400 seconds later):
Expected brightness = 0 + (100-0) * 14400/28800 = 50%
→ LED should be at 50%
```

---

### Test 3.2: Test Mode - Manual Control
**Objective**: Verify manual channel control works

**Steps**:
1. Click "⚡ Test-Modus starten"
2. See 6 channel sliders appear
3. Move slider for Channel 1
4. Observe LED brightness change
5. Return to automatic mode

**Expected Result**:
- [ ] Slider values 0-100%
- [ ] LED responds immediately
- [ ] Chart shows "Test Mode" banner
- [ ] Exit test mode resumes schedule
- [ ] No stuck values

---

### Test 3.3: Temperature Display (if enabled)
**Objective**: Verify temperature sensor integration

**Procedure**:
1. If DS18B20 sensor connected, look at status area
2. Should show "🌡️ XX.X°C"
3. Change water temperature (warm water)
4. Refresh and observe temperature update

**Expected Result**:
- [ ] Temperature displays if sensor present
- [ ] Updates every 10 seconds
- [ ] Shows reasonable values (20-32°C for aquarium)
- [ ] No garbage data or errors

---

## Test Suite 4: Edge Cases

### Test 4.1: Midnight Rollover
**Objective**: Verify 24-hour schedule wraps correctly

**Procedure**:
1. Create schedule with points:
   - 23:00 → 100%
   - 07:00 → 50%
2. Check interpolation at 00:30 (middle of night)
3. Verify linear fade from 23:00 to 07:00

**Expected Result**:
- [ ] Device correctly interpolates over midnight
- [ ] No abrupt jumps at 00:00
- [ ] Brightness at 00:30 is correct
- [ ] Schedule wraps seamlessly

---

### Test 4.2: Identical Consecutive Values
**Objective**: Verify constant values render correctly

**Steps**:
1. Create schedule:
   - 08:00 → 50%
   - 09:00 → 50%
   - 10:00 → 50%
2. Observe chart

**Expected Result**:
- [ ] Horizontal line at 50% from 08:00-10:00
- [ ] Points visible at 08:00, 09:00, 10:00
- [ ] No slopes or fluctuations
- [ ] Renders correctly

---

### Test 4.3: Rapid On/Off Pattern
**Objective**: Verify fast transitions work

**Steps**:
1. Create alternating pattern:
   - 12:00 → 0%
   - 12:01 → 100%
   - 12:02 → 0%
   - 12:03 → 100%
2. Observe chart

**Expected Result**:
- [ ] Steep lines visible between points
- [ ] No smoothing distortion
- [ ] Points clearly marked
- [ ] Linear interpolation only

---

### Test 4.4: Single Point (All Day Constant)
**Objective**: Verify single-point schedule works

**Procedure**:
1. Delete all but one point
2. Set to 12:00 → 75%
3. Observe chart and device

**Expected Result**:
- [ ] Flat line at 75% across 24-hour range
- [ ] LED stays constant brightness
- [ ] No errors or crashes

---

## Test Suite 5: UI Usability

### Test 5.1: Responsive Design
**Objective**: Verify UI works on different screen sizes

**Devices to Test**:
- [ ] Desktop (1920×1080) - full layout
- [ ] Tablet (800×600) - responsive
- [ ] Phone (375×667) - mobile layout

**Expected Result**:
- [ ] All elements visible
- [ ] No horizontal scrolling needed
- [ ] Touch controls work on mobile
- [ ] Chart scales appropriately

---

### Test 5.2: Chart Tooltip Accuracy
**Objective**: Verify tooltips show correct values

**Steps**:
1. Hover mouse over various points on chart
2. Note time and value in tooltip
3. Verify accuracy

**Expected Result**:
- [ ] Tooltip shows time (HH:MM format)
- [ ] Tooltip shows value (X%)
- [ ] Numbers match schedule definition
- [ ] No off-by-one errors

---

### Test 5.3: Navigation and Links
**Objective**: Verify all UI sections accessible

**Steps**:
1. Check navigation to:
   - [ ] Schedule editor (chart)
   - [ ] Channel controls
   - [ ] Test mode
   - [ ] Add target section
   - [ ] Macro system (if available)

**Expected Result**:
- [ ] All sections load
- [ ] No broken links
- [ ] Returns work correctly

---

## Test Suite 6: Performance & Stability

### Test 6.1: Memory Stability
**Objective**: Verify no memory leaks during extended use

**Procedure**:
1. Open API debug endpoint: `http://192.168.0.1/api/debug`
2. Note free heap size
3. Use UI actively for 30 minutes:
   - Add/remove points
   - Save schedules
   - Switch between channels
   - Reload page multiple times
4. Check free heap again

**Expected Result**:
- [ ] Free heap remains stable (>50KB)
- [ ] No continuous decline
- [ ] No crash after 30 min

**Debug Output Example**:
```json
{
  "free_heap": 65536,
  "max_free_block": 62464,
  "heap_fragmentation": 4.7,
  "uptime_ms": 120000,
  "vcc_voltage_mv": 3300,
  "cpu_freq_mhz": 160
}
```

---

### Test 6.2: API Response Time
**Objective**: Verify API performance is acceptable

**Procedure**:
1. Open browser DevTools Network tab
2. Perform various operations:
   - Load schedule
   - Save schedule
   - Add target
   - Delete target
3. Note response times

**Expected Result**:
- [ ] All responses <200ms
- [ ] Typical response 50-100ms
- [ ] No timeouts
- [ ] Consistent performance

---

### Test 6.3: Concurrent Operations
**Objective**: Verify device handles simultaneous requests

**Procedure**:
1. Open two browser windows
2. In Window 1: Load schedule editor
3. In Window 2: Open test mode
4. In Window 3: Load another schedule
5. Switch between windows, make changes

**Expected Result**:
- [ ] All windows work independently
- [ ] No crashes or conflicts
- [ ] Changes visible in all windows
- [ ] Device responds to latest request

---

## Test Suite 7: Configuration Validation

### Test 7.1: Firmware Configuration
**Objective**: Verify firmware settings match UI

**Check Points**:
1. Firmware: `MAX_TARGET_COUNT_PER_CHANNEL = 32`
   - [ ] Check in `src/AquaControl_config.h`
2. UI: `maxTargetsPerChannel = 32`
   - [ ] Check in `extras/SDCard/js/chart-manager.js` line 10

**Expected Result**:
- [ ] Both set to 32
- [ ] No mismatch

---

### Test 7.2: PWM Channel Configuration
**Objective**: Verify all 16 PWM channels configured

**Procedure**:
1. Check firmware: `PWM_CHANNELS` define
2. Check UI: Channel count in `CONFIG.channelNames`
3. Test adding point to each channel

**Expected Result**:
- [ ] Firmware supports 16 channels
- [ ] UI displays all relevant channels (typically 1-6)
- [ ] No missing or broken channels

---

## Test Suite 8: Documentation Validation

### Test 8.1: README Accuracy
**Objective**: Verify project documentation is current

**Checks**:
- [ ] Version number in README matches firmware (0.5.001)
- [ ] Feature list accurate
- [ ] Setup instructions clear and correct
- [ ] Known limitations documented

---

### Test 8.2: Code Comments
**Objective**: Verify recent changes are documented

**Checks**:
- [ ] `generateMonotoneSamples()` comment explains linear-only behavior
- [ ] `maxTargetsPerChannel = 32` comment explains ESP8266 RAM limit
- [ ] Configuration comments are clear
- [ ] No outdated comments

---

## Reporting Results

### Test Result Template

```
TEST SUITE: UI Visualization
DATE: YYYY-MM-DD
FIRMWARE: 0.5.001
TESTER: [Your Name]

RESULTS:
- [ ] Test 1.1: PASS / FAIL / N/A
- [ ] Test 1.2: PASS / FAIL / N/A
- [ ] Test 1.3: PASS / FAIL / N/A
- [ ] Test 1.4: PASS / FAIL / N/A
- [ ] Test 1.5: PASS / FAIL / N/A

ISSUES FOUND:
1. [Issue title]
   - Steps to reproduce
   - Expected vs. actual
   - Severity: CRITICAL / HIGH / MEDIUM / LOW

NOTES:
[Any additional observations]
```

### Acceptance Criteria
- ✅ All Test Suites 1-4 PASS (visualization, API, hardware, edge cases)
- ✅ Test Suite 5 PASS with no usability issues
- ✅ Test Suite 6 PASS with no memory leaks or crashes
- ✅ Test Suite 7 PASS - configuration aligned
- ✅ Test Suite 8 PASS - documentation current

---

## Known Issues (v0.5.001)

1. **No issues reported yet** - This is the first comprehensive test suite

---

## Next Steps After Testing

1. **If all tests pass**:
   - [ ] Mark as "Stable Release"
   - [ ] Document test results
   - [ ] Plan Phase 2 features

2. **If issues found**:
   - [ ] Log detailed bug reports
   - [ ] Prioritize by severity
   - [ ] Create fix branch
   - [ ] Retest after fixes

---

## Appendix: Useful Debug Commands

### Check Device Status
```
curl http://192.168.0.1/api/status
```

### Get Debug Info
```
curl http://192.168.0.1/api/debug
```

### Load All Schedules
```
curl http://192.168.0.1/api/schedule/all
```

### Browser Console Commands
```javascript
// Check current chart data
console.log(chartManager.sampledSchedules);

// Check current values at specific time (seconds from midnight)
let values = chartManager.getValuesAtTime(43200);  // 12:00 noon
console.log(values);
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-30  
**Status**: Ready for Testing
