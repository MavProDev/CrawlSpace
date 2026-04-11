from crawlspace.constants import PROCESS_PATTERNS


def classify_process(name: str, cmdline: list[str]) -> str:
    """Classify a process by name and command line into a category."""
    name_lower = name.lower().replace(".exe", "")
    cmdline_lower = " ".join(cmdline).lower()
    for category, patterns in PROCESS_PATTERNS.items():
        for pattern in patterns:
            if pattern == name_lower:
                return category
            if pattern in cmdline_lower:
                return category
    return "unknown"


def is_dev_process(name: str, cmdline: list[str]) -> bool:
    """Return True if the process matches any known dev process pattern."""
    return classify_process(name, cmdline) != "unknown"


CATEGORY_LABELS = {
    "python": "Python",
    "node": "Node.js",
    "devtool": "Dev Tools",
    "infrastructure": "Infra",
    "other": "Other",
    "unknown": "Unknown",
}

CATEGORY_ORDER = ["python", "node", "devtool", "infrastructure", "other"]
