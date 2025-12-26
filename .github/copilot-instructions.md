# SBAquaControl - AI Coding Instructions

## Project Overview
ESP8266-based aquarium LED light controller (Arduino library) with WiFi web interface for daylight simulation. Supports up to 16 PWM channels via PCA9685 or native ESP8266/AVR pins.

## Architecture & Key Components

### Core Classes ([src/AquaControl.h](../src/AquaControl.h), [src/AquaControl.cpp](../src/AquaControl.cpp))
- **`AquaControl`**: Main controller class with `init()` and `proceedCycle()` methods
- **`PwmChannel`**: Manages individual LED channels with time-based targets and smooth transitions
  - Each channel has up to 10 targets (time/value pairs) defined in `Target` struct
  - `proceedCycle()` interpolates between targets based on current time
  - Test mode support (60-second timeout) for manual channel control
- **`TemperatureReader`**: Async DS18B20 temperature reading using tick-tock pattern (non-blocking)

### Hardware Abstraction Pattern
PWM implementation varies by platform - controlled via conditional compilation:
```cpp
#if defined(USE_PCA9685)       // 16 channels, 12-bit (0-4095), I2C
#elif defined(__AVR__)         // 6-16 channels, 8-bit (0-255), native pins
#elif defined(ESP8266)         // 2 channels, 10-bit (0-1023), software PWM
```
Use `PWM_MAX`, `PWM_CHANNELS`, and `PWM_CHANNEL_N` constants - never hardcode values.

### Configuration System ([src/AquaControl_config.h](../src/AquaControl_config.h))
Feature flags control build:
- `USE_PCA9685`: External PWM controller vs. native pins
- `USE_RTC_DS3231`: DS3231 RTC vs. NTP time sync
- `USE_WEBSERVER`: ESP8266 web interface
- `USE_DS18B20_TEMP_SENSOR`: Temperature monitoring

### Web Interface ([src/Webserver.cpp](../src/Webserver.cpp), [extras/SDCard/\*.htm](../extras/SDCard/))
- ESP8266WebServer serves HTML from SD card (`SD_CS = D8` on ESP8266)
- Config stored in SD card files: `config/wlan.cfg`, LED settings per channel
- Template system: `##PLACEHOLDER##` replaced dynamically (e.g., `##FW_VERSION##`, `##TEMP##`)
- Handler pattern: `handleXxxGET()` serves forms, `handleXxxPOST()` processes submissions

### WLAN Configuration
- Client mode (connects to existing network) or AP mode fallback
- Default AP: SSID `SBAQC_WIFI`, password `sbaqc12345`, IP `192.168.0.1`
- Supports manual IP or DHCP via `config/wlan.cfg`
- Config parsing: key-value pairs like `ssid="MyNetwork"`, wrapped in quotes

## Critical Workflows

### Building & Platform Requirements
**CRITICAL**: ESP8266 core version compatibility is fragile:
- Arduino IDE: **Use ESP8266 v2.2.0 only** (v2.3.0 causes crashes)
- Visual Micro: **Use ESP8266 v2.3.0 only** (v2.2.0 causes crashes)

Install as Arduino library: Extract to `~/Documents/Arduino/libraries/SBAquaControl/`

### Example Usage Pattern ([examples/AquaControlSketch/AquaControlSketch.ino](../examples/AquaControlSketch/AquaControlSketch.ino))
```cpp
AquaControl aqc;
void setup() { aqc.init(); }
void loop() { aqc.proceedCycle(); }
```
Call `proceedCycle()` continuously - it handles non-blocking operations.

### Time & RTC Handling
- Uses TimeLib.h for time management (`time_t`, `hour()`, `minute()`)
- DS3231 RTC on standard I2C pins syncs system time
- All times stored as Unix timestamps (seconds since 1970)
- `CurrentSecOfDay` pattern used throughout for daily scheduling

## Project-Specific Conventions

### Non-Blocking Operations
**Never use `delay()`** in production code except during WiFi connection (already present).
- Temperature reading: tick-tock state machine with `_TickTock` flag
- PWM transitions: gradual value changes per cycle via `_PwmTarget` tracking

### String Handling
Uses Arduino `String` class extensively, particularly in config parsing:
```cpp
String sLine = file.readStringUntil(10);  // Read until LF
sLine.replace("##TOKEN##", value);        // Template replacement
```
Strip CR/LF manually: `if (sLine.charAt(sLine.length()-1) == 13)...`

### File I/O Pattern
Config updates use temp file approach:
1. Read `config/file.cfg`
2. Write modified to `config/file_new.cfg`
3. Delete original, rename temp → original

### Serial Debugging
Extensive use of `Serial.print(F("..."))` for debugging - keep consistent style.
Use `F()` macro to store strings in flash (critical on AVR).

## Integration Points

### External Dependencies
- **Adafruit_PWMServoDriver**: PCA9685 I2C PWM controller (when `USE_PCA9685` defined)
- **DS3232RTC**: RTC time sync library
- **OneWire**: DS18B20 temperature sensor
- **ESP8266WiFi/WebServer**: WiFi and HTTP server (ESP8266 only)
- **SD**: Config and HTML storage

### Circuit Reference
Fritzing project: [extras/Circuit/SBAQC_1.0.fzz](../extras/Circuit/SBAQC_1.0.fzz)

## Language & Comments
Project documentation and comments are in **German** - maintain consistency when adding user-facing strings or comments.

## Current Status
Project version 0.5.001 (build 2017-12-10). Active development on test mode and web interface improvements.

## Planned UI Modernization (December 2025)

### New Interactive Web Interface
Replacing template-based HTML with modern single-page application:
- **Chart.js/Plotly** for interactive 24-hour schedule visualization
- **REST/JSON API** endpoints for data exchange
- **Client-side rendering** (browser does heavy lifting, ESP8266 just serves data)
- **6 active channels** (system supports 16, but only displaying/managing 6)

### Macro System Architecture
Macros are temporary schedule overrides with time-based patterns:
```
Regular Schedule → [User clicks "Movie Mode" macro] → Macro runs for 2 hours → Resume regular schedule
```

**Macro Structure:**
```json
{
  "name": "Movie Mode",
  "duration": 7200,
  "channels": [
    {"channel": 0, "targets": [{"time": 0, "value": 0}, {"time": 7200, "value": 0}]},
    {"channel": 1, "targets": [{"time": 0, "value": 0}, {"time": 7200, "value": 0}]}
  ]
}
```

**Macro Creation Workflow:**
1. User clicks "Create Macro" button
2. Wizard prompts for name and duration
3. Graph displays macro timeframe (0 to duration in seconds)
4. User edits channel curves like normal schedule
5. Save creates button in macro panel
6. Clicking macro button activates temporary override

**Storage:** `config/macros.json` contains all macro definitions

### Implementation Strategy
- **Phase 1:** JSON API endpoints (GET/POST schedule, test mode)
- **Phase 2:** Interactive schedule editor with live preview
- **Phase 3:** Macro wizard and activation system
- **Memory optimization:** Streaming JSON to avoid String concatenation
