"""
Configuration Module - Application Configuration Management
Handles all app configuration, constants, paths, and design system.
"""

import os
from pathlib import Path
from typing import Set, Dict

# ========================= APPLICATION INFO =========================
APP_NAME = "focusBreaker"
APP_VERSION = "2.0.0"
APP_AUTHOR = "BoardGirls"
APP_DESCRIPTION = "Productivity app with enforced break discipline"

# Schema version for database migrations
SCHEMA_VERSION = 1
DB_FILE = "focusbreaker.db"

# ========================= PATH CONFIGURATION =========================
class AppPaths:
    """
    Application directory and file paths using pathlib.
    """
    # Base directories
    BASE_DIR = Path(__file__).resolve().parent.parent  # Project root (I:/py/fBreakerv2)
    APP_DIR = BASE_DIR / "focusbreaker"                # Application source dir
    
    # Assets (Point to the root assets folder)
    ASSETS_DIR = BASE_DIR / "assets"
    FONTS_DIR = ASSETS_DIR / "fonts"
    IMAGES_DIR = ASSETS_DIR / "images"
    
    # App-specific media (Inside focusbreaker/assets)
    INTERNAL_ASSETS_DIR = APP_DIR / "assets"
    MEDIA_DIR = INTERNAL_ASSETS_DIR / "media"
    
    # Media subdirectories
    MEDIA_NORMAL_DIR = MEDIA_DIR / "normal"
    MEDIA_STRICT_DIR = MEDIA_DIR / "strict"
    MEDIA_FOCUSED_DIR = MEDIA_DIR / "focused"
    
    # Media Subdirectories (Defaults and User)
    MEDIA_NORMAL_DEFAULTS = MEDIA_NORMAL_DIR / "defaults"
    MEDIA_NORMAL_USER = MEDIA_NORMAL_DIR / "user"
    MEDIA_STRICT_DEFAULTS = MEDIA_STRICT_DIR / "defaults"
    MEDIA_STRICT_USER = MEDIA_STRICT_DIR / "user"
    MEDIA_FOCUSED_DEFAULTS = MEDIA_FOCUSED_DIR / "defaults"
    MEDIA_FOCUSED_USER = MEDIA_FOCUSED_DIR / "user"
    
    # Logs
    LOGS_DIR = BASE_DIR / "logs"
    
    # Database
    DATABASE_FILE = BASE_DIR / DB_FILE
    
    @classmethod
    def get_database_path(cls) -> Path:
        return cls.DATABASE_FILE
    
    @classmethod
    def get_media_dir(cls, mode: str, user_content: bool = False) -> Path:
        if mode == 'normal':
            return cls.MEDIA_NORMAL_USER if user_content else cls.MEDIA_NORMAL_DEFAULTS
        elif mode == 'strict':
            return cls.MEDIA_STRICT_USER if user_content else cls.MEDIA_STRICT_DEFAULTS
        elif mode == 'focused':
            return cls.MEDIA_FOCUSED_USER if user_content else cls.MEDIA_FOCUSED_DEFAULTS
        else:
            raise ValueError(f"Invalid mode: {mode}")
    
    @classmethod
    def ensure_directories_exist(cls):
        dirs = [cls.MEDIA_DIR, cls.MEDIA_NORMAL_DEFAULTS, cls.MEDIA_NORMAL_USER, 
                cls.MEDIA_STRICT_DEFAULTS, cls.MEDIA_STRICT_USER, 
                cls.MEDIA_FOCUSED_DEFAULTS, cls.MEDIA_FOCUSED_USER, cls.LOGS_DIR]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

# ========================= BRAND IDENTITY & PALETTE =========================
class Palette:
    # Brand
    BRAND_PRIMARY = "#1B7F79"      # Sidebar background
    BRAND_SECONDARY = "#2A9B93"    # Heading text, subtitle text
    BRAND_LIGHT = "#E1F5F3"        # Teal tint backgrounds, badges
    
    # Surface
    SURFACE_DEFAULT = "#F2EDE3"    # Main content area background
    SURFACE_DARK = "#E8E0D0"       # Hover states, dividers
    SURFACE_WHITE = "#FFFFFF"      # Input fields, buttons
    
    # Accent ( Brown family)
    ACCENT_PRIMARY = "#8B5E3C"     # Active nav item highlight
    ACCENT_LIGHT = "#F5E8DC"       # Active nav item background tint
    
    # Text & UI
    TEXT_PRIMARY = "#1E2D2C"       # Body text (teal-tinted near-black)
    TEXT_SECONDARY = "#6B8886"     # Muted labels, card descriptions
    TEXT_MUTED = "#9AAEAC"         # Input placeholder, step counter
    TEXT_INVERSE = "#FFFFFF"       # White
    
    BORDER_DEFAULT = "#C8D8D6"     # Input borders, dividers
    
    # Mode Card Colors
    MODE_NORMAL_FILL = "#F2A99A"
    MODE_NORMAL_BORDER = "#E8796A"
    MODE_NORMAL_TEXT = "#7A3028"
    
    MODE_STRICT_FILL = "#8BB98A"
    MODE_STRICT_BORDER = "#6BA068"
    MODE_STRICT_TEXT = "#2A4D29"
    
    MODE_FOCUS_FILL = "#9B93C8"
    MODE_FOCUS_BORDER = "#7A6FB5"
    MODE_FOCUS_TEXT = "#2E2560"

    # Status colors
    STATUS_SUCCESS = "#4CAF50"    # green
    STATUS_WARNING = "#FFC107"    # orange/yellow
    STATUS_ERROR = "#F44336"      # red
    
    # Status color aliases
    SUCCESS = STATUS_SUCCESS
    WARNING = STATUS_WARNING
    ERROR = STATUS_ERROR
    DANGER = STATUS_ERROR

class Colors:
    """Design Mappings"""
    BG = Palette.SURFACE_DEFAULT
    SURFACE = Palette.SURFACE_WHITE
    SURFACE_ALT = Palette.SURFACE_DARK
    SIDEBAR = Palette.BRAND_PRIMARY
    DARK = Palette.BRAND_PRIMARY  # For main_shell background
    
    TEXT = Palette.TEXT_PRIMARY
    TEXT_SECONDARY = Palette.TEXT_SECONDARY
    TEXT_MUTED = Palette.TEXT_MUTED
    TEXT_INVERSE = Palette.TEXT_INVERSE
    
    PRIMARY = Palette.BRAND_SECONDARY
    ACCENT = Palette.ACCENT_PRIMARY
    
    HIGHLIGHT = Palette.ACCENT_PRIMARY
    BORDER = Palette.BORDER_DEFAULT
    BORDER_STRONG = Palette.BRAND_SECONDARY
    
    # Status colors
    SUCCESS = Palette.STATUS_SUCCESS
    WARNING = Palette.STATUS_WARNING
    ERROR = Palette.STATUS_ERROR
    DANGER = Palette.STATUS_ERROR
    
    # UI colors - backwards compatibility
    NORMAL_DIM = Palette.BRAND_LIGHT
    TEAL_LIGHT = Palette.BRAND_SECONDARY
    
    # Mode colors
    NORMAL = Palette.MODE_NORMAL_FILL
    STRICT = Palette.MODE_STRICT_FILL
    FOCUSED = Palette.MODE_FOCUS_FILL

# ========================= UI CONFIGURATION =========================
class UIConfig:
    WINDOW_W = 1000
    WINDOW_H = 750
    SIDEBAR_EXPANDED = 160
    SIDEBAR_COLLAPSED = 64
    RADIUS_SM = 6
    RADIUS_MD = 10
    RADIUS_LG = 16
    RADIUS_PILL = 999
    LOGO_PATH = "assets/images/focusBreaker_circle_logo.png"

# ========================= ENGINE CONFIG =========================
class AudioConfig:
    SUPPORTED_FORMATS: Set[str] = {'.mp3', '.wav', '.ogg'}
    DEFAULT_MEDIA_VOLUME = 80
    DEFAULT_ALARM_VOLUME = 70
    ALARM_DURATION = 5

class MediaConfig:
    """Media file configuration and supported formats"""
    SUPPORTED_IMAGE_FORMATS: Set[str] = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    SUPPORTED_VIDEO_FORMATS: Set[str] = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}

class TimingConfig:
    """Core engine timing constants."""
    NORMAL_WORK = 25
    NORMAL_BREAK = 5
    NORMAL_SNOOZE = 5
    NORMAL_MAX_SNOOZE = 3
    STRICT_WORK = 52
    STRICT_BREAK = 17
    STRICT_COOLDOWN = 20
    FOCUSED_MIN_BREAK = 30

MODES: Dict[str, Dict] = {
    "normal": {
        "name": "NORMAL",
        "description": "Balanced work & breaks",
        "color": Palette.MODE_NORMAL_FILL,
        "border": Palette.MODE_NORMAL_BORDER,
        "text": Palette.MODE_NORMAL_TEXT,
    },
    "strict": {
        "name": "STRICT",
        "description": "High stakes productivity",
        "color": Palette.MODE_STRICT_FILL,
        "border": Palette.MODE_STRICT_BORDER,
        "text": Palette.MODE_STRICT_TEXT,
    },
    "focused": {
        "name": "FOCUS",
        "description": "Deep flow state",
        "color": Palette.MODE_FOCUS_FILL,
        "border": Palette.MODE_FOCUS_BORDER,
        "text": Palette.MODE_FOCUS_TEXT,
    },
}
