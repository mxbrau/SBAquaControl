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

- **[PRODUCT.md](PRODUCT.md)** - Feature overview and user workflows
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and technical details
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development guidelines and build process
- **[docs/reference/QUICK_REFERENCE.md](docs/reference/QUICK_REFERENCE.md)** - Command cheat sheet and quick lookup
- **[docs/status/FIRMWARE_STATUS.md](docs/status/FIRMWARE_STATUS.md)** - Current implementation status
- **[docs/status/ROADMAP.md](docs/status/ROADMAP.md)** - Future development plans
- **[docs/status/TESTING_GUIDE.md](docs/status/TESTING_GUIDE.md)** - Comprehensive test suite

---

## 🔧 Hardware Setup

Der Verdrahtungsplan liegt als Fritzing Projekt im Ordner `extras/Circuit/SBAQC_1.0.fzz`.

For detailed hardware specifications, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 📝 Changelog

### 2017-12-10 Build 0.5.001
- Testmodus hinzugefügt: In der Weboberfläche gibt es einen Testmodus. Man kann für jeden Kanal einen Wert eingeben und auf "Testmodus aktivieren" klicken. Die Steuerung stellt die Lichtkanäle anschließend auf diese Werte ein. Der Testmodus kann über die Schaltfläche "Testmodus deaktivieren" verlassen werden. Der Testmodus bleibt maximal 60 Sekunden lang aktiviert.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Version**: 0.5.001  
**Last Updated**: 2026-01-02
