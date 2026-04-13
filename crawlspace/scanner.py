"""CrawlSpace — background process scanner with orphan detection."""

import time
import psutil
from PyQt6.QtCore import QThread, pyqtSignal
from crawlspace.process_info import ProcessInfo
from crawlspace.categories import classify_process, is_dev_process
from crawlspace.constants import EXCLUDE_PROCESSES
from crawlspace.utils.platform import self_pid

# Names that indicate a live coding session (shell / AI tool)
_SESSION_NAMES = {
    "claude", "codex", "claude-code", "bash", "sh", "zsh",
    "cmd", "powershell", "pwsh", "conhost", "windowsterminal", "wt",
    "code", "cursor", "windsurf",
}


class ScannerThread(QThread):
    """Background thread that scans for dev processes and detects orphans."""

    processes_updated = pyqtSignal(list)
    process_arrived = pyqtSignal(object)
    process_departed = pyqtSignal(object)

    def __init__(self, interval_ms: int = 5000,
                 whitelist_paths: list[str] | None = None) -> None:
        super().__init__()
        self._interval_ms = interval_ms
        self._running = True
        self._previous_pids: set[int] = set()
        self._previous_map: dict[int, ProcessInfo] = {}
        self._whitelist_paths = [p.lower() for p in (whitelist_paths or [])]
        self._self_pid = self_pid()
        # Cache cwd per PID — a process's cwd rarely changes, so fetch once
        # and reuse on subsequent scans. Keyed by (pid, create_time) to avoid
        # PID recycling giving us stale paths.
        self._cwd_cache: dict[tuple[int, float], str] = {}

    def run(self) -> None:
        while self._running:
            try:
                processes = self._scan()
                self.processes_updated.emit(processes)
                current_pids = {p.pid for p in processes}
                for p in processes:
                    if p.pid not in self._previous_pids:
                        self.process_arrived.emit(p)
                for pid in self._previous_pids - current_pids:
                    old = self._previous_map.get(pid)
                    if old:
                        self.process_departed.emit(old)
                self._previous_pids = current_pids
                self._previous_map = {p.pid: p for p in processes}
                # Prune cwd cache for processes that vanished
                live_keys = {(p.pid, p.create_time) for p in processes}
                self._cwd_cache = {k: v for k, v in self._cwd_cache.items()
                                   if k in live_keys}
            except Exception as e:
                print(f"[Scanner] Error: {e}")
            # Sleep in small chunks so stop() is responsive
            for _ in range(self._interval_ms // 100):
                if not self._running:
                    return
                self.msleep(100)

    def _scan(self) -> list[ProcessInfo]:
        results = []
        now = time.time()
        attrs = ['pid', 'name', 'cmdline', 'ppid', 'create_time',
                 'status', 'username', 'cpu_percent', 'memory_info', 'exe']
        for proc in psutil.process_iter(attrs=attrs):
            try:
                info = proc.info
                pid = info['pid']
                if pid == self._self_pid:
                    continue
                name = info.get('name', '') or ''
                cmdline = info.get('cmdline') or []
                if not is_dev_process(name, cmdline):
                    continue
                name_lower = name.lower().replace(".exe", "")
                if name_lower in EXCLUDE_PROCESSES:
                    continue
                # Skip CrawlSpace's own processes
                cmdline_joined = " ".join(cmdline).lower()
                if "crawlspace" in cmdline_joined:
                    continue
                exe_path = info.get('exe', '') or ''
                if self._is_whitelisted(exe_path):
                    continue
                create_time = info.get('create_time', 0) or 0
                uptime = max(0, now - create_time) if create_time else 0
                mem_info = info.get('memory_info')
                memory_mb = round(mem_info.rss / (1024 * 1024), 1) if mem_info else 0.0
                cpu = info.get('cpu_percent', 0.0) or 0.0
                ppid = info.get('ppid', 0) or 0

                pi = ProcessInfo(
                    pid=pid, name=name, cmdline=cmdline,
                    ppid=ppid,
                    cpu_percent=cpu, memory_mb=memory_mb,
                    create_time=create_time, uptime_seconds=uptime,
                    uptime_human=self._format_uptime(uptime),
                    status=info.get('status', '') or '',
                    username=info.get('username', '') or '',
                    category=classify_process(name, cmdline),
                    exe_path=exe_path,
                )

                # Detect orphan status by walking the parent chain
                is_orphan, parent_chain = self._check_orphan(pid, ppid)
                pi.is_orphan = is_orphan
                pi.parent_chain = parent_chain

                # Working directory — cached per (pid, create_time) to avoid
                # per-scan syscall while surviving PID recycling
                cache_key = (pid, create_time)
                cwd = self._cwd_cache.get(cache_key)
                if cwd is None:
                    try:
                        cwd = psutil.Process(pid).cwd() or ""
                    except (psutil.NoSuchProcess, psutil.AccessDenied,
                            psutil.ZombieProcess):
                        cwd = ""
                    self._cwd_cache[cache_key] = cwd
                pi.cwd = cwd

                # Orphan score — higher = more likely a dead ghost
                # Actual orphans (parent dead) always rank above active session procs.
                # Within each group, longer uptime + lower CPU = higher ghost score.
                uptime_hours = uptime / 3600
                cpu_activity = min(cpu / 100.0, 1.0)
                base = uptime_hours * 0.5 + (1.0 - cpu_activity) * 0.3
                pi.orphan_score = round(base + (10.0 if is_orphan else 0.0), 2)
                results.append(pi)
            except (psutil.NoSuchProcess, psutil.AccessDenied,
                    psutil.ZombieProcess):
                continue
            except Exception:
                continue
        return results

    @staticmethod
    def _check_orphan(pid: int, ppid: int) -> tuple[bool, str]:
        """Walk parent chain to determine if process is orphaned.

        Returns (is_orphan, parent_description).
        - Orphan: parent process is dead or chain leads nowhere
        - Active: parent chain leads to a live shell/claude session
        """
        chain = []
        current_ppid = ppid
        visited = {pid}
        for _ in range(10):  # max depth to avoid loops
            if current_ppid in visited or current_ppid <= 1:
                break
            visited.add(current_ppid)
            try:
                parent = psutil.Process(current_ppid)
                pname = parent.name().lower().replace(".exe", "")
                chain.append(pname)
                if pname in _SESSION_NAMES:
                    # Parent is a live session — NOT orphaned
                    return False, " > ".join(reversed(chain))
                current_ppid = parent.ppid()
            except (psutil.NoSuchProcess, psutil.AccessDenied,
                    psutil.ZombieProcess):
                # Parent is dead — this IS an orphan
                return True, "parent exited"
            except Exception:
                return True, "unknown"
        # Chain exhausted without finding a session — treat as orphan
        if chain:
            return True, " > ".join(reversed(chain))
        return True, "no parent"

    def _is_whitelisted(self, exe_path: str) -> bool:
        if not exe_path:
            return False
        lower = exe_path.lower()
        return any(lower.startswith(wp) for wp in self._whitelist_paths)

    @staticmethod
    def _format_uptime(seconds: float) -> str:
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m"
        elif seconds < 86400:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            return f"{h}h {m}m"
        else:
            d = int(seconds // 86400)
            h = int((seconds % 86400) // 3600)
            return f"{d}d {h}h"

    def stop(self) -> None:
        self._running = False

    def set_interval(self, ms: int) -> None:
        self._interval_ms = ms

    def set_whitelist(self, paths: list[str]) -> None:
        self._whitelist_paths = [p.lower() for p in paths]

    def scan_once(self) -> list[ProcessInfo]:
        """Synchronous single scan for immediate refresh."""
        return self._scan()
