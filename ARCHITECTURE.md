# SBAquaControl System Architecture

**See Also:**
- [PRODUCT.md](PRODUCT.md) - User-facing features and workflows
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development workflows and coding standards
- [docs/design/MACRO_REFACTORING.md](docs/design/MACRO_REFACTORING.md) - Macro system design details
- [docs/design/UI_UPDATE_LINEAR_INTERPOLATION.md](docs/design/UI_UPDATE_LINEAR_INTERPOLATION.md) - UI visualization changes

---

## Overview

SBAquaControl is an ESP8266-based aquarium LED light controller with WiFi-enabled web interface. The system provides 24-hour schedule automation for up to 16 PWM channels via PCA9685 I2C controller, real-time temperature monitoring, and macro (override) functionality for temporary lighting patterns.

**Key constraint**: ESP8266 has **160KB total RAM** with ~50-55% reserved at runtime. Memory efficiency is critical (see [CONTRIBUTING.md](CONTRIBUTING.md#memory-constraints)).

---

## Hardware Layer

### Microcontroller: ESP8266 (160MHz, 160KB RAM)
- **Boot**: Loads config from SD card, initializes WiFi, starts web server
- **Main loop**: Runs `proceedCycle()` every millisecond (non-blocking operations only)
- **Clock**: Synced via DS3231 RTC module on I2C bus (standard GPIO4/GPIO5)

### PWM Output
- **PCA9685** (16 channels, 12-bit, 300Hz): I2C interface at 0x40, synchronized via `pwm.setPWM()`
- **Native pins** (fallback): D0, D3 for direct GPIO PWM on ESP8266
- **Resolution**: PWM_MAX = 4095 (PCA9685), 1023 (ESP8266), 255 (AVR)
- **Smoothing**: Linear interpolation over time prevents harsh on-off transitions (see `PwmChannel::proceedCycle()`)

### Storage: SD Card (CS pin D8 on ESP8266)
- **Schedule configs**: `config/ledch_00.cfg` to `ledch_15.cfg` (one per channel)
- **Macro configs**: `macros/macro_001_ch00.cfg` to `macro_NNN_ch15.cfg` (duration-based schedules)
- **System config**: `config/wlan.cfg` (WiFi credentials, IP settings)
- **Web UI**: `app.htm`, `js/`, `css/` folders served via HTTP

### Sensors
- **DS18B20** (optional, 1-Wire): Water temperature reading, non-blocking tick-tock state machine (2-second cycle)
- **DS3231 RTC**: Hardware real-time clock (syncs system time on boot)

---

## Software Architecture

### Firmware (C++ - embedded)

#### Core Classes

**`AquaControl`** (main controller)
- `init()`: Boot sequence (SD, WiFi, RTC, PWM init, load schedules)
- `proceedCycle()`: Main loop called repeatedly (handles PWM updates, web server, temperature reading)
- `addChannelTarget()`, `writeLedConfig()`: Schedule persistence
- `writePwmToDevice()`: Writes computed PWM value to PCA9685 or native pin

**`PwmChannel`** (per-channel logic)
- `Targets[]`: Array of up to 32 time/value pairs per channel
- `proceedCycle()`: Linear interpolation engine
  - Finds current and next target times
  - Calculates smooth transition: `vx = (m * deltaNow) + n` (slope-intercept form)
  - Handles day-wrapping (last target→first target of next day)
- `TestMode`: Temporary override (60-second timeout) for manual testing
- `addTarget()`, `removeTargetAt()`: Sorted insertion/removal

**`TemperatureReader`** (optional, async)
- `readTemperature()`: Tick-tock pattern (first call: start conversion, second call: read result)
- Non-blocking: doesn't halt main loop while waiting for sensor

#### Memory Management (Critical)
- **String class**: Avoided in production paths—causes heap fragmentation
- **Pattern**: Use char buffers + `sprintf()` for file operations
- **Example**: Instead of `String path = "config/ledch_" + String(i) + ".cfg"`, use:
  ```cpp
  char sTempFilename[30];
  sprintf(sTempFilename, "config/ledch_%02d.cfg", i);
  ```
- **JSON streaming**: `_Server.sendContent()` used to avoid building entire response in memory

#### Build Configuration (platformio.ini)
- **[env:esp8266]**: USB upload (initial programming)
- **[env:esp8266_ota]**: WiFi OTA updates (recommended for iteration)
- **Conditional compilation** (AquaControl_config.h):
  - `USE_PCA9685`: 16-channel via I2C (default)
  - `USE_RTC_DS3231`: RTC synchronization
  - `USE_WEBSERVER`: HTTP API and web UI
  - `USE_DS18B20_TEMP_SENSOR`: Temperature monitoring

---

### Web Interface (JavaScript - single-page app)

#### Frontend Stack
- **HTML shell** (`app.htm`): Minimal template with handlebars-style `##PLACEHOLDER##` replacement
- **Framework**: Vanilla JavaScript (no npm dependencies to respect ESP8266 constraints)
- **Chart library**: Chart.js (CDN-loaded) for 24-hour schedule visualization
- **Polling**: Every 2 seconds via `fetch()` to `/api/status` (includes time, temperature, macro state)

#### Key Modules

**`app.js`** (application controller)
- `init()`: Bootstrap UI, fetch initial state
- `updateSchedule()`: Poll `/api/schedule/all`, re-render chart
- `openMacroWizard()`: Launch creation dialog
- Event handlers: click → API call → update UI

**`chart-manager.js`** (visualization)
- `renderChart()`: Initialize Chart.js with channel data
- `updateTarget()`: Drag-to-edit targets on chart
- `deleteTarget()`: Right-click menu for removal
- Linear interpolation: Draws smooth curves between targets

**`api.js`** (REST wrapper)
- `GET /api/status`: Current time, temperature, macro state
- `GET /api/schedule/get?channel=N`: Fetch targets for channel N
- `POST /api/schedule/save`: Save all targets for channel (JSON body)
- `POST /api/schedule/target/add`: Add single target
- `POST /api/test/start`, `/api/test/update`, `/api/test/exit`: Manual override mode
- `GET/POST /api/macro/*`: Macro list, load, save, activate, stop, delete

---

## System Workflows

### Boot Sequence
```
ESP8266 reset
  → SD card init
  → Load wlan.cfg
  → WiFi connect (20s timeout, fallback to AP mode)
  → Initialize RTC, sync time
  → Initialize PCA9685
  → Load schedule configs (ledch_00.cfg → ledch_05.cfg)
  → Start web server
  → Enter main loop
```

### Main Loop (Non-blocking)
```
proceedCycle() [called every ~1ms]:
  → Update CurrentSecOfDay
  → For each channel:
     → Calculate interpolated PWM value
     → If changed, flag for update
     → Write to PCA9685
  → Handle web requests (_Server.handleClient())
  → Poll temperature (if async ready)
  → Handle OTA updates
```

### Schedule Execution
```
User sets target: 08:30 @ 100% brightness
  → Stored in Targets[] array (sorted by time)
  → At 08:30:00, proceedCycle() detects:
     → lastTarget = 08:00 @ 80%
     → currentTarget = 08:30 @ 100%
     → Calculates slope: (100-80) / (30min) = 0.667%/min
     → Interpolates current value based on elapsed time
  → PWM smoothly transitions from 80→100 over 30 minutes
  → At 09:00, next target becomes active
```

### Macro System
```
User creates "Movie Mode" macro (2-hour duration, all channels @ 0%)
  → Saved to: macros/macro_001_ch00.cfg → ch05.cfg
  → User clicks "activate" → POST /api/macro/activate
  → Firmware loads macro schedule and tracks expiration time
  → Channels switch to macro targets
  → Timer counts down in _activeMacro.expiresAt
  → proceedCycle() checks if macro expired
  → When complete, auto-restores previous schedule
  → User can manually stop via POST /api/macro/stop
```

### Time Synchronization
```
Boot sequence attempts time sync in priority order:
  1. NTP sync (if USE_NTP defined, 2-second timeout)
  2. RTC sync (DS3231 hardware clock)
  3. Manual sync via /api/time/set (fallback)
  
Sync status tracked in _LastTimeSyncSource enum:
  - TimeSyncSource::Ntp (successful NTP)
  - TimeSyncSource::Rtc (RTC fallback)
  - TimeSyncSource::Api (manual set)
  - TimeSyncSource::Unknown (no sync yet)
```

---

## Data Formats

### Schedule File (config/ledch_NN.cfg)
```
08:30;100
12:00;50
18:45;100
23:00;10
```
Format: `HH:MM;VALUE` (VALUE = 0-100%)

### Macro File (macros/macro_NNN_chNN.cfg)
```
00:30;0
01:00;50
02:00;0
```
Format: `MM:SS;VALUE` (duration-based, not 24-hour)

### WLAN Config (config/wlan.cfg)
```
mode="client"
ssid="MyNetwork"
pw="password123"
ip="auto"
gateway="auto"
```

### JSON API Response (example)
```json
{
  "test_mode": false,
  "current_time": "14:23:05",
  "current_seconds": 51785,
  "temperature": 24.5,
  "macro_active": false
}
```

---

## Design Patterns

### Tick-Tock for Async Operations
Used by temperature sensor to avoid blocking main loop:
```cpp
if (!_TickTock) {
  // First call: start operation
  startTemperatureConversion();
  _TickTock = true;
} else {
  // Second call: read result
  readResult();
  _TickTock = false;
}
```

### Linear Interpolation
All smooth transitions use this formula:
```cpp
float vx = (slope * elapsedTime) + baseValue;
```
Applied to PWM, LED dimming, and future gradient features.

### File I2C with Temp File Pattern
Config updates use atomic writes:
1. Read original file
2. Write modified version to `_new.cfg`
3. Delete original, rename temp → original

Prevents corruption if power lost during write.

---

## Known Limitations & Future Work

### Current Limitations
- ✅ ~~Macro activation/stop endpoints are stubs~~ **FIXED**: Fully implemented with timer
- ✅ ~~No manual time-setting API~~ **FIXED**: `/api/time/set` endpoint implemented
- Only 6 of 16 channels managed by UI (system supports 16)
- No timezone support (always UTC)
- No authentication (assumes private network)

### Phase 2-5 Roadmap
1. **Phase 2**: Complete macro timer + auto-restore
2. **Phase 3**: Time-setting API + UI picker
3. **Phase 4**: Timezone support, NTP sync
4. **Phase 5**: Multi-user authentication, gradients
