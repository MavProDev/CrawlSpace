"""CrawlSpace — bulk action bar shown when processes are selected."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from crawlspace.constants import C, FONTS, make_font


class BulkActionBar(QWidget):
    """Bar displayed when 1+ processes are selected. Shows count and action buttons."""

    kill_selected = pyqtSignal()
    kill_selected_trees = pyqtSignal()
    suspend_selected = pyqtSignal()
    deselect_all = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(44)
        self.setVisible(False)
        self.setStyleSheet(
            f"background-color: {C['card_bg'].name()};"
            f"border-top: 1px solid {C['divider'].name()};"
            f"border-bottom: 1px solid {C['divider'].name()};"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(10)

        # Left: selection info
        self._count_label = QLabel("0 selected")
        self._count_label.setFont(make_font(FONTS["body_bold"]))
        self._count_label.setStyleSheet(f"color: {C['text_hi'].name()}; border: none;")
        layout.addWidget(self._count_label)

        layout.addStretch()

        # Center: kill buttons
        btn_kill = QPushButton("Kill Selected")
        btn_kill.setObjectName("red_btn")
        btn_kill.setFixedHeight(28)
        btn_kill.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_kill.setFont(make_font(FONTS["label_bold"]))
        btn_kill.setToolTip("Kill all checked processes (Ctrl+K)")
        btn_kill.clicked.connect(self.kill_selected.emit)
        layout.addWidget(btn_kill)

        btn_kill_tree = QPushButton("Kill Selected Trees")
        btn_kill_tree.setFixedHeight(28)
        btn_kill_tree.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_kill_tree.setFont(make_font(FONTS["label_bold"]))
        btn_kill_tree.setToolTip("Kill selected processes and all children (Ctrl+Shift+K)")
        btn_kill_tree.clicked.connect(self.kill_selected_trees.emit)
        layout.addWidget(btn_kill_tree)

        layout.addStretch()

        # Right: suspend + deselect
        btn_suspend = QPushButton("Suspend Selected")
        btn_suspend.setFixedHeight(28)
        btn_suspend.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_suspend.setFont(make_font(FONTS["label_bold"]))
        btn_suspend.setToolTip("Freeze selected processes without killing")
        btn_suspend.clicked.connect(self.suspend_selected.emit)
        layout.addWidget(btn_suspend)

        btn_deselect = QPushButton("Deselect All")
        btn_deselect.setObjectName("flat_btn")
        btn_deselect.setFixedHeight(28)
        btn_deselect.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_deselect.setFont(make_font(FONTS["label_bold"]))
        btn_deselect.setToolTip("Uncheck all processes (Ctrl+D)")
        btn_deselect.clicked.connect(self.deselect_all.emit)
        layout.addWidget(btn_deselect)

    def update_selection(self, count: int, total_mb: float) -> None:
        """Update the selection count display and show/hide bar."""
        if count == 0:
            self.setVisible(False)
            return
        self.setVisible(True)
        self._count_label.setText(
            f"{count} selected ({total_mb:.0f} MB)"
        )
