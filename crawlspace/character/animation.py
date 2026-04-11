"""Animation controller for bounce/pulse counters and FPS management."""

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from crawlspace.constants import (
    BOUNCE_INCREMENT, PULSE_INCREMENT, PULSE_INCREMENT_BORED,
    TICK_ACTIVE, TICK_IDLE, TICK_TOAST,
)


class AnimationController(QObject):
    """Manages animation counters and frame timing."""
    frame_tick = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bounce: float = 0.0
        self._pulse: float = 0.0
        self._bored: bool = False
        self._timer = QTimer(self)
        self._timer.setInterval(TICK_ACTIVE)
        self._timer.timeout.connect(self._tick)

    @property
    def bounce(self) -> float:
        return self._bounce

    @property
    def pulse(self) -> float:
        return self._pulse

    def _tick(self) -> None:
        self._bounce += BOUNCE_INCREMENT
        self._pulse += PULSE_INCREMENT_BORED if self._bored else PULSE_INCREMENT
        self.frame_tick.emit()

    def start(self) -> None:
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def set_active(self) -> None:
        self._timer.setInterval(TICK_ACTIVE)
        self._bored = False

    def set_idle(self) -> None:
        self._timer.setInterval(TICK_IDLE)

    def set_toast_fps(self) -> None:
        self._timer.setInterval(TICK_TOAST)

    def set_bored(self, bored: bool) -> None:
        self._bored = bored

    @property
    def is_running(self) -> bool:
        return self._timer.isActive()
