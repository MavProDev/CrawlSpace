"""CrawlSpace — lightweight main window for killing ghost processes."""

import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QApplication, QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QShortcut, QKeySequence, QCursor, QColor

from crawlspace.constants import C, FONTS, make_font
from crawlspace.config import ConfigManager
from crawlspace.app import CrawlSpaceApp
from crawlspace.character.animation import AnimationController
from crawlspace.character.emotions import EmotionStateMachine
from crawlspace.process_info import ProcessInfo
from crawlspace.utils.colors import uptime_color
from crawlspace.ui.title_bar import TitleBar
from PyQt6.QtWidgets import QCheckBox


class MainWindow(QWidget):
    """Lean CrawlSpace window — see ghost processes, kill them, done."""

    settings_requested = pyqtSignal()

    def __init__(self, app_ctrl: CrawlSpaceApp, config: ConfigManager,
                 anim: AnimationController, emotions: EmotionStateMachine,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._app = app_ctrl
        self._config = config
        self._processes: list[ProcessInfo] = []

        self.setWindowTitle("CrawlSpace")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        )
        self.setMinimumSize(500, 300)
        self.resize(
            config.get("window_w", 650),
            config.get("window_h", 440),
        )
        self.move(config.get("window_x", 200), config.get("window_y", 200))
        self.setStyleSheet(f"background-color: {C['notch_bg'].name()};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 0, 1, 1)  # 1px border for resize grip
        layout.setSpacing(0)

        # ── Title bar ──
        self._title_bar = TitleBar(anim, emotions, self)
        self._title_bar.minimize_clicked.connect(self.showMinimized)
        self._title_bar.close_clicked.connect(self._close_to_tray)
        self._title_bar.settings_clicked.connect(self._open_settings)
        layout.addWidget(self._title_bar)

        # ── Status bar with toggle ──
        status_bar = QWidget()
        status_bar.setFixedHeight(26)
        status_bar.setStyleSheet(
            f"background: {C['card_bg'].name()};"
            f"border-bottom: 1px solid {C['divider'].name()};"
        )
        slay = QHBoxLayout(status_bar)
        slay.setContentsMargins(12, 0, 12, 0)
        slay.setSpacing(8)

        self._status = QLabel("Scanning...")
        self._status.setFont(make_font(FONTS["caption"]))
        self._status.setStyleSheet(f"color: {C['text_lo'].name()};")
        slay.addWidget(self._status)

        slay.addStretch()

        self._show_active = False
        self._chk_active = QCheckBox("Show active session processes")
        self._chk_active.setChecked(False)
        self._chk_active.setFont(make_font(FONTS["tiny"]))
        self._chk_active.setStyleSheet(f"color: {C['text_lo'].name()};")
        self._chk_active.toggled.connect(self._on_toggle_active)
        slay.addWidget(self._chk_active)

        layout.addWidget(status_bar)

        # ── Process table ──
        self._table = QTreeWidget()
        self._table.setHeaderLabels(["Status", "Name", "Command", "Uptime", "Mem", ""])
        self._table.setColumnCount(6)
        self._table.setAlternatingRowColors(True)
        self._table.setRootIsDecorated(False)
        self._table.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self._table.setSortingEnabled(True)
        self._table.setIndentation(0)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._context_menu)
        self._table.itemClicked.connect(self._on_item_clicked)

        header = self._table.header()
        self._table.setColumnWidth(0, 70)
        self._table.setColumnWidth(1, 100)
        self._table.setColumnWidth(2, 220)
        self._table.setColumnWidth(3, 65)
        self._table.setColumnWidth(4, 60)
        self._table.setColumnWidth(5, 56)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self._table, stretch=1)

        # ── Info bar (shows details of clicked process) ──
        self._info_bar = QLabel("")
        self._info_bar.setFont(make_font(FONTS["mono"]))
        self._info_bar.setStyleSheet(
            f"color: {C['text_md'].name()}; padding: 4px 12px;"
            f"background: {C['card_bg'].name()};"
            f"border-top: 1px solid {C['divider'].name()};"
        )
        self._info_bar.setWordWrap(True)
        self._info_bar.setMaximumHeight(48)
        self._info_bar.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._info_bar.setVisible(False)
        layout.addWidget(self._info_bar)

        # ── Footer ──
        footer = QWidget()
        footer.setFixedHeight(32)
        footer.setStyleSheet(
            f"background: {C['card_bg'].name()};"
            f"border-top: 1px solid {C['divider'].name()};"
        )
        flay = QHBoxLayout(footer)
        flay.setContentsMargins(12, 0, 12, 0)
        flay.setSpacing(8)

        self._btn_kill_all = QPushButton("Kill All Orphans")
        self._btn_kill_all.setObjectName("red_btn")
        self._btn_kill_all.setFixedHeight(24)
        self._btn_kill_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_kill_all.setFont(make_font(FONTS["label_bold"]))
        self._btn_kill_all.setToolTip('Kill all orphaned processes (requires typing "KILL")')
        self._btn_kill_all.clicked.connect(self._kill_all_orphans)
        flay.addWidget(self._btn_kill_all)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setFixedHeight(24)
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setFont(make_font(FONTS["label_bold"]))
        btn_refresh.setToolTip("Scan now (Ctrl+R)")
        btn_refresh.clicked.connect(self._refresh)
        flay.addWidget(btn_refresh)

        flay.addStretch()

        self._footer_label = QLabel()
        self._footer_label.setFont(make_font(FONTS["tiny"]))
        self._footer_label.setStyleSheet(f"color: {C['text_lo'].name()};")
        flay.addWidget(self._footer_label)

        layout.addWidget(footer)

        # ── Shortcuts ──
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self._refresh)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self._close_to_tray)

        # ── Resize edge tracking ──
        self._resize_edge = ""
        self._resize_start = None
        self._resize_geo = None
        self.setMouseTracking(True)

    # ── Data ─────────────────────────────────────────────────

    def on_processes_updated(self, processes: list[ProcessInfo]) -> None:
        """Called by scanner with updated process list."""
        self._processes = processes
        self._rebuild_table()

    def _on_toggle_active(self, checked: bool) -> None:
        self._show_active = checked
        self._rebuild_table()

    def _rebuild_table(self) -> None:
        self._table.setSortingEnabled(False)
        self._table.clear()
        procs = self._processes
        orphans = [p for p in procs if p.is_orphan]
        active = [p for p in procs if not p.is_orphan]

        # Status text always shows full counts
        if not orphans and not active:
            self._status.setText("No ghost processes found. You're clean!")
            self._status.setStyleSheet(f"color: {C['green'].name()};")
        else:
            parts = []
            if orphans:
                parts.append(f"{len(orphans)} orphaned")
            if active:
                parts.append(f"{len(active)} active (hidden)")
            total_mb = sum(p.memory_mb for p in procs)
            self._status.setText(f"{' + '.join(parts)}  |  {total_mb:.0f} MB")
            self._status.setStyleSheet(
                f"color: {C['coral'].name() if orphans else C['text_md'].name()};"
            )

        # Show orphans always, active only if toggled on
        for p in sorted(orphans, key=lambda x: x.uptime_seconds, reverse=True):
            self._add_row(p)
        if self._show_active:
            for p in sorted(active, key=lambda x: x.uptime_seconds, reverse=True):
                self._add_row(p)

        self._footer_label.setText(f"Last scan: {time.strftime('%H:%M:%S')}")
        self._btn_kill_all.setEnabled(len(orphans) > 0)
        self._btn_kill_all.setText(
            f"Kill All Orphans ({len(orphans)})" if orphans else "No Orphans"
        )
        self._table.setSortingEnabled(True)

    def _add_row(self, p: ProcessInfo) -> None:
        item = QTreeWidgetItem()

        # Status column
        if p.is_orphan:
            item.setText(0, "Orphan")
            item.setForeground(0, C["coral"])
            item.setToolTip(0, f"Parent exited — safe to kill\n{p.parent_chain}")
        else:
            item.setText(0, "Active")
            item.setForeground(0, C["green"])
            item.setToolTip(0, f"Part of a live session\n{p.parent_chain}")

        item.setFont(0, make_font(FONTS["tiny_bold"]))

        # Name
        item.setText(1, p.name)
        item.setFont(1, make_font(FONTS["body"]))

        # Command (short)
        item.setText(2, p.cmdline_short)
        item.setToolTip(2, p.cmdline_str)
        item.setFont(2, make_font(FONTS["caption"]))
        item.setForeground(2, C["text_md"])

        # Uptime
        item.setText(3, p.uptime_human)
        item.setForeground(3, uptime_color(p.uptime_seconds))

        # Memory
        item.setText(4, f"{p.memory_mb:.0f} MB")

        # Store PID
        item.setData(0, Qt.ItemDataRole.UserRole, p.pid)

        self._table.addTopLevelItem(item)

        # Kill button — red for orphans, grey for active
        kill_btn = QPushButton("Kill")
        kill_btn.setFixedSize(50, 22)
        kill_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        kill_btn.setFont(make_font(FONTS["tiny_bold"]))
        if p.is_orphan:
            kill_btn.setObjectName("red_btn")
        else:
            kill_btn.setStyleSheet(
                f"background: {C['card_bg'].name()}; color: {C['text_lo'].name()};"
                f"border: 1px solid {C['divider'].name()}; border-radius: 3px;"
            )
            kill_btn.setToolTip("This process may be part of a live Claude session")
        kill_btn.clicked.connect(lambda _, pid=p.pid, orphan=p.is_orphan: self._kill_one(pid, orphan))
        self._table.setItemWidget(item, 5, kill_btn)

    # ── Click behavior ───────────────────────────────────────

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        pid = item.data(0, Qt.ItemDataRole.UserRole)
        if pid is None:
            return
        proc = next((p for p in self._processes if p.pid == pid), None)
        if not proc:
            return
        # Show full command + origin info in the info bar
        status = "ORPHAN (safe to kill)" if proc.is_orphan else "ACTIVE SESSION"
        ports = f" | Ports: {', '.join(str(x) for x in proc.listening_ports)}" if proc.listening_ports else ""
        self._info_bar.setText(
            f"[{status}]  PID {proc.pid}  |  {proc.exe_path}{ports}\n"
            f"$ {proc.cmdline_str}"
        )
        self._info_bar.setVisible(True)

    # ── Actions ──────────────────────────────────────────────

    def _kill_one(self, pid: int, is_orphan: bool) -> None:
        if not is_orphan:
            # Confirm before killing active session processes
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.warning(
                self, "Kill Active Process?",
                "This process may be part of a live Claude Code session.\n"
                "Are you sure you want to kill it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self._app.do_kill(pid)
        self._info_bar.setVisible(False)
        self._refresh()

    def _kill_all_orphans(self) -> None:
        orphans = [p for p in self._processes if p.is_orphan]
        if not orphans:
            return
        from crawlspace.ui.kill_dialog import KillAllDialog
        dlg = KillAllDialog(len(orphans), parent=self)
        dlg.exec()
        if dlg.confirmed:
            for p in orphans:
                self._app.do_kill(p.pid)
            self._refresh()

    def _refresh(self) -> None:
        self._app.scanner.scan_once()

    def _context_menu(self, pos) -> None:
        item = self._table.itemAt(pos)
        if not item:
            return
        pid = item.data(0, Qt.ItemDataRole.UserRole)
        proc = next((p for p in self._processes if p.pid == pid), None)
        if not proc:
            return

        menu = QMenu(self)
        menu.addAction("Kill").triggered.connect(
            lambda: self._kill_one(pid, proc.is_orphan))
        menu.addAction("Kill Tree").triggered.connect(
            lambda: (self._app.do_kill_tree(pid), self._refresh()))
        menu.addSeparator()
        menu.addAction("Copy PID").triggered.connect(
            lambda: QApplication.clipboard().setText(str(pid)))
        menu.addAction("Copy Command").triggered.connect(
            lambda: QApplication.clipboard().setText(proc.cmdline_str))
        menu.addAction("Copy Path").triggered.connect(
            lambda: QApplication.clipboard().setText(proc.exe_path))
        menu.exec(QCursor.pos())

    # ── Settings ─────────────────────────────────────────────

    def _open_settings(self) -> None:
        from crawlspace.ui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self._config, self._title_bar._anim, parent=self)
        dlg.exec()

    # ── Window management ────────────────────────────────────

    def _close_to_tray(self) -> None:
        self._config.set_many({
            "window_x": self.x(), "window_y": self.y(),
            "window_w": self.width(), "window_h": self.height(),
        })
        self.hide()

    def closeEvent(self, event) -> None:
        self._close_to_tray()
        event.ignore()

    def show_and_raise(self) -> None:
        """Show, raise, and activate."""
        self.show()
        self.raise_()
        self.activateWindow()

    # ── Edge resize for frameless window ─────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._hit_edge(event.position())
            if edge:
                self._resize_edge = edge
                self._resize_start = event.globalPosition().toPoint()
                self._resize_geo = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._resize_edge and self._resize_start:
            delta = event.globalPosition().toPoint() - self._resize_start
            geo = self._resize_geo.__class__(self._resize_geo)
            e = self._resize_edge
            if "r" in e:
                geo.setRight(self._resize_geo.right() + delta.x())
            if "b" in e:
                geo.setBottom(self._resize_geo.bottom() + delta.y())
            if "l" in e:
                geo.setLeft(self._resize_geo.left() + delta.x())
            if "t" in e:
                geo.setTop(self._resize_geo.top() + delta.y())
            if geo.width() >= self.minimumWidth() and geo.height() >= self.minimumHeight():
                self.setGeometry(geo)
            event.accept()
            return
        # Update cursor on hover
        edge = self._hit_edge(event.position())
        if edge:
            cursors = {
                "r": Qt.CursorShape.SizeHorCursor,
                "l": Qt.CursorShape.SizeHorCursor,
                "b": Qt.CursorShape.SizeVerCursor,
                "t": Qt.CursorShape.SizeVerCursor,
                "rb": Qt.CursorShape.SizeFDiagCursor,
                "lb": Qt.CursorShape.SizeBDiagCursor,
                "rt": Qt.CursorShape.SizeBDiagCursor,
                "lt": Qt.CursorShape.SizeFDiagCursor,
            }
            self.setCursor(cursors.get(edge, Qt.CursorShape.ArrowCursor))
        else:
            self.unsetCursor()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._resize_edge:
            self._resize_edge = ""
            self._resize_start = None
            self._resize_geo = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _hit_edge(self, pos) -> str:
        m = 5
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        edge = ""
        if x <= m:
            edge += "l"
        elif x >= w - m:
            edge += "r"
        if y <= m:
            edge += "t"
        elif y >= h - m:
            edge += "b"
        return edge
