# CrawlSpace

Lightweight Windows desktop daemon that hunts and kills orphaned dev processes.

## Stack
- Python 3.12+, PyQt6, psutil
- Single .exe via PyInstaller
- NO other external dependencies

## Code Style
- Type hints on all function signatures
- Dataclasses for data models
- f-strings for string formatting
- snake_case for functions/variables, PascalCase for classes
- Docstrings on all public methods (one-line unless complex)
- Constants in UPPER_SNAKE_CASE in constants.py
- All colors defined in constants.py, never hardcoded in UI files
- QSS styles centralized in styles.py, never inline

## Architecture Rules
- Scanner runs on QThread, never blocks UI thread
- All psutil calls wrapped in try/except (NoSuchProcess, AccessDenied, ZombieProcess)
- Config saves are debounced (max once per 5 seconds)
- Animation timer drops to 10fps when window is hidden/minimized
- Detail panel lazy-loads expensive data (open files, env vars, connections)
- Process table uses QTreeWidget with flat + tree view toggle
- Self-PID excluded from process list entirely (not greyed out — hidden)

## Testing
- Run with: python -m crawlspace.main
- Verify tray icon appears, context menu works
- Verify process detection by running: python -c "import time; time.sleep(999)"
- Kill that test process from CrawlSpace to verify kill flow

## Common Commands
- pip install -r requirements.txt
- python -m crawlspace.main
- python build.py (PyInstaller packaging)

## Do NOT
- Add dependencies beyond PyQt6 and psutil
- Use QML or Qt Designer — all UI is code-built
- Use threads directly — use QThread with signals
- Hold references to psutil.Process objects between scan cycles
- Hardcode colors outside constants.py
- Create separate CSS/QSS files — keep in styles.py
