# Learning Progress Tracker

**Last updated**: 2026-01-02 by system initialization  
**Confidence scale**: 1=too deep/advanced | 3=about right | 5=too basic/incomplete

---

## Core Concepts

### ESP8266 Memory Model
- **Discussion count**: 0
- **Last covered**: —
- **Summary**: —
- **Confidence flag**: 3 (default)
- **References**: [ARCHITECTURE.md#Hardware-Layer](ARCHITECTURE.md#hardware-layer), [CONTRIBUTING.md#Memory](CONTRIBUTING.md#memory-esp8266-160kb-ram-50-55-in-use)

### Linear Interpolation in PWM
- **Discussion count**: 0
- **Last covered**: —
- **Summary**: —
- **Confidence flag**: 3 (default)
- **References**: [ARCHITECTURE.md#Design-Patterns](ARCHITECTURE.md#design-patterns), [AquaControl.cpp#L810-L890](src/AquaControl.cpp#L810)

### TimeLib.h and Unix Timestamps
- **Discussion count**: 0
- **Last covered**: —
- **Summary**: —
- **Confidence flag**: 3 (default)
- **References**: [ARCHITECTURE.md#Microcontroller](ARCHITECTURE.md#microcontroller-esp8266-160mhz-160kb-ram), [AquaControl.cpp#L180-L220](src/AquaControl.cpp#L180)

### PCA9685 I2C PWM Controller
- **Discussion count**: 0
- **Last covered**: —
- **Summary**: —
- **Confidence flag**: 3 (default)
- **References**: [ARCHITECTURE.md#PWM-Output](ARCHITECTURE.md#pwm-output), [AquaControl.cpp#L600-L650](src/AquaControl.cpp#L600)

### DS3231 RTC and System Time
- **Discussion count**: 0
- **Last covered**: —
- **Summary**: —
- **Confidence flag**: 3 (default)
- **References**: [ARCHITECTURE.md#Microcontroller](ARCHITECTURE.md#microcontroller-esp8266-160mhz-160kb-ram)

### Tick-Tock Async Pattern
- **Discussion count**: 0
- **Last covered**: —
- **Summary**: —
- **Confidence flag**: 3 (default)
- **References**: [ARCHITECTURE.md#Design-Patterns](ARCHITECTURE.md#design-patterns), [TemperatureReader](src/AquaControl.cpp#L608)

### SD Card File I/O and Config Management
- **Discussion count**: 0
- **Last covered**: —
- **Summary**: —
- **Confidence flag**: 3 (default)
- **References**: [ARCHITECTURE.md#Storage](ARCHITECTURE.md#storage-sd-card-cs-pin-d8-on-esp8266), [AquaControl.cpp#readLedConfig()](src/AquaControl.cpp#L370)

### String vs char Buffer Memory Safety
- **Discussion count**: 0
- **Last covered**: —
- **Summary**: —
- **Confidence flag**: 3 (default)
- **References**: [CONTRIBUTING.md#Memory](CONTRIBUTING.md#memory-esp8266-160kb-ram-50-55-in-use), [ARCHITECTURE.md#Memory-Management](ARCHITECTURE.md#memory-management-critical)

### Main Loop and proceedCycle() Architecture
- **Discussion count**: 0
- **Last covered**: —
- **Summary**: —
- **Confidence flag**: 3 (default)
- **References**: [ARCHITECTURE.md#Main-Loop](ARCHITECTURE.md#main-loop-non-blocking)

### REST API Design and HTTP Endpoints
- **Discussion count**: 0
- **Last covered**: —
- **Summary**: —
- **Confidence flag**: 3 (default)
- **References**: [ARCHITECTURE.md#Web-Interface](ARCHITECTURE.md#web-interface-javascript---single-page-app), [Webserver.cpp](src/Webserver.cpp)

---

## JavaScript / Web UI Concepts

### Chart.js Visualization and Event Handling
- **Discussion count**: 0
- **Last covered**: —
- **Summary**: —
- **Confidence flag**: 3 (default)
- **References**: [chart-manager.js](extras/SDCard/js/chart-manager.js)

### Async JavaScript (fetch, promises, async/await)
- **Discussion count**: 0
- **Last covered**: —
- **Summary**: —
- **Confidence flag**: 3 (default)
- **References**: [api.js](extras/SDCard/js/api.js), [app.js](extras/SDCard/js/app.js)

### DOM Manipulation and Event Listeners
- **Discussion count**: 0
- **Last covered**: —
- **Summary**: —
- **Confidence flag**: 3 (default)
- **References**: [app.js](extras/SDCard/js/app.js)

---

## System Workflows

### Boot Sequence and Initialization
- **Discussion count**: 0
- **Last covered**: —
- **Summary**: —
- **Confidence flag**: 3 (default)
- **References**: [ARCHITECTURE.md#Boot-Sequence](ARCHITECTURE.md#boot-sequence), [AquaControl.cpp#init()](src/AquaControl.cpp#L200)

### Schedule Execution and Target Interpolation
- **Discussion count**: 0
- **Last covered**: —
- **Summary**: —
- **Confidence flag**: 3 (default)
- **References**: [ARCHITECTURE.md#Schedule-Execution](ARCHITECTURE.md#schedule-execution)

### Macro System and Temporary Overrides
- **Discussion count**: 0
- **Last covered**: —
- **Summary**: —
- **Confidence flag**: 3 (default)
- **References**: [PRODUCT.md#3-Temporary-Lighting-Overrides-Macros](PRODUCT.md#3-temporary-lighting-overrides-macros)

---

## Instructions for Learn Agent

When explaining concepts:
1. **Before**: Consult this file for prior discussions and confidence flags
2. **Adjust depth**:
   - If confidence ≤ 2: Use fine-grained, line-by-line explanations
   - If confidence = 3: Standard explanations with examples
   - If confidence ≥ 4: High-level overviews, skip basic details
3. **After explaining**: Update the topic section with:
   - Increment discussion count
   - Add 1-2 sentence summary (what was covered)
   - **Propose** update to user for approval (don't auto-save)
4. **User role**: Adjust confidence flag up/down to calibrate agent

## Instructions for User

- **Edit confidence flags** anytime to recalibrate (range 1-5)
- **Don't maintain manually**: Agent proposes updates after each explanation
- **Review summaries**: Ensure they match what you want to remember
- **Track mastery**: Topics with high discussion count can go faster next time
