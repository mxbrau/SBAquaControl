# SBAquaControl Product Overview

**SBAquaControl** is a WiFi-enabled aquarium LED lighting controller for professional-grade daylight simulation. It automates color and brightness across up to 16 LED channels with customizable 24-hour schedules, supports emergency overrides via temporary "macros," and provides real-time monitoring via a modern web interface.

---

## Core Features

### 1. Automated 24-Hour Lighting Schedules
- **Per-channel control**: Set independent schedules for white, blue, red, and other LED types
- **Smooth transitions**: Linear interpolation between target brightness levels (no harsh flashing)
- **Flexible targets**: Define unlimited time/brightness pairs per channel (stored in sorted order)
- **Example schedule**:
  - 06:00 → 0% (off)
  - 08:00 → 30% (sunrise)
  - 12:00 → 100% (midday peak)
  - 18:00 → 50% (evening warm)
  - 23:00 → 0% (night off)
- **Daily wrap-around**: Schedule seamlessly continues next day

### 2. Real-Time Web Interface
- **Chart-based editor**: Visualize 24-hour schedule on interactive graph
- **Drag-to-edit**: Modify brightness by dragging points on chart
- **Live status**: Real-time temperature, current time, active schedule feedback
- **Test mode**: Manually override channels (60-second safety timeout) for instant verification
- **Responsive design**: Works on mobile, tablet, and desktop browsers
- **Zero configuration**: Access via ESP8266's IP address (e.g., `192.168.0.8`)

### 3. Temporary Lighting Overrides (Macros)
- **What are macros?**: Pre-saved lighting patterns that temporarily replace your schedule
- **Use cases**:
  - "Movie Mode": Dim all lights to 0% for 2 hours
  - "Feeding Mode": Spike blue channel to 100% for 30 minutes
  - "Cleaning Mode": Full white light for 1 hour
- **Duration-based**: Set how long macro stays active; automatically restores previous schedule
- **Easy access**: One-click activation from web UI
- **Custom creation**: Wizard guides you to design new macros

### 4. Optional Features
- **Temperature monitoring**: Real-time water temperature display via DS18B20 sensor
- **Over-the-air updates**: Update firmware via WiFi (no USB cable required)
- **System diagnostics**: View heap memory, CPU frequency, uptime
- **Fallback modes**: Reverts to access point if WiFi unavailable

---

## User Workflows

### Creating a Schedule
1. Open web interface → "Schedule" tab
2. Click "Add Target" or drag on chart
3. Set time (HH:MM format) and brightness (0-100%)
4. Targets auto-sort by time
5. "Save" writes to SD card and activates immediately
6. Changes persist across power loss

### Activating a Macro
1. Open web interface → "Macros" tab
2. Choose pre-saved macro (e.g., "Movie Mode")
3. Click "Activate" → macro runs for its duration
4. Countdown timer shows remaining time
5. When expired, schedule automatically resumes
6. Can manually "Stop" macro early

### Creating a Custom Macro
1. Click "Create Macro" button
2. Enter name (e.g., "Concert Lighting")
3. Set duration (HH:MM format)
4. Design pattern for each channel (same UI as schedule)
5. Save → macro stored permanently
6. Appears in macro list for future use

### Testing Lighting Instantly
1. Open web interface → "Test Mode" tab
2. Adjust brightness sliders for each channel
3. Changes apply immediately (no 60-second ramp)
4. Auto-exits after 60 seconds (prevents accidental permanent override)
5. Returns to scheduled behavior

---

## Technical Specifications

### System Specifications
| Feature | Specification |
|---------|---|
| Channels | 16 PWM outputs (6 managed by UI, 16 by firmware) |
| Resolution | 12-bit (0-4095 levels) |
| Frequency | 300Hz PWM carrier |
| Memory | 160KB RAM (50-55% used at runtime) |
| Storage | SD card (configs + schedules) |
| Connectivity | WiFi 802.11b/g/n (2.4GHz) |
| Access | Web browser (no app required) |
| Authentication | IP-based (private network) |

### Supported Hardware
- **Microcontroller**: ESP8266 (NodeMCU v2 recommended)
- **PWM Driver**: Adafruit PCA9685 (16-channel I2C expander)
- **Clock**: DS3231 RTC module (I2C)
- **Temperature** (optional): DS18B20 (1-Wire)
- **SD Card**: Standard SD module (SPI interface)

### API Endpoints
- `GET /api/status` → Current time, temp, macro state
- `GET /api/schedule/get?channel=N` → Channel targets
- `POST /api/schedule/save` → Persist targets to SD
- `POST /api/test/start|update|exit` → Manual override mode
- `GET/POST /api/macro/*` → Create, activate, stop, delete macros

---

## User Benefits

### For Aquarium Hobbyists
- **Natural simulation**: Automate realistic sunrise/sunset patterns
- **Fish health**: Consistent lighting reduces stress, improves coloration
- **Plant growth**: Customizable light curves optimize photosynthesis
- **Energy savings**: Program lights off during sleeping hours
- **Peace of mind**: Lights run automatically, no daily manual adjustments

### For Professional Environments
- **Reproducibility**: Save and replay exact lighting sequences across tanks
- **Integration**: Adjustable via simple HTTP API (extendable to home automation)
- **Diagnostics**: Real-time temperature and system health monitoring
- **Reliability**: Persistent schedules survive power loss

---

## Limitations

### Hardware
- Maximum 16 channels (UI currently shows 6)
- Requires 5V power supply for PCA9685 (separate from 3.3V ESP8266)
- WiFi range: Standard 802.11 (~50m open air)

### Software (Current Version 0.5.001)
- No manual time-setting (RTC must be set via Arduino bootloader)
- Macro timer not yet active (activation endpoint is stub)
- No timezone/DST support (always UTC)
- No user authentication (assumes trusted private network)
- Only local HTTP (no HTTPS)

### Future Enhancements
- Macro timer implementation (Phase 2)
- Time-setting API + UI (Phase 2)
- Timezone support (Phase 3)
- User authentication (Phase 4)
- Gradients and animations (Phase 5)

---

## Getting Started

### Installation (20 minutes)
1. Flash firmware to ESP8266 via USB (PlatformIO CLI)
2. Configure WiFi credentials in `config/wlan.cfg`
3. Insert SD card with config files
4. Power on → join network → visit ESP8266 IP in browser

### First Schedule (5 minutes)
1. Open web interface
2. Click "Schedule" → "Add Target"
3. Set 08:00 @ 50% brightness
4. Set 20:00 @ 0% brightness
5. Save → schedule active

See [QUICKSTART.md](QUICKSTART.md) for step-by-step guide.

---

## Support & Feedback

- **Documentation**: [README.md](README.md), [ARCHITECTURE.md](ARCHITECTURE.md), [TESTING_GUIDE.md](TESTING_GUIDE.md)
- **Issues**: GitHub Issues (for development tracking)
- **Code**: Open-source, available for modification
