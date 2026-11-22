"""
NetVision - Configuration and Constants
Defines application-wide settings, default thresholds, color palette, and paths.
Supports %LOCALAPPDATA% separation for installed/packaged user-data.
"""

from pathlib import Path
import os
import sys
import shutil
import logging

logger = logging.getLogger(__name__)

# Application Info
APP_NAME = "NetVision"
APP_SUBTITLE = "Smart Network Quality & Wi-Fi Coverage Analyzer"
APP_VERSION = "2.0.0"
ORGANIZATION_NAME = "BTech CSE Academic Projects"

# App & Asset Paths (Supports PyInstaller frozen bundle and source development)
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys._MEIPASS)
    EXE_DIR = Path(sys.executable).resolve().parent
else:
    # Running from source: __file__ is in src/netvision/config.py -> parent.parent.parent is NetVision/
    APP_DIR = Path(__file__).resolve().parent.parent.parent
    EXE_DIR = APP_DIR

ASSETS_DIR = APP_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
APP_ICON_ICO = ICONS_DIR / "netvision.ico"
APP_ICON_PNG = ICONS_DIR / "netvision.png"
DEV_DATA_DIR = APP_DIR / "data"
TEMPLATE_DB_PATH = DEV_DATA_DIR / "netvision.db"

# User-writable Runtime Data Directory (%LOCALAPPDATA%\NetVision)
def get_user_data_dir() -> Path:
    base = os.getenv("LOCALAPPDATA")
    if not base:
        base = os.path.expanduser("~")
    return Path(base) / "NetVision"

USER_DATA_DIR = get_user_data_dir()
USER_DB_DIR = USER_DATA_DIR / "database"
LOGS_DIR = USER_DATA_DIR / "logs"
REPORTS_DIR = USER_DATA_DIR / "reports"
EXPORTS_DIR = USER_DATA_DIR / "exports"
CONFIG_DIR = USER_DATA_DIR / "config"
CACHE_DIR = USER_DATA_DIR / "cache"

DEFAULT_DB_PATH = USER_DB_DIR / "netvision.db"
LOG_FILE_PATH = LOGS_DIR / "netvision.log"


def ensure_app_directories():
    """
    Creates required runtime directories under %LOCALAPPDATA%\\NetVision.
    Safely seeds initial database from bundled template if no existing user database is present.
    """
    for directory in (USER_DATA_DIR, USER_DB_DIR, LOGS_DIR, REPORTS_DIR, EXPORTS_DIR, CONFIG_DIR, CACHE_DIR):
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create user directory {directory}: {e}")

    # Safe first-launch database initialization
    if not DEFAULT_DB_PATH.exists():
        if TEMPLATE_DB_PATH.exists():
            try:
                shutil.copy2(TEMPLATE_DB_PATH, DEFAULT_DB_PATH)
                logger.info(f"Initialized user database from template: {DEFAULT_DB_PATH}")
            except Exception as e:
                logger.error(f"Failed to copy template database to {DEFAULT_DB_PATH}: {e}")
        else:
            logger.info("No template database found; a new database will be initialized at first use.")


# Automatically ensure directories on config import
ensure_app_directories()

# Network Quality Thresholds (Configurable)
DEFAULT_THRESHOLDS = {
    "signal": {
        "excellent": 75,  # >= 75%
        "good": 50,       # >= 50%
        "fair": 30,       # >= 30%
        "poor": 0         # < 30%
    },
    "latency": {
        "excellent": 30,  # <= 30 ms
        "good": 60,       # <= 60 ms
        "fair": 100,      # <= 100 ms
        "poor": 200       # > 100 ms
    },
    "packet_loss": {
        "excellent": 0.0, # 0%
        "good": 1.0,      # <= 1%
        "fair": 3.0,      # <= 3%
        "poor": 5.0       # > 3%
    },
    "download_speed": {
        "excellent": 50.0, # >= 50 Mbps
        "good": 25.0,      # >= 25 Mbps
        "fair": 10.0,      # >= 10 Mbps
        "poor": 0.0        # < 10 Mbps
    }
}

# Default Ping Targets for Latency Monitoring
DEFAULT_PING_TARGETS = [
    {"label": "Google DNS (8.8.8.8)", "host": "8.8.8.8"},
    {"label": "Cloudflare DNS (1.1.1.1)", "host": "1.1.1.1"},
    {"label": "OpenDNS (208.67.222.222)", "host": "208.67.222.222"},
    {"label": "Quad9 DNS (9.9.9.9)", "host": "9.9.9.9"}
]

# Default Speed Test Test-File Servers (Legitimate Cloudflare / CDN endpoints)
DEFAULT_SPEED_SERVERS = [
    {
        "name": "Cloudflare Global Edge",
        "down_url": "https://speed.cloudflare.com/__down?bytes=",
        "up_url": "https://speed.cloudflare.com/__up"
    }
]

# Dark Theme Color Palette — Professional Network Instrumentation
COLORS = {
    "bg_dark": "#10151C",          # Main application background
    "bg_surface": "#151D27",       # Secondary panels, sidebars
    "bg_elevated": "#1C2632",      # Elevated surfaces, cards
    "bg_input": "#0E1319",         # Input field backgrounds
    "bg_surface_hover": "#232F3E", # Hover state for surfaces

    "border": "#1E2A38",           # Subtle structural borders
    "border_light": "#2A3A4C",     # Slightly visible separators
    "border_focus": "#22B8CF",     # Focus ring accent

    "text_primary": "#D5DEE8",     # Main readable text
    "text_secondary": "#8291A3",   # Labels, descriptions
    "text_muted": "#5A6B7F",       # Inactive, placeholder text
    "text_bright": "#F0F4F8",      # High-emphasis headings

    "primary": "#22B8CF",          # Primary accent (teal)
    "primary_dark": "#1A8FA0",     # Darker primary variant
    "primary_subtle": "rgba(34, 184, 207, 0.12)",  # Primary tinted bg

    "success": "#39D98A",          # Healthy / excellent status
    "success_bg": "rgba(57, 217, 138, 0.10)",
    "success_dim": "#2BA06A",

    "warning": "#F5B942",          # Cautionary status
    "warning_bg": "rgba(245, 185, 66, 0.10)",

    "danger": "#F06464",           # Critical / poor status
    "danger_bg": "rgba(240, 100, 100, 0.10)",

    "info": "#7C8CF5",             # Informational accent
    "info_bg": "rgba(124, 140, 245, 0.10)",

    "purple": "#B07CFA",           # Secondary decorative accent
}
