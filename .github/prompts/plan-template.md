---
title: [Short descriptive title of the feature or bug fix]
version: 1.0
date_created: YYYY-MM-DD
last_updated: YYYY-MM-DD
---

# Implementation Plan: [Feature/Bug Name]

## Overview
Brief 2-3 sentence description of what this plan accomplishes, why it matters, and what problem it solves.

**Example**: This plan adds a macro timer system that tracks when a temporary lighting override (macro) is activated and automatically restores the previous schedule when the duration expires. Currently, macros can be created and saved but not executed.

---

## Requirements

### Functional Requirements
- What the feature must do (user-facing behavior)
- Example: "When user clicks 'Activate' on a macro, the lighting pattern should run for the specified duration, then automatically restore the previous schedule"

### Non-Functional Requirements
- Memory constraints: "Must not exceed 20KB additional RAM"
- Performance: "Macro activation should respond in <500ms"
- Persistence: "Macro timer state must survive power loss" (if applicable)

**Example**:
- Memory: Macro state tracking should add <5KB
- Response time: API endpoint should respond in <100ms
- Persistence: Not required (timer resets on power loss)

---

## Architecture and Design

### High-Level Design
Describe how the feature fits into the existing architecture:
- What classes/functions will be modified or created?
- What data structures are needed?
- How does it interact with existing systems?

**Example**:
```
Add MacroState struct to AquaControl class:
  - active: bool (is a macro currently running?)
  - startTime: uint32_t (Unix timestamp when macro activated)
  - duration: uint32_t (seconds until macro expires)
  - originalTargets[]: PwmChannel array (to restore after expiration)

Modify proceedCycle() to check if macro is expired and auto-restore.
Implement handleApiMacroActivate() endpoint (currently stub).
```

### Key Algorithms
- Linear interpolation reference: [AquaControl.cpp#L810-L890](../../src/AquaControl.cpp#L810)
- Tick-tock async reference: [TemperatureReader](../../src/AquaControl.cpp#L608)
- File I/O pattern reference: [writeWlanConfig()](../../src/AquaControl.cpp#L290)

### Design Decisions
- Why char buffers instead of String? (memory safety)
- Why streaming JSON instead of building strings? (RAM constraints)
- Why this particular timing approach? (non-blocking main loop)

---

## Implementation Tasks

Break implementation into checklist items. Each should be ~30-60 minutes of work.

### Phase 1: Data Structures and Init
- [ ] Add `MacroState` struct to [AquaControl.h](../../src/AquaControl.h#L100)
  - Fields: `active`, `startTime`, `duration`, `originalTargets[]`
  - Location: After `PwmChannel` class definition
  
- [ ] Add member variable to `AquaControl` class
  - `MacroState _activeMacro;`
  - Initialize in constructor

- [ ] Add macro state check in `proceedCycle()` [AquaControl.cpp#L600]
  - Check if macro is active and duration expired
  - Call new function `restoreSchedule()` if expired

### Phase 2: API Endpoints
- [ ] Implement `handleApiMacroActivate()` in [Webserver.cpp#L1028]
  - Parse JSON body: `{"id": "macro_001", "channel": 0}`
  - Load macro targets from SD card
  - Set `_activeMacro.active = true`, `startTime = now()`
  - Return: `{"status": "ok", "expires_in": 7200}`

- [ ] Implement auto-restore in `proceedCycle()`
  - Check: `if (_activeMacro.active && (now() - _activeMacro.startTime) > _activeMacro.duration)`
  - Call `restoreSchedule()` and set `_activeMacro.active = false`

- [ ] Update `handleApiStatus()` to include macro state
  - Add to JSON response: `"macro_active": true, "macro_expires_in": 1234`

### Phase 3: Macro Stop Functionality
- [ ] Implement `handleApiMacroStop()` in [Webserver.cpp#L1036]
  - Set `_activeMacro.active = false`
  - Call `restoreSchedule()` immediately
  - Return: `{"status": "ok"}`

### Phase 4: Helper Functions
- [ ] Implement `restoreSchedule()` in [AquaControl.cpp]
  - Restore original targets to all channels from `_activeMacro.originalTargets[]`
  - Clear `_activeMacro` state
  - Mark channels as needing PWM update

### Phase 5: Testing
- [ ] Manual test: Activate macro, verify lights change
- [ ] Manual test: Wait for duration, verify auto-restore
- [ ] Manual test: Stop macro early, verify immediate restore
- [ ] Build test: `pio run -e esp8266 --target upload`

---

## Testing Strategy

### Unit Tests
- Timestamp comparison logic (macro expiration)
- Target restoration logic

### Integration Tests
- End-to-end: Create macro → Activate → Auto-restore
- Edge cases:
  - Activate macro with 0-second duration (should expire immediately?)
  - Power loss during macro (state lost, is that OK?)
  - Overlapping macro activations (only one active at a time?)

### Manual Tests
1. Open web UI
2. Click "Macros" → "Movie Mode" (pre-existing macro)
3. Click "Activate"
   - Verify lights change to macro pattern
   - Verify countdown timer appears
   - Verify API response includes `expires_in` value
4. Wait for timer to expire
   - Verify lights restore to previous schedule
   - Verify macro no longer shows as active
5. Click "Create Macro" → set 30-second duration
6. Activate new macro
7. Click "Stop" immediately
   - Verify lights restore instantly
   - Verify macro state cleared

---

## Open Questions

1. **On power loss during macro**: Should the timer persist to SD card, or is it OK to lose state? (Recommend: OK to lose, simpler)

2. **Multiple macro activations**: If user clicks "Activate" twice, should it extend the timer or replace it? (Recommend: Replace/reset the timer)

3. **Macro storage format**: Should macro duration be stored in the `.cfg` file, or added as a separate `_meta.json`? (Recommend: `meta.json` to avoid changing existing file format)

---

## Success Criteria

✅ All tasks in "Implementation Tasks" completed  
✅ No compiler errors or warnings (esp8266 target)  
✅ Manual tests pass (lights change, restore, stop works)  
✅ Memory usage doesn't exceed +5KB  
✅ Response time <100ms for API calls  
✅ Code follows naming conventions and patterns  
✅ No `String` concatenation in new code  
✅ Ready for code review  

---

## Dependencies & Blockers

- Depends on: existing macro file system (already working)
- Blocked by: none
- Unblocks: Phase 3 (time-setting API) builds on macro timer foundation

---

## Notes

- Reference the linear interpolation pattern for any value transitions
- Use `now()` from TimeLib for timestamp comparisons
- Remember 60-second test mode auto-timeout for comparison
- Streaming JSON will be important if macro count grows large
