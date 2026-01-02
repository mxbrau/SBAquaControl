# SBAquaControl Refactoring Masterplan

**Created**: 2026-01-02  
**Updated**: 2026-01-02 (corrected Step 2/3 sequencing + standardized file naming)  
**Status**: Step 1 Complete, Steps 2-7 Ready for Execution  
**Total Estimated Time**: 7-9 hours across multiple sessions

---

## Executive Summary

This masterplan organizes the SBAquaControl refactoring into 7 major steps with **3 parallel workstreams** to maximize efficiency. The foundation (Step 1) is complete, enabling immediate parallel execution of documentation and feature tracks.

**Completed**: ✅ Step 1 (Context Engineering Foundation)  
**Ready for Parallel**: Steps 3, 4, 5 (3 simultaneous sessions possible)  
**Sequential**: Step 2 (after 3), Steps 6 & 7 (wait for features to stabilize)

---

## Dependency Graph

```
┌─────────────────────────────────────────┐
│ Step 1: Foundation ✅ COMPLETE          │
│ Duration: 90 min (completed 2026-01-02) │
└─────────────┬───────────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌─────────────┐   ┌─────────────────────┐
│ DOC TRACK   │   │ FEATURE TRACK       │
│ (Sequential)│   │ (Parallel possible) │
└─────────────┘   └─────────────────────┘
    │                   │
    │         ┌─────────┴─────────┐
    │         │                   │
    ▼         ▼                   ▼
┌──────────┐ ┌──────────┐  ┌──────────┐
│ Step 3:  │ │ Step 4:  │  │ Step 5:  │
│ Docs     │ │ Macro    │  │ Time API │
│ Cleanup  │ │ Timer    │  │ (105 min)│
│ (75 min) │ │ (120 min)│  └──────────┘
└──────────┘ └──────────┘        │
    │              │              │
    ▼              └──────┬───────┘
┌──────────┐             │
│ Step 2:  │             ▼
│ Learning │    ┌─────────────────┐
│ Guide    │    │ Step 6: Code    │
│ (60 min) │    │ Standardization │
└──────────┘    │ (150 min)       │
    │           └─────────────────┘
    │                   │
    └──────────┬─────────┘
               ▼
     ┌──────────────────┐
     │ Step 7: GitHub   │
     │ Issues (60 min)  │
     └──────────────────┘
```

**Key Change**: Step 3 (Docs Cleanup) now **precedes** Step 2 (Learning Guide) because clean, consolidated documentation provides a better foundation for creating the learning guide.

---

## Steps Overview

| Step | Status | Agent(s) | Duration | Parallel? | Dependencies |
|------|--------|----------|----------|-----------|--------------|
| 1. Foundation | ✅ Complete | Manual | 90 min | N/A | None |
| 3. Docs Cleanup | ⏳ Ready | Plan + Implement | 75 min | ✅ Yes | Step 1 |
| 2. Learning Guide | ⏳ Ready | Plan + Learn | 60 min | ❌ No | **Step 3** |
| 4. Macro Timer | ⏳ Ready | Plan + Implement + Review | 120 min | ✅ Yes | Step 1 |
| 5. Time API | ⏳ Ready | Plan + Implement + Review | 105 min | ✅ Yes | Step 1 |
| 6. Code Standards | ⏳ Ready | Plan + Implement + Review | 150 min | ❌ No | Steps 4, 5 |
| 7. GitHub Issues | ⏳ Ready | Plan + Manual | 60 min | ❌ No | Steps 4, 5, 6 |

**Note**: Step numbers preserved from original plan (2-7) for consistency, but execution order is now: 3 → 2.

---

## Step 1: Context Engineering Foundation ✅

**Status**: COMPLETE  
**Completed**: 2026-01-02

### Deliverables ✅
- [x] ARCHITECTURE.md (system design)
- [x] PRODUCT.md (user features)
- [x] CONTRIBUTING.md (developer guide)
- [x] .github/copilot-instructions.md (updated)
- [x] .github/learning-progress.md (tracking)
- [x] .github/agents/ (4 custom agents)
- [x] .github/prompts/plan-template.md

**Unlocks**: All subsequent steps

---

## Step 3: Documentation Consolidation 📝

**Agent**: Planner → Implementer  
**Duration**: 60-75 min  
**Can Start**: ✅ Immediately  
**Parallel**: ✅ Yes with Steps 4, 5  
**Plan File**: [step-03-documentation-consolidation.md](step-03-documentation-consolidation.md)

### Objective
Consolidate redundant docs, archive summaries, improve structure to create clean foundation for Step 2.

### Why First?
Step 2 (Learning Guide) benefits from:
- ✅ Clean documentation to reference (no README/QUICKSTART redundancy)
- ✅ Clear file structure to link to (`docs/design/`, `docs/reference/`, `docs/status/`)
- ✅ Cross-referenced docs (ARCHITECTURE ↔ PRODUCT ↔ CONTRIBUTING)
- ✅ Archived session summaries (reduced noise)

### Tasks
1. Archive 23 session summaries to `.github/archives/`
2. Merge README + QUICKSTART (preserve German content)
3. Reorganize specialized docs to subdirectories
4. Remove Arduino IDE references
5. Add cross-reference links between core docs

### Deliverables
- [x] Plan: `step-03-documentation-consolidation.md`
- [ ] Merged README.md
- [ ] Archived summaries
- [ ] Reorganized doc structure: `docs/design/`, `docs/reference/`, `docs/status/`
- [ ] Cross-reference links added

---

## Step 2: Physics-Oriented Learning Guide 📚

**Agent**: Planner → Learn Agent  
**Duration**: 45-60 min  
**Can Start**: ❌ After Step 3 complete  
**Parallel**: ❌ No (depends on Step 3)  
**Plan File**: [step-02-learning-guide.md](step-02-learning-guide.md)

### Objective
Create `LEARNING_GUIDE.md` with physicist-friendly explanations of embedded concepts using actual codebase examples and clean documentation structure from Step 3.

### Topics (10)
1. Linear Interpolation → Physics: position/velocity calculations
2. Time Representation → Physics: absolute vs relative reference frames
3. Main Loop Architecture → Physics: stroboscopic measurement
4. I2C Communication → Physics: CAMAC/VME shared bus
5. Conditional Compilation → Physics: detector-specific code
6. PWM Hardware Abstraction → Physics: detector calibration layers
7. Memory Management → Physics: pre-allocated DAQ buffer pools
8. JSON Streaming → Physics: streaming detector data
9. Tick-Tock Async → Physics: oscilloscope double-buffering
10. File I/O Atomicity → Physics: write-ahead logging in DAQ systems

### Deliverables
- [x] Plan: `step-02-learning-guide.md`
- [ ] LEARNING_GUIDE.md with 10 topics
- [ ] Each topic: Concept, Physics Analogy, Why/How, Code Example (file:line), Pitfalls, See Also
- [ ] ADHD-optimized (scannable, bold takeaways)

---

## Step 4: Macro Timer System 🐛

**Agent**: Planner → Implementer → Reviewer  
**Duration**: 90-120 min  
**Can Start**: ✅ Immediately (**HIGHEST PRIORITY**)  
**Parallel**: ✅ Yes with Steps 3, 5  
**Plan File**: [step-04-macro-timer-system.md](step-04-macro-timer-system.md)

### Objective
Fix critical bug: implement macro activation, timer, auto-restore.

### Current Bugs
- ❌ `handleApiMacroActivate()` stub (Webserver.cpp:1028)
- ❌ `handleApiMacroStop()` stub (Webserver.cpp:1036)
- ❌ No timer tracking
- ❌ Duration not persisted

### Implementation Phases
1. Add `MacroState` struct (AquaControl.h)
2. Implement `handleApiMacroActivate()`
3. Auto-restore in `proceedCycle()`
4. Implement `handleApiMacroStop()`
5. Update `/api/status` endpoint

### Deliverables
- [x] Plan: `step-04-macro-timer-system.md`
- [ ] MacroState struct (3KB RAM)
- [ ] Working macro activation
- [ ] Auto-restore after duration
- [ ] Manual stop functionality
- [ ] Memory budget: <5KB additional RAM

---

## Step 5: Time-Setting API 🕐

**Agent**: Implementer → Reviewer  
**Duration**: 90-105 min  
**Can Start**: ✅ Immediately  
**Parallel**: ✅ Yes with Steps 3, 4  
**Plan File**: [step-05-time-setting-api.md](step-05-time-setting-api.md)

### Objective
Add `/api/time/set` endpoint to update DS3231 RTC via web UI.

### Current Issue
- ❌ No API to set time
- ❌ Requires external RTC programmer

### Implementation Phases
1. Core `setRTCTime()` method (20 min)
2. JSON API handler (30 min)
3. Route registration (10 min)
4. Integration testing (30 min)
5. Documentation (15 min)

### Deliverables
- [x] Plan: `step-05-time-setting-api.md`
- [ ] `handleApiTimeSet()` in Webserver.cpp
- [ ] JSON parsing + validation
- [ ] RTC.set() integration + TimeLib sync
- [ ] Time persists across power loss
- [ ] Memory budget: <100 bytes additional RAM

---

## Step 6: Code Standardization 🧹

**Agent**: Planner → Implementer → Reviewer  
**Duration**: 120-150 min  
**Can Start**: ❌ After Steps 4 & 5 complete  
**Parallel**: ❌ No (avoid merge conflicts in Webserver.cpp)  
**Plan File**: [step-06-code-standardization.md](step-06-code-standardization.md)

### Objective
Enforce memory-safe patterns, remove legacy code, add documentation.

### Current Issues
- ⚠️ String concatenation (heap fragmentation risk)
- ⚠️ 40% of AquaControlSketch.ino commented out
- ⚠️ Macro id/name semantically unclear
- ⚠️ Missing JSDoc in JavaScript

### Implementation Phases
1. String safety audit
2. Replace String with char buffers
3. Remove commented code
4. Normalize macro id/name
5. Add JSDoc to JS files
6. Add function comments to C++

### Deliverables
- [x] Plan: `step-06-code-standardization.md`
- [ ] Zero String concatenation in production paths
- [ ] Clean AquaControlSketch.ino (from 56 to ~15 lines)
- [ ] JSDoc in all JS files (app.js, chart-manager.js, api.js)
- [ ] Function comments in C++ files
- [ ] Memory audit shows 2-5KB reduction

---

## Step 7: GitHub Issues Migration 📋

**Agent**: Planner → Manual  
**Duration**: 60 min  
**Can Start**: ❌ After Steps 4, 5, 6 complete  
**Parallel**: ❌ No (references completed work)  
**Plan File**: [step-07-github-issues-migration.md](step-07-github-issues-migration.md)

### Objective
Migrate all bugs, features, and improvement tasks from local markdown files to GitHub Issues for transparent tracking and community collaboration.

### Issues to Create (15 total)

**Completed Work** (create + close immediately):
- ✅ Issue #1: Boot-time OOM crashes
- ✅ Issue #2: Severe RAM over-allocation
- ✅ Issue #3: Memory leaks in web API
- ✅ Issue #4: UI-firmware mismatch

**Active Work** (Steps 4-6):
- ⏳ Issue #5: Macro timer activation
- ⏳ Issue #6: Time-setting API endpoint
- ⏳ Issue #7: String concatenation cleanup
- ⏳ Issue #8: JSDoc comments
- ⏳ Issue #9: Legacy code removal

**Future Roadmap**:
- 📋 Issue #10: Timezone/DST support
- 📋 Issue #11: Gradient animation effects
- 📋 Issue #12: Multi-user authentication
- 📋 Issue #13: HTTPS support
- 📋 Issue #14: UI manages 16 channels
- 📋 Issue #15: Macro persistence across power loss

### Deliverables
- [x] Plan: `step-07-github-issues-migration.md`
- [x] Issue templates: bug_report.md, feature_request.md, documentation.md
- [x] Quick reference: Step 7/ISSUE_QUICK_REFERENCE.md
- [ ] GitHub issues created (manual execution)
- [ ] Labels and milestones configured
- [ ] Updated ROADMAP.md with issue references

---

## Parallelization Strategy

### ✅ **Phase 1: Immediate Parallel Execution (3 Sessions)**

**Session A (Doc Track)** — 135 min total
1. **First**: Step 3: Docs Consolidation (75 min)
   - Clean up documentation structure
   - Archive session summaries
   - Merge README + QUICKSTART
   - Add cross-references
2. **Then**: Step 2: Learning Guide (60 min)
   - Create LEARNING_GUIDE.md using clean docs as foundation
   - Reference consolidated documentation structure

**Session B (Critical Bug)** — 120 min
- Step 4: Macro Timer (**Highest Priority**)
- Fix stubbed endpoints
- Implement timer + auto-restore

**Session C (Feature)** — 105 min
- Step 5: Time-Setting API
- Add POST /api/time/set endpoint
- RTC integration

**Total parallelized time**: ~135 min (longest session A) vs 420 min sequential  
**Time savings**: ~285 min (~4.75 hours)

### ⏳ **Phase 2: Sequential After Features (2 Sessions)**

**Session D (Code Quality)** — 150 min
- Step 6: Code Standardization
- **Dependencies**: Steps 4 & 5 merged (avoid conflicts in Webserver.cpp)
- String safety + JSDoc + legacy code removal

**Session E (Project Mgmt)** — 60 min
- Step 7: GitHub Issues Migration
- **Dependencies**: Steps 4, 5, 6 complete (references completed work)
- Manual execution (copy-paste issue templates)

---

## File Naming Convention

All implementation plans follow this format:
- `step-NN-descriptive-name.md`

**Current Plans**:
- ✅ `step-02-learning-guide.md`
- ✅ `step-03-documentation-consolidation.md`
- ✅ `step-04-macro-timer-system.md`
- ✅ `step-05-time-setting-api.md`
- ✅ `step-06-code-standardization.md`
- ✅ `step-07-github-issues-migration.md`

---

## This Session: Plan Generation (60-90 min)

### Plans to Create (6 total)

1. ✅ `step-05-time-setting-api.md` — Time API endpoint
2. ✅ `step-04-macro-timer-system.md` — Critical bug fix (highest priority)
3. ✅ `step-02-learning-guide.md` — Documentation track
4. ✅ `step-03-documentation-consolidation.md` — Documentation track
5. ✅ `step-06-code-standardization.md` — Code quality track
6. ✅ `step-07-github-issues-migration.md` — Final cleanup track

### Execution ✅
All 6 plans generated using planner agent following plan-template.md format.

**Output**: `.github/plans/step-NN-*.md` files ready for future implementation sessions

---

## Success Metrics

### Foundation ✅
- [x] 3 core docs (ARCHITECTURE, PRODUCT, CONTRIBUTING)
- [x] 4 custom agents tested
- [x] Learning tracker initialized

### Documentation (Steps 3 & 2)
- [ ] Docs consolidated (Step 3)
- [ ] Session summaries archived (Step 3)
- [ ] Cross-references added (Step 3)
- [ ] LEARNING_GUIDE.md with 10 topics (Step 2)

### Features (Steps 4 & 5)
- [ ] Macros activate and auto-restore
- [ ] Time settable via web UI
- [ ] Both persist across power loss

### Code Quality (Step 6)
- [ ] Zero String concatenation
- [ ] No commented legacy code
- [ ] JSDoc in all JS files
- [ ] Memory stable (<55% of 160KB)

### Project Mgmt (Step 7)
- [ ] All issues tracked in GitHub
- [ ] Issue templates created
- [ ] ROADMAP references issues

---

## Next Steps

### Immediate (Today)
1. ✅ All 6 plans generated
2. ✅ File naming standardized
3. ✅ Dependencies clarified (Step 3 before Step 2)
4. Review plans for accuracy

### Tomorrow (Phase 1 - 3 Parallel Sessions)
1. **Session A**: Load `step-03-documentation-consolidation.md` → Execute → Then load `step-02-learning-guide.md`
2. **Session B**: Load `step-04-macro-timer-system.md` → Implement with TDD → Hand off to reviewer
3. **Session C**: Load `step-05-time-setting-api.md` → Implement with TDD → Hand off to reviewer

### Week 2 (Phase 2 - Sequential)
1. **Session D**: Merge Steps 4 & 5 → Load `step-06-code-standardization.md` → Execute
2. **Session E**: Load `step-07-github-issues-migration.md` → Execute manually
