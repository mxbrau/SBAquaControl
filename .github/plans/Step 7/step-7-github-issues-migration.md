---
title: Step 7 - GitHub Issues Migration
version: 1.0
date_created: 2026-01-02
last_updated: 2026-01-02
---

# Implementation Plan: GitHub Issues Migration

## Overview
Migrate all bugs, features, and improvement tasks from local markdown files (SESSION_SUMMARY, ROADMAP.md, MASTERPLAN.md) to GitHub Issues for transparent tracking and community collaboration. This is the final cleanup step after code changes (Steps 4-6) complete, establishing a public task management system with proper categorization, milestones, and project board organization.

**Why**: Local markdown files are hard to track, don't support discussion/assignment, and are invisible to contributors. GitHub Issues enables transparent progress tracking, community contributions, and integration with pull requests.

---

## Requirements

### Functional Requirements
- Migrate all existing tasks to GitHub Issues with proper categorization
- Create issue templates for consistent bug reports and feature requests
- Establish label system (bug, enhancement, documentation, good-first-issue)
- Set up milestones aligned with ROADMAP.md (v0.6, v0.7, v1.0)
- Update ROADMAP.md to reference GitHub issues (e.g., "See #5 for timezone support")
- Close completed issues from Steps 4-6 with PR references
- (Optional) Create project board for visual task management

### Non-Functional Requirements
- Issue titles must be clear and searchable (50-80 characters ideal)
- Descriptions must include context, acceptance criteria, and technical details
- Labels must follow GitHub best practices (lowercase, hyphen-separated)
- All references to line numbers must use markdown links format
- Backward compatibility: Keep ROADMAP.md as high-level overview, issues for details

---

## Architecture and Design

### High-Level Design

**Current State**:
```
Local Markdown Files
├── SESSION_SUMMARY_2025-12-30.md (historical bugs/fixes)
├── ROADMAP.md (feature roadmap with inline tasks)
├── MASTERPLAN.md (refactoring steps)
└── PRODUCT.md (vision and future features)
```

**Target State**:
```
GitHub Issues (Public Tracking)
├── Labels (categorization)
│   ├── bug (red)
│   ├── enhancement (green)
│   ├── documentation (blue)
│   ├── good-first-issue (purple)
│   ├── help-wanted (yellow)
│   └── wontfix (gray)
├── Milestones (versioning)
│   ├── v0.6 (Macro Timer + Time API)
│   ├── v0.7 (Code Standards + Docs)
│   └── v1.0 (Spline Smoothing + Advanced Features)
├── Issue Templates
│   ├── bug_report.md
│   ├── feature_request.md
│   └── documentation.md
└── Project Board (optional)
    ├── Backlog
    ├── In Progress
    ├── Review
    └── Done

ROADMAP.md (Updated)
└── References issues: "See #5 for timezone support"
```

### Issue Organization Strategy

**Labels** (color-coded):
- `bug` (🔴 red): Something isn't working
- `enhancement` (🟢 green): New feature or request
- `documentation` (🔵 blue): Improvements or additions to docs
- `good-first-issue` (🟣 purple): Good for newcomers
- `help-wanted` (🟡 yellow): Extra attention needed
- `wontfix` (⚪ gray): Won't be fixed/implemented

**Milestones**:
- **v0.6** (Q1 2026): Steps 4-5 completion (Macro Timer, Time API)
- **v0.7** (Q1 2026): Step 6 completion (Code standardization, docs)
- **v1.0** (Q2 2026): Phase 2 features (spline smoothing, enhanced UI)
- **Future** (Q3+ 2026): Advanced features (timezone, HTTPS, multi-user)

**Priority Levels** (via labels + milestone assignment):
- P0 (Critical): Bugs in v0.6 milestone
- P1 (High): Features in v0.6 milestone
- P2 (Medium): Features in v0.7 milestone
- P3 (Low): Features in v1.0+ milestones

---

## Implementation Tasks

### Phase 1: GitHub Repository Setup (15 min)

- [ ] Create issue labels in GitHub repository
  - Navigate to: `Settings > Labels`
  - Create labels: `bug`, `enhancement`, `documentation`, `good-first-issue`, `help-wanted`, `wontfix`
  - Color codes: bug=#d73a4a, enhancement=#0e8a16, documentation=#0075ca, good-first-issue=#7057ff, help-wanted=#fbca04, wontfix=#ffffff

- [ ] Create milestones in GitHub repository
  - Navigate to: `Issues > Milestones > New Milestone`
  - **v0.6**: Title="v0.6 - Macro Timer & Time API", Due=2026-01-31, Description="Complete Steps 4-5 of refactoring plan"
  - **v0.7**: Title="v0.7 - Code Standardization", Due=2026-02-28, Description="Complete Step 6 of refactoring plan"
  - **v1.0**: Title="v1.0 - Spline Smoothing", Due=2026-06-30, Description="Phase 2 features from ROADMAP.md"
  - **Future**: Title="Future Enhancements", Due=None, Description="Long-term roadmap items (timezone, HTTPS, etc.)"

### Phase 2: Issue Templates Creation (20 min)

- [ ] Create `.github/ISSUE_TEMPLATE/bug_report.md`
  ```markdown
  ---
  name: Bug Report
  about: Report a bug or unexpected behavior
  title: "[BUG] "
  labels: bug
  assignees: ''
  ---
  
  **Describe the bug**
  A clear and concise description of what the bug is.
  
  **To Reproduce**
  Steps to reproduce the behavior:
  1. Go to '...'
  2. Click on '...'
  3. See error
  
  **Expected behavior**
  What you expected to happen.
  
  **Environment**
  - Platform: [ESP8266 / Arduino Nano / other]
  - Firmware Version: [0.5.001]
  - Browser: [Chrome / Firefox / Safari]
  
  **Serial Output** (if applicable)
  ```
  Paste serial output here
  ```
  
  **Additional context**
  Any other context about the problem (screenshots, config files, etc.)
  ```

- [ ] Create `.github/ISSUE_TEMPLATE/feature_request.md`
  ```markdown
  ---
  name: Feature Request
  about: Suggest an idea for this project
  title: "[FEATURE] "
  labels: enhancement
  assignees: ''
  ---
  
  **Is your feature request related to a problem?**
  A clear description of what the problem is. Ex. I'm always frustrated when [...]
  
  **Describe the solution you'd like**
  A clear and concise description of what you want to happen.
  
  **Describe alternatives you've considered**
  Alternative solutions or features you've considered.
  
  **Additional context**
  Any other context or screenshots about the feature request.
  
  **Implementation Considerations**
  - Memory impact: [estimate if known]
  - Complexity: [low / medium / high]
  - Dependencies: [list related features]
  ```

- [ ] Create `.github/ISSUE_TEMPLATE/documentation.md`
  ```markdown
  ---
  name: Documentation Improvement
  about: Suggest improvements to documentation
  title: "[DOCS] "
  labels: documentation
  assignees: ''
  ---
  
  **Which document needs improvement?**
  File name(s) and section(s) that need work.
  
  **What's missing or unclear?**
  Description of the problem with current documentation.
  
  **Suggested improvement**
  What should be added, changed, or removed.
  
  **Target audience**
  Who will benefit from this improvement? (new users, contributors, advanced users)
  ```

- [ ] Create `.github/ISSUE_TEMPLATE/config.yml` (optional - disables blank issues)
  ```yaml
  blank_issues_enabled: false
  contact_links:
    - name: Community Discussion
      url: https://github.com/yourusername/SBAquaControl/discussions
      about: Ask questions or share ideas in discussions
  ```

### Phase 3: Issue Creation - Completed Work (10 min)

**Purpose**: Close these immediately with references to completed PRs/commits

- [ ] **Issue #1**: [BUG] Boot-time OOM crashes during config loading
  - **Labels**: `bug`
  - **Milestone**: `v0.6`
  - **Status**: Closed
  - **Description**:
    ```markdown
    **Problem**: Device crashed during startup with StoreProhibitedCause exception
    
    **Root Cause**: String concatenations in config loading creating temporary heap allocations during init sequence
    
    **Solution**: Replaced `Serial.println(String(F("...")) + String(i))` patterns with separate `Serial.print()` calls
    
    **Files Modified**: [AquaControl.cpp](../src/AquaControl.cpp) (lines 349, 357, 436, 441)
    
    **Result**: Clean boot sequence, no crashes
    
    **Fixed by**: Session 2025-12-30 (see SESSION_SUMMARY_2025-12-30.md)
    ```

- [ ] **Issue #2**: [BUG] Severe RAM over-allocation (82% static usage)
  - **Labels**: `bug`
  - **Milestone**: `v0.6`
  - **Status**: Closed
  - **Description**:
    ```markdown
    **Problem**: Compile-time RAM usage at 82%, leaving only ~28 KB heap
    
    **Root Cause**: `MAX_TARGET_COUNT_PER_CHANNEL = 128` consuming 10.2 KB of SRAM  
    - 16 channels × 128 targets × 5 bytes = 10,240 bytes static allocation
    
    **Solution**: Reduced `MAX_TARGET_COUNT_PER_CHANNEL` from 128 → 32 for ESP8266
    - New allocation: 16 × 32 × 5 = 2,560 bytes
    - Freed: 7,680 bytes (75% reduction)
    
    **Result**: Compile-time RAM usage dropped to 50-55%, heap available ~60-80 KB
    
    **Files Modified**: [AquaControl_config.h](../src/AquaControl_config.h#L21)
    
    **Fixed by**: Session 2025-12-30 (see SESSION_SUMMARY_2025-12-30.md)
    ```

- [ ] **Issue #3**: [BUG] Memory leaks in web API (String concatenation)
  - **Labels**: `bug`
  - **Milestone**: `v0.6`
  - **Status**: Closed
  - **Description**:
    ```markdown
    **Problem**: Streaming JSON handlers building large String objects, fragmenting heap
    
    **Root Cause**: Code like `String item = "{\"time\":" + String(time) + ...`
    
    **Solution**: Converted to `sprintf()` with fixed-size char buffers (48 bytes), stream results directly
    
    **Affected handlers**:
    - `handleApiScheduleGet()` 
    - `handleApiScheduleAll()`
    - `handleApiScheduleSave()`
    
    **Files Modified**: [Webserver.cpp](../src/Webserver.cpp)
    
    **Fixed by**: Session 2025-12-30 (see SESSION_SUMMARY_2025-12-30.md)
    ```

- [ ] **Issue #4**: [BUG] UI-firmware mismatch (spline vs linear interpolation)
  - **Labels**: `bug`, `documentation`
  - **Milestone**: `v0.6`
  - **Status**: Closed
  - **Description**:
    ```markdown
    **Problem**: UI showed smooth spline curves, firmware executed linear interpolation
    
    **Solution**: 
    - Disabled automatic smoothing in Chart Manager
    - Updated `chart-manager.js` to show linear segments only
    - Reduced `maxTargetsPerChannel` from 128 → 32 to match firmware
    
    **Files Modified**: [chart-manager.js](../extras/SDCard/js/chart-manager.js#L1-L16)
    
    **Documentation Added**: UI_UPDATE_LINEAR_INTERPOLATION.md, FIRMWARE_STATUS.md
    
    **Fixed by**: Session 2025-12-30 (see SESSION_SUMMARY_2025-12-30.md)
    ```

### Phase 4: Issue Creation - Steps 4-6 Work (15 min)

**Purpose**: Track current refactoring work, close after PRs merge

- [ ] **Issue #5**: [FEATURE] Macro timer activation implementation
  - **Labels**: `enhancement`
  - **Milestone**: `v0.6`
  - **Status**: Open → Close after Step 4 PR
  - **Description**:
    ```markdown
    **Feature Request**: Implement macro timer system to track temporary lighting overrides
    
    **Current State**: Macros can be created and saved but not executed (API endpoint is stub)
    
    **Requirements**:
    - Add `MacroState` struct to track active macro (startTime, duration, originalTargets)
    - Implement `handleApiMacroActivate()` endpoint
    - Auto-restore previous schedule when duration expires
    - Update `proceedCycle()` to check macro expiration
    
    **Implementation Plan**: See [Step 4 Plan](../.github/plans/step-4-macro-timer.md)
    
    **Memory Impact**: <5KB additional RAM
    
    **Dependencies**: None
    
    **Acceptance Criteria**:
    - [ ] User clicks "Activate" on macro → lighting changes immediately
    - [ ] After duration expires → schedule auto-restores
    - [ ] `/api/status` shows `macro_active: true` and `macro_expires_in: 1234`
    ```

- [ ] **Issue #6**: [FEATURE] Time-setting API endpoint
  - **Labels**: `enhancement`
  - **Milestone**: `v0.6`
  - **Status**: Open → Close after Step 5 PR
  - **Description**:
    ```markdown
    **Feature Request**: Add API endpoint to set system time when RTC unavailable
    
    **Current State**: Manual time setting works via existing UI, but no API endpoint
    
    **Requirements**:
    - Implement `handleApiTimeSet()` endpoint
    - Accept JSON: `{"timestamp": 1704153600}` (Unix timestamp)
    - Update system time via `setTime(timestamp)`
    - Validate timestamp (must be >2020-01-01)
    
    **Implementation Plan**: See [Step 5 Plan](../.github/plans/step-5-time-setting-api.md)
    
    **Use Case**: Allows NTP-free time sync from JavaScript (`Date.now()`)
    
    **Acceptance Criteria**:
    - [ ] POST `/api/time/set` with valid timestamp → system time updates
    - [ ] Invalid timestamp → returns 400 error
    - [ ] `/api/status` shows updated time
    ```

- [ ] **Issue #7**: [REFACTOR] String concatenation cleanup
  - **Labels**: `enhancement`, `good-first-issue`
  - **Milestone**: `v0.7`
  - **Status**: Open → Close after Step 6 PR
  - **Description**:
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
    - [AquaControl.cpp](../src/AquaControl.cpp) (Serial.print statements)
    - [Webserver.cpp](../src/Webserver.cpp) (template replacements)
    
    **Acceptance Criteria**:
    - [ ] No `String(...)` + `String(...)` patterns remain
    - [ ] All dynamic strings use char buffers with size limits
    - [ ] Heap usage stable during continuous operation
    ```

- [ ] **Issue #8**: [DOCS] Add JSDoc comments to JavaScript modules
  - **Labels**: `documentation`, `good-first-issue`
  - **Milestone**: `v0.7`
  - **Status**: Open → Close after Step 6 PR
  - **Description**:
    ```markdown
    **Goal**: Add JSDoc comments to all JavaScript functions for better IDE support
    
    **Files Needing Documentation**:
    - [api.js](../extras/SDCard/js/api.js) (API wrapper functions)
    - [chart-manager.js](../extras/SDCard/js/chart-manager.js) (Chart rendering)
    - [app.js](../extras/SDCard/js/app.js) (Main application logic)
    
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

- [ ] **Issue #9**: [REFACTOR] Remove legacy template system code
  - **Labels**: `enhancement`
  - **Milestone**: `v0.7`
  - **Status**: Open → Close after Step 6 PR
  - **Description**:
    ```markdown
    **Goal**: Remove obsolete template system now that UI uses client-side rendering
    
    **Legacy Code to Remove**:
    - `##PLACEHOLDER##` replacement logic in [Webserver.cpp](../src/Webserver.cpp)
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

### Phase 5: Issue Creation - Future Enhancements (10 min)

**Purpose**: Track long-term roadmap items from PRODUCT.md

- [ ] **Issue #10**: [FEATURE] Timezone and DST support
  - **Labels**: `enhancement`, `help-wanted`
  - **Milestone**: `Future`
  - **Description**:
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

- [ ] **Issue #11**: [FEATURE] Gradient animation effects
  - **Labels**: `enhancement`
  - **Milestone**: `v1.0`
  - **Description**:
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

- [ ] **Issue #12**: [FEATURE] Multi-user authentication
  - **Labels**: `enhancement`, `help-wanted`
  - **Milestone**: `Future`
  - **Description**:
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

- [ ] **Issue #13**: [FEATURE] HTTPS support with self-signed certificates
  - **Labels**: `enhancement`, `help-wanted`
  - **Milestone**: `Future`
  - **Description**:
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

- [ ] **Issue #14**: [FEATURE] UI support for 16 channels (currently 6)
  - **Labels**: `enhancement`
  - **Milestone**: `v1.0`
  - **Description**:
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

- [ ] **Issue #15**: [FEATURE] Macro persistence across power loss
  - **Labels**: `enhancement`
  - **Milestone**: `Future`
  - **Description**:
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

### Phase 6: Documentation Updates (5 min)

- [ ] Update [ROADMAP.md](../ROADMAP.md) to reference issues
  - **Find**: `Timezone/DST support (Phase 3)`
  - **Replace**: `Timezone/DST support (Phase 3) - See #10`
  - **Repeat** for all roadmap items that now have issues

- [ ] Update [MASTERPLAN.md](../.github/MASTERPLAN.md) Step 7 status
  - **Find**: `| 7. GitHub Issues | ⏳ Ready | Plan + Manual | 60 min | ❌ No | Steps 4, 5, 6 |`
  - **Replace**: `| 7. GitHub Issues | ✅ Complete | Plan + Manual | 60 min | ❌ No | Steps 4, 5, 6 |`

- [ ] Create `.github/CONTRIBUTING.md` section on issue workflow
  ```markdown
  ## Issue Workflow
  
  ### Reporting Bugs
  Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md) and include:
  - Steps to reproduce
  - Expected vs. actual behavior
  - Serial output (if applicable)
  - Environment details (platform, firmware version)
  
  ### Requesting Features
  Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md) and consider:
  - Is this aligned with project goals? (See PRODUCT.md)
  - Memory impact on ESP8266 (<80 KB total RAM)
  - Complexity and implementation effort
  
  ### Contributing Code
  1. Check existing issues for related work
  2. Comment on issue to claim it (avoid duplicate work)
  3. Create feature branch: `git checkout -b feature/issue-5-macro-timer`
  4. Follow [coding standards](CONTRIBUTING.md#code-style)
  5. Submit PR with reference: "Fixes #5"
  ```

### Phase 7: Optional Project Board (5 min)

- [ ] Create GitHub Project Board (optional)
  - Navigate to: `Projects > New Project > Board`
  - Name: "SBAquaControl Development"
  - Columns: `Backlog`, `In Progress`, `Review`, `Done`
  
- [ ] Populate board with issues
  - Backlog: All `Future` milestone issues (#10-15)
  - In Progress: Open v0.6 issues (#5-6)
  - Done: Closed v0.6 issues (#1-4)

- [ ] Add automation rules (optional)
  - When issue assigned → move to "In Progress"
  - When PR linked → move to "Review"
  - When issue closed → move to "Done"

---

## Issue Priority Order

### Immediate (Create First)
1. Issue #5 (Macro Timer) - Blocks Step 4
2. Issue #6 (Time API) - Blocks Step 5
3. Issue #7 (String Cleanup) - Blocks Step 6
4. Issue #8 (JSDoc) - Blocks Step 6
5. Issue #9 (Legacy Code) - Blocks Step 6

### Completed Work (Create + Close)
6. Issue #1 (Boot Crash) - Close with SESSION_SUMMARY reference
7. Issue #2 (RAM Usage) - Close with SESSION_SUMMARY reference
8. Issue #3 (Memory Leaks) - Close with SESSION_SUMMARY reference
9. Issue #4 (UI Mismatch) - Close with SESSION_SUMMARY reference

### Future Roadmap (Create Last)
10. Issue #10 (Timezone) - Phase 3
11. Issue #11 (Animations) - Phase 5
12. Issue #12 (Auth) - Phase 4
13. Issue #13 (HTTPS) - Phase 4
14. Issue #14 (16 Channels) - v1.0
15. Issue #15 (Macro Persistence) - Future

---

## Testing & Validation

### Issue Template Testing
- [ ] Create test bug report using template → verify all fields present
- [ ] Create test feature request using template → verify formatting correct
- [ ] Verify blank issues disabled (if config.yml created)

### Label & Milestone Verification
- [ ] All issues have at least one label
- [ ] All issues assigned to a milestone
- [ ] Label colors match GitHub best practices

### Documentation Cross-References
- [ ] All ROADMAP.md references link to issues
- [ ] All issue descriptions link back to relevant files
- [ ] Line number links use correct format (e.g., #L123)

### Board Automation (if created)
- [ ] Assign issue to yourself → moves to "In Progress"
- [ ] Link PR to issue → moves to "Review"
- [ ] Close issue → moves to "Done"

---

## Rollout Strategy

### Phase 1: Foundation (15 min)
Execute tasks from **Phase 1** (labels, milestones) and **Phase 2** (templates)

### Phase 2: Historical Context (10 min)
Create issues #1-4 from **Phase 3** and immediately close with references

### Phase 3: Active Work (15 min)
Create issues #5-9 from **Phase 4** (leave open for Steps 4-6)

### Phase 4: Future Vision (10 min)
Create issues #10-15 from **Phase 5** (assign to `Future` milestone)

### Phase 5: Documentation (5 min)
Update ROADMAP.md and MASTERPLAN.md from **Phase 6**

### Phase 6: Optional Board (5 min)
Create project board from **Phase 7** if desired

**Total Time**: ~60 minutes

---

## Success Criteria

- [ ] All 15 issues created with proper labels and milestones
- [ ] Issue templates available in repository
- [ ] ROADMAP.md references GitHub issues (e.g., "See #10")
- [ ] Completed work (issues #1-4) closed with documentation references
- [ ] Active work (issues #5-9) open and linked to implementation plans
- [ ] Future work (issues #10-15) tracked for community visibility
- [ ] (Optional) Project board visualizes task flow

**Post-Migration**:
- All new bugs/features go through GitHub Issues (not markdown files)
- Contributors can discover work via "good-first-issue" label
- Progress visible via milestone completion percentage
- Pull requests automatically link to issues via "Fixes #N" syntax

---

## Notes

**Manual Execution Required**: Agents cannot create GitHub issues directly (no API access). User must manually create each issue using descriptions provided above.

**Copy-Paste Format**: Each issue description above is formatted as complete markdown ready to paste into GitHub's issue creation form.

**Future Automation**: Consider GitHub CLI (`gh issue create`) or GitHub Actions to automate issue creation from markdown files.

**Backward Compatibility**: Keep ROADMAP.md as high-level overview for quick reference. Issues contain detailed implementation notes.
