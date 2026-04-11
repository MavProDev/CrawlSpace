from crawlspace.process_info import ProcessInfo


def test_default_values():
    """Create with just pid+name, verify defaults."""
    p = ProcessInfo(pid=1234, name="python")
    assert p.pid == 1234
    assert p.name == "python"
    assert p.cmdline == []
    assert p.ppid == 0
    assert p.cpu_percent == 0.0
    assert p.memory_mb == 0.0
    assert p.create_time == 0.0
    assert p.uptime_seconds == 0.0
    assert p.uptime_human == ""
    assert p.status == ""
    assert p.username == ""
    assert p.category == "other"
    assert p.exe_path == ""
    assert p.children == []
    assert p.orphan_score == 0.0
    assert p.listening_ports == []


def test_cmdline_str():
    """Verify cmdline_str joins tokens with spaces."""
    p = ProcessInfo(pid=1, name="python", cmdline=["python", "main.py", "--debug"])
    assert p.cmdline_str == "python main.py --debug"


def test_cmdline_short_truncation():
    """Verify strings longer than 60 chars are truncated with ellipsis."""
    long_cmd = ["a" * 61]
    p = ProcessInfo(pid=1, name="x", cmdline=long_cmd)
    result = p.cmdline_short
    assert len(result) == 60
    assert result.endswith("...")


def test_cmdline_short_no_truncation():
    """Verify strings 60 chars or shorter pass through unchanged."""
    short_cmd = ["a" * 60]
    p = ProcessInfo(pid=1, name="x", cmdline=short_cmd)
    assert p.cmdline_short == "a" * 60

    exact_short = ["a" * 59]
    p2 = ProcessInfo(pid=2, name="x", cmdline=exact_short)
    assert p2.cmdline_short == "a" * 59


def test_mutable_defaults_independent():
    """Two instances must not share list defaults."""
    p1 = ProcessInfo(pid=1, name="a")
    p2 = ProcessInfo(pid=2, name="b")

    p1.cmdline.append("foo")
    p1.children.append(99)
    p1.listening_ports.append(8000)

    assert p2.cmdline == []
    assert p2.children == []
    assert p2.listening_ports == []
