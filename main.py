"""
NetVision - Smart Network Quality & Wi-Fi Coverage Analyzer
Windows Desktop Application Entry Point
"""

import sys
import os
import logging
import multiprocessing
import traceback
from pathlib import Path

# Add src and project root to sys.path for direct python execution
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from logging.handlers import RotatingFileHandler
from netvision.config import (
    APP_NAME, APP_VERSION, ORGANIZATION_NAME, LOG_FILE_PATH,
    APP_ICON_PNG, APP_ICON_ICO, ensure_app_directories
)
from netvision.ui.theme import DARK_THEME_QSS
from netvision.ui.main_window import MainWindow


def setup_logging():
    """Configures application-wide logging with rotating file output in %LOCALAPPDATA%."""
    ensure_app_directories()
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers = []
    if sys.stdout is not None:
        handlers.append(logging.StreamHandler(sys.stdout))
    try:
        file_handler = RotatingFileHandler(
            str(LOG_FILE_PATH),
            maxBytes=2_000_000,
            backupCount=3,
            encoding="utf-8"
        )
        handlers.append(file_handler)
    except Exception as e:
        if sys.stderr is not None:
            sys.stderr.write(f"Warning: Could not initialize file logging at {LOG_FILE_PATH}: {e}\n")

    if not handlers:
        handlers.append(logging.NullHandler())

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=handlers
    )


def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler logging crashes to rotating log file."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger = logging.getLogger("NetVision.Crash")
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical(f"Unhandled Exception: {err_msg}")


def main():
    """Main application execution routine."""
    setup_logging()
    sys.excepthook = handle_uncaught_exception

    logger = logging.getLogger("NetVision")
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}...")

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(ORGANIZATION_NAME)

    # Set Application Icon globally
    if APP_ICON_PNG.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_PNG)))
    elif APP_ICON_ICO.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_ICO)))

    # Apply Dark Modern Theme Stylesheet
    app.setStyleSheet(DARK_THEME_QSS)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
