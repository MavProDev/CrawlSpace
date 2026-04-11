import pytest
from crawlspace.process_info import ProcessInfo
from crawlspace.process_tree import build_tree, resolve_tree, get_roots


def make_proc(pid: int, ppid: int) -> ProcessInfo:
    return ProcessInfo(pid=pid, name=f"proc_{pid}", ppid=ppid)


@pytest.fixture
def sample_processes():
    """
    Tree structure:
      100 (ppid=1)  <-- root
        200 (ppid=100)
          400 (ppid=200)  <-- grandchild
        300 (ppid=100)
    """
    return [
        make_proc(100, 1),
        make_proc(200, 100),
        make_proc(300, 100),
        make_proc(400, 200),
    ]


def test_build_tree(sample_processes):
    tree = build_tree(sample_processes)
    assert set(tree[100]) == {200, 300}
    assert tree[200] == [400]
    assert 300 not in tree  # 300 has no children in the list
    assert 400 not in tree


def test_resolve_tree(sample_processes):
    tree = build_tree(sample_processes)
    descendants = resolve_tree(100, tree)
    assert set(descendants) == {200, 300, 400}


def test_resolve_tree_no_children(sample_processes):
    tree = build_tree(sample_processes)
    assert resolve_tree(400, tree) == []


def test_get_roots(sample_processes):
    roots = get_roots(sample_processes)
    assert len(roots) == 1
    assert roots[0].pid == 100


def test_circular_reference():
    """Verify resolve_tree handles circular references without infinite loop."""
    processes = [
        make_proc(100, 1),
        make_proc(200, 100),
        make_proc(400, 200),
        make_proc(500, 400),
        make_proc(600, 500),
    ]
    tree = build_tree(processes)
    # Manually inject a cycle: 600 -> 500 (500 is already an ancestor of 600)
    tree.setdefault(600, []).append(500)
    # Should not loop infinitely
    result = resolve_tree(100, tree)
    assert 500 in result
    assert 600 in result
