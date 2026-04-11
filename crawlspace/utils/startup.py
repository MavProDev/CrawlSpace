"""Windows Registry management for Start with Windows feature."""

import sys
import winreg

APP_NAME: str = "CrawlSpace"
RUN_KEY: str = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"


def is_startup_enabled() -> bool:
    """Check if CrawlSpace is registered to start with Windows."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def enable_startup() -> None:
    """Add CrawlSpace to the Windows Run registry key."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, sys.executable)
    except OSError:
        pass


def disable_startup() -> None:
    """Remove CrawlSpace from the Windows Run registry key."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
    except FileNotFoundError:
        pass
    except OSError:
        pass
