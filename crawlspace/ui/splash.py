"""Boot splash screen with animated Crawldad and terminal loading lines."""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QPainterPath
from PyQt6.QtWidgets import QWidget

from crawlspace import __version__
from crawlspace.character.animation import AnimationController
from crawlspace.character.crawldad import draw_crawldad
from crawlspace.constants import C, FONTS


# ---------------------------------------------------------------------------
# Loading-line definitions
# ---------------------------------------------------------------------------

_LOADING_LINES: list[str] = [
    "[✻] Initializing CrawlSpace...",
    "[✽] Waking up Craw...",
    "[✶] Scanning process table...",
    "[✳] Cataloging dev environments...",
    "[✢] Checking for zombies...",
]

_FINAL_LINE_TEMPLATE: str = "[·] Hunting complete. {count} processes found."

# Timing constants
_LINE_DELAY_MS: int = 250
_FADE_DELAY_MS: int = 500
_FADE_STEP_MS: int = 33
_FADE_DECREMENT: float = 0.02

# Layout constants
_WIDTH: int = 480
_HEIGHT: int = 360
_CORNER_RADIUS: int = 16
_PIXEL_SIZE: float = 4.0

# Crawldad grid dimensions (from crawldad.py: 11 cols x 10 rows)
_CRAW_COLS: int = 11
_CRAW_ROWS: int = 10


class SplashScreen(QWidget):
    """Frameless splash screen shown during application boot."""

    finished = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._lines_shown: list[str] = []
        self._process_count: int | None = None
        self._opacity: float = 1.0
        self._fading: bool = False

        # Animation controller for Crawldad bounce / eye glow
        self._anim = AnimationController(self)
        self._anim.frame_tick.connect(self.update)

        # Timer for revealing loading lines one at a time
        self._line_timer = QTimer(self)
        self._line_timer.setInterval(_LINE_DELAY_MS)
        self._line_timer.timeout.connect(self._show_next_line)
        self._line_index: int = 0

        # Timer for the fade-out sequence
        self._fade_timer = QTimer(self)
        self._fade_timer.setInterval(_FADE_STEP_MS)
        self._fade_timer.timeout.connect(self._fade_tick)

        # Window flags: frameless, always on top, translucent
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(_WIDTH, _HEIGHT)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show_splash(self) -> None:
        """Display the splash and begin the loading animation."""
        self._center_on_screen()
        self.show()
        self._anim.start()
        self._line_timer.start()

    def set_process_count(self, count: int) -> None:
        """Set the process count used in the final loading line."""
        self._process_count = count

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def _center_on_screen(self) -> None:
        """Center the splash on the primary screen."""
        screen = self.screen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        x = geo.x() + (geo.width() - _WIDTH) // 2
        y = geo.y() + (geo.height() - _HEIGHT) // 2
        self.move(x, y)

    # ------------------------------------------------------------------
    # Line reveal logic
    # ------------------------------------------------------------------

    def _show_next_line(self) -> None:
        """Reveal the next terminal loading line."""
        if self._line_index < len(_LOADING_LINES):
            self._lines_shown.append(_LOADING_LINES[self._line_index])
            self._line_index += 1
            self.update()
        else:
            # All prefix lines shown — append final line and start fade
            self._line_timer.stop()
            count = self._process_count if self._process_count is not None else 0
            self._lines_shown.append(
                _FINAL_LINE_TEMPLATE.format(count=count)
            )
            self.update()
            QTimer.singleShot(_FADE_DELAY_MS, self._begin_fade)

    def _begin_fade(self) -> None:
        """Start the opacity fade-out."""
        self._fading = True
        self._fade_timer.start()

    def _fade_tick(self) -> None:
        """Decrease opacity each tick until fully transparent."""
        self._opacity -= _FADE_DECREMENT
        if self._opacity <= 0.0:
            self._opacity = 0.0
            self._fade_timer.stop()
            self._anim.stop()
            self.hide()
            self.finished.emit()
        else:
            self.setWindowOpacity(self._opacity)
            self.update()

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, event: object) -> None:
        """Render the splash contents via QPainter."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # --- Rounded background ---
        bg_path = QPainterPath()
        bg_path.addRoundedRect(
            0.0, 0.0, float(_WIDTH), float(_HEIGHT),
            float(_CORNER_RADIUS), float(_CORNER_RADIUS),
        )
        painter.setClipPath(bg_path)
        painter.fillPath(bg_path, C["notch_bg"])

        # --- Crawldad (centered horizontally, upper third) ---
        craw_w = _CRAW_COLS * _PIXEL_SIZE
        craw_h = _CRAW_ROWS * _PIXEL_SIZE
        craw_x = (_WIDTH - craw_w) / 2.0
        craw_y = 40.0

        draw_crawldad(
            painter,
            craw_x,
            craw_y,
            _PIXEL_SIZE,
            bounce=self._anim.bounce,
            eye_glow=True,
            glow_phase=self._anim.pulse,
        )

        # --- Title: "CrawlSpace" ---
        title_font_spec = FONTS["title_large"]
        title_font = QFont(title_font_spec[0], title_font_spec[1])
        title_font.setBold(title_font_spec[2] == "Bold")
        painter.setFont(title_font)
        painter.setPen(C["coral"])

        title_y = craw_y + craw_h + 30.0
        painter.drawText(
            0, int(title_y), _WIDTH, 36,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            "CrawlSpace",
        )

        # --- Version ---
        version_font = QFont(title_font_spec[0], 11)
        version_font.setBold(False)
        painter.setFont(version_font)
        painter.setPen(C["text_lo"])

        version_y = title_y + 32.0
        painter.drawText(
            0, int(version_y), _WIDTH, 20,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            f"v{__version__}",
        )

        # --- Terminal loading lines ---
        mono_spec = FONTS["mono"]
        mono_font = QFont(mono_spec[0], mono_spec[1])
        mono_font.setBold(mono_spec[2] == "Bold")
        painter.setFont(mono_font)
        painter.setPen(C["text_md"])

        line_x = 48
        line_y_start = int(version_y + 30.0)
        line_height = 18

        for i, line in enumerate(self._lines_shown):
            painter.drawText(
                line_x, line_y_start + i * line_height,
                _WIDTH - line_x * 2, line_height,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                line,
            )

        # --- Footer ---
        caption_spec = FONTS["caption"]
        caption_font = QFont(caption_spec[0], caption_spec[1])
        caption_font.setBold(caption_spec[2] == "Bold")
        painter.setFont(caption_font)
        painter.setPen(C["text_lo"])

        painter.drawText(
            0, _HEIGHT - 28, _WIDTH, 20,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            "Built by @ReelDad",
        )

        painter.end()
