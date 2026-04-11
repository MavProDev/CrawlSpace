"""CrawlSpace — toast notification system with stacking and rate limiting."""

import time
import math
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QApplication
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QRectF
from PyQt6.QtGui import (
    QPainter, QFont, QColor, QBrush, QPen, QPainterPath,
)

from crawlspace.constants import C, FONTS, make_font
from crawlspace.character.crawldad import draw_crawldad
from crawlspace.character.animation import AnimationController


# Toast type → (border color key, emotion, title prefix)
_TOAST_TYPES = {
    "new_process":    ("coral",  "alert",   "New Process"),
    "process_died":   ("green",  "neutral", "Process Died"),
    "kill_success":   ("green",  "happy",   "Kill Confirmed"),
    "kill_failed":    ("red",    "sob",     "Kill Failed"),
    "high_resource":  ("amber",  "neutral", "High Resource"),
    "startup":        ("coral",  "neutral", "Startup"),
    "zombie":         ("red",    "sad",     "Zombie Alert"),
    "port_conflict":  ("amber",  "alert",   "Port Conflict"),
}

_TOAST_WIDTH = 320
_TOAST_HEIGHT = 80
_TOAST_GAP = 8
_TOAST_MARGIN = 16
_SLIDE_DURATION = 300
_AUTO_DISMISS_MS = 8000


class Toast(QWidget):
    """A single toast notification widget with Craw and slide animation."""

    clicked = pyqtSignal()
    dismissed = pyqtSignal(object)  # self

    def __init__(self, toast_type: str, message: str, anim: AnimationController,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._toast_type = toast_type
        self._message = message
        self._anim = anim
        self._type_info = _TOAST_TYPES.get(toast_type, _TOAST_TYPES["new_process"])
        self._border_color = C[self._type_info[0]]
        self._emotion = self._type_info[1]
        self._title = self._type_info[2]
        self._opacity = 1.0
        self._fading = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(_TOAST_WIDTH, _TOAST_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Auto-dismiss timer
        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.setInterval(_AUTO_DISMISS_MS)
        self._dismiss_timer.timeout.connect(self._start_fade)

        # Fade timer
        self._fade_timer = QTimer(self)
        self._fade_timer.setInterval(33)
        self._fade_timer.timeout.connect(self._fade_tick)

        # Animation refresh
        anim.frame_tick.connect(self.update)

    def show_toast(self) -> None:
        """Show the toast and start auto-dismiss countdown."""
        self.show()
        self._dismiss_timer.start()

    def paintEvent(self, event) -> None:
        """Render toast with Craw, border, title, message."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setOpacity(self._opacity)

        # Background
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 8, 8)
        p.setPen(QPen(self._border_color, 2))
        p.setBrush(QBrush(C["notch_bg"]))
        p.drawPath(path)

        # Left accent bar
        accent_path = QPainterPath()
        accent_path.addRoundedRect(QRectF(0, 0, 4, self.height()), 2, 2)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self._border_color))
        p.drawPath(accent_path)

        # Craw at ps=2.8
        draw_crawldad(
            p, 14, 14, 2.8,
            bounce=self._anim.bounce,
            emotion=self._emotion,
            eye_glow=True,
            glow_phase=self._anim.pulse,
        )

        # Title
        p.setPen(QPen(self._border_color))
        p.setFont(make_font(FONTS["label_bold"]))
        p.drawText(58, 22, self._title)

        # Message
        p.setPen(QPen(C["text_md"]))
        p.setFont(make_font(FONTS["caption"]))
        # Word-wrap manually within bounds
        rect = QRectF(58, 28, _TOAST_WIDTH - 70, _TOAST_HEIGHT - 34)
        p.drawText(rect, Qt.TextFlag.TextWordWrap, self._message)

        p.end()

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()
        self._dismiss()

    def _start_fade(self) -> None:
        self._fading = True
        self._fade_timer.start()

    def _fade_tick(self) -> None:
        self._opacity -= 0.05
        if self._opacity <= 0:
            self._fade_timer.stop()
            self._dismiss()
        else:
            self.update()

    def _dismiss(self) -> None:
        self._dismiss_timer.stop()
        self._fade_timer.stop()
        self.hide()
        self.dismissed.emit(self)


class ToastManager:
    """Manages toast creation, stacking, and rate limiting."""

    def __init__(self, anim: AnimationController) -> None:
        self._anim = anim
        self._toasts: list[Toast] = []
        self._last_toast_time: float = 0.0
        self._rate_limit_seconds: float = 5.0
        self._pending: list[tuple[str, str]] = []
        self._enabled: bool = True
        self._dnd: bool = False
        self._type_toggles: dict[str, bool] = {}
        self._on_click_callback = None

    def set_enabled(self, enabled: bool) -> None:
        """Master toggle for notifications."""
        self._enabled = enabled

    def set_dnd(self, dnd: bool) -> None:
        """Do-not-disturb mode."""
        self._dnd = dnd

    def set_type_enabled(self, toast_type: str, enabled: bool) -> None:
        """Per-type toggle."""
        self._type_toggles[toast_type] = enabled

    def set_on_click(self, callback) -> None:
        """Set callback when any toast is clicked."""
        self._on_click_callback = callback

    def show_toast(self, toast_type: str, message: str) -> None:
        """Show a toast notification (rate-limited)."""
        if not self._enabled or self._dnd:
            return
        if not self._type_toggles.get(toast_type, True):
            return

        now = time.time()
        if now - self._last_toast_time < self._rate_limit_seconds:
            # Batch pending notifications
            self._pending.append((toast_type, message))
            return

        self._last_toast_time = now
        self._create_toast(toast_type, message)

    def _create_toast(self, toast_type: str, message: str) -> None:
        toast = Toast(toast_type, message, self._anim)
        toast.dismissed.connect(self._on_toast_dismissed)
        if self._on_click_callback:
            toast.clicked.connect(self._on_click_callback)
        self._toasts.append(toast)
        self._reposition()
        toast.show_toast()

    def _on_toast_dismissed(self, toast: Toast) -> None:
        if toast in self._toasts:
            self._toasts.remove(toast)
            toast.deleteLater()
        self._reposition()

        # Show pending toast if any
        if self._pending:
            toast_type, message = self._pending.pop(0)
            # If multiple pending, batch them
            if self._pending:
                batch_count = len(self._pending) + 1
                message = f"{message} (+{batch_count - 1} more)"
                self._pending.clear()
            self._create_toast(toast_type, message)

    def _reposition(self) -> None:
        """Stack toasts from bottom-right of primary screen."""
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        x = geo.right() - _TOAST_WIDTH - _TOAST_MARGIN
        y = geo.bottom() - _TOAST_MARGIN

        for toast in reversed(self._toasts):
            y -= _TOAST_HEIGHT
            toast.move(x, y)
            y -= _TOAST_GAP
