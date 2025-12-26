# Quick Start - Get Developing in 5 Minutes

## Step 1: Install Tools (2 minutes)

### Install PlatformIO in VS Code
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "PlatformIO IDE"
4. Click Install
5. Restart VS Code

### Install Python Dependencies
```powershell
cd j:\Sciebo\Dokumente\Hobbys\Aquarium\Schaltung\SBAquaControl
cd test
pip install -r requirements.txt
```

---

## Step 2: Start UI Development (1 minute)

### Run Mock Server
```powershell
# In j:\Sciebo\Dokumente\Hobbys\Aquarium\Schaltung\SBAquaControl\test
python mock_server.py
```

You should see:
```
============================================================
  SBAquaControl Mock API Server
============================================================
  URL: http://localhost:5000
  Press Ctrl+C to stop
============================================================
```

### Open Browser
Navigate to: **http://localhost:5000**

*Note: We haven't created app.htm yet, so you'll see an error. That's our next step!*

---

## Step 3: Create Your First UI File (2 minutes)

Create **extras/SDCard/app.htm** with this minimal starter:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Aquarium Control</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
    <h1>🐠 Aquarium Light Control</h1>
    <p>Temperature: <span id="temp">--</span>°C</p>
    <p>Time: <span id="time">--:--:--</span></p>
    
    <button onclick="testAPI()">Test API Connection</button>
    <div id="output"></div>
    
    <script>
        async function testAPI() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                document.getElementById('temp').textContent = data.temperature;
                document.getElementById('time').textContent = data.current_time;
                document.getElementById('output').innerHTML = 
                    '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                
                alert('API works! ✓');
            } catch (error) {
                alert('API Error: ' + error);
            }
        }
        
        // Auto-update time every second
        setInterval(async () => {
            const response = await fetch('/api/status');
            const data = await response.json();
            document.getElementById('time').textContent = data.current_time;
        }, 1000);
    </script>
</body>
</html>
```

### Test It!
1. Save the file
2. Refresh browser (http://localhost:5000)
3. Click "Test API Connection"
4. You should see JSON data!

---

## Development is Now Active! 🎉

**You can now:**
- Edit HTML/JavaScript files
- Refresh browser to see changes
- Use browser DevTools (F12) for debugging
- Test API endpoints without hardware

---

## What's Next?

### Option A: Build the Full UI (Recommended First)
1. Create modern interface with Chart.js
2. Add sliders for manual control
3. Test everything in browser
4. **No ESP8266 needed yet!**

### Option B: Enable OTA on Your ESP8266
1. Connect ESP8266 via USB (one time)
2. Upload code with OTA enabled
3. Install ESP in aquarium
4. All future updates via WiFi!

**Which path would you like to take?**
- Say "UI first" and I'll create the complete web interface
- Say "OTA first" and I'll help you set up wireless updates

---

## Troubleshooting

**Mock server won't start:**
```powershell
# Make sure you're in the test folder
cd test
python mock_server.py
```

**Browser shows "Can't GET /":**
- The app.htm file doesn't exist yet (create it above!)
- Or it's in the wrong folder (should be extras/SDCard/app.htm)

**API calls fail:**
- Mock server not running? Check the terminal
- Wrong URL? Should be http://localhost:5000

**PlatformIO not showing up in VS Code:**
- Restart VS Code after installation
- Check Extensions panel - it should show "PlatformIO IDE"

---

## Current Status

✅ PlatformIO configured (platformio.ini)  
✅ Mock API server ready (test/mock_server.py)  
✅ OTA support added to ESP8266 code  
⏳ Web interface (create extras/SDCard/app.htm)  
⏳ ESP8266 first upload (when ready)  

**You're ready to start development!**
