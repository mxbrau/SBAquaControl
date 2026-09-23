# SBAquaControl Development Roadmap

**Current Version**: 0.5.001
**Status**: ✅ Stable with all core features implemented
**Next Milestone**: Phase 2 - Enhanced Visualization (next)

---

## Version History

### v0.5.001 (Current - January 2026)
**Focus**: Core Feature Completion & Stability

**Achievements**:
- ✅ Fixed critical OOM crashes during boot
- ✅ Optimized ESP8266 RAM usage (82% → ~56%)
- ✅ Implemented streaming JSON API (no large String allocations)
- ✅ Updated UI to show linear interpolation only (matches firmware)
- ✅ **Implemented hybrid time synchronization** (NTP → RTC → API fallback)
- ✅ **Implemented macro timer system** with activation/stop/auto-restore
- ✅ **Implemented time-setting API** (`/api/time/set`)
- ✅ Comprehensive testing documentation

**Known Limitations**:
- Linear interpolation only (no smooth curves)
- 32 targets per channel maximum
- No seasonal adjustments
- No temperature-based compensation

---

## Phase 2: Enhanced Visualization (next)

### Goal
Add **optional** spline smoothing to UI while keeping firmware simple

### Architecture Overview

```
User Workflow:
    Create Schedule (10 control points)
              ↓
        [Linear / Smooth selector]
              ↓
    ┌─────────────────┬─────────────┐
    ↓                 ↓
[Linear Mode]    [Smooth Mode]
(Current)         (New - Phase 2)
    ↓                 ↓
Show linear      Apply spline
lines to chart   algorithm
    ↓                 ↓
Save 10           Generate
targets           100+ samples
    ↓                 ↓
Device runs      Send all samples
linear           to device
interpolation    ↓
    ↓             Device stores
Looks angular    100+ samples
                 ↓
                 Device runs
                 linear interpolation
                 ↓
                 Looks smooth!
```

### Key Features
1. **Dual Mode Support**
   - Linear: Fast, simple, transparent
   - Smooth: Beautiful curves, client-side computation

2. **Spline Algorithm Options**
   - Catmull-Rom (recommended - natural looking)
   - B-Spline (smooth, stable)
   - Cubic Hermite (preserves monotonicity)

3. **Sampling Strategy**
   - Variable density (5-10 second intervals typical)
   - Respects 32-target limit
   - Smart reduction if too many samples

### Implementation Tasks

#### Task 2.1: Add Spline Library
**Files**: `extras/SDCard/js/spline.js` (new)

```javascript
// Catmull-Rom spline implementation
function catmullRom(p0, p1, p2, p3, t) {
    // Standard Catmull-Rom basis functions
    // ...
}

// Generate samples between control points
function generateSplineSamples(controlPoints, samplesPerSegment) {
    // Use Catmull-Rom to interpolate
    // Return densified array
}
```

**Effort**: 2-3 hours
**Test**: Verify smooth curves, monotonicity preservation

---

#### Task 2.2: Update UI Controls
**Files**: `extras/SDCard/app.htm` (modify schedule section)

```html
<!-- Add interpolation mode selector -->
<div class="interpolation-mode">
    <label>
        <input type="radio" name="mode" value="linear" checked>
        📈 Linear (Straight lines)
    </label>
    <label>
        <input type="radio" name="mode" value="smooth">
        🎨 Smooth (Spline curves)
    </label>
</div>

<!-- Sampling density slider (for smooth mode) -->
<div id="smoothSettings" class="hidden">
    <label>Sampling Interval:</label>
    <input type="range" min="1" max="20" value="5">
    <span id="samplingInfo">Every 5 seconds</span>
</div>
```

**Effort**: 1-2 hours
**Test**: UI visibility, toggle behavior

---

#### Task 2.3: Update ChartManager
**Files**: `extras/SDCard/js/chart-manager.js` (extend, not replace)

```javascript
class ChartManager {
    constructor(canvasId, interpolationMode = 'linear') {
        this.interpolationMode = interpolationMode;  // 'linear' or 'smooth'
        this.samplingInterval = 5;                   // seconds
        // ... existing code ...
    }

    // Updated method
    generateSamples(points, mode = 'linear') {
        if (mode === 'linear') {
            return this.generateLinearSamples(points);   // existing
        } else if (mode === 'smooth') {
            return this.generateSplineSamples(points);   // new
        }
    }

    // New method
    generateSplineSamples(controlPoints) {
        // Use Catmull-Rom or B-Spline
        // Sample at intervals defined by this.samplingInterval
        // Return densified point array
    }
}
```

**Effort**: 3-4 hours
**Test**: Visual accuracy, boundary conditions

---

#### Task 2.4: Backend Support
**Files**: `src/Webserver.cpp` (new endpoint)

```cpp
// New API endpoint for spline generation
void handleApiScheduleGenerate() {
    // Receive control points + spline params
    // Request format: {channel, controlPoints, samplesPerSegment}
    // Perform spline computation
    // Return densified targets

    // Alternative: Offload to client only (no firmware changes needed)
}
```

**Effort**: 2-3 hours (or skip if client-side only)
**Note**: Client-side spline is preferred (no firmware load)

---

### Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Spline doesn't fit in RAM | Medium | High | Test with actual data; implement sampling reduction |
| Wrong sample density | Medium | Medium | Provide UI preview; show sample count |
| Firmware changes break compatibility | Low | High | Keep firmware UNCHANGED; all logic client-side |
| User confusion (linear vs smooth) | Medium | Low | Clear labeling; save mode choice per channel |

---

## Phase 3: Macro System & Dynamic Curves (Q1-Q2 2026) - ✅ COMPLETED

### Status: ✅ COMPLETED (January 2026)

All macro system features have been implemented:

**Completed Features**:
- ✅ Macro creation wizard UI
- ✅ Macro persistence to SD card
- ✅ Runtime macro activation with timer tracking
- ✅ Auto-restore after duration expires
- ✅ Manual stop functionality
- ✅ UI banner & countdown display
- ✅ API endpoints: list, get, save, activate, stop, delete

**Implementation Files**:
- `src/AquaControl.h` - MacroState struct and tracking
- `src/AquaControl.cpp` - Macro file I/O and lifecycle
- `src/Webserver.cpp` - API endpoints (handleApiMacro*)
- `extras/SDCard/js/app.js` - Macro wizard and activation UI

### Architecture (As Implemented)

```
User clicks: [Movie Mode 🎬]
    ↓
POST /api/macro/activate {id, duration}
    ↓
Backend loads macro configs from SD
    ↓
_activeMacro.isActive = true
_activeMacro.expiresAt = now() + duration
    ↓
proceedCycle() prioritizes macro targets
    ↓
Timer counts down (visible in UI)
    ↓
When expired: auto-restore to regular schedule
    ↓
Banner shows: "Movie Mode - 1:45 remaining"
```

**Data Storage**: `macros/macro_NNN_chNN.cfg` (duration-based format)

---

## Phase 4: Seasonal & Environmental Profiles (after v0.5.x hardening)

### Goal
Support varying light schedules based on season or conditions

### Features

#### Seasonal Adjustment
```
Base Schedule: Sunrise at 08:00, Sunset at 18:00
    ↓
Summer (long days): Sunrise 06:30, Sunset 20:30
Autumn (medium): Sunrise 07:30, Sunset 18:30
Winter (short days): Sunrise 08:30, Sunset 16:30
Spring (medium): Sunrise 07:30, Sunset 18:30
```

#### Temperature-Based Compensation
```
Normal: Target = 80%
Water too warm (28°C): Reduce intensity by 10% → 70%
Water too cold (22°C): Increase intensity by 5% → 85%

PID feedback loop:
error = targetTemp - currentTemp
correction = P×error + I×integral(error) + D×derivative(error)
intensity = baseIntensity + correction
```

#### Time Zone Support
```
Web UI: Input local timezone
Device: Stores UTC time from RTC
Display: Shows user's local time
Schedules: Always in local timezone
```

### Implementation
**Effort**: 6-8 weeks (lower priority)

---

## Phase 5: Advanced Features (future)

### Possible Enhancements

- **Multi-Tank Profiles**: Different schedules per physical tank section
- **Photo Period Simulation**: Accurate sunrise/sunset timing for specific locations
- **Lunar Cycle Support**: Moonlight effects following real moon phases
- **Water Parameter Integration**: Link brightness to pH, NH3, etc.
- **AI-Powered Scheduling**: ML model predicts optimal schedules for species
- **Community Schedule Sharing**: Download/share tested profiles
- **Mobile App**: iOS/Android native app for control on-the-go
- **Cloud Integration**: Remote monitoring across multiple systems
- **Gradient Animation Effects**: smooth color transitions beyond linear fades (from retired MASTERPLAN)
- **Multi-User Authentication**: password/role separation for the web UI (from retired MASTERPLAN)
- **HTTPS Support**: TLS for the ESP8266 web server (from retired MASTERPLAN)
- **16-Channel UI**: manage all 16 firmware channels, not just the 6 visible today (from retired MASTERPLAN)
- **Macro Persistence Across Power Loss**: resume interrupted macros after reboot (from retired MASTERPLAN)

---

## Development Guidelines

### For All Phases

#### Code Quality
- ✅ Keep firmware changes minimal (reduce complexity, bugs)
- ✅ Offload computation to client when possible
- ✅ Test memory usage before adding features
- ✅ Document all changes thoroughly

#### Backward Compatibility
- ✅ Old firmware must work with new UI (or clearly warn)
- ✅ Old UI must work with new firmware
- ✅ Configuration format versioning
- ✅ Graceful fallback for missing features

#### Performance
- ✅ API responses <200ms
- ✅ Chart render <100ms
- ✅ File operations <1s
- ✅ No memory leaks over 8+ hours

#### Testing
- ✅ Unit tests for algorithms
- ✅ Integration tests for workflows
- ✅ Hardware tests with actual LEDs
- ✅ Load tests for concurrent operations

---

## Timeline Summary

```
v0.5.001 (released January 2026 - STABLE)
├─ ✅ Core feature completion
├─ ✅ Macro timer system implemented
├─ ✅ Hybrid time sync implemented
├─ ✅ Stability & optimization
└─ ✅ Host unit-test harness (test/test_host_unit.py, always run by `pytest`)

Next: Phase 2 - Enhanced Visualization
├─ Optional spline smoothing
├─ Dual mode (linear/smooth)
└─ Client-side algorithms

Completed: Phase 3 - Macro System
├─ ✅ Macro system implemented
├─ ✅ Temporary overrides working
└─ ✅ Smart auto-restore

Later: Phase 4 - Seasonal Support
├─ Date-based adjustments
├─ Temperature feedback
└─ Timezone support

Future: Phase 5 - Advanced Features
├─ Mobile app
├─ AI scheduling
├─ Community profiles
└─ Cloud integration
```

---

## Success Metrics

### Phase 3 (Macro System) - ✅ COMPLETED
- ✅ Macros activate within 1 second
- ✅ Fade-back smooth and natural
- ✅ Timer tracking functional
- ✅ All API endpoints working
- ✅ Auto-restore implemented

### Phase 2 (Enhanced Visualization) - NEXT
- ⬜ Smooth curves render correctly
- ⬜ Sample generation completes <500ms
- ⬜ User can easily toggle modes
- ⬜ Device still executes linear interpolation
- ⬜ No firmware modifications required

### Phase 4 (Seasonal Support) - later
- ⬜ Seasonal adjustments intuitive
- ⬜ Temperature feedback stable (<2% error)
- ⬜ Multiple timezones supported
- ⬜ Persistence reliable

---

## Decision Checkpoints

At each phase boundary, evaluate:

1. **Does the feature add real value?**
   - User demand
   - Maintenance burden
   - Code complexity

2. **Can we implement it safely?**
   - Memory constraints
   - Firmware stability
   - Backward compatibility

3. **Is the implementation elegant?**
   - Code clarity
   - Documentation
   - Testing coverage

4. **Is performance acceptable?**
   - Response times
   - Memory usage
   - Power consumption

5. **Do users understand it?**
   - UI clarity
   - Help documentation
   - Learning curve

---

## Contributing

Guidelines for future developers:

1. **Start with Phase 1 (v0.5.001)**
   - Understand the architecture
   - Run full test suite
   - Verify stability

2. **Choose a phase**
   - Pick Phase 2, 3, or 4
   - Follow implementation plan
   - Create feature branch

3. **Implement systematically**
   - Follow code guidelines
   - Test thoroughly
   - Document changes
   - Update this roadmap

4. **Get feedback**
   - Submit PR with test results
   - Ask for code review
   - Address concerns
   - Merge to main

---

## References

- **Current Source**: [src/](../../src/)
- **UI Source**: [extras/SDCard/](../../extras/SDCard/)
- **Testing Guide**: [TESTING_GUIDE.md](TESTING_GUIDE.md)
- **Firmware Status**: [FIRMWARE_STATUS.md](FIRMWARE_STATUS.md)
- **UI Updates**: [UI_UPDATE_LINEAR_INTERPOLATION.md](../design/UI_UPDATE_LINEAR_INTERPOLATION.md)

---

**Document Version**: 2.0
**Last Updated**: 2026-01-05
**Status**: Phase 3 completed, Phase 4 ready for planning
