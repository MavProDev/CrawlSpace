"""Build CrawlSpace into a single .exe via PyInstaller."""

import PyInstaller.__main__
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

PyInstaller.__main__.run([
    "crawlspace/main.py",
    "--onefile",
    "--noconsole",
    "--name=CrawlSpace",
    "--icon=assets/crawldad.ico",
    "--add-data=assets/crawldad.ico;assets",
    "--clean",
])
