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
    "--hidden-import=crawlspace.ui.splash",
    "--hidden-import=crawlspace.ui.onboarding",
    "--hidden-import=crawlspace.ui.main_window",
    "--hidden-import=crawlspace.ui.title_bar",
    "--hidden-import=crawlspace.ui.admin_banner",
    "--hidden-import=crawlspace.ui.toolbar",
    "--hidden-import=crawlspace.ui.process_table",
    "--hidden-import=crawlspace.ui.detail_panel",
    "--hidden-import=crawlspace.ui.bulk_action_bar",
    "--hidden-import=crawlspace.ui.kill_dialog",
    "--hidden-import=crawlspace.ui.history_panel",
    "--hidden-import=crawlspace.ui.overlay",
    "--hidden-import=crawlspace.ui.toast",
    "--hidden-import=crawlspace.ui.tray",
    "--hidden-import=crawlspace.ui.settings_dialog",
    "--hidden-import=crawlspace.utils.startup",
    "--hidden-import=crawlspace.utils.updater",
    "--hidden-import=crawlspace.utils.sounds",
    "--clean",
])
