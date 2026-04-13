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
    "--hidden-import=crawlspace.ui.styles",
    "--hidden-import=crawlspace.ui.main_window",
    "--hidden-import=crawlspace.ui.title_bar",
    "--hidden-import=crawlspace.ui.admin_banner",
    "--hidden-import=crawlspace.ui.kill_dialog",
    "--hidden-import=crawlspace.ui.overlay",
    "--hidden-import=crawlspace.ui.tray",
    "--hidden-import=crawlspace.ui.settings_dialog",
    "--hidden-import=crawlspace.utils.startup",
    "--hidden-import=crawlspace.utils.updater",
    "--hidden-import=crawlspace.utils.sounds",
    "--clean",
])
