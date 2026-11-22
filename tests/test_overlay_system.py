"""
NetVision - Unit and Integration Tests for Statistics Overlay System
Tests OverlayConfig (disabled by default), Multi-Window Independent Widgets,
Presets, Display Modes, Shortcut Manager, Mini Graph Widget, and OverlayManager.
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
from netvision.ui.overlay.floating_widget import FloatingStatWidget
from netvision.ui.overlay.overlay_manager import OverlayManager
from netvision.ui.overlay.stat_detail_dialog import StatDetailDialog
from netvision.ui.overlay.visual_editor import VisualDesktopEditor, SimulatedDesktopCanvas
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


def test_overlay_disabled_by_default():
    """STRICT REQUIREMENT: Overlay must NOT be enabled by default."""
    cfg = OverlayConfig()
    assert cfg.master_enabled is False, "Overlay must be disabled by default"


def test_all_shortcuts_unassigned_by_default():
    """STRICT REQUIREMENT: All keyboard shortcuts must be unassigned by default."""
    cfg = OverlayConfig()
    assert cfg.master_shortcut == ""
    for stat_id, item in cfg.stats.items():
        assert item.shortcut == "", f"Stat {stat_id} should have empty shortcut by default, got '{item.shortcut}'"


def test_display_modes_supported():
    item = StatItemConfig(stat_id="cpu", name="CPU Usage")
    for mode in [DisplayMode.DONT_SHOW, DisplayMode.NUMBERS, DisplayMode.GRAPH]:
        item.mode = mode
        assert item.mode in DisplayMode.CHOICES


def test_overlay_config_serialization():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "test_overlay.json"
        cfg = OverlayConfig()
        cfg.master_enabled = True
        cfg.stats["cpu"].mode = DisplayMode.GRAPH
        cfg.stats["fps"].mode = DisplayMode.NUMBERS

        cfg.save(tmp_path)
        assert tmp_path.exists()

        loaded = OverlayConfig.load(tmp_path)
        assert loaded.master_enabled is True
        assert loaded.stats["cpu"].mode == DisplayMode.GRAPH
        assert loaded.stats["fps"].mode == DisplayMode.NUMBERS


# ==========================================
# 2. Independent Multi-Window Floating Widgets Tests
# ==========================================

def test_independent_floating_widgets_behavior(qapp):
    """
    CRITICAL REQUIREMENT:
    Moving or resizing one widget must NEVER alter another widget.
    """
    fps_item = StatItemConfig(stat_id="fps", name="FPS", x=100, y=100, width=150, height=44)
    cpu_item = StatItemConfig(stat_id="cpu", name="CPU Usage", x=300, y=300, width=180, height=60)

    fps_widget = FloatingStatWidget(fps_item)
    cpu_widget = FloatingStatWidget(cpu_item)

    assert fps_widget.x() == 100
    assert cpu_widget.x() == 300

    # Move FPS widget
    fps_widget.move(500, 200)
    fps_item.x = 500
    fps_item.y = 200

    # Verify CPU widget position did NOT change!
    assert cpu_widget.x() == 300
    assert cpu_widget.y() == 300

    # Resize CPU widget
    cpu_widget.resize(250, 80)
    # Verify FPS widget size did NOT change!
    assert fps_widget.width() == 150

    fps_widget.close()
    cpu_widget.close()


def test_overlay_manager_orchestration(qapp):
    cfg = OverlayConfig()
    cfg.master_enabled = False
    collector = StatisticsCollector(sample_interval_ms=1000)
    manager = OverlayManager(cfg, collector)

    # Initial state: overlay stopped
    assert not collector.is_running
    for w in manager.widgets.values():
        assert not w.isVisible()

    # Start overlay
    manager.start_overlay()
    assert cfg.master_enabled is True
    assert collector.is_running

    # Toggle individual stat
    manager.toggle_stat_visibility("fps")
    assert cfg.stats["fps"].enabled is False

    # Stop overlay
    manager.stop_overlay()
    assert cfg.master_enabled is False
    assert not collector.is_running
    for w in manager.widgets.values():
        assert not w.isVisible()

    manager.close_all()


# ==========================================
# 3. Presets Engine Tests
# ==========================================

def test_presets_application():
    cfg = OverlayConfig()

    # 1. Minimal Preset: only ping, wifi_signal, fps visible
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

    # 3. Detailed Preset: all metrics enabled
    cfg.apply_preset("Detailed")
    assert cfg.active_preset == "Detailed"
    for s_id, item in cfg.stats.items():
        assert item.mode != DisplayMode.DONT_SHOW


# ==========================================
# 4. Shortcut Manager & Conflict Detection Tests
# ==========================================

def test_parse_hotkey_string():
    parsed = parse_hotkey_string("Ctrl+Shift+C")
    assert parsed is not None
    mods, vk = parsed
    assert vk == ord("C")

    parsed_f = parse_hotkey_string("F9")
    assert parsed_f is not None
    _, vk_f = parsed_f
    assert vk_f == 0x78

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
# 5. Mini Graph Sparkline Widget Tests
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
    graph.resize(200, 60)
    graph.repaint()


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


def test_native_gpu_reader():
    gpu_helper = WindowsGpuHelper()
    val = gpu_helper.get_gpu_percent()
    assert isinstance(val, float)
    assert 0.0 <= val <= 100.0
    gpu_helper.close()


def test_statistics_collector_snapshot(qapp):
    collector = StatisticsCollector(sample_interval_ms=1000)
    received = []
    collector.stats_updated.connect(lambda s: received.append(s))

    collector._collect_sample()
    assert len(received) == 1
    snapshot = received[0]

    for expected_key in [
        "fps", "cpu", "gpu", "ram", "net_io",
        "wifi_signal", "ping", "jitter", "packet_loss",
        "download_speed", "upload_speed"
    ]:
        assert expected_key in snapshot
        assert "val" in snapshot[expected_key]
        assert "display" in snapshot[expected_key]
        assert "history" in snapshot[expected_key]

    collector.clean_up()


# ==========================================
# 7. Settings Page Subsections Tests
# ==========================================

def test_settings_page_subsections_and_controls(qapp):
    cfg = OverlayConfig()
    page = SettingsPage(overlay_config=cfg)

    # Verify 7 subsections
    assert page.tab_widget.count() == 7
    tab_titles = [page.tab_widget.tabText(i) for i in range(7)]
    assert any("General" in t for t in tab_titles)
    assert any("Individual" in t for t in tab_titles)
    assert any("Positioning" in t for t in tab_titles)
    assert any("Appearance" in t for t in tab_titles)
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


# ==========================================
# 8. Stat Detail Dialog Tests
# ==========================================

def test_stat_detail_dialog_configuration(qapp):
    item = StatItemConfig(
        stat_id="cpu",
        name="CPU Usage",
        category="system",
        mode=DisplayMode.NUMBERS,
        font_size=12,
        color="#38bdf8",
        width=180,
        height=44,
        x=200,
        y=150
    )
    dlg = StatDetailDialog(item)
    assert dlg.spin_font.value() == 12
    assert dlg.spin_w.value() == 180
    assert dlg.spin_h.value() == 44

    # Change settings in dialog
    dlg.spin_font.setValue(16)
    dlg.spin_w.setValue(220)
    dlg.spin_h.setValue(55)
    idx_graph = dlg.combo_mode.findData(DisplayMode.GRAPH)
    dlg.combo_mode.setCurrentIndex(idx_graph)

    dlg._on_apply_clicked()

    # Verify original item was updated
    assert item.font_size == 16
    assert item.width == 220
    assert item.height == 55
    assert item.mode == DisplayMode.GRAPH
    assert item.enabled is True
    dlg.close()


# ==========================================
# 9. Visual Desktop Editor & Canvas Tests
# ==========================================

def test_visual_desktop_editor_workflow(qapp):
    cfg = OverlayConfig()
    cfg.stats["cpu"].mode = DisplayMode.GRAPH
    cfg.stats["fps"].mode = DisplayMode.NUMBERS

    editor = VisualDesktopEditor(cfg)
    assert editor.canvas is not None
    assert editor.canvas.res_w >= 800
    assert editor.canvas.res_h >= 600

    # Canvas desktop coordinate mapping
    dr = editor.canvas.get_desktop_rect()
    assert dr.width() > 0 and dr.height() > 0

    c_rect = editor.canvas.desktop_to_canvas_rect(dr, 100, 100, 200, 60)
    assert c_rect.width() > 0 and c_rect.height() > 0

    # Select CPU widget
    editor._on_widget_selected("cpu")
    assert editor.lbl_selected_name.text().startswith("Active: CPU Usage")
    assert editor.form_widget.isEnabled()

    # Modify property via panel (setValue automatically triggers valueChanged -> _on_prop_geom_changed)
    editor.spin_x.setValue(350)
    assert editor.working_config.stats["cpu"].x == 350
    # Original config unchanged (working copy isolation)
    assert cfg.stats["cpu"].x != 350

    # Test Undo
    editor._on_undo()
    assert editor.working_config.stats["cpu"].x != 350

    # Test Redo
    editor._on_redo()
    assert editor.working_config.stats["cpu"].x == 350

    # Test Save & Apply signal
    saved_configs = []
    editor.save_and_apply.connect(lambda c: saved_configs.append(c))
    editor._on_save_clicked()
    assert len(saved_configs) == 1
    assert saved_configs[0].stats["cpu"].x == 350

    # Test Cancel signal
    cancels = []
    editor.cancelled.connect(lambda: cancels.append(True))
    editor._on_cancel_clicked()
    assert len(cancels) == 1
    editor.close()


# ==========================================
# 10. Settings Page Visual Editor & Cards Integration
# ==========================================

def test_settings_page_redesigned_ui(qapp, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: QMessageBox.Ok)
    cfg = OverlayConfig()
    page = SettingsPage(overlay_config=cfg)

    # Individual Statistics tab has card widgets
    assert len(page.stat_card_widgets) == 11
    assert "cpu" in page.stat_card_widgets
    assert "fps" in page.stat_card_widgets

    # Filter cards by search
    page.input_stat_search.setText("gpu")
    page._filter_stat_cards()
    assert not page.stat_card_widgets["gpu"].isHidden()
    assert page.stat_card_widgets["cpu"].isHidden()

    page.input_stat_search.setText("")
    page._filter_stat_cards()
    assert not page.stat_card_widgets["cpu"].isHidden()

    # Positioning tab stack integration
    assert page.pos_stack.count() == 2
    assert page.pos_stack.currentIndex() == 0

    # Click Open Visual Overlay Editor
    page.btn_open_visual_editor.click()
    assert page.pos_stack.currentIndex() == 1

    # Cancel returns to page 0
    page.visual_editor.cancelled.emit()
    assert page.pos_stack.currentIndex() == 0

    # Quick preset alignment
    page._align_preset_corner("tl")
    assert page.config.stats["fps"].x == 24
    assert page.config.stats["fps"].y == 24

    page.close()


# ==========================================
# 11. Desktop Overlay Transparency & Widget Lock Tests
# ==========================================

def test_floating_widget_transparency_and_master_lock(qapp):
    item = StatItemConfig(stat_id="fps", name="FPS", x=50, y=50, width=120, height=40)
    widget = FloatingStatWidget(item)

    # Must have transparent background window flags
    assert widget.testAttribute(Qt.WA_TranslucentBackground)
    assert widget.testAttribute(Qt.WA_NoSystemBackground)
    assert widget.windowFlags() & Qt.FramelessWindowHint
    assert widget.windowFlags() & Qt.WindowStaysOnTopHint

    # By default, widget must be master locked to prevent accidental dragging
    assert widget.master_locked is True

    widget.close()
