# Macro Edit Empty Chart Fix Plan

## Problem Summary
When editing an existing macro, the chart appears empty with no time axis. Investigation reveals the root cause: the `/api/macro/get` endpoint returns targets without the `isControl` flag, while the chart's `updateChannel()` method requires this flag to identify control points.

## Root Cause Analysis

### Backend Issue
**File**: [src/Webserver.cpp#L926](src/Webserver.cpp#L926)

The macro GET endpoint sends targets like:
```json
{"time":300,"value":50}
```

But should send:
```json
{"time":300,"value":50,"isControl":true}
```

### Frontend Expectation
**File**: [extras/SDCard/js/chart-manager.js#L121-L157](extras/SDCard/js/chart-manager.js#L121-L157)

The `updateChannel()` method checks for `isControl` flag:
```javascript
const controlPointsPresent = points.some(p => p.isControl === true);

if (controlPointsPresent) {
    controlPoints = points.filter(p => p.isControl);
    samples = this.generateMonotoneSamples(controlPoints);
} else {
    // Treats as pre-sampled - but macro data isn't sampled!
    controlPoints = [];
    samples = points;  // Raw points without proper chart structure
}
```

When `isControl` is missing:
1. Chart treats data as "pre-sampled" (not control points)
2. Sets `controlPoints = []` (empty)
3. Uses raw `points` as samples
4. Chart fails to render properly because samples lack proper structure

### Comparison with Schedule Endpoints
Schedule endpoints correctly include `isControl`:
- [src/Webserver.cpp#L258](src/Webserver.cpp#L258): `/api/schedule/get` ✅
- [src/Webserver.cpp#L287](src/Webserver.cpp#L287): `/api/schedule/all` ✅
- [src/Webserver.cpp#L926](src/Webserver.cpp#L926): `/api/macro/get` ❌

## Implementation Plan

### Task 1: Add isControl Flag to Macro GET Response
**File**: [src/Webserver.cpp#L926](src/Webserver.cpp#L926)

Change:
```cpp
sprintf(buf, "{\"time\":%ld,\"value\":%d}", timeVal, value);
```

To:
```cpp
sprintf(buf, "{\"time\":%ld,\"value\":%d,\"isControl\":true}", timeVal, value);
```

This aligns macro responses with schedule responses and ensures the chart recognizes targets as control points.

### Task 2: Verify Chart Behavior
**File**: [extras/SDCard/js/chart-manager.js#L121-L157](extras/SDCard/js/chart-manager.js#L121-L157)

After fix, verify that `updateChannel()`:
1. Detects `isControl === true` in incoming data
2. Extracts control points correctly
3. Generates monotone samples
4. Renders chart with proper time axis and markers

## Testing Strategy

### Manual Testing
1. Create a macro with 2-3 targets via wizard
2. Save macro
3. Click "Edit" on the macro
4. Verify:
   - Chart displays with proper time axis (0 to duration)
   - Control points appear as markers
   - Lines connect points correctly
   - Dragging points works
   - Time values match saved targets

### Browser Console Verification
1. Open DevTools Network tab
2. Edit a macro
3. Check `/api/macro/get?id=macro_XXX` response
4. Verify each target includes `"isControl":true`

### Regression Testing
- Regular schedules still load correctly
- Macro creation wizard works
- Macro activation works
- Macro deletion works

## Expected Outcome
After applying the fix:
- Editing macros displays populated chart with time axis
- Control points are visible and draggable
- Chart behavior matches schedule editor
- No empty/broken charts when editing existing macros

## Implementation Time
**Estimated**: 5 minutes (single-line change + build/upload)
