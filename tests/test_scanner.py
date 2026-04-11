import pytest
from crawlspace.scanner import ScannerThread


class TestFormatUptime:
    def test_format_seconds(self):
        assert ScannerThread._format_uptime(45) == "45s"

    def test_format_minutes(self):
        assert ScannerThread._format_uptime(300) == "5m"

    def test_format_hours(self):
        assert ScannerThread._format_uptime(7380) == "2h 3m"

    def test_format_days(self):
        assert ScannerThread._format_uptime(90000) == "1d 1h"
