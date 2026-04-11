"""CrawlSpace — first-run onboarding dialog with animated Crawldad mascot."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from crawlspace.constants import C, FONTS
from crawlspace.character.crawldad import draw_crawldad
from crawlspace.character.animation import AnimationController
from crawlspace.config import ConfigManager


# ---------------------------------------------------------------------------
# Animated Crawldad widget (renders inside the onboarding dialog)
# ---------------------------------------------------------------------------


class _CrawWidget(QWidget):
    """Small canvas that renders the animated Crawldad character."""

    def __init__(self, anim: AnimationController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._anim = anim
        self.setFixedSize(100, 60)
        self._anim.frame_tick.connect(self.update)

    def paintEvent(self, event) -> None:  # noqa: N802
        """Paint the Crawldad character centered in the widget."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        ps = 4.0
        grid_w = 11 * ps
        grid_h = 10 * ps
        cx = (self.width() - grid_w) / 2
        cy = (self.height() - grid_h) / 2

        draw_crawldad(
            painter,
            x=cx,
            y=cy,
            ps=ps,
            bounce=self._anim.bounce,
            emotion="happy",
            eye_glow=True,
            glow_phase=self._anim.pulse,
        )
        painter.end()


# ---------------------------------------------------------------------------
# Toggle-switch styled QCheckBox
# ---------------------------------------------------------------------------

_TOGGLE_TRACK_W = 40
_TOGGLE_TRACK_H = 20
_TOGGLE_KNOB_MARGIN = 2
_TOGGLE_KNOB_D = _TOGGLE_TRACK_H - 2 * _TOGGLE_KNOB_MARGIN


class _ToggleSwitch(QCheckBox):
    """QCheckBox drawn as an iOS-style toggle switch."""

    def __init__(self, label: str, parent: QWidget | None = None) -> None:
        super().__init__(label, parent)
        self.setMinimumHeight(_TOGGLE_TRACK_H + 8)

    def sizeHint(self) -> QSize:  # noqa: N802
        """Return preferred size."""
        text_w = self.fontMetrics().horizontalAdvance(self.text()) + 12
        return QSize(_TOGGLE_TRACK_W + text_w, _TOGGLE_TRACK_H + 8)

    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw the toggle track, knob, and label text."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # -- Track --
        track_y = (self.height() - _TOGGLE_TRACK_H) // 2
        track_path = QPainterPath()
        track_path.addRoundedRect(
            0, track_y, _TOGGLE_TRACK_W, _TOGGLE_TRACK_H,
            _TOGGLE_TRACK_H / 2, _TOGGLE_TRACK_H / 2,
        )

        if self.isChecked():
            track_color = C["coral"]
        else:
            track_color = C["divider"]

        painter.fillPath(track_path, QBrush(track_color))

        # -- Knob --
        knob_y = track_y + _TOGGLE_KNOB_MARGIN
        if self.isChecked():
            knob_x = _TOGGLE_TRACK_W - _TOGGLE_KNOB_D - _TOGGLE_KNOB_MARGIN
        else:
            knob_x = _TOGGLE_KNOB_MARGIN

        knob_path = QPainterPath()
        knob_path.addEllipse(knob_x, knob_y, _TOGGLE_KNOB_D, _TOGGLE_KNOB_D)
        painter.fillPath(knob_path, QBrush(C["text_hi"]))

        # -- Label text --
        font_family, font_size, font_weight = FONTS["body"]
        font = QFont(font_family, font_size)
        painter.setFont(font)
        painter.setPen(QPen(C["text_hi"]))
        text_x = _TOGGLE_TRACK_W + 10
        painter.drawText(
            text_x, 0, self.width() - text_x, self.height(),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self.text(),
        )

        painter.end()

    def hitButton(self, pos) -> bool:  # noqa: N802
        """Make the entire widget clickable."""
        return self.rect().contains(pos)


# ---------------------------------------------------------------------------
# OnboardingDialog
# ---------------------------------------------------------------------------


class OnboardingDialog(QWidget):
    """First-run onboarding dialog for CrawlSpace."""

    finished = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config: ConfigManager | None = None
        self._anim = AnimationController(self)

        # -- Window flags --
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(480, 360)

        self._build_ui()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Construct all child widgets and layouts."""
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(0)

        # -- Crawldad widget (animated, top center) --
        craw = _CrawWidget(self._anim, self)
        craw_row = QHBoxLayout()
        craw_row.addStretch()
        craw_row.addWidget(craw)
        craw_row.addStretch()
        root.addLayout(craw_row)

        root.addSpacing(8)

        # -- Title --
        title = QLabel("Welcome to CrawlSpace")
        title_family, title_size, title_weight = FONTS["title_large"]
        title_font = QFont(title_family, title_size)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {C['coral'].name()}; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        root.addSpacing(4)

        # -- Subtitle --
        subtitle = QLabel("Hunting zombies in your dev environment.")
        sub_family, sub_size, _ = FONTS["body"]
        sub_font = QFont(sub_family, sub_size)
        subtitle.setFont(sub_font)
        subtitle.setStyleSheet(f"color: {C['text_md'].name()}; background: transparent;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(subtitle)

        root.addSpacing(24)

        # -- Toggle switches --
        toggles_layout = QVBoxLayout()
        toggles_layout.setSpacing(12)
        toggles_layout.setContentsMargins(60, 0, 60, 0)

        self._toggle_startup = _ToggleSwitch("Start with Windows")
        self._toggle_startup.setChecked(True)
        toggles_layout.addWidget(self._toggle_startup)

        self._toggle_notify = _ToggleSwitch("Enable notifications")
        self._toggle_notify.setChecked(True)
        toggles_layout.addWidget(self._toggle_notify)

        self._toggle_overlay = _ToggleSwitch("Enable overlay")
        self._toggle_overlay.setChecked(False)
        toggles_layout.addWidget(self._toggle_overlay)

        root.addLayout(toggles_layout)

        root.addStretch()

        # -- "Let's Hunt" button --
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._hunt_btn = QPushButton("Let's Hunt")
        self._hunt_btn.setObjectName("coral_btn")
        self._hunt_btn.setFixedSize(160, 38)
        btn_font_family, btn_font_size, _ = FONTS["heading"]
        btn_font = QFont(btn_font_family, btn_font_size)
        btn_font.setBold(True)
        self._hunt_btn.setFont(btn_font)
        self._hunt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hunt_btn.clicked.connect(self._on_hunt_clicked)

        btn_row.addWidget(self._hunt_btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Painting — rounded dark background
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802
        """Paint a rounded dark background for the frameless dialog."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)

        # Background fill
        painter.fillPath(path, QBrush(C["notch_bg"]))

        # Subtle border
        painter.setPen(QPen(C["notch_border"], 1))
        painter.drawPath(path)

        painter.end()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show_onboarding(self, config: ConfigManager) -> None:
        """Show the dialog if this is the first run, else emit finished immediately."""
        self._config = config

        if config.get("first_run_done"):
            self.finished.emit()
            return

        # Centre on screen
        screen = self.screen()
        if screen is not None:
            geo = screen.availableGeometry()
            self.move(
                geo.x() + (geo.width() - self.width()) // 2,
                geo.y() + (geo.height() - self.height()) // 2,
            )

        self._anim.start()
        self.show()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_hunt_clicked(self) -> None:
        """Save toggle preferences, mark first run done, close, and emit finished."""
        if self._config is not None:
            self._config.set_many({
                "start_with_windows": self._toggle_startup.isChecked(),
                "toast_enabled": self._toggle_notify.isChecked(),
                "overlay_enabled": self._toggle_overlay.isChecked(),
                "first_run_done": True,
            })

        self._anim.stop()
        self.close()
        self.finished.emit()
