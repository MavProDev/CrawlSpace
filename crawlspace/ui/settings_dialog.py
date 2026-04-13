"""CrawlSpace — tabbed settings dialog."""

import sys
import platform
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QCheckBox, QComboBox, QSpinBox, QSlider,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView, QToolButton,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QPainterPath, QBrush, QPen

from crawlspace import __version__
from crawlspace.constants import C, FONTS, THEMES, make_font
from crawlspace.config import ConfigManager
from crawlspace.character.crawldad import draw_crawldad
from crawlspace.character.animation import AnimationController

# Keyboard shortcuts for the Shortcuts tab
_SHORTCUTS = [
    ("Ctrl+K", "Kill selected processes"),
    ("Ctrl+Shift+K", "Kill selected process trees"),
    ("Ctrl+R", "Manual refresh"),
    ("Ctrl+F", "Focus search bar"),
    ("Ctrl+A", "Select all processes"),
    ("Ctrl+D", "Deselect all"),
    ("Ctrl+T", "Toggle flat/tree view"),
    ("F5", "Toggle flat/tree view"),
    ("Delete", "Kill selected (with confirmation)"),
    ("Escape", "Close to tray / clear selection"),
    ("Space", "Toggle checkbox on focused row"),
    ("Enter", "Expand/collapse detail panel"),
]


class SettingsDialog(QDialog):
    """Tabbed settings panel for CrawlSpace."""

    settings_changed = pyqtSignal()

    def __init__(self, config: ConfigManager, anim: AnimationController,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._anim = anim

        self.setWindowTitle("CrawlSpace Settings")
        self.setFixedSize(520, 480)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(40)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 8, 0)

        title = QLabel("Settings")
        title.setFont(make_font(FONTS["heading"]))
        title.setStyleSheet(f"color: {C['coral'].name()}; background: transparent;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        close_btn = QToolButton()
        close_btn.setText("\u2715")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            f"QToolButton {{ color: #ffffff; background: transparent;"
            f"  border: none; font-size: 16px; font-weight: bold; }}"
            f"QToolButton:hover {{ color: {C['red'].name()}; background: #3a1515;"
            f"  border-radius: 4px; }}"
        )
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)

        outer.addWidget(header)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_general_tab(), "General")
        self._tabs.addTab(self._build_scanning_tab(), "Scanning")
        self._tabs.addTab(self._build_notifications_tab(), "Notifications")
        self._tabs.addTab(self._build_kill_tab(), "Kill")
        self._tabs.addTab(self._build_overlay_tab(), "Overlay")
        self._tabs.addTab(self._build_shortcuts_tab(), "Shortcuts")
        self._tabs.addTab(self._build_about_tab(), "About")
        outer.addWidget(self._tabs)

    # ── Tab builders ─────────────────────────────────────────

    def _build_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Start with Windows
        self._chk_startup = QCheckBox("Start with Windows")
        self._chk_startup.setChecked(self._config.get("start_with_windows", False))
        self._chk_startup.toggled.connect(self._on_startup_toggled)
        self._chk_startup.setToolTip("Launch CrawlSpace automatically when Windows starts")
        layout.addWidget(self._chk_startup)

        # Start minimized
        self._chk_minimized = QCheckBox("Start minimized to tray")
        self._chk_minimized.setChecked(self._config.get("start_minimized", False))
        self._chk_minimized.toggled.connect(lambda v: self._save("start_minimized", v))
        layout.addWidget(self._chk_minimized)

        # Theme picker
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Color theme:"))
        self._theme_combo = QComboBox()
        for name in THEMES:
            self._theme_combo.addItem(name.title(), name)
        current = self._config.get("color_theme", "coral")
        idx = self._theme_combo.findData(current)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self._theme_combo.setToolTip("Change the accent color theme")
        theme_row.addWidget(self._theme_combo)
        theme_row.addStretch()
        layout.addLayout(theme_row)

        layout.addStretch()
        return tab

    def _build_scanning_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Refresh interval
        interval_row = QHBoxLayout()
        interval_row.addWidget(QLabel("Scan interval (seconds):"))
        self._spin_interval = QSpinBox()
        self._spin_interval.setRange(1, 60)
        self._spin_interval.setValue(self._config.get("scan_interval_seconds", 5))
        self._spin_interval.setToolTip("How often to scan for dev processes (1-60s)")
        self._spin_interval.valueChanged.connect(
            lambda v: self._save("scan_interval_seconds", v)
        )
        interval_row.addWidget(self._spin_interval)
        interval_row.addStretch()
        layout.addLayout(interval_row)

        # Zombie threshold
        zombie_row = QHBoxLayout()
        zombie_row.addWidget(QLabel("Zombie threshold (hours):"))
        self._spin_zombie = QSpinBox()
        self._spin_zombie.setRange(1, 48)
        self._spin_zombie.setValue(self._config.get("zombie_threshold_hours", 4))
        self._spin_zombie.setToolTip("Processes older than this are flagged as zombies (1-48h)")
        self._spin_zombie.valueChanged.connect(
            lambda v: self._save("zombie_threshold_hours", v)
        )
        zombie_row.addWidget(self._spin_zombie)
        zombie_row.addStretch()
        layout.addLayout(zombie_row)

        # Whitelist info
        wl_count = len(self._config.get("whitelist_paths", []))
        self._wl_label = QLabel(f"Whitelist: {wl_count} paths configured")
        self._wl_label.setStyleSheet(f"color: {C['text_lo'].name()};")
        self._wl_label.setFont(make_font(FONTS["caption"]))
        layout.addWidget(self._wl_label)

        layout.addStretch()
        return tab

    def _build_notifications_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Master toggle
        self._chk_toast = QCheckBox("Enable notifications")
        self._chk_toast.setChecked(self._config.get("toast_enabled", True))
        self._chk_toast.toggled.connect(lambda v: self._save("toast_enabled", v))
        layout.addWidget(self._chk_toast)

        # DND
        self._chk_dnd = QCheckBox("Do Not Disturb mode")
        self._chk_dnd.setChecked(self._config.get("dnd_mode", False))
        self._chk_dnd.toggled.connect(lambda v: self._save("dnd_mode", v))
        layout.addWidget(self._chk_dnd)

        # Sound
        self._chk_sound = QCheckBox("Enable sounds")
        self._chk_sound.setChecked(self._config.get("sound_enabled", False))
        self._chk_sound.toggled.connect(lambda v: self._save("sound_enabled", v))
        layout.addWidget(self._chk_sound)

        # Toast duration
        dur_row = QHBoxLayout()
        dur_row.addWidget(QLabel("Toast duration (seconds):"))
        self._spin_toast_dur = QSpinBox()
        self._spin_toast_dur.setRange(3, 30)
        self._spin_toast_dur.setValue(self._config.get("toast_duration_seconds", 8))
        self._spin_toast_dur.valueChanged.connect(
            lambda v: self._save("toast_duration_seconds", v)
        )
        dur_row.addWidget(self._spin_toast_dur)
        dur_row.addStretch()
        layout.addLayout(dur_row)

        # Per-type toggles
        sep = QLabel("Per-type toggles:")
        sep.setFont(make_font(FONTS["label_bold"]))
        sep.setStyleSheet(f"color: {C['text_md'].name()};")
        layout.addWidget(sep)

        type_toggles = [
            ("notify_new_process", "New process detected"),
            ("notify_process_died", "Process exited"),
            ("notify_kill_success", "Kill successful"),
            ("notify_kill_failed", "Kill failed"),
            ("notify_zombie", "Zombie process alert"),
            ("notify_port_conflict", "Port conflict"),
        ]
        for key, label in type_toggles:
            chk = QCheckBox(label)
            chk.setChecked(self._config.get(key, True))
            chk.toggled.connect(lambda v, k=key: self._save(k, v))
            layout.addWidget(chk)

        layout.addStretch()
        return tab

    def _build_kill_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Graceful timeout
        timeout_row = QHBoxLayout()
        timeout_row.addWidget(QLabel("Graceful kill timeout (seconds):"))
        self._spin_kill_timeout = QSpinBox()
        self._spin_kill_timeout.setRange(1, 10)
        self._spin_kill_timeout.setValue(self._config.get("kill_timeout_seconds", 3))
        self._spin_kill_timeout.setToolTip("Wait this long after SIGTERM before SIGKILL (1-10s)")
        self._spin_kill_timeout.valueChanged.connect(
            lambda v: self._save("kill_timeout_seconds", v)
        )
        timeout_row.addWidget(self._spin_kill_timeout)
        timeout_row.addStretch()
        layout.addLayout(timeout_row)

        # Confirm kills
        self._chk_confirm = QCheckBox("Ask for confirmation before killing")
        self._chk_confirm.setChecked(self._config.get("confirm_kill", True))
        self._chk_confirm.toggled.connect(lambda v: self._save("confirm_kill", v))
        layout.addWidget(self._chk_confirm)

        # Kill All note
        note = QLabel('Note: "Kill All" always requires typing KILL to confirm.\nThis cannot be disabled.')
        note.setFont(make_font(FONTS["caption"]))
        note.setStyleSheet(f"color: {C['text_lo'].name()};")
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addStretch()
        return tab

    def _build_overlay_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Enable overlay
        self._chk_overlay = QCheckBox("Enable overlay")
        self._chk_overlay.setChecked(self._config.get("overlay_enabled", False))
        self._chk_overlay.toggled.connect(lambda v: self._save("overlay_enabled", v))
        layout.addWidget(self._chk_overlay)

        # Default edge
        edge_row = QHBoxLayout()
        edge_row.addWidget(QLabel("Default edge:"))
        self._edge_combo = QComboBox()
        for edge in ["right", "left", "top", "bottom"]:
            self._edge_combo.addItem(edge.title(), edge)
        current_edge = self._config.get("overlay_edge", "right")
        idx = self._edge_combo.findData(current_edge)
        if idx >= 0:
            self._edge_combo.setCurrentIndex(idx)
        self._edge_combo.currentIndexChanged.connect(self._on_edge_changed)
        edge_row.addWidget(self._edge_combo)
        edge_row.addStretch()
        layout.addLayout(edge_row)

        # Overlay opacity
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel("Opacity:"))
        self._slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self._slider_opacity.setRange(30, 100)
        self._slider_opacity.setValue(int(self._config.get("overlay_opacity", 0.85) * 100))
        self._slider_opacity.setToolTip("Overlay background opacity")
        self._opacity_label = QLabel(f"{self._slider_opacity.value()}%")
        self._slider_opacity.valueChanged.connect(self._on_opacity_changed)
        opacity_row.addWidget(self._slider_opacity)
        opacity_row.addWidget(self._opacity_label)
        layout.addLayout(opacity_row)

        layout.addStretch()
        return tab

    def _build_shortcuts_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)

        table = QTableWidget(len(_SHORTCUTS), 2)
        table.setHorizontalHeaderLabels(["Shortcut", "Action"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(0, 140)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.verticalHeader().setVisible(False)

        for i, (key, action) in enumerate(_SHORTCUTS):
            key_item = QTableWidgetItem(key)
            key_item.setFont(make_font(FONTS["mono"]))
            table.setItem(i, 0, key_item)
            table.setItem(i, 1, QTableWidgetItem(action))

        layout.addWidget(table)
        return tab

    def _build_about_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Craw widget
        craw_widget = _AboutCrawWidget(self._anim, tab)
        layout.addWidget(craw_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("CrawlSpace")
        title.setFont(make_font(FONTS["title_large"]))
        title.setStyleSheet(f"color: {C['coral'].name()};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Version
        ver = QLabel(f"v{__version__}")
        ver.setFont(make_font(FONTS["body"]))
        ver.setStyleSheet(f"color: {C['text_lo'].name()};")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ver)

        # Tagline
        tag = QLabel("Hunting zombies in your dev environment.")
        tag.setFont(make_font(FONTS["caption"]))
        tag.setStyleSheet(f"color: {C['text_md'].name()};")
        tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tag)

        layout.addSpacing(8)

        # Credits
        credits = QLabel("Built by @ReelDad / MavPro Group LLC")
        credits.setFont(make_font(FONTS["label"]))
        credits.setStyleSheet(f"color: {C['text_md'].name()};")
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits)

        # System info
        layout.addSpacing(8)
        info_lines = [
            f"Python {platform.python_version()}",
            f"Platform: {platform.system()} {platform.release()}",
            f"Architecture: {platform.machine()}",
        ]
        for line in info_lines:
            lbl = QLabel(line)
            lbl.setFont(make_font(FONTS["tiny"]))
            lbl.setStyleSheet(f"color: {C['text_lo'].name()};")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl)

        layout.addStretch()
        return tab

    # ── Handlers ─────────────────────────────────────────────

    def _on_startup_toggled(self, enabled: bool) -> None:
        self._save("start_with_windows", enabled)
        from crawlspace.utils.startup import enable_startup, disable_startup
        if enabled:
            enable_startup()
        else:
            disable_startup()

    def _save(self, key: str, value) -> None:
        self._config.set(key, value)
        self.settings_changed.emit()

    def _on_theme_changed(self, index: int) -> None:
        theme_name = self._theme_combo.currentData()
        if theme_name:
            self._save("color_theme", theme_name)
            from crawlspace.utils.colors import apply_theme
            apply_theme(theme_name)

    def _on_edge_changed(self, index: int) -> None:
        edge = self._edge_combo.currentData()
        if edge:
            self._save("overlay_edge", edge)

    def _on_opacity_changed(self, value: int) -> None:
        self._opacity_label.setText(f"{value}%")
        self._save("overlay_opacity", value / 100.0)

    # ── Paint ────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        """Paint rounded dark background."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        p.setPen(QPen(C["divider"], 1))
        p.setBrush(QBrush(C["notch_bg"]))
        p.drawPath(path)
        p.end()

    # ── Drag support ─────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if hasattr(self, '_drag_pos') and self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self._drag_pos = None


class _AboutCrawWidget(QWidget):
    """Animated Craw for the About tab."""

    def __init__(self, anim: AnimationController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._anim = anim
        self.setFixedSize(80, 50)
        anim.frame_tick.connect(self.update)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        ps = 3.5
        cx = (self.width() - 11 * ps) / 2
        cy = (self.height() - 10 * ps) / 2
        draw_crawldad(p, cx, cy, ps,
                      bounce=self._anim.bounce,
                      emotion="happy",
                      eye_glow=True,
                      glow_phase=self._anim.pulse)
        p.end()
