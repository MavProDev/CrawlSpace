"""CrawlSpace — inline expandable process detail panel."""

import psutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QScrollArea, QLineEdit, QFrame,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from crawlspace.constants import C, FONTS, make_font
from crawlspace.process_info import ProcessInfo

_SENSITIVE_KEYS = {"KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL", "AUTH", "API_KEY"}


class DetailPanel(QWidget):
    """Expandable inline panel showing full process detail. Lazy-loads expensive data."""

    kill_requested = pyqtSignal(int)
    kill_tree_requested = pyqtSignal(int)
    suspend_requested = pyqtSignal(int)
    resume_requested = pyqtSignal(int)
    close_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._proc: ProcessInfo | None = None
        self.setVisible(False)
        self.setMaximumHeight(320)
        self.setStyleSheet(
            f"background-color: {C['card_bg'].name()};"
            f"border: 1px solid {C['divider'].name()};"
            f"border-radius: 6px;"
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 8, 12, 8)
        outer.setSpacing(6)

        # ── Header: name + PID + status + action buttons ──
        header = QHBoxLayout()
        header.setSpacing(8)

        self._name_label = QLabel()
        self._name_label.setFont(make_font(FONTS["heading"]))
        self._name_label.setStyleSheet(f"color: {C['text_hi'].name()}; border: none;")
        header.addWidget(self._name_label)

        self._pid_badge = QLabel()
        self._pid_badge.setFont(make_font(FONTS["mono"]))
        self._pid_badge.setStyleSheet(
            f"color: {C['coral'].name()}; background: {C['notch_bg'].name()};"
            f"border-radius: 3px; padding: 1px 6px;"
        )
        header.addWidget(self._pid_badge)

        self._status_dot = QLabel()
        self._status_dot.setFixedSize(10, 10)
        header.addWidget(self._status_dot)

        header.addStretch()

        # Action buttons
        for label, signal_name, obj_name in [
            ("Kill", "kill_requested", "red_btn"),
            ("Kill Tree", "kill_tree_requested", "red_btn"),
            ("Suspend", "suspend_requested", ""),
            ("Resume", "resume_requested", ""),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(24)
            btn.setFont(make_font(FONTS["label_bold"]))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if obj_name:
                btn.setObjectName(obj_name)
            signal = getattr(self, signal_name)
            btn.clicked.connect(lambda checked, s=signal: self._emit_pid(s))
            header.addWidget(btn)

        btn_close = QPushButton("x")
        btn_close.setFixedSize(24, 24)
        btn_close.setObjectName("flat_btn")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self._close)
        header.addWidget(btn_close)

        outer.addLayout(header)

        # ── Metrics row ──
        self._metrics_label = QLabel()
        self._metrics_label.setFont(make_font(FONTS["caption"]))
        self._metrics_label.setStyleSheet(f"color: {C['text_md'].name()}; border: none;")
        self._metrics_label.setWordWrap(True)
        outer.addWidget(self._metrics_label)

        # ── Command line ──
        self._cmdline_box = QLineEdit()
        self._cmdline_box.setReadOnly(True)
        self._cmdline_box.setFont(make_font(FONTS["mono"]))
        self._cmdline_box.setStyleSheet(
            f"background: {C['notch_bg'].name()}; color: {C['text_hi'].name()};"
            f"border: 1px solid {C['divider'].name()}; border-radius: 3px; padding: 4px;"
        )
        outer.addWidget(self._cmdline_box)

        # ── Tabs: Files, Network, Environment ──
        self._tabs = QTabWidget()
        self._tabs.setMaximumHeight(160)
        self._tabs.setStyleSheet(f"QTabWidget::pane {{ border: none; background: {C['notch_bg'].name()}; }}")

        self._files_area = self._make_scroll_tab("Open Files")
        self._net_area = self._make_scroll_tab("Network")
        self._env_area = self._make_scroll_tab("Environment")

        outer.addWidget(self._tabs)

    def _make_scroll_tab(self, title: str) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"border: none; background: {C['notch_bg'].name()};")
        content = QWidget()
        content.setLayout(QVBoxLayout())
        content.layout().setContentsMargins(8, 4, 8, 4)
        content.layout().setSpacing(2)
        scroll.setWidget(content)
        self._tabs.addTab(scroll, title)
        return scroll

    def show_process(self, proc: ProcessInfo) -> None:
        """Display details for a process. Lazy-loads expensive data."""
        self._proc = proc
        self.setVisible(True)

        self._name_label.setText(proc.name)
        self._pid_badge.setText(f"PID {proc.pid}")

        # Status dot
        color = C["green"] if proc.status == "running" else (
            C["amber"] if proc.status == "sleeping" else C["red"]
        )
        self._status_dot.setStyleSheet(
            f"background-color: {color.name()}; border-radius: 5px; border: none;"
        )

        # Metrics
        parts = [
            f"CPU: {proc.cpu_percent:.1f}%",
            f"Memory: {proc.memory_mb:.1f} MB",
            f"Uptime: {proc.uptime_human}",
            f"User: {proc.username}",
            f"PPID: {proc.ppid}",
        ]
        if proc.exe_path:
            parts.append(f"Path: {proc.exe_path}")
        self._metrics_label.setText("  |  ".join(parts))

        # Command line
        self._cmdline_box.setText(proc.cmdline_str)

        # Lazy-load tabs
        self._load_files(proc.pid)
        self._load_network(proc.pid)
        self._load_environment(proc.pid)

    def _emit_pid(self, signal) -> None:
        if self._proc:
            signal.emit(self._proc.pid)

    def _close(self) -> None:
        self._proc = None
        self.setVisible(False)
        self.close_requested.emit()

    def _load_files(self, pid: int) -> None:
        """Load open files list (handles AccessDenied gracefully)."""
        layout = self._files_area.widget().layout()
        self._clear_layout(layout)
        try:
            proc = psutil.Process(pid)
            files = proc.open_files()
            if not files:
                layout.addWidget(self._dim_label("No open files"))
            else:
                for f in files[:30]:
                    layout.addWidget(self._mono_label(f.path))
        except psutil.AccessDenied:
            layout.addWidget(self._dim_label("Access Denied — run as admin"))
        except psutil.NoSuchProcess:
            layout.addWidget(self._dim_label("Process no longer exists"))
        except Exception as e:
            layout.addWidget(self._dim_label(f"Error: {e}"))
        layout.addStretch()

    def _load_network(self, pid: int) -> None:
        """Load network connections."""
        layout = self._net_area.widget().layout()
        self._clear_layout(layout)
        try:
            proc = psutil.Process(pid)
            conns = proc.net_connections()
            if not conns:
                layout.addWidget(self._dim_label("No network connections"))
            else:
                for c in conns[:30]:
                    local = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "?"
                    remote = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "-"
                    status = c.status if c.status else ""
                    layout.addWidget(self._mono_label(f"{local}  ->  {remote}  [{status}]"))
        except psutil.AccessDenied:
            layout.addWidget(self._dim_label("Access Denied — run as admin"))
        except psutil.NoSuchProcess:
            layout.addWidget(self._dim_label("Process no longer exists"))
        except Exception as e:
            layout.addWidget(self._dim_label(f"Error: {e}"))
        layout.addStretch()

    def _load_environment(self, pid: int) -> None:
        """Load environment variables with sensitive value masking."""
        layout = self._env_area.widget().layout()
        self._clear_layout(layout)
        try:
            proc = psutil.Process(pid)
            env = proc.environ()
            if not env:
                layout.addWidget(self._dim_label("No environment variables"))
            else:
                for key in sorted(env.keys())[:60]:
                    value = env[key]
                    is_sensitive = any(s in key.upper() for s in _SENSITIVE_KEYS)
                    display_val = "****" if is_sensitive else value[:120]
                    row = QHBoxLayout()
                    row.setSpacing(8)
                    k_label = QLabel(key)
                    k_label.setFont(make_font(FONTS["mono"]))
                    k_label.setStyleSheet(f"color: {C['coral'].name()};")
                    k_label.setFixedWidth(220)
                    row.addWidget(k_label)
                    v_label = QLabel(display_val)
                    v_label.setFont(make_font(FONTS["caption"]))
                    v_label.setStyleSheet(f"color: {C['text_md'].name()};")
                    v_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                    row.addWidget(v_label)
                    if is_sensitive:
                        reveal_btn = QPushButton("Reveal")
                        reveal_btn.setFixedSize(50, 18)
                        reveal_btn.setFont(make_font(FONTS["tiny"]))
                        reveal_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                        actual_val = value[:120]
                        reveal_btn.clicked.connect(
                            lambda checked, lbl=v_label, val=actual_val, btn=reveal_btn:
                            self._reveal(lbl, val, btn)
                        )
                        row.addWidget(reveal_btn)
                    row.addStretch()
                    container = QWidget()
                    container.setLayout(row)
                    layout.addWidget(container)
        except psutil.AccessDenied:
            layout.addWidget(self._dim_label("Access Denied — run as admin"))
        except psutil.NoSuchProcess:
            layout.addWidget(self._dim_label("Process no longer exists"))
        except Exception as e:
            layout.addWidget(self._dim_label(f"Error: {e}"))
        layout.addStretch()

    @staticmethod
    def _reveal(label: QLabel, value: str, btn: QPushButton) -> None:
        label.setText(value)
        btn.setVisible(False)

    def _mono_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(make_font(FONTS["mono"]))
        lbl.setStyleSheet(f"color: {C['text_md'].name()};")
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        return lbl

    def _dim_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(make_font(FONTS["caption"]))
        lbl.setStyleSheet(f"color: {C['text_lo'].name()};")
        return lbl

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
