"""CrawlSpace — toolbar with view toggle, category filters, search, and resource summary."""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLineEdit, QLabel, QButtonGroup,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QShortcut, QKeySequence

from crawlspace.constants import C, FONTS, make_font
from crawlspace.categories import CATEGORY_LABELS, CATEGORY_ORDER


class ToolBar(QWidget):
    """Top toolbar: view toggle, category tabs, search, refresh, resource summary."""

    view_changed = pyqtSignal(str)        # "flat" or "tree"
    category_changed = pyqtSignal(str)    # category key or "all"
    search_changed = pyqtSignal(str)      # live search text
    refresh_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(72)
        self._current_view = "flat"
        self._current_category = "all"
        self._category_counts: dict[str, int] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(8)

        # ── View toggle ──
        view_box = QHBoxLayout()
        view_box.setSpacing(0)
        self._btn_flat = QPushButton("Flat")
        self._btn_tree = QPushButton("Tree")
        for btn in (self._btn_flat, self._btn_tree):
            btn.setFixedSize(52, 26)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(make_font(FONTS["label_bold"]))
        self._btn_flat.setCheckable(True)
        self._btn_tree.setCheckable(True)
        self._btn_flat.setChecked(True)
        self._view_group = QButtonGroup(self)
        self._view_group.setExclusive(True)
        self._view_group.addButton(self._btn_flat, 0)
        self._view_group.addButton(self._btn_tree, 1)
        self._view_group.idClicked.connect(self._on_view_toggled)
        view_box.addWidget(self._btn_flat)
        view_box.addWidget(self._btn_tree)
        layout.addLayout(view_box)

        # ── Separator ──
        sep = QLabel("|")
        sep.setStyleSheet(f"color: {C['divider'].name()}; font-size: 16pt;")
        sep.setFixedWidth(16)
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sep)

        # ── Category tabs ──
        self._cat_buttons: dict[str, QPushButton] = {}
        cat_box = QHBoxLayout()
        cat_box.setSpacing(2)

        btn_all = QPushButton("All")
        btn_all.setCheckable(True)
        btn_all.setChecked(True)
        btn_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_all.setFont(make_font(FONTS["label"]))
        btn_all.setObjectName("flat_btn")
        self._cat_buttons["all"] = btn_all
        cat_box.addWidget(btn_all)

        self._cat_group = QButtonGroup(self)
        self._cat_group.setExclusive(True)
        self._cat_group.addButton(btn_all, 0)

        for i, key in enumerate(CATEGORY_ORDER, 1):
            label = CATEGORY_LABELS.get(key, key.title())
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(make_font(FONTS["label"]))
            btn.setObjectName("flat_btn")
            self._cat_buttons[key] = btn
            self._cat_group.addButton(btn, i)
            cat_box.addWidget(btn)

        self._cat_group.idClicked.connect(self._on_category_toggled)
        layout.addLayout(cat_box)

        layout.addStretch()

        # ── Search bar ──
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search name, PID, command...")
        self._search.setFixedWidth(220)
        self._search.setFixedHeight(28)
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self._search)

        # ── Refresh button ──
        btn_refresh = QPushButton("⟳")
        btn_refresh.setFixedSize(28, 28)
        btn_refresh.setToolTip("Refresh (Ctrl+R)")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setFont(QFont("Segoe UI", 12))
        btn_refresh.setObjectName("flat_btn")
        btn_refresh.clicked.connect(self.refresh_clicked.emit)
        layout.addWidget(btn_refresh)

        # ── Resource summary (second row) ──
        self._resource_label = QLabel("")
        self._resource_label.setFont(make_font(FONTS["caption"]))
        self._resource_label.setStyleSheet(f"color: {C['text_lo'].name()};")
        self._resource_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._resource_label)

        # ── Keyboard shortcut for search ──
        self._shortcut_search = QShortcut(QKeySequence("Ctrl+F"), self)
        self._shortcut_search.activated.connect(self._search.setFocus)

        self._apply_toggle_styles()

    def _on_view_toggled(self, button_id: int) -> None:
        mode = "flat" if button_id == 0 else "tree"
        self._current_view = mode
        self._apply_toggle_styles()
        self.view_changed.emit(mode)

    def _on_category_toggled(self, button_id: int) -> None:
        keys = ["all"] + CATEGORY_ORDER
        if 0 <= button_id < len(keys):
            self._current_category = keys[button_id]
            self._apply_cat_styles()
            self.category_changed.emit(self._current_category)

    def _apply_toggle_styles(self) -> None:
        coral = C["coral"].name()
        card = C["card_bg"].name()
        text = C["text_hi"].name()
        text_mid = C["text_md"].name()
        for btn, is_active in [
            (self._btn_flat, self._current_view == "flat"),
            (self._btn_tree, self._current_view == "tree"),
        ]:
            if is_active:
                btn.setStyleSheet(
                    f"background-color: {coral}; color: #ffffff; border: none;"
                    f"border-radius: 4px; font-weight: bold;"
                )
            else:
                btn.setStyleSheet(
                    f"background-color: {card}; color: {text_mid}; border: none;"
                    f"border-radius: 4px;"
                )

    def _apply_cat_styles(self) -> None:
        coral = C["coral"].name()
        for key, btn in self._cat_buttons.items():
            if key == self._current_category:
                btn.setStyleSheet(
                    f"color: {coral}; font-weight: bold; border-bottom: 2px solid {coral};"
                    f"background: transparent; border-radius: 0;"
                )
            else:
                btn.setStyleSheet("")
                btn.setObjectName("flat_btn")

    def update_counts(self, processes: list) -> None:
        """Update category tab counts and resource summary."""
        counts: dict[str, int] = {}
        total_cpu = 0.0
        total_mem = 0.0
        ports: set[int] = set()
        for p in processes:
            counts[p.category] = counts.get(p.category, 0) + 1
            total_cpu += p.cpu_percent
            total_mem += p.memory_mb
            ports.update(p.listening_ports)
        self._category_counts = counts

        # Update button labels with counts
        total = len(processes)
        self._cat_buttons["all"].setText(f"All ({total})")
        for key in CATEGORY_ORDER:
            label = CATEGORY_LABELS.get(key, key.title())
            c = counts.get(key, 0)
            self._cat_buttons[key].setText(f"{label} ({c})" if c else label)

        # Resource summary
        port_str = ", ".join(str(p) for p in sorted(ports)[:6])
        parts = [f"{total} processes", f"CPU: {total_cpu:.1f}%", f"RAM: {total_mem:.0f} MB"]
        if port_str:
            parts.append(f"Ports: {port_str}")
        self._resource_label.setText(" | ".join(parts))

    def set_view_mode(self, mode: str) -> None:
        """Set view mode programmatically."""
        if mode == "tree":
            self._btn_tree.setChecked(True)
            self._on_view_toggled(1)
        else:
            self._btn_flat.setChecked(True)
            self._on_view_toggled(0)

    def focus_search(self) -> None:
        """Focus the search bar."""
        self._search.setFocus()
        self._search.selectAll()

    @property
    def search_text(self) -> str:
        """Current search filter text."""
        return self._search.text()

    @property
    def current_category(self) -> str:
        """Currently selected category filter."""
        return self._current_category
