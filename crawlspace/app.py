"""CrawlSpace application controller."""

from crawlspace.config import ConfigManager
from crawlspace.scanner import ScannerThread
from crawlspace.history import EventHistory
from crawlspace.character.emotions import EmotionStateMachine
from crawlspace.character.animation import AnimationController
from crawlspace.killer import kill_process, kill_tree, suspend_process, resume_process
from crawlspace.process_tree import build_tree


class CrawlSpaceApp:
    """Main application controller. Orchestrates all components."""

    def __init__(self, config: ConfigManager, scanner: ScannerThread,
                 history: EventHistory, emotions: EmotionStateMachine,
                 anim: AnimationController, is_admin: bool):
        self.config = config
        self.scanner = scanner
        self.history = history
        self.emotions = emotions
        self.anim = anim
        self.is_admin = is_admin
        self._processes: list = []
        self._tree: dict = {}

        scanner.processes_updated.connect(self._on_processes_updated)

    def _on_processes_updated(self, processes):
        self._processes = processes
        self._tree = build_tree(processes)

    @property
    def processes(self):
        return self._processes

    @property
    def tree(self):
        return self._tree

    def do_kill(self, pid: int) -> tuple[bool, str]:
        """Kill a single process."""
        timeout = self.config.get("kill_timeout_seconds", 3)
        success, msg = kill_process(pid, timeout)
        event_type = "PROCESS_KILLED" if success else "KILL_FAILED"
        proc = next((p for p in self._processes if p.pid == pid), None)
        name = proc.name if proc else f"PID {pid}"
        category = proc.category if proc else ""
        self.history.append(event_type, pid, name, category, msg)
        if success:
            self.emotions.trigger_happy(3.0)
        else:
            self.emotions.trigger_sob(3.0)
        return success, msg

    def do_kill_tree(self, pid: int) -> tuple[int, int, list[str]]:
        """Kill a process and all its descendants."""
        timeout = self.config.get("kill_timeout_seconds", 3)
        killed, failed, messages = kill_tree(pid, self._tree, timeout)
        for msg in messages:
            is_kill = "Killed" in msg or "Force-killed" in msg or "already gone" in msg
            self.history.append(
                "PROCESS_KILLED" if is_kill else "KILL_FAILED",
                pid, "", "", msg
            )
        if failed == 0:
            self.emotions.trigger_happy(3.0)
        else:
            self.emotions.trigger_sob(3.0)
        return killed, failed, messages

    def do_suspend(self, pid: int) -> tuple[bool, str]:
        """Suspend a process."""
        success, msg = suspend_process(pid)
        if success:
            proc = next((p for p in self._processes if p.pid == pid), None)
            self.history.append("PROCESS_SUSPENDED", pid,
                               proc.name if proc else "", "", msg)
        return success, msg

    def do_resume(self, pid: int) -> tuple[bool, str]:
        """Resume a suspended process."""
        success, msg = resume_process(pid)
        if success:
            proc = next((p for p in self._processes if p.pid == pid), None)
            self.history.append("PROCESS_RESUMED", pid,
                               proc.name if proc else "", "", msg)
        return success, msg
