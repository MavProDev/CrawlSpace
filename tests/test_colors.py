"""Tests for crawlspace.utils.colors — color utility functions."""

from __future__ import annotations

import pytest
from PyQt6.QtGui import QColor


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_lerp_color_midpoint(qapp):
    """black(0,0,0) to white(255,255,255) at f=0.5 -> ~gray(127,127,127)."""
    from crawlspace.utils.colors import lerp_color

    black = QColor(0, 0, 0)
    white = QColor(255, 255, 255)
    mid = lerp_color(black, white, 0.5)

    assert isinstance(mid, QColor)
    assert mid.red() == 127
    assert mid.green() == 127
    assert mid.blue() == 127


def test_lerp_color_clamping(qapp):
    """f=-1 returns c1, f=2 returns c2."""
    from crawlspace.utils.colors import lerp_color

    red = QColor(255, 0, 0)
    blue = QColor(0, 0, 255)

    # f < 0 should clamp to f=0 (return c1 = red)
    result_low = lerp_color(red, blue, -1)
    assert result_low.red() == 255
    assert result_low.blue() == 0

    # f > 1 should clamp to f=1 (return c2 = blue)
    result_high = lerp_color(red, blue, 2)
    assert result_high.red() == 0
    assert result_high.blue() == 255


def test_with_alpha(qapp):
    """verify alpha is set, RGB unchanged."""
    from crawlspace.utils.colors import with_alpha

    original = QColor(100, 150, 200)
    result = with_alpha(original, 128)

    assert isinstance(result, QColor)
    assert result.red() == 100
    assert result.green() == 150
    assert result.blue() == 200
    assert result.alpha() == 128


def test_with_alpha_clamping(qapp):
    """alpha=-10 clamps to 0, alpha=300 clamps to 255."""
    from crawlspace.utils.colors import with_alpha

    color = QColor(50, 100, 150)

    low = with_alpha(color, -10)
    assert low.alpha() == 0

    high = with_alpha(color, 300)
    assert high.alpha() == 255


def test_body_pulse_returns_qcolor(qapp):
    """verify return type is QColor and values are in valid range."""
    from crawlspace.utils.colors import body_pulse_color

    import math
    for pulse in [0.0, 1.0, math.pi, 2 * math.pi]:
        result = body_pulse_color(pulse)
        assert isinstance(result, QColor), f"Expected QColor, got {type(result)}"
        assert 0 <= result.red() <= 255
        assert 0 <= result.green() <= 255
        assert 0 <= result.blue() <= 255


def test_uptime_color_thresholds(qapp):
    """<1h returns text_md, 2h returns amber, 5h returns red."""
    from crawlspace.utils.colors import uptime_color
    from crawlspace.constants import C

    # Less than 1 hour (3599 seconds)
    result_short = uptime_color(3599)
    assert result_short == C["text_md"], (
        f"Expected text_md for <1h, got {result_short.name()}"
    )

    # 2 hours (between 1h and 4h)
    result_medium = uptime_color(2 * 3600)
    assert result_medium == C["amber"], (
        f"Expected amber for 2h, got {result_medium.name()}"
    )

    # 5 hours (4h+)
    result_long = uptime_color(5 * 3600)
    assert result_long == C["red"], (
        f"Expected red for 5h, got {result_long.name()}"
    )
