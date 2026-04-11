"""CrawlSpace — process table with flat/tree views, inline bars, context menu."""

from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QWidget, QHBoxLayout, QLabel, QMenu,
    QApplication, QHeaderView, QStyledItemDelegate, QStyle,
)
from PyQt6.QtCore import pyqtSignal, Qt, QRectF
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QBrush, QPen, QAction, QCursor,
)

from crawlspace.constants import C, FONTS, COMMON_PORTS, make_font
from crawlspace.categories import CATEGORY_LABELS, CATEGORY_ORDER
from crawlspace.process_info import ProcessInfo
from crawlspace.utils.colors import uptime_color


# Column indices
COL_CHECK = 0
COL_CAT = 1
COL_NAME = 2
COL_PID = 3
COL_CPU = 4
COL_MEM = 5
COL_UPTIME = 6
COL_STATUS = 7
COL_ACTIONS = 8

_CAT_ICONS = {
    "python": "Py", "node": "JS", "devtool": "DT",
    "infrastructure": "If", "other": "Ot", "unknown": "?",
}

_HEADERS = ["", "Cat", "Name", "PID", "CPU %", "Memory", "Uptime", "Status", ""]
_COL_WIDTHS = [30, 36, 200, 60, 70, 80, 80, 70, 40]


class InlineBarDelegate(QStyledItemDelegate):
    """Draws a tiny colored bar behind CPU% and Memory values."""

    def paint(self, painter: QPainter, option, index) -> None:
        super().paint(painter, option, index)
        col = index.column()
        if col not in (COL_CPU, COL_MEM):
            return
        value = index.data(Qt.ItemDataRole.UserRole)
        if value is None:
            return
        value = float(value)
        if col == COL_CPU:
            frac = min(value / 100.0, 1.0)
            color = C["green"] if frac < 0.5 else (C["amber"] if frac < 0.8 else C["red"])
        else:
            frac = min(value / 1024.0, 1.0)
            color = C["green"] if frac < 0.3 else (C["amber"] if frac < 0.6 else C["red"])
        rect = option.rect
        bar_h = 3
        bar_y = rect.bottom() - bar_h - 1
        bar_w = int((rect.width() - 8) * frac)
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 80)))
        painter.drawRect(rect.x() + 4, bar_y, rect.width() - 8, bar_h)
        painter.setBrush(QBrush(color))
        painter.drawRect(rect.x() + 4, bar_y, bar_w, bar_h)
        painter.restore()


class ProcessTable(QTreeWidget):
    """Process list supporting flat (grouped) and tree (parent-child) views."""

    process_selected = pyqtSignal(object)         # ProcessInfo or None
    kill_requested = pyqtSignal(int)              # PID
    kill_tree_requested = pyqtSignal(int)         # PID
    suspend_requested = pyqtSignal(int)           # PID
    resume_requested = pyqtSignal(int)            # PID
    selection_changed_pids = pyqtSignal(list)     # list[int] of checked PIDs

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._mode = "flat"
        self._processes: list[ProcessInfo] = []
        self._tree_map: dict[int, list[int]] = {}
        self._pid_items: dict[int, QTreeWidgetItem] = {}
        self._checked_pids: set[int] = set()
        self._search_text = ""
        self._category_filter = "all"
        self._selected_pid: int | None = None

        self.setHeaderLabels(_HEADERS)
        self.setColumnCount(len(_HEADERS))
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(False)
        self.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)
        self.setIndentation(20)
        self.setSortingEnabled(True)
        self.setItemDelegate(InlineBarDelegate(self))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemClicked.connect(self._on_item_clicked)

        header = self.header()
        for i, w in enumerate(_COL_WIDTHS):
            self.setColumnWidth(i, w)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(COL_NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_CHECK, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(COL_CAT, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(COL_ACTIONS, QHeaderView.ResizeMode.Fixed)

    # ── Public API ───────────────────────────────────────────

    def set_mode(self, mode: str) -> None:
        """Switch between 'flat' and 'tree' view."""
        self._mode = mode
        self._rebuild()

    def set_search(self, text: str) -> None:
        """Set the live search filter."""
        self._search_text = text.lower()
        self._rebuild()

    def set_category_filter(self, category: str) -> None:
        """Filter to a specific category or 'all'."""
        self._category_filter = category
        self._rebuild()

    def update_processes(self, processes: list[ProcessInfo],
                         tree_map: dict[int, list[int]]) -> None:
        """Update the full process list and rebuild the view."""
        self._processes = processes
        self._tree_map = tree_map
        self._rebuild()

    def get_checked_pids(self) -> list[int]:
        """Return list of checked PIDs."""
        return list(self._checked_pids)

    def select_all(self) -> None:
        """Check all visible process rows."""
        self._checked_pids = {p.pid for p in self._filtered_processes()}
        self._rebuild()
        self._emit_selection()

    def deselect_all(self) -> None:
        """Uncheck all rows."""
        self._checked_pids.clear()
        self._rebuild()
        self._emit_selection()

    # ── Filtering ────────────────────────────────────────────

    def _filtered_processes(self) -> list[ProcessInfo]:
        procs = self._processes
        if self._category_filter != "all":
            procs = [p for p in procs if p.category == self._category_filter]
        if self._search_text:
            s = self._search_text
            procs = [p for p in procs if (
                s in p.name.lower() or
                s in str(p.pid) or
                s in p.cmdline_str.lower() or
                any(s in str(port) for port in p.listening_ports)
            )]
        return procs

    # ── Build ────────────────────────────────────────────────

    def _rebuild(self) -> None:
        self.clear()
        self._pid_items.clear()
        filtered = self._filtered_processes()

        if self._mode == "flat":
            self._build_flat(filtered)
        else:
            self._build_tree(filtered)

    def _build_flat(self, processes: list[ProcessInfo]) -> None:
        """Flat view: rows grouped by category with collapsible headers."""
        self.setRootIsDecorated(True)
        by_cat: dict[str, list[ProcessInfo]] = {}
        for p in processes:
            by_cat.setdefault(p.category, []).append(p)

        for cat_key in CATEGORY_ORDER:
            cat_procs = by_cat.get(cat_key, [])
            if not cat_procs:
                continue
            label = CATEGORY_LABELS.get(cat_key, cat_key.title())
            header_item = QTreeWidgetItem(self)
            header_item.setText(COL_NAME, f"{label} ({len(cat_procs)})")
            header_item.setFont(COL_NAME, make_font(FONTS["label_bold"]))
            header_item.setForeground(COL_NAME, C["coral"])
            header_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            header_item.setExpanded(True)
            header_item.setFirstColumnSpanned(True)

            for p in sorted(cat_procs, key=lambda x: x.name.lower()):
                child = self._make_item(p, header_item)
                self._pid_items[p.pid] = child

    def _build_tree(self, processes: list[ProcessInfo]) -> None:
        """Tree view: parent-child hierarchy."""
        self.setRootIsDecorated(True)
        pid_map = {p.pid: p for p in processes}
        pid_set = {p.pid for p in processes}

        roots = [p for p in processes if p.ppid not in pid_set]

        def _add_children(parent_item: QTreeWidgetItem, parent_pid: int) -> None:
            child_pids = self._tree_map.get(parent_pid, [])
            for cpid in child_pids:
                cp = pid_map.get(cpid)
                if cp is None:
                    continue
                child_item = self._make_item(cp, parent_item)
                self._pid_items[cpid] = child_item
                _add_children(child_item, cpid)

        for root in sorted(roots, key=lambda x: x.name.lower()):
            root_item = self._make_item(root, self)
            root_item.setExpanded(True)
            self._pid_items[root.pid] = root_item
            _add_children(root_item, root.pid)

    def _make_item(self, proc: ProcessInfo,
                   parent) -> QTreeWidgetItem:
        item = QTreeWidgetItem(parent)

        # Checkbox
        item.setCheckState(COL_CHECK,
                           Qt.CheckState.Checked if proc.pid in self._checked_pids
                           else Qt.CheckState.Unchecked)

        # Category icon
        item.setText(COL_CAT, _CAT_ICONS.get(proc.category, "?"))
        item.setTextAlignment(COL_CAT, Qt.AlignmentFlag.AlignCenter)

        # Name
        item.setText(COL_NAME, proc.name)
        item.setFont(COL_NAME, make_font(FONTS["body"]))

        # PID
        item.setText(COL_PID, str(proc.pid))
        item.setTextAlignment(COL_PID, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        item.setFont(COL_PID, make_font(FONTS["mono"]))

        # CPU %
        item.setText(COL_CPU, f"{proc.cpu_percent:.1f}")
        item.setData(COL_CPU, Qt.ItemDataRole.UserRole, proc.cpu_percent)
        item.setTextAlignment(COL_CPU, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Memory
        item.setText(COL_MEM, f"{proc.memory_mb:.1f} MB")
        item.setData(COL_MEM, Qt.ItemDataRole.UserRole, proc.memory_mb)
        item.setTextAlignment(COL_MEM, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Uptime (age-colored)
        item.setText(COL_UPTIME, proc.uptime_human)
        item.setForeground(COL_UPTIME, uptime_color(proc.uptime_seconds))
        if proc.uptime_seconds >= 86400:
            item.setText(COL_UPTIME, f"! {proc.uptime_human}")
        item.setTextAlignment(COL_UPTIME, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Status
        item.setText(COL_STATUS, proc.status)

        # Port highlighting
        zombie_ports = [p for p in proc.listening_ports if p in COMMON_PORTS]
        if zombie_ports:
            for col in range(self.columnCount()):
                item.setBackground(col, QBrush(QColor(C["amber"].red(), C["amber"].green(), C["amber"].blue(), 20)))

        # Store PID for retrieval
        item.setData(COL_NAME, Qt.ItemDataRole.UserRole, proc.pid)

        return item

    # ── Events ───────────────────────────────────────────────

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        pid = item.data(COL_NAME, Qt.ItemDataRole.UserRole)
        if pid is None:
            return  # category header

        # Handle checkbox toggle
        if column == COL_CHECK:
            if item.checkState(COL_CHECK) == Qt.CheckState.Checked:
                self._checked_pids.add(pid)
            else:
                self._checked_pids.discard(pid)
            self._emit_selection()
            return

        # Select row for detail panel
        proc = next((p for p in self._processes if p.pid == pid), None)
        if proc:
            self._selected_pid = pid
            self.process_selected.emit(proc)

    def _emit_selection(self) -> None:
        self.selection_changed_pids.emit(list(self._checked_pids))

    def _show_context_menu(self, pos) -> None:
        item = self.itemAt(pos)
        if item is None:
            return
        pid = item.data(COL_NAME, Qt.ItemDataRole.UserRole)
        if pid is None:
            return
        proc = next((p for p in self._processes if p.pid == pid), None)
        if proc is None:
            return

        menu = QMenu(self)

        act_kill = menu.addAction("Kill Process")
        act_kill.triggered.connect(lambda: self.kill_requested.emit(pid))
        act_kill_tree = menu.addAction("Kill Process Tree")
        act_kill_tree.triggered.connect(lambda: self.kill_tree_requested.emit(pid))

        menu.addSeparator()

        if proc.status == "stopped":
            act_resume = menu.addAction("Resume")
            act_resume.triggered.connect(lambda: self.resume_requested.emit(pid))
        else:
            act_suspend = menu.addAction("Suspend")
            act_suspend.triggered.connect(lambda: self.suspend_requested.emit(pid))

        menu.addSeparator()

        act_copy_pid = menu.addAction("Copy PID")
        act_copy_pid.triggered.connect(
            lambda: QApplication.clipboard().setText(str(pid))
        )

        act_copy_cmd = menu.addAction("Copy Command Line")
        act_copy_cmd.triggered.connect(
            lambda: QApplication.clipboard().setText(proc.cmdline_str)
        )

        act_copy_path = menu.addAction("Copy Process Path")
        act_copy_path.triggered.connect(
            lambda: QApplication.clipboard().setText(proc.exe_path)
        )

        act_copy_summary = menu.addAction("Copy Summary")
        act_copy_summary.triggered.connect(lambda: self._copy_summary(proc))

        menu.addSeparator()

        act_taskmgr = menu.addAction("Open in Task Manager")
        act_taskmgr.triggered.connect(self._open_taskmgr)

        menu.addSeparator()

        act_select_cat = menu.addAction(f"Select All in {CATEGORY_LABELS.get(proc.category, proc.category)}")
        act_select_cat.triggered.connect(lambda: self._select_category(proc.category))

        menu.exec(QCursor.pos())

    def _copy_summary(self, proc: ProcessInfo) -> None:
        port_str = ", ".join(str(p) for p in proc.listening_ports) if proc.listening_ports else "none"
        summary = (
            f"{proc.name} (PID {proc.pid}) | {proc.cmdline_short} | "
            f"CPU: {proc.cpu_percent:.1f}% | RAM: {proc.memory_mb:.0f} MB | "
            f"Uptime: {proc.uptime_human} | Port: {port_str}"
        )
        QApplication.clipboard().setText(summary)

    @staticmethod
    def _open_taskmgr() -> None:
        import subprocess
        try:
            subprocess.Popen(["taskmgr.exe"])
        except Exception:
            pass

    def _select_category(self, category: str) -> None:
        for p in self._processes:
            if p.category == category:
                self._checked_pids.add(p.pid)
        self._rebuild()
        self._emit_selection()

    def keyPressEvent(self, event) -> None:
        """Handle keyboard shortcuts within the table."""
        key = event.key()
        if key == Qt.Key.Key_Space:
            item = self.currentItem()
            if item:
                pid = item.data(COL_NAME, Qt.ItemDataRole.UserRole)
                if pid is not None:
                    if pid in self._checked_pids:
                        self._checked_pids.discard(pid)
                        item.setCheckState(COL_CHECK, Qt.CheckState.Unchecked)
                    else:
                        self._checked_pids.add(pid)
                        item.setCheckState(COL_CHECK, Qt.CheckState.Checked)
                    self._emit_selection()
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            item = self.currentItem()
            if item:
                pid = item.data(COL_NAME, Qt.ItemDataRole.UserRole)
                proc = next((p for p in self._processes if p.pid == pid), None)
                if proc:
                    self.process_selected.emit(proc)
            return
        super().keyPressEvent(event)
