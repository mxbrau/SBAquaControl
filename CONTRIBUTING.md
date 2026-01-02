# Contributing to SBAquaControl

**See Also:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - System internals and technical design
- [docs/status/DEVELOPMENT.md](docs/status/DEVELOPMENT.md) - Extended workflow guide
- [docs/status/TESTING_GUIDE.md](docs/status/TESTING_GUIDE.md) - Validation procedures

---

Welcome! This guide helps you understand the codebase structure and development workflows for SBAquaControl.

## Before You Start

Read these documents in order:
1. **[PRODUCT.md](PRODUCT.md)** — What the system does
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** — How it works internally
3. **This file** — How to develop and contribute

## Build System

### Requirements
- **VS Code** with **PlatformIO IDE** extension (not Arduino IDE)
- **Python 3.8+** (for development scripts)

### Building Firmware

**First-time USB upload:**
```bash
pio run -e esp8266 --target upload
```

**OTA (WiFi) upload** (after initial setup):
```bash
pio run -e esp8266_ota --target upload
```

**Monitor serial output:**
```bash
pio device monitor
```

All `pio` commands must run in VS Code's **PlatformIO CLI terminal**, not PowerShell.

## Code Organization

### Firmware (C++)
- `src/AquaControl.h` → Main controller class declaration
- `src/AquaControl.cpp` → Core logic + initialization
- `src/Webserver.cpp` → HTTP API endpoints (JSON REST)
- `src/AquaControl_config.h` → Compile-time feature flags
- `examples/AquaControlSketch/AquaControlSketch.ino` → Arduino sketch (entry point)

### Web UI (JavaScript/HTML)
- `extras/SDCard/app.htm` → HTML shell with placeholders
- `extras/SDCard/js/app.js` → Application controller
- `extras/SDCard/js/chart-manager.js` → Chart.js visualization
- `extras/SDCard/js/api.js` → REST API wrapper
- `extras/SDCard/css/` → Styling

### Configuration (SD Card)
- `extras/SDCard/config/ledch_00.cfg` → Schedule per channel
- `extras/SDCard/config/wlan.cfg` → WiFi settings
- `extras/SDCard/macros/macro_NNN_chNN.cfg` → Macro definitions

## Critical Design Constraints

### Memory (ESP8266: 160KB RAM, 50-55% in use)
- ❌ **Avoid**: `String` class in production code (causes heap fragmentation)
- ✅ **Use**: `char` buffers + `sprintf()`
- ❌ **Avoid**: Building large strings before sending
- ✅ **Use**: `_Server.sendContent()` to stream JSON responses

**Memory-safe pattern:**
```cpp
char buf[64];
sprintf(buf, "{\"channel\":%u,\"value\":%u}", channel, value);
_Server.sendContent(buf);
```

### Non-blocking Operations
- ❌ **Never**: Call `delay()` except during WiFi init
- ✅ **Do**: Use state machines (tick-tock pattern) for async tasks
- ❌ **Never**: Perform I2C operations synchronously in main loop
- ✅ **Do**: Break operations across multiple `proceedCycle()` calls

**Tick-tock pattern example** (see TemperatureReader):
```cpp
if (!_TickTock) {
  _TickTock = true;
  // First call: start operation (non-blocking)
  startSensorRead();
} else {
  _TickTock = false;
  // Second call: fetch result (guaranteed ready)
  processResult();
}
```

### Linear Interpolation
All smooth transitions use this formula:
```
slope = (targetValue - baseValue) / elapsedTime
interpolated = slope * currentElapsed + baseValue
```
Applied to PWM, LED color channels, and future gradients.

## Coding Standards

### C++ Naming
- Functions: `camelCase` (e.g., `addChannelTarget()`)
- Classes: `PascalCase` (e.g., `AquaControl`, `PwmChannel`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `PWM_MAX`, `PWM_CHANNELS`)
- Member variables: Prefix `_` for private (e.g., `_PwmValue`)

### JavaScript Naming
- Functions: `camelCase` (e.g., `updateSchedule()`)
- Variables: `camelCase` (e.g., `currentValue`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `API_BASE_URL`)

### Comments
- Prefer **why** over **what** (code shows what, comments explain intent)
- Use `F()` macro for string literals in C++ to save RAM:
  ```cpp
  Serial.println(F("Initializing SD card...")); // ✅ stored in flash
  Serial.println("Initializing SD card..."); // ❌ duplicated in RAM
  ```

### File I/O Pattern
Use atomic writes to prevent corruption:
```cpp
// 1. Read original
// 2. Write to _new file
// 3. Delete original
// 4. Rename _new → original
```
Example: `writeWlanConfig()` in AquaControl.cpp

## Testing Workflow

### Manual Testing
1. Load [docs/status/TESTING_GUIDE.md](docs/status/TESTING_GUIDE.md) for test cases
2. Use "Test Mode" in web UI to verify channel behavior
3. Inspect Serial monitor for error messages

### Unit Tests (Future)
Currently manual. When adding automated tests:
- Framework: Unity (configured in platformio.ini)
- Location: `test/` directory
- Command: `pio test`

## GitHub Workflow

### Issue Tracking
1. Check [GitHub Issues](https://github.com/your-repo/issues) before starting work
2. Create issue for bugs/features (reference in commits)
3. Link pull requests to issues

### Commit Messages
```
Fix: macro timer not stopping after duration
Ref: issue #1

Implemented handleApiMacroActivate() with MacroState tracking.
Auto-restores previous schedule when macro expires.
```

### Pull Request Template
- Link related issue
- Describe changes
- Note any new memory usage or build implications

## Documentation Updates

### When to Update Docs
- ❌ **Don't** create session summaries (avoid duplicates)
- ✅ **Do** update ARCHITECTURE.md if system design changes
- ✅ **Do** update CONTRIBUTING.md for new coding patterns
- ✅ **Do** add comments to complex functions

### Learning Progress Tracking
- After explaining a concept to you, agent updates [.github/learning-progress.md](.github/learning-progress.md)
- You adjust confidence flags (1=too deep, 5=too basic) to calibrate agent
- Use this as you familiarize yourself with different areas

## Context Maintenance

### Triggers for Updating copilot-instructions.md
1. **On every commit**: Auto-check if docs are referenced correctly
2. **After 500+ edited lines**: Review if new patterns emerged
3. **On feature completion**: Update relevant architecture docs

### Git Workflow
```bash
git add .
git commit -m "Build: add macro timer tracking (issue #1)"
# Commit triggers automatic doc validation
```

## Debugging Tips

### Serial Output
- Check monitor output: `pio device monitor` (19200 baud)
- Use `F()` macro to avoid memory bloat
- Disable if RAM is tight

### Over-the-Air Upload Failures
- Ensure device has stable WiFi connection
- Check password: `upload_flags = --auth=aquarium123`
- Verify IP address: Set in `env:esp8266_ota` → `upload_port`

### SD Card Issues
- File system errors usually appear in Serial monitor
- Ensure SD card is inserted before boot
- Use web UI `/api/debug` endpoint to check file system

## Performance Expectations

- **Main loop**: ~10ms per cycle (100Hz refresh)
- **Chart rendering**: <500ms for 24-hour schedule
- **Schedule save**: <1s (SD card write)
- **WebSocket polling**: Every 2 seconds (low overhead)

## Questions?

Refer to [ARCHITECTURE.md](ARCHITECTURE.md) for system design, [README.md](README.md#-quick-start) for setup, or [docs/status/TESTING_GUIDE.md](docs/status/TESTING_GUIDE.md) for validation workflows.

For learning the code: Use the custom `learn` agent in VS Code Chat to get adaptive explanations. Update [.github/learning-progress.md](.github/learning-progress.md) confidence flags as you become familiar with concepts.
