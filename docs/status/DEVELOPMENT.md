# SBAquaControl Development Setup Guide

## Quick Start

### 1. Install PlatformIO (One-Time Setup)

**Option A: VS Code Extension (Recommended)**
1. Open VS Code
2. Install extension: "PlatformIO IDE" 
3. Restart VS Code
4. Done! PlatformIO is ready

**Option B: Command Line**
```powershell
pip install platformio
```

### 2. UI Development (No Hardware Needed)

Develop the web interface on your PC without touching the ESP8266:

```powershell
# Install dependencies
cd test
pip install -r requirements.txt

# Run mock server
python mock_server.py

# Open browser to http://localhost:5000
# Edit HTML/JS files in extras/SDCard/
# Refresh browser to see changes
```

**Fast iteration loop:**
1. Edit `extras/SDCard/app.htm` or `app.js`
2. Save file
3. Refresh browser
4. Repeat!

### 3. First ESP8266 Upload (USB Required - One Time Only)

**Connect ESP8266 via USB, then:**

```powershell
# In project root folder
pio run -e esp8266 --target upload

# Or in VS Code:
# 1. Click PlatformIO icon (alien head) in left sidebar
# 2. Click "Upload" under esp8266 environment
```

**Note your ESP8266's IP address from Serial Monitor - you'll need it for OTA!**

### 4. Enable OTA Updates (Update via WiFi!)

After first USB upload, you can update wirelessly:

**Step 1: Edit platformio.ini**
```ini
[env:esp8266_ota]
upload_port = 192.168.1.XXX  ; Replace with YOUR ESP8266's IP
```

**Step 2: Upload via WiFi**
```powershell
# ESP8266 stays in aquarium!
pio run -e esp8266_ota --target upload

# Or in VS Code: Select "esp8266_ota" environment, click Upload
```

**Benefits:**
- ✅ No physical access needed
- ✅ Aquarium stays lit
- ✅ Upload takes ~10 seconds
- ✅ Update from anywhere on your network

---

## Development Workflow

### Phase 1: UI Development (Days 1-3)
**Hardware:** None needed
**Location:** Your desk

```
1. Run mock server: python test/mock_server.py
2. Open http://localhost:5000
3. Create/edit HTML/JavaScript files
4. Test in browser
5. Repeat until UI is perfect
```

### Phase 2: Backend API (Day 4)
**Hardware:** ESP8266 on USB (desk)
**Location:** Your desk

```
1. Connect ESP8266 to PC
2. Add API endpoints to Webserver.cpp
3. Upload via USB: pio run -e esp8266 -t upload
4. Test API with browser/Postman
5. Monitor Serial output for debugging
6. Iterate quickly
```

### Phase 3: OTA Testing (Day 5)
**Hardware:** ESP8266 in aquarium
**Location:** ESP in aquarium, you at desk

```
1. Install ESP8266 in aquarium (first upload via USB has OTA enabled)
2. Note IP address
3. All future updates via WiFi!
4. Make changes to code
5. Upload via OTA: pio run -e esp8266_ota -t upload
6. Test and iterate
```

---

## OTA Update Details

### How OTA Works

1. ESP8266 runs a small web server for receiving firmware
2. You send new firmware via WiFi
3. ESP8266 updates itself and reboots
4. Total downtime: ~15 seconds
5. If update fails, ESP8266 keeps running old version (safe!)

### Security

OTA is password-protected:
```cpp
// In your sketch setup():
ArduinoOTA.setPassword("aquarium123");  // Change this!
```

### Troubleshooting OTA

**Problem:** OTA upload fails with "No response from device"

**Solutions:**
1. Check ESP8266 IP address hasn't changed
2. Ensure ESP8266 and PC on same WiFi network
3. Check firewall isn't blocking port 3232
4. Verify OTA password matches

**Problem:** Upload successful but changes not visible

**Solution:** Hard refresh browser (Ctrl+F5) to clear cache

---

## File Organization

```
SBAquaControl/
├── platformio.ini           # PlatformIO configuration (OTA settings here)
├── test/
│   ├── mock_server.py       # Run this for UI development
│   └── requirements.txt     # Python dependencies
├── src/
│   ├── AquaControl.h        # Main controller
│   ├── AquaControl.cpp      # Implementation
│   └── Webserver.cpp        # API endpoints (ADD OTA CODE HERE)
├── extras/
│   └── SDCard/
│       ├── app.htm          # NEW: Modern web interface (CREATE THIS)
│       ├── js/
│       │   └── app.js       # NEW: JavaScript logic (CREATE THIS)
│       └── css/
│           └── app.css      # NEW: Styling (CREATE THIS)
└── examples/
    └── AquaControlSketch/
        └── AquaControlSketch.ino  # Example sketch
```

---

## Common Commands

```powershell
# UI Development (no hardware)
python test/mock_server.py

# First upload (USB required)
pio run -e esp8266 -t upload

# Monitor serial output
pio device monitor

# Upload via WiFi (after first upload)
pio run -e esp8266_ota -t upload

# Clean build
pio run -t clean

# Build without uploading
pio run -e esp8266

# Update libraries
pio lib update
```

---

## Next Steps

1. **Install PlatformIO** (if not already done)
2. **Start mock server:** `python test/mock_server.py`
3. **Create basic UI:** We'll create `app.htm` together
4. **Test in browser:** Develop entire UI without hardware
5. **One USB upload:** Enable OTA for future updates
6. **Iterate wirelessly:** All future updates via WiFi!

Ready to create the web interface?
