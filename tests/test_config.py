"""Tests for crawlspace.config — ConfigManager and helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from crawlspace.constants import DEFAULT_CONFIG


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_manager(tmp_config_dir):
    """Return a fresh ConfigManager whose paths point to tmp_config_dir."""
    import crawlspace.config as cfg

    # ConfigManager.__init__ uses the module-level CONFIG_DIR / CONFIG_FILE,
    # which are already patched by the tmp_config_dir fixture.
    return cfg.ConfigManager()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_default_config_has_all_keys(qapp, tmp_config_dir):
    """A freshly created ConfigManager must contain every DEFAULT_CONFIG key."""
    manager = _make_manager(tmp_config_dir)
    for key in DEFAULT_CONFIG:
        assert manager.get(key) == DEFAULT_CONFIG[key], (
            f"Key '{key}' mismatch: got {manager.get(key)!r}, "
            f"expected {DEFAULT_CONFIG[key]!r}"
        )


def test_atomic_write_creates_file(qapp, tmp_config_dir):
    """_atomic_write must create the target file with correct JSON content."""
    from crawlspace.config import _atomic_write

    target = tmp_config_dir / "test_output.json"
    data = {"hello": "world", "answer": 42}
    _atomic_write(target, data)

    assert target.exists(), "Target file was not created"
    with open(target, encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert loaded == data


def test_config_get_set_roundtrip(qapp, tmp_config_dir):
    """Values written via set() must persist across ConfigManager instances."""
    manager = _make_manager(tmp_config_dir)
    manager.set("color_theme", "blue")
    manager.set("scan_interval_seconds", 99)

    # Flush ensures the debounce cannot swallow the write
    manager.flush()

    # Create a second manager backed by the same file
    manager2 = _make_manager(tmp_config_dir)
    assert manager2.get("color_theme") == "blue"
    assert manager2.get("scan_interval_seconds") == 99


def test_apply_theme_changes_palette(qapp, tmp_config_dir):
    """apply_theme('blue') must update C['coral'] to the blue accent colour."""
    from crawlspace.config import apply_theme
    from crawlspace.constants import C, THEMES

    # Record original coral value
    original_coral = C["coral"]

    apply_theme("blue")

    expected_r, expected_g, expected_b = THEMES["blue"]["accent"]
    actual = C["coral"]

    assert actual.red() == expected_r, f"red mismatch: {actual.red()} != {expected_r}"
    assert actual.green() == expected_g
    assert actual.blue() == expected_b

    # Restore so other tests aren't affected
    apply_theme("coral")


def test_config_get_default(qapp, tmp_config_dir):
    """get() with an unknown key must return the provided default."""
    manager = _make_manager(tmp_config_dir)
    sentinel = object()
    result = manager.get("__nonexistent_key__", sentinel)
    assert result is sentinel


def test_config_set_many(qapp, tmp_config_dir):
    """set_many() must apply all updates atomically and persist them."""
    manager = _make_manager(tmp_config_dir)
    updates = {
        "color_theme": "purple",
        "confirm_kill": False,
        "zombie_threshold_hours": 8,
    }
    manager.set_many(updates)
    manager.flush()

    manager2 = _make_manager(tmp_config_dir)
    for key, value in updates.items():
        assert manager2.get(key) == value, (
            f"Key '{key}': expected {value!r}, got {manager2.get(key)!r}"
        )
