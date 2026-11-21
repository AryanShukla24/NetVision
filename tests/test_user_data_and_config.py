"""
Unit Tests for User Data Separation, Configuration Paths, and Directory Initialization
Verifies %LOCALAPPDATA% hierarchy, seed database handling, and missing asset resilience.
"""

import os
import gc
import tempfile
from pathlib import Path
from netvision.config import (
    get_user_data_dir,
    ensure_app_directories,
    USER_DATA_DIR,
    USER_DB_DIR,
    LOGS_DIR,
    REPORTS_DIR,
    EXPORTS_DIR,
    CONFIG_DIR,
    CACHE_DIR,
    DEFAULT_DB_PATH,
    APP_ICON_ICO,
    APP_ICON_PNG
)
from netvision.database.db_manager import DatabaseManager


def test_user_data_directory_structure():
    """Verifies that all required subdirectories exist under the user data root."""
    ensure_app_directories()
    assert USER_DATA_DIR.exists()
    assert USER_DB_DIR.exists()
    assert LOGS_DIR.exists()
    assert REPORTS_DIR.exists()
    assert EXPORTS_DIR.exists()
    assert CONFIG_DIR.exists()
    assert CACHE_DIR.exists()


def test_app_icons_exist():
    """Verifies that application icons are present in assets/icons/."""
    assert APP_ICON_ICO.exists(), f"Icon not found at {APP_ICON_ICO}"
    assert APP_ICON_PNG.exists(), f"PNG icon not found at {APP_ICON_PNG}"
    assert APP_ICON_ICO.stat().st_size > 1000
    assert APP_ICON_PNG.stat().st_size > 1000


def test_custom_user_database_initialization():
    """Verifies safe database initialization in an isolated directory with spaces."""
    tmp_dir = tempfile.TemporaryDirectory(prefix="NetVision Test Spaces ", ignore_cleanup_errors=True)
    try:
        custom_db_path = Path(tmp_dir.name) / "subfolder" / "netvision_test.db"
        db = DatabaseManager(db_path=custom_db_path)
        assert custom_db_path.exists()
        
        # Verify schema tables
        with db.get_connection() as conn:
            tables = [
                row[0] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table';"
                ).fetchall()
            ]
            assert "schema_version" in tables
            assert "speed_tests" in tables
            assert "latency_tests" in tables
            assert "signal_logs" in tables
            assert "locations" in tables
            assert "app_settings" in tables
    finally:
        gc.collect()
        try:
            tmp_dir.cleanup()
        except Exception:
            pass


def test_database_never_silently_overwritten():
    """Verifies that an existing database is not erased when DatabaseManager is re-instantiated."""
    tmp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    try:
        db_file = Path(tmp_dir.name) / "persistent_user.db"
        db1 = DatabaseManager(db_path=db_file)
        db1.add_location("Custom Special Lab")
        
        # Re-instantiate without recreating
        db2 = DatabaseManager(db_path=db_file)
        locs = db2.get_locations()
        assert "Custom Special Lab" in locs
    finally:
        gc.collect()
        try:
            tmp_dir.cleanup()
        except Exception:
            pass
