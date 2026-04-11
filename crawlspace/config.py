"""CrawlSpace — thread-safe JSON config manager with atomic writes."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

CONFIG_DIR = Path.home() / ".crawlspace"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history.json"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _atomic_write(path: Path, data: dict) -> None:
    """Write *data* as JSON to *path* atomically via a temp file + os.replace()."""
    path = Path(path)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        # Clean up the temp file so we don't leave debris behind.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Theme helper
# ---------------------------------------------------------------------------


def apply_theme(name: str) -> None:
    """Swap the live colour palette to the named theme (falls back to 'coral')."""
    from PyQt6.QtGui import QColor

    from crawlspace.constants import C, THEMES

    theme = THEMES.get(name) or THEMES.get("coral", {})
    if not theme:
        return

    accent = theme.get("accent")
    accent_light = theme.get("accent_light")

    if accent is not None:
        C["coral"] = QColor(*accent) if isinstance(accent, tuple) else QColor(accent)
    if accent_light is not None:
        C["coral_light"] = (
            QColor(*accent_light)
            if isinstance(accent_light, tuple)
            else QColor(accent_light)
        )


# ---------------------------------------------------------------------------
# ConfigManager
# ---------------------------------------------------------------------------


class ConfigManager:
    """Persistent, thread-safe application configuration backed by JSON."""

    _DEBOUNCE_SECONDS: float = 5.0

    def __init__(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._config: dict[str, Any] = {}
        self._dirty: bool = False
        self._last_save_time: float = 0.0
        self._load()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load config from disk, merging over DEFAULT_CONFIG defaults."""
        from crawlspace.constants import DEFAULT_CONFIG

        base = DEFAULT_CONFIG.copy()
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, encoding="utf-8") as fh:
                    on_disk = json.load(fh)
                base.update(on_disk)
            except (json.JSONDecodeError, OSError):
                # Corrupt / unreadable — fall back to defaults silently.
                pass
        self._config = base
        self._dirty = False

    def _save_locked(self, *, force: bool = False) -> None:
        """Write config to disk (call while holding self._lock).

        Skips the write if the last save was less than *_DEBOUNCE_SECONDS* ago,
        unless *force* is True.
        """
        now = time.monotonic()
        if not force and (now - self._last_save_time) < self._DEBOUNCE_SECONDS:
            # Too soon — just stay dirty; caller will flush later.
            self._dirty = True
            return
        snapshot = dict(self._config)
        _atomic_write(CONFIG_FILE, snapshot)
        self._last_save_time = now
        self._dirty = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for *key*, or *default* if the key is absent."""
        with self._lock:
            return self._config.get(key, default)

    def set(self, key: str, value: Any, save_now: bool = True) -> None:
        """Set *key* = *value* and optionally persist immediately."""
        with self._lock:
            self._config[key] = value
            self._dirty = True
            if save_now:
                self._save_locked()

    def set_many(self, updates: dict[str, Any]) -> None:
        """Apply all key/value pairs in *updates* and persist."""
        with self._lock:
            self._config.update(updates)
            self._dirty = True
            self._save_locked()

    def save(self) -> None:
        """Persist config (debounced — may be skipped if saved recently)."""
        with self._lock:
            self._save_locked()

    def flush(self) -> None:
        """Force an immediate save regardless of debounce window."""
        with self._lock:
            self._save_locked(force=True)
