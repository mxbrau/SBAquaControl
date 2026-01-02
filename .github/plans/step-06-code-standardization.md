---
title: Step 6 - Code Standardization & Cleanup
version: 1.0
date_created: 2026-01-02
last_updated: 2026-01-02
---

# Implementation Plan: Code Standardization & Cleanup

## Overview
Enforce memory-safe patterns, remove legacy code, standardize inconsistent naming conventions, and add comprehensive documentation across the codebase. This critical housekeeping step eliminates technical debt accumulated during rapid feature development, prevents heap fragmentation on ESP8266 (160KB RAM), and improves code maintainability for future contributors.

**Why it matters**: String concatenation in production paths causes unpredictable crashes on ESP8266 after hours of operation. Removing 40% legacy code from examples reduces confusion. Consistent naming and documentation accelerates onboarding and debugging.

---

## Requirements

### Functional Requirements
- **No behavioral changes**: All existing features continue working identically
- **Memory safety**: Replace all String concatenation in hot paths with fixed char buffers
- **Documentation completeness**: All public functions have JSDoc (JS) or descriptive comments (C++)
- **Naming consistency**: Macro "id" (internal identifier) vs "name" (display label) semantically distinct

### Non-Functional Requirements
- **Memory impact**: Must **reduce** RAM usage by 2-5KB (from String elimination)
- **Build verification**: `pio run -e esp8266` succeeds after each phase
- **Code coverage**: 100% of public API functions documented
- **Zero legacy code**: Remove all commented-out sections in examples/

**Critical constraints**:
- ESP8266 has only 160KB RAM total (~80KB available after system overhead)
- Each String concatenation causes heap fragmentation (unpredictable crashes after 6-12 hours)
- Must maintain German comments for user-facing strings (keep existing style)

---

## Architecture and Design

### High-Level Design
This refactoring touches 3 primary areas without changing architecture:

1. **String Safety Audit** ([src/Webserver.cpp](../../src/Webserver.cpp))
   - Pattern: `String s = "foo" + var + "bar";` → `char buf[N]; sprintf(buf, "foo%sbar", var);`
   - Target: 6 String instances identified in Webserver.cpp (see grep results)
   - Scope: File I/O paths (`sPwmFilename`, `sMacroPath`) and template parsing (`sLine`)

2. **Legacy Code Removal** ([examples/AquaControlSketch/AquaControlSketch.ino](../../examples/AquaControlSketch/AquaControlSketch.ino))
   - Remove unused serial command parser (lines 19-33)
   - Remove commented-out `digitalClockDisplay()` functions (lines 35-56)
   - Result: File reduces from 56 to ~15 lines (minimal setup/loop example)

3. **Documentation & Naming Standardization**
   - JavaScript: Add JSDoc to all public functions in [js/app.js](../../extras/SDCard/js/app.js), [js/api.js](../../extras/SDCard/js/api.js), [js/chart-manager.js](../../extras/SDCard/js/chart-manager.js)
   - C++: Add brief function comments to all public methods in [AquaControl.h](../../src/AquaControl.h)
   - Macro fields: Enforce `id` (filename: `macro_001`) vs `name` (display: "Movie Mode")

### Key Patterns

#### Memory-Safe String Pattern
```cpp
// ❌ AVOID: Heap fragmentation (each + operator allocates new String)
String sPwmFilename = "config/ledch_";
if (channel < 10) sPwmFilename += "0";
sPwmFilename += String(channel);
sPwmFilename += ".cfg";

// ✅ PREFER: Fixed stack allocation (zero fragmentation)
char pwmFilename[32];
sprintf(pwmFilename, "config/ledch_%02d.cfg", channel);
```

#### Template Streaming Pattern (already correct)
```cpp
// ✅ This pattern in handleRoot() is CORRECT - keep as-is
_Server.setContentLength(CONTENT_LENGTH_UNKNOWN);
_Server.send(200, "text/html", "");
while (myFile.available()) {
    String sLine = myFile.readStringUntil(10);  // OK: Single-line buffer
    sLine.replace("##PLACEHOLDER##", value);     // OK: Limited scope
    _Server.sendContent(sLine);                  // Sent immediately, no accumulation
}
```
**Note**: `handleRoot()` uses String safely (line-by-line streaming). Focus on file path construction.

#### JSDoc Standard
```javascript
/**
 * Loads all channel schedules from API and updates chart visualization
 * @returns {Promise<void>}
 * @throws {Error} If API call fails or response is malformed
 */
async function loadSchedules() { ... }
```

### Design Decisions

**Why char buffers instead of String?**
- String class allocates on heap → fragmentation over time → crashes after 6-12 hours
- char[N] on stack → deterministic memory → predictable behavior
- sprintf() is standard C (battle-tested, minimal overhead)

**Why audit before refactoring?**
- Need baseline of all String instances to track progress
- Some String uses are safe (line-by-line streaming) vs unsafe (path concatenation)
- Prevents missing hidden instances during refactoring

**Why remove legacy code now?**
- Blocks merging until Steps 4 & 5 complete (avoid conflicts)
- Example file is primary reference for new users (must be clean)
- Commented code creates confusion about "correct" usage patterns

**Why standardize id/name now?**
- Macro system expanding in Step 4 (timer activation by ID)
- API uses `id` parameter, but semantics unclear in current code
- Prevents bugs from confusing internal identifier with display label

---

## Implementation Tasks

### Phase 1: String Safety Audit (Baseline)
**Goal**: Document all String usage before refactoring

- [ ] Create audit spreadsheet in [.github/audits/string-usage.md](../../.github/audits/string-usage.md)
  - Columns: File, Line, Variable Name, Usage Pattern, Safe/Unsafe, Refactor Priority
  - Use grep results as starting point: 6 instances in Webserver.cpp

- [ ] Classify each String instance:
  - **SAFE**: `sLine` in handleRoot() (line-by-line streaming, no accumulation)
  - **UNSAFE**: `sPwmFilename` (line 388) - path concatenation
  - **UNSAFE**: `sMacroPath` (lines 684, 738, 1072) - path concatenation
  - **REVIEW**: `sLine` in macro parsing (line 751) - similar to handleRoot(), likely safe

- [ ] Add memory usage baseline test:
  - Build project: `pio run -e esp8266`
  - Extract RAM usage from build output (look for "Global variables use XXXXX bytes")
  - Document in audit file for before/after comparison

**Deliverable**: Complete audit file with 6+ entries, baseline RAM number

---

### Phase 2: Replace String Path Concatenation
**Goal**: Eliminate unsafe String usage in file path construction

- [ ] Refactor `sPwmFilename` in [Webserver.cpp#L388](../../src/Webserver.cpp#L388)
  ```cpp
  // Current (lines 388-393):
  String sPwmFilename = "config/ledch_";
  if (channel < 10) sPwmFilename += "0";
  sPwmFilename += String(channel);
  sPwmFilename += ".cfg";
  
  // Replace with:
  char pwmFilename[32];
  sprintf(pwmFilename, "config/ledch_%02d.cfg", channel);
  // Update all references from sPwmFilename to pwmFilename
  ```

- [ ] Refactor `sMacroPath` in handleApiMacroSaveOrUpdate [Webserver.cpp#L684](../../src/Webserver.cpp#L684)
  ```cpp
  // Current:
  String sMacroPath = "macros/macro_";
  sMacroPath += macroId;
  sMacroPath += ".cfg";
  
  // Replace with:
  char macroPath[64];
  sprintf(macroPath, "macros/macro_%s.cfg", macroId);
  ```

- [ ] Refactor `sMacroPath` in handleApiMacroListGET [Webserver.cpp#L738](../../src/Webserver.cpp#L738)
  ```cpp
  // Current:
  String sMacroPath = "macros/";
  // Used to open directory - might be SD.open("macros/") directly
  
  // Replace with:
  File macroDir = SD.open("macros/");  // Direct string literal
  ```

- [ ] Refactor `sMacroPath` in handleApiMacroActivate [Webserver.cpp#L1072](../../src/Webserver.cpp#L1072)
  ```cpp
  // Same pattern as #684 - replace with sprintf()
  ```

- [ ] Build verification after each file change:
  ```bash
  pio run -e esp8266
  ```

- [ ] Memory usage comparison:
  - Extract new RAM usage from build output
  - Calculate delta (expect 2-5KB reduction)
  - Document in audit file

**Deliverable**: Zero String path concatenations, build succeeds, RAM reduced

---

### Phase 3: Remove Legacy Code from Examples
**Goal**: Clean up AquaControlSketch.ino to minimal working example

- [ ] Remove unused serial command parser in [AquaControlSketch.ino#L19-L33](../../examples/AquaControlSketch/AquaControlSketch.ino#L19)
  ```cpp
  // DELETE these lines:
  if (Serial.available()){
      String sInput = Serial.readStringUntil('\n');
      Serial.println(sInput);
      switch (sInput[0]){
      case 'm':
          Serial.println(F("Switching to manual mode"));
          break;
      case 'a':
          Serial.println(F("Switching to automatic mode"));
          break;
      default:
          break;
      }
  }
  ```

- [ ] Remove commented-out functions [AquaControlSketch.ino#L35-L56](../../examples/AquaControlSketch/AquaControlSketch.ino#L35)
  ```cpp
  // DELETE these functions:
  // void digitalClockDisplay() { ... }
  // void printDigits(int digits) { ... }
  ```

- [ ] Verify final file structure:
  ```cpp
  #include <OneWire.h>
  #include <Arduino.h>
  #include <AquaControl.h>
  #include <SPI.h>
  #include <SD.h>

  AquaControl aqc;

  void setup() {
      Serial.begin(19200);
      aqc.init();
  }

  void loop() {
      aqc.proceedCycle();
  }
  ```

- [ ] Test compile:
  ```bash
  pio run -e esp8266
  ```

**Deliverable**: AquaControlSketch.ino reduced to 15-20 lines, builds successfully

---

### Phase 4: Normalize Macro ID/Name Semantics
**Goal**: Establish clear distinction between internal ID and display name

- [ ] Update macro file format documentation in [ARCHITECTURE.md](../../ARCHITECTURE.md)
  - Add section: "Macro File Naming Convention"
  - Rule: `id` = filename prefix (e.g., "macro_001" → file: `macros/macro_001.cfg`)
  - Rule: `name` = user-visible label (e.g., "Movie Mode" - display in UI)

- [ ] Audit current macro usage in API handlers:
  - [handleApiMacroSaveOrUpdate()](../../src/Webserver.cpp#L670) - uses `id` parameter ✅
  - [handleApiMacroListGET()](../../src/Webserver.cpp#L735) - returns `id` field ✅
  - [handleApiMacroActivate()](../../src/Webserver.cpp#L1060) - uses `id` parameter ✅

- [ ] Verify JavaScript consistency:
  - [api.js](../../extras/SDCard/js/api.js) - all functions use `id` parameter ✅
  - [app.js](../../extras/SDCard/js/app.js) - check macro display uses `name` field

- [ ] Add comment to macro struct (if defined) or API handlers:
  ```cpp
  // Macro identification:
  //   - "id": Internal filename identifier (e.g., "macro_001")
  //   - "name": User-facing display label (e.g., "Movie Mode")
  ```

**Deliverable**: Documentation updated, comments added, no code changes needed (already correct)

---

### Phase 5: Add JSDoc to JavaScript Files
**Goal**: Document all public functions in web UI JavaScript

- [ ] Document functions in [js/api.js](../../extras/SDCard/js/api.js#L1-L116)
  - `call()` - Generic API wrapper
  - `getStatus()` - Fetch system status
  - `getSchedule()` - Fetch single channel schedule
  - `getAllSchedules()` - Fetch all schedules
  - `saveSchedule()` - Save channel targets
  - `clearAllSchedules()` - Reset all schedules
  - `addTarget()` - Add schedule point
  - `deleteTarget()` - Remove schedule point
  - `startTestMode()` - Enter manual control
  - `updateTestValue()` - Set channel value in test mode
  - `exitTestMode()` - Return to auto mode
  - `getMacros()` - List all macros
  - `getMacro()` - Fetch single macro
  - `saveMacro()` - Save macro definition
  - `activateMacro()` - Activate temporary override
  
  **Template**:
  ```javascript
  /**
   * Fetches current system status including temperature and macro state
   * @returns {Promise<Object>} Status object with temp, macro_active, etc.
   * @throws {Error} If API call fails
   */
  async getStatus() { ... }
  ```

- [ ] Document functions in [js/app.js](../../extras/SDCard/js/app.js#L1-L732)
  - Focus on public/exported functions:
    - `init()` - Application initialization
    - `loadSchedules()` - Load and display schedules
    - `loadMacros()` - Load macro list
    - `createChannelControls()` - Generate slider UI
    - `startStatusUpdates()` - Begin status polling
    - `handleSliderChange()` - Process manual input
  - Skip internal helpers unless particularly complex

- [ ] Document functions in [js/chart-manager.js](../../extras/SDCard/js/chart-manager.js)
  - `ChartManager` class constructor
  - `init()` - Initialize chart instance
  - `updateSchedule()` - Render schedule data
  - `addTarget()` - Add point to chart
  - `removeTarget()` - Remove point from chart
  - Any other public methods

**Deliverable**: All public functions have JSDoc comments (estimate: 25-30 functions total)

---

### Phase 6: Add Function Comments to C++
**Goal**: Document public API in AquaControl.h and key methods in implementation files

- [ ] Add comments to class declarations in [AquaControl.h](../../src/AquaControl.h)
  - `PwmChannel` class:
    ```cpp
    /** 
     * Manages individual PWM channel with time-based targets and smooth transitions
     * Supports up to 10 target points per channel
     */
    class PwmChannel { ... }
    ```
  
  - `TemperatureReader` class:
    ```cpp
    /**
     * Non-blocking DS18B20 temperature sensor reader using tick-tock pattern
     * Call readTemperature() repeatedly - returns valid data after conversion completes
     */
    class TemperatureReader { ... }
    ```
  
  - `AquaControl` class:
    ```cpp
    /**
     * Main controller class coordinating PWM output, time sync, and web interface
     * Usage: Call init() once in setup(), proceedCycle() continuously in loop()
     */
    class AquaControl { ... }
    ```

- [ ] Add method comments in [AquaControl.cpp](../../src/AquaControl.cpp)
  - `init()` - Initialization sequence
  - `proceedCycle()` - Main state machine (non-blocking)
  - `PwmChannel::proceedCycle()` - Interpolation logic
  - `TemperatureReader::readTemperature()` - Async temperature reading
  - Any other public methods

  **Template**:
  ```cpp
  /**
   * Non-blocking main loop handler - call continuously from Arduino loop()
   * Manages PWM interpolation, temperature reading, and web server
   */
  void proceedCycle() { ... }
  ```

- [ ] Add brief comments to [Webserver.cpp](../../src/Webserver.cpp) handlers
  - Each `handleXxxGET()` and `handleXxxPOST()` function:
    ```cpp
    /**
     * GET /api/schedule - Fetch channel schedule targets
     * Query params: channel (0-5)
     * Response: JSON array of {time, value} objects
     */
    void handleApiScheduleGET() { ... }
    ```

**Deliverable**: All public classes/methods have descriptive comments (estimate: 15-20 functions)

---

### Phase 7: Build Verification & Final Audit
**Goal**: Confirm all changes integrate correctly and meet success criteria

- [ ] Full build test:
  ```bash
  pio run -e esp8266 --target upload
  ```

- [ ] Memory usage final comparison:
  - Extract RAM usage from build output
  - Compare to baseline from Phase 1
  - Verify ≥2KB reduction

- [ ] Manual functional test:
  - Power on ESP8266
  - Access web UI
  - Verify schedules load and display
  - Verify test mode works (sliders control channels)
  - Verify macro list loads
  - Monitor serial output for stability (run 10+ minutes)

- [ ] Code review checklist:
  - [ ] Zero String concatenations in file path construction
  - [ ] AquaControlSketch.ino is minimal example (15-20 lines)
  - [ ] All JavaScript public functions have JSDoc
  - [ ] All C++ public classes/methods have comments
  - [ ] Macro id/name semantics documented
  - [ ] Build succeeds with no warnings
  - [ ] RAM usage reduced by ≥2KB

- [ ] Update [FIRMWARE_STATUS.md](../../FIRMWARE_STATUS.md):
  - Mark Step 6 as complete
  - Document RAM reduction achieved
  - Note any remaining technical debt

**Deliverable**: Clean build, passing tests, updated documentation

---

## Testing Strategy

### Unit Tests
*Note: This refactoring is primarily mechanical (replacing String with char[]) - automated testing limited*

- **String replacement verification**: 
  - Compile-time: Build errors if sprintf() format mismatches types
  - Manual code review: Verify buffer sizes adequate (32 bytes for paths, 64 for macro IDs)

- **Legacy code removal verification**:
  - Build test confirms no broken dependencies
  - Example sketch still compiles and runs

### Integration Tests

- **End-to-end schedule workflow**:
  1. Open web UI → Schedules tab
  2. Add target to channel 0
  3. Verify target saves (check serial output for file write confirmation)
  4. Reload page
  5. Verify target persists (loaded from SD card)

- **End-to-end macro workflow**:
  1. Open Macros tab
  2. Click existing macro (if any)
  3. Verify macro loads (check serial output for file read)
  4. Create new macro (ID: "test_001", Name: "Test Macro")
  5. Verify macro saves
  6. Reload page
  7. Verify macro appears in list

### Manual Tests

**Test 1: String Refactoring (Path Construction)**
1. Navigate to `/api/schedule?channel=3`
2. Expected: Returns JSON targets for channel 3
3. Check serial: Look for `"config/ledch_03.cfg"` (correct zero-padding)
4. Verify no crashes or memory errors

**Test 2: Legacy Code Removal (Example Sketch)**
1. Open [AquaControlSketch.ino](../../examples/AquaControlSketch/AquaControlSketch.ino)
2. Verify only essential code remains (no serial parser, no commented functions)
3. Upload to ESP8266: `pio run -e esp8266 --target upload`
4. Expected: Boots normally, web UI accessible
5. Monitor serial: No error messages

**Test 3: Documentation (JSDoc)**
1. Open [js/api.js](../../extras/SDCard/js/api.js) in VS Code
2. Hover over `API.getStatus()` in any calling code
3. Expected: Tooltip shows JSDoc description and return type
4. Repeat for 5-10 other functions

**Test 4: Memory Stability (Long-Running Test)**
1. Upload firmware with all refactorings
2. Access web UI, navigate all tabs
3. Enable test mode → adjust sliders → exit test mode (repeat 5x)
4. Let device run for 1 hour
5. Monitor serial output: No memory errors, no crashes
6. Expected: Device remains responsive after 1 hour (previous String issues caused crashes after 6-12 hours, but 1 hour is a good smoke test)

---

## Open Questions

1. **String in template streaming (handleRoot(), line 37-50)**: 
   - Current implementation uses String for line-by-line file reading and template replacement
   - This is **safe** because each line is streamed immediately (no accumulation)
   - **Decision**: Keep as-is, do NOT refactor (already optimal pattern)

2. **Buffer sizes for char arrays**:
   - File paths: Currently using 32 bytes (adequate for `config/ledch_00.cfg`)
   - Macro IDs: Using 64 bytes (allows longer macro identifiers like `macro_holiday_mode_2025`)
   - **Question**: Should we standardize buffer sizes? (e.g., all paths = 64 bytes for future-proofing?)
   - **Recommendation**: Use 32 for standard paths, 64 for user-controlled strings (macro IDs, SSID, etc.)

3. **German vs English in code comments**:
   - User-facing strings are German (Serial.print messages, HTML content)
   - Code comments currently mix German and English
   - **Decision**: Keep status quo (existing style), do NOT force consistency now (separate low-priority task)

4. **JSDoc coverage threshold**:
   - Some helper functions are trivial (e.g., `formatTime(seconds)`)
   - **Question**: Document all functions, or only public API?
   - **Recommendation**: All exported/public functions + any complex internals (>10 lines)

---

## Success Criteria

✅ **String Safety**:
- Zero String concatenations in file path construction (Webserver.cpp)
- All file paths use char[N] + sprintf()
- Build output shows ≥2KB RAM reduction

✅ **Legacy Code**:
- AquaControlSketch.ino reduced to ≤20 lines (setup + loop only)
- No commented-out code in examples/

✅ **Documentation**:
- All JavaScript public functions have JSDoc (@param, @returns, @description)
- All C++ public classes/methods have descriptive comments
- Macro id/name semantics documented in ARCHITECTURE.md

✅ **Naming Consistency**:
- Macro "id" vs "name" distinction clear in code and docs
- No ambiguous variable names for macro identifiers

✅ **Build Health**:
- `pio run -e esp8266` succeeds with zero warnings
- No compiler errors after any phase
- Example sketch compiles and runs

✅ **Functional Stability**:
- All existing features work identically
- Web UI loads and functions normally
- Device runs ≥1 hour without crashes or memory errors

✅ **Code Review Ready**:
- No String concatenation in production code paths
- Clear, maintainable code structure
- Comprehensive inline documentation
- Ready for next development phase (Step 7+)

---

## Dependencies & Blockers

### Dependencies
- **Blocked by**: Steps 4 & 5 must complete first to avoid merge conflicts
  - Step 4 (Macro Timer) modifies [Webserver.cpp](../../src/Webserver.cpp) handleApiMacroActivate()
  - Step 5 (Time API) modifies [AquaControl.cpp](../../src/AquaControl.cpp) time handling
  - Wait for both PRs to merge before starting Phase 2 (String refactoring)

### Unblocks
- **Unblocks**: All future development work
  - Memory-safe foundation for complex features (OTA updates, WiFi config, etc.)
  - Clean example accelerates community contributions
  - Documentation enables self-service troubleshooting

### External Dependencies
- None (pure refactoring, no new libraries)

---

## Notes

### Reference Implementation Patterns
- **Linear interpolation**: [AquaControl.cpp#L810-L890](../../src/AquaControl.cpp#L810) - model for smooth transitions
- **Tick-tock async**: [TemperatureReader](../../src/AquaControl.cpp#L608) - non-blocking state machine pattern
- **File I/O**: [writeWlanConfig()](../../src/Webserver.cpp#L290) - temp file approach for safe config updates
- **Template streaming**: [handleRoot()](../../src/Webserver.cpp#L25-L56) - memory-safe HTML generation

### Memory Management Philosophy
ESP8266 heap fragmentation is the #1 cause of production crashes. Key principles:
1. **Prefer stack allocation**: char[N] over String, fixed arrays over dynamic
2. **Stream, don't accumulate**: Send data as generated (see handleRoot() pattern)
3. **Minimize allocations**: Reuse buffers in loops, avoid `new` in hot paths
4. **Measure continuously**: Track build RAM usage, test long-running stability

### Code Style Consistency
- Use `F()` macro for all Serial.print strings (stores in flash, not RAM)
- Indent with tabs (existing codebase standard)
- Keep German user-facing messages (existing convention)
- Follow PlatformIO naming: `_variable` for instance members, `Variable` for class names

### Timeline Estimate
- Phase 1 (Audit): 1 hour
- Phase 2 (String refactoring): 2-3 hours (iterative testing)
- Phase 3 (Legacy removal): 30 minutes
- Phase 4 (Naming docs): 30 minutes
- Phase 5 (JSDoc): 2-3 hours (25-30 functions)
- Phase 6 (C++ comments): 1-2 hours (15-20 functions)
- Phase 7 (Verification): 1-2 hours (testing + documentation)

**Total**: 8-12 hours of focused work over 2-3 sessions

### Related Documentation
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - System design overview
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - Coding standards and build process
- [FIRMWARE_STATUS.md](../../FIRMWARE_STATUS.md) - Development progress tracker
- [UI_UPDATE_LINEAR_INTERPOLATION.md](../../UI_UPDATE_LINEAR_INTERPOLATION.md) - Chart rendering patterns
