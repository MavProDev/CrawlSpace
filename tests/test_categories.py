from crawlspace.categories import classify_process, is_dev_process


def test_python_by_name():
    """classify_process('python.exe', []) returns 'python'."""
    assert classify_process("python.exe", []) == "python"


def test_node_by_name():
    """classify_process('node', []) returns 'node'."""
    assert classify_process("node", []) == "node"


def test_devtool_by_cmdline():
    """classify_process matches devtool pattern in cmdline."""
    assert classify_process("someprocess", ["--", "claude", "code"]) == "devtool"


def test_unknown_process():
    """classify_process('notepad.exe', []) returns 'unknown'."""
    assert classify_process("notepad.exe", []) == "unknown"


def test_is_dev_process():
    """is_dev_process returns True for known, False for unknown."""
    assert is_dev_process("python", []) is True
    assert is_dev_process("notepad", []) is False


def test_case_insensitive():
    """classify_process('Python.EXE', []) returns 'python'."""
    assert classify_process("Python.EXE", []) == "python"


def test_uvicorn():
    """classify_process('uvicorn', ['uvicorn', 'main:app']) returns 'python'."""
    assert classify_process("uvicorn", ["uvicorn", "main:app"]) == "python"
