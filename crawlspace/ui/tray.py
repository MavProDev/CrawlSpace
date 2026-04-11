"""System tray icon with context menu and dynamic badge."""

from pathlib import Path
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QPainter, QColor, QPixmap, QIcon, QFont, QPen, QBrush
from PyQt6.QtCore import Qt, QRectF

from crawlspace.constants import C
from crawlspace.utils.colors import badge_color


def make_tray(app, crawlspace_app, config, scanner):
    """Create and configure the system tray icon."""
    # Load icon
    icon_path = Path(__file__).parent.parent.parent / "assets" / "crawldad.ico"
    if not icon_path.exists():
        # Fallback: try relative to package
        icon_path = Path(__file__).parent.parent / ".." / "assets" / "crawldad.ico"
    base_icon = QIcon(str(icon_path.resolve()))
    tray = QSystemTrayIcon(base_icon, app)

    _state = {"count": 0, "base_pixmap": base_icon.pixmap(32, 32)}

    def _update_badge(processes):
        count = len(processes)
        _state["count"] = count
        pix = QPixmap(_state["base_pixmap"])
        if count > 0:
            p = QPainter(pix)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            color = badge_color(count)
            badge_size = 14
            bx = pix.width() - badge_size - 1
            by = 1
            p.setBrush(QBrush(color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(bx, by, badge_size, badge_size))
            p.setPen(QPen(QColor(255, 255, 255)))
            p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            text = str(count) if count <= 99 else "99+"
            p.drawText(QRectF(bx, by, badge_size, badge_size),
                       Qt.AlignmentFlag.AlignCenter, text)
            p.end()
        tray.setIcon(QIcon(pix))
        suffix = "es" if count != 1 else ""
        tray.setToolTip(f"CrawlSpace \u2014 {count} dev process{suffix}")

    scanner.processes_updated.connect(_update_badge)

    # Context menu
    menu = QMenu()
    menu.setStyleSheet(
        "QMenu{background:#121216;color:#f0ece8;border:1px solid #2c2c34;"
        "padding:4px;font-size:12px;}"
        "QMenu::item:selected{background:#d97757;}"
    )
    menu.addAction("Open CrawlSpace")  # placeholder for main window
    menu.addSeparator()
    menu.addAction("Quick Scan").triggered.connect(
        lambda: scanner.scan_once()
    )

    # Quick Kill submenu
    _quick_kill_menu = menu.addMenu("Quick Kill")
    _quick_kill_menu.setStyleSheet(menu.styleSheet())

    def _update_quick_kill(processes):
        _quick_kill_menu.clear()
        sorted_procs = sorted(processes, key=lambda p: p.orphan_score, reverse=True)[:3]
        if not sorted_procs:
            act = _quick_kill_menu.addAction("No processes")
            act.setEnabled(False)
            return
        for proc in sorted_procs:
            action = _quick_kill_menu.addAction(
                f"{proc.name} (PID {proc.pid}) \u2014 {proc.uptime_human}"
            )
            pid = proc.pid
            action.triggered.connect(
                lambda checked, p=pid: _do_quick_kill(p)
            )

    def _do_quick_kill(pid):
        crawlspace_app.do_kill(pid)
        scanner.scan_once()

    scanner.processes_updated.connect(_update_quick_kill)

    menu.addSeparator()
    menu.addAction("Settings...")  # placeholder
    menu.addSeparator()
    menu.addAction("Quit").triggered.connect(app.quit)

    tray.setContextMenu(menu)
    tray.setToolTip("CrawlSpace \u2014 scanning...")

    # Left-click opens main window (placeholder)
    tray.activated.connect(
        lambda reason: None  # will wire to main_window.show() in Phase 4
        if reason == QSystemTrayIcon.ActivationReason.Trigger else None
    )

    tray.show()
    return tray
