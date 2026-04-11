"""Particle effects: hearts, rain, yawn for Crawldad emotions."""

import math
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QPainterPath
from crawlspace.constants import C


def draw_hearts(painter: QPainter, center_x: float, top_y: float,
                pulse: float, count: int = 3) -> None:
    """Draw floating heart particles (happy emotion)."""
    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    for i in range(count):
        seed = pulse * 0.8 + i * 2.1
        phase = (seed % 3.0) / 3.0
        px = center_x + math.sin(seed * 1.7 + i) * 6
        py = top_y - phase * 18 - 2
        alpha = int(180 * (1 - phase))
        sz = 1.5 + (1 - phase) * 0.5
        color = QColor(235, 100, 120, alpha)
        painter.setBrush(QBrush(color))
        # Left bump
        painter.drawEllipse(QRectF(px - sz, py - sz * 0.5, sz, sz))
        # Right bump
        painter.drawEllipse(QRectF(px, py - sz * 0.5, sz, sz))
        # Bottom point
        tri = QPainterPath()
        tri.moveTo(px - sz, py)
        tri.lineTo(px + sz, py)
        tri.lineTo(px, py + sz)
        tri.closeSubpath()
        painter.drawPath(tri)
    painter.restore()


def draw_rain(painter: QPainter, center_x: float, top_y: float,
              pulse: float, count: int = 3) -> None:
    """Draw falling rain drops (sad/sob emotion)."""
    painter.save()
    for i in range(count):
        seed = pulse * 0.8 + i * 2.1
        phase = (seed % 3.0) / 3.0
        px = center_x + math.sin(seed * 1.7 + i) * 6
        py = top_y + phase * 14 + 2
        alpha = int(140 * (1 - phase))
        color = QColor(120, 160, 220, alpha)
        painter.setPen(QPen(color, 1.2))
        painter.drawLine(int(px), int(py), int(px), int(py + 3))
    painter.restore()


def draw_yawn(painter: QPainter, center_x: float, top_y: float,
              pulse: float) -> None:
    """Draw a small yawn circle floating upward (bored state)."""
    painter.save()
    phase = (pulse % 5.0) / 5.0
    if phase < 0.6:
        px = center_x + math.sin(pulse * 0.5) * 3
        py = top_y - phase * 12
        alpha = int(120 * (1 - phase / 0.6))
        sz = 2.0 + phase * 1.5
        color = QColor(C["text_lo"].red(), C["text_lo"].green(),
                       C["text_lo"].blue(), alpha)
        painter.setPen(QPen(color, 0.8))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(px - sz / 2, py - sz / 2, sz, sz))
    painter.restore()
