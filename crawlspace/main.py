"""CrawlSpace entry point."""

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
from crawlspace.ui.tray import make_tray


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if not acquire_lock():
        print("CrawlSpace is already running.")
        sys.exit(1)

    config = ConfigManager()
    apply_theme(config.get("color_theme", "coral"))

    admin = is_admin()
    history = EventHistory()
    history.prune(days=7)
    emotions = EmotionStateMachine()
    anim = AnimationController()

    scanner = ScannerThread(
        interval_ms=config.get("scan_interval_seconds", 5) * 1000,
        whitelist_paths=config.get("whitelist_paths", []),
    )

    # Wire scanner signals to history and emotions
    def _on_arrived(proc):
        history.append("PROCESS_DETECTED", proc.pid, proc.name,
                       proc.category, proc.cmdline_short)
        emotions.on_process_detected()

    def _on_departed(proc):
        history.append("PROCESS_DIED", proc.pid, proc.name,
                       proc.category, proc.cmdline_short)

    def _on_updated(processes):
        if not processes:
            emotions.on_no_processes()
        else:
            emotions.on_process_detected()

    scanner.processes_updated.connect(_on_updated)
    scanner.process_arrived.connect(_on_arrived)
    scanner.process_departed.connect(_on_departed)

    # Create app controller
    crawlspace_app = CrawlSpaceApp(config, scanner, history, emotions, anim, admin)

    # Create tray
    tray = make_tray(app, crawlspace_app, config, scanner)

    # Start
    scanner.start()
    anim.start()

    banner = (
        "+======================================+\n"
        f"|   CrawlSpace v{__version__:<22s}|\n"
        f"|   Admin: {'Yes' if admin else 'No':<29s}|\n"
        "|   @ReelDad / MavPro Group LLC       |\n"
        "+======================================+"
    )
    print(banner)

    def cleanup():
        scanner.stop()
        anim.stop()
        scanner.wait(2000)
        history.save()
        config.flush()
        release_lock()

    app.aboutToQuit.connect(cleanup)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
