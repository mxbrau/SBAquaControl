# SBAquaControl Quick Reference
**Version**: 0.5.001
**Purpose**: Fast lookup for common tasks

---

## 🚀 Quick Start

### Flash Firmware
```bash
# Clone and open in VS Code with PlatformIO
pio run -e esp8266 --target upload

# Or for OTA (WiFi) updates after initial setup:
pio run -e esp8266_ota --target upload
```

### Access Web UI
```
URL: http://192.168.103.8
Default SSID: SBAQC_WIFI
Default Password: sbaqc12345
```

### Add Control Point
1. Set time in "⏰ Zeitpunkt hinzufügen" section
2. Adjust channel sliders to desired brightness
3. Click "Aktuelle Werte zu dieser Zeit speichern"
4. Verify point appears on chart with straight line to neighbors

---

## 📊 Architecture Summary

```
Hardware:
├─ ESP8266 (160 KB RAM, ~56% used)
├─ PCA9685 PWM Controller (16 channels)
├─ DS3231 RTC (optional, time sync)
├─ DS18B20 Temperature (optional)
└─ SD Card (config + macro storage)

Firmware:
├─ 16 PWM channels × 32 targets max = 2.6 KB
├─ Linear interpolation (no smoothing)
├─ Streaming JSON API (no large String allocations)
├─ Hybrid time sync (NTP → RTC → API)
├─ Macro timer system with auto-restore
└─ OTA update capable

UI:
├─ Chart.js visualization (linear curves)
├─ Real-time schedule editor
├─ Macro creation wizard
├─ Test mode for manual control
├─ Time sync status display
└─ JSON API integration
```

---

## 🔧 Configuration Parameters

### Firmware (src/AquaControl_config.h)

| Parameter | Value | Notes |
|-----------|-------|-------|
| `USE_PCA9685` | Defined | 16 PWM channels via I2C |
| `USE_RTC_DS3231` | Defined | DS3231 time sync |
| `USE_WEBSERVER` | Defined | Web UI enabled |
| `MAX_TARGET_COUNT_PER_CHANNEL` | 32 | ESP8266 RAM limit |
| `PWM_FREQ` | 300 Hz | Smooth PWM frequency |
| `PWM_MAX` | 4095 | 12-bit PCA9685 resolution |
| `SD_CS` | D8 | Chip select pin |

### UI (extras/SDCard/js/chart-manager.js)

| Parameter | Value | Notes |
|-----------|-------|-------|
| `maxTargetsPerChannel` | 32 | Matches firmware |
| `samplesPerSegmentDefault` | 2 | Linear mode (not smoothed) |
| `interpolationMode` | 'linear' | No spline smoothing |

---

## 📁 File Structure

```
src/
├─ AquaControl.h           ← Main class definition
├─ AquaControl.cpp         ← Core PWM & config logic
├─ AquaControl_config.h    ← Compile-time settings
└─ Webserver.cpp           ← HTTP API endpoints

extras/SDCard/
├─ app.htm                 ← Modern SPA dashboard
├─ editled.htm             ← Form-based schedule editor
├─ css/
│  ├─ style.css            ← Old UI styling
│  └─ app.css              ← New SPA styling
├─ js/
│  ├─ app.js               ← SPA main logic
│  ├─ chart-manager.js     ← Chart.js integration
│  ├─ api.js               ← API wrapper
│  └─ config.js            ← UI configuration
└─ config/
   └─ ledch_*.cfg          ← Schedule files (1 per channel)

Documentation/
├─ FIRMWARE_STATUS.md      ← Current state & features
├─ UI_UPDATE_LINEAR_INTERPOLATION.md ← UI changes
├─ TESTING_GUIDE.md        ← Test procedures
├─ ROADMAP.md              ← Future phases
└─ SESSION_SUMMARY_2025-12-30.md ← This session's work
```

---

## 🔌 API Endpoints

### Schedule Operations
```
GET  /api/status                 → Device status (time, temp, macro state)
GET  /api/schedule/get?channel=N → Load single channel
GET  /api/schedule/all           → Load all 6 channels
POST /api/schedule/save          → Save schedule to SD
POST /api/schedule/target/add    → Add single target
POST /api/schedule/target/delete → Remove target
```

### Macro System
```
GET  /api/macro/list             → List all available macros
GET  /api/macro/get?id=XXX       → Load macro details
POST /api/macro/save             → Create/update macro
POST /api/macro/activate         → Activate macro (with timer)
POST /api/macro/stop             → Stop active macro
POST /api/macro/delete           → Delete macro
```

### Time Synchronization
```
POST /api/time/set               → Set time manually (hour, minute, second)
                                   Auto-fallback when NTP/RTC unavailable
```

### Test Mode
```
POST /api/test/start             → Enter test mode
POST /api/test/update            → Update slider values
POST /api/test/exit              → Exit test mode
```

### Diagnostic
```
GET  /api/debug                  → Heap memory info
POST /api/reboot                 → Restart device
```

### Request Examples
```bash
# Get all schedules
curl http://192.168.103.8/api/schedule/all

# Get device status (includes time, temp, macro state)
curl http://192.168.103.8/api/status

# Get debug info
curl http://192.168.103.8/api/debug

# Set time manually (when NTP/RTC unavailable)
curl -X POST http://192.168.103.8/api/time/set \
  -H "Content-Type: application/json" \
  -d '{"hour":14,"minute":30,"second":0}'

# List all macros
curl http://192.168.103.8/api/macro/list

# Activate a macro (2-hour duration)
curl -X POST http://192.168.103.8/api/macro/activate \
  -H "Content-Type: application/json" \
  -d '{"id":"macro_001","duration":7200}'

# Stop active macro
curl -X POST http://192.168.103.8/api/macro/stop

# Start test mode
curl -X POST http://192.168.103.8/api/test/start

# Add control point (JSON body)
curl -X POST http://192.168.103.8/api/schedule/target/add \
  -H "Content-Type: application/json" \
  -d '{"channel":0,"time":28800,"value":75}'
```

---

## 🐛 Common Issues & Fixes

### Issue: Time is incorrect after boot
**Fix**:
1. Check if RTC battery is present and charged
2. Enable NTP sync in `src/AquaControl_config.h` (define `USE_NTP`)
3. Use browser time sync: UI auto-syncs when time is invalid
4. Manually set time: `POST /api/time/set` with current time
5. Check `/api/status` for `time_source` and `time_valid` fields

### Issue: Macro doesn't activate
**Fix**:
1. Verify macro files exist on SD card: `macros/macro_NNN_chNN.cfg`
2. Check duration is non-zero in activation request
3. Verify no other macro is already active
4. Monitor serial output for activation errors
5. Check `/api/status` for `macro_active` field

### Issue: Chart shows no data
**Fix**:
1. Verify SD card has schedule files: `ledch_00.cfg`, `ledch_01.cfg`, etc.
2. Check browser console (F12) for JavaScript errors
3. Verify API returns data: `GET /api/schedule/all`

### Issue: Device won't boot
**Fix**:
1. Check free heap: `GET /api/debug` (should be >50 KB)
2. Verify SD card is present and readable
3. Check serial monitor for error messages
4. Try reflashing firmware

### Issue: LEDs don't respond to schedule
**Fix**:
1. Verify test mode is OFF
2. Check current time is correct: `GET /api/status`
3. Verify PCA9685 is connected (I2C address 0x40)
4. Test with manual slider in test mode

### Issue: API response timeout
**Fix**:
1. Check WiFi connection stability
2. Monitor free heap: `GET /api/debug`
3. Reduce concurrent requests
4. Restart device if heap <30 KB

---

## 📈 Performance Benchmarks

| Operation | Target | Actual |
|-----------|--------|--------|
| Boot time | <5s | ~3s |
| API response | <200ms | 50-150ms |
| Chart render | <100ms | 30-80ms |
| Save schedule | <1s | 0.5-0.8s |
| Memory stable | >50KB heap | ~70KB available |
| CPU utilization | <50% | ~20-30% |

---

## 🧪 Testing Quick Checklist

```
Functionality Tests:
☐ Load schedule from device
☐ Add new control point
☐ Delete control point
☐ Save schedule
☐ Reload page (data persists)

Hardware Tests:
☐ LED fades match chart prediction
☐ Linear interpolation confirmed
☐ Test mode controls channels
☐ Exit test mode returns to schedule

Performance Tests:
☐ Free heap >50 KB
☐ API responses <200ms
☐ No memory leaks over 1 hour
☐ Responsive to user input

Edge Cases:
☐ Single point (constant value)
☐ Midnight rollover
☐ Rapid on/off pattern
☐ 32-point schedule loaded
```

---

## 📚 Documentation Map

| Need | Document |
|------|----------|
| Understand current system | `FIRMWARE_STATUS.md` |
| UI visualization details | `UI_UPDATE_LINEAR_INTERPOLATION.md` |
| Run full test suite | `TESTING_GUIDE.md` |
| Plan new features | `ROADMAP.md` |
| This session's work | `SESSION_SUMMARY_2025-12-30.md` |
| Quick lookup | This file |

---

## 🎯 Common Development Tasks

### Add New API Endpoint
**File**: `src/Webserver.cpp`

1. Create handler function:
```cpp
void handleApiMyEndpoint() {
    String body = _Server.arg("plain");
    // Process request
    char buf[128];
    sprintf(buf, "{\"result\":\"ok\"}");
    _Server.send(200, "application/json", buf);
}
```

2. Register in `init()`:
```cpp
_Server.on("/api/myendpoint", HTTP_GET, handleApiMyEndpoint);
```

### Modify PWM Behavior
**File**: `src/AquaControl.cpp` - `PwmChannel::proceedCycle()`

Key variables:
- `_PwmTarget` - desired PWM value
- `_PwmValue` - current PWM value
- `CurrentWriteValue` - value sent to hardware
- `PWM_STEP` - fade speed (5 typical)

### Update UI Chart
**File**: `extras/SDCard/js/chart-manager.js`

Key methods:
- `updateChannel()` - load data from API
- `generateLinearSamples()` - convert targets to points
- `interpolateValue()` - linear calculation at specific time
- `chart.update()` - redraw display

---

## 🔐 Security Notes

### Default Credentials (CHANGE IN PRODUCTION)
- SSID: `SBAQC_WIFI`
- Password: `sbaqc12345`
- OTA Password: `aquarium123`

### Recommendations
1. Change WiFi password in config
2. Change OTA password if exposed to network
3. Use HTTPS if WiFi not fully secured
4. Consider MAC filtering

### Known Limitations
- No authentication on API endpoints
- No encryption of stored schedules
- All commands accepted from any IP

---

## 📞 Helpful Commands

### Check Device Status
```bash
# Via browser
http://192.168.103.8/api/status

# Via curl
curl http://192.168.103.8/api/status | jq
```

### Monitor Memory
```bash
# Real-time heap monitoring
watch -n 1 'curl -s http://192.168.103.8/api/debug | jq .free_heap'
```

### View Serial Output
```bash
# PlatformIO (Ctrl+Alt+S in VS Code):
pio device monitor --baud 19200
```

### Clear All Schedules
```bash
# Delete SD card files
rm config/ledch_*.cfg

# Or via web UI: Delete all control points for each channel
```

---

## 🚦 State Transitions

### Device Lifecycle
```
Power On
    ↓
Init SD Card
    ↓
Load WLAN Config
    ↓
Connect WiFi
    ↓
Sync RTC Time
    ↓
Init PWM Channels
    ↓
Load LED Configs (schedules)
    ↓
Ready for proceedCycle()
    ↓
Main Loop
├─ Calculate current PWM values
├─ Update LED channels
├─ Handle WebServer requests
├─ Read temperature (optional)
└─ Repeat every cycle
```

### Test Mode Transition
```
Normal Schedule
    ↓ (User clicks Test Mode)
Test Mode Active
├─ Ignore schedule
├─ Use slider values
├─ Show Test Mode banner
└─ Timeout after 60s
    ↓
Resume Normal Schedule
```

---

## 💾 Data Persistence

### Schedule Storage
```
Format: Plain text, one target per line
Syntax: HH:MM;VALUE
Example:
08:00;0
12:00;100
18:00;50
23:00;0

File: config/ledch_0N.cfg (where N = 00-15)
Max size: ~1 KB per channel
Max targets: 32 per channel
```

### Configuration Files
```
config/wlan.cfg      → WiFi settings
config/ledch_00.cfg  → Channel 0 schedule
config/ledch_01.cfg  → Channel 1 schedule
...
config/macros.json   → Macros (future Phase 3)
```

---

## 🔄 Update Procedure

### OTA Update (Over-The-Air)
```
1. Compile new firmware
2. Device → OTA menu (if accessible)
3. Select .bin file
4. Wait for upload and restart
```

### Manual Update (Via USB)
```
1. Connect ESP8266 via USB (first time only)
2. pio run -e esp8266 --target upload
3. Device reboots and continues operation

# For subsequent updates, use OTA:
pio run -e esp8266_ota --target upload
```

### SD Card Update
```
1. Remove SD card
2. Update HTML/JS files on PC
3. Reinsert SD card
4. Web UI loads new files automatically
```

---

## ✅ Pre-Release Checklist

- [ ] Compile without warnings
- [ ] Boot sequence completes <5 seconds
- [ ] Free heap >50 KB
- [ ] All API endpoints respond
- [ ] Chart displays correctly
- [ ] Schedule saves and persists
- [ ] Test mode works
- [ ] LED fade matches chart
- [ ] No memory leaks (1 hour runtime)
- [ ] Documentation is current

---

**Version**: 1.0
**Last Updated**: 2025-12-30
**Status**: Ready for Reference
