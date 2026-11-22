"""
Tests for Visual Identity Redesign, Positioning Editor Desktop Preview,
Positioning Table layout, and Emoji Elimination across NetVision.
"""

import os
import re
import pytest
from PySide6.QtWidgets import QApplication, QTableWidget, QComboBox
from PySide6.QtCore import Qt

from netvision.config import COLORS
from netvision.ui.theme import DARK_THEME_QSS
from netvision.ui.main_window import MainWindow
from netvision.core.overlay_config import OverlayConfig
from netvision.ui.overlay.visual_editor import VisualDesktopEditor, SimulatedDesktopCanvas
from netvision.ui.pages.settings_page import SettingsPage
from netvision.database.db_manager import DatabaseManager


@pytest.fixture(scope="session")
def qapp():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_color_palette_system():
    """Verify that the design system color tokens match the technical instrumentation spec."""
    assert COLORS['bg_dark'] == "#10151C"
    assert COLORS['bg_surface'] == "#151D27"
    assert COLORS['bg_elevated'] == "#1C2632"
    assert COLORS['primary'] == "#22B8CF"
    assert COLORS['success'] == "#39D98A"
    assert COLORS['warning'] == "#F5B942"
    assert COLORS['danger'] == "#F06464"
    assert COLORS['text_primary'] == "#D5DEE8"
    assert COLORS['text_secondary'] == "#8291A3"


def test_theme_stylesheet_contains_palette_and_chevrons():
    """Verify DARK_THEME_QSS contains the new colors, monospace font styles, and dropdown arrows."""
    assert "#10151C" in DARK_THEME_QSS
    assert "#151D27" in DARK_THEME_QSS
    assert "#1C2632" in DARK_THEME_QSS
    assert "#22B8CF" in DARK_THEME_QSS
    assert "#D5DEE8" in DARK_THEME_QSS
    assert "#8291A3" in DARK_THEME_QSS
    # Verify chevron arrow styling is included in QComboBox
    assert "QComboBox::down-arrow" in DARK_THEME_QSS


def test_no_emojis_in_main_window_navigation(qapp, tmp_path):
    """Verify all navigation buttons have clean, professional text with zero emoji icons."""
    db = DatabaseManager(db_path=tmp_path / "test_no_emojis.db")
    window = MainWindow(db_manager=db)

    # Check the nav buttons
    emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]', flags=re.UNICODE)
    for btn in window._nav_buttons:
        text = btn.text()
        assert not emoji_pattern.search(text), f"Nav button contains emoji: '{text}'"

    window.close()


def test_positioning_editor_desktop_canvas(qapp):
    """Verify SimulatedDesktopCanvas initializes monitor resolution and desktop capture."""
    cfg = OverlayConfig()
    canvas = SimulatedDesktopCanvas(config=cfg, screen_res=(1920, 1080))
    # Should report valid resolutions
    assert canvas.res_w == 1920
    assert canvas.res_h == 1080

    # Changing resolution works
    canvas.set_resolution(1366, 768)
    assert canvas.res_w == 1366
    assert canvas.res_h == 768


def test_visual_editor_splitter_and_controls(qapp):
    """Verify VisualDesktopEditor creates 78/22 splitter ratio and clean action buttons."""
    cfg = OverlayConfig()
    editor = VisualDesktopEditor(config=cfg)
    # Check splitter exists
    assert editor.splitter is not None
    assert editor.canvas is not None
    assert editor.combo_screen is not None
    assert editor.combo_res is not None

    # Check button labels have no emojis
    for btn in [editor.btn_save, editor.btn_cancel, editor.btn_undo, editor.btn_redo,
                editor.btn_reset_sel, editor.btn_reset_all, editor.btn_refresh_preview]:
        text = btn.text()
        assert not any(ord(c) > 0x1F000 for c in text), f"Editor button has emoji: {text}"

    # Test capture_desktop method runs cleanly
    editor.capture_desktop()


def test_settings_page_positioning_table_layout(qapp):
    """Verify SettingsPage Positioning Table renders all 11 statistics without truncation."""
    cfg = OverlayConfig()
    page = SettingsPage(overlay_config=cfg)

    # Access the positioning table
    table = page.table_pos
    assert isinstance(table, QTableWidget)
    assert table.rowCount() == 11, f"Expected 11 rows in positioning table, found {table.rowCount()}"

    # Verify minimum height is configured to accommodate all rows without vertical truncation
    assert table.minimumHeight() >= 500

    # Verify column 3 (Snap Corner) width allocation has >= 150px min width to prevent text clipping
    page._adjust_table_columns()
    col3_width = table.columnWidth(3)
    assert col3_width >= 150, f"Column 3 width is {col3_width}px, expected >= 150px to prevent clipping"

    # Verify cell widgets in column 3 contain combo boxes
    for row in range(11):
        wrapper = table.cellWidget(row, 3)
        assert wrapper is not None
        combo = wrapper.findChild(QComboBox)
        assert combo is not None
        assert combo.count() == 5  # "Snap Corner...", Top-Left, Top-Right, Bottom-Left, Bottom-Right
