# 🚀 Quick Test Guide

## Start the Mock Server

```powershell
cd j:\Sciebo\Dokumente\Hobbys\Aquarium\Schaltung\SBAquaControl\test
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python mock_server.py
```

You should see:
```
Mock Aquarium Control Server
Serving on http://localhost:5000
Open http://localhost:5000/app.htm in your browser
```

## Open the Interface

1. Open your browser to: **http://localhost:5000/app.htm**
2. You should see the full interface with:
   - 📊 Interactive Chart showing 24-hour schedule
   - 🎚️ Six channel sliders (Blau, Weiß, Rot, Grün, UV, Mondlicht)
   - ⚡ Test Mode button
   - 🎬 Macro section

## Test the Features

### Test Slider Response (Your Question!)

1. Click "⚡ Test-Modus starten"
2. Move any slider
3. Watch the console (F12 → Console tab)
4. You'll see: `✅ Test update sent: Channel X = Y%`

**Result:** Updates are sent **150ms after you stop moving the slider**
- Visual feedback: Instant (slider moves immediately)
- Network request: Debounced (waits 150ms)
- Light change: Would happen ~150-300ms total on real hardware

### Test Schedule Editing

1. Move sliders to desired values
2. Select a time (e.g., 12:00)
3. Click "Aktuelle Werte zu dieser Zeit speichern"
4. Watch the graph update with new point

### Test Macros

1. Click "➕ Neues Makro erstellen"
2. Enter name "Film-Modus" and duration "2 hours"
3. Click "Weiter"
4. Adjust sliders to set light pattern (e.g., all at 5%)
5. Click "💾 Makro speichern"
6. Click the macro card to activate it
7. Watch the countdown timer!

## Console Debugging

Open browser console (F12) to see:
- 🚀 Initialization messages
- ✅ Successful API calls
- ❌ Any errors
- Network timing

Example output:
```
🚀 Initializing Aquarium Control...
📥 Loading schedules...
✅ Schedules loaded
📥 Loading macros...
✅ 2 macros loaded
✅ Initialization complete
✅ Test update sent: Channel 0 = 50%
```

## Performance Check

1. Open DevTools → Network tab
2. Move a slider
3. Look for POST to `/api/test/update`
4. Check timing:
   - **Waiting (TTFB)**: Should be < 50ms (mock server)
   - **Real ESP8266**: Would be ~100-200ms on WiFi

## Next Steps

Once satisfied with the UI:
1. Implement JSON API endpoints in Webserver.cpp
2. Upload to ESP8266 via USB
3. Test with real hardware!

---

## Troubleshooting

**Problem:** Page doesn't load  
**Solution:** Make sure mock server is running on port 5000

**Problem:** Sliders don't work  
**Solution:** Check browser console for JavaScript errors

**Problem:** Chart doesn't show  
**Solution:** Ensure Chart.js CDN is accessible (requires internet)

**Offline Alternative:** Download Chart.js to extras/SDCard/js/chart.min.js
