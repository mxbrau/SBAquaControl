---
title: Macro Timer System - Critical Bug Fix
version: 1.0
date_created: 2026-01-02
last_updated: 2026-01-02
---

# Implementation Plan: Macro Timer System

## Overview
This plan implements macro activation, timer tracking, and automatic schedule restoration to fix the stubbed `handleApiMacroActivate()` and `handleApiMacroStop()` endpoints. Currently, macros can be created and saved but cannot be executed—clicking "Activate" does nothing. This feature enables users to run temporary lighting overrides (e.g., "Movie Mode", "Feeding Time") that automatically revert to the regular schedule after a specified duration.

**Critical Bug**: [Webserver.cpp#L1028](../../src/Webserver.cpp#L1028) and [Webserver.cpp#L1036](../../src/Webserver.cpp#L1036) are stub implementations with TODO comments.

---

## Requirements

### Functional Requirements
1. **Macro Activation**: When user clicks "Activate" on a macro via web UI, the system must:
   - Parse macro ID and channel from JSON request body
   - Load macro targets from SD card (`macros/macro_NNN_chNN.cfg`)
   - Replace current channel schedule with macro targets
   - Start countdown timer based on macro duration
   - Return success response with expiration timestamp

2. **Auto-Restore**: When macro duration expires, system must:
   - Automatically restore the original schedule for all affected channels
   - Clear macro state (mark as inactive)
   - Seamlessly transition back to regular lighting pattern

3. **Manual Stop**: User can manually stop an active macro before expiration:
   - Immediately restore original schedule
   - Clear macro state
   - Return success confirmation

4. **Status Reporting**: API `/api/status` endpoint must include:
   - Whether a macro is currently active
   - Time remaining until auto-restore (in seconds)
   - Active macro ID (for UI display)

### Non-Functional Requirements
- **Memory**: Macro state tracking must add <5KB RAM (store only essential state)
- **Response time**: API endpoints must respond in <200ms
- **Persistence**: Timer state does NOT persist across power loss (acceptable trade-off)
- **Non-blocking**: Auto-restore check must integrate into existing `proceedCycle()` pattern (<1ms overhead)
- **Channel support**: Must support all 16 PWM channels (though UI only displays 6)

---

## Architecture and Design

### High-Level Design

**Add MacroState struct to AquaControl class**:
```cpp
typedef struct {
    bool active;                     // Is a macro currently running?
    time_t startTime;                // Unix timestamp when macro was activated
    uint32_t duration;               // Macro duration in seconds
    char macroId[20];                // Macro identifier (e.g., "macro_001")
    Target originalTargets[PWM_CHANNELS][MAX_TARGET_COUNT_PER_CHANNEL]; // Backup of original schedules
    uint8_t originalTargetCounts[PWM_CHANNELS]; // Backup of original target counts
} MacroState;
```

**Modified/Created Functions**:
1. `AquaControl::_activeMacro` (member variable): Instance of MacroState struct
2. `AquaControl::proceedCycle()` (modified): Add macro expiration check after line 715
3. `AquaControl::activateMacro()` (new): Load macro, backup current schedule, apply macro targets
4. `AquaControl::restoreSchedule()` (new): Restore original targets from backup
5. `handleApiMacroActivate()` (implement stub): Parse request, call `activateMacro()`, respond with JSON
6. `handleApiMacroStop()` (implement stub): Call `restoreSchedule()`, respond with JSON
7. `handleApiStatus()` (modify): Add macro state fields to JSON response

### Key Algorithms

**Linear Interpolation Reference**: [AquaControl.cpp#L928-L1000](../../src/AquaControl.cpp#L928)
- Macro targets use same Target struct as regular schedules
- `PwmChannel::proceedCycle()` automatically handles interpolation
- No changes needed to interpolation logic

**Tick-Tock Async Reference**: [AquaControl.cpp#L750-L830](../../src/AquaControl.cpp#L750)
- Temperature sensor uses `_TickTock` flag and `_NextPossibleActivity` timestamp
- Macro timer follows similar pattern: check `now() - startTime > duration`

**File I/O Pattern Reference**: [Webserver.cpp#L800-L900](../../src/Webserver.cpp#L800) (macro save)
- Macros stored in `macros/macro_NNN_chNN.cfg` format (one file per channel)
- Format identical to regular schedule: `HH:MM:SS,VVV` lines (time, value pairs)
- Parse using same logic as `readLedConfig()`

### Design Decisions

**Why backup targets in MacroState instead of re-reading from SD?**
- **Speed**: Loading from SD during auto-restore adds ~50-100ms latency
- **Reliability**: Avoids SD card read failures during timer expiration
- **Memory trade-off**: ~3KB additional RAM (16 channels × 32 targets × 6 bytes) is acceptable

**Why no persistence across power loss?**
- **Complexity**: Requires saving state to SD on every second of macro execution
- **Wear**: SD cards have limited write cycles (~10,000-100,000)
- **Use case**: Macros are temporary overrides (30 min - 2 hours); power loss is rare

**Why single active macro instead of multiple?**
- **User experience**: Multiple overlapping macros would confuse users (which is active?)
- **Memory**: Supporting N concurrent macros multiplies memory cost by N
- **Future-proof**: Can extend to macro queue later if needed

**Why char buffer `macroId[20]` instead of String?**
- **Memory safety**: Prevents heap fragmentation from String concatenation
- **Consistency**: Matches project convention (see `sprintf()` pattern in Webserver.cpp)

---

## Implementation Tasks

### Phase 1: Data Structures and Initialization (Est. 45 min)

- [ ] Add `MacroState` struct definition to [AquaControl.h#L175](../../src/AquaControl.h#L175)
  - Location: After `WlanConfig` struct definition (line 174)
  - Fields: `active`, `startTime`, `duration`, `macroId[20]`, `originalTargets[][]`, `originalTargetCounts[]`
  - Use `#ifdef USE_WEBSERVER` guard (macros only work with web interface)

- [ ] Add `MacroState _activeMacro;` member to `AquaControl` class [AquaControl.h#L282](../../src/AquaControl.h#L282)
  - Location: After `WlanConfig _WlanConfig;` declaration
  - Initialize `_activeMacro.active = false` in constructor [AquaControl.h#L287](../../src/AquaControl.h#L287)

- [ ] Add helper method declarations to `AquaControl` class [AquaControl.h#L295](../../src/AquaControl.h#L295)
  ```cpp
  bool activateMacro(const String &macroId, uint32_t duration);
  void restoreSchedule();
  bool isMacroActive() const { return _activeMacro.active; }
  uint32_t getMacroTimeRemaining() const;
  ```

### Phase 2: Macro Activation Logic (Est. 90 min)

- [ ] Implement `AquaControl::activateMacro()` in [AquaControl.cpp#L1068](../../src/AquaControl.cpp#L1068) (end of file)
  - **Step 1**: Check if macro is already active (return false if true)
  - **Step 2**: Backup current schedules to `_activeMacro.originalTargets[][]` and `_activeMacro.originalTargetCounts[]`
    ```cpp
    for (uint8_t ch = 0; ch < PWM_CHANNELS; ch++) {
        _activeMacro.originalTargetCounts[ch] = _PwmChannels[ch].TargetCount;
        for (uint8_t t = 0; t < _PwmChannels[ch].TargetCount; t++) {
            _activeMacro.originalTargets[ch][t] = _PwmChannels[ch].Targets[t];
        }
    }
    ```
  - **Step 3**: Load macro targets from SD card for each channel
    - Iterate channels 0-15
    - Construct path: `char path[40]; sprintf(path, "macros/%s_ch%02d.cfg", macroId.c_str(), ch);`
    - If file exists, parse targets (reuse `readLedConfig()` pattern)
    - Replace `_PwmChannels[ch].Targets[]` with macro targets
  - **Step 4**: Set macro state
    ```cpp
    _activeMacro.active = true;
    _activeMacro.startTime = now();
    _activeMacro.duration = duration;
    strncpy(_activeMacro.macroId, macroId.c_str(), 19);
    _activeMacro.macroId[19] = '\0';
    ```
  - **Step 5**: Mark all channels for PWM update (`_PwmChannels[ch].HasToWritePwm = true`)
  - **Step 6**: Return true on success

- [ ] Implement `AquaControl::getMacroTimeRemaining()` in [AquaControl.cpp](../../src/AquaControl.cpp)
  - Return `0` if macro not active
  - Calculate: `uint32_t elapsed = now() - _activeMacro.startTime;`
  - Return: `(elapsed >= _activeMacro.duration) ? 0 : (_activeMacro.duration - elapsed);`

### Phase 3: Auto-Restore Functionality (Est. 60 min)

- [ ] Implement `AquaControl::restoreSchedule()` in [AquaControl.cpp](../../src/AquaControl.cpp)
  - **Step 1**: Check if macro is active (return early if not)
  - **Step 2**: Restore original targets for all channels
    ```cpp
    for (uint8_t ch = 0; ch < PWM_CHANNELS; ch++) {
        _PwmChannels[ch].TargetCount = _activeMacro.originalTargetCounts[ch];
        for (uint8_t t = 0; t < _activeMacro.originalTargetCounts[ch]; t++) {
            _PwmChannels[ch].Targets[t] = _activeMacro.originalTargets[ch][t];
        }
        _PwmChannels[ch].HasToWritePwm = true; // Force PWM update
    }
    ```
  - **Step 3**: Clear macro state
    ```cpp
    _activeMacro.active = false;
    _activeMacro.startTime = 0;
    _activeMacro.duration = 0;
    _activeMacro.macroId[0] = '\0';
    ```
  - **Step 4**: Log to serial: `Serial.println(F("✅ Macro auto-restored"));`

- [ ] Add macro expiration check to `AquaControl::proceedCycle()` [AquaControl.cpp#L720](../../src/AquaControl.cpp#L720)
  - Location: After `CurrentMilli = millis() % 1000;` (line 715), before channel loop (line 724)
  - Add code:
    ```cpp
    // Check macro expiration (non-blocking timer)
    #ifdef USE_WEBSERVER
    if (_activeMacro.active && getMacroTimeRemaining() == 0) {
        restoreSchedule();
    }
    #endif
    ```

### Phase 4: API Endpoint Implementation (Est. 75 min)

- [ ] Implement `handleApiMacroActivate()` in [Webserver.cpp#L1004](../../src/Webserver.cpp#L1004)
  - **Current state**: Stub with TODO comment at line 1028
  - **Replacement logic**:
    ```cpp
    // Parse macro id (already implemented, lines 1006-1022)
    String macroId = ...; // Keep existing parsing logic
    
    // Parse duration from JSON body
    int durIdx = body.indexOf("\"duration\":");
    uint32_t duration = 0;
    if (durIdx != -1) {
        int durStart = durIdx + 11;
        int durEnd = body.indexOf(',', durStart);
        if (durEnd == -1) durEnd = body.indexOf('}', durStart);
        duration = body.substring(durStart, durEnd).toInt();
    }
    
    // Activate macro
    extern AquaControl aqc; // Access global instance
    if (aqc.activateMacro(macroId, duration)) {
        // Build JSON response
        char response[100];
        sprintf(response, "{\"status\":\"ok\",\"expires_in\":%lu}", duration);
        _Server.send(200, "application/json", response);
        
        Serial.print(F("🎬 Macro activated: "));
        Serial.print(macroId);
        Serial.print(F(", duration: "));
        Serial.print(duration);
        Serial.println(F("s"));
    } else {
        _Server.send(500, "application/json", "{\"error\":\"Activation failed\"}");
    }
    ```

- [ ] Implement `handleApiMacroStop()` in [Webserver.cpp#L1032](../../src/Webserver.cpp#L1032)
  - **Current state**: Stub with TODO comment at line 1035
  - **Replacement logic**:
    ```cpp
    extern AquaControl aqc;
    if (aqc.isMacroActive()) {
        aqc.restoreSchedule();
        _Server.send(200, "application/json", "{\"status\":\"ok\"}");
        Serial.println(F("🛑 Macro stopped manually"));
    } else {
        _Server.send(400, "application/json", "{\"error\":\"No macro active\"}");
    }
    ```

- [ ] Update `handleApiStatus()` in [Webserver.cpp#L400-L500](../../src/Webserver.cpp#L400) to include macro state
  - **Location**: Find the JSON response building section (look for `_Server.sendContent()` calls)
  - **Add fields**:
    ```cpp
    // Add after temperature field (if present) or before closing brace
    extern AquaControl aqc;
    if (aqc.isMacroActive()) {
        char macroJson[100];
        sprintf(macroJson, ",\"macro_active\":true,\"macro_expires_in\":%lu,\"macro_id\":\"%s\"",
                aqc.getMacroTimeRemaining(), aqc._activeMacro.macroId);
        _Server.sendContent(macroJson);
    } else {
        _Server.sendContent(",\"macro_active\":false");
    }
    ```

### Phase 5: Testing and Validation (Est. 60 min)

- [ ] Build firmware: `pio run -e esp8266 --target upload`
  - Verify no compilation errors
  - Check memory usage (should increase by <5KB)

- [ ] Manual test: Macro activation
  - Open web UI at `http://192.168.x.x/app.htm`
  - Navigate to Macros section
  - Click "Activate" on pre-existing macro (if available, otherwise create one with 60-second duration)
  - **Expected**: Lights change immediately to macro pattern
  - **Verify**: Serial output shows `🎬 Macro activated: macro_XXX, duration: 60s`

- [ ] Manual test: Status API polling
  - Open browser DevTools → Network tab
  - Observe `/api/status` requests (every 2 seconds)
  - **Expected**: Response includes `"macro_active":true,"macro_expires_in":58,...`
  - **Verify**: `expires_in` value decreases each poll

- [ ] Manual test: Auto-restore (patience required)
  - Wait for macro duration to expire (60 seconds)
  - **Expected**: Lights automatically return to regular schedule
  - **Verify**: Serial output shows `✅ Macro auto-restored`
  - **Verify**: Next `/api/status` response includes `"macro_active":false`

- [ ] Manual test: Manual stop
  - Activate another macro (120-second duration)
  - Immediately click "Stop" button in UI
  - **Expected**: Lights instantly restore to regular schedule
  - **Verify**: Serial output shows `🛑 Macro stopped manually`

- [ ] Edge case test: Overlapping activation
  - Activate macro A (120-second duration)
  - Wait 10 seconds
  - Attempt to activate macro B
  - **Expected**: Macro B activation fails (only one active at a time)
  - **Verify**: Error response from API

- [ ] Edge case test: Power loss simulation (optional)
  - Activate macro
  - Power cycle ESP8266 (unplug/replug USB)
  - **Expected**: After reboot, regular schedule is active (macro state lost)
  - **Verify**: No errors in serial log

---

## Testing Strategy

### Unit Tests
**Note**: SBAquaControl does not currently have unit test infrastructure. Manual testing is primary validation method.

- **Timestamp comparison logic** (validate in `getMacroTimeRemaining()`)
  - Edge case: `now()` wraps at day boundary (Unix timestamp increases, should not affect logic)
  - Edge case: Duration = 0 seconds (should expire immediately)

- **Target restoration logic** (validate in `restoreSchedule()`)
  - Ensure all 16 channels are restored, not just first 6
  - Verify `TargetCount` and `Targets[]` arrays match pre-activation state

### Integration Tests

**End-to-end flow**:
1. Create macro via UI with 30-second duration
2. Activate macro → verify lights change
3. Poll `/api/status` → verify countdown timer
4. Wait 30 seconds → verify auto-restore
5. Check `/api/schedule/all` → verify original schedule intact

**Edge cases**:
- **Macro with 0-second duration**: Should activate and immediately restore (test with `{"duration":0}` in JSON)
- **Macro affecting only 1 channel**: Verify other 15 channels remain unchanged
- **SD card read failure**: Simulate by deleting macro file mid-activation (should gracefully fail)

### Manual Tests (Checklist)

- [ ] Test 1: Create and activate macro
  1. Open web UI → Macros tab
  2. Click "Create Macro" → Name: "Test", Duration: 60
  3. Set channel 0 to 100%, channels 1-5 to 0%
  4. Click "Save"
  5. Click "Activate" on newly created macro
  6. **Pass criteria**: Lights change to macro pattern, serial log confirms activation

- [ ] Test 2: Verify auto-restore
  1. Continue from Test 1
  2. Wait 60 seconds (use stopwatch)
  3. **Pass criteria**: Lights restore to regular schedule, serial log shows auto-restore message

- [ ] Test 3: Manual stop before expiration
  1. Activate macro with 300-second duration
  2. Wait 10 seconds
  3. Click "Stop" button
  4. **Pass criteria**: Lights restore immediately, serial log shows manual stop

- [ ] Test 4: Status API includes macro state
  1. Activate macro
  2. Open DevTools → Network → filter `/api/status`
  3. **Pass criteria**: Response JSON includes `macro_active:true` and `macro_expires_in` field

- [ ] Test 5: Cannot activate second macro while first is active
  1. Activate macro A
  2. Immediately try to activate macro B
  3. **Pass criteria**: API returns error, serial log shows rejection

---

## Open Questions

1. **Macro duration format in JSON request**:
   - **Question**: Is duration sent as seconds (integer) or milliseconds?
   - **Assumption**: Seconds (matches UI input fields)
   - **Risk**: Low (can validate with frontend code in `js/app.js`)

2. **Macro file naming convention**:
   - **Question**: Does macro ID include channel number in filename (e.g., `macro_001_ch00.cfg`) or separate files per channel?
   - **Observation**: Based on [Webserver.cpp#L880-L920](../../src/Webserver.cpp#L880) (macro save), macros are saved per-channel with `_chNN` suffix
   - **Decision**: Use `macros/macro_XXX_chNN.cfg` pattern (one file per channel)

3. **Behavior when macro file is missing**:
   - **Question**: If macro exists for channels 0-2 but not 3-15, should activation fail or partially succeed?
   - **Recommendation**: Activate all available channels, skip missing files (graceful degradation)
   - **Reason**: Macros may intentionally affect only specific channels

4. **Serial debug output verbosity**:
   - **Question**: Should macro activation/restore log detailed channel info (16 lines of "Channel X restored") or summary?
   - **Recommendation**: Summary only (single line) to reduce serial spam
   - **Reason**: Main loop runs every 1ms; excessive logging could cause watchdog resets

---

## Success Criteria

### Functional Success
- [ ] User can activate a macro from web UI
- [ ] Lights change immediately to macro pattern
- [ ] After duration expires, lights automatically restore to regular schedule
- [ ] User can manually stop macro before expiration
- [ ] `/api/status` endpoint reports macro state and countdown timer
- [ ] Multiple macro activations are rejected (only one active at a time)

### Technical Success
- [ ] Firmware compiles without errors or warnings
- [ ] Memory usage increase is <5KB (monitor via `pio run` output)
- [ ] `proceedCycle()` overhead is <1ms (no watchdog resets)
- [ ] No SD card write operations during timer countdown (read-only after activation)
- [ ] Code follows project conventions:
  - Uses `char[]` buffers instead of `String` for paths
  - Uses `sprintf()` for JSON response building
  - Uses `F()` macro for serial debug strings
  - Follows German comment style where applicable

### User Experience Success
- [ ] Web UI displays countdown timer while macro is active
- [ ] Manual stop button is responsive (<200ms)
- [ ] No visual glitches during activation or restore (smooth PWM transitions)
- [ ] Serial log provides clear feedback for debugging

---

## Dependencies

- **Frontend changes** (separate task): Update `js/app.js` to:
  - Send `duration` field in `/api/macro/activate` POST request
  - Poll `/api/status` and display countdown timer
  - Show "Stop" button when macro is active

- **Macro creation wizard** (already implemented): Macros must exist on SD card before activation

---

## Estimated Total Time

- Phase 1: 45 minutes
- Phase 2: 90 minutes
- Phase 3: 60 minutes
- Phase 4: 75 minutes
- Phase 5: 60 minutes
- **Total**: ~5.5 hours (includes testing and debugging)

---

## Notes for Implementation

1. **Global `aqc` instance**: Webserver.cpp handlers need access to AquaControl instance. Pattern already used in codebase (see `extern AquaControl aqc;` declarations).

2. **Memory profiling**: After implementation, run `pio run -e esp8266` and check build output for RAM usage:
   ```
   RAM:   [=====     ]  52.3% (used 42932 bytes from 81920 bytes)
   ```
   Target: <57% after macro system addition.

3. **Watchdog timer**: ESP8266 has 1-second watchdog. Ensure `yield()` calls remain in `proceedCycle()` main loop.

4. **SD card reliability**: Consider adding retry logic for file reads (3 attempts before failing).

---

## References

- Plan template: [.github/prompts/plan-template.md](../prompts/plan-template.md)
- Architecture documentation: [ARCHITECTURE.md](../../ARCHITECTURE.md)
- Existing macro save implementation: [Webserver.cpp#L880-L920](../../src/Webserver.cpp#L880)
- Linear interpolation algorithm: [AquaControl.cpp#L928-L1000](../../src/AquaControl.cpp#L928)
- Tick-tock async pattern: [AquaControl.cpp#L750-L830](../../src/AquaControl.cpp#L750)
