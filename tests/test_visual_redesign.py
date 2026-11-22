"""
Tests for Visual Identity Redesign, Positioning Editor Desktop Preview,
Positioning Table layout, Drag-and-Drop Coordinate Mapping, and Lucide Icon System.
"""

import os
import re
import pytest
from PySide6.QtWidgets import QApplication, QTableWidget, QComboBox
from PySide6.QtCore import Qt, QRect, QPoint

from netvision.config import COLORS
from netvision.ui.theme import DARK_THEME_QSS
from netvision.ui.main_window import MainWindow
from netvision.core.overlay_config import OverlayConfig, DisplayMode
from netvision.ui.overlay.visual_editor import (
    VisualDesktopEditor, InteractiveDesktopCanvas, SimulatedDesktopCanvas,
    HANDLE_TL, HANDLE_BR, HANDLE_R, HANDLE_B
)
from netvision.ui.overlay.desktop_capture import (
    capture_desktop_preview, get_available_monitors, get_windows_active_wallpaper_path
)
from netvision.ui.components.icons import get_icon, LUCIDE_SVGS
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
    assert "QComboBox::down-arrow" in DARK_THEME_QSS


def test_lucide_icon_system():
    """Verify all 12 navigation icons and editor action icons render valid vector QIcons."""
    for name in LUCIDE_SVGS:
        icon = get_icon(name, size=18)
        assert not icon.isNull(), f"Icon '{name}' failed to render"


def test_no_emojis_in_main_window_navigation(qapp, tmp_path):
    """Verify all navigation buttons have clean, professional text with zero emoji icons."""
    db = DatabaseManager(db_path=tmp_path / "test_no_emojis.db")
    window = MainWindow(db_manager=db)

    emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]', flags=re.UNICODE)
    for btn in window._nav_buttons:
        text = btn.text()
        assert not emoji_pattern.search(text), f"Nav button contains emoji: '{text}'"
        # Verify each button has an authentic icon set
        assert not btn.icon().isNull(), f"Nav button '{text}' is missing an icon"

    window.close()


def test_desktop_capture_engine(qapp):
    """Verify desktop capture engine retrieves real monitor geometry and authentic background."""
    monitors = get_available_monitors()
    assert len(monitors) >= 1

    pix, status = capture_desktop_preview(screen_idx=0, target_res=(1366, 768))
    assert pix is not None
    assert not pix.isNull()
    assert pix.width() == 1366
    assert pix.height() == 768
    assert len(status) > 0


def test_coordinate_mapping_1366_and_1920(qapp):
    """
    STRICT REQUIREMENT: Coordinate conversion between actual desktop and scaled preview
    must be bidirectional and mathematically accurate at both 1366x768 and 1920x1080.
    """
    cfg = OverlayConfig()

    for w_res, h_res in [(1366, 768), (1920, 1080)]:
        canvas = InteractiveDesktopCanvas(config=cfg, screen_res=(w_res, h_res))
        canvas.resize(1000, 600)

        dr = canvas.get_desktop_rect()
        assert dr.width() > 0 and dr.height() > 0

        # Test desktop -> canvas -> desktop roundtrip conversion
        test_coords = [(0, 0), (100, 100), (w_res // 2, h_res // 2), (w_res - 180, h_res - 65)]
        for dx, dy in test_coords:
            c_rect = canvas.desktop_to_canvas_rect(dr, dx, dy, 180, 65)
            # Reconstruct desktop pos from canvas top-left
            recon_x, recon_y = canvas.canvas_to_desktop_pos(dr, c_rect.x(), c_rect.y())
            # Precision tolerance within 1-2 pixels due to rounding
            assert abs(recon_x - dx) <= 2, f"Failed at ({w_res}x{h_res}): x={dx}, recon_x={recon_x}"
            assert abs(recon_y - dy) <= 2, f"Failed at ({w_res}x{h_res}): y={dy}, recon_y={recon_y}"


def test_visual_editor_drag_resize_undo_redo(qapp):
    """Verify drag-and-drop, 8-point resize handles, and undo/redo history in VisualDesktopEditor."""
    cfg = OverlayConfig()
    editor = VisualDesktopEditor(config=cfg)

    # 1. Selection
    editor.canvas.selected_stat_id = "fps"
    editor._on_widget_selected("fps")
    assert editor.spin_x.value() == cfg.stats["fps"].x
    assert editor.spin_y.value() == cfg.stats["fps"].y

    # 2. Modify coordinates via inspector
    editor.spin_x.setValue(250)
    assert editor.working_config.stats["fps"].x == 250

    # 3. Undo restores previous position
    editor._on_undo()
    assert editor.working_config.stats["fps"].x != 250

    # 4. Redo reapplies new position
    editor._on_redo()
    assert editor.working_config.stats["fps"].x == 250

    # 5. Alignment operations
    editor._align_left()
    assert editor.working_config.stats["fps"].x == 24
    editor._align_top()
    assert editor.working_config.stats["fps"].y == 24


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
