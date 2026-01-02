# SBAquaControl Refactoring Masterplan

**Created**: 2026-01-02  
**Status**: Step 1 Complete, Steps 2-7 Ready for Parallel Execution  
**Total Estimated Time**: 7-9 hours across multiple sessions

---

## Executive Summary

This masterplan organizes the SBAquaControl refactoring into 7 major steps with **3 parallel workstreams** to maximize efficiency. The foundation (Step 1) is complete, enabling immediate parallel execution of documentation and feature tracks.

**Completed**: ✅ Step 1 (Context Engineering Foundation)  
**Ready for Parallel**: Steps 2, 3, 4, 5 (3 simultaneous sessions possible)  
**Sequential**: Steps 6, 7 (wait for features to stabilize)

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
│ (Parallel)  │   │ (Parallel possible) │
└─────────────┘   └─────────────────────┘
    │                   │
    │         ┌─────────┴─────────┐
    │         │                   │
    │         ▼                   ▼
    │   ┌──────────┐        ┌──────────┐
    │   │ Step 4:  │        │ Step 5:  │
    │   │ Macro    │        │ Time API │
    │   │ Timer    │        │ (105 min)│
    │   │ (120 min)│        └──────────┘
    │   └──────────┘              │
    │         │                   │
    ▼         └─────────┬─────────┘
┌──────────┐            │
│ Step 2:  │            ▼
│ Learning │   ┌─────────────────┐
│ Guide    │   │ Step 6: Code    │
│ (60 min) │   │ Standardization │
└──────────┘   │ (150 min)       │
    │          └─────────────────┘
    ▼                   │
┌──────────┐            │
│ Step 3:  │            │
│ Docs     │            │
│ Cleanup  │            │
│ (75 min) │            │
└──────────┘            │
    │                   │
    └─────────┬─────────┘
              ▼
    ┌──────────────────┐
    │ Step 7: GitHub   │
    │ Issues (60 min)  │
    └──────────────────┘
```

---

## Steps Overview

| Step | Status | Agent(s) | Duration | Parallel? | Dependencies |
|------|--------|----------|----------|-----------|--------------|
| 1. Foundation | ✅ Complete | Manual | 90 min | N/A | None |
| 2. Learning Guide | ⏳ Ready | Plan + Learn | 60 min | ✅ Yes | Step 1 |
| 3. Docs Cleanup | ⏳ Ready | Plan + Implement | 75 min | ✅ Yes | Step 1 |
| 4. Macro Timer | ⏳ Ready | Plan + Implement + Review | 120 min | ✅ Yes | Step 1 |
| 5. Time API | ⏳ Ready | Plan + Implement + Review | 105 min | ✅ Yes | Step 1 |
| 6. Code Standards | ⏳ Ready | Plan + Implement + Review | 150 min | ❌ No | Steps 4, 5 |
| 7. GitHub Issues | ⏳ Ready | Plan + Manual | 60 min | ❌ No | Steps 4, 5, 6 |

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

## Step 2: Physics-Oriented Learning Guide 📚

**Agent**: Planner → Learn Agent  
**Duration**: 45-60 min  
**Can Start**: ✅ Immediately (independent)  
**Parallel**: ✅ Yes with Steps 3, 4, 5

### Objective
Create `LEARNING_GUIDE.md` with physicist-friendly explanations of embedded concepts using actual codebase examples.

### Topics (8-10)
1. Linear Interpolation (PwmChannel::proceedCycle)
2. Tick-Tock Async (TemperatureReader)
3. Main Loop Architecture (<10ms constraint)
4. Memory Management (String vs char buffers)
5. I2C Communication (PCA9685, DS3231)
6. Time Management (TimeLib, Unix timestamps)
7. JSON Streaming (_Server.sendContent)
8. File I/O Atomicity (temp file pattern)

### Deliverables
- [ ] Plan: `.github/plans/learning-guide.md`
- [ ] Guide: `LEARNING_GUIDE.md`

---

## Step 3: Documentation Consolidation 📝

**Agent**: Planner → Implementer  
**Duration**: 60-75 min  
**Can Start**: ✅ Immediately (independent)  
**Parallel**: ✅ Yes with Steps 2, 4, 5

### Objective
Consolidate redundant docs, archive summaries, improve structure.

### Tasks
1. Merge README + QUICKSTART
2. Archive session summaries to `.github/archives/`
3. Move specialized docs to `docs/design/`, `docs/status/`
4. Add cross-reference links

### Deliverables
- [ ] Plan: `.github/plans/docs-consolidation.md`
- [ ] Merged README.md
- [ ] Archived summaries
- [ ] Reorganized doc structure

---

## Step 4: Macro Timer System 🐛

**Agent**: Planner → Implementer → Reviewer  
**Duration**: 90-120 min  
**Can Start**: ✅ Immediately (**HIGHEST PRIORITY**)  
**Parallel**: ✅ Yes with Steps 2, 3, 5

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
- [ ] Plan: `.github/plans/macro-timer.md`
- [ ] Working macro activation
- [ ] Auto-restore after duration
- [ ] Manual stop functionality

---

## Step 5: Time-Setting API 🕐

**Agent**: Implementer → Reviewer  
**Duration**: 90-105 min  
**Can Start**: ✅ Immediately  
**Parallel**: ✅ Yes with Steps 2, 3, 4  
**Note**: Plan already created during agent test ✅

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
- [x] Plan: Created during test (needs saving)
- [ ] `setRTCTime()` in AquaControl.cpp
- [ ] `handleApiTimeSet()` in Webserver.cpp
- [ ] Time persists across power loss

---

## Step 6: Code Standardization 🧹

**Agent**: Planner → Implementer → Reviewer  
**Duration**: 120-150 min  
**Can Start**: ❌ After Steps 4 & 5 complete  
**Parallel**: ❌ No (avoid merge conflicts)

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
- [ ] Plan: `.github/plans/code-standardization.md`
- [ ] Zero String concatenation
- [ ] Clean AquaControlSketch.ino
- [ ] JSDoc in all JS files

---

## Step 7: GitHub Issues Migration 📋

**Agent**: Planner → Manual  
**Duration**: 60 min  
**Can Start**: ❌ After Steps 4, 5, 6 complete  
**Parallel**: ❌ No (references completed work)

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
- [x] Plan: `.github/plans/step-7-github-issues-migration.md`
- [x] Issue templates: bug_report.md, feature_request.md, documentation.md
- [x] Quick reference: `.github/ISSUE_QUICK_REFERENCE.md`
- [ ] GitHub issues created (manual)
- [ ] Labels and milestones configured
- [ ] Updated ROADMAP.md with issue references

---

## Parallelization Strategy

### ✅ **Phase 1: Immediate Parallel Execution**

**Session A (Doc Track)** — 60-75 min
- Step 2: Learning Guide
- Step 3: Docs Consolidation

**Session B (Critical Bug)** — 120 min
- Step 4: Macro Timer (**Highest Priority**)

**Session C (Feature)** — 105 min
- Step 5: Time-Setting API

**Total parallelized time**: ~120 min (vs 360 min sequential)

### ⏳ **Phase 2: Sequential After Features**

**Session D (Code Quality)** — 150 min
- Step 6: Code Standardization
- *Depends on: Steps 4 & 5 complete*

**Session E (Cleanup)** — 60 min
- Step 7: GitHub Issues
- *Depends on: Steps 4, 5, 6 complete*

---

## This Session: Plan Generation (60-90 min)

### Plans to Create (6 total)

1. ✅ **time-setting-api.md** — Save tested plan from agent workflow demo
2. 🔄 **macro-timer.md** — Critical bug fix (highest priority)
3. 🔄 **learning-guide.md** — Documentation track
4. 🔄 **docs-consolidation.md** — Documentation track
5. 🔄 **code-standardization.md** — Code quality track
6. 🔄 **github-issues.md** — Final cleanup track

### Execution
Invoke planner agent 5 times (time-setting plan already exists) to generate detailed implementation plans using plan-template.md format.

**Output**: `.github/plans/*.md` files ready for future implementation sessions

---

## Success Metrics

### Foundation ✅
- [x] 3 core docs (ARCHITECTURE, PRODUCT, CONTRIBUTING)
- [x] 4 custom agents tested
- [x] Learning tracker initialized

### Documentation (Steps 2 & 3)
- [ ] LEARNING_GUIDE.md with 8+ topics
- [ ] README consolidated
- [ ] Session summaries archived

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

After plan generation completes, future sessions can execute independently:

- **Session A**: Load `learning-guide.md` + `docs-consolidation.md` → Execute documentation track
- **Session B**: Load `macro-timer.md` → Implement critical bug fix
- **Session C**: Load `time-setting-api.md` → Implement time API
- **Session D**: Load `code-standardization.md` → Clean up codebase (after B & C)
- **Session E**: Load `github-issues.md` → Create GitHub issues (final)
