# SBAquaControl

Schullebernd Aqua Control ist eine WLAN Aquarium Lichtsteuerung (Tageslichtsimulation) für LED Beleuchtungen.

Eine komplette Beschreibung zum Aufbau der Steuerung sowie zum Selbstbau einer Aquarium LED Beleuchtung ist auf http://schullebernd.de/ zu finden.

---

## 🚀 Quick Start

### Prerequisites

- **VS Code** with **PlatformIO IDE** extension
- **Python 3.8+** (for UI development with mock server)
- ESP8266 module (for hardware deployment)

### Installation

1. **Install PlatformIO in VS Code**
   - Open VS Code
   - Go to Extensions (Ctrl+Shift+X)
   - Search for "PlatformIO IDE"
   - Click Install
   - Restart VS Code

2. **Clone the Repository**
   ```bash
   git clone https://github.com/mxbrau/SBAquaControl.git
   cd SBAquaControl
   ```

3. **Install Python Dependencies** (for UI development)
   ```bash
   cd test
   pip install -r requirements.txt
   ```

### Development Workflow

#### Option A: UI Development (No Hardware Required)

Start the mock server to develop the web interface without an ESP8266:

```bash
cd test
python mock_server.py
```

Then open your browser to http://localhost:5000

This allows you to develop and test the web UI, create HTML/JavaScript files, and test API endpoints without hardware.

#### Option B: Firmware Development

1. **First Upload via USB**
   ```bash
   pio run -e esp8266 --target upload
   pio device monitor
   ```

2. **Enable OTA for Wireless Updates**
   
   After the initial USB upload, you can update the firmware wirelessly:
   ```bash
   pio run -e esp8266_ota --target upload
   ```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed build instructions and development guidelines.

---

## 📚 Documentation

**Quick Navigation**: See [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for a complete guide to all documentation.

### Core Documentation
- **[PRODUCT.md](PRODUCT.md)** - Feature overview and user workflows
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and technical details
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development guidelines and build process

### Reference & Status
- **[docs/reference/QUICK_REFERENCE.md](docs/reference/QUICK_REFERENCE.md)** - Command cheat sheet and API reference
- **[docs/status/FIRMWARE_STATUS.md](docs/status/FIRMWARE_STATUS.md)** - Current implementation status
- **[docs/status/ROADMAP.md](docs/status/ROADMAP.md)** - Future development plans
- **[docs/status/TESTING_GUIDE.md](docs/status/TESTING_GUIDE.md)** - Comprehensive test suite

---

## 🔧 Hardware Setup

Der Verdrahtungsplan liegt als Fritzing Projekt im Ordner `extras/Circuit/SBAQC_1.0.fzz`.

For detailed hardware specifications, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 📝 Current Status

**Version**: 0.5.001  
**Last Updated**: 2026-01-05

### Implemented Features
- ✅ **24-hour LED Schedule Automation** - Linear interpolation between targets
- ✅ **Web Interface** - Modern single-page app with Chart.js visualization
- ✅ **Macro System** - Temporary lighting overrides with timer support
- ✅ **Hybrid Time Sync** - NTP → RTC → API fallback system
- ✅ **Test Mode** - Manual channel control (60-second timeout)
- ✅ **Temperature Monitoring** - Optional DS18B20 sensor support
- ✅ **OTA Updates** - Wireless firmware updates via WiFi
- ✅ **Memory Optimized** - 50-55% RAM usage on ESP8266

### Known Limitations
- Linear interpolation only (no smooth curves)
- Maximum 32 targets per channel
- No timezone/DST support (UTC only)
- No user authentication (assumes trusted network)

See [ROADMAP](docs/status/ROADMAP.md) for planned enhancements.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
