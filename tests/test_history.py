"""Tests for crawlspace.history — EventHistory ring buffer."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_history(tmp_config_dir, max_events: int = 200):
    """Return a fresh EventHistory with paths redirected to tmp_config_dir."""
    from crawlspace.history import EventHistory
    return EventHistory(max_events=max_events)


def _add_event(history, event_type: str = "PROCESS_DETECTED",
               pid: int = 1000, name: str = "test.exe"):
    history.append(event_type, pid, name, category="python", detail="")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_append_and_get(tmp_config_dir):
    """add 3 events, get_events returns them newest first."""
    from crawlspace.history import EventHistory

    h = EventHistory()
    h.append("PROCESS_DETECTED", 101, "alpha.exe")
    h.append("PROCESS_DIED",     102, "beta.exe")
    h.append("PROCESS_KILLED",   103, "gamma.exe")

    events = h.get_events()
    assert len(events) == 3
    # Newest first — last appended should be index 0
    assert events[0]["name"] == "gamma.exe"
    assert events[1]["name"] == "beta.exe"
    assert events[2]["name"] == "alpha.exe"


def test_ring_buffer_max(tmp_config_dir):
    """Create with max_events=5, add 10, verify only 5 remain."""
    from crawlspace.history import EventHistory

    h = EventHistory(max_events=5)
    for i in range(10):
        h.append("PROCESS_DETECTED", 1000 + i, f"proc{i}.exe")

    assert h.count == 5
    events = h.get_events(limit=10)
    # Only the last 5 processes should remain (proc5 through proc9)
    names = {e["name"] for e in events}
    for i in range(5, 10):
        assert f"proc{i}.exe" in names
    for i in range(0, 5):
        assert f"proc{i}.exe" not in names


def test_filter_by_type(tmp_config_dir):
    """add mixed types, filter returns correct subset."""
    from crawlspace.history import EventHistory

    h = EventHistory()
    h.append("PROCESS_DETECTED", 100, "a.exe")
    h.append("PROCESS_KILLED",   101, "b.exe")
    h.append("PROCESS_DETECTED", 102, "c.exe")
    h.append("KILL_FAILED",      103, "d.exe")

    detected = h.get_events(filter_type="PROCESS_DETECTED")
    assert len(detected) == 2
    assert all(e["type"] == "PROCESS_DETECTED" for e in detected)

    killed = h.get_events(filter_type="PROCESS_KILLED")
    assert len(killed) == 1
    assert killed[0]["name"] == "b.exe"

    failed = h.get_events(filter_type="KILL_FAILED")
    assert len(failed) == 1


def test_prune_old_events(tmp_config_dir):
    """add events with old timestamps, prune removes them."""
    from crawlspace.history import EventHistory

    h = EventHistory()
    # Add a recent event
    h.append("PROCESS_DETECTED", 200, "recent.exe")
    # Manually inject an old event by patching its timestamp
    old_ts = (datetime.now() - timedelta(days=10)).isoformat()
    with h._lock:
        h._events.append({
            "timestamp": old_ts,
            "type": "PROCESS_DIED",
            "pid": 201,
            "name": "old.exe",
            "category": "",
            "detail": "",
        })

    assert h.count == 2
    removed = h.prune(days=7)
    assert removed == 1
    assert h.count == 1
    events = h.get_events()
    assert events[0]["name"] == "recent.exe"


def test_save_and_load(tmp_config_dir):
    """save to file, create new EventHistory, verify events loaded."""
    from crawlspace.history import EventHistory

    h = EventHistory()
    h.append("PROCESS_DETECTED", 300, "save_test.exe", category="node")
    h.append("PROCESS_KILLED",   301, "save_test2.exe")
    h.save()

    # Verify the file was actually written
    import crawlspace.config as cfg
    assert cfg.HISTORY_FILE.exists()

    # Create a second instance — it should load the persisted events
    h2 = EventHistory()
    assert h2.count == 2
    events = h2.get_events()
    names = {e["name"] for e in events}
    assert "save_test.exe" in names
    assert "save_test2.exe" in names


def test_count_property(tmp_config_dir):
    """verify count matches number of events."""
    from crawlspace.history import EventHistory

    h = EventHistory()
    assert h.count == 0

    for i in range(7):
        h.append("PROCESS_DETECTED", 400 + i, f"p{i}.exe")

    assert h.count == 7

    h.clear()
    assert h.count == 0
