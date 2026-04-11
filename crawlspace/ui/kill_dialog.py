"""CrawlSpace — kill confirmation dialogs."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QScrollArea, QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from crawlspace.constants import C, FONTS, make_font
from crawlspace.process_info import ProcessInfo


class KillConfirmDialog(QDialog):
    """Confirmation dialog before killing processes."""

    def __init__(self, processes: list[ProcessInfo], kill_tree: bool = False,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._confirmed = False
        self.setWindowTitle("Confirm Kill")
        self.setFixedSize(420, 340)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title
        action = "Kill Tree" if kill_tree else "Kill"
        title = QLabel(f"{action} {len(processes)} process{'es' if len(processes) != 1 else ''}?")
        title.setFont(make_font(FONTS["heading"]))
        title.setStyleSheet(f"color: {C['red'].name()};")
        layout.addWidget(title)

        # Subtitle
        sub = QLabel("The following processes will be terminated:")
        sub.setFont(make_font(FONTS["label"]))
        sub.setStyleSheet(f"color: {C['text_md'].name()};")
        layout.addWidget(sub)

        # Process list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(160)
        scroll.setStyleSheet(
            f"QScrollArea {{ background: {C['card_bg'].name()}; border: 1px solid {C['divider'].name()}; border-radius: 4px; }}"
        )
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(8, 8, 8, 8)
        list_layout.setSpacing(4)

        for p in processes:
            row = QLabel(f"{p.name}  (PID {p.pid})  —  {p.uptime_human}  —  {p.memory_mb:.0f} MB")
            row.setFont(make_font(FONTS["mono"]))
            row.setStyleSheet(f"color: {C['text_hi'].name()};")
            list_layout.addWidget(row)

        list_layout.addStretch()
        scroll.setWidget(list_widget)
        layout.addWidget(scroll)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel = QPushButton("Cancel")
        cancel.setFixedSize(90, 32)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)

        confirm = QPushButton(action)
        confirm.setFixedSize(110, 32)
        confirm.setObjectName("red_btn")
        confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm.clicked.connect(self._do_confirm)
        btn_row.addWidget(confirm)

        layout.addLayout(btn_row)

    def _do_confirm(self) -> None:
        self._confirmed = True
        self.accept()

    @property
    def confirmed(self) -> bool:
        """Whether the user confirmed the kill."""
        return self._confirmed

    def paintEvent(self, event) -> None:
        """Paint rounded dark background."""
        from PyQt6.QtGui import QPainter, QPainterPath, QBrush, QPen
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        p.setPen(QPen(C["divider"], 1))
        p.setBrush(QBrush(C["notch_bg"]))
        p.drawPath(path)
        p.end()


class KillAllDialog(QDialog):
    """Kill All confirmation requiring the user to type 'KILL'."""

    def __init__(self, count: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._confirmed = False
        self.setWindowTitle("Kill All Processes")
        self.setFixedSize(400, 260)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Warning icon + title
        title = QLabel(f"⚠  Kill ALL {count} dev processes?")
        title.setFont(make_font(FONTS["heading"]))
        title.setStyleSheet(f"color: {C['red'].name()};")
        layout.addWidget(title)

        warn = QLabel(
            "This will terminate every detected dev process.\n"
            "This action cannot be undone."
        )
        warn.setFont(make_font(FONTS["body"]))
        warn.setStyleSheet(f"color: {C['text_md'].name()};")
        warn.setWordWrap(True)
        layout.addWidget(warn)

        # Type KILL input
        prompt = QLabel('Type "KILL" to confirm:')
        prompt.setFont(make_font(FONTS["label_bold"]))
        prompt.setStyleSheet(f"color: {C['amber'].name()};")
        layout.addWidget(prompt)

        self._input = QLineEdit()
        self._input.setPlaceholderText("KILL")
        self._input.setFont(make_font(FONTS["mono"]))
        self._input.setFixedHeight(32)
        self._input.textChanged.connect(self._check_input)
        layout.addWidget(self._input)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel = QPushButton("Cancel")
        cancel.setFixedSize(90, 32)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)

        self._confirm_btn = QPushButton("Kill All")
        self._confirm_btn.setFixedSize(110, 32)
        self._confirm_btn.setObjectName("red_btn")
        self._confirm_btn.setEnabled(False)
        self._confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._confirm_btn.clicked.connect(self._do_confirm)
        btn_row.addWidget(self._confirm_btn)

        layout.addLayout(btn_row)

    def _check_input(self, text: str) -> None:
        self._confirm_btn.setEnabled(text.strip() == "KILL")

    def _do_confirm(self) -> None:
        if self._input.text().strip() == "KILL":
            self._confirmed = True
            self.accept()

    @property
    def confirmed(self) -> bool:
        """Whether the user confirmed Kill All."""
        return self._confirmed

    def paintEvent(self, event) -> None:
        """Paint rounded dark background."""
        from PyQt6.QtGui import QPainter, QPainterPath, QBrush, QPen
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        p.setPen(QPen(C["divider"], 1))
        p.setBrush(QBrush(C["notch_bg"]))
        p.drawPath(path)
        p.end()
