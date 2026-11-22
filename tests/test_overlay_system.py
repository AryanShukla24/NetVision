"""
NetVision - Unit and Integration Tests for Statistics Overlay System
Tests OverlayConfig, Presets, Display Modes, Shortcut Manager,
Mini Graph Widget, Visual Layout Editor, and Telemetry Collector.
"""

import os
import json
import tempfile
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QRect

from netvision.core.overlay_config import (
    OverlayConfig, StatItemConfig, DisplayMode, get_default_stats_catalog
)
from netvision.core.stats_collector import (
    StatisticsCollector, NativeSystemMetrics, WindowsGpuHelper
)
from netvision.core.shortcut_manager import (
    GlobalShortcutManager, parse_hotkey_string
)
from netvision.ui.overlay.mini_graph import MiniGraphWidget
from netvision.ui.overlay.overlay_window import StatisticsOverlayWindow, NumberBadgeCard
from netvision.ui.overlay.layout_editor import (
    EditorCanvasWidget, OverlayLayoutEditor, DraggableCardWidget
)
from netvision.ui.pages.settings_page import SettingsPage


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# ==========================================
# 1. Overlay Config & Catalog Tests
# ==========================================

def test_catalog_contains_all_11_statistics():
    catalog = get_default_stats_catalog()
    expected_stats = [
        "fps", "cpu", "gpu", "ram", "net_io",
        "wifi_signal", "ping", "jitter", "packet_loss",
        "download_speed", "upload_speed"
    ]
    assert len(catalog) == 11
    for s in expected_stats:
        assert s in catalog
        assert isinstance(catalog[s], StatItemConfig)


def test_all_shortcuts_unassigned_by_default():
    """STRICT REQUIREMENT: All keyboard shortcuts must be unassigned by default."""
    cfg = OverlayConfig()
    for stat_id, item in cfg.stats.items():
        assert item.shortcut == "", f"Stat {stat_id} should have empty shortcut by default, got '{item.shortcut}'"


def test_display_modes_supported():
    """Verify each stat item supports hidden, numbers, and graph modes."""
    item = StatItemConfig(stat_id="cpu", name="CPU Usage")
    for mode in [DisplayMode.DONT_SHOW, DisplayMode.NUMBERS, DisplayMode.GRAPH]:
        item.mode = mode
        assert item.mode in DisplayMode.CHOICES


def test_overlay_config_serialization():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "test_overlay.json"
        cfg = OverlayConfig()
        cfg.opacity = 0.75
        cfg.locked = True
        cfg.stats["cpu"].mode = DisplayMode.GRAPH
        cfg.stats["fps"].mode = DisplayMode.NUMBERS

        cfg.save(tmp_path)
        assert tmp_path.exists()

        loaded = OverlayConfig.load(tmp_path)
        assert loaded.opacity == 0.75
        assert loaded.locked is True
        assert loaded.stats["cpu"].mode == DisplayMode.GRAPH
        assert loaded.stats["fps"].mode == DisplayMode.NUMBERS


# ==========================================
# 2. Presets Engine Tests
# ==========================================

def test_presets_application():
    cfg = OverlayConfig()

    # 1. Minimal Preset: only ping, wifi_signal, fps in numbers mode
    cfg.apply_preset("Minimal")
    assert cfg.active_preset == "Minimal"
    assert cfg.stats["fps"].mode == DisplayMode.NUMBERS
    assert cfg.stats["ping"].mode == DisplayMode.NUMBERS
    assert cfg.stats["wifi_signal"].mode == DisplayMode.NUMBERS
    assert cfg.stats["cpu"].mode == DisplayMode.DONT_SHOW
    assert cfg.stats["gpu"].mode == DisplayMode.DONT_SHOW

    # 2. Performance Preset: gaming & system focus
    cfg.apply_preset("Performance")
    assert cfg.active_preset == "Performance"
    assert cfg.stats["cpu"].mode == DisplayMode.GRAPH
    assert cfg.stats["gpu"].mode == DisplayMode.GRAPH
    assert cfg.stats["fps"].mode == DisplayMode.NUMBERS
    assert cfg.stats["ram"].mode == DisplayMode.NUMBERS
    assert cfg.stats["wifi_signal"].mode == DisplayMode.DONT_SHOW

    # 3. Detailed Preset: all metrics enabled
    cfg.apply_preset("Detailed")
    assert cfg.active_preset == "Detailed"
    for s_id, item in cfg.stats.items():
        assert item.mode != DisplayMode.DONT_SHOW, f"Metric {s_id} should be visible in Detailed preset"


def test_custom_presets_management():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "custom_presets.json"
        cfg = OverlayConfig()
        cfg.stats["fps"].mode = DisplayMode.GRAPH
        cfg.stats["cpu"].font_size = 18

        cfg.save_custom_preset("GamerUltra")
        assert "GamerUltra" in cfg.custom_presets
        assert cfg.active_preset == "GamerUltra"

        # Apply different preset then restore custom
        cfg.apply_preset("Minimal")
        assert cfg.stats["fps"].mode == DisplayMode.NUMBERS
        cfg.apply_preset("GamerUltra")
        assert cfg.stats["fps"].mode == DisplayMode.GRAPH

        # Delete custom preset
        deleted = cfg.delete_custom_preset("GamerUltra")
        assert deleted is True
        assert "GamerUltra" not in cfg.custom_presets


# ==========================================
# 3. Shortcut Manager & Conflict Detection Tests
# ==========================================

def test_parse_hotkey_string():
    parsed = parse_hotkey_string("Ctrl+Shift+C")
    assert parsed is not None
    mods, vk = parsed
    assert vk == ord("C")

    parsed_f = parse_hotkey_string("F9")
    assert parsed_f is not None
    _, vk_f = parsed_f
    assert vk_f == 0x78  # VK_F9

    assert parse_hotkey_string("") is None
    assert parse_hotkey_string("InvalidKeyNameXYZ") is None


def test_shortcut_conflict_detection(qapp):
    mgr = GlobalShortcutManager()
    mgr.register_shortcut("cpu", "Ctrl+Shift+C")

    # Conflict on identical shortcut for another metric
    conflict = mgr.check_conflict("Ctrl+Shift+C", "gpu")
    assert conflict == "cpu"

    # No conflict when checking same stat
    no_conflict = mgr.check_conflict("Ctrl+Shift+C", "cpu")
    assert no_conflict is None

    # No conflict for unused shortcut
    unused = mgr.check_conflict("Ctrl+Shift+G", "gpu")
    assert unused is None

    mgr.clean_up()


# ==========================================
# 4. Mini Graph Sparkline Widget Tests
# ==========================================

def test_mini_graph_widget_rendering(qapp):
    graph = MiniGraphWidget(
        title="CPU Usage",
        unit="%",
        color="#38bdf8",
        scale_mode="fixed",
        min_val=0.0,
        max_val=100.0,
        history_len=30
    )
    data = [10.0, 25.5, 40.0, 32.0, 78.5, 55.0]
    graph.set_data(data, current_val=55.0)

    assert len(graph._data) == 6
    assert graph._current_val == 55.0

    # Ensure update and resize don't throw
    graph.resize(200, 60)
    graph.repaint()


# ==========================================
# 5. Visual Layout Editor & Canvas Tests
# ==========================================

def test_editor_canvas_snapping_and_guides(qapp):
    cfg = OverlayConfig()
    cfg.apply_preset("Detailed")
    cfg.snap_to_grid = True
    cfg.grid_size = 10

    # 1. Test pure grid snapping without alignment guides
    cfg.show_alignment_guides = False
    canvas = EditorCanvasWidget(cfg)
    assert len(canvas.cards) > 0

    snapped_x, snapped_y = canvas.apply_snapping("cpu", 13, 27, 100, 40)
    assert snapped_x % 10 == 0
    assert snapped_y % 10 == 0

    # 2. Test alignment guide snapping (snaps to nearby card edge at x=12)
    canvas.show_guides = True
    guide_x, _ = canvas.apply_snapping("cpu", 13, 27, 100, 40)
    assert guide_x == 12  # Aligns to card edge at 12


def test_editor_undo_redo_stack(qapp):
    cfg = OverlayConfig()
    canvas = EditorCanvasWidget(cfg)

    orig_w = cfg.window_width
    assert not canvas.can_undo()

    # Modify width and record
    cfg.window_width = 650
    canvas.record_history_state()
    assert canvas.can_undo()

    # Undo
    canvas.undo()
    assert cfg.window_width == orig_w
    assert canvas.can_redo()

    # Redo
    canvas.redo()
    assert cfg.window_width == 650


# ==========================================
# 6. Statistics Collector Tests
# ==========================================

def test_native_system_metrics():
    sys_metrics = NativeSystemMetrics()
    mem = sys_metrics.get_memory_info()
    assert "percent" in mem
    assert "total_gb" in mem
    assert mem["total_gb"] > 0
    assert 0.0 <= mem["percent"] <= 100.0

    cpu = sys_metrics.get_cpu_percent()
    assert isinstance(cpu, float)
    assert 0.0 <= cpu <= 100.0


def test_statistics_collector_snapshot(qapp):
    collector = StatisticsCollector(sample_interval_ms=1000)
    received = []
    collector.stats_updated.connect(lambda s: received.append(s))

    collector._collect_sample()
    assert len(received) == 1
    snapshot = received[0]

    # Verify all 11 metrics are present in the snapshot
    for expected_key in [
        "fps", "cpu", "gpu", "ram", "net_io",
        "wifi_signal", "ping", "jitter", "packet_loss",
        "download_speed", "upload_speed"
    ]:
        assert expected_key in snapshot
        assert "val" in snapshot[expected_key]
        assert "display" in snapshot[expected_key]
        assert "history" in snapshot[expected_key]

    collector.stop()


# ==========================================
# 7. Settings Page Tabbed Architecture Tests
# ==========================================

def test_settings_page_tabs_and_controls(qapp):
    cfg = OverlayConfig()
    page = SettingsPage(overlay_config=cfg)

    # Verify 6 sub-tabs
    assert page.tab_widget.count() == 6
    tab_titles = [page.tab_widget.tabText(i) for i in range(6)]
    assert any("Overlay" in t for t in tab_titles)
    assert any("Statistics" in t for t in tab_titles)
    assert any("Layout Editor" in t for t in tab_titles)
    assert any("Shortcuts" in t for t in tab_titles)
    assert any("Presets" in t for t in tab_titles)
    assert any("Thresholds" in t for t in tab_titles)

    # Verify Network Thresholds controls exist and can load settings
    test_settings = {
        "default_ping_target": "1.1.1.1",
        "sampling_interval_sec": "4",
        "thresholds_json": json.dumps({
            "signal": {"excellent": 80, "good": 60, "fair": 35},
            "latency": {"excellent": 25, "good": 50, "fair": 90},
            "packet_loss": {"good": 0.5, "fair": 2.0},
            "download_speed": {"excellent": 100.0, "good": 40.0, "fair": 15.0}
        })
    }
    page.load_settings(test_settings)
    assert page.input_default_target.text() == "1.1.1.1"
    assert page.spin_interval.value() == 4
    assert page.spin_s_exc.value() == 80
