"""CrawlSpace — event history ring buffer with JSON persistence."""

import json
import threading
from datetime import datetime, timedelta
from collections import deque
import crawlspace.config as _cfg


class EventHistory:
    """In-memory ring buffer (200 events) with JSON persistence."""

    EVENT_TYPES = {"PROCESS_DETECTED", "PROCESS_DIED", "PROCESS_KILLED",
                   "PROCESS_SUSPENDED", "PROCESS_RESUMED", "KILL_FAILED"}

    def __init__(self, max_events: int = 200):
        self._events: deque = deque(maxlen=max_events)
        self._lock = threading.Lock()
        self._load()

    def append(self, event_type: str, pid: int, name: str,
               category: str = "", detail: str = "") -> None:
        """Append a new event to the ring buffer."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "pid": pid,
            "name": name,
            "category": category,
            "detail": detail,
        }
        with self._lock:
            self._events.append(event)

    def get_events(self, filter_type: str | None = None,
                   limit: int = 50) -> list[dict]:
        """Return events newest-first, optionally filtered by type."""
        with self._lock:
            events = list(self._events)
        if filter_type:
            events = [e for e in events if e["type"] == filter_type]
        return list(reversed(events[-limit:]))

    def save(self) -> None:
        """Persist the event buffer to disk atomically."""
        with self._lock:
            data = list(self._events)
        _cfg._atomic_write(_cfg.HISTORY_FILE, data)

    def _load(self) -> None:
        """Load persisted events from disk on startup."""
        try:
            if _cfg.HISTORY_FILE.exists():
                with open(_cfg.HISTORY_FILE) as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self._events.extend(data)
        except Exception:
            pass

    def prune(self, days: int = 7) -> int:
        """Remove events older than *days*. Returns count of removed events."""
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        with self._lock:
            before = len(self._events)
            self._events = deque(
                (e for e in self._events if e.get("timestamp", "") >= cutoff_str),
                maxlen=self._events.maxlen,
            )
            return before - len(self._events)

    def clear(self) -> None:
        """Remove all events from the buffer."""
        with self._lock:
            self._events.clear()

    @property
    def count(self) -> int:
        """Return the current number of events in the buffer."""
        with self._lock:
            return len(self._events)
