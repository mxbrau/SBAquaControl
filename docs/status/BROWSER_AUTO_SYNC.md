# Browser Auto-Sync Time Feature

**Status**: ✅ IMPLEMENTED  
**Last Updated**: January 5, 2026

## Overview
When NTP sync fails (e.g., router NTP not configured), the ESP8266 signals the browser to automatically provide the current time via the `/api/status` endpoint's `needs_time_sync` flag.

**Current Status**: This feature is fully functional in v0.5.001. The web UI automatically syncs time when needed.

## How It Works

### Backend (ESP8266)
1. During boot, if NTP sync fails, `_NtpSyncFailed` flag is set to `true`
2. `/api/status` returns `"needs_time_sync": true` when this flag is set
3. When browser calls `/api/time/set`, the flag is cleared to `false`

### Frontend (Browser/JavaScript)
The browser needs to:
1. Poll `/api/status` periodically (e.g., every 5-10 seconds)
2. Check if `needs_time_sync` is `true`
3. If true, automatically POST current browser time to `/api/time/set`

## Implementation Example

### JavaScript Auto-Sync Function

Add this to your web UI (e.g., `extras/SDCard/app.htm`):

```javascript
// Check if device needs time sync and automatically provide it
async function checkAndSyncTime() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        // If device needs time sync, send browser time
        if (status.needs_time_sync === true) {
            console.log('Device needs time sync, sending browser time...');
            await sendBrowserTime();
        }
    } catch (error) {
        console.error('Error checking time sync status:', error);
    }
}

// Send browser's current time to the device
async function sendBrowserTime() {
    const now = new Date();
    const timeData = {
        hour: now.getHours(),
        minute: now.getMinutes(),
        second: now.getSeconds()
    };
    
    try {
        const response = await fetch('/api/time/set', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(timeData)
        });
        
        const result = await response.json();
        console.log('Time sync result:', result);
        
        if (response.ok) {
            console.log('✅ Browser auto-synced time to device');
            // Optionally show a notification to the user
            showNotification('Time synchronized from browser');
        }
    } catch (error) {
        console.error('Error syncing time:', error);
    }
}

// Start checking for time sync needs every 10 seconds
setInterval(checkAndSyncTime, 10000);

// Also check immediately on page load
checkAndSyncTime();
```

### API Response Examples

#### Status when NTP failed
```json
{
  "time_source": "unknown",
  "rtc_present": true,
  "time_valid": false,
  "needs_time_sync": true,
  "last_sync_ts": 0
}
```

#### Status after browser sync
```json
{
  "time_source": "api",
  "rtc_present": true,
  "time_valid": true,
  "needs_time_sync": false,
  "last_sync_ts": 1735862445
}
```

## Workflow Diagram

```
Boot Sequence:
┌─────────────────┐
│ Try NTP Sync    │
│ (192.168.103.1) │
└────────┬────────┘
         │
         ├─ Success ──> _NtpSyncFailed = false
         │              needs_time_sync = false
         │
         └─ Failed ───> _NtpSyncFailed = true
                        needs_time_sync = true
                        ↓
                  Try RTC Sync
                        ↓
                  ┌─────────────┐
                  │ time_valid? │
                  └─────┬───────┘
                        │
                  ├─ Yes ──> Use RTC time
                  │          needs_time_sync = true (still)
                  │
                  └─ No ───> Wait for browser
                             ↓
                       Browser polls /api/status
                             ↓
                       Sees needs_time_sync = true
                             ↓
                       Auto POST to /api/time/set
                             ↓
                       _NtpSyncFailed = false
                       needs_time_sync = false
                       time_source = "api"
```

## User Experience

### Scenario 1: Router NTP Working
1. Device boots
2. NTP sync succeeds
3. Browser shows normal UI
4. No action required

### Scenario 2: Router NTP Not Configured
1. Device boots
2. NTP sync fails (timeout after 2 seconds)
3. Falls back to RTC (if available)
4. Browser detects `needs_time_sync: true`
5. **Browser automatically sends current time** (no user interaction needed)
6. Device time updated, flag cleared
7. UI shows "Time synchronized from browser" notification

### Scenario 3: No RTC, NTP Failed
1. Device boots
2. NTP sync fails
3. No RTC available
4. `time_valid: false`, `needs_time_sync: true`
5. Browser automatically provides time
6. System operates normally with browser-synced time

## Benefits

1. **Zero User Intervention**: Time syncs automatically when NTP fails
2. **Seamless Fallback**: User doesn't need to know which sync method worked
3. **Always Accurate**: Browser time is usually accurate (synced from OS)
4. **Network Isolation**: Works even without router NTP or internet access
5. **Visual Feedback**: UI can show which sync method was used

## Configuration

No configuration needed! The feature works automatically when:
- `USE_NTP` is defined in firmware
- NTP sync fails during boot
- Browser polls `/api/status` endpoint

## Testing

1. **Test NTP Failure Auto-Sync**:
   - Disable router NTP or use invalid NTP server IP
   - Boot device with `USE_NTP` enabled
   - Open web UI in browser
   - Verify browser automatically syncs time within 10 seconds
   - Check `/api/status` shows `time_source: "api"` and `needs_time_sync: false`

2. **Test Flag Clearing**:
   - After auto-sync, reboot device
   - Verify `needs_time_sync` starts as `true` (NTP still fails)
   - Verify browser auto-syncs again
   - Confirm flag clears after sync

3. **Test Manual Override**:
   - Even with auto-sync enabled, manual time setting via UI should work
   - Flag should clear after manual sync too

## Notes

- Browser time depends on device clock accuracy (PC/phone/tablet)
- First sync happens within 10 seconds of page load
- Periodic checks ensure time stays current
- Flag persists across page refreshes until time is synced
- Works with any browser (Chrome, Firefox, Safari, Edge)
- No external dependencies required

## Future Enhancements

- Add visual indicator in UI when auto-sync is triggered
- Allow user to disable auto-sync via settings
- Add timestamp of last browser sync
- Support date setting (currently time-only)
- Add retry logic if POST fails
