"""
NetVision - Advanced System & Overlay Settings Page
Organized tabbed interface managing:
1. Overlay Settings (master toggle, opacity, locking, geometry, refresh rate)
2. Statistics (per-stat display modes: Don't Show, Numbers, Graph)
3. Visual Layout Editor (drag-and-drop, 8-point resizing, snapping, undo/redo)
4. Keyboard Shortcuts (individual hotkeys, all unassigned by default, conflict checks)
5. Presets (Minimal, Performance, Detailed, Custom presets, JSON export/import)
6. Network Thresholds & Locations (signal, ping, packet loss, speed thresholds, custom locations)
"""

from typing import List, Dict, Any, Optional
import json
import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSpinBox, QDoubleSpinBox, QLineEdit,
    QListWidget, QMessageBox, QComboBox, QTabWidget, QSlider,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QColorDialog, QFileDialog, QInputDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QKeySequence

from netvision.config import DEFAULT_THRESHOLDS, DEFAULT_PING_TARGETS, COLORS
from netvision.core.overlay_config import (
    OverlayConfig, DisplayMode, StatItemConfig
)
from netvision.ui.overlay.layout_editor import OverlayLayoutEditor

logger = logging.getLogger(__name__)


class KeyRecorderButton(QPushButton):
    """Button that listens for a key combination and captures it."""

    shortcut_recorded = Signal(str)

    def __init__(self, current_key: str = "", parent=None):
        super().__init__(current_key if current_key else "(None)", parent)
        self.current_key = current_key
        self.is_recording = False
        self.setProperty("class", "SecondaryButton")
        self.clicked.connect(self._start_recording)

    def _start_recording(self):
        self.is_recording = True
        self.setText("Press key combination...")
        self.setStyleSheet("background-color: #0284c7; color: #ffffff; font-weight: bold;")
        self.setFocus()

    def keyPressEvent(self, event):
        if not self.is_recording:
            super().keyPressEvent(event)
            return

        key = event.key()
        modifiers = event.modifiers()

        # Ignore standalone modifier presses
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            return

        # If user presses Escape, cancel recording
        if key == Qt.Key_Escape:
            self.is_recording = False
            self.setText(self.current_key if self.current_key else "(None)")
            self.setStyleSheet("")
            return

        # Construct key sequence string
        key_seq = QKeySequence(modifiers | key)
        key_str = key_seq.toString(QKeySequence.PortableText)

        self.is_recording = False
        self.current_key = key_str
        self.setText(key_str)
        self.setStyleSheet("")
        self.shortcut_recorded.emit(key_str)


class SettingsPage(QWidget):
    """Comprehensive settings management page for NetVision."""

    request_save_settings = Signal(dict)
    request_restore_defaults = Signal()
    request_add_location = Signal(str)
    overlay_config_changed = Signal(OverlayConfig)
    shortcut_updated = Signal(str, str)  # (stat_id, shortcut_str)

    def __init__(self, overlay_config: Optional[OverlayConfig] = None, parent=None):
        super().__init__(parent)
        self.config = overlay_config or OverlayConfig.load()
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # Header with Save and Restore Actions
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("System Settings & Customization Hub")
        title.setProperty("class", "PageTitle")
        subtitle = QLabel("Configure real-time statistics overlay, visual editor, global shortcuts, presets, and diagnostic thresholds")
        subtitle.setProperty("class", "PageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_restore_all = QPushButton("↺ Restore All Defaults")
        self.btn_restore_all.setProperty("class", "SecondaryButton")
        self.btn_restore_all.clicked.connect(self._on_restore_clicked)
        header_layout.addWidget(self.btn_restore_all)

        self.btn_save_all = QPushButton("💾 Save All Changes")
        self.btn_save_all.setProperty("class", "PrimaryButton")
        self.btn_save_all.clicked.connect(self._on_save_all_clicked)
        header_layout.addWidget(self.btn_save_all)

        main_layout.addLayout(header_layout)

        # Modern Sub-Tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                background: {COLORS['bg_dark']};
                border-radius: 8px;
                padding: 12px;
            }}
            QTabBar::tab {{
                background: {COLORS['bg_surface']};
                color: {COLORS['text_secondary']};
                padding: 8px 16px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {COLORS['primary_dark']};
                color: {COLORS['text_primary']};
            }}
            QTabBar::tab:hover:!selected {{
                background: {COLORS['bg_surface_hover']};
            }}
        """)

        # Tab 1: Overlay Window Controls
        self.tab_overlay = self._build_overlay_tab()
        self.tab_widget.addTab(self.tab_overlay, "🖥 Overlay Window")

        # Tab 2: Statistics Config (Visibility & Modes)
        self.tab_statistics = self._build_statistics_tab()
        self.tab_widget.addTab(self.tab_statistics, "📊 Statistics Config")

        # Tab 3: Visual Layout Editor
        self.layout_editor = OverlayLayoutEditor(self.config, self)
        self.layout_editor.layout_saved.connect(self._on_editor_layout_changed)
        self.tab_widget.addTab(self.layout_editor, "📐 Layout Editor")

        # Tab 4: Shortcuts (All unassigned by default)
        self.tab_shortcuts = self._build_shortcuts_tab()
        self.tab_widget.addTab(self.tab_shortcuts, "⌨ Shortcuts")

        # Tab 5: Presets Manager
        self.tab_presets = self._build_presets_tab()
        self.tab_widget.addTab(self.tab_presets, "🎨 Presets")

        # Tab 6: Network Thresholds & Locations (Preserved Original Functionality)
        self.tab_thresholds = self._build_thresholds_tab()
        self.tab_widget.addTab(self.tab_thresholds, "⚙ Network Thresholds")

        main_layout.addWidget(self.tab_widget)

    # --- TAB 1: OVERLAY WINDOW SETTINGS ---

    def _build_overlay_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(14)

        card = QFrame()
        card.setProperty("class", "ContentCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        c_layout.setSpacing(14)

        title = QLabel("Floating Overlay Display Settings")
        title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['primary']};")
        c_layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(12)

        # Master Toggle
        self.chk_master_overlay = QCheckBox("Enable Statistics Overlay")
        self.chk_master_overlay.setChecked(self.config.master_enabled)
        self.chk_master_overlay.toggled.connect(self._on_master_toggle)
        grid.addWidget(self.chk_master_overlay, 0, 0, 1, 2)

        # Always-on-Top Toggle
        self.chk_always_top = QCheckBox("Keep Always on Top of Other Windows")
        self.chk_always_top.setChecked(self.config.always_on_top)
        self.chk_always_top.toggled.connect(self._on_overlay_settings_changed)
        grid.addWidget(self.chk_always_top, 0, 2, 1, 2)

        # Lock Window Dragging
        self.chk_lock_pos = QCheckBox("Lock Overlay Position (Prevent Dragging)")
        self.chk_lock_pos.setChecked(self.config.locked)
        self.chk_lock_pos.toggled.connect(self._on_overlay_settings_changed)
        grid.addWidget(self.chk_lock_pos, 1, 0, 1, 2)

        # Refresh Rate
        grid.addWidget(QLabel("Update Frequency (ms):"), 1, 2)
        self.spin_refresh = QSpinBox()
        self.spin_refresh.setRange(300, 5000)
        self.spin_refresh.setSingleStep(250)
        self.spin_refresh.setValue(self.config.refresh_rate_ms)
        self.spin_refresh.valueChanged.connect(self._on_overlay_settings_changed)
        grid.addWidget(self.spin_refresh, 1, 3)

        # Opacity Slider
        grid.addWidget(QLabel("Window Opacity (%):"), 2, 0)
        op_box = QHBoxLayout()
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(20, 100)
        self.slider_opacity.setValue(int(self.config.opacity * 100))
        self.lbl_opacity_val = QLabel(f"{int(self.config.opacity * 100)}%")
        self.slider_opacity.valueChanged.connect(self._on_opacity_slider_changed)
        op_box.addWidget(self.slider_opacity)
        op_box.addWidget(self.lbl_opacity_val)
        grid.addLayout(op_box, 2, 1)

        # Reset Overlay Position Button
        self.btn_reset_pos = QPushButton("📍 Center Overlay on Screen")
        self.btn_reset_pos.setProperty("class", "SecondaryButton")
        self.btn_reset_pos.clicked.connect(self._on_reset_overlay_pos)
        grid.addWidget(self.btn_reset_pos, 2, 2, 1, 2)

        c_layout.addLayout(grid)
        layout.addWidget(card)
        layout.addStretch()
        return widget

    def _on_master_toggle(self, checked: bool):
        self.config.master_enabled = checked
        self.config.save()
        self.overlay_config_changed.emit(self.config)

    def _on_opacity_slider_changed(self, val: int):
        self.lbl_opacity_val.setText(f"{val}%")
        self.config.opacity = val / 100.0
        self.config.save()
        self.overlay_config_changed.emit(self.config)

    def _on_overlay_settings_changed(self):
        self.config.always_on_top = self.chk_always_top.isChecked()
        self.config.locked = self.chk_lock_pos.isChecked()
        self.config.refresh_rate_ms = self.spin_refresh.value()
        self.config.save()
        self.overlay_config_changed.emit(self.config)

    def _on_reset_overlay_pos(self):
        self.config.window_x = 100
        self.config.window_y = 100
        self.config.save()
        self.overlay_config_changed.emit(self.config)
        QMessageBox.information(self, "Position Reset", "Overlay position centered at (100, 100).")

    # --- TAB 2: STATISTICS CONFIGURATION ---

    def _build_statistics_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        card = QFrame()
        card.setProperty("class", "ContentCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(14, 12, 14, 12)

        t_title = QLabel("Individual Statistic Visibility and Display Modes")
        t_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['primary']};")
        c_layout.addWidget(t_title)

        desc = QLabel("Configure each metric to Don't Show (hidden), Numbers, or Graph display mode with custom colors.")
        desc.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        c_layout.addWidget(desc)

        # Table of Statistics
        self.table_stats = QTableWidget()
        self.table_stats.setColumnCount(6)
        self.table_stats.setHorizontalHeaderLabels([
            "Statistic Name", "Category", "Display Mode", "Accent Color", "Font Size / History", "Color Action"
        ])
        self.table_stats.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_stats.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_stats.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_stats.setAlternatingRowColors(True)

        self._populate_stats_table()
        c_layout.addWidget(self.table_stats)

        layout.addWidget(card)
        return widget

    def _populate_stats_table(self):
        self.table_stats.setRowCount(0)
        catalog = self.config.stats

        for row, (stat_id, item) in enumerate(catalog.items()):
            self.table_stats.insertRow(row)

            # 0: Name
            item_name = QTableWidgetItem(item.name)
            item_name.setFlags(item_name.flags() ^ Qt.ItemIsEditable)
            self.table_stats.setItem(row, 0, item_name)

            # 1: Category
            item_cat = QTableWidgetItem(item.category.capitalize())
            item_cat.setFlags(item_cat.flags() ^ Qt.ItemIsEditable)
            self.table_stats.setItem(row, 1, item_cat)

            # 2: Display Mode ComboBox
            combo = QComboBox()
            combo.addItem("Don't Show", DisplayMode.DONT_SHOW)
            combo.addItem("Numbers", DisplayMode.NUMBERS)
            combo.addItem("Graph", DisplayMode.GRAPH)
            idx = combo.findData(item.mode)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            combo.currentIndexChanged.connect(lambda _, s=stat_id, c=combo: self._on_stat_mode_table_changed(s, c))
            self.table_stats.setCellWidget(row, 2, combo)

            # 3: Color preview badge
            lbl_color = QLabel(f" {item.color} ")
            lbl_color.setAlignment(Qt.AlignCenter)
            lbl_color.setStyleSheet(f"background-color: {item.color}; color: #000; font-weight: bold; border-radius: 4px;")
            self.table_stats.setCellWidget(row, 3, lbl_color)

            # 4: Size / Detail
            detail_str = f"Font: {item.font_size}px | Hist: {item.history_len}pts"
            item_detail = QTableWidgetItem(detail_str)
            item_detail.setFlags(item_detail.flags() ^ Qt.ItemIsEditable)
            self.table_stats.setItem(row, 4, item_detail)

            # 5: Color Pick Button
            btn_pick = QPushButton("Pick Color")
            btn_pick.setProperty("class", "SecondaryButton")
            btn_pick.clicked.connect(lambda _, s=stat_id, l=lbl_color: self._on_table_pick_color(s, l))
            self.table_stats.setCellWidget(row, 5, btn_pick)

    def _on_stat_mode_table_changed(self, stat_id: str, combo: QComboBox):
        mode = combo.currentData()
        if stat_id in self.config.stats:
            self.config.stats[stat_id].mode = mode
            self.config.stats[stat_id].enabled = (mode != DisplayMode.DONT_SHOW)
            self.layout_editor.canvas.rebuild_cards()
            self.config.save()
            self.overlay_config_changed.emit(self.config)

    def _on_table_pick_color(self, stat_id: str, lbl_color: QLabel):
        if stat_id not in self.config.stats:
            return
        item = self.config.stats[stat_id]
        c = QColorDialog.getColor(QColor(item.color), self, f"Select Color for {item.name}")
        if c.isValid():
            item.color = c.name()
            lbl_color.setText(f" {item.color} ")
            lbl_color.setStyleSheet(f"background-color: {item.color}; color: #000; font-weight: bold; border-radius: 4px;")
            self.layout_editor.canvas.rebuild_cards()
            self.config.save()
            self.overlay_config_changed.emit(self.config)

    # --- TAB 3: VISUAL LAYOUT EDITOR SIGNAL ---

    def _on_editor_layout_changed(self, new_config: OverlayConfig):
        self.config = new_config
        self.config.save()
        self.overlay_config_changed.emit(self.config)

    # --- TAB 4: KEYBOARD SHORTCUTS ---

    def _build_shortcuts_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        card = QFrame()
        card.setProperty("class", "ContentCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        c_layout.setSpacing(12)

        top_bar = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Individual Metric Keyboard Shortcut Configuration")
        title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['primary']};")
        subtitle = QLabel("Press a shortcut key anytime to toggle that statistic on/off while preserving its display mode.\n(Notice: All shortcuts are unassigned by default).")
        subtitle.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        top_bar.addLayout(title_box)
        top_bar.addStretch()

        self.btn_reset_shortcuts = QPushButton("↺ Unassign All Shortcuts")
        self.btn_reset_shortcuts.setProperty("class", "SecondaryButton")
        self.btn_reset_shortcuts.clicked.connect(self._on_reset_all_shortcuts)
        top_bar.addWidget(self.btn_reset_shortcuts)

        c_layout.addLayout(top_bar)

        # Shortcuts Table
        self.table_shortcuts = QTableWidget()
        self.table_shortcuts.setColumnCount(4)
        self.table_shortcuts.setHorizontalHeaderLabels([
            "Statistic", "Assigned Shortcut", "Bind Key Action", "Clear"
        ])
        self.table_shortcuts.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_shortcuts.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_shortcuts.setAlternatingRowColors(True)

        self._populate_shortcuts_table()
        c_layout.addWidget(self.table_shortcuts)

        layout.addWidget(card)
        return widget

    def _populate_shortcuts_table(self):
        self.table_shortcuts.setRowCount(0)
        for row, (stat_id, item) in enumerate(self.config.stats.items()):
            self.table_shortcuts.insertRow(row)

            # 0: Name
            s_name = QTableWidgetItem(f"{item.name} ({item.category.capitalize()})")
            s_name.setFlags(s_name.flags() ^ Qt.ItemIsEditable)
            self.table_shortcuts.setItem(row, 0, s_name)

            # 1: Current shortcut display badge
            sc_text = item.shortcut if item.shortcut else "Unassigned"
            lbl_badge = QLabel(sc_text)
            lbl_badge.setAlignment(Qt.AlignCenter)
            color_style = "color: #38bdf8; font-weight: bold;" if item.shortcut else "color: #64748b;"
            lbl_badge.setStyleSheet(f"background-color: #1e293b; padding: 4px 8px; border-radius: 4px; {color_style}")
            self.table_shortcuts.setCellWidget(row, 1, lbl_badge)

            # 2: Key Recorder Button
            btn_rec = KeyRecorderButton(item.shortcut)
            btn_rec.shortcut_recorded.connect(
                lambda sc, s=stat_id, l=lbl_badge: self._on_shortcut_recorded(s, sc, l)
            )
            self.table_shortcuts.setCellWidget(row, 2, btn_rec)

            # 3: Clear Button
            btn_clear = QPushButton("Clear")
            btn_clear.setProperty("class", "SecondaryButton")
            btn_clear.clicked.connect(
                lambda _, s=stat_id, b=btn_rec, l=lbl_badge: self._on_shortcut_cleared(s, b, l)
            )
            self.table_shortcuts.setCellWidget(row, 3, btn_clear)

    def _on_shortcut_recorded(self, stat_id: str, shortcut_str: str, lbl_badge: QLabel):
        # Conflict Detection Check
        shortcut_str = shortcut_str.strip()
        if shortcut_str:
            for other_id, other_item in self.config.stats.items():
                if other_id != stat_id and other_item.shortcut.strip().upper() == shortcut_str.upper():
                    QMessageBox.warning(
                        self,
                        "Shortcut Conflict Detected",
                        f"The shortcut '{shortcut_str}' is already assigned to '{other_item.name}'.\nPlease select a different key combination."
                    )
                    self._populate_shortcuts_table()
                    return

        if stat_id in self.config.stats:
            self.config.stats[stat_id].shortcut = shortcut_str
            lbl_badge.setText(shortcut_str if shortcut_str else "Unassigned")
            lbl_badge.setStyleSheet("color: #38bdf8; font-weight: bold; background-color: #1e293b; padding: 4px 8px; border-radius: 4px;")
            self.config.save()
            self.shortcut_updated.emit(stat_id, shortcut_str)

    def _on_shortcut_cleared(self, stat_id: str, btn_rec: KeyRecorderButton, lbl_badge: QLabel):
        if stat_id in self.config.stats:
            self.config.stats[stat_id].shortcut = ""
            btn_rec.setText("(None)")
            btn_rec.current_key = ""
            lbl_badge.setText("Unassigned")
            lbl_badge.setStyleSheet("color: #64748b; background-color: #1e293b; padding: 4px 8px; border-radius: 4px;")
            self.config.save()
            self.shortcut_updated.emit(stat_id, "")

    def _on_reset_all_shortcuts(self):
        for item in self.config.stats.values():
            item.shortcut = ""
        self.config.save()
        self._populate_shortcuts_table()
        for stat_id in self.config.stats.keys():
            self.shortcut_updated.emit(stat_id, "")
        QMessageBox.information(self, "Shortcuts Reset", "All overlay shortcuts have been reset to Unassigned.")

    # --- TAB 5: PRESETS MANAGER ---

    def _build_presets_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        card = QFrame()
        card.setProperty("class", "ContentCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        c_layout.setSpacing(12)

        p_title = QLabel("Overlay Layout Presets Management")
        p_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['primary']};")
        c_layout.addWidget(p_title)

        p_desc = QLabel("Quickly apply curated layouts or save your customized layout as a preset.")
        p_desc.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        c_layout.addWidget(p_desc)

        h_box = QHBoxLayout()

        # Presets List
        self.list_presets = QListWidget()
        self._refresh_presets_list()
        h_box.addWidget(self.list_presets)

        # Actions Column
        actions_box = QVBoxLayout()
        actions_box.setSpacing(8)

        self.btn_apply_preset = QPushButton("✔ Apply Selected Preset")
        self.btn_apply_preset.setProperty("class", "PrimaryButton")
        self.btn_apply_preset.clicked.connect(self._on_apply_preset)
        actions_box.addWidget(self.btn_apply_preset)

        self.btn_save_custom_preset = QPushButton("💾 Save Current as Preset...")
        self.btn_save_custom_preset.setProperty("class", "SecondaryButton")
        self.btn_save_custom_preset.clicked.connect(self._on_save_custom_preset)
        actions_box.addWidget(self.btn_save_custom_preset)

        self.btn_delete_preset = QPushButton("🗑 Delete Custom Preset")
        self.btn_delete_preset.setProperty("class", "SecondaryButton")
        self.btn_delete_preset.clicked.connect(self._on_delete_custom_preset)
        actions_box.addWidget(self.btn_delete_preset)

        actions_box.addSpacing(16)

        self.btn_export_presets = QPushButton("📤 Export to JSON...")
        self.btn_export_presets.setProperty("class", "SecondaryButton")
        self.btn_export_presets.clicked.connect(self._on_export_presets_json)
        actions_box.addWidget(self.btn_export_presets)

        self.btn_import_presets = QPushButton("📥 Import from JSON...")
        self.btn_import_presets.setProperty("class", "SecondaryButton")
        self.btn_import_presets.clicked.connect(self._on_import_presets_json)
        actions_box.addWidget(self.btn_import_presets)

        actions_box.addStretch()
        h_box.addLayout(actions_box)

        c_layout.addLayout(h_box)
        layout.addWidget(card)
        return widget

    def _refresh_presets_list(self):
        self.list_presets.clear()
        builtins = ["Minimal", "Performance", "Detailed"]
        for p in builtins:
            self.list_presets.addItem(f"★ {p} (Built-in)")
        for cp in self.config.custom_presets.keys():
            self.list_presets.addItem(f"👤 {cp} (Custom)")

    def _on_apply_preset(self):
        sel = self.list_presets.currentItem()
        if not sel:
            return
        name = sel.text().split(" ")[1]  # Extract clean name
        self.config.apply_preset(name)
        self.config.save()
        self.layout_editor.spin_win_w.setValue(self.config.window_width)
        self.layout_editor.spin_win_h.setValue(self.config.window_height)
        self.layout_editor.canvas.rebuild_cards()
        self._populate_stats_table()
        self.overlay_config_changed.emit(self.config)
        QMessageBox.information(self, "Preset Applied", f"Preset '{name}' has been successfully applied.")

    def _on_save_custom_preset(self):
        name, ok = QInputDialog.getText(self, "Save Custom Preset", "Enter a unique preset name:")
        if ok and name.strip():
            clean_name = name.strip()
            self.config.save_custom_preset(clean_name)
            self._refresh_presets_list()
            QMessageBox.information(self, "Preset Saved", f"Custom preset '{clean_name}' saved.")

    def _on_delete_custom_preset(self):
        sel = self.list_presets.currentItem()
        if not sel:
            return
        raw = sel.text()
        if "Built-in" in raw:
            QMessageBox.warning(self, "Cannot Delete", "Built-in presets cannot be deleted.")
            return
        name = raw.split(" ")[1]
        if self.config.delete_custom_preset(name):
            self._refresh_presets_list()
            QMessageBox.information(self, "Deleted", f"Custom preset '{name}' removed.")

    def _on_export_presets_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Overlay Configuration", "netvision_overlay_presets.json", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.config.to_dict(), f, indent=2)
                QMessageBox.information(self, "Export Successful", f"Saved configuration to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export: {e}")

    def _on_import_presets_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Overlay Configuration", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.config = OverlayConfig.from_dict(data)
                self.config.save()
                self._refresh_presets_list()
                self._populate_stats_table()
                self._populate_shortcuts_table()
                self.layout_editor.canvas.rebuild_cards()
                self.overlay_config_changed.emit(self.config)
                QMessageBox.information(self, "Import Successful", "Overlay configuration imported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import configuration: {e}")

    # --- TAB 6: NETWORK THRESHOLDS & LOCATIONS (PRESERVED FUNCTIONALITY) ---

    def _build_thresholds_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(14)

        # General Monitoring Defaults
        gen_card = QFrame()
        gen_card.setProperty("class", "ContentCard")
        g_layout = QVBoxLayout(gen_card)
        g_layout.setContentsMargins(16, 12, 16, 12)

        g_title = QLabel("General & Monitoring Defaults")
        g_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['primary']};")
        g_layout.addWidget(g_title)

        g_grid = QGridLayout()
        g_grid.setSpacing(12)

        lbl_target = QLabel("Default Ping Target Host:")
        self.input_default_target = QLineEdit("8.8.8.8")
        self.input_default_target.setPlaceholderText("8.8.8.8 or 1.1.1.1")

        lbl_interval = QLabel("Signal Monitor Polling Interval (seconds):")
        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(1, 10)
        self.spin_interval.setValue(2)

        g_grid.addWidget(lbl_target, 0, 0)
        g_grid.addWidget(self.input_default_target, 0, 1)
        g_grid.addWidget(lbl_interval, 0, 2)
        g_grid.addWidget(self.spin_interval, 0, 3)
        g_layout.addLayout(g_grid)
        layout.addWidget(gen_card)

        # Thresholds Card
        thresh_card = QFrame()
        thresh_card.setProperty("class", "ContentCard")
        t_layout = QVBoxLayout(thresh_card)
        t_layout.setContentsMargins(16, 12, 16, 12)

        t_title = QLabel("Network Quality Evaluation Thresholds")
        t_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['primary']};")
        t_layout.addWidget(t_title)

        grid = QGridLayout()
        grid.setSpacing(12)

        # Signal Thresholds
        grid.addWidget(QLabel("Wi-Fi Signal Excellent (>= %):"), 0, 0)
        self.spin_s_exc = QSpinBox()
        self.spin_s_exc.setRange(50, 100)
        self.spin_s_exc.setValue(DEFAULT_THRESHOLDS["signal"]["excellent"])
        grid.addWidget(self.spin_s_exc, 0, 1)

        grid.addWidget(QLabel("Wi-Fi Signal Good (>= %):"), 0, 2)
        self.spin_s_good = QSpinBox()
        self.spin_s_good.setRange(30, 90)
        self.spin_s_good.setValue(DEFAULT_THRESHOLDS["signal"]["good"])
        grid.addWidget(self.spin_s_good, 0, 3)

        grid.addWidget(QLabel("Wi-Fi Signal Fair (>= %):"), 0, 4)
        self.spin_s_fair = QSpinBox()
        self.spin_s_fair.setRange(10, 70)
        self.spin_s_fair.setValue(DEFAULT_THRESHOLDS["signal"]["fair"])
        grid.addWidget(self.spin_s_fair, 0, 5)

        # Latency Thresholds
        grid.addWidget(QLabel("Ping Latency Excellent (<= ms):"), 1, 0)
        self.spin_l_exc = QSpinBox()
        self.spin_l_exc.setRange(5, 50)
        self.spin_l_exc.setValue(DEFAULT_THRESHOLDS["latency"]["excellent"])
        grid.addWidget(self.spin_l_exc, 1, 1)

        grid.addWidget(QLabel("Ping Latency Good (<= ms):"), 1, 2)
        self.spin_l_good = QSpinBox()
        self.spin_l_good.setRange(20, 100)
        self.spin_l_good.setValue(DEFAULT_THRESHOLDS["latency"]["good"])
        grid.addWidget(self.spin_l_good, 1, 3)

        grid.addWidget(QLabel("Ping Latency Fair (<= ms):"), 1, 4)
        self.spin_l_fair = QSpinBox()
        self.spin_l_fair.setRange(50, 250)
        self.spin_l_fair.setValue(DEFAULT_THRESHOLDS["latency"]["fair"])
        grid.addWidget(self.spin_l_fair, 1, 5)

        # Packet Loss
        grid.addWidget(QLabel("Packet Loss Good (<= %):"), 2, 0)
        self.spin_p_good = QDoubleSpinBox()
        self.spin_p_good.setRange(0.0, 5.0)
        self.spin_p_good.setSingleStep(0.5)
        self.spin_p_good.setValue(DEFAULT_THRESHOLDS["packet_loss"]["good"])
        grid.addWidget(self.spin_p_good, 2, 1)

        grid.addWidget(QLabel("Packet Loss Fair (<= %):"), 2, 2)
        self.spin_p_fair = QDoubleSpinBox()
        self.spin_p_fair.setRange(1.0, 15.0)
        self.spin_p_fair.setSingleStep(0.5)
        self.spin_p_fair.setValue(DEFAULT_THRESHOLDS["packet_loss"]["fair"])
        grid.addWidget(self.spin_p_fair, 2, 3)

        # Download Speed
        grid.addWidget(QLabel("Download Speed Excellent (>= Mbps):"), 3, 0)
        self.spin_d_exc = QDoubleSpinBox()
        self.spin_d_exc.setRange(10.0, 500.0)
        self.spin_d_exc.setValue(DEFAULT_THRESHOLDS["download_speed"]["excellent"])
        grid.addWidget(self.spin_d_exc, 3, 1)

        grid.addWidget(QLabel("Download Speed Good (>= Mbps):"), 3, 2)
        self.spin_d_good = QDoubleSpinBox()
        self.spin_d_good.setRange(5.0, 200.0)
        self.spin_d_good.setValue(DEFAULT_THRESHOLDS["download_speed"]["good"])
        grid.addWidget(self.spin_d_good, 3, 3)

        grid.addWidget(QLabel("Download Speed Fair (>= Mbps):"), 3, 4)
        self.spin_d_fair = QDoubleSpinBox()
        self.spin_d_fair.setRange(1.0, 50.0)
        self.spin_d_fair.setValue(DEFAULT_THRESHOLDS["download_speed"]["fair"])
        grid.addWidget(self.spin_d_fair, 3, 5)

        t_layout.addLayout(grid)
        layout.addWidget(thresh_card)

        # Custom Locations Card
        loc_card = QFrame()
        loc_card.setProperty("class", "ContentCard")
        l_layout = QVBoxLayout(loc_card)
        l_layout.setContentsMargins(16, 12, 16, 12)

        l_title = QLabel("Custom Environment Location Labels")
        l_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['primary']};")
        l_layout.addWidget(l_title)

        add_bar = QHBoxLayout()
        self.input_new_loc = QLineEdit()
        self.input_new_loc.setPlaceholderText("Enter custom location label (e.g. CS Lab 3, Library 2nd Floor, Room 402)...")
        add_bar.addWidget(self.input_new_loc)

        self.btn_add_loc = QPushButton("+ Add Location")
        self.btn_add_loc.setProperty("class", "SecondaryButton")
        self.btn_add_loc.clicked.connect(self._on_add_loc_clicked)
        add_bar.addWidget(self.btn_add_loc)
        l_layout.addLayout(add_bar)

        self.list_locations = QListWidget()
        self.list_locations.setMaximumHeight(90)
        l_layout.addWidget(self.list_locations)

        layout.addWidget(loc_card)
        layout.addStretch()
        return widget

    def set_locations(self, locations: List[str]):
        """Populates existing locations list."""
        self.list_locations.clear()
        for loc in locations:
            self.list_locations.addItem(loc)

    def _on_add_loc_clicked(self):
        name = self.input_new_loc.text().strip()
        if not name:
            return
        self.input_new_loc.clear()
        self.request_add_location.emit(name)

    def load_settings(self, settings_dict: Dict[str, Any]):
        """Populates network threshold UI controls with saved settings."""
        if not settings_dict:
            return

        if "default_ping_target" in settings_dict:
            self.input_default_target.setText(settings_dict["default_ping_target"])

        if "sampling_interval_sec" in settings_dict:
            try:
                self.spin_interval.setValue(int(settings_dict["sampling_interval_sec"]))
            except ValueError:
                pass

        if "thresholds_json" in settings_dict:
            try:
                th = json.loads(settings_dict["thresholds_json"])
                sig = th.get("signal", {})
                if "excellent" in sig: self.spin_s_exc.setValue(int(sig["excellent"]))
                if "good" in sig: self.spin_s_good.setValue(int(sig["good"]))
                if "fair" in sig: self.spin_s_fair.setValue(int(sig["fair"]))

                lat = th.get("latency", {})
                if "excellent" in lat: self.spin_l_exc.setValue(int(lat["excellent"]))
                if "good" in lat: self.spin_l_good.setValue(int(lat["good"]))
                if "fair" in lat: self.spin_l_fair.setValue(int(lat["fair"]))

                loss = th.get("packet_loss", {})
                if "good" in loss: self.spin_p_good.setValue(float(loss["good"]))
                if "fair" in loss: self.spin_p_fair.setValue(float(loss["fair"]))

                spd = th.get("download_speed", {})
                if "excellent" in spd: self.spin_d_exc.setValue(float(spd["excellent"]))
                if "good" in spd: self.spin_d_good.setValue(float(spd["good"]))
                if "fair" in spd: self.spin_d_fair.setValue(float(spd["fair"]))
            except Exception:
                pass

    def _on_restore_clicked(self):
        """Restores default values across thresholds and overlay."""
        self.spin_s_exc.setValue(DEFAULT_THRESHOLDS["signal"]["excellent"])
        self.spin_s_good.setValue(DEFAULT_THRESHOLDS["signal"]["good"])
        self.spin_s_fair.setValue(DEFAULT_THRESHOLDS["signal"]["fair"])

        self.spin_l_exc.setValue(DEFAULT_THRESHOLDS["latency"]["excellent"])
        self.spin_l_good.setValue(DEFAULT_THRESHOLDS["latency"]["good"])
        self.spin_l_fair.setValue(DEFAULT_THRESHOLDS["latency"]["fair"])

        self.spin_p_good.setValue(DEFAULT_THRESHOLDS["packet_loss"]["good"])
        self.spin_p_fair.setValue(DEFAULT_THRESHOLDS["packet_loss"]["fair"])

        self.spin_d_exc.setValue(DEFAULT_THRESHOLDS["download_speed"]["excellent"])
        self.spin_d_good.setValue(DEFAULT_THRESHOLDS["download_speed"]["good"])
        self.spin_d_fair.setValue(DEFAULT_THRESHOLDS["download_speed"]["fair"])

        self.input_default_target.setText("8.8.8.8")
        self.spin_interval.setValue(2)

        self.config.apply_preset("Detailed")
        self.config.save()
        self._populate_stats_table()
        self._populate_shortcuts_table()
        self.layout_editor.canvas.rebuild_cards()
        self.overlay_config_changed.emit(self.config)

        self.request_restore_defaults.emit()
        QMessageBox.information(self, "Defaults Restored", "System thresholds and overlay settings restored to defaults.")

    def _on_save_all_clicked(self):
        """Validates threshold orderings, saves overlay config and network thresholds."""
        # 1. Validate Signal Threshold Ordering (excellent > good > fair)
        s_exc = self.spin_s_exc.value()
        s_good = self.spin_s_good.value()
        s_fair = self.spin_s_fair.value()
        if not (s_exc > s_good > s_fair):
            QMessageBox.warning(
                self,
                "Invalid Threshold Ordering",
                f"Wi-Fi Signal thresholds must satisfy: Excellent ({s_exc}%) > Good ({s_good}%) > Fair ({s_fair}%)."
            )
            return

        # 2. Validate Latency Threshold Ordering (excellent < good < fair)
        l_exc = self.spin_l_exc.value()
        l_good = self.spin_l_good.value()
        l_fair = self.spin_l_fair.value()
        if not (l_exc < l_good < l_fair):
            QMessageBox.warning(
                self,
                "Invalid Threshold Ordering",
                f"Latency thresholds must satisfy: Excellent ({l_exc} ms) < Good ({l_good} ms) < Fair ({l_fair} ms)."
            )
            return

        # 3. Validate Packet Loss Ordering (good < fair)
        p_good = self.spin_p_good.value()
        p_fair = self.spin_p_fair.value()
        if not (p_good < p_fair):
            QMessageBox.warning(
                self,
                "Invalid Threshold Ordering",
                f"Packet loss thresholds must satisfy: Good ({p_good}%) < Fair ({p_fair}%)."
            )
            return

        # 4. Validate Download Speed Ordering (excellent > good > fair)
        d_exc = self.spin_d_exc.value()
        d_good = self.spin_d_good.value()
        d_fair = self.spin_d_fair.value()
        if not (d_exc > d_good > d_fair):
            QMessageBox.warning(
                self,
                "Invalid Threshold Ordering",
                f"Download speed thresholds must satisfy: Excellent ({d_exc} Mbps) > Good ({d_good} Mbps) > Fair ({d_fair} Mbps)."
            )
            return

        target_host = self.input_default_target.text().strip() or "8.8.8.8"
        interval = self.spin_interval.value()

        thresholds = {
            "signal": {"excellent": s_exc, "good": s_good, "fair": s_fair, "poor": 0},
            "latency": {"excellent": l_exc, "good": l_good, "fair": l_fair, "poor": l_fair * 2},
            "packet_loss": {"excellent": 0.0, "good": p_good, "fair": p_fair, "poor": p_fair * 1.5},
            "download_speed": {"excellent": d_exc, "good": d_good, "fair": d_fair, "poor": 0.0}
        }

        payload = {
            "thresholds_json": json.dumps(thresholds),
            "default_ping_target": target_host,
            "sampling_interval_sec": str(interval)
        }

        # Save Overlay Config
        self.config.save()
        self.overlay_config_changed.emit(self.config)

        # Emit Network Settings
        self.request_save_settings.emit(payload)
        QMessageBox.information(self, "Settings Saved", "All overlay, shortcut, preset, and network threshold settings saved successfully.")
