"""Regression guards for issues #36 and #37 (fast, always run).

#36: `initEventLog()` is CALLED, not merely defined. A hand-resolved rebase
deleted the call (4ddd3d5, the issue #8 rebase) while leaving the definition,
so the SD event log was dead on master with no compile error and no failing
test. A grep for the call site catches that in one line.

#37: `/api/debug` must not append a key AFTER the root object's closing
brace. That produced two concatenated fragments, so the whole response was
unparseable - and it is what hid #36 for weeks. A structural check on C++
source is deliberately NOT attempted here: recovering the exact emitted shape
from interleaved sendContent()/sprintf() calls and loop bodies is unreliable
(a per-iteration closer in a loop cannot be folded into a linear brace
count, and braces inside string literals are not structure). Instead this
pins the two source lines that caused it, which is cheap and exact, and the
authoritative check - `json.loads` on the bytes from the real device - is
documented in the issue and belongs to the hardware verification pass.

Fast: pure file parsing, no toolchain, no server. Always run.
"""

import os
import re

import pytest
from conftest import REPO

AQUA = os.path.join(REPO, "src", "AquaControl.cpp")
FIRMWARE = os.path.join(REPO, "src", "Webserver.cpp")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def test_event_log_is_initialised():
    """initEventLog() must be CALLED (issue #36).

    Exactly one call site: the definition alone means the log never starts.
    """
    calls = len(re.findall(r"^\s*initEventLog\(\)\s*;", _read(AQUA), re.M))
    assert calls == 1, (
        f"expected exactly 1 initEventLog() call in {os.path.relpath(AQUA, REPO)}, "
        f"found {calls}. With zero calls the SD event log never starts, "
        f"_sdLogOk stays false, every logEvent() is a no-op, and /api/debug "
        f"reports a permanently dead log (issue #36)."
    )


def test_event_log_starts_after_sd_begin():
    """The call must sit after SD.begin() and before the network init.

    Ordering is the whole point: the boot line and reset reason must land in
    the log before any network activity, which is what initEventLog()'s own
    comment specifies.
    """
    src = _read(AQUA)
    # Anchor inside init()'s body, not on the declarations: `SD.begin(...)`
    # and `initESP8266NetworkConnection()` also appear as function names
    # earlier in the file, and index() would find those first.
    init = src.index("void AquaControl::init(")
    begin = src.index("if (!SD.begin(SD_CS))", init)
    call = src.index("initEventLog();", init)
    net = src.index("initESP8266NetworkConnection()", init)
    assert begin < call < net, (
        "initEventLog() must be called after SD.begin() succeeds and before "
        "initESP8266NetworkConnection(), so the boot line and reset reason are "
        "recorded before any network activity (issue #36)"
    )


def test_debug_response_has_no_key_after_root_close():
    """No top-level key may be emitted after /api/debug's root object closes.

    Issue #37: `]}` (closing the channels array AND the root) was followed by
    `,"log":{`, so the response was two concatenated fragments and no JSON
    parser could read it. Both facts are pinned here.
    """
    src = _read(FIRMWARE)
    start = src.index("void handleApiDebug()")
    nxt = src.find("\nvoid ", start + 10)
    body = src[start: nxt if nxt != -1 else len(src)]

    # The channels array must be closed on its own, leaving the root open.
    assert '_Server.sendContent("]}"); // Close channels array AND main JSON object' not in body, (
        "handleApiDebug still closes the root object right after the channels "
        "array (issue #37). Close the array only - `sendContent(\"]\")` - and "
        "close the root object at the very end of the handler."
    )
    assert re.search(r'//\s*Close channels array AND main JSON object', body) is None, (
        "the stale '// Close channels array AND main JSON object' comment is "
        "still present (issue #37)"
    )

    # The log object is appended to a still-open root, so the root must be
    # closed by a fragment emitted AFTER the log object - and that closer must
    # be the last sendContent() in the handler.
    log_key = body.index('sendContent(",\\"log\\":{')
    calls = list(
        re.finditer(r'_Server\.sendContent\(\s*(.+?)\s*\);', body[log_key:], re.S)
    )
    assert calls, "no sendContent() found after the log key (issue #37)"
    last = calls[-1].group(1)
    assert last.strip() == '"}"', (
        f"the LAST fragment of handleApiDebug must close the root object "
        f'(sendContent("}}")), found {last[:60]!r}. Issue #37 emitted the "log" '
        f"key after the root's closing brace, so the response was two "
        f"concatenated documents and no JSON parser could read it."
    )
