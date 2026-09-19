# Bug investigation 03 — Loading the macro list takes 20 s or more

**Status:** root cause identified and localised (algorithmic, not hardware). Fix proposed, not
compiled/flashed. The per-SD-operation cost is an *estimate* pending on-device measurement
(§4.1 gives the measurement).
**Issue:** [#9](https://github.com/mxbrau/SBAquaControl/issues/9) (analysis only - fix pending)
**Affected:** `src/Webserver.cpp` — `handleApiMacroList()` (L914-962),
`handleApiMacroGet()` (L965-1075), `loadMacroMetadata()` (L761-830),
`computeMacroDurationFromFiles()` (L834-902), `computeMacroDuration()` (L906-911);
`extras/SDCard/js/app.js` — `loadMacros()` (L200-230)

---

## 1. Reported symptom

> Loading the macros often takes quite some time — 20 s and more.

"Often" is the right word: it is not a constant 20 s but scales with the number of files on the
card and with the number of macros, and it gets worse when several requests overlap.

## 2. Root cause — the macro list is discovered by probing 999 file names

`handleApiMacroList()` (L914-962) does not list the directory. It **guesses** at file names and
tests each one:

```cpp
for (uint16_t macroNum = 1; macroNum <= 999; macroNum++)
{
    char sTempFilename[50];
    String sMacroPath = "macros/macro_";                       // 4 String allocations
    sMacroPath += (macroNum <= 9 ? "00" : (macroNum <= 99 ? "0" : ""));
    sMacroPath += String(macroNum);
    sMacroPath += "_ch00.cfg";
    sMacroPath.toCharArray(sTempFilename, 50);

    if (SD.exists(sTempFilename))                              // <-- syscall #1..#999
    {
        ...
        uint32_t duration = computeMacroDuration(macroIdStr, macroName);   // more SD I/O
        ...
    }
}
```

Consequences:

1. **999 `SD.exists()` calls per list request**, even when the card holds one macro. On the
   ESP8266 `SD.exists()` is implemented as *open + close*, i.e. a path lookup through the FAT
   plus SPI traffic per call — roughly 10-20 ms per call on a default-speed SPI bus. That alone
   is **10-20 s**, which is exactly the reported figure.
2. **~4000 short-lived `String` objects per request** (4 per iteration). The project's own
   comments warn about this (L359: *"the string objects causing freezes when using in
   SD.exists or SD.open commands"*). Heap fragmentation is also what makes the *rest* of the
   firmware (which needs contiguous blocks for the web server) degrade over time.
3. **Redundant work inside the loop.** For every macro actually found, the code calls
   `computeMacroDuration()` → `loadMacroMetadata()` → `SD.exists("<id>.json")` + `SD.open()` +
   read. If that metadata file is missing, it falls back to `computeMacroDurationFromFiles()`
   (L834-902), which **probes all 16 channel files** (`SD.exists` × 16) and opens every one of
   them to parse the maximum time — and the result is never written back, so the expensive
   fallback runs again on the next request. So a card with N macros and no metadata costs
   999 + N × (1 + 16 exists + up to 16 opens + parses) SD operations.

## 3. Why the perceived wait is much larger than the list request alone

`extras/SDCard/js/app.js`, `loadMacros()` (L200-230):

```js
const data = await API.getMacros();                      // GET /api/macro/list   (the 999 probes)
state.macros = await Promise.all(data.macros.map(async (macro) => {
    const details = await API.getMacro(macro.id);        // GET /api/macro/get  per macro, IN PARALLEL
    ...
}));
```

So opening the page costs **1 + N HTTP requests**, where each `get` again calls
`computeMacroDuration()` (duplicating the work the list endpoint just did) **and** opens 6
channel files and parses them line by line with `String` (`readStringUntil`, `indexOf`,
`substring` — L1020-1060). The firmware serves one request at a time
(`_Server.handleClient()` in the main loop), so N parallel requests are **serialised**: the
user-visible time is the *sum* of all of them, not the maximum.

`loadMacros()` is also re-run after every save and every delete (`app.js` L308, L652), so the
same multi-second scan is paid again after each macro edit. There is no caching anywhere, and
static assets are served without cache headers (see investigation 02, H3), so the ~50 KB of JS
is re-fetched from the SD card too.

## 4. Proposed fix

### 4.1 Step 0 — measure before changing anything (5 minutes, no code)

From a laptop:

```bash
curl -o /dev/null -w 'list   %{time_total}s\n' http://<host>/api/macro/list
curl -o /dev/null -w 'get    %{time_total}s\n' 'http://<host>/api/macro/get?id=macro_001'
curl -o /dev/null -w 'status %{time_total}s\n' http://<host>/api/status
```
* `list` ≈ 20 s → confirms §2 (the 999 probes).
* `list` fast but the page still slow → confirms §3 (the N+1 fan-out).
* Serial timestamps around the calls (`Serial.printf("list start %u\n", millis())` … `end`) give
  the per-macro cost and let you fill in the estimate in §2 with a real number.

### 4.2 Replace the 999 probes with one directory enumeration

```cpp
void handleApiMacroList()
{
    _Server.setContentLength(CONTENT_LENGTH_UNKNOWN);
    _Server.send(200, "application/json", "");
    _Server.sendContent("{\"macros\":[");
    _Server.sendHeader("Cache-Control", "no-store");

    File dir = SD.open("/macros");
    if (dir && dir.isDirectory())
    {
        bool first = true;
        while (File entry = dir.openNextFile())
        {
            // only macro_<NNN>_ch00.cfg  ->  id "macro_<NNN>"
            const char *nm = entry.name();                 // may be "macro_001_ch00.cfg"
            if (strstr(nm, "_ch00.cfg") == nullptr) { entry.close(); continue; }

            char id[16];
            // nm may be "/macros/macro_001_ch00.cfg" or "macro_001_ch00.cfg" depending on core
            const char *base = strrchr(nm, '/');  base = base ? base + 1 : nm;
            strncpy(id, base, 10);  id[10] = '\0';         // "macro_001"

            String macroName; uint32_t duration = 0;
            loadMacroMetadata(id, macroName, duration);     // keep, but cache it (4.3)
            ...
            entry.close();
        }
        dir.close();
    }
    _Server.sendContent("]}");
}
```

This turns 999 path lookups into **one directory open + N directory reads** (N = number of files
in `macros/`), independent of the 999-name ceiling. The exact API surface differs between SD-library versions
(`File::openNextFile()` exists in the ESP8266 Arduino core; `isDirectory()`, `name()` and
whether `name()` returns a full path or a base name **must be verified against the core version
pinned by PlatformIO before flashing** — that is the one part of this patch to test first, with
a `Serial.println(entry.name())` on a scratch card.

### 4.3 Cache the list in RAM, and stop recomputing the duration

* Keep a tiny array in the firmware: `struct MacroEntry { char id[16]; char name[24]; uint32_t duration; };`
  ~10 entries = ~440 bytes — acceptable even on the ESP8266 given the RAM budget.
* Fill it on boot and **invalidate only on `/api/macro/save`, `/api/macro/delete`** (both already
  exist as handlers). Then `/api/macro/list` becomes a pure RAM read: milliseconds.
* Persist the fallback: when `computeMacroDurationFromFiles()` had to be used, write the
  metadata JSON (`saveMacroMetadata()`) so the 16-file scan never happens twice for the same
  macro.

### 4.4 Fix the client to use what the list already returns

`/api/macro/list` already returns `duration` (L953-956), but `app.js` ignores it and fetches
every macro again. Either delete the `Promise.all` block in `loadMacros()` and use
`macro.duration`, or make `loadMacros()` fetch details only for the macro the user actually
opens. This removes the whole N+1 fan-out from the page load.

### 4.5 Cheap extras

* Replace `String` line parsing in `handleApiMacroGet()` (L1020-1060) with
  `readBytesUntil('\n', charBuf, …)` + `strchr`/`atoi` — the pattern already used in
  `computeMacroDurationFromFiles()` (L852-895) and recommended by the project's own memory
  rules (`ARCHITECTURE.md`, "Memory Management").
* Send `Cache-Control` for the static assets so the ~50 KB JS is not re-downloaded on every visit.
* Optional: raise the SD SPI clock if the installed card/wiring tolerates it (verify; a slow or
  counterfeit card is also worth ruling out — §5).

## 5. Troubleshooting plan

### 5.1 Isolate the layer

1. **Firmware vs card vs network.** Run §4.1's three curls from a laptop on the LAN.
   `/api/status` must be fast (< 100 ms). If `/api/status` is *also* slow, the problem is not
   the macro code — check investigation 02 (modem sleep / connection pressure) first.
2. **Serial instrumentation.** In `handleApiMacroList()`, print `millis()` before/after the loop
   and after each `computeMacroDuration()` call:
   ```
   list loop: 18 942 ms   (999 SD.exists)
   dur macro_001: 61 ms   (metadata)
   dur macro_002: 412 ms  (16-channel fallback!)
   ```
   This immediately shows which of §2/§3 dominates and whether the 16-file fallback is firing.
3. **Scale test.** Copy the same macro to `macros/macro_002..010_ch00.cfg`, reload the macro
   page, and re-measure. Time growing ~linearly with the *number of files on the card* rather
   than with the number of macros confirms the 999-probe loop; growth proportional to the
   number of macros confirms the per-macro duration fallback.
4. **Rule out the SD card.** Put the card in a PC and time a recursive scan; also test a known
   good card of the same size. A failing/worn card makes every `SD.exists()` take far longer and
   would amplify everything above.
5. **Browser side.** DevTools → Network → reload the page: count the requests to
   `/api/macro/get`, look at the waterfall (are they serialised?), and check whether
   `app.js`/`chart-manager.js` come back as `200` again instead of `304`/cached. This confirms
   §3 and §4.5 directly.
6. **Heap check.** `GET /api/debug` before and after loading the macros page: `free_heap` and
   `heap_fragmentation` (`Webserver.cpp` L1604-1614). A large drop or rising fragmentation
   confirms the `String` churn and predicts the "freezes" the project's comments mention.

### 5.2 Expected result after the fix

| | before | after 4.2 + 4.3 + 4.4 |
|---|---|---|
| requests per macro page load | 1 + N | 1 |
| SD path lookups | 999 (+ N×17) | ~1 directory walk |
| heap churn | ~4000 `String`s | none |

Target: macro page load < 500 ms. If it is still slow, the remaining cost is in
`loadMacroMetadata`/`/api/macro/get` file parsing (§4.5) or on the client (§4.5 caching).

## 6. What needs the user / hardware

1. **Serial console access** for the instrumentation in §5.2 (USB or OTA) — without it the
   per-operation cost can only be estimated.
2. **A decision on the macro ID/naming scheme** if the directory walk is adopted: the current
   code assumes `macro_%03u_ch00.cfg`; any file on the card that does not match must be
   ignored rather than mistaken for a macro. It is worth checking the actual card contents
   (`ls macros/`) — if there is a `macro_001.json` **and** `macro_001_ch00..ch05.cfg`, the
   directory walk sees 7 files per macro and must filter correctly.
3. **A card that can be re-imaged** for the scale test in §5.1.3, and ideally a second card to
   rule out card wear.
4. **Confirmation of the SD library version** used by the PlatformIO build, because
   `openNextFile()`/`name()` semantics vary; this is the only part of the proposed patch that
   needs on-target verification before it can be trusted.

## 7. Verification status

* Root cause (§2) and the fan-out (§3) are read directly from the source; the *magnitude* of the
  per-`SD.exists()` cost is an estimate (10-20 ms) that §4.1/§5.1.2 are designed to replace with
  a measurement. No hardware or SD card was available here.
* The patch in §4.2 is a sketch and has **not been compiled, flashed or run**; the
  `openNextFile()`/`name()` semantics must be checked against the pinned core version (§6.4).

## 8. References

* `src/Webserver.cpp` L914-962 (`handleApiMacroList`), L965-1075 (`handleApiMacroGet`),
  L726-757 (`saveMacroMetadata`), L761-830 (`loadMacroMetadata`), L834-902
  (`computeMacroDurationFromFiles`), L906-911 (`computeMacroDuration`)
* `extras/SDCard/js/app.js` L200-230 (`loadMacros`, N+1), L308 + L652 (re-load after save/delete)
* `extras/SDCard/js/config.js` (`statusUpdateInterval: 1000`), `extras/SDCard/js/api.js`
* `docs/design/MACRO_REFACTORING.md`, `ARCHITECTURE.md` ("Memory Management" — avoid `String`
  in SD paths), `.github/plans/macro-optimization-final-review.md`
