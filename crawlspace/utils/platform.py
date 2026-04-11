import os
import sys
import ctypes

def is_admin() -> bool:
    """Check if running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def relaunch_as_admin() -> None:
    """Re-launch this process with UAC elevation, then exit."""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit(0)

def self_pid() -> int:
    """Return this process's PID."""
    return os.getpid()

def get_screen_geometry(widget=None):
    """Get the screen geometry for the screen containing widget, or primary screen."""
    from PyQt6.QtWidgets import QApplication
    if widget is not None:
        screen = QApplication.screenAt(widget.geometry().center())
        if screen:
            return screen.geometry()
    screen = QApplication.primaryScreen()
    return screen.geometry() if screen else None

def get_current_screen(widget):
    """Return the QScreen that contains the majority of widget's area."""
    from PyQt6.QtWidgets import QApplication
    screen = QApplication.screenAt(widget.geometry().center())
    return screen if screen else QApplication.primaryScreen()
