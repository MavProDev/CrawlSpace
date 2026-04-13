# CrawlSpace

**Hunting zombies in your dev environment.**

A lightweight Windows desktop daemon that detects and kills **ghost processes** — orphaned dev servers, runaway scripts, and zombie builds left behind by AI coding tools like Claude Code, Cursor, and Codex. Sits quietly in your system tray until you need it.

## Download. Run. Done.

1. Grab `CrawlSpace.exe` from the [latest release](https://github.com/MavProDev/CrawlSpace/releases/latest)
2. Double-click to run — no installer, no dependencies
3. Craw appears in your system tray

## What Makes It Different

Normal task managers show you *every* process. CrawlSpace shows you **only the ones you care about**: orphaned dev processes whose parent terminal or IDE already exited.

It walks each detected process's parent chain up to 10 levels. If the chain ends at a live shell, Claude Code, or VS Code session, the process is marked **Active** and hidden by default. If the parent is dead, it's a true **Orphan** — safe to kill, and one click does it.

## Features

**Ghost detection**
- Scans for 90+ known dev process patterns: Python, Node, npm, pnpm, Vite, Next, Django, FastAPI, Docker, ngrok, Cargo, Go, Ruby, Rails, and more
- Walks the parent chain to distinguish orphans (parent dead → safe to kill) from active session processes (parent still alive → warns before killing)
- Excludes active Claude Code / bash / cmd / PowerShell / VS Code processes from the list entirely
- Self-exclusion: CrawlSpace never shows its own process

**Kill**
- One-click kill per row — orphans get a red button, active processes get a greyed one with a confirmation warning
- **Kill All Orphans** button with typed "KILL" confirmation
- Quick Kill submenu in the tray for the top zombie processes
- Kill tree (children-first, BFS depth-ordered) via right-click menu

**See where they came from**
- Command column shows `[ProjectName] command args` — project name derived from the process's working directory
- Click any row for the full working directory path, full command line, and orphan status in the info bar
- Hover the name column for a tooltip showing the cwd

**Edge-docked notch**
- Optional compact overlay that snaps to any screen edge
- Shows Craw + process count badge + memory total
- Click to open the main window, drag to reposition, right-click to hide

**System tray**
- Dynamic icon badge showing process count (green → amber → coral → red as it grows)
- Quick Scan, Quick Kill submenu, Show Notch toggle, Quit
- Left-click to open main window

**Craw the mascot**
- Procedurally-drawn pixel-art character rendered in the title bar
- Always bouncing, eyes always glowing, tracking your cursor
- Hand-ported from the [ClawdNotch](https://github.com/MavProDev/ClawdNotch) "Clawd" character

**Settings**
- 8 color themes (coral, blue, green, purple, cyan, amber, pink, red)
- Configurable scan interval, kill timeout, startup-with-Windows registry entry
- Dark theme throughout

## System Requirements

- Windows 10 or Windows 11
- No Python installation required (standalone `.exe`, 35.7 MB)

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+R | Refresh / scan now |
| Escape | Close to tray |

## Build from Source

```bash
# Prerequisites: Python 3.12+, pip
git clone https://github.com/MavProDev/CrawlSpace.git
cd CrawlSpace
pip install -r requirements.txt
python -m crawlspace.main

# Package as .exe
pip install pyinstaller
python build.py
# Output: dist/CrawlSpace.exe
```

## Stack

- Python 3.12+ / PyQt6 / psutil — **zero other dependencies**
- Single `.exe` via PyInstaller (35.7 MB)
- Scanner runs on a background `QThread` with sub-100ms stop responsiveness
- Diff-based table updates — only changed cells repaint per scan cycle
- Animation drops to 10 fps when window is hidden to conserve CPU

## How It Actually Works

```
Scanner (QThread, every ~5s)
  ↓ psutil.process_iter
  ↓ filter: is_dev_process? not in exclude list? not self?
  ↓ walk parent chain (up to 10 levels)
  ↓   → parent dead → ORPHAN (safe to kill)
  ↓   → parent is live shell/claude/code → ACTIVE (warn)
  ↓ cache cwd per (pid, create_time)
  ↓ emit processes_updated(list[ProcessInfo])
       ↓
   Main window (diff update)     Tray icon (badge + tooltip)     Notch (badge + memory)
```

Every `psutil` call is wrapped in `try/except NoSuchProcess, AccessDenied, ZombieProcess`. Scanner never blocks the UI thread. Process info cache is pruned when processes vanish so memory stays bounded.

## License

MIT License. See [LICENSE](LICENSE).

## Credits

Built by [@ReelDad](https://github.com/MavProDev) / MavPro Group LLC
