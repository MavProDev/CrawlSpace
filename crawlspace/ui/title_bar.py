"""CrawlSpace — custom title bar with Craw, native drag, and window controls."""

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QFont
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

from crawlspace.constants import C, FONTS, make_font
from crawlspace.character.crawldad import draw_crawldad, eye_shift
from crawlspace.character.animation import AnimationController
from crawlspace.character.emotions import EmotionStateMachine
from crawlspace import __version__


class _CrawWidget(QWidget):
    """Compact paint surface for the animated Crawldad character."""

    def __init__(self, anim: AnimationController, emotions: EmotionStateMachine,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._anim = anim
        self._emotions = emotions
        self.setFixedSize(QSize(38, 36))
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        ex, ey = eye_shift(self)
        draw_crawldad(p,
                      x=(self.width() - 11 * 3.0) / 2,
                      y=(self.height() - 10 * 3.0) / 2,
                      ps=3.0,
                      bounce=self._anim.bounce,
                      ex=ex, ey=ey,
                      emotion=self._emotions.current,
                      eye_glow=True,
                      glow_phase=self._anim.pulse)
        p.end()


class TitleBar(QWidget):
    """Custom title bar with native window drag and visible controls."""

    minimize_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    close_clicked = pyqtSignal()

    def __init__(self, anim: AnimationController, emotions: EmotionStateMachine,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._anim = anim
        self.setFixedHeight(40)
        self.setStyleSheet(
            f"background: {C['notch_bg'].name()};"
            f"border-bottom: 1px solid {C['divider'].name()};"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 4, 0)
        layout.setSpacing(6)

        # Craw mascot
        self._craw = _CrawWidget(anim, emotions, self)
        layout.addWidget(self._craw)

        # Title
        title = QLabel("CrawlSpace")
        title.setStyleSheet(
            f"color: {C['coral'].name()}; font-size: 14pt; font-weight: bold;"
            f"background: transparent;"
        )
        layout.addWidget(title)

        # Version
        ver = QLabel(f"v{__version__}")
        ver.setStyleSheet(
            f"color: {C['text_lo'].name()}; font-size: 8pt;"
            f"background: transparent; padding-top: 3px;"
        )
        layout.addWidget(ver)

        layout.addStretch()

        # Window control buttons — use ID selectors to beat global QPushButton QSS
        def _wctrl(text: str, name: str, tooltip: str, color: str,
                   hover_bg: str, hover_color: str) -> QPushButton:
            btn = QPushButton(text)
            btn.setObjectName(name)
            btn.setToolTip(tooltip)
            btn.setFixedSize(32, 32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"#{name} {{ background: transparent; border: none;"
                f"  color: {color}; font-size: 16px; font-weight: bold; }}"
                f"#{name}:hover {{ background: {hover_bg}; color: {hover_color};"
                f"  border-radius: 4px; }}"
            )
            return btn

        self._btn_min = _wctrl("\u2014", "tb_min", "Minimize",
                               C['text_hi'].name(), C['card_bg'].name(), "#ffffff")
        self._btn_min.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(self._btn_min)

        self._btn_settings = _wctrl("\u2699", "tb_set", "Settings",
                                    C['text_hi'].name(), C['card_bg'].name(), C['coral'].name())
        self._btn_settings.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self._btn_settings)

        self._btn_close = _wctrl("\u2715", "tb_close", "Close to tray",
                                 C['text_hi'].name(), "#3a1515", C['red'].name())
        self._btn_close.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self._btn_close)

        # Connect animation to repaint Craw only
        anim.frame_tick.connect(self._craw.update)

    # ── Native window drag ───────────────────────────────────

    def mousePressEvent(self, event) -> None:
        """Start native system window move on left-click drag."""
        if event.button() == Qt.MouseButton.LeftButton:
            window = self.window()
            if window and window.windowHandle():
                window.windowHandle().startSystemMove()
            event.accept()
