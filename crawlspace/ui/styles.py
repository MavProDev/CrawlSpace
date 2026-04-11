"""CrawlSpace — centralized QSS stylesheets for dark theme."""

from crawlspace.constants import C


def _hex(color) -> str:
    """Convert QColor to hex string."""
    return color.name()


def _rgba(color, alpha: int = 255) -> str:
    """Convert QColor to rgba() string."""
    return f"rgba({color.red()},{color.green()},{color.blue()},{alpha})"


def build_stylesheet() -> str:
    """Build the complete application stylesheet."""
    bg = _hex(C["notch_bg"])
    card = _hex(C["card_bg"])
    border = _hex(C["divider"])
    border_subtle = _hex(C["notch_border"])
    text = _hex(C["text_hi"])
    text_mid = _hex(C["text_md"])
    text_dim = _hex(C["text_lo"])
    coral = _hex(C["coral"])
    coral_light = _hex(C["coral_light"])
    green = _hex(C["green"])
    amber = _hex(C["amber"])
    red = _hex(C["red"])
    row_alt = _hex(C["row_alt"])
    row_hover = _hex(C["row_hover"])

    return f"""
/* ── Global ─────────────────────────────────────────── */
QWidget {{
    background-color: {bg};
    color: {text};
    font-family: "Segoe UI";
    font-size: 10pt;
    border: none;
}}

/* ── Labels ─────────────────────────────────────────── */
QLabel {{
    background: transparent;
    padding: 0px;
}}

/* ── Buttons ────────────────────────────────────────── */
QPushButton {{
    background-color: {card};
    color: {text};
    border: 1px solid {border};
    border-radius: 4px;
    padding: 5px 14px;
    font-size: 9pt;
}}
QPushButton:hover {{
    background-color: {border_subtle};
    border-color: {coral};
}}
QPushButton:pressed {{
    background-color: {_rgba(C["coral"], 40)};
}}
QPushButton:disabled {{
    color: {text_dim};
    border-color: {border};
}}
QPushButton#coral_btn {{
    background-color: {coral};
    color: #ffffff;
    border: none;
    font-weight: bold;
}}
QPushButton#coral_btn:hover {{
    background-color: {coral_light};
}}
QPushButton#red_btn {{
    background-color: {red};
    color: #ffffff;
    border: none;
    font-weight: bold;
}}
QPushButton#red_btn:hover {{
    background-color: #f06060;
}}
QPushButton#green_btn {{
    background-color: {green};
    color: #ffffff;
    border: none;
    font-weight: bold;
}}
QPushButton#flat_btn {{
    background: transparent;
    border: none;
    padding: 4px 8px;
    color: {text_mid};
}}
QPushButton#flat_btn:hover {{
    color: {text};
    background-color: {_rgba(C["coral"], 20)};
}}

/* ── Line Edit / Search ─────────────────────────────── */
QLineEdit {{
    background-color: {card};
    color: {text};
    border: 1px solid {border};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 9pt;
    selection-background-color: {_rgba(C["coral"], 80)};
}}
QLineEdit:focus {{
    border-color: {coral};
}}

/* ── Tree Widget (Process Table) ────────────────────── */
QTreeWidget {{
    background-color: {bg};
    alternate-background-color: {row_alt};
    border: none;
    outline: none;
    font-size: 9pt;
}}
QTreeWidget::item {{
    padding: 3px 4px;
    border: none;
    border-bottom: 1px solid {_rgba(C["divider"], 40)};
}}
QTreeWidget::item:hover {{
    background-color: {row_hover};
}}
QTreeWidget::item:selected {{
    background-color: {_rgba(C["coral"], 25)};
    border-left: 2px solid {coral};
}}
QTreeWidget::branch {{
    background: transparent;
}}
QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {{
    image: none;
    border-image: none;
}}
QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {{
    image: none;
    border-image: none;
}}

/* ── Header View ────────────────────────────────────── */
QHeaderView {{
    background-color: {bg};
    border: none;
}}
QHeaderView::section {{
    background-color: {card};
    color: {text_mid};
    border: none;
    border-bottom: 1px solid {border};
    border-right: 1px solid {_rgba(C["divider"], 30)};
    padding: 4px 8px;
    font-size: 8pt;
    font-weight: bold;
}}
QHeaderView::section:hover {{
    color: {text};
    background-color: {border_subtle};
}}

/* ── ScrollBar ──────────────────────────────────────── */
QScrollBar:vertical {{
    background: {bg};
    width: 8px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {border_subtle};
    min-height: 30px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {text_dim};
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
    border: none;
}}
QScrollBar:horizontal {{
    background: {bg};
    height: 8px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {border_subtle};
    min-width: 30px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {text_dim};
}}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
    border: none;
}}

/* ── Menu ───────────────────────────────────────────── */
QMenu {{
    background-color: {card};
    color: {text};
    border: 1px solid {border};
    padding: 4px;
    font-size: 9pt;
}}
QMenu::item {{
    padding: 5px 24px 5px 12px;
    border-radius: 3px;
}}
QMenu::item:selected {{
    background-color: {coral};
    color: #ffffff;
}}
QMenu::separator {{
    height: 1px;
    background: {border};
    margin: 4px 8px;
}}

/* ── Tab Bar ────────────────────────────────────────── */
QTabBar {{
    background: transparent;
    border: none;
}}
QTabBar::tab {{
    background: transparent;
    color: {text_mid};
    padding: 4px 10px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 9pt;
    margin-right: 2px;
}}
QTabBar::tab:hover {{
    color: {text};
    background-color: {_rgba(C["coral"], 15)};
}}
QTabBar::tab:selected {{
    color: {coral};
    border-bottom-color: {coral};
    font-weight: bold;
}}

/* ── CheckBox ───────────────────────────────────────── */
QCheckBox {{
    background: transparent;
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {border};
    border-radius: 3px;
    background: {card};
}}
QCheckBox::indicator:hover {{
    border-color: {coral};
}}
QCheckBox::indicator:checked {{
    background-color: {coral};
    border-color: {coral};
}}

/* ── ToolTip ────────────────────────────────────────── */
QToolTip {{
    background-color: {card};
    color: {text};
    border: 1px solid {border};
    padding: 4px 8px;
    font-size: 9pt;
}}

/* ── Splitter ───────────────────────────────────────── */
QSplitter::handle {{
    background: {border};
    height: 1px;
}}

/* ── Frame / Group ──────────────────────────────────── */
QFrame#card {{
    background-color: {card};
    border: 1px solid {border};
    border-radius: 6px;
}}
QFrame#divider {{
    background-color: {border};
    max-height: 1px;
}}

/* ── ComboBox ───────────────────────────────────────── */
QComboBox {{
    background-color: {card};
    color: {text};
    border: 1px solid {border};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 9pt;
}}
QComboBox:hover {{
    border-color: {coral};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {card};
    color: {text};
    border: 1px solid {border};
    selection-background-color: {coral};
    selection-color: #ffffff;
}}

/* ── Progress Bar (inline resource bars) ────────────── */
QProgressBar {{
    background-color: {_rgba(C["notch_border"], 80)};
    border: none;
    border-radius: 2px;
    max-height: 4px;
    text-align: center;
}}
QProgressBar::chunk {{
    border-radius: 2px;
}}
"""
