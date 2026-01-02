---
title: Physics-Oriented Learning Guide for Embedded Concepts
version: 1.0
date_created: 2026-01-02
last_updated: 2026-01-02
handoff: learn agent
---

# Implementation Plan: LEARNING_GUIDE.md

## Overview
Create a physicist-friendly learning guide that explains embedded programming concepts using actual SBAquaControl code examples. The guide will bridge the gap between abstract software patterns and concrete implementations by using physics analogies familiar to scientists, while avoiding the pitfalls of linear tutorial-style documentation that can be overwhelming for ADHD learning styles.

**Target audience**: User with physics background (Bachelors-level), ADHD learning style  
**Approach**: Concept-first, problem-focused, real code examples  
**Output**: Single markdown file with 8-10 core concepts  

---

## Requirements

### Functional Requirements
- **8-10 topics** covering fundamental embedded concepts used in SBAquaControl
- **Physics analogies** for each concept (e.g., linear interpolation = velocity calculation)
- **Real code examples** from actual codebase with file:line references
- **Problem-focused structure**: "Why this matters" → "How it works" → "See it in action"
- **Progressive difficulty**: Foundational patterns first → Advanced integration patterns
- **Cross-references** to ARCHITECTURE.md and learning-progress.md

### Non-Functional Requirements
- **Concise**: Each topic 300-500 words (not tutorial-length)
- **Scannable**: Headers, code blocks, callouts for quick navigation
- **Confidence-calibrated**: Initial topics at level 3 (adjustable based on user feedback)
- **Self-contained**: Each topic understandable independently (no forced sequential reading)
- **Maintainable**: Easy to update when code changes

---

## Architecture and Design

### Document Structure
```
LEARNING_GUIDE.md
├── Introduction (physicist background, how to use this guide)
├── Topic 1: Foundational Concepts (Linear Interpolation)
│   ├── Concept Overview (What is it?)
│   ├── Physics Analogy (How is it like position/velocity?)
│   ├── Code Example (proceedCycle implementation)
│   ├── Common Pitfalls (Integer overflow, day-wrapping)
│   └── See Also (references)
├── Topic 2: [Next concept...]
└── Appendix: Quick Reference Table (pattern → file location)
```

### Topic Template Pattern
Each topic follows this structure:
1. **Concept**: 1-2 sentence summary ("What is this?")
2. **Physics Analogy**: Relates to familiar physics concepts
3. **Why It Matters**: Problem it solves in SBAquaControl
4. **How It Works**: Technical explanation with math/diagrams
5. **Code Example**: Real implementation with line references
6. **Common Pitfalls**: What to watch out for
7. **See Also**: Links to ARCHITECTURE.md, related topics

### 8-10 Core Topics (Progressive Order)

#### Phase 1: Foundational Patterns (Build Mental Model)
1. **Linear Interpolation** — Smooth PWM transitions between targets
2. **Time Representation** — Unix timestamps, seconds-of-day, milliseconds
3. **Main Loop Architecture** — Why `proceedCycle()` must be non-blocking (<10ms)

#### Phase 2: Hardware Abstraction (System Integration)
4. **I2C Communication** — PCA9685 PWM controller, DS3231 RTC
5. **Conditional Compilation** — Platform-specific code (PCA9685 vs native PWM)
6. **PWM Hardware Abstraction** — Unified interface across platforms

#### Phase 3: Memory-Constrained Programming (ESP8266 Specifics)
7. **Memory Management** — String vs char buffers, heap fragmentation
8. **JSON Streaming** — Avoiding String concatenation in HTTP responses

#### Phase 4: Advanced Patterns (Real-World Complexity)
9. **Tick-Tock Async Pattern** — Non-blocking temperature reading
10. **File I/O Atomicity** — Safe SD card writes with temp files

---

## Implementation Tasks

### Phase 1: Document Structure Setup
**Duration**: 10 min  
**Deliverables**: File skeleton, template sections

- [ ] Create `LEARNING_GUIDE.md` in project root
  - Add frontmatter: title, version, target audience
  - Add introduction section (how to use, confidence flags)
  - Add appendix placeholder (quick reference table)

- [ ] Define topic template in comments
  ```markdown
  <!-- Topic Template:
  ## N. [Topic Name]
  
  **Concept**: One-sentence summary
  **Physics Analogy**: How it relates to physics
  **Confidence Level**: 3 (adjust based on feedback)
  
  ### Why It Matters
  [Problem it solves...]
  
  ### How It Works
  [Technical explanation...]
  
  ### Code Example
  [Real implementation with links...]
  
  ### Common Pitfalls
  [What to watch out for...]
  
  ### See Also
  [References...]
  -->
  ```

### Phase 2: Foundational Topics (Topics 1-3)
**Duration**: 20 min  
**Deliverables**: 3 foundational topics with code examples

- [ ] **Topic 1: Linear Interpolation** — [src/AquaControl.cpp#L928-L1010](../../src/AquaControl.cpp#L928)
  - **Physics analogy**: Like calculating position from velocity: $x(t) = x_0 + v \cdot t$
  - **Math breakdown**: Slope-intercept form `vx = (m * deltaNow) + n`
  - **Code walkthrough**: 
    - Find current and next targets (line 951-982)
    - Calculate slope `m = dv/dt` (line 989)
    - Interpolate value (line 992)
    - Handle day-wrapping edge case (line 977-984)
  - **Common pitfalls**: 
    - Integer overflow when `dt` is large (use float intermediate)
    - Negative time when wrapping midnight (line 965)
    - Clamping to prevent overshoot (line 993-1003)

- [ ] **Topic 2: Time Representation** — [src/AquaControl.cpp#L180-L220](../../src/AquaControl.cpp#L180)
  - **Physics analogy**: Like coordinate systems (absolute vs relative reference frames)
  - **Three time scales**:
    - Unix timestamp: Absolute (seconds since 1970-01-01)
    - Seconds-of-day: Relative (0-86399, resets at midnight)
    - Milliseconds: Sub-second precision (0-999)
  - **Code example**: [AquaControl::proceedCycle()](../../src/AquaControl.cpp#L711)
    - `CurrentSecOfDay = elapsedSecsToday(now())` (line 622)
    - `CurrentMilli = millis() % 1000` (line 623)
  - **Common pitfall**: Mixing absolute and relative time (causes day-wrapping bugs)

- [ ] **Topic 3: Main Loop Architecture** — [src/AquaControl.cpp#L711-L750](../../src/AquaControl.cpp#L711)
  - **Physics analogy**: Like a stroboscopic measurement (sample at regular intervals)
  - **10ms constraint**: ESP8266 watchdog timer requires loop completion <10ms
  - **Non-blocking pattern**: All operations use state machines, no `delay()`
  - **Code example**: 
    - [AquaControl::proceedCycle()](../../src/AquaControl.cpp#L711) orchestrates all subsystems
    - Calls [PwmChannel::proceedCycle()](../../src/AquaControl.cpp#L928) for each channel
    - Handles web server with `_Server.handleClient()` (line 744)
  - **Common pitfall**: Using `delay()` blocks main loop → watchdog reset

### Phase 3: Hardware Abstraction Topics (Topics 4-6)
**Duration**: 15 min  
**Deliverables**: 3 hardware integration topics

- [ ] **Topic 4: I2C Communication** — [src/AquaControl.cpp#L840-L850](../../src/AquaControl.cpp#L840)
  - **Physics analogy**: Like a shared bus in particle physics experiments (CAMAC, VME)
  - **Two devices on same bus**:
    - PCA9685 PWM controller (address 0x40)
    - DS3231 RTC (address 0x68)
  - **Code example**: [writePwmToDevice()](../../src/AquaControl.cpp#L840)
    - `pwm.setPWM(channel, 0, value)` writes to PCA9685 via I2C
  - **Common pitfall**: I2C is slow (~100kHz) — don't update all 16 channels every cycle

- [ ] **Topic 5: Conditional Compilation** — [src/AquaControl_config.h](../../src/AquaControl_config.h)
  - **Physics analogy**: Like detector-specific analysis code (CMS vs ATLAS)
  - **Platform selection**:
    ```cpp
    #if defined(USE_PCA9685)       // 16 channels, 12-bit
    #elif defined(ESP8266)         // 2 channels, 10-bit
    #elif defined(__AVR__)         // 6-16 channels, 8-bit
    ```
  - **Code example**: [writePwmToDevice()](../../src/AquaControl.cpp#L840)
    - Line 841-843: PCA9685 I2C call
    - Line 844-845: Native `analogWrite()` fallback
  - **Common pitfall**: Hardcoding `PWM_MAX = 4095` breaks on other platforms

- [ ] **Topic 6: PWM Hardware Abstraction** — [src/AquaControl.h](../../src/AquaControl.h)
  - **Physics analogy**: Like detector calibration (convert ADC counts to energy)
  - **Unified interface**: `CurrentWriteValue` is always 0-PWM_MAX
  - **Constants**: `PWM_MAX`, `PWM_CHANNELS`, `PWM_CHANNEL_N`
  - **Code example**: [AquaControl.h constants](../../src/AquaControl.h)
  - **Common pitfall**: Never use magic numbers (e.g., `if (value > 4095)`)

### Phase 4: Memory-Constrained Topics (Topics 7-8)
**Duration**: 10 min  
**Deliverables**: 2 memory optimization topics

- [ ] **Topic 7: Memory Management** — [ARCHITECTURE.md#Memory-Management](../../ARCHITECTURE.md)
  - **Physics analogy**: Like memory pool in DAQ systems (pre-allocated buffers)
  - **ESP8266 constraint**: 160KB total, ~80KB available at runtime
  - **String class problem**: Heap fragmentation from repeated allocation/deallocation
  - **Code example**: [extractIPAddress()](../../src/AquaControl.cpp#L853)
    - Uses `String` (mutable copy) but only in init path
    - Alternative pattern: `sprintf(buffer, "format", args)`
  - **Common pitfall**: String concatenation in `proceedCycle()` → heap fragmentation → crash

- [ ] **Topic 8: JSON Streaming** — [src/Webserver.cpp](../../src/Webserver.cpp)
  - **Physics analogy**: Like streaming data from detector (don't buffer entire run)
  - **Problem**: Building full JSON response String can exceed RAM
  - **Solution**: `_Server.sendContent(chunk)` sends data incrementally
  - **Code example**: [handleApiScheduleAll()](../../src/Webserver.cpp) (when implemented)
  - **Common pitfall**: `String json = "["; for(...) json += "..."; json += "]"` → out of memory

### Phase 5: Advanced Patterns (Topics 9-10)
**Duration**: 15 min  
**Deliverables**: 2 advanced integration topics

- [ ] **Topic 9: Tick-Tock Async Pattern** — [src/AquaControl.cpp#L608-L820](../../src/AquaControl.cpp#L608)
  - **Physics analogy**: Like double-buffering in oscilloscope (acquire while processing previous)
  - **Problem**: DS18B20 temperature reading takes 750ms → blocks main loop
  - **Solution**: State machine with two calls
    1. First call: Start conversion, return immediately
    2. Second call (750ms later): Read result
  - **Code example**: [TemperatureReader::readTemperature()](../../src/AquaControl.cpp#L765)
    - Line 770: Check if conversion time elapsed (`_TickTock` flag)
    - Line 777: Start conversion if not started
    - Line 805: Read result if started
  - **Common pitfall**: Forgetting to call twice → never gets result

- [ ] **Topic 10: File I/O Atomicity** — [src/Webserver.cpp](../../src/Webserver.cpp)
  - **Physics analogy**: Like write-ahead logging in data acquisition (ensure crash-safe)
  - **Problem**: SD card corruption if power loss during write
  - **Solution**: Write to temp file, then atomic rename
  - **Code pattern**:
    1. Write to `config/ledch_00_new.cfg`
    2. Delete `config/ledch_00.cfg`
    3. Rename `_new.cfg` → `.cfg`
  - **Code example**: [writeLedConfig()](../../src/AquaControl.cpp#L290) (pattern reference)
  - **Common pitfall**: Directly overwriting file → partial writes if power loss

### Phase 6: Appendix and Cross-References
**Duration**: 10 min  
**Deliverables**: Quick reference table, links

- [ ] Create Quick Reference Table
  ```markdown
  | Pattern | Used In | File:Line |
  |---------|---------|-----------|
  | Linear Interpolation | PWM transitions | [AquaControl.cpp#L928](src/AquaControl.cpp#L928) |
  | Tick-Tock Async | Temperature reading | [AquaControl.cpp#L765](src/AquaControl.cpp#L765) |
  | Non-Blocking Loop | Main orchestration | [AquaControl.cpp#L711](src/AquaControl.cpp#L711) |
  | ...
  ```

- [ ] Add cross-references
  - Link each topic to [ARCHITECTURE.md](../../ARCHITECTURE.md) sections
  - Link to [learning-progress.md](../.github/learning-progress.md) for tracking
  - Add "Next Steps" section pointing to advanced topics

- [ ] Add navigation aids
  - Table of contents with anchor links
  - "Prerequisites" section for each topic (which earlier topics to read first)
  - Confidence flag explanation in introduction

### Phase 7: Review and Polish
**Duration**: 10 min  
**Deliverables**: Proofread document, validate links

- [ ] Validate all file:line references (ensure line numbers are current)
- [ ] Check physics analogies for accuracy and clarity
- [ ] Ensure code examples compile (at least syntax-check)
- [ ] Proofread for typos, formatting consistency
- [ ] Update MASTERPLAN.md to mark Step 2 complete

---

## Testing Strategy

### Content Validation
- [ ] **Physics accuracy**: Review analogies with user (doctorate physicist)
- [ ] **Code accuracy**: Verify line references point to correct code
- [ ] **Link validation**: All internal links resolve correctly
- [ ] **Readability**: Physicist with no embedded background can follow

### User Feedback Loop
1. User reads Topic 1-3 (foundational)
2. User updates [learning-progress.md](../.github/learning-progress.md) confidence flags:
   - Flag = 1 → Too detailed/advanced
   - Flag = 3 → About right
   - Flag = 5 → Too basic/missing depth
3. Learn agent adjusts remaining topics based on feedback
4. Repeat for Topics 4-6, 7-10

### Success Criteria
✅ All 8-10 topics completed with examples  
✅ Each topic has physics analogy  
✅ All code examples have valid file:line references  
✅ Document is 2500-4000 words (not a full tutorial)  
✅ User can navigate topics independently (no forced order)  
✅ Confidence flags initialized at level 3  

---

## Open Questions

1. **Depth of math**: Should linear interpolation include full derivation, or just formula? (Recommend: Formula + intuition, not full proof)

2. **Diagram inclusion**: Should topics include ASCII diagrams or links to external visualizations? (Recommend: ASCII for simple cases, defer complex diagrams to future iteration)

3. **Code snippet length**: How much surrounding context to include? (Recommend: 10-20 lines max, link to full file for more)

4. **ADHD optimization**: Should each topic have a "TL;DR" callout box at the top? (Recommend: Yes, add 1-sentence summary in bold)

---

## Success Criteria

✅ LEARNING_GUIDE.md created with 8-10 topics  
✅ Each topic follows template structure  
✅ Physics analogies present and accurate  
✅ Real code examples with file:line links  
✅ Progressive difficulty (foundational → advanced)  
✅ Cross-references to ARCHITECTURE.md, learning-progress.md  
✅ Quick reference table in appendix  
✅ Document is scannable (headers, callouts, code blocks)  
✅ User can read topics independently (no forced sequence)  
✅ Total length 2500-4000 words  

---

## Dependencies & Blockers

- **Depends on**: Step 1 complete ✅ (ARCHITECTURE.md, learning-progress.md exist)
- **Blocked by**: None
- **Unblocks**: Future physics-based explanations in other docs
- **Parallel with**: Steps 3, 4, 5 (independent workstreams)

---

## Notes

### Physics Analogy Guidelines
- Use concepts from classical mechanics, electromagnetism, statistical mechanics
- Avoid quantum mechanics or esoteric topics (not universally familiar)
- Prefer equations in LaTeX format: `$x(t) = x_0 + v \cdot t$`
- Reference frame analogies work well (absolute vs relative time)

### Code Example Best Practices
- Always link with line ranges: `[AquaControl.cpp#L928-L1010](src/AquaControl.cpp#L928)`
- Include enough context (function signature, variable declarations)
- Highlight the key pattern (use comments in code block)
- Don't paste full functions (link to full code instead)

### ADHD-Friendly Formatting
- **Bold** key takeaways
- Use callout boxes: `> ⚠️ **Common Pitfall**: ...`
- Short paragraphs (3-5 lines max)
- Code blocks for visual break
- Bullet lists for enumerations

### Maintenance Plan
- When code changes, update line numbers in quarterly review
- Add new topics as user learns (e.g., "Macro System Architecture")
- Track discussion counts in learning-progress.md to avoid redundant re-explanations

---

## Handoff to Learn Agent

**Context**: This plan is ready for the **learn agent** to execute. The learn agent should:

1. Read this plan completely
2. Read [ARCHITECTURE.md](../../ARCHITECTURE.md) for technical context
3. Read [learning-progress.md](../.github/learning-progress.md) for current confidence levels
4. Create LEARNING_GUIDE.md following the topic template
5. Start with Topics 1-3, get user feedback on confidence levels
6. Adjust depth of Topics 4-10 based on feedback
7. Update learning-progress.md with new discussion counts and summaries

**Key Principle**: Explain concepts at confidence level 3 by default, adjust based on user feedback. The goal is to build intuition, not memorization.

**Estimated Time**: 60 minutes (10 min per topic + 10 min setup/polish)
