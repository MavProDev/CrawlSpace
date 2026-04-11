from dataclasses import dataclass, field


@dataclass
class ProcessInfo:
    """Data model for a detected dev process."""
    pid: int
    name: str
    cmdline: list[str] = field(default_factory=list)
    ppid: int = 0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    create_time: float = 0.0
    uptime_seconds: float = 0.0
    uptime_human: str = ""
    status: str = ""
    username: str = ""
    category: str = "other"
    exe_path: str = ""
    children: list[int] = field(default_factory=list)
    orphan_score: float = 0.0
    listening_ports: list[int] = field(default_factory=list)

    @property
    def cmdline_str(self) -> str:
        """Full command line as a single string."""
        return " ".join(self.cmdline)

    @property
    def cmdline_short(self) -> str:
        """Command line truncated to 60 chars."""
        full = self.cmdline_str
        return full[:57] + "..." if len(full) > 60 else full
