import psutil
from crawlspace.process_tree import resolve_tree


def kill_process(pid: int, timeout: int = 3) -> tuple[bool, str]:
    """Kill a single process. SIGTERM first, then SIGKILL after timeout."""
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        proc.terminate()
        try:
            proc.wait(timeout=timeout)
            return True, f"Killed {name} (PID {pid})"
        except psutil.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)
            return True, f"Force-killed {name} (PID {pid})"
    except psutil.NoSuchProcess:
        return True, f"Process {pid} already gone"
    except psutil.AccessDenied:
        return False, f"Access denied for PID {pid}. Run as admin."
    except Exception as e:
        return False, f"Failed to kill PID {pid}: {e}"


def kill_tree(pid: int, tree: dict[int, list[int]], timeout: int = 3) -> tuple[int, int, list[str]]:
    """Kill a process and all descendants. Deepest children first, then parent."""
    descendants = resolve_tree(pid, tree)  # already in deepest-first order
    all_pids = descendants + [pid]
    killed = 0
    failed = 0
    messages = []
    for p in all_pids:
        success, msg = kill_process(p, timeout)
        messages.append(msg)
        if success:
            killed += 1
        else:
            failed += 1
    return killed, failed, messages


def suspend_process(pid: int) -> tuple[bool, str]:
    """Suspend (freeze) a process."""
    try:
        proc = psutil.Process(pid)
        proc.suspend()
        return True, f"Suspended {proc.name()} (PID {pid})"
    except psutil.NoSuchProcess:
        return True, f"Process {pid} already gone"
    except psutil.AccessDenied:
        return False, f"Access denied for PID {pid}. Run as admin."
    except Exception as e:
        return False, f"Failed to suspend PID {pid}: {e}"


def resume_process(pid: int) -> tuple[bool, str]:
    """Resume a suspended process."""
    try:
        proc = psutil.Process(pid)
        proc.resume()
        return True, f"Resumed {proc.name()} (PID {pid})"
    except psutil.NoSuchProcess:
        return True, f"Process {pid} already gone"
    except psutil.AccessDenied:
        return False, f"Access denied for PID {pid}. Run as admin."
    except Exception as e:
        return False, f"Failed to resume PID {pid}: {e}"
