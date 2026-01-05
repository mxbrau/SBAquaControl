# SBAquaControl Documentation Index

**Last Updated**: January 5, 2026  
**Firmware Version**: 0.5.001

This index helps you navigate the SBAquaControl documentation and find the information you need quickly.

---

## 📚 Getting Started (New Users)

Start here if you're new to the project:

1. **[README.md](README.md)** - Project overview, quick start guide, and installation
2. **[QUICKSTART.md](QUICKSTART.md)** - Redirects to README quick start section
3. **[PRODUCT.md](PRODUCT.md)** - Features overview, user workflows, and benefits
4. **[docs/reference/QUICK_REFERENCE.md](docs/reference/QUICK_REFERENCE.md)** - Command cheat sheet and API reference

**Recommended Reading Order**: README → PRODUCT → QUICK_REFERENCE

---

## 🔧 Development & Contributing

For developers who want to modify or extend the project:

1. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development guidelines, coding standards, and build process
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design, technical details, and implementation patterns
3. **[docs/status/DEVELOPMENT.md](docs/status/DEVELOPMENT.md)** - Extended workflow guide and setup instructions

**Key Sections**:
- Build system and PlatformIO setup
- Memory constraints and optimization patterns
- Non-blocking operations and design patterns
- File organization and structure

---

## 📊 Current Status & Roadmap

Understanding what's implemented and what's planned:

1. **[docs/status/FIRMWARE_STATUS.md](docs/status/FIRMWARE_STATUS.md)** - Current implementation status and features
2. **[docs/status/ROADMAP.md](docs/status/ROADMAP.md)** - Future development plans and phases
3. **[docs/status/TESTING_GUIDE.md](docs/status/TESTING_GUIDE.md)** - Comprehensive test procedures

**Current Status (v0.5.001)**:
- ✅ Phase 1-3 Complete (Core features, optimization, macro system)
- 🚀 Phase 4 Next: Enhanced visualization (Q1 2026)

---

## 🧪 Testing & Validation

Test procedures and validation guides:

1. **[docs/status/TESTING_GUIDE.md](docs/status/TESTING_GUIDE.md)** - Comprehensive testing guide
2. **[docs/testing/test-hybrid-time-sync.md](docs/testing/test-hybrid-time-sync.md)** - Time sync feature tests
3. **[docs/testing/test-time-api.md](docs/testing/test-time-api.md)** - Time API endpoint tests

**When to Use**:
- Before deploying to production
- After making firmware changes
- Validating new features

---

## 🎨 Design Documents

Technical design specifications and implementation details:

1. **[docs/design/MACRO_REFACTORING.md](docs/design/MACRO_REFACTORING.md)** - Macro system design and architecture
2. **[docs/design/UI_UPDATE_LINEAR_INTERPOLATION.md](docs/design/UI_UPDATE_LINEAR_INTERPOLATION.md)** - UI visualization changes

**Purpose**: Reference documentation for understanding design decisions

---

## 🔍 Feature-Specific Documentation

Deep dives into specific features:

### Hybrid Time Synchronization
- **[docs/status/HYBRID_TIME_SYNC_IMPLEMENTATION.md](docs/status/HYBRID_TIME_SYNC_IMPLEMENTATION.md)** - Implementation summary (✅ completed)
- **[docs/status/BROWSER_AUTO_SYNC.md](docs/status/BROWSER_AUTO_SYNC.md)** - Browser auto-sync feature (✅ implemented)
- **[docs/testing/test-hybrid-time-sync.md](docs/testing/test-hybrid-time-sync.md)** - Test procedures

**Key Features**:
- NTP sync (optional via USE_NTP)
- RTC fallback
- Manual sync via API
- Browser auto-sync

### Macro System
- **[docs/design/MACRO_REFACTORING.md](docs/design/MACRO_REFACTORING.md)** - Design specification
- **[ARCHITECTURE.md#macro-system](ARCHITECTURE.md)** - Implementation details

**Key Features**:
- Temporary lighting overrides
- Duration-based timer
- Auto-restore to regular schedule
- Wizard-based creation

---

## 📖 API Reference

Quick reference for all API endpoints:

**[docs/reference/QUICK_REFERENCE.md](docs/reference/QUICK_REFERENCE.md)** - Complete API endpoint list with examples

**Endpoint Categories**:
- Schedule operations (get, save, add, delete targets)
- Macro system (list, get, save, activate, stop, delete)
- Time synchronization (manual time setting)
- Test mode (manual channel control)
- Diagnostics (debug info, reboot)

**Example Usage**:
```bash
# Get device status
curl http://192.168.103.8/api/status

# Activate a macro
curl -X POST http://192.168.103.8/api/macro/activate \
  -H "Content-Type: application/json" \
  -d '{"id":"macro_001","duration":7200}'

# Set time manually
curl -X POST http://192.168.103.8/api/time/set \
  -H "Content-Type: application/json" \
  -d '{"hour":14,"minute":30,"second":0}'
```

---

## 📁 Archived Documents

Historical implementation tracking (for reference only):

**Location**: `.github/archives/`

**Contents**:
- IMPLEMENTATION_COMPLETE.md - Hybrid time sync completion summary
- IMPLEMENTATION_SUMMARY.md - Macro fix implementation
- MACRO_FIX_TESTING.md - Macro fix testing guide
- OPTIMIZATIONS_APPLIED.md - Memory optimization summary
- step-05-summary.md - Implementation step summary
- time-sync-plan.md - Time sync planning document (completed)
- time-sync-fixes.md - Time sync fixes log
- SESSION_SUMMARY_2025-12-30.md - Development session summary

**Note**: These documents are archived because the features are complete. They remain for historical reference but are not part of current documentation.

---

## 🗺️ Documentation Map by Use Case

### "I want to build my own SBAquaControl"
1. [README.md](README.md) - Hardware list and setup
2. [CONTRIBUTING.md](CONTRIBUTING.md) - Build instructions
3. [docs/status/TESTING_GUIDE.md](docs/status/TESTING_GUIDE.md) - Validation

### "I want to use the web interface"
1. [PRODUCT.md](PRODUCT.md) - Feature overview
2. [docs/reference/QUICK_REFERENCE.md](docs/reference/QUICK_REFERENCE.md) - Quick commands
3. [README.md](README.md) - Access information

### "I want to develop new features"
1. [CONTRIBUTING.md](CONTRIBUTING.md) - Development setup
2. [ARCHITECTURE.md](ARCHITECTURE.md) - System internals
3. [docs/status/ROADMAP.md](docs/status/ROADMAP.md) - Planned features

### "I want to understand the macro system"
1. [PRODUCT.md](PRODUCT.md) - User perspective
2. [docs/design/MACRO_REFACTORING.md](docs/design/MACRO_REFACTORING.md) - Technical design
3. [ARCHITECTURE.md](ARCHITECTURE.md) - Implementation details

### "I want to troubleshoot issues"
1. [docs/reference/QUICK_REFERENCE.md](docs/reference/QUICK_REFERENCE.md) - Common issues
2. [docs/status/TESTING_GUIDE.md](docs/status/TESTING_GUIDE.md) - Diagnostic procedures
3. [CONTRIBUTING.md](CONTRIBUTING.md) - Debugging tips

---

## 📝 Document Maintenance

### When to Update Documentation

- **README.md**: When adding major features or changing installation process
- **PRODUCT.md**: When user-facing features change
- **ARCHITECTURE.md**: When system design changes (new components, patterns)
- **CONTRIBUTING.md**: When adding new coding standards or workflows
- **ROADMAP.md**: After completing phases or adjusting priorities
- **FIRMWARE_STATUS.md**: After significant feature implementations
- **TESTING_GUIDE.md**: When adding new test procedures

### Documentation Standards

1. **Keep it current**: Update docs when code changes
2. **Be concise**: Link to details rather than duplicating information
3. **Use examples**: Show real command examples and code snippets
4. **Mark status**: Use ✅ for completed, 🚀 for in-progress, ❌ for not implemented
5. **Version tag**: Include "Last Updated" dates and version numbers
6. **Cross-reference**: Link related documents for context

---

## 🆘 Quick Help

**Can't find what you're looking for?**

1. Check this index first
2. Use GitHub's search across all docs
3. Check [QUICK_REFERENCE.md](docs/reference/QUICK_REFERENCE.md) for commands
4. Review [ROADMAP.md](docs/status/ROADMAP.md) for planned features
5. Browse [.github/archives/](.github/archives/) for historical context

**Found outdated documentation?**

Please update it following the standards above, or open an issue describing what needs updating.

---

**Document Version**: 1.0  
**Maintained By**: SBAquaControl Development Team
