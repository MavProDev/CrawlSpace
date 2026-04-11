"""CrawlSpace — color utility functions for the UI layer."""

import math
from PyQt6.QtGui import QColor
from crawlspace.constants import C, THEMES


def lerp_color(c1: QColor, c2: QColor, f: float) -> QColor:
    """Linearly interpolate between two QColors. f clamped to [0, 1]."""
    f = max(0.0, min(1.0, f))
    return QColor(
        int(c1.red() + (c2.red() - c1.red()) * f),
        int(c1.green() + (c2.green() - c1.green()) * f),
        int(c1.blue() + (c2.blue() - c1.blue()) * f),
    )


def with_alpha(color: QColor, alpha: int) -> QColor:
    """Return a copy of QColor with the given alpha (clamped 0-255)."""
    return QColor(color.red(), color.green(), color.blue(), max(0, min(255, alpha)))


def apply_theme(name: str) -> None:
    """Apply a color theme by mutating the C palette dict."""
    t = THEMES.get(name, THEMES["coral"])
    C["coral"] = QColor(*t["accent"])
    C["coral_light"] = QColor(*t["accent_light"])


def body_pulse_color(pulse: float) -> QColor:
    """Compute the warm coral pulse for Crawldad's body."""
    q = 0.5 + 0.5 * math.sin(pulse * 2)
    return QColor(
        int(217 + 23 * q),
        int(119 + 66 * q),
        int(87 - 32 * q),
    )


def uptime_color(seconds: float) -> QColor:
    """Color-code by process age: normal < 1h, amber 1-4h, red 4h+."""
    hours = seconds / 3600
    if hours < 1:
        return C["text_md"]
    elif hours < 4:
        return C["amber"]
    else:
        return C["red"]


def badge_color(count: int) -> QColor:
    """Color for process count badge."""
    if count <= 2:
        return C["green"]
    elif count <= 5:
        return C["amber"]
    elif count <= 9:
        return C["coral"]
    else:
        return C["red"]
