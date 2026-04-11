"""
CrawlSpace — constants.py
Single source of truth for all visual and behavioral constants.
"""

from PyQt6.QtGui import QColor, QFont


def make_font(spec: tuple) -> QFont:
    """Create a QFont from a FONTS tuple (family, size, weight_string)."""
    family, size, weight_str = spec
    font = QFont(family, size)
    if weight_str == "Bold":
        font.setBold(True)
    return font

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

C = {
    "notch_bg":     QColor(12, 12, 14),
    "notch_border": QColor(40, 40, 48),
    "card_bg":      QColor(28, 28, 34),
    "divider":      QColor(44, 44, 52),
    "text_hi":      QColor(240, 236, 232),
    "text_md":      QColor(155, 148, 142),
    "text_lo":      QColor(85, 80, 76),
    "coral":        QColor(217, 119, 87),
    "coral_light":  QColor(235, 155, 120),
    "green":        QColor(72, 199, 132),
    "amber":        QColor(240, 185, 55),
    "red":          QColor(230, 72, 72),
    "row_alt":      QColor(17, 17, 21),
    "row_hover":    QColor(26, 26, 30),
}

# ---------------------------------------------------------------------------
# Color themes
# ---------------------------------------------------------------------------

THEMES = {
    "coral":   {"accent": (217, 119, 87),  "accent_light": (235, 155, 120)},
    "blue":    {"accent": (88, 166, 255),  "accent_light": (130, 190, 255)},
    "green":   {"accent": (72, 199, 132),  "accent_light": (110, 220, 160)},
    "purple":  {"accent": (180, 130, 220), "accent_light": (200, 160, 235)},
    "cyan":    {"accent": (80, 200, 220),  "accent_light": (120, 220, 235)},
    "amber":   {"accent": (240, 185, 55),  "accent_light": (250, 205, 100)},
    "pink":    {"accent": (220, 100, 160), "accent_light": (240, 140, 185)},
    "red":     {"accent": (230, 72, 72),   "accent_light": (245, 110, 110)},
}

# ---------------------------------------------------------------------------
# Fonts — (family, size, weight_string)
# ---------------------------------------------------------------------------

FONTS = {
    "title_large": ("Segoe UI", 24, "Bold"),
    "title":       ("Segoe UI", 14, "Bold"),
    "heading":     ("Segoe UI", 12, "Bold"),
    "body_bold":   ("Segoe UI", 10, "Bold"),
    "body":        ("Segoe UI", 10, "Normal"),
    "label_bold":  ("Segoe UI", 9,  "Bold"),
    "label":       ("Segoe UI", 9,  "Normal"),
    "caption":     ("Segoe UI", 8,  "Normal"),
    "tiny":        ("Segoe UI", 7,  "Normal"),
    "tiny_bold":   ("Segoe UI", 7,  "Bold"),
    "mono":        ("Consolas", 10, "Normal"),
}

# ---------------------------------------------------------------------------
# Process-detection patterns
# ---------------------------------------------------------------------------

PROCESS_PATTERNS = {
    "python": [
        "python", "python3", "pythonw", "py",
        "uvicorn", "gunicorn", "hypercorn", "daphne",
        "flask", "fastapi", "django",
        "celery", "dramatiq", "rq",
        "pytest", "coverage", "tox", "nox",
        "jupyter", "jupyter-notebook", "jupyter-lab", "ipython",
        "streamlit", "gradio", "scrapy",
        "mypy", "ruff", "black", "isort",
    ],
    "node": [
        "node", "nodejs", "npm", "npx", "yarn", "pnpm", "bun", "deno",
        "tsx", "ts-node", "tsup",
        "next", "nuxt", "vite", "webpack", "esbuild", "rollup", "parcel", "turbopack",
        "electron",
        "jest", "vitest", "mocha", "playwright", "cypress",
        "eslint", "prettier",
        "pm2", "nodemon", "ts-node-dev",
        "express", "fastify", "hono", "koa",
    ],
    "devtool": [
        "cursor", "copilot", "aider", "cline",
    ],
    "infrastructure": [
        "docker", "docker-compose", "kubectl", "ngrok", "localtunnel", "cloudflared",
    ],
    "other": [
        "cargo", "go", "ruby", "rails", "puma", "sidekiq",
        "php", "artisan", "php-fpm",
        "java", "gradle", "gradlew",
        "dotnet",
    ],
}

# ---------------------------------------------------------------------------
# Processes to exclude (active tools / shells — not ghost processes)
# ---------------------------------------------------------------------------

EXCLUDE_PROCESSES = [
    "claude", "codex", "claude-code",
    "bash", "sh", "cmd", "powershell", "pwsh",
    "conhost", "windowsterminal", "wt",
    "code",  # VS Code itself (not its spawned servers)
]

# ---------------------------------------------------------------------------
# Common dev ports
# ---------------------------------------------------------------------------

COMMON_PORTS = [3000, 3001, 4200, 5000, 5173, 5174, 8000, 8080, 8888, 9000]

# ---------------------------------------------------------------------------
# Animation constants
# ---------------------------------------------------------------------------

BOUNCE_INCREMENT = 0.08
PULSE_INCREMENT = 0.10
PULSE_INCREMENT_BORED = 0.07
BOUNCE_AMPLITUDE = 1.2
LEG_WOBBLE_AMPLITUDE = 0.5
LEG_PHASE_OFFSET = 0.8
EYE_GLOW_FREQUENCY = 1.8
EYE_HALO_SIZE_MULT = 2.2
EYE_HALO_OFFSET_MULT = 0.6
EYE_SHIFT_MAX_X = 1.2
EYE_SHIFT_MAX_Y = 1.0
TREMBLE_FREQ_X = 47
TREMBLE_FREQ_Y = 53
TREMBLE_AMPLITUDE = 0.3
TICK_ACTIVE = 33
TICK_IDLE = 100
TICK_TOAST = 16
BORED_TIMEOUT_SECONDS = 300
DIM_OPACITY = 0.55

# ---------------------------------------------------------------------------
# Default application configuration
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    # Startup
    "start_with_windows": False,
    "start_minimized": False,

    # Appearance
    "color_theme": "coral",

    # Scanning
    "scan_interval_seconds": 5,
    "kill_timeout_seconds": 3,
    "confirm_kill": True,

    # Toasts / sound
    "toast_enabled": True,
    "toast_duration_seconds": 8,
    "sound_enabled": False,

    # Do-not-disturb
    "dnd_mode": False,

    # Overlay
    "overlay_enabled": False,
    "overlay_edge": "right",
    "overlay_opacity": 0.85,

    # Window geometry
    "window_x": 100,
    "window_y": 100,
    "window_w": 900,
    "window_h": 600,

    # View
    "view_mode": "flat",
    "sort_column": "name",
    "sort_ascending": True,

    # Whitelist
    "whitelist_paths": [],

    # Zombie detection
    "zombie_threshold_hours": 4,

    # First run
    "first_run_done": False,

    # Notification toggles
    "notify_new_process": True,
    "notify_process_died": True,
    "notify_kill_success": True,
    "notify_kill_failed": True,
    "notify_zombie": True,
    "notify_port_conflict": True,
}

# ---------------------------------------------------------------------------
# Spinner frames
# ---------------------------------------------------------------------------

SPINNER_FRAMES = ["·", "✻", "✽", "✶", "✳", "✢"]

# ---------------------------------------------------------------------------
# Emotion styles
# ---------------------------------------------------------------------------

EMOTION_STYLES = {
    "neutral": {
        "bounce_mult": 1.0,
        "tint": None,
        "leg_droop": 0,
        "tremble": False,
        "eye_droop": 0,
    },
    "happy": {
        "bounce_mult": 1.5,
        "tint": QColor(235, 155, 120),
        "leg_droop": 0,
        "tremble": False,
        "eye_droop": 0,
    },
    "sad": {
        "bounce_mult": 0.5,
        "tint": QColor(180, 130, 120),
        "leg_droop": 1,
        "tremble": False,
        "eye_droop": 0.5,
    },
    "sob": {
        "bounce_mult": 0.3,
        "tint": QColor(200, 100, 90),
        "leg_droop": 2,
        "tremble": True,
        "eye_droop": 0.5,
    },
    "alert": {
        "bounce_mult": 1.3,
        "tint": None,
        "leg_droop": 0,
        "tremble": False,
        "eye_droop": 0,
    },
}
