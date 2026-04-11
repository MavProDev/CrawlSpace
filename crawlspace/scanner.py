import os
import time
import psutil
from PyQt6.QtCore import QThread, pyqtSignal
from crawlspace.process_info import ProcessInfo
from crawlspace.categories import classify_process, is_dev_process
from crawlspace.utils.platform import self_pid

class ScannerThread(QThread):
    processes_updated = pyqtSignal(list)      # list[ProcessInfo]
    process_arrived = pyqtSignal(object)      # ProcessInfo
    process_departed = pyqtSignal(object)     # ProcessInfo

    def __init__(self, interval_ms: int = 5000, whitelist_paths: list[str] | None = None):
        super().__init__()
        self._interval_ms = interval_ms
        self._running = True
        self._previous_pids: set[int] = set()
        self._previous_map: dict[int, ProcessInfo] = {}
        self._whitelist_paths = [p.lower() for p in (whitelist_paths or [])]
        self._self_pid = self_pid()

    def run(self):
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
            except Exception as e:
                print(f"[Scanner] Error: {e}")
            self.msleep(self._interval_ms)

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
                exe_path = info.get('exe', '') or ''
                if self._is_whitelisted(exe_path):
                    continue
                create_time = info.get('create_time', 0) or 0
                uptime = max(0, now - create_time) if create_time else 0
                mem_info = info.get('memory_info')
                memory_mb = round(mem_info.rss / (1024 * 1024), 1) if mem_info else 0.0
                cpu = info.get('cpu_percent', 0.0) or 0.0
                pi = ProcessInfo(
                    pid=pid, name=name, cmdline=cmdline,
                    ppid=info.get('ppid', 0) or 0,
                    cpu_percent=cpu, memory_mb=memory_mb,
                    create_time=create_time, uptime_seconds=uptime,
                    uptime_human=self._format_uptime(uptime),
                    status=info.get('status', '') or '',
                    username=info.get('username', '') or '',
                    category=classify_process(name, cmdline),
                    exe_path=exe_path,
                )
                uptime_hours = uptime / 3600
                cpu_idle = 1.0 if cpu < 0.1 else 0.0
                pi.orphan_score = round(uptime_hours * 0.4 + cpu_idle * 0.3, 2)
                results.append(pi)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception:
                continue
        return results

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

    def stop(self):
        self._running = False

    def set_interval(self, ms: int):
        self._interval_ms = ms

    def set_whitelist(self, paths: list[str]):
        self._whitelist_paths = [p.lower() for p in paths]

    def scan_once(self) -> list[ProcessInfo]:
        """Synchronous single scan for testing or immediate refresh."""
        return self._scan()
