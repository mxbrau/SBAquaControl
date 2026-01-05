# Macro CRUD/Activation Fix - Testing Guide

## Summary of Changes

This implementation fixes macro activation UI feedback issues and NaN duration display by adding proper metadata to API endpoints.

### Backend Changes (C++)

1. **New Helper Function: `computeMacroDuration()`**
   - Scans all 16 PWM channels to find maximum target time
   - Returns duration in seconds (0 if no macro files found)
   - Provides fallback name (defaults to macroId)

2. **Updated API Endpoints:**
   - `/api/macro/list` - Now includes `duration` and `name` fields
   - `/api/macro/get` - Now includes `duration` and `name` fields
   - `/api/macro/save` - Returns computed `duration` in response
   - `/api/macro/activate` - Validates duration, computes from files if missing

3. **Added Safety Guards:**
   - `AquaControl::activateMacro()` rejects zero duration
   - `/api/macro/activate` validates duration before activation
   - Buffer overflow protection using `snprintf()` and streaming

### Frontend Changes (JavaScript)

1. **Simplified `loadMacros()`:**
   - Removed N+1 API query pattern (was calling getMacro for each item)
   - Now uses duration from list response directly
   - Fixes NaN display in macro cards
   - Improves performance significantly

## Manual Testing Checklist

### Prerequisites
- ESP8266 device with firmware uploaded
- SD card inserted with macros/ directory
- Web browser connected to device WiFi
- Serial monitor open (optional, for debugging)

### Test 1: Macro Creation
**Objective:** Verify new macros display duration correctly

1. Open web UI at `http://192.168.x.x/app.htm`
2. Navigate to Macros tab
3. Click "Create Macro" button
4. Enter name: "Test Macro"
5. Set duration: 2 hours 30 minutes
6. Add some channel targets in step 2
7. Click "Save"
8. **Expected:** Macro card shows "2h 30min" (not "NaN min")
9. **Verify in serial:** `✅ Macro saved: macro_001`

### Test 2: Macro Activation
**Objective:** Verify macro activates and UI reflects active state

1. Click on the macro card created in Test 1
2. **Expected:** 
   - Macro banner appears at top of page
   - Countdown timer starts from "2:30:00"
   - Serial log shows: `🎬 Macro activated: macro_001, duration: 9000s`
3. Observe channels change to macro targets
4. **Verify in browser DevTools:**
   - Check Network tab for `/api/status` requests
   - Response should include: `"macro_active":true,"macro_expires_in":8999,"macro_id":"macro_001"`

### Test 3: Macro Auto-Restore (Short Test)
**Objective:** Verify macro auto-restores after duration expires

1. Create a macro with 1 minute duration
2. Activate the macro
3. Wait 60 seconds
4. **Expected:**
   - Channels restore to regular schedule
   - Macro banner disappears
   - Serial log shows: `✅ Macro auto-restored`
   - Next `/api/status` shows: `"macro_active":false`

### Test 4: Manual Macro Stop
**Objective:** Verify manual stop functionality

1. Activate a macro with long duration (e.g., 1 hour)
2. Wait 10 seconds
3. Click "Stop" button in macro banner
4. **Expected:**
   - Channels immediately restore to regular schedule
   - Macro banner disappears
   - Serial log shows: `🛑 Macro stopped manually`

### Test 5: Macro Editing
**Objective:** Verify macro editing preserves duration

1. Click "Edit" button on existing macro
2. **Expected:** 
   - Wizard opens with correct name
   - Duration fields show correct hours/minutes
   - Chart loads with existing targets
3. Change a channel target
4. Click "Save"
5. **Expected:**
   - Macro card updates (duration should remain correct)
   - Serial log shows: `✅ Macro saved: macro_XXX`

### Test 6: Edge Cases

#### Test 6a: Activation with Missing Duration (Backend Fallback)
**Note:** This requires simulating a client that doesn't send duration

1. Use browser DevTools Console:
   ```javascript
   fetch('/api/macro/activate', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({id: 'macro_001'})  // No duration field
   }).then(r => r.json()).then(console.log)
   ```
2. **Expected:** Backend computes duration from files and activates macro
3. Check serial log for activation confirmation

#### Test 6b: Activation with Zero Duration
**Note:** This should be rejected by backend

1. Use browser DevTools Console:
   ```javascript
   fetch('/api/macro/activate', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({id: 'macro_001', duration: 0})
   }).then(r => r.json()).then(console.log)
   ```
2. **Expected:** HTTP 400 error with `{"error":"Invalid duration"}`
3. Serial log shows: `❌ Macro activation failed: duration is 0`

#### Test 6c: Overlapping Macro Activation
1. Activate macro A
2. Immediately try to activate macro B
3. **Expected:** 
   - UI shows confirmation dialog: "Ein Makro ist bereits aktiv. Trotzdem wechseln?"
   - If user cancels, macro A continues
   - If user confirms, backend rejects (only one macro allowed)

### Test 7: Performance Test
**Objective:** Verify UI loads macros quickly

1. Create 5-10 macros with various durations
2. Reload the page
3. Navigate to Macros tab
4. **Expected:**
   - All macros load within 2 seconds
   - No "NaN min" displays
   - Browser DevTools Network tab shows only ONE `/api/macro/list` call (not N+1 queries)

## Security Verification

### Buffer Overflow Protection
**Verified in code review:**
- ✅ All `sprintf()` calls replaced with `snprintf()` where user input is involved
- ✅ Buffer sizes reduced to appropriate minimums (16 bytes for uint32_t)
- ✅ User-controlled strings streamed via `sendContent()` instead of buffered

### Input Validation
**Verified in code:**
- ✅ Zero duration rejected in `activateMacro()`
- ✅ Missing macroId returns HTTP 400
- ✅ Macro file existence checked before reading

## Known Limitations

1. **Physical Testing Required:** This implementation cannot be fully validated without physical ESP8266 hardware and SD card
2. **No C++ Unit Tests:** Project lacks embedded test infrastructure; validation is manual only
3. **Duration Persistence:** Macro timer state does NOT persist across power loss (by design)
4. **Single Active Macro:** Only one macro can be active at a time

## Rollback Plan

If issues are discovered:
1. Revert commits in reverse order:
   ```bash
   git revert b25934d  # Security fixes
   git revert 712646b  # UI simplification
   git revert f47f889  # Backend metadata
   ```
2. Redeploy previous working version
3. Investigate issue in development environment

## Next Steps

After manual testing passes:
1. Document any discovered issues
2. Create follow-up tasks for any edge cases
3. Consider adding integration tests using Python mock server
4. Update user documentation with macro duration behavior

## Contact

For issues or questions about this implementation, please refer to:
- Implementation plan: `.github/plans/macro-crud-fix-plan.md`
- Original plan: `.github/plans/step-04-macro-timer-system.md`
