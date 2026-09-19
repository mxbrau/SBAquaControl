---
title: Move the repository to a permanent location off the former Sciebo backup folder
labels: tooling, chore
---

## Context

The working copy lives at
`J:\Sciebo_bac\Dokumente\Hobbys\Aquarium\Schaltung\SBAquaControl` - a **former
Sciebo backup folder** that is no longer synchronised. The owner stopped using
the Sciebo-synced location (`J:\Sciebo\...`) because Sciebo and Git did not work
together reliably.

It is not a company repo, so an imperfect setup is tolerable - but this one has
concrete downsides.

## Why it matters

1. **No safety net for the working copy.** The code is on GitHub, so commits are
   safe, but the local folder is a leftover of a backup tree. If the backup tool
   that created `Sciebo_bac` ever rewrites or cleans that folder, the working
   copy and anything uncommitted go with it.
2. **The folder name lies.** Nothing signals "this is the live repo"; the next
   person (or the next me) looking for it will start in `J:\Sciebo\...`.
3. **Transient git ref reads (diagnosed 2026-09-19).** `git rev-parse remote/master`
   failed with "Needed a single revision" *although the ref file existed and was
   valid*; a minute later the same directory (`.git/refs/remotes/remote/`) listed
   5 entries where an earlier read had returned an empty directory, and
   `git for-each-ref` resolved everything. The sandbox reads this folder over a
   9p/drvfs mount (`J:\` -> `/workspace`), which intermittently returns partial
   directory listings and stale/failed reads. Two git processes on the same `.git`
   (the container and a Windows-side VS Code that auto-fetches) plausibly make it
   worse. Practical rule: re-run the command before believing a ref or file is
   missing, and `git fetch remote` if it really is. A local repo on an NTFS
   folder outside this mount would remove the class of problem entirely - which is
   the point of this issue.
4. Moving is cheap **now** and expensive later: the Hermes sandbox mounts the
   repo folder (`J:\` is mounted into the container), so a move means updating
   that mount and re-running `bash .sbaqua-build-env/setup.sh` once.

## Proposal

- Pick a permanent home, e.g. `J:\Projekte\SBAquaControl` or a local dev drive
  folder such as `C:\Users\tenabre\source\SBAquaControl`.
- **Not** a cloud-synced folder - Sciebo + `.git` was already tried here and
  abandoned.
- Move the folder, verify `git status`, `git fetch remote`, and
  `uv run python test/run_checks.py` (BUILD + PARITY + LIVE) all behave, then
  point the Hermes workspace/mount at the new path.
- Keep GitHub as the off-site copy; consider enabling the repo's own backup
  habit: push after each working session.
- Only after the new location is verified: delete or archive the old tree.

## Acceptance criteria

- [ ] Repo lives in a deliberately chosen, documented location outside cloud-sync trees
- [ ] `git fetch`/`push` verified there and all automated checks pass
- [ ] The Hermes sandbox mounts the new path and `setup.sh` provisions cleanly
- [ ] Old folder removed or archived; no second working copy left ambiguously behind
- [ ] `README.md` (or `CONTRIBUTING.md`) states where the canonical working copy lives
