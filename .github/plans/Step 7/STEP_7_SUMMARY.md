# Step 7 Planning Summary

**Date**: January 2, 2026  
**Planner Agent**: ✅ Complete  
**Status**: Ready for manual execution  
**Estimated Time**: 60 minutes

---

## What Was Created

### Core Documents (4 files)

1. **[`.github/plans/step-7-github-issues-migration.md`](plans/step-7-github-issues-migration.md)** (186 lines)
   - Complete implementation plan following `plan-template.md` structure
   - Architecture, design decisions, task breakdown
   - All 15 issue descriptions with full markdown

2. **[`.github/ISSUE_QUICK_REFERENCE.md`](ISSUE_QUICK_REFERENCE.md)** (~350 lines)
   - Copy-paste ready issue descriptions
   - Labels, milestones, and status for each issue
   - Manual creation checklist with time estimates

3. **[`.github/plans/README_STEP_7.md`](plans/README_STEP_7.md)** (~200 lines)
   - User-friendly implementation guide
   - Quick start instructions (manual + automated)
   - Post-migration workflow and verification checklist

4. **[`.github/scripts/create-issues.sh`](scripts/create-issues.sh)** (Bash script)
   - Optional automation via GitHub CLI
   - Creates labels, milestones, and all 15 issues
   - Color-coded output for progress tracking

### Issue Templates (4 files)

1. [`.github/ISSUE_TEMPLATE/bug_report.md`](ISSUE_TEMPLATE/bug_report.md)
2. [`.github/ISSUE_TEMPLATE/feature_request.md`](ISSUE_TEMPLATE/feature_request.md)
3. [`.github/ISSUE_TEMPLATE/documentation.md`](ISSUE_TEMPLATE/documentation.md)
4. [`.github/ISSUE_TEMPLATE/config.yml`](ISSUE_TEMPLATE/config.yml)

**Total**: 8 new files created

---

## Issue Breakdown (15 Total)

### ✅ Completed (4 issues - close immediately)
- #1: Boot-time OOM crashes
- #2: Severe RAM over-allocation (82% → 50%)
- #3: Memory leaks in web API (String concatenation)
- #4: UI-firmware mismatch (spline vs linear)

**Action**: Create and close with references to SESSION_SUMMARY_2025-12-30.md

### ⏳ Active Work (5 issues - close after PRs merge)
- #5: Macro timer activation (Step 4)
- #6: Time-setting API endpoint (Step 5)
- #7: String concatenation cleanup (Step 6)
- #8: JSDoc comments (Step 6)
- #9: Legacy code removal (Step 6)

**Action**: Create and keep open, close when respective PR merges

### 📋 Future Roadmap (6 issues - long-term tracking)
- #10: Timezone/DST support (Phase 3)
- #11: Gradient animation effects (Phase 5)
- #12: Multi-user authentication (Phase 4)
- #13: HTTPS support (Phase 4)
- #14: UI manages 16 channels (currently 6)
- #15: Macro persistence across power loss

**Action**: Create with "Future" milestone for community visibility

---

## Label & Milestone Structure

### Labels (6 total)
- `bug` 🔴 (#d73a4a) - 4 issues
- `enhancement` 🟢 (#0e8a16) - 10 issues
- `documentation` 🔵 (#0075ca) - 2 issues
- `good-first-issue` 🟣 (#7057ff) - 2 issues
- `help-wanted` 🟡 (#fbca04) - 3 issues
- `wontfix` ⚪ (#ffffff) - 0 issues (reserved)

### Milestones (4 total)
- **v0.6** (Due: 2026-01-31) - 6 issues - "Macro Timer & Time API"
- **v0.7** (Due: 2026-02-28) - 3 issues - "Code Standardization"
- **v1.0** (Due: 2026-06-30) - 2 issues - "Spline Smoothing"
- **Future** (No due date) - 4 issues - "Long-term enhancements"

---

## How to Execute (Manual)

### Phase 1: GitHub Setup (15 min)
1. Navigate to `Settings > Labels` in GitHub repo
2. Create 6 labels using [ISSUE_QUICK_REFERENCE.md](ISSUE_QUICK_REFERENCE.md) color codes
3. Navigate to `Issues > Milestones`
4. Create 4 milestones with due dates

### Phase 2: Create Issues (40 min)
1. Open [ISSUE_QUICK_REFERENCE.md](ISSUE_QUICK_REFERENCE.md)
2. For each issue (#1-15):
   - Click "New Issue" in GitHub
   - Copy title from reference doc
   - Paste description (pre-formatted markdown)
   - Assign labels and milestone
   - Submit
3. **Immediately close** issues #1-4 with comment: "Fixed in December 2025 optimization session. See SESSION_SUMMARY_2025-12-30.md"

### Phase 3: Update Docs (5 min)
1. Update [ROADMAP.md](../ROADMAP.md):
   - Replace `Timezone/DST support (Phase 3)` → `Timezone/DST support (Phase 3) - See #10`
   - Repeat for all roadmap items now tracked as issues
2. Update [MASTERPLAN.md](MASTERPLAN.md):
   - Change Step 7 status from `⏳ Ready` → `✅ Complete`
3. Commit changes: `git commit -m "docs: migrate tasks to GitHub Issues"`

**Total Time**: ~60 minutes

---

## Alternative: GitHub CLI Automation

If you have `gh` CLI installed and authenticated:

```bash
# Make script executable
chmod +x .github/scripts/create-issues.sh

# Edit REPO variable (line 6)
nano .github/scripts/create-issues.sh
# Change: REPO="yourusername/SBAquaControl"

# Run script
./.github/scripts/create-issues.sh
```

**Note**: Script is currently a skeleton - full implementation would need all 15 issues added. Manual creation via ISSUE_QUICK_REFERENCE.md is more reliable for first-time setup.

---

## Verification Checklist

After execution:
- [ ] 6 labels created with correct colors
- [ ] 4 milestones created with due dates
- [ ] 15 issues created with proper labels/milestones
- [ ] Issues #1-4 closed with references
- [ ] Issues #5-15 open and properly categorized
- [ ] ROADMAP.md references issues (e.g., "See #10")
- [ ] MASTERPLAN.md Step 7 marked ✅ Complete
- [ ] Issue templates appear in "New Issue" dropdown

---

## Success Criteria

**Step 7 is complete when**:
- ✅ All task tracking migrated from markdown → GitHub Issues
- ✅ Transparent tracking system visible to contributors
- ✅ Issues linked to ROADMAP.md for context
- ✅ Templates available for new bug reports and features
- ✅ Milestone tracking shows progress toward v0.6, v0.7, v1.0

**Post-Migration Workflow**:
- All new bugs/features → GitHub Issues (not markdown)
- PRs use "Fixes #N" to auto-close issues
- Contributors discover work via "good-first-issue" label
- Project board (optional) visualizes workflow

---

## Files Reference

**Start here**: [README_STEP_7.md](plans/README_STEP_7.md) - User-friendly guide  
**Copy-paste source**: [ISSUE_QUICK_REFERENCE.md](ISSUE_QUICK_REFERENCE.md) - All issue descriptions  
**Architecture details**: [step-7-github-issues-migration.md](plans/step-7-github-issues-migration.md) - Full plan  
**Automation (optional)**: [create-issues.sh](scripts/create-issues.sh) - GitHub CLI script

---

## Next Steps

1. **Review** all created documents (8 files)
2. **Execute** Step 7 manually or via script (~60 min)
3. **Verify** all issues created and properly categorized
4. **Update** ROADMAP.md and MASTERPLAN.md
5. **Proceed** with Steps 4-6 execution (if not already started)

**Questions?** See [MASTERPLAN.md](MASTERPLAN.md) for overall strategy.
