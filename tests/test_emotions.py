import time
from unittest.mock import patch
from crawlspace.character.emotions import EmotionStateMachine


def test_default_neutral(qapp):
    """Initial state is neutral."""
    em = EmotionStateMachine()
    assert em.current == "neutral"


def test_trigger_happy(qapp):
    """trigger_happy changes state."""
    em = EmotionStateMachine()
    em.trigger_happy(duration=5.0)
    assert em.current == "happy"


def test_auto_revert(qapp):
    """State reverts to neutral after duration expires."""
    em = EmotionStateMachine()
    em.trigger_happy(duration=0.05)
    assert em.current == "happy"
    time.sleep(0.1)
    assert em.current == "neutral"


def test_bored_state(qapp):
    """Enters bored after 5 min of no processes."""
    em = EmotionStateMachine()
    em._last_process_time = time.time() - 301  # simulate 5+ min ago
    em.on_no_processes()
    assert em._current == "bored"


def test_process_detected_resets_bored(qapp):
    """on_process_detected snaps out of bored."""
    em = EmotionStateMachine()
    em._current = "bored"
    em.on_process_detected()
    assert em.current == "alert"


def test_signal_emitted(qapp):
    """emotion_changed signal fires on state change."""
    em = EmotionStateMachine()
    received = []
    em.emotion_changed.connect(lambda s: received.append(s))
    em.trigger_happy(duration=5.0)
    assert received == ["happy"]
