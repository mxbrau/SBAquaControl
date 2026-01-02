# GitHub Issues - Quick Reference

**Purpose**: Ready-to-paste issue descriptions for manual creation in GitHub

---

## Issue #1: [BUG] Boot-time OOM crashes during config loading

**Labels**: `bug`  
**Milestone**: `v0.6`  
**Status**: ✅ Closed (fixed in Dec 2025)

**Description**:
```markdown
**Problem**: Device crashed during startup with StoreProhibitedCause exception

**Root Cause**: String concatenations in config loading creating temporary heap allocations during init sequence

**Solution**: Replaced `Serial.println(String(F("...")) + String(i))` patterns with separate `Serial.print()` calls

**Files Modified**: src/AquaControl.cpp (lines 349, 357, 436, 441)

**Result**: Clean boot sequence, no crashes

**Fixed by**: Session 2025-12-30 (see SESSION_SUMMARY_2025-12-30.md)
```

**Close immediately** with comment referencing SESSION_SUMMARY_2025-12-30.md

---

## Issue #2: [BUG] Severe RAM over-allocation (82% static usage)

**Labels**: `bug`  
**Milestone**: `v0.6`  
**Status**: ✅ Closed (fixed in Dec 2025)

**Description**:
```markdown
**Problem**: Compile-time RAM usage at 82%, leaving only ~28 KB heap

**Root Cause**: `MAX_TARGET_COUNT_PER_CHANNEL = 128` consuming 10.2 KB of SRAM  
- 16 channels × 128 targets × 5 bytes = 10,240 bytes static allocation

**Solution**: Reduced `MAX_TARGET_COUNT_PER_CHANNEL` from 128 → 32 for ESP8266
- New allocation: 16 × 32 × 5 = 2,560 bytes
- Freed: 7,680 bytes (75% reduction)

**Result**: Compile-time RAM usage dropped to 50-55%, heap available ~60-80 KB

**Files Modified**: src/AquaControl_config.h (line 21)

**Fixed by**: Session 2025-12-30 (see SESSION_SUMMARY_2025-12-30.md)
```

**Close immediately** with comment referencing SESSION_SUMMARY_2025-12-30.md

---

## Issue #3: [BUG] Memory leaks in web API (String concatenation)

**Labels**: `bug`  
**Milestone**: `v0.6`  
**Status**: ✅ Closed (fixed in Dec 2025)

**Description**:
```markdown
**Problem**: Streaming JSON handlers building large String objects, fragmenting heap

**Root Cause**: Code like `String item = "{\"time\":" + String(time) + ...`

**Solution**: Converted to `sprintf()` with fixed-size char buffers (48 bytes), stream results directly

**Affected handlers**:
- `handleApiScheduleGet()` 
- `handleApiScheduleAll()`
- `handleApiScheduleSave()`

**Files Modified**: src/Webserver.cpp

**Fixed by**: Session 2025-12-30 (see SESSION_SUMMARY_2025-12-30.md)
```

**Close immediately** with comment referencing SESSION_SUMMARY_2025-12-30.md

---

## Issue #4: [BUG] UI-firmware mismatch (spline vs linear interpolation)

**Labels**: `bug`, `documentation`  
**Milestone**: `v0.6`  
**Status**: ✅ Closed (fixed in Dec 2025)

**Description**:
```markdown
**Problem**: UI showed smooth spline curves, firmware executed linear interpolation

**Solution**: 
- Disabled automatic smoothing in Chart Manager
- Updated `chart-manager.js` to show linear segments only
- Reduced `maxTargetsPerChannel` from 128 → 32 to match firmware

**Files Modified**: extras/SDCard/js/chart-manager.js (lines 1-16)

**Documentation Added**: UI_UPDATE_LINEAR_INTERPOLATION.md, FIRMWARE_STATUS.md

**Fixed by**: Session 2025-12-30 (see SESSION_SUMMARY_2025-12-30.md)
```

**Close immediately** with comment referencing SESSION_SUMMARY_2025-12-30.md and new docs

---

## Issue #5: [FEATURE] Macro timer activation implementation

**Labels**: `enhancement`  
**Milestone**: `v0.6`  
**Status**: ⏳ Open (Step 4)

**Description**:
```markdown
**Feature Request**: Implement macro timer system to track temporary lighting overrides

**Current State**: Macros can be created and saved but not executed (API endpoint is stub)

**Requirements**:
- Add `MacroState` struct to track active macro (startTime, duration, originalTargets)
- Implement `handleApiMacroActivate()` endpoint
- Auto-restore previous schedule when duration expires
- Update `proceedCycle()` to check macro expiration

**Implementation Plan**: See `.github/plans/step-4-macro-timer.md`

**Memory Impact**: <5KB additional RAM

**Dependencies**: None

**Acceptance Criteria**:
- [ ] User clicks "Activate" on macro → lighting changes immediately
- [ ] After duration expires → schedule auto-restores
- [ ] `/api/status` shows `macro_active: true` and `macro_expires_in: 1234`
```

**Keep open** until Step 4 PR merged, then close with "Fixes #5" in PR description

---

## Issue #6: [FEATURE] Time-setting API endpoint

**Labels**: `enhancement`  
**Milestone**: `v0.6`  
**Status**: ⏳ Open (Step 5)

**Description**:
```markdown
**Feature Request**: Add API endpoint to set system time when RTC unavailable

**Current State**: Manual time setting works via existing UI, but no API endpoint

**Requirements**:
- Implement `handleApiTimeSet()` endpoint
- Accept JSON: `{"timestamp": 1704153600}` (Unix timestamp)
- Update system time via `setTime(timestamp)`
- Validate timestamp (must be >2020-01-01)

**Implementation Plan**: See `.github/plans/step-5-time-setting-api.md`

**Use Case**: Allows NTP-free time sync from JavaScript (`Date.now()`)

**Acceptance Criteria**:
- [ ] POST `/api/time/set` with valid timestamp → system time updates
- [ ] Invalid timestamp → returns 400 error
- [ ] `/api/status` shows updated time
```

**Keep open** until Step 5 PR merged, then close with "Fixes #6" in PR description

---

## Issue #7: [REFACTOR] String concatenation cleanup

**Labels**: `enhancement`, `good-first-issue`  
**Milestone**: `v0.7`  
**Status**: ⏳ Open (Step 6)

**Description**:
```markdown
**Goal**: Replace all remaining String concatenation patterns with `sprintf()` char buffers

**Current State**: Most API handlers use safe patterns, but some legacy code remains

**Pattern to Replace**:
```cpp
// BAD (heap fragmentation)
String msg = "Channel " + String(i) + " value: " + String(val);

// GOOD (stack allocation)
char msg[64];
snprintf(msg, sizeof(msg), "Channel %d value: %d", i, val);
```

**Files to Check**:
- src/AquaControl.cpp (Serial.print statements)
- src/Webserver.cpp (template replacements)

**Acceptance Criteria**:
- [ ] No `String(...)` + `String(...)` patterns remain
- [ ] All dynamic strings use char buffers with size limits
- [ ] Heap usage stable during continuous operation
```

**Keep open** until Step 6 PR merged

---

## Issue #8: [DOCS] Add JSDoc comments to JavaScript modules

**Labels**: `documentation`, `good-first-issue`  
**Milestone**: `v0.7`  
**Status**: ⏳ Open (Step 6)

**Description**:
```markdown
**Goal**: Add JSDoc comments to all JavaScript functions for better IDE support

**Files Needing Documentation**:
- extras/SDCard/js/api.js (API wrapper functions)
- extras/SDCard/js/chart-manager.js (Chart rendering)
- extras/SDCard/js/app.js (Main application logic)

**JSDoc Example**:
```javascript
/**
 * Fetches schedule data for a specific channel
 * @param {number} channelId - Channel ID (0-15)
 * @returns {Promise<Object>} Schedule data with targets array
 * @throws {Error} If API request fails
 */
async function getSchedule(channelId) { ... }
```

**Acceptance Criteria**:
- [ ] All public functions have JSDoc comments
- [ ] Parameter types and return values documented
- [ ] IDE autocomplete works for all functions
```

**Keep open** until Step 6 PR merged

---

## Issue #9: [REFACTOR] Remove legacy template system code

**Labels**: `enhancement`  
**Milestone**: `v0.7`  
**Status**: ⏳ Open (Step 6)

**Description**:
```markdown
**Goal**: Remove obsolete template system now that UI uses client-side rendering

**Legacy Code to Remove**:
- `##PLACEHOLDER##` replacement logic in src/Webserver.cpp
- Old HTML template files (if any remain)
- Template parsing functions no longer used

**Verification**:
- [ ] `grep -r "##.*##" extras/SDCard/` returns no results
- [ ] All HTML served as static files (no server-side replacement)
- [ ] API endpoints return pure JSON (no HTML fragments)

**Acceptance Criteria**:
- [ ] Template replacement code removed from Webserver.cpp
- [ ] No functional changes (UI works identically)
- [ ] Code size reduced by ~500 bytes
```

**Keep open** until Step 6 PR merged

---

## Issue #10: [FEATURE] Timezone and DST support

**Labels**: `enhancement`, `help-wanted`  
**Milestone**: `Future`  
**Status**: 📋 Backlog

**Description**:
```markdown
**Feature Request**: Add timezone and daylight saving time support

**Current State**: System uses UTC time only, user must manually adjust schedules

**Proposed Solution**:
- Add timezone offset to config: `{"timezone": "Europe/Berlin", "offset": 3600}`
- Support DST transitions (requires timezone database or API lookup)
- UI displays local time, firmware stores UTC

**Implementation Challenges**:
- ESP8266 memory constraints (timezone database = ~20 KB)
- DST transition dates vary by region
- Possible solutions: NTP with timezone API, manual offset + DST rules

**Related**: ROADMAP.md Phase 3

**Acceptance Criteria**:
- [ ] User sets timezone in config
- [ ] UI shows local time (e.g., 14:30 CET)
- [ ] Schedules execute at correct local time year-round
```

---

## Issue #11: [FEATURE] Gradient animation effects

**Labels**: `enhancement`  
**Milestone**: `v1.0`  
**Status**: 📋 Backlog

**Description**:
```markdown
**Feature Request**: Add animated lighting effects (sunrise, sunset, clouds)

**Proposed Features**:
- Sunrise simulation (gradual warm-up over 30-60 minutes)
- Sunset simulation (gradual cool-down)
- Cloud passing effects (random dimming/brightening)
- Lightning storm mode (rapid flashes)

**Implementation Strategy**:
- Define effect as macro with rapid target transitions
- UI wizard: "Sunrise at 08:00" → generates 60 targets (1 per minute)
- Firmware executes as normal schedule (no special logic needed)

**Memory Impact**: Same as macros (reuses existing target system)

**Related**: ROADMAP.md Phase 5

**Acceptance Criteria**:
- [ ] User selects "Sunrise Effect" from preset library
- [ ] UI shows preview animation
- [ ] Device executes smooth gradient over specified duration
```

---

## Issue #12: [FEATURE] Multi-user authentication

**Labels**: `enhancement`, `help-wanted`  
**Milestone**: `Future`  
**Status**: 📋 Backlog

**Description**:
```markdown
**Feature Request**: Add basic authentication to web interface

**Current State**: Web UI accessible to anyone on network (no login)

**Proposed Solution**:
- HTTP Basic Auth (simplest, supported by ESP8266WebServer)
- Username/password stored in `config/auth.cfg`
- Optional: Admin vs. Read-only roles

**Security Considerations**:
- HTTP Basic Auth sends credentials in clear text → recommend HTTPS (Issue #13)
- Password hashing (bcrypt) may exceed ESP8266 CPU capabilities
- Alternative: Token-based auth with session cookies

**Related**: ROADMAP.md Phase 4

**Acceptance Criteria**:
- [ ] Accessing web UI prompts for username/password
- [ ] Invalid credentials → 401 Unauthorized
- [ ] Valid credentials → full access to features
```

---

## Issue #13: [FEATURE] HTTPS support with self-signed certificates

**Labels**: `enhancement`, `help-wanted`  
**Milestone**: `Future`  
**Status**: 📋 Backlog

**Description**:
```markdown
**Feature Request**: Enable HTTPS to encrypt web traffic

**Current State**: HTTP only (unencrypted communication)

**Implementation Options**:
- ESP8266 supports TLS via BearSSL library
- Self-signed certificate (user accepts browser warning)
- Certificate stored on SD card or SPIFFS

**Challenges**:
- TLS handshake = ~40 KB heap allocation (tight on ESP8266)
- Self-signed cert = browser warnings (user education needed)
- Certificate generation/renewal process

**Related**: ROADMAP.md Phase 4, Issue #12 (authentication)

**Acceptance Criteria**:
- [ ] Device accessible via `https://192.168.1.100`
- [ ] Traffic encrypted (verified with browser dev tools)
- [ ] Minimal performance impact (<500ms additional latency)
```

---

## Issue #14: [FEATURE] UI support for 16 channels (currently 6)

**Labels**: `enhancement`  
**Milestone**: `v1.0`  
**Status**: 📋 Backlog

**Description**:
```markdown
**Feature Request**: Extend UI to manage all 16 available PWM channels

**Current State**: Firmware supports 16 channels, UI only displays/manages 6

**Proposed Solution**:
- Add tabs or accordion view for channel groups (1-8, 9-16)
- Channel enable/disable toggle (hide unused channels)
- Bulk operations: "Copy schedule from CH1 to CH2-4"

**UI Mockup**:
```
[Channels 1-8] [Channels 9-16]  ← Tabs

CH1: White LEDs     [✓] Enabled  [Edit]
CH2: Blue LEDs      [✓] Enabled  [Edit]
CH3: Red LEDs       [ ] Disabled
...
```

**Acceptance Criteria**:
- [ ] UI shows all 16 channels
- [ ] User can edit schedule for any channel
- [ ] Disabled channels hidden from main view
```

---

## Issue #15: [FEATURE] Macro persistence across power loss

**Labels**: `enhancement`  
**Milestone**: `Future`  
**Status**: 📋 Backlog

**Description**:
```markdown
**Feature Request**: Save active macro state to survive power loss

**Current State**: Active macro resets on power cycle (timer lost)

**Proposed Solution**:
- Write macro state to SD card on activation
- File: `config/active_macro.tmp` with `{startTime, duration, channelId}`
- On boot: Check if macro should still be active → restore or delete file

**Edge Cases**:
- Power loss during macro → resume or cancel?
- RTC time lost during outage → macro duration invalid
- Solution: Store absolute end time (timestamp), not duration

**Acceptance Criteria**:
- [ ] User activates 2-hour macro
- [ ] Device loses power after 30 minutes
- [ ] On reboot → macro resumes with 90 minutes remaining
```

---

## Manual Creation Checklist

### Step 1: Create Labels (5 min)
Navigate to: `Settings > Labels`

- [ ] `bug` (color: #d73a4a)
- [ ] `enhancement` (color: #0e8a16)
- [ ] `documentation` (color: #0075ca)
- [ ] `good-first-issue` (color: #7057ff)
- [ ] `help-wanted` (color: #fbca04)
- [ ] `wontfix` (color: #ffffff)

### Step 2: Create Milestones (5 min)
Navigate to: `Issues > Milestones > New Milestone`

- [ ] **v0.6** (Due: 2026-01-31) - "Macro Timer & Time API"
- [ ] **v0.7** (Due: 2026-02-28) - "Code Standardization"
- [ ] **v1.0** (Due: 2026-06-30) - "Spline Smoothing"
- [ ] **Future** (No due date) - "Long-term roadmap items"

### Step 3: Create Issues (30 min)
Navigate to: `Issues > New Issue`

**Completed Work** (create + close immediately):
- [ ] Issue #1 (Boot Crash)
- [ ] Issue #2 (RAM Usage)
- [ ] Issue #3 (Memory Leaks)
- [ ] Issue #4 (UI Mismatch)

**Active Work** (create and leave open):
- [ ] Issue #5 (Macro Timer)
- [ ] Issue #6 (Time API)
- [ ] Issue #7 (String Cleanup)
- [ ] Issue #8 (JSDoc)
- [ ] Issue #9 (Legacy Code)

**Future Roadmap**:
- [ ] Issue #10 (Timezone)
- [ ] Issue #11 (Animations)
- [ ] Issue #12 (Authentication)
- [ ] Issue #13 (HTTPS)
- [ ] Issue #14 (16 Channels)
- [ ] Issue #15 (Macro Persistence)

### Step 4: Update Documentation (10 min)
- [ ] Update ROADMAP.md with issue references
- [ ] Update MASTERPLAN.md Step 7 status to ✅ Complete
- [ ] Commit changes: `git commit -m "docs: migrate tasks to GitHub Issues"`

### Step 5: Optional Project Board (10 min)
- [ ] Create board: `Projects > New Project > Board`
- [ ] Add columns: Backlog, In Progress, Review, Done
- [ ] Populate with issues
- [ ] Configure automation rules

**Total Time**: ~60 minutes
