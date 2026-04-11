"""
Tests for crawlspace/constants.py
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load():
    """Import constants — deferred so failures give clear messages."""
    from crawlspace import constants
    return constants


# ---------------------------------------------------------------------------
# Color dict C
# ---------------------------------------------------------------------------

REQUIRED_COLOR_KEYS = [
    "notch_bg", "notch_border", "card_bg", "divider",
    "text_hi", "text_md", "text_lo",
    "coral", "coral_light", "green", "amber", "red",
    "row_alt", "row_hover",
]


def test_c_has_all_required_keys():
    c = _load().C
    for key in REQUIRED_COLOR_KEYS:
        assert key in c, f"Missing color key: {key!r}"


def test_c_has_exactly_14_keys():
    c = _load().C
    assert len(c) == 14, f"Expected 14 color keys, got {len(c)}"


def test_c_values_are_qcolor():
    from PyQt6.QtGui import QColor
    c = _load().C
    for key, val in c.items():
        assert isinstance(val, QColor), f"C[{key!r}] is not a QColor"


# ---------------------------------------------------------------------------
# THEMES
# ---------------------------------------------------------------------------

EXPECTED_THEMES = {"coral", "blue", "green", "purple", "cyan", "amber", "pink", "red"}


def test_themes_has_8_entries():
    themes = _load().THEMES
    assert len(themes) == 8, f"Expected 8 themes, got {len(themes)}"


def test_themes_has_correct_names():
    themes = _load().THEMES
    assert set(themes.keys()) == EXPECTED_THEMES


def test_themes_each_has_accent_and_accent_light():
    themes = _load().THEMES
    for name, theme in themes.items():
        assert "accent" in theme, f"Theme {name!r} missing 'accent'"
        assert "accent_light" in theme, f"Theme {name!r} missing 'accent_light'"


def test_themes_accent_values_are_3_int_tuples():
    themes = _load().THEMES
    for name, theme in themes.items():
        for key in ("accent", "accent_light"):
            val = theme[key]
            assert isinstance(val, tuple) and len(val) == 3, (
                f"Theme {name!r}[{key!r}] should be a 3-tuple"
            )
            for component in val:
                assert isinstance(component, int), (
                    f"Theme {name!r}[{key!r}] component {component!r} is not int"
                )


# ---------------------------------------------------------------------------
# PROCESS_PATTERNS
# ---------------------------------------------------------------------------

REQUIRED_CATEGORIES = {"python", "node", "devtool", "infrastructure", "other"}


def test_process_patterns_has_5_categories():
    pp = _load().PROCESS_PATTERNS
    assert len(pp) == 5, f"Expected 5 categories, got {len(pp)}"


def test_process_patterns_has_correct_categories():
    pp = _load().PROCESS_PATTERNS
    assert set(pp.keys()) == REQUIRED_CATEGORIES


def test_process_patterns_values_are_non_empty_lists():
    pp = _load().PROCESS_PATTERNS
    for cat, patterns in pp.items():
        assert isinstance(patterns, list) and len(patterns) > 0, (
            f"Category {cat!r} should be a non-empty list"
        )


# ---------------------------------------------------------------------------
# DEFAULT_CONFIG
# ---------------------------------------------------------------------------

REQUIRED_CONFIG_KEYS = [
    "start_with_windows", "start_minimized",
    "color_theme",
    "scan_interval_seconds", "kill_timeout_seconds", "confirm_kill",
    "toast_enabled", "toast_duration_seconds", "sound_enabled",
    "dnd_mode",
    "overlay_enabled", "overlay_edge", "overlay_opacity",
    "window_x", "window_y", "window_w", "window_h",
    "view_mode", "sort_column", "sort_ascending",
    "whitelist_paths",
    "zombie_threshold_hours",
    "first_run_done",
    "notify_new_process", "notify_process_died",
    "notify_kill_success", "notify_kill_failed",
    "notify_zombie", "notify_port_conflict",
]


def test_default_config_has_all_required_keys():
    cfg = _load().DEFAULT_CONFIG
    for key in REQUIRED_CONFIG_KEYS:
        assert key in cfg, f"DEFAULT_CONFIG missing key: {key!r}"


def test_default_config_whitelist_paths_is_list():
    cfg = _load().DEFAULT_CONFIG
    assert isinstance(cfg["whitelist_paths"], list)


def test_default_config_view_mode_default():
    cfg = _load().DEFAULT_CONFIG
    assert cfg["view_mode"] == "flat"


def test_default_config_sort_column_default():
    cfg = _load().DEFAULT_CONFIG
    assert cfg["sort_column"] == "name"


# ---------------------------------------------------------------------------
# Animation constants are positive numbers
# ---------------------------------------------------------------------------

ANIMATION_CONSTANTS = [
    "BOUNCE_INCREMENT", "PULSE_INCREMENT", "PULSE_INCREMENT_BORED",
    "BOUNCE_AMPLITUDE", "LEG_WOBBLE_AMPLITUDE", "LEG_PHASE_OFFSET",
    "EYE_GLOW_FREQUENCY", "EYE_HALO_SIZE_MULT", "EYE_HALO_OFFSET_MULT",
    "EYE_SHIFT_MAX_X", "EYE_SHIFT_MAX_Y",
    "TREMBLE_FREQ_X", "TREMBLE_FREQ_Y", "TREMBLE_AMPLITUDE",
    "TICK_ACTIVE", "TICK_IDLE", "TICK_TOAST",
    "BORED_TIMEOUT_SECONDS", "DIM_OPACITY",
]


def test_animation_constants_are_positive():
    mod = _load()
    for name in ANIMATION_CONSTANTS:
        val = getattr(mod, name)
        assert isinstance(val, (int, float)), f"{name} is not a number"
        assert val > 0, f"{name} should be positive, got {val}"


# ---------------------------------------------------------------------------
# EMOTION_STYLES
# ---------------------------------------------------------------------------

REQUIRED_EMOTIONS = {"neutral", "happy", "sad", "sob", "alert"}
REQUIRED_EMOTION_KEYS = {"bounce_mult", "tint", "leg_droop", "tremble", "eye_droop"}


def test_emotion_styles_has_5_entries():
    es = _load().EMOTION_STYLES
    assert len(es) == 5, f"Expected 5 emotions, got {len(es)}"


def test_emotion_styles_has_correct_names():
    es = _load().EMOTION_STYLES
    assert set(es.keys()) == REQUIRED_EMOTIONS


def test_emotion_styles_each_has_required_keys():
    es = _load().EMOTION_STYLES
    for name, style in es.items():
        for key in REQUIRED_EMOTION_KEYS:
            assert key in style, f"EMOTION_STYLES[{name!r}] missing key {key!r}"


# ---------------------------------------------------------------------------
# SPINNER_FRAMES
# ---------------------------------------------------------------------------

def test_spinner_frames_is_non_empty_list():
    sf = _load().SPINNER_FRAMES
    assert isinstance(sf, list) and len(sf) > 0


# ---------------------------------------------------------------------------
# COMMON_PORTS
# ---------------------------------------------------------------------------

def test_common_ports_is_list_of_ints():
    ports = _load().COMMON_PORTS
    assert isinstance(ports, list) and len(ports) > 0
    for p in ports:
        assert isinstance(p, int), f"Port {p!r} is not int"


def test_common_ports_contains_expected_values():
    ports = _load().COMMON_PORTS
    for expected in [3000, 5000, 8000, 8080]:
        assert expected in ports, f"Expected port {expected} in COMMON_PORTS"
