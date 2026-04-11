# CrawlSpace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone Windows desktop daemon that detects, inspects, and kills orphaned dev processes, with an animated pixel-art mascot (Crawldad).

**Architecture:** Python 3.12+ / PyQt6 / psutil, single .exe via PyInstaller. Scanner runs on QThread, emits signals to UI. Config is thread-safe with atomic writes. Character is procedurally drawn via QPainter at runtime. App controller (`app.py`) orchestrates kill/suspend/resume workflows separate from UI.

**Tech Stack:** Python 3.14, PyQt6>=6.6, psutil>=5.9. Dev: pytest. Packaging: PyInstaller.

---

## Context

CrawlSpace is part of @ReelDad's suite of Claude Code desktop tools. The mascot "Crawldad" is visually identical to "Clawd" from ClawdNotch (same 11x10 pixel grid, same rendering pipeline). The project is standalone — no shared code at runtime, but patterns are ported from ClawdNotch.

**Repo:** https://github.com/MavProDev/CrawlSpace
**Local:** `C:\Users\reeld\OneDrive\Desktop\Claude Projects\CrawlSpace\`

## Critical Rules

1. No runtime deps beyond PyQt6 and psutil
2. Self-PID never in process list (hidden, not greyed out)
3. Kill All requires typing "KILL" — non-disableable
4. Every psutil call wrapped in try/except (NoSuchProcess, AccessDenied, ZombieProcess)
5. Scanner on QThread, never psutil on UI thread
6. All colors from constants.py, never hardcoded in UI
7. Config writes atomic (temp file + os.replace)
8. Crawldad always bounces, glows green, tracks cursor

---

## Tasks 1-20: Phases 1-3 (Foundation + Process Engine + Character)

### Task 1: Project Scaffolding

**Files:**
- Create: `crawlspace/__init__.py`, `crawlspace/ui/__init__.py`, `crawlspace/character/__init__.py`, `crawlspace/utils/__init__.py`, `tests/__init__.py`, `tests/conftest.py`
- Create: `requirements.txt`, `.gitignore`, `CLAUDE.md`
- Move: `crawldad.ico` → `assets/crawldad.ico`

- [ ] Step 1: Create directories + __init__.py files (crawlspace/__init__.py has __version__ = "0.1.0")
- [ ] Step 2: Create requirements.txt (PyQt6>=6.6.0, psutil>=5.9.0)
- [ ] Step 3: Create .gitignore
- [ ] Step 4: Create CLAUDE.md from spec
- [ ] Step 5: Move crawldad.ico to assets/
- [ ] Step 6: Create venv + install deps
- [ ] Step 7: Verify import works
- [ ] Step 8: Commit

### Task 2: Constants Module

**Files:**
- Create: `crawlspace/constants.py`
- Create: `tests/test_constants.py`

- [ ] Step 1: Write constants.py (C dict, THEMES, FONTS, PROCESS_PATTERNS, COMMON_PORTS, animation constants, DEFAULT_CONFIG, SPINNER_FRAMES, EMOTION_STYLES)
- [ ] Step 2: Write tests
- [ ] Step 3: Run tests — PASS
- [ ] Step 4: Commit

### Task 3: Config Manager

**Files:**
- Create: `crawlspace/config.py`
- Create: `tests/test_config.py`, `tests/conftest.py`

- [ ] Step 1: Write conftest.py (qapp fixture, tmp_config_dir fixture)
- [ ] Step 2: Write config.py (_atomic_write, apply_theme, ConfigManager with Lock/debounce)
- [ ] Step 3: Write tests (defaults, atomic write, round-trip, apply_theme, get default, debounce)
- [ ] Step 4: Run tests — PASS
- [ ] Step 5: Commit

### Task 4: Singleton Lock

**Files:** Create: `crawlspace/utils/singleton.py`

- [ ] Step 1: Write singleton.py (CreateMutexW, acquire_lock, release_lock)
- [ ] Step 2: Commit

### Task 5: Platform Utilities

**Files:** Create: `crawlspace/utils/platform.py`

- [ ] Step 1: Write platform.py (is_admin, relaunch_as_admin, self_pid, screen geometry helpers)
- [ ] Step 2: Commit

### Task 6: Process Data Model

**Files:** Create: `crawlspace/process_info.py`, `tests/test_process_info.py`

- [ ] Step 1: Write process_info.py (@dataclass ProcessInfo with all fields + orphan_score + properties)
- [ ] Step 2: Write tests
- [ ] Step 3: Run tests — PASS
- [ ] Step 4: Commit

### Task 7: Process Categories

**Files:** Create: `crawlspace/categories.py`, `tests/test_categories.py`

- [ ] Step 1: Write categories.py (classify_process, is_dev_process, CATEGORY_LABELS, CATEGORY_ORDER)
- [ ] Step 2: Write tests (7 cases: python/node/devtool/unknown/is_dev/case_insensitive/uvicorn)
- [ ] Step 3: Run tests — PASS
- [ ] Step 4: Commit

### Task 8: Process Scanner

**Files:** Create: `crawlspace/scanner.py`

- [ ] Step 1: Write scanner.py (ScannerThread with signals, _scan with psutil, self-PID exclusion, whitelist, orphan score, _format_uptime)
- [ ] Step 2: Write tests for _format_uptime
- [ ] Step 3: Run tests — PASS
- [ ] Step 4: Commit

### Task 9: Process Tree Builder

**Files:** Create: `crawlspace/process_tree.py`, `tests/test_process_tree.py`

- [ ] Step 1: Write process_tree.py (build_tree, resolve_tree with visited set, get_roots)
- [ ] Step 2: Write tests (5 cases with mock ProcessInfo)
- [ ] Step 3: Run tests — PASS
- [ ] Step 4: Commit

### Task 10: Process Killer

**Files:** Create: `crawlspace/killer.py`

- [ ] Step 1: Write killer.py (kill_process SIGTERM→SIGKILL, kill_tree bottom-up, suspend_process, resume_process)
- [ ] Step 2: Commit

### Task 11: Event History

**Files:** Create: `crawlspace/history.py`, `tests/test_history.py`

- [ ] Step 1: Write history.py (EventHistory with deque maxlen=200, Lock, append/get/save/load/prune/clear)
- [ ] Step 2: Write tests (6 cases)
- [ ] Step 3: Run tests — PASS
- [ ] Step 4: Commit

### Task 12: Color Utilities

**Files:** Create: `crawlspace/utils/colors.py`, `tests/test_colors.py`

- [ ] Step 1: Write colors.py (lerp_color, with_alpha, apply_theme, body_pulse_color, uptime_color, badge_color)
- [ ] Step 2: Write tests (6 cases)
- [ ] Step 3: Run tests — PASS
- [ ] Step 4: Commit

### Task 13: Crawldad Character Renderer

**Files:** Create: `crawlspace/character/crawldad.py`

- [ ] Step 1: Write crawldad.py (CRAWLDAD grid, draw_crawldad function ported from ClawdNotch clawd.py, eye_shift, always eye_glow=True)
- [ ] Step 2: Commit

### Task 14: Animation Controller

**Files:** Create: `crawlspace/character/animation.py`

- [ ] Step 1: Write animation.py (AnimationController with frame_tick signal, bounce/pulse counters, FPS switching)
- [ ] Step 2: Commit

### Task 15: Particle Effects

**Files:** Create: `crawlspace/character/particles.py`

- [ ] Step 1: Write particles.py (draw_hearts, draw_rain, draw_yawn with exact values from character bible)
- [ ] Step 2: Commit

### Task 16: Emotion State Machine

**Files:** Create: `crawlspace/character/emotions.py`, `tests/test_emotions.py`

- [ ] Step 1: Write emotions.py (EmotionStateMachine with signal, triggers, auto-revert, bored detection)
- [ ] Step 2: Write tests (6 cases)
- [ ] Step 3: Run tests — PASS
- [ ] Step 4: Commit

### Task 17: Main Entry Point

**Files:** Create: `crawlspace/main.py`, `crawlspace/__main__.py`

- [ ] Step 1: Write main.py (QApplication, singleton, config, scanner, history, emotions, anim, signal wiring, tray, cleanup)
- [ ] Step 2: Write __main__.py
- [ ] Step 3: Manual verify
- [ ] Step 4: Commit

### Task 18: System Tray with Dynamic Badge

**Files:** Create: `crawlspace/ui/tray.py`

- [ ] Step 1: Write tray.py (QSystemTrayIcon, dark menu, badge via QPainter, Quick Kill submenu with top 3 orphan_score, tooltip)
- [ ] Step 2: Manual verify
- [ ] Step 3: Commit

### Task 19: App Controller + Wiring

**Files:** Create: `crawlspace/app.py`, Modify: `crawlspace/main.py`

- [ ] Step 1: Write app.py (CrawlSpaceApp with do_kill/do_kill_tree/do_suspend/do_resume + history + emotions)
- [ ] Step 2: Update main.py to use CrawlSpaceApp
- [ ] Step 3: End-to-end verify
- [ ] Step 4: Commit

### Task 20: Run All Tests + Push

- [ ] Step 1: Run full test suite — all ~45 tests pass
- [ ] Step 2: Fix any failures
- [ ] Step 3: Final commit + push to GitHub

---

## Verification Checklist

After all tasks complete:
1. `python -m pytest tests/ -v` — all tests pass
2. `python -m crawlspace.main` — app starts, tray icon with badge
3. Start test processes — detected within 5s, badge updates
4. Quick Kill from tray — process dies, badge updates
5. Second instance attempt — prints error, exits
