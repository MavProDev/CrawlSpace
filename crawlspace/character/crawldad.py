"""Crawldad pixel-art mascot renderer."""

import math
import time
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QCursor
from crawlspace.constants import C, EMOTION_STYLES

# 11 columns x 10 rows. 0=transparent, 1=body, 2=eye
CRAWLDAD = [
    [0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0],  # row 0: ears
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],  # row 1: head top
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],  # row 2: head
    [0, 1, 2, 2, 1, 1, 1, 2, 2, 1, 0],  # row 3: eyes top
    [0, 1, 2, 2, 1, 1, 1, 2, 2, 1, 0],  # row 4: eyes bottom
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],  # row 5: chest
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0],  # row 6: waist
    [0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0],  # row 7: legs
    [0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0],  # row 8: legs
    [0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0],  # row 9: feet
]


def draw_crawldad(painter: QPainter, x: float, y: float, ps: float,
                  bounce: float = 0, tint: QColor | None = None,
                  ex: float = 0, ey: float = 0,
                  emotion: str = "neutral",
                  eye_glow: bool = True, glow_phase: float = 0.0) -> None:
    """Draw the Crawldad character at position (x, y) with pixel size ps."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    style = EMOTION_STYLES.get(emotion, EMOTION_STYLES["neutral"])
    body = tint or style["tint"] or C["coral"]
    eye = QColor(35, 25, 22)

    if eye_glow:
        glow_intensity = 0.5 + 0.5 * math.sin(glow_phase * 1.8)
        eye = QColor(
            int(0 + 35 * (1 - glow_intensity)),
            int(200 + 55 * glow_intensity),
            int(40 + 25 * glow_intensity),
        )

    adj_bounce = bounce * style["bounce_mult"]
    tremble_x = (math.sin(time.time() * 47) * 0.3) if style["tremble"] else 0
    tremble_y = (math.cos(time.time() * 53) * 0.3) if style["tremble"] else 0

    for ri, row in enumerate(CRAWLDAD):
        for ci, cell in enumerate(row):
            if cell == 0:
                continue
            color = body if cell == 1 else eye
            px = x + ci * ps + tremble_x
            py = y + math.sin(adj_bounce) * 1.2 + ri * ps + tremble_y

            if ri >= 7:  # legs
                py += math.sin(adj_bounce * 0.5 + ci * 0.8) * 0.5
                py += style["leg_droop"]

            if cell == 2:  # eyes
                px += ex
                py += ey + style["eye_droop"]
                if eye_glow:
                    glow_a = int(40 + 30 * math.sin(glow_phase * 1.8))
                    glow_c = QColor(0, 255, 65, glow_a)
                    gs = ps * 2.2
                    painter.fillRect(
                        QRectF(px - ps * 0.6, py - ps * 0.6, gs, gs),
                        QBrush(glow_c),
                    )

            painter.fillRect(QRectF(px, py, ps + 0.5, ps + 0.5), QBrush(color))

    painter.restore()


def eye_shift(widget) -> tuple[float, float]:
    """Calculate eye offset toward cursor position."""
    cursor = QCursor.pos()
    center_x = widget.x() + widget.width() / 2
    center_y = widget.y() + widget.height() / 2
    dx = cursor.x() - center_x
    dy = cursor.y() - center_y
    distance = max(1, math.sqrt(dx * dx + dy * dy))
    return dx / distance * 1.2, dy / distance * 1.0
