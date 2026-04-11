"""CrawlSpace -- admin privilege warning banner."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from crawlspace.constants import C
from crawlspace.utils.platform import relaunch_as_admin


class AdminBanner(QWidget):
    """Amber warning bar shown when the app is not running as admin."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(36)
        self._build_ui()
        self.hide()

    def _build_ui(self) -> None:
        """Construct the banner layout and apply styles."""
        amber = C["amber"]
        text_hi = C["text_hi"]

        self.setStyleSheet(
            f"background: rgba({amber.red()},{amber.green()},{amber.blue()},38);"
            f"border-left: 3px solid rgb({amber.red()},{amber.green()},{amber.blue()});"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 6, 0)
        layout.setSpacing(8)

        # Warning icon
        icon_label = QLabel("\u26a0")
        icon_label.setStyleSheet(
            f"color: rgb({amber.red()},{amber.green()},{amber.blue()});"
            "font-size: 14pt; background: transparent; border: none;"
        )
        icon_label.setFixedWidth(22)
        layout.addWidget(icon_label)

        # Warning text
        text_label = QLabel(
            "Running without admin privileges. Some processes may not be killable."
        )
        text_label.setStyleSheet(
            f"color: rgb({text_hi.red()},{text_hi.green()},{text_hi.blue()});"
            "font-size: 9pt; background: transparent; border: none;"
        )
        layout.addWidget(text_label, stretch=1)

        # Restart as Admin button
        restart_btn = QPushButton("Restart as Admin")
        restart_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        restart_btn.setStyleSheet(
            f"background: rgb({amber.red()},{amber.green()},{amber.blue()});"
            "color: #000000; font-size: 8pt; font-weight: bold;"
            "border: none; border-radius: 3px; padding: 3px 10px;"
        )
        restart_btn.clicked.connect(relaunch_as_admin)
        layout.addWidget(restart_btn)

        # Dismiss button
        dismiss_btn = QPushButton("\u2715")
        dismiss_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dismiss_btn.setFixedSize(22, 22)
        dismiss_btn.setStyleSheet(
            f"color: rgb({amber.red()},{amber.green()},{amber.blue()});"
            "background: transparent; border: none; font-size: 12pt;"
        )
        dismiss_btn.clicked.connect(self.hide)
        layout.addWidget(dismiss_btn)

    def set_visible_if_needed(self, is_admin: bool) -> None:
        """Show the banner only when the app lacks admin privileges."""
        self.setVisible(not is_admin)
