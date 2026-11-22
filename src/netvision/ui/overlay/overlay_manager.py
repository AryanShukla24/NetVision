"""
NetVision - Multi-Window Overlay Orchestration Manager
Coordinates independent floating statistic windows, telemetry dispatching,
per-widget positioning, and master lifecycle (disabled by default).
"""

from typing import Dict, Any, Optional
import logging
from PySide6.QtCore import QObject, Signal

from netvision.core.overlay_config import OverlayConfig, DisplayMode, get_default_stats_catalog
from netvision.core.stats_collector import StatisticsCollector
from netvision.ui.overlay.floating_widget import FloatingStatWidget

logger = logging.getLogger(__name__)


class OverlayManager(QObject):
    """
    Manages the lifecycle, positioning, and telemetry forwarding
    for independent floating statistic windows.
    """

    overlay_state_changed = Signal(bool)     # Emits master_enabled
    stat_toggled = Signal(str, bool)         # (stat_id, is_visible)
    config_updated = Signal()

    def __init__(self, config: OverlayConfig, stats_collector: StatisticsCollector, parent=None):
        super().__init__(parent)
        self.config = config
        self.stats_collector = stats_collector
        self.widgets: Dict[str, FloatingStatWidget] = {}

        # Wire telemetry signal from collector
        self.stats_collector.stats_updated.connect(self._on_telemetry_updated)

        # Build floating widgets
        self._initialize_widgets()

        # By strict requirement: ensure overlay is disabled initially if config says False
        if self.config.master_enabled:
            self.start_overlay()
        else:
            self.stop_overlay()

    def _initialize_widgets(self):
        """Creates an independent FloatingStatWidget for each supported statistic."""
        for stat_id, item in self.config.stats.items():
            widget = FloatingStatWidget(item, master_locked=self.config.master_locked)
            widget.position_changed.connect(self._on_widget_moved)
            widget.size_changed.connect(self._on_widget_resized)
            self.widgets[stat_id] = widget

    def start_overlay(self):
        """Enables the overlay and displays all visible statistic windows."""
        self.config.master_enabled = True
        self.config.save()

        for stat_id, item in self.config.stats.items():
            widget = self.widgets.get(stat_id)
            if widget:
                widget.apply_config(item)
                if item.enabled and item.mode != DisplayMode.DONT_SHOW:
                    widget.show()
                else:
                    widget.hide()

        # Start non-blocking telemetry collector
        self.stats_collector.start(self.config.refresh_rate_ms)
        self.overlay_state_changed.emit(True)
        logger.info("Statistics overlay started (independent multi-window mode)")

    def stop_overlay(self):
        """Disables the overlay and hides all floating windows."""
        self.config.master_enabled = False
        self.config.save()

        for widget in self.widgets.values():
            widget.hide()

        # Stop telemetry polling to save 100% background CPU
        self.stats_collector.stop()
        self.overlay_state_changed.emit(False)
        logger.info("Statistics overlay stopped")

    def toggle_overlay(self):
        """Master toggle for the entire overlay system."""
        if self.config.master_enabled:
            self.stop_overlay()
        else:
            self.start_overlay()

    def toggle_stat_visibility(self, stat_id: str):
        """Toggles an individual statistic window on/off without altering its display mode."""
        if stat_id not in self.config.stats or stat_id not in self.widgets:
            return

        item = self.config.stats[stat_id]
        widget = self.widgets[stat_id]

        item.enabled = not item.enabled
        self.config.save()

        if self.config.master_enabled:
            if item.enabled and item.mode != DisplayMode.DONT_SHOW:
                widget.apply_config(item)
                widget.show()
            else:
                widget.hide()

        self.stat_toggled.emit(stat_id, item.enabled)
        self.config_updated.emit()

    def apply_config(self, new_config: OverlayConfig):
        """Applies updated configuration across all floating widgets."""
        self.config = new_config
        self.config.save()

        # Update each widget
        for stat_id, item in self.config.stats.items():
            if stat_id in self.widgets:
                widget = self.widgets[stat_id]
                widget.set_master_locked(self.config.master_locked)
                widget.apply_config(item)

                if self.config.master_enabled and item.enabled and item.mode != DisplayMode.DONT_SHOW:
                    widget.show()
                else:
                    widget.hide()

        if self.config.master_enabled:
            self.stats_collector.set_interval(self.config.refresh_rate_ms)
            if not self.stats_collector.is_running:
                self.stats_collector.start(self.config.refresh_rate_ms)
        else:
            self.stats_collector.stop()

        self.config_updated.emit()

    def reset_widget_position(self, stat_id: str):
        """Resets a single widget's position to its default corner coordinate."""
        default_catalog = get_default_stats_catalog()
        if stat_id in default_catalog and stat_id in self.config.stats:
            def_item = default_catalog[stat_id]
            item = self.config.stats[stat_id]
            item.x = def_item.x
            item.y = def_item.y
            self.config.save()
            if stat_id in self.widgets:
                self.widgets[stat_id].move(item.x, item.y)
            self.config_updated.emit()

    def reset_all_positions(self):
        """Distributes all statistic windows across standard screen corners."""
        default_catalog = get_default_stats_catalog()
        for stat_id, def_item in default_catalog.items():
            if stat_id in self.config.stats:
                item = self.config.stats[stat_id]
                item.x = def_item.x
                item.y = def_item.y
                if stat_id in self.widgets:
                    self.widgets[stat_id].move(item.x, item.y)
        self.config.save()
        self.config_updated.emit()

    def set_master_locked(self, locked: bool):
        self.config.master_locked = locked
        self.config.save()
        for widget in self.widgets.values():
            widget.set_editing_mode(not locked)
        self.config_updated.emit()

    def set_editing_mode(self, editing: bool):
        """Toggles on-desktop interactive editing vs locked click-through mode."""
        self.set_master_locked(not editing)

    def _on_widget_moved(self, stat_id: str, x: int, y: int):
        if stat_id in self.config.stats:
            self.config.stats[stat_id].x = x
            self.config.stats[stat_id].y = y
            self.config.save()
            self.config_updated.emit()

    def _on_widget_resized(self, stat_id: str, w: int, h: int):
        if stat_id in self.config.stats:
            item = self.config.stats[stat_id]
            if item.mode == DisplayMode.GRAPH:
                item.graph_width = w
                item.graph_height = h
            else:
                item.width = w
                item.height = h
            self.config.save()
            self.config_updated.emit()

    def _on_telemetry_updated(self, snapshot: Dict[str, Any]):
        """Forwards real-time telemetry only to currently visible floating windows."""
        if not self.config.master_enabled:
            return

        for stat_id, data in snapshot.items():
            widget = self.widgets.get(stat_id)
            if widget and widget.isVisible():
                display_str = data.get("display", "--")
                history = data.get("history", [])
                val = data.get("val", 0.0)
                widget.update_value(display_str, history, val)

    def close_all(self):
        """Closes all floating windows on application exit."""
        self.stats_collector.stop()
        for widget in self.widgets.values():
            widget.close()
