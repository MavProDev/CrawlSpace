"""System tray icon with context menu and dynamic badge."""

from pathlib import Path
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QPainter, QColor, QPixmap, QIcon, QFont, QPen, QBrush
from PyQt6.QtCore import Qt, QRectF

from crawlspace.constants import C
from crawlspace.utils.colors import badge_color


def _find_icon() -> Path:
    """Find crawldad.ico, handling both dev and PyInstaller-bundled paths."""
    import sys
    if hasattr(sys, '_MEIPASS'):
        p = Path(sys._MEIPASS) / "assets" / "crawldad.ico"
        if p.exists():
            return p
    p = Path(__file__).parent.parent.parent / "assets" / "crawldad.ico"
    return p


def make_tray(app, crawlspace_app, config, scanner, main_window=None, notch=None):
    """Create and configure the system tray icon."""
    icon_path = _find_icon()
    base_icon = QIcon(str(icon_path.resolve()))
    tray = QSystemTrayIcon(base_icon, app)

    _state = {"count": 0, "base_pixmap": base_icon.pixmap(32, 32)}

    def _update_badge(processes: list) -> None:
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
        total_mb = sum(proc.memory_mb for proc in processes)
        tray.setToolTip(f"CrawlSpace \u2014 {count} ghost process{suffix} | {total_mb:.0f} MB")

    scanner.processes_updated.connect(_update_badge)

    # Context menu
    menu = QMenu()
    menu.setStyleSheet(
        "QMenu{background:#121216;color:#f0ece8;border:1px solid #2c2c34;"
        "padding:4px;font-size:12px;}"
        "QMenu::item:selected{background:#d97757;}"
    )

    if main_window:
        menu.addAction("Open CrawlSpace").triggered.connect(main_window.show_and_raise)

    menu.addSeparator()
    menu.addAction("Quick Scan").triggered.connect(lambda: scanner.scan_once())

    # Quick Kill submenu
    _quick_kill_menu = menu.addMenu("Quick Kill")
    _quick_kill_menu.setStyleSheet(menu.styleSheet())

    def _update_quick_kill(processes: list) -> None:
        _quick_kill_menu.clear()
        sorted_procs = sorted(processes, key=lambda pr: pr.orphan_score, reverse=True)[:5]
        if not sorted_procs:
            act = _quick_kill_menu.addAction("No ghost processes")
            act.setEnabled(False)
            return
        for proc in sorted_procs:
            action = _quick_kill_menu.addAction(
                f"{proc.name} (PID {proc.pid}) \u2014 {proc.uptime_human}"
            )
            pid = proc.pid
            action.triggered.connect(
                lambda checked, target=pid: _do_quick_kill(target)
            )

    def _do_quick_kill(pid: int) -> None:
        crawlspace_app.do_kill(pid)
        scanner.scan_once()

    scanner.processes_updated.connect(_update_quick_kill)

    # Notch toggle
    if notch:
        menu.addSeparator()
        act_notch = menu.addAction("Show Notch")
        act_notch.setCheckable(True)
        act_notch.setChecked(config.get("overlay_enabled", False))

        def _toggle_notch(checked: bool) -> None:
            config.set("overlay_enabled", checked)
            if checked:
                notch.show_notch()
            else:
                notch.hide_notch()

        act_notch.triggered.connect(_toggle_notch)

    menu.addSeparator()
    def _quit() -> None:
        import os
        scanner.stop()
        scanner.wait(500)
        app.quit()
        os._exit(0)

    menu.addAction("Quit").triggered.connect(_quit)

    tray.setContextMenu(menu)
    tray.setToolTip("CrawlSpace \u2014 scanning...")

    def _on_activated(reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger and main_window:
            main_window.show_and_raise()

    tray.activated.connect(_on_activated)
    tray.show()
    return tray
