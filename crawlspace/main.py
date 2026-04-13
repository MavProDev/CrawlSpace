"""CrawlSpace entry point — lightweight ghost process killer."""

import os
import sys
from PyQt6.QtWidgets import QApplication

from crawlspace import __version__
from crawlspace.config import ConfigManager
from crawlspace.utils.colors import apply_theme
from crawlspace.utils.singleton import acquire_lock, release_lock
from crawlspace.utils.platform import is_admin
from crawlspace.scanner import ScannerThread
from crawlspace.history import EventHistory
from crawlspace.character.emotions import EmotionStateMachine
from crawlspace.character.animation import AnimationController
from crawlspace.app import CrawlSpaceApp
from crawlspace.ui.styles import build_stylesheet
from crawlspace.ui.tray import make_tray
from crawlspace.ui.main_window import MainWindow
from crawlspace.ui.overlay import Notch


def main() -> None:
    """Application entry point."""
    # Set AppUserModelID so Windows taskbar shows our icon, not Python's
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MavPro.CrawlSpace.1")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if not acquire_lock():
        print("CrawlSpace is already running.")
        sys.exit(1)

    # Set app icon (taskbar + window icon) to Craw
    from pathlib import Path
    from PyQt6.QtGui import QIcon
    ico = Path(__file__).parent.parent / "assets" / "crawldad.ico"
    if ico.exists():
        app.setWindowIcon(QIcon(str(ico)))

    config = ConfigManager()
    apply_theme(config.get("color_theme", "coral"))
    app.setStyleSheet(build_stylesheet())

    admin = is_admin()
    history = EventHistory()
    history.prune(days=7)
    emotions = EmotionStateMachine()
    anim = AnimationController()

    scanner = ScannerThread(
        interval_ms=config.get("scan_interval_seconds", 5) * 1000,
        whitelist_paths=config.get("whitelist_paths", []),
    )

    # Wire scanner → history + emotions
    scanner.process_arrived.connect(
        lambda p: history.append("PROCESS_DETECTED", p.pid, p.name, p.category, p.cmdline_short)
    )
    scanner.process_departed.connect(
        lambda p: history.append("PROCESS_DIED", p.pid, p.name, p.category, p.cmdline_short)
    )
    scanner.processes_updated.connect(
        lambda procs: emotions.on_process_detected() if procs else emotions.on_no_processes()
    )

    # App controller
    crawlspace_app = CrawlSpaceApp(config, scanner, history, emotions, anim, admin)

    # Main window
    main_window = MainWindow(crawlspace_app, config, anim, emotions)
    scanner.processes_updated.connect(main_window.on_processes_updated)

    # Notch (edge-docked widget)
    notch = Notch(anim, emotions, config)
    notch.set_on_click(main_window.show_and_raise)

    def _update_notch(processes) -> None:
        notch.update_data(len(processes), sum(p.memory_mb for p in processes))

    scanner.processes_updated.connect(_update_notch)

    # Tray icon
    tray = make_tray(app, crawlspace_app, config, scanner, main_window, notch)

    # Start
    scanner.start()
    anim.start()

    # Show notch if enabled, main window if not minimized
    if config.get("overlay_enabled", False):
        notch.show_notch()
    if not config.get("start_minimized", False):
        main_window.show_and_raise()

    print(f"CrawlSpace v{__version__} | Admin: {'Yes' if admin else 'No'}")

    def cleanup() -> None:
        scanner.stop()
        anim.stop()
        scanner.wait(500)
        history.save()
        config.flush()
        release_lock()
        os._exit(0)

    app.aboutToQuit.connect(cleanup)

    # Run event loop — then guarantee death no matter what
    try:
        app.exec()
    finally:
        os._exit(0)


if __name__ == "__main__":
    main()
