---
title: Server often unreachable from phones, worst phone connects best [firmware]
labels: bug, firmware, network, needs-hardware
---

> **Provenance:** this analysis was written on the branch `fix/wifi-reachability` as
> `docs/investigations/02-wifi-reachability-from-phones.md`. It is reproduced here verbatim so the finding is durable; the fix
> will be developed on a fresh branch off `master` and closes this issue.
> Verification status is stated in the document itself - read it before
> assuming any fix has been compiled or flashed.

---

## Bug investigation 02 — Server often unreachable from phones (worst phone connects best)

**Status:** no single confirmed root cause; five code-level defects found, ranked below with a
discriminating test for each. All are verifiable read-only from the source; none have been
reproduced on hardware from here.
**Affected:** `src/AquaControl.cpp` — `initESP8266NetworkConnection()` (L52-87),
`AquaControl::proceedCycle()` (L869-923), `AquaControl::init()` (L735-770, L784-819);
`src/Webserver.cpp` (`handleRoot` L23-54, `handleNotFound` L56-124);

---

## 1. Reported symptom

* The ESP8266 web UI is **often not reachable** from the phones.
* The **network scan / router client list clearly shows the device** — so it is associated.
* The phones have good general internet access.
* **The oldest phone (iPhone 11) connects reliably; the newest phone has the most trouble.**

That last observation is the most informative clue in the report: it is a
*client-side-behaviour-dependent* failure. Modern mobile browsers open **6-8 parallel TCP
connections** per origin, aggressively pre-connect, retry/timeout faster, attempt
HTTP/2 upgrade and IPv6 (AAAA) first, and use MAC randomisation. An old iPhone keeps fewer
connections open and is more patient. Anything that makes the ESP8266's tiny single-threaded
web server choke under *parallel* or *repeated* connection attempts reproduces exactly this
ranking — and it is also consistent with "it's associated but unreachable".

## 2. Findings, ranked

### H1 (highest) — WiFi modem sleep is never disabled

`initESP8266NetworkConnection()` (L52-87) sets only `WiFi.persistent(false)` and
`WiFi.mode(WIFI_STA)`. **`WiFi.setSleepMode()` is called nowhere in the project** (verified by
searching `src/`). The ESP8266 Arduino core therefore runs the default modem-sleep behaviour:
the RF stage is duty-cycled between DTIM beacons.

Effect: latency spikes of 100-500 ms, **dropped/ignored packets**, and TCP connections that
fail on the first SYN or stall mid-handshake. It is the classic cause of "the ESP is pingable
sometimes / the browser spins and times out / an old client with a long timeout works better
than a new one with a fast failure". It also degrades exactly under the multi-connection
access pattern modern phones use.

*Predicted fingerprint:* `ping` shows **intermittent loss and high jitter, not a clean
timeout**; a second attempt immediately after often succeeds; a request that has already
started (keep-alive) is fine.
*Discriminating test:* `<host>` ping 50 packets → look for loss/jitter; then
`curl -o /dev/null -w '%{time_total}'` the same URL 20× in a loop → look for a bimodal
distribution (fast ~50 ms vs 1-3 s). Re-test with the phone's own browser: first load fails,
reload works.
*Fix:* in `initESP8266NetworkConnection()`, right after `WiFi.mode(WIFI_STA);`

```cpp
WiFi.setSleepMode(WIFI_NONE_SLEEP);   // no modem sleep: required for a responsive TCP server
```
(one line; costs a little idle current — irrelevant for a mains-powered controller).

### H2 — No WiFi link supervision and no reconnect after boot

After the boot loop (L66-71) **nothing ever looks at `WiFi.status()` again**; the main loop
(L869-923) handles OTA, PWM, the web server and the temperature sensor, but never the network.
There is no `WiFi.setAutoReconnect(...)` call, no reconnect attempt, no log, no recovery, no
watchdog on the association.

So if the association drops once (AP roam/band-steer, DHCP renewal glitch, a router "kick
idle clients" policy, a power dip), the device can remain **visible in the router's client
list** (stale entry / ARP lease / DHCP lease) while it is not actually reachable and never
comes back. Only a manual power cycle fixes it — which matches "often not reachable" being
unpredictable and persisting.

*Predicted fingerprint:* it works after a reboot and then stops; the router shows the client
with an old "last seen"/lease entry; the ESP's serial log (if you can see it) shows nothing
because nothing is logged.
*Discriminating test:* put a serial console on the device (OTA or USB), leave it running, and
poll `/api/status` from a laptop; when the phones report "unreachable", check the serial log
and `WiFi.status()`. Also compare the router's client list timestamp for the ESP against now.
*Fix:* add a cheap, non-blocking supervisor to `proceedCycle()`:

```cpp
// non-blocking WiFi supervision (once every 5 s)
static uint32_t lastWifiCheck = 0;
if (millis() - lastWifiCheck >= 5000) {
    lastWifiCheck = millis();
    if (WiFi.status() != WL_CONNECTED) {
        Serial.printf("WiFi down (reason %d) - reconnecting\n", WiFi.getDisconnectReason());
        WiFi.reconnect();
        static uint8_t fails = 0;
        if (++fails >= 12) { ESP.restart(); }   // 60 s without a link -> hard recovery
    } else {
        fails = 0;
    }
}
```
plus `WiFi.setAutoReconnect(true);` at init. (Note: this needs a `static` counter outside the
lambda-free loop — implement it as a member, not a local `static`, if you prefer.)

### H3 — Single-threaded server + 1 Hz polling from every open tab + N+1 macro requests

The web server has exactly one slot: `_Server.handleClient()` is called from the main loop
(L910) and one request is processed to completion inside that call. While a request is being
served — and `handleRoot` streams `app.htm` **line by line** via `sendContent()` with
`CONTENT_LENGTH_UNKNOWN` (L34-49), and `handleNotFound` does `SD.open()` + `streamFile()` for
every `.js`/`.css` (L75-95) — no other client is accepted. New connections pile up in the
lwIP listen backlog; when it is full, SYNs are dropped and the phone gives up.

Meanwhile the page itself creates sustained connection pressure:

* `extras/SDCard/js/config.js`: `statusUpdateInterval: 1000` → **one `/api/status` request per
  second, per open tab**.
* `extras/SDCard/js/app.js` `loadMacros()` (L200-230): `GET /api/macro/list`, then
  `Promise.all(...)` → **one `GET /api/macro/get?id=…` per macro, in parallel** (N+1 requests,
  fired simultaneously, each blocking for seconds — see investigation 03).
* ~50 KB of assets (`app.js` 29 KB, `chart-manager.js` 13 KB, `app.htm` 7 KB, `app.css`
  10.5 KB) are re-downloaded from the SD card **on every page load — no `Cache-Control`, no
  `ETag`, no `Last-Modified`** is ever sent. Mobile Safari/Chrome opens a burst of parallel
  connections for exactly these files.

*Predicted fingerprint:* failure correlates with **activity** (page open/reload, macros tab,
two phones at once), not with time; a single curl from a laptop usually works; the HTTP server
becomes unresponsive for a few seconds while a page loads.
*Discriminating test:* from a laptop run 8 parallel requests and watch for timeouts:
`for i in $(seq 8); do curl -s -o /dev/null -w "%{http_code} %{time_total}\n" http://<host>/api/status & done; wait`
→ timeouts / very unequal times indicate backlog saturation. A single curl should be fast.
*Fix (cheap, high value):*
1. Raise the poll interval (`statusUpdateInterval: 5000`) or make `/api/status` update the DOM
   without a request when the tab is hidden (`document.visibilityState`).
2. Send caching headers for static assets (they only change on firmware upload):
   `_Server.sendHeader("Cache-Control", "max-age=604800");`
3. Collapse `loadMacros()`' N+1 into the single `/api/macro/list` call — the firmware already
   returns `duration` there (see investigation 03).
4. Serve `app.htm` with a proper `Content-Length` (or gzip/`PROGMEM`) instead of line-wise
   chunked streaming.

### H4 — No mDNS, no hostname, no guaranteed address

`<ESP8266mDNS.h>` **is included** (`src/AquaControl.h` L26) but `MDNS.begin()` is **never
called** — searching the source finds no `MDNS.` call at all. The OTA hostname is set
(`ArduinoOTA.setHostname("SBAQC")`, L748) but nothing registers a resolvable name for the web
UI, and no `WiFi.hostname()` is set either. Unless `config/wlan.cfg` holds a manual IP
(`ManualIP`), the device takes a **DHCP lease that can change** after a router reboot or lease
expiry.

Consequence: any phone bookmark, home-screen icon, or cached tab that points at an IP/mDNS
name silently "loses" the server even though it is on the network and healthy — and phones
cache aggressively. Again an older phone with an old, still-valid IP may work while a newer
one (which resolved/re-resolved differently, or uses Private Wi-Fi Address) fails.

*Predicted fingerprint:* some bookmarks/tabs never work while a fresh IP works; the router
shows the device at a different address than the bookmark.
*Discriminating test:* compare the address the phones use against `WiFi.localIP()` in the
serial log / the router's client list; try `nslookup <name>.local` (will fail).
*Fix:* fixed IP or DHCP reservation **plus** hostname/mDNS:

```cpp
WiFi.hostname("sbaqc");
MDNS.begin("sbaqc");
MDNS.addService("http", "tcp", 80);
```
then use `http://sbaqc.local/` everywhere.

### H5 — `_Server.begin()` is called twice, the first time before routes exist

`AquaControl::init()` calls `_Server.begin()` at **L786** (immediately after "Initializing
Webserver") and again at **L818** (after `onNotFound`). The first call binds/starts the
listening socket before any route is registered. It is probably harmless on this core, but it
means the server is (briefly) up with an empty route table and the second call has to close and
re-open the listening socket — a needless source of "first connection after boot fails".
*Fix:* delete the `_Server.begin()` at L786, keep the one after the route table.

### H6 (lower probability) — environment / RF

Not visible in the code but worth confirming, because it explains the phone asymmetry:
* Phones on **5 GHz only** with a mesh/band-steering AP, or on a **guest/IoT VLAN** with client
  isolation, can be blocked from the ESP8266's SSID while the app still "shows" the device.
* Aggressive "Wi-Fi Assist"/"private relay"/proxying on the newest phones falls back to
  cellular for the IP the ESP is reachable at.
* ESP8266 RF marginal: RSSI below ≈ -75 dBm plus modem sleep (H1) is a multiplicative failure.
* AP "kick idle clients" / power-save policies terminating a sleeping ESP's association
  (compounds H2).

## 3. What needs the user / hardware access

1. **Router admin access** — client list (is the ESP really associated, with a fresh "last
   seen"?), DHCP lease / reservation, 2.4 vs 5 GHz, band steering, client/AP isolation, guest
   network, and AP logs (deauth/decode reasons for the ESP's MAC).
2. **A laptop on the same SSID** for ping/curl timing tests and parallel-connection tests.
3. **Serial console on the device** (USB or OTA) — needed to see `WiFi.status()`,
   `WiFi.RSSI()`, `WiFi.getDisconnectReason()` and to confirm H1/H2 with a fix applied.
4. **A decision on addressing**: DHCP reservation vs fixed IP in `config/wlan.cfg`, and whether
   to standardise on `sbaqc.local`.
5. **A phone whose settings you can change** to test the "Private Wi-Fi Address" hypothesis
   (toggle it off for the SSID and retry).

## 4. Troubleshooting plan

### Step 0 — classify the failure before touching code

From a laptop on the same SSID, with the ESP known to be at `<host>`:

| Test | Command | Reading |
|---|---|---|
| L2/L3 reachable + stability | `ping -c 50 <host>` | loss/jitter → **H1 / H2** |
| ARP present | `arp -a | grep -i <esp-mac>` | present but ping fails → stale lease (**H2**) |
| Port open | `nc -vz <host> 80` | refused/timeout → server not up (**H2**) |
| One HTTP request | `curl -o /dev/null -w '%{http_code} %{time_total}\n' http://<host>/api/status` | slow (>1 s) → **H1/H3** |
| 20 sequential requests | `for i in $(seq 20); do curl -s -o /dev/null -w '%{time_total} ' http://<host>/api/status; done; echo` | bimodal → **H1** |
| 8 parallel requests | `for i in $(seq 8); do curl -s -m 5 -o /dev/null -w '%{http_code} ' http://<host>/api/status & done; wait; echo` | some `000` → **H3** |
| Whole page from the laptop | `curl -o /dev/null -w '%{size_download} %{time_total}\n' http://<host>/` | ~50 KB / several s → **H3** |
| Name resolution | `nslookup <name>.local` | fails → **H4** |

### Step 1 — the phone comparison (this is the user-visible symptom)

Reproduce on **both** phones at the same moment, same action (reload the page):
* old iPhone 11 works, new phone fails → strongly favours **H1 + H3** (timeout aggressiveness,
  parallel connections) over H2/H4 (which would fail both).
* Both phones fail but a laptop works → favours **H2/H4** (association or addressing).
* The new phone fails on the first attempt and works on reload → **H1** (modem sleep).

### Step 2 — confirm the ranking with the serial console

Add (temporarily) to `proceedCycle()`:
```cpp
static uint32_t lw = 0;
if (millis() - lw >= 2000) { lw = millis();
  Serial.printf("wifi=%d rssi=%d heap=%u reason=%d\n", WiFi.status(), WiFi.RSSI(),
                ESP.getFreeHeap(), WiFi.getDisconnectReason()); }
```
* `wifi=0/6` (not connected) while the router shows the device → **H2**.
* `wifi=3` (connected) but `rssi < -75` → **H6** (RF) amplifying **H1**.
* `wifi=3`, good RSSI, and the phones still fail → **H3** (server-side saturation) or **H4**.

### Step 3 — apply the fixes in this order and re-test after each

1. `WiFi.setSleepMode(WIFI_NONE_SLEEP);` — one line, biggest expected win (**H1**).
2. WiFi supervision + reconnect (**H2**).
3. Delete the duplicate `_Server.begin()` (**H5**).
4. Poll interval 1000 → 5000 ms, `Cache-Control` on static assets, `loadMacros()` N+1 → 1
   (**H3**).
5. `WiFi.hostname()` + `MDNS.begin()` + DHCP reservation (**H4**).

After each step, re-run the Step 0 table and note which row changed. If step 1 alone fixes it,
that is the answer; if only step 4 does, the problem was connection pressure, not sleep.

### Step 4 — if nothing in the code helps

Re-check H6 with the router: put a phone on the **2.4 GHz SSID only**, disable client
isolation, and (temporarily) disable any "smart connect"/band steering and the phone's Private
Wi-Fi Address for that SSID. Also confirm the ESP is not on a guest VLAN. A flaky 5 V supply
(voltage sag during WiFi TX bursts → brown-out resets) also produces exactly "unreachable but
present in scans"; `ESP.getVcc()`/`/api/debug` (`vcc_voltage_mv`, `free_heap`, `uptime`) in
`Webserver.cpp` `handleApiDebug` (L1590-1695) is the cheap check: if `uptime` resets, the
device is rebooting, not merely unreachable.

## 5. Verification status

* Everything above is read from the source; **`WiFi.setSleepMode` / `MDNS.begin` are absent by
  search, not by assumption**, and the polling intervals / `Promise.all` fan-out /
  missing cache headers were read from `extras/SDCard/js/*`.
* No hardware was available here: H1-H5 are *hypotheses with a discriminating test*, not
  confirmed root causes. Step 0's classification table is what turns them into a diagnosis, and
  it can be run before any code change.
* The proposed fixes are **not compiled or flashed** (PlatformIO not installed here).

## 6. References

* `src/AquaControl.cpp` L52-87 (network init), L715-770 + L784-819 (init, web server setup,
  duplicate `begin()`), L869-923 (main loop — no WiFi handling after boot)
* `src/AquaControl.h` L26 (`ESP8266mDNS.h` included, never used), L37 (`_Server(80)`)
* `src/Webserver.cpp` L23-54 (`handleRoot`, line-wise chunked streaming), L56-124
  (`handleNotFound`, static files from SD), L144-233 (`handleApiStatus`), L1590-1695
  (`/api/debug`: `free_heap`, `uptime`, `vcc_voltage_mv`)
* `extras/SDCard/js/config.js` (`statusUpdateInterval: 1000`), `extras/SDCard/js/app.js`
  L200-230 (`loadMacros`, N+1), `extras/SDCard/js/api.js`
* `docs/status/HYBRID_TIME_SYNC_IMPLEMENTATION.md`, `docs/status/FIRMWARE_STATUS.md`
