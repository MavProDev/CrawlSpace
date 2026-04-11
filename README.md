# CrawlSpace

**Hunting zombies in your dev environment.**

CrawlSpace is a lightweight Windows desktop daemon that detects, inspects, and kills orphaned developer processes left running by AI coding tools, dev servers, and build systems. It sits quietly in your system tray until you need it.

## Download. Run. Done.

1. Grab `CrawlSpace.exe` from the [latest release](https://github.com/MavProDev/CrawlSpace/releases/latest)
2. Double-click to run. No installer needed.
3. Craw appears in your system tray. That's it.

## Features

**Process Detection**
- Scans for 90+ known dev processes: Python, Node.js, AI tools, Docker, and more
- Detects orphaned processes, zombie dev servers, and runaway builds
- Shows CPU, memory, uptime, listening ports, and parent-child relationships
- Flat view (grouped by category) and tree view (parent-child hierarchy)

**Kill System**
- Kill single processes, entire process trees, or everything at once
- Graceful SIGTERM with configurable timeout before SIGKILL
- Kill All requires typing "KILL" to confirm (non-disableable safety)
- Suspend and resume processes without killing them

**Process Inspector**
- Click any process to see full details: command line, open files, network connections, environment variables
- Sensitive environment variables (keys, tokens, passwords) are masked with a reveal button
- Copy process summary, PID, command line, or path to clipboard
- Open in Task Manager as a fallback

**Craw the Mascot**
- Procedurally-drawn pixel-art character rendered at runtime via QPainter
- Always bouncing, eyes always glowing green, always tracking your cursor
- Emotes based on events: happy after kills, sad on failures, bored when idle
- Particle effects: floating hearts, falling rain, yawn circles

**Edge-Docked Overlay**
- Compact always-on-top widget showing Craw + process count + memory usage
- Snaps to any screen edge, drag to reposition
- Multi-monitor aware with rotating border glow

**Toast Notifications**
- Slide-in notifications for new processes, kills, failures, and zombies
- Rate-limited, stackable, auto-dismissing
- Each toast shows Craw with emotion matching the event type

**Settings**
- 8 color themes, configurable scan interval, whitelist, zombie threshold
- Per-notification-type toggles, Do Not Disturb mode
- Start with Windows, start minimized, overlay toggle
- All settings persist across restarts

## System Requirements

- Windows 10 or Windows 11
- No Python installation required (standalone .exe)

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

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+K | Kill selected |
| Ctrl+Shift+K | Kill selected trees |
| Ctrl+R | Refresh |
| Ctrl+F | Search |
| Ctrl+A | Select all |
| Ctrl+D | Deselect all |
| Ctrl+T / F5 | Toggle flat/tree view |
| Delete | Kill selected |
| Escape | Close to tray |
| Space | Toggle checkbox |
| Enter | Expand detail panel |

## Stack

- Python 3.12+ / PyQt6 / psutil
- Single .exe via PyInstaller (36 MB)
- Zero external dependencies beyond PyQt6 and psutil

## License

MIT License. See [LICENSE](LICENSE).

## Credits

Built by [@ReelDad](https://github.com/MavProDev) / MavPro Group LLC
