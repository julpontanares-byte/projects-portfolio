from focusbreaker.config import Colors, UIConfig, Palette

def get_stylesheet() -> str:
    return f"""
/* ── Tooltips ── */
QToolTip {{
    background-color: #ffffff;
    color: #1E2D2C;
    border: 1px solid #1B7F79;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 10px;
    font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif;
    font-weight: 500;
}}

/* ── Global Base ── */
QMainWindow QWidget {{
    background-color: transparent;
    border: none !important;
}}

QWidget {{
    color: {Palette.TEXT_PRIMARY};
    font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif;
    font-size: 14px;
    border: none;
    outline: none;
}}

QLabel, QPushButton, QFrame {{
    border: none;
}}

QMainWindow {{
    background-color: transparent;
}}

/* ── Global Shell ── */
QWidget#main_shell {{
    background-color: {Palette.BRAND_PRIMARY};
    border-radius: 24px;
}}

QWidget#content_root {{
    background-color: {Palette.SURFACE_DEFAULT};
    border-radius: 20px;
    margin: 4px; 
}}

/* ── Top Navigation Bar ── */
QWidget#top_nav {{
    background-color: transparent;
    border-bottom: 1px solid {Palette.SURFACE_DARK};
    min-height: 80px;
}}

QLabel#nav_logo {{
    font-size: 22px;
    font-weight: 800;
    color: {Palette.TEXT_PRIMARY};
    letter-spacing: -0.5px;
}}

QLabel#nav_logo_accent {{
    color: {Palette.BRAND_SECONDARY};
}}

/* Tab Switcher Pill */
QWidget#tab_switcher_container {{
    background-color: {Palette.SURFACE_DARK};
    border-radius: 24px;
    padding: 4px;
}}

QPushButton#nav_tab {{
    padding: 8px 24px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 13px;
    color: {Palette.TEXT_SECONDARY};
    background-color: transparent;
}}

QPushButton#nav_tab:hover {{
    color: {Palette.TEXT_PRIMARY};
}}

QPushButton#nav_tab[active="true"] {{
    background-color: {Palette.SURFACE_WHITE};
    color: {Palette.BRAND_PRIMARY};
}}

/* ── Typography & Section Headers ── */
QLabel#page_title {{
    font-size: 32px;
    font-weight: 800;
    color: {Palette.TEXT_PRIMARY};
    letter-spacing: -1px;
}}

QLabel#section_label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 800;
    color: {Palette.TEXT_MUTED};
    letter-spacing: 2px;
    text-transform: uppercase;
}}

QWidget#section_divider {{
    background-color: {Palette.SURFACE_DARK};
    max-height: 2px;
    border-radius: 1px;
}}

/* ── Cards ── */
QFrame#metric_card, QFrame#active_session_card, QFrame#card, QFrame#active_session_empty,
QFrame#metric_card_frame, QFrame#chart_card_frame {{
    background-color: {Palette.SURFACE_WHITE};
    border-radius: 24px;
    border: 1px solid transparent;
}}

QFrame#metric_card:hover, QFrame#card:hover, 
QFrame#metric_card_frame:hover, QFrame#chart_card_frame:hover {{
    border: 1px solid {Palette.BRAND_LIGHT};
}}

/* ── Specific Overrides for Charts in Analytics ── */
QFrame#chart_card_frame {{
    min-height: 320px;
    border-radius: 20px;
    border: 1px solid {Palette.SURFACE_DARK};
}}

QFrame#metric_card_frame {{
    border-radius: 16px;
    border: 1px solid {Palette.SURFACE_DARK};
}}

/* ── Info Icons ── */
QLabel#info_icon_btn {{
    background: {Palette.BRAND_LIGHT};
    color: {Palette.BRAND_PRIMARY};
    border-radius: 9px;
    font-family: 'Georgia', serif;
    font-size: 11px;
    font-weight: 800;
    font-style: italic;
    border: 1px solid {Palette.BRAND_PRIMARY};
}}

QLabel#info_icon_btn:hover {{
    background: {Palette.BRAND_PRIMARY};
    color: white;
}}

/* ── Active Session Card ── */
QFrame#active_session_card {{
    border-top: 6px solid {Palette.BRAND_SECONDARY};
}}

QLabel#task_name_heading {{
    font-size: 24px;
    font-weight: 800;
    color: {Palette.TEXT_PRIMARY};
    letter-spacing: -0.5px;
}}

QLabel#timer_display {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 56px;
    font-weight: 800;
    color: {Palette.TEXT_PRIMARY};
    letter-spacing: -3px;
}}

QProgressBar#session_progress {{
    background-color: {Palette.SURFACE_DARK};
    border-radius: 4px;
    height: 8px;
}}

QProgressBar#session_progress::chunk {{
    background-color: {Palette.BRAND_PRIMARY};
    border-radius: 4px;
}}

/* Badges */
QLabel.badge {{
    padding: 4px 12px;
    border-radius: 8px;
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
}}

QLabel.badge_mode {{
    background-color: {Palette.BRAND_LIGHT};
    color: {Palette.BRAND_PRIMARY};
}}

QLabel.badge_live {{
    background-color: #E8F5E9;
    color: #2E7D32;
}}

/* Footer Alert Banner */
QFrame#alert_banner {{
    background-color: {Palette.ACCENT_LIGHT};
    border-radius: 16px;
}}

/* ── Generic Metric Cards ── */
QLabel#metric_value {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 36px;
    font-weight: 800;
    color: {Palette.BRAND_PRIMARY};
    letter-spacing: -1px;
}}

/* ── Achievement Tiles ── */
QFrame#achievement_tile {{
    background-color: {Palette.SURFACE_DARK};
    border-radius: 20px;
    min-width: 90px;
    min-height: 110px;
}}

QFrame#achievement_tile[locked="false"] {{
    background-color: {Palette.BRAND_LIGHT};
}}

QLabel#ach_icon {{
    font-size: 36px;
}}

QLabel#ach_name_text {{
    font-size: 9px;
    font-weight: 800;
    color: {Palette.TEXT_SECONDARY};
    letter-spacing: 0.5px;
}}

/* ── History Page ── */
QFrame#history_row {{
    background-color: {Palette.SURFACE_WHITE};
    border-radius: 16px;
}}

QFrame#history_row:hover {{
    background-color: {Palette.SURFACE_WHITE};
    border: 1px solid {Palette.BRAND_LIGHT};
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 8px;
    margin: 10px 0 10px 0;
}}

QScrollBar::handle:vertical {{
    background: {Palette.TEXT_MUTED};
    min-height: 40px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {Palette.TEXT_SECONDARY};
}}

/* ── Buttons ── */
QPushButton#fab_add {{
    background-color: {Palette.BRAND_PRIMARY};
    color: white;
    border-radius: 35px;
    font-size: 48px;
    font-weight: 300;
    text-align: center;
    padding-bottom: 8px; /* Adjusting for the natural vertical offset of the '+' character */
}}

QPushButton#fab_add:hover {{
    background-color: {Palette.BRAND_SECONDARY};
}}
"""
