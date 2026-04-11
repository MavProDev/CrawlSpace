"""Procedural sound generation using Windows built-in beep."""

import threading
import winsound

KILL_FREQ: int = 800
KILL_DURATION: int = 80

DETECT_FREQ: int = 600
DETECT_DURATION: int = 60

ERROR_FREQ: int = 300
ERROR_DURATION: int = 150


def play_sound(frequency: int = 440, duration_ms: int = 100) -> None:
    """Generate and play a sine wave beep without blocking the UI."""
    def _beep() -> None:
        try:
            winsound.Beep(frequency, duration_ms)
        except Exception:
            pass

    thread = threading.Thread(target=_beep, daemon=True)
    thread.start()


def sound_kill() -> None:
    """Play a short high beep for process kill events."""
    play_sound(KILL_FREQ, KILL_DURATION)


def sound_detect() -> None:
    """Play a medium beep for process detection events."""
    play_sound(DETECT_FREQ, DETECT_DURATION)


def sound_error() -> None:
    """Play a low beep for error events."""
    play_sound(ERROR_FREQ, ERROR_DURATION)
