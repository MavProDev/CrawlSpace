"""CrawlSpace — edge-docked notch widget. Clean and fast."""

from PyQt6.QtWidgets import QWidget, QApplication, QMenu
from PyQt6.QtCore import Qt, QPoint, QRectF
from PyQt6.QtGui import (
    QPainter, QFont, QColor, QBrush, QPen, QPainterPath,
)

from crawlspace.constants import C, FONTS, make_font
from crawlspace.character.crawldad import draw_crawldad, eye_shift
from crawlspace.character.animation import AnimationController
from crawlspace.character.emotions import EmotionStateMachine
from crawlspace.utils.colors import badge_color
from crawlspace.config import ConfigManager

# Collapsed dimensions per orientation
_HW, _HH = 160, 32   # horizontal (top/bottom)
_VW, _VH = 32, 120    # vertical (left/right)
_PS = 2.2              # Craw pixel size
_GRID_W, _GRID_H = 11, 10


class Notch(QWidget):
    """Compact edge-docked notch with Craw + process count badge."""

    def __init__(self, anim: AnimationController, emotions: EmotionStateMachine,
                 config: ConfigManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._anim = anim
        self._emotions = emotions
        self._config = config
        self._count = 0
        self._total_mb = 0.0
        self._edge = config.get("overlay_edge", "top")
        self._ori = "vertical" if self._edge in ("left", "right") else "horizontal"
        self._on_click = None

        # Drag state
        self._dragging = False
        self._drag_off = QPoint()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._apply_size()
        # Only repaint when visible — avoid wasted cycles
        anim.frame_tick.connect(self._tick)

        # Restore position
        lx = config.get("overlay_x", -1)
        ly = config.get("overlay_y", -1)
        if lx >= 0 and ly >= 0:
            self.move(lx, ly)
        else:
            self._snap()

    # ── Public ───────────────────────────────────────────────

    def set_on_click(self, callback) -> None:
        """Set callback for left-click (opens main window)."""
        self._on_click = callback

    def update_data(self, count: int, total_mb: float) -> None:
        """Update process count and memory."""
        self._count = count
        self._total_mb = total_mb

    def _tick(self) -> None:
        """Animation frame — only repaint if visible."""
        if self.isVisible():
            self.update()

    def show_notch(self) -> None:
        """Show the notch."""
        self.show()

    def hide_notch(self) -> None:
        """Hide the notch."""
        self.hide()

    # ── Paint ────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        e = self._edge

        # Edge-aware rounded corners: flat on docked edge, round on others
        r = 8
        s = 1  # flat corner
        tl = s if e in ("top", "left") else r
        tr = s if e in ("top", "right") else r
        br = s if e in ("bottom", "right") else r
        bl = s if e in ("bottom", "left") else r

        path = QPainterPath()
        path.moveTo(tl, 0)
        path.lineTo(w - tr, 0)
        if tr > 1:
            path.arcTo(w - 2 * tr, 0, 2 * tr, 2 * tr, 90, -90)
        else:
            path.lineTo(w, 0)
        path.lineTo(w, h - br)
        if br > 1:
            path.arcTo(w - 2 * br, h - 2 * br, 2 * br, 2 * br, 0, -90)
        else:
            path.lineTo(w, h)
        path.lineTo(bl, h)
        if bl > 1:
            path.arcTo(0, h - 2 * bl, 2 * bl, 2 * bl, 270, -90)
        else:
            path.lineTo(0, h)
        path.lineTo(0, tl)
        if tl > 1:
            path.arcTo(0, 0, 2 * tl, 2 * tl, 180, -90)
        else:
            path.lineTo(0, 0)
        path.closeSubpath()

        # Background
        bg = QColor(C["notch_bg"].red(), C["notch_bg"].green(), C["notch_bg"].blue(), 240)
        p.setPen(QPen(C["divider"], 1))
        p.setBrush(QBrush(bg))
        p.drawPath(path)

        # Accent line on docked edge
        p.setPen(QPen(C["coral"], 2))
        if e == "top":
            p.drawLine(12, 1, w - 12, 1)
        elif e == "bottom":
            p.drawLine(12, h - 1, w - 12, h - 1)
        elif e == "left":
            p.drawLine(1, 12, 1, h - 12)
        elif e == "right":
            p.drawLine(w - 1, 12, w - 1, h - 12)

        # Craw
        ex, ey = eye_shift(self)
        if self._ori == "horizontal":
            cx = 6
            cy = (h - _GRID_H * _PS) / 2
        else:
            cx = (w - _GRID_W * _PS) / 2
            cy = 6

        draw_crawldad(p, cx, cy, _PS,
                      bounce=self._anim.bounce,
                      ex=ex, ey=ey,
                      emotion=self._emotions.current,
                      eye_glow=True,
                      glow_phase=self._anim.pulse)

        # Badge
        if self._count > 0:
            bc = badge_color(self._count)
            bsz = 14
            if self._ori == "horizontal":
                bx = 6 + _GRID_W * _PS + 4
                by = (h - bsz) / 2
            else:
                bx = (w - bsz) / 2
                by = 6 + _GRID_H * _PS + 4

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(bc))
            p.drawEllipse(QRectF(bx, by, bsz, bsz))
            p.setPen(QPen(QColor(255, 255, 255)))
            p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            text = str(self._count) if self._count <= 99 else "99+"
            p.drawText(QRectF(bx, by, bsz, bsz), Qt.AlignmentFlag.AlignCenter, text)

        # Label (horizontal only)
        if self._ori == "horizontal" and self._count > 0:
            lx = 6 + _GRID_W * _PS + bsz + 8
            p.setPen(QPen(C["text_lo"]))
            p.setFont(make_font(FONTS["tiny"]))
            p.drawText(QRectF(lx, 0, w - lx - 4, h),
                       Qt.AlignmentFlag.AlignVCenter, f"{self._total_mb:.0f} MB")

        p.end()

    # ── Mouse ────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_off = event.pos()

    def mouseMoveEvent(self, event) -> None:
        if self._dragging:
            new_pos = self.pos() + event.pos() - self._drag_off
            # Clamp to screen
            scr = self._screen_geo()
            x = max(scr.x(), min(new_pos.x(), scr.right() - self.width()))
            y = max(scr.y(), min(new_pos.y(), scr.bottom() - self.height()))
            self.move(x, y)

    def mouseReleaseEvent(self, event) -> None:
        if self._dragging:
            self._dragging = False
            # Did we actually drag or just click?
            delta = (event.pos() - self._drag_off)
            if abs(delta.x()) < 4 and abs(delta.y()) < 4:
                # Click — open main window
                if self._on_click:
                    self._on_click()
                return
            # Drag — detect edge, snap, save
            self._det_edge()
            self._apply_size()
            self._snap()
            self._save_pos()

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu{background:#121216;color:#f0ece8;border:1px solid #2c2c34;"
            "padding:4px;font-size:12px;}"
            "QMenu::item:selected{background:#d97757;}"
        )
        if self._on_click:
            menu.addAction("Open CrawlSpace").triggered.connect(self._on_click)
        menu.addSeparator()
        menu.addAction("Hide Notch").triggered.connect(self.hide_notch)
        menu.exec(event.globalPos())

    # ── Edge logic ───────────────────────────────────────────

    def _det_edge(self) -> None:
        """Detect nearest screen edge."""
        scr = self._screen_geo()
        cx = self.x() + self.width() // 2
        cy = self.y() + self.height() // 2

        dists = {
            "top":    cy - scr.top(),
            "bottom": scr.bottom() - cy,
            "left":   cx - scr.left(),
            "right":  scr.right() - cx,
        }
        nearest = min(dists, key=dists.get)
        self._edge = nearest
        self._ori = "vertical" if nearest in ("left", "right") else "horizontal"

    def _apply_size(self) -> None:
        """Set widget size based on orientation."""
        if self._ori == "horizontal":
            self.setFixedSize(_HW, _HH)
        else:
            self.setFixedSize(_VW, _VH)

    def _snap(self) -> None:
        """Snap flush to the detected edge."""
        scr = self._screen_geo()
        x, y = self.x(), self.y()

        if self._edge == "top":
            y = scr.top()
        elif self._edge == "bottom":
            y = scr.bottom() - self.height()
        elif self._edge == "left":
            x = scr.left()
        elif self._edge == "right":
            x = scr.right() - self.width()

        # Keep within screen bounds on the other axis
        if self._ori == "horizontal":
            x = max(scr.left(), min(x, scr.right() - self.width()))
        else:
            y = max(scr.top(), min(y, scr.bottom() - self.height()))

        self.move(x, y)

    def _save_pos(self) -> None:
        """Persist position and edge."""
        self._config.set_many({
            "overlay_x": self.x(),
            "overlay_y": self.y(),
            "overlay_edge": self._edge,
        })

    @staticmethod
    def _screen_geo():
        """Get available geometry of primary screen."""
        screen = QApplication.primaryScreen()
        return screen.availableGeometry() if screen else QApplication.primaryScreen().geometry()
