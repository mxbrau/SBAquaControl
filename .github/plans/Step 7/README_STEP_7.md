# Step 7: GitHub Issues Migration - Implementation Guide

**Status**: ✅ Planning Complete - Ready for Manual Execution  
**Estimated Time**: 60 minutes  
**Prerequisites**: Steps 4, 5, 6 completed (or at least initiated)

---

## What This Step Delivers

This step migrates all task tracking from local markdown files to GitHub Issues, establishing a transparent, collaborative task management system with:

- **15 GitHub Issues** categorized by status (completed, active, future)
- **Issue Templates** for consistent bug reports and feature requests
- **Label System** for categorization (bug, enhancement, documentation, etc.)
- **Milestones** aligned with ROADMAP.md (v0.6, v0.7, v1.0, Future)
- **Updated Documentation** with issue cross-references

---

## Quick Start

### Option 1: Manual Creation (Recommended)
Use [ISSUE_QUICK_REFERENCE.md](../ISSUE_QUICK_REFERENCE.md) as copy-paste source:

1. **Create Labels & Milestones** (10 min)
   - Navigate to GitHub Settings → Labels
   - Create 6 labels (bug, enhancement, documentation, good-first-issue, help-wanted, wontfix)
   - Navigate to Issues → Milestones
   - Create 4 milestones (v0.6, v0.7, v1.0, Future)

2. **Create Issues** (40 min)
   - Open [ISSUE_QUICK_REFERENCE.md](../ISSUE_QUICK_REFERENCE.md)
   - Copy each issue description
   - Paste into GitHub "New Issue" form
   - Assign labels and milestones
   - Close issues #1-4 immediately (already fixed)

3. **Update Documentation** (10 min)
   - Update [ROADMAP.md](../../ROADMAP.md) with issue references
   - Update [MASTERPLAN.md](../MASTERPLAN.md) Step 7 status to ✅ Complete
   - Commit changes

### Option 2: GitHub CLI Automation (Advanced)
Use the provided shell script (requires `gh` CLI installed):

```bash
# Install GitHub CLI (if not installed)
# macOS: brew install gh
# Windows: winget install GitHub.cli
# Linux: See https://cli.github.com/

# Authenticate
gh auth login

# Edit script to update REPO variable
nano .github/scripts/create-issues.sh
# Change: REPO="yourusername/SBAquaControl"

# Make executable and run
chmod +x .github/scripts/create-issues.sh
./.github/scripts/create-issues.sh
```

**Note**: Script creates labels, milestones, and issues automatically but may need manual adjustments.

---

## Files Delivered

### Core Planning Document
- [`.github/plans/step-7-github-issues-migration.md`](../plans/step-7-github-issues-migration.md)
  - Complete implementation plan with architecture and task breakdown
  - Follows `plan-template.md` structure
  - 186 lines with all 15 issue descriptions

### Issue Templates
- [`.github/ISSUE_TEMPLATE/bug_report.md`](../ISSUE_TEMPLATE/bug_report.md)
  - Template for bug reports with environment details
- [`.github/ISSUE_TEMPLATE/feature_request.md`](../ISSUE_TEMPLATE/feature_request.md)
  - Template for feature requests with implementation considerations
- [`.github/ISSUE_TEMPLATE/documentation.md`](../ISSUE_TEMPLATE/documentation.md)
  - Template for documentation improvements
- [`.github/ISSUE_TEMPLATE/config.yml`](../ISSUE_TEMPLATE/config.yml)
  - Disables blank issues, directs users to templates

### Quick Reference
- [`.github/ISSUE_QUICK_REFERENCE.md`](../ISSUE_QUICK_REFERENCE.md)
  - Copy-paste ready issue descriptions
  - Manual creation checklist
  - ~350 lines with all metadata (labels, milestones, status)

### Automation Script
- [`.github/scripts/create-issues.sh`](../scripts/create-issues.sh)
  - Bash script for GitHub CLI automation
  - Creates labels, milestones, and all 15 issues
  - Color-coded output for progress tracking

---

## Issue Organization

### By Status

**Completed** (4 issues) - Close immediately with references:
- #1: Boot-time OOM crashes ✅
- #2: Severe RAM over-allocation ✅
- #3: Memory leaks in web API ✅
- #4: UI-firmware mismatch ✅

**Active Work** (5 issues) - Close after respective PRs merge:
- #5: Macro timer activation (Step 4) ⏳
- #6: Time-setting API endpoint (Step 5) ⏳
- #7: String concatenation cleanup (Step 6) ⏳
- #8: JSDoc comments (Step 6) ⏳
- #9: Legacy code removal (Step 6) ⏳

**Future Roadmap** (6 issues) - Track long-term goals:
- #10: Timezone/DST support 📋
- #11: Gradient animation effects 📋
- #12: Multi-user authentication 📋
- #13: HTTPS support 📋
- #14: UI manages 16 channels 📋
- #15: Macro persistence across power loss 📋

### By Milestone

| Milestone | Issues | Due Date | Purpose |
|-----------|--------|----------|---------|
| v0.6 | #1-6 | 2026-01-31 | Macro Timer & Time API |
| v0.7 | #7-9 | 2026-02-28 | Code Standardization |
| v1.0 | #11, #14 | 2026-06-30 | Spline Smoothing & 16 Channels |
| Future | #10, #12, #13, #15 | None | Long-term enhancements |

### By Label

- `bug` (4): #1, #2, #3, #4
- `enhancement` (10): #5, #6, #7, #9, #10, #11, #12, #13, #14, #15
- `documentation` (2): #4, #8
- `good-first-issue` (2): #7, #8
- `help-wanted` (3): #10, #12, #13

---

## Post-Migration Workflow

### Creating New Issues
1. Navigate to: `https://github.com/yourusername/SBAquaControl/issues/new/choose`
2. Select template (Bug Report / Feature Request / Documentation)
3. Fill in required fields
4. Assign labels and milestone
5. Submit issue

### Linking Pull Requests
When creating a PR that fixes an issue, use keywords in PR description:
```markdown
Fixes #5

## Changes
- Implemented MacroState struct
- Added handleApiMacroActivate() endpoint
- Auto-restore on expiration in proceedCycle()

## Testing
- [x] Macro activates correctly
- [x] Timer expires and restores schedule
- [x] API status shows macro state
```

GitHub will automatically:
- Link PR to issue
- Close issue when PR merges
- Add PR reference to issue timeline

### Updating ROADMAP.md
Replace inline task descriptions with issue references:

**Before**:
```markdown
- Timezone/DST support (Phase 3)
```

**After**:
```markdown
- Timezone/DST support (Phase 3) - See #10
```

This keeps ROADMAP.md as a high-level overview while GitHub Issues contain detailed implementation notes.

---

## Verification Checklist

After manual creation, verify:

### Labels & Milestones
- [ ] 6 labels created with correct colors
- [ ] 4 milestones created with due dates
- [ ] All issues have at least one label
- [ ] All issues assigned to a milestone

### Issues Created
- [ ] 4 completed issues (#1-4) created and closed
- [ ] 5 active issues (#5-9) created and open
- [ ] 6 future issues (#10-15) created and open
- [ ] Total: 15 issues

### Issue Quality
- [ ] All titles follow format: `[TYPE] Description`
- [ ] All descriptions include acceptance criteria
- [ ] All file references use markdown links
- [ ] All "Fixes #N" references work

### Documentation Updated
- [ ] ROADMAP.md references issues
- [ ] MASTERPLAN.md Step 7 marked complete
- [ ] Changes committed to git

---

## Troubleshooting

### "Label already exists" error
Some default labels (like `bug`, `enhancement`) may already exist in your repository. This is fine - verify the color matches and proceed.

### Milestone dates won't set
GitHub API requires ISO 8601 format: `2026-01-31T23:59:59Z`. The web interface handles this automatically.

### Issue templates not showing
Templates require commit to `main` branch and a few minutes to propagate. Check: `Settings > Features > Issues > Set up templates`.

### GitHub CLI not authenticated
Run `gh auth login` and follow prompts. Choose HTTPS or SSH, then authenticate via browser.

---

## Success Metrics

**Step 7 is complete when**:
- ✅ All 15 issues created in GitHub
- ✅ Issue templates available for new issues
- ✅ ROADMAP.md references issues (not inline tasks)
- ✅ Completed work (#1-4) closed with documentation links
- ✅ Active work (#5-9) tracked and linked to implementation plans
- ✅ Future work (#10-15) visible for community contributions

**Result**: Transparent task management ready for community collaboration. All future bugs/features go through GitHub Issues (not markdown files).

---

## Next Steps

After Step 7 completion:
1. **Execute Steps 4-6** (if not already done)
2. **Close issues** as PRs merge (use "Fixes #N" in PR descriptions)
3. **Monitor community** for new bug reports and feature requests
4. **Triage incoming issues** with labels and milestones
5. **Update project board** (if created) as work progresses

**Optional Enhancements**:
- Add CI/CD integration (GitHub Actions to validate builds on PR)
- Set up issue auto-assignment (via CODEOWNERS file)
- Create saved filters (e.g., "good-first-issue" for contributors)
- Configure notifications (watch repository for new issues)

---

## Questions?

See [MASTERPLAN.md](../MASTERPLAN.md) for overall refactoring strategy or [CONTRIBUTING.md](../../CONTRIBUTING.md) for development workflow.
