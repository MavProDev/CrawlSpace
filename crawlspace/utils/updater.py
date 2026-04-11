"""Background thread to check GitHub releases for updates."""

import json
import urllib.request
from typing import Tuple

from PyQt6.QtCore import QThread, pyqtSignal

RELEASES_URL: str = "https://api.github.com/repos/MavProDev/CrawlSpace/releases/latest"
REQUEST_TIMEOUT: int = 10


def _parse_version(version: str) -> Tuple[int, ...]:
    """Parse a version string like 'v1.2.3' or '1.2.3' into a comparable tuple."""
    cleaned = version.lstrip("vV")
    return tuple(int(part) for part in cleaned.split("."))


class UpdateChecker(QThread):
    """Thread that checks GitHub for a newer release."""

    update_available = pyqtSignal(str, str)

    def __init__(self, current_version: str) -> None:
        super().__init__()
        self._current_version = current_version

    def check(self) -> None:
        """Start the update check thread."""
        self.start()

    def run(self) -> None:
        """Fetch latest release from GitHub and emit signal if newer."""
        try:
            request = urllib.request.Request(
                RELEASES_URL,
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                data = json.loads(response.read().decode("utf-8"))

            latest_version: str = data.get("tag_name", "")
            download_url: str = data.get("html_url", "")

            if not latest_version:
                return

            if _parse_version(latest_version) > _parse_version(self._current_version):
                self.update_available.emit(latest_version, download_url)
        except Exception:
            pass
