from crawlspace.process_info import ProcessInfo


def build_tree(processes: list[ProcessInfo]) -> dict[int, list[int]]:
    """Build a parent-to-children mapping from a flat process list."""
    pid_set = {p.pid for p in processes}
    tree: dict[int, list[int]] = {}
    for p in processes:
        if p.ppid in pid_set:
            tree.setdefault(p.ppid, []).append(p.pid)
    pid_map = {p.pid: p for p in processes}
    for parent_pid, child_pids in tree.items():
        if parent_pid in pid_map:
            pid_map[parent_pid].children = child_pids
    return tree


def resolve_tree(pid: int, tree: dict[int, list[int]]) -> list[int]:
    """Resolve all descendants of a PID in kill-safe order (deepest first).

    Returns descendants with deepest children first, so a killer iterating
    this list will terminate leaves before their parents — avoiding orphan
    re-parenting to init.
    """
    from collections import deque
    depths: dict[int, int] = {}
    queue = deque([(pid, 0)])
    visited = {pid}
    while queue:
        current, depth = queue.popleft()
        for child in tree.get(current, []):
            if child in visited:
                continue
            visited.add(child)
            depths[child] = depth + 1
            queue.append((child, depth + 1))
    # Sort descendants by depth desc (deepest first)
    return sorted(depths.keys(), key=lambda p: -depths[p])


def get_roots(processes: list[ProcessInfo]) -> list[ProcessInfo]:
    """Return processes whose parent is not in the process list."""
    pid_set = {p.pid for p in processes}
    return [p for p in processes if p.ppid not in pid_set]
