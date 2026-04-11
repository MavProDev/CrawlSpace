"""Emotion state machine for Crawldad character."""

import time
from PyQt6.QtCore import QObject, pyqtSignal


class EmotionStateMachine(QObject):
    """Manages Crawldad's emotional state with auto-revert and bored detection."""
    emotion_changed = pyqtSignal(str)

    STATES = {"neutral", "happy", "sad", "sob", "alert", "bored"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current: str = "neutral"
        self._revert_time: float = 0.0
        self._last_process_time: float = time.time()
        self._bored_threshold: float = 300.0  # 5 minutes

    @property
    def current(self) -> str:
        """Current emotion, checking for auto-revert."""
        self._check_revert()
        return self._current

    def trigger_happy(self, duration: float = 3.0) -> None:
        self._set("happy", duration)

    def trigger_sad(self, duration: float = 5.0) -> None:
        self._set("sad", duration)

    def trigger_sob(self, duration: float = 3.0) -> None:
        self._set("sob", duration)

    def trigger_alert(self, duration: float = 2.0) -> None:
        self._set("alert", duration)

    def on_process_detected(self) -> None:
        """Call when scanner finds processes. Resets bored timer."""
        self._last_process_time = time.time()
        if self._current == "bored":
            self._set("alert", 2.0)

    def on_no_processes(self) -> None:
        """Call when scanner finds zero processes."""
        if self._current not in ("happy", "sad", "sob", "alert"):
            elapsed = time.time() - self._last_process_time
            if elapsed >= self._bored_threshold:
                if self._current != "bored":
                    self._current = "bored"
                    self.emotion_changed.emit("bored")

    def _set(self, emotion: str, duration: float) -> None:
        self._current = emotion
        self._revert_time = time.time() + duration
        self.emotion_changed.emit(emotion)

    def _check_revert(self) -> None:
        if self._revert_time > 0 and time.time() >= self._revert_time:
            self._revert_time = 0.0
            old = self._current
            self._current = "neutral"
            if old != "neutral":
                self.emotion_changed.emit("neutral")
