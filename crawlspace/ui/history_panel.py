"""CrawlSpace — collapsible event history panel."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QComboBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from crawlspace.constants import C, FONTS, make_font
from crawlspace.history import EventHistory


_EVENT_COLORS = {
    "PROCESS_DETECTED": C["coral"],
    "PROCESS_DIED":     C["text_md"],
    "PROCESS_KILLED":   C["green"],
    "KILL_FAILED":      C["red"],
    "PROCESS_SUSPENDED": C["amber"],
    "PROCESS_RESUMED":  C["green"],
}

_EVENT_LABELS = {
    "PROCESS_DETECTED": "Detected",
    "PROCESS_DIED":     "Died",
    "PROCESS_KILLED":   "Killed",
    "KILL_FAILED":      "Kill Failed",
    "PROCESS_SUSPENDED": "Suspended",
    "PROCESS_RESUMED":  "Resumed",
}


class HistoryPanel(QWidget):
    """Collapsible event history panel at bottom of main window."""

    def __init__(self, history: EventHistory, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._history = history
        self._collapsed = True
        self._filter_type: str | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header row (always visible)
        header = QWidget()
        header.setFixedHeight(30)
        header.setStyleSheet(
            f"background-color: {C['card_bg'].name()};"
            f"border-top: 1px solid {C['divider'].name()};"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        header_layout.setSpacing(8)

        self._toggle_btn = QPushButton("▸ History")
        self._toggle_btn.setObjectName("flat_btn")
        self._toggle_btn.setFont(make_font(FONTS["label_bold"]))
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.clicked.connect(self._toggle)
        header_layout.addWidget(self._toggle_btn)

        self._count_label = QLabel("0 events")
        self._count_label.setFont(make_font(FONTS["caption"]))
        self._count_label.setStyleSheet(f"color: {C['text_lo'].name()};")
        header_layout.addWidget(self._count_label)

        header_layout.addStretch()

        # Filter dropdown
        self._filter_combo = QComboBox()
        self._filter_combo.setFixedSize(120, 22)
        self._filter_combo.addItem("All Events", None)
        for event_type, label in _EVENT_LABELS.items():
            self._filter_combo.addItem(label, event_type)
        self._filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self._filter_combo)

        outer.addWidget(header)

        # Collapsible content
        self._content = QScrollArea()
        self._content.setWidgetResizable(True)
        self._content.setMaximumHeight(180)
        self._content.setVisible(False)
        self._content.setStyleSheet(f"background-color: {C['notch_bg'].name()}; border: none;")

        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(12, 6, 12, 6)
        self._list_layout.setSpacing(2)
        self._list_layout.addStretch()
        self._content.setWidget(self._list_widget)

        outer.addWidget(self._content)

    def _toggle(self) -> None:
        self._collapsed = not self._collapsed
        self._content.setVisible(not self._collapsed)
        arrow = "▸" if self._collapsed else "▾"
        self._toggle_btn.setText(f"{arrow} History")
        if not self._collapsed:
            self.refresh()

    def _on_filter_changed(self, index: int) -> None:
        self._filter_type = self._filter_combo.currentData()
        self.refresh()

    def refresh(self) -> None:
        """Reload events from history buffer."""
        events = self._history.get_events(filter_type=self._filter_type, limit=50)
        self._count_label.setText(f"{self._history.count} events")

        # Clear existing rows
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Build rows
        for event in events:
            row = self._make_row(event)
            self._list_layout.insertWidget(self._list_layout.count() - 1, row)

    def _make_row(self, event: dict) -> QWidget:
        row = QWidget()
        row.setFixedHeight(22)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Timestamp
        ts = event.get("timestamp", "")[:19].replace("T", " ")
        ts_label = QLabel(ts)
        ts_label.setFont(make_font(FONTS["tiny"]))
        ts_label.setStyleSheet(f"color: {C['text_lo'].name()};")
        ts_label.setFixedWidth(120)
        layout.addWidget(ts_label)

        # Event type badge
        event_type = event.get("type", "")
        color = _EVENT_COLORS.get(event_type, C["text_md"])
        type_label = QLabel(_EVENT_LABELS.get(event_type, event_type))
        type_label.setFont(make_font(FONTS["tiny_bold"]))
        type_label.setStyleSheet(
            f"color: #ffffff; background-color: {color.name()};"
            f"border-radius: 3px; padding: 1px 5px;"
        )
        type_label.setFixedWidth(70)
        type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(type_label)

        # Process name + PID
        name = event.get("name", "")
        pid = event.get("pid", "")
        info = QLabel(f"{name} (PID {pid})")
        info.setFont(make_font(FONTS["caption"]))
        info.setStyleSheet(f"color: {C['text_hi'].name()};")
        layout.addWidget(info)

        # Detail
        detail = event.get("detail", "")
        if detail:
            detail_label = QLabel(detail[:60])
            detail_label.setFont(make_font(FONTS["caption"]))
            detail_label.setStyleSheet(f"color: {C['text_lo'].name()};")
            layout.addWidget(detail_label)

        layout.addStretch()
        return row
