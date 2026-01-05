# Macro CRUD/Activation Fix Plan

## Overview
Fix macro CRUD and activation inconsistencies so UI and firmware stay in sync: preserve/edit IDs, round-trip name/duration metadata, validate activation duration, and provide consistent metadata to avoid NaN/instant-expire behavior.

## Requirements
- Functional: Editing a macro updates the same ID (rename optional by display name only), name/duration round-trip via API, activation uses a validated duration (fallback to stored value), deletion removes all macro files for that ID, list/get endpoints expose canonical metadata.
- Non-functional: Memory-safe (avoid large String concatenation; reuse buffers), non-blocking main loop, preserve existing file formats; respect channel cap (6 visible) and MAX_TARGET_COUNT.

## Architecture and Design
- Metadata: compute canonical duration as max target time across all channels; fallback name = id. Compute-on-read is acceptable.
- Save flow: if `id` exists, treat as update (reuse ID). If new, allocate next `macro_NNN`. Renaming is display-name only; ID stays stable to avoid file churn.
- Get/list flow: `/api/macro/get` returns `id`, `name`, `duration`, and channels; `/api/macro/list` also includes duration to reduce UI fetches.
- Activate flow: require duration > 0; if missing/zero, derive from stored macro data (max target time) or reject with 400.
- UI: rely on backend duration; fallback = max target time across all channels.

## Implementation Tasks
- [ ] Add helper to compute macro duration/name when reading files (max target time across channels; name fallback to id) in [src/Webserver.cpp](src/Webserver.cpp).
- [ ] Update `/api/macro/get` to include `name` and `duration`; compute duration from all channels’ targets, default 0 when empty ([src/Webserver.cpp#L728-L792](src/Webserver.cpp#L728-L792)).
- [ ] Update `/api/macro/list` to include duration (computed once per macro) ([src/Webserver.cpp#L690-L723](src/Webserver.cpp#L690-L723)).
- [ ] Rework `/api/macro/save`: if `id` exists, treat as edit (reuse ID); if new, allocate next `macro_NNN`. Keep display-name-only renaming. Return actual `id` used and computed `duration` ([src/Webserver.cpp#L819-L915](src/Webserver.cpp#L819-L915)).
- [ ] Harden `/api/macro/activate`: validate `duration`; if zero/missing, load macro targets, compute duration (max target time), and use it; otherwise reject with 400 ([src/Webserver.cpp#L1024-L1056](src/Webserver.cpp#L1024-L1056), [src/AquaControl.cpp#L1083-L1142](src/AquaControl.cpp#L1083-L1142)).
- [ ] In `AquaControl::activateMacro`, guard against zero duration (return false) and log; keep schedule backup and PWM write flags unchanged ([src/AquaControl.cpp#L1083-L1142](src/AquaControl.cpp#L1083-L1142)).
- [ ] UI: adjust macro load/render to trust backend duration; if missing, compute max over all channels instead of channel 0 only ([extras/SDCard/js/app.js#L197-L238](extras/SDCard/js/app.js#L197-L238)). Use returned `name` when available.
- [ ] UI: in `editMacro`, rely on `data.duration`/`data.name`; keep fallback to max target time if needed ([extras/SDCard/js/app.js#L707-L742](extras/SDCard/js/app.js#L707-L742)).
- [ ] UI: when activating, use backend-provided duration from `state.macros` (canonical duration) and handle activation errors gracefully ([extras/SDCard/js/app.js#L221-L246](extras/SDCard/js/app.js#L221-L246)).

## Testing Strategy
- Manual on device/SD:
  - Create macro (new ID); list shows correct duration/name.
  - Edit macro (same ID) updates targets and duration; no duplicate files remain.
  - Activate macro with stored duration; countdown decrements; auto-restore at expiry.
  - Activate with missing duration (simulated) uses fallback; zero duration is rejected.
  - Delete macro removes all `_chXX` files; list updates.
- Browser devtools: verify `/api/macro/list`, `/api/macro/get`, `/api/status` payloads include `name`/`duration` and `macro_expires_in` counts down.
- Optional: dry-run harness to load macro files and validate duration computation.

## Open Questions
- None pending; renaming is display-name-only, ID stays stable. Compute-on-read is acceptable; metadata file could be a future enhancement if performance becomes an issue.
