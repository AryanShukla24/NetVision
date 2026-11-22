"""
NetVision - Comprehensive Settings Page
Features dedicated subsections for:
1. General (master overlay toggle, start/stop, individual widget visibility, position lock)
2. Individual Statistics (mode, opacity, font size, dimensions, colors)
3. Positioning (individual X/Y, reset position per widget, quick corner snap, reset all)
4. Appearance (transparent background by default, subtle bg toggle, shadow, rounded corners)
5. Shortcuts (master toggle hotkey, per-statistic hotkeys, conflict detection, unassigned by default)
6. Presets (Minimal, Performance, Detailed, Custom presets, JSON export/import)
7. Network Thresholds & Locations (Wi-Fi, latency, loss, speed evaluation thresholds, location manager)
"""

from typing import List, Dict, Any, Optional
import json
import logging
import copy
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSpinBox, QDoubleSpinBox, QLineEdit,
    QListWidget, QMessageBox, QComboBox, QTabWidget, QSlider,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QColorDialog, QFileDialog, QInputDialog, QScrollArea, QGroupBox,
    QStackedWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QGuiApplication

from netvision.config import DEFAULT_THRESHOLDS, DEFAULT_PING_TARGETS, COLORS
from netvision.core.overlay_config import (
    OverlayConfig, DisplayMode, StatItemConfig, get_default_stats_catalog
)
from netvision.ui.overlay.stat_detail_dialog import StatDetailDialog
from netvision.ui.overlay.visual_editor import VisualDesktopEditor
from netvision.ui.components.toast import ToastNotification

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
        self.setText("Press shortcut keys...")
        self.setStyleSheet(f"background-color: {COLORS['primary_dark']}; color: #ffffff; font-weight: bold;")
        self.setFocus()

    def keyPressEvent(self, event):
        if not self.is_recording:
            super().keyPressEvent(event)
            return

        key = event.key()
        modifiers = event.modifiers()

        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            return

        if key == Qt.Key_Escape:
            self.is_recording = False
            self.setText(self.current_key if self.current_key else "(None)")
            self.setStyleSheet("")
            return

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
        self.toast = ToastNotification(self)

    def show_toast(self, message: str, toast_type: str = "success", duration_ms: int = 3500):
        """Displays non-blocking animated toast feedback."""
        if hasattr(self, "toast") and self.toast:
            self.toast.show_toast(message, toast_type=toast_type, duration_ms=duration_ms)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "toast") and self.toast:
            self.toast._position_toast()
        self._adjust_table_columns()

    def showEvent(self, event):
        super().showEvent(event)
        self._adjust_table_columns()

    def _wrap_cell_widget(self, widget: QWidget, align=Qt.AlignCenter) -> QWidget:
        """Wraps a cell widget inside a transparent container layout for precise vertical and horizontal alignment."""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setAlignment(align)
        layout.addWidget(widget)
        return container

    def _adjust_table_columns(self):
        """Proportionally distributes column widths to prevent cut-off headers, clipped dropdowns, and button overflow."""
        if hasattr(self, "table_shortcuts") and self.table_shortcuts:
            viewport_w = self.table_shortcuts.viewport().width()
            if viewport_w > 120:
                c0 = int(viewport_w * 0.35)
                c1 = int(viewport_w * 0.22)
                c2 = int(viewport_w * 0.25)
                c3 = max(60, viewport_w - c0 - c1 - c2 - 2)
                self.table_shortcuts.setColumnWidth(0, c0)
                self.table_shortcuts.setColumnWidth(1, c1)
                self.table_shortcuts.setColumnWidth(2, c2)
                self.table_shortcuts.setColumnWidth(3, c3)

        if hasattr(self, "table_pos") and self.table_pos:
            viewport_w = self.table_pos.viewport().width()
            if viewport_w > 120:
                c0 = max(120, int(viewport_w * 0.25))
                c1 = max(75, int(viewport_w * 0.13))
                c2 = max(75, int(viewport_w * 0.13))
                c3 = max(150, int(viewport_w * 0.24))
                c4 = max(85, int(viewport_w * 0.13))
                c5 = max(55, viewport_w - c0 - c1 - c2 - c3 - c4 - 2)
                self.table_pos.setColumnWidth(0, c0)
                self.table_pos.setColumnWidth(1, c1)
                self.table_pos.setColumnWidth(2, c2)
                self.table_pos.setColumnWidth(3, c3)
                self.table_pos.setColumnWidth(4, c4)
                self.table_pos.setColumnWidth(5, c5)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # Header with Save and Restore Actions
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("System Settings & Customization Hub")
        title.setProperty("class", "PageTitle")
        subtitle = QLabel("Configure independent floating widgets, appearance, positioning, shortcuts, and network diagnostics")
        subtitle.setProperty("class", "PageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_restore_all = QPushButton("Restore Defaults")
        self.btn_restore_all.setProperty("class", "SecondaryButton")
        self.btn_restore_all.clicked.connect(self._on_restore_clicked)
        header_layout.addWidget(self.btn_restore_all)

        self.btn_save_all = QPushButton("Save All Changes")
        self.btn_save_all.setProperty("class", "PrimaryButton")
        self.btn_save_all.clicked.connect(self._on_save_all_clicked)
        header_layout.addWidget(self.btn_save_all)

        main_layout.addLayout(header_layout)

        # Tabbed Subsections
        self.tab_widget = QTabWidget()

        # 1. General Subsection
        self.tab_general = self._build_general_tab()
        self.tab_widget.addTab(self.tab_general, "General")

        # 2. Individual Statistics Subsection
        self.tab_stats = self._build_statistics_tab()
        self.tab_widget.addTab(self.tab_stats, "Individual Statistics")

        # 3. Positioning Subsection
        self.tab_positioning = self._build_positioning_tab()
        self.tab_widget.addTab(self.tab_positioning, "Positioning")
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # 4. Appearance Subsection
        self.tab_appearance = self._build_appearance_tab()
        self.tab_widget.addTab(self.tab_appearance, "Appearance")

        # 5. Shortcuts Subsection
        self.tab_shortcuts = self._build_shortcuts_tab()
        self.tab_widget.addTab(self.tab_shortcuts, "Shortcuts")

        # 6. Presets Subsection
        self.tab_presets = self._build_presets_tab()
        self.tab_widget.addTab(self.tab_presets, "Presets")

        # 7. Network Thresholds Subsection
        self.tab_thresholds = self._build_thresholds_tab()
        self.tab_widget.addTab(self.tab_thresholds, "Thresholds & Locations")

        main_layout.addWidget(self.tab_widget)
        self.tab_widget.currentChanged.connect(lambda _: self._adjust_table_columns())

    # --- SUBSECTION 1: GENERAL ---

    def _build_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        card = QFrame()
        card.setProperty("class", "ContentCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        c_layout.setSpacing(12)

        # Status Banner
        self.banner_frame = QFrame()
        self._update_status_banner()
        c_layout.addWidget(self.banner_frame)

        # Master Controls Bar
        ctrl_box = QHBoxLayout()
        self.btn_start_overlay = QPushButton("Start Overlay")
        self.btn_start_overlay.setProperty("class", "PrimaryButton")
        self.btn_start_overlay.clicked.connect(self._on_start_overlay_clicked)
        ctrl_box.addWidget(self.btn_start_overlay)

        self.btn_stop_overlay = QPushButton("Stop Overlay")
        self.btn_stop_overlay.setProperty("class", "SecondaryButton")
        self.btn_stop_overlay.clicked.connect(self._on_stop_overlay_clicked)
        ctrl_box.addWidget(self.btn_stop_overlay)

        self.btn_reset_overlay = QPushButton("Reset Overlay Settings")
        self.btn_reset_overlay.setProperty("class", "SecondaryButton")
        self.btn_reset_overlay.clicked.connect(self._on_reset_overlay_settings)
        ctrl_box.addWidget(self.btn_reset_overlay)

        ctrl_box.addStretch()
        c_layout.addLayout(ctrl_box)

        # Lock Positioning & Update Rate
        grid = QGridLayout()
        grid.setSpacing(10)

        self.chk_master_enabled = QCheckBox("Enable Statistics Overlay System")
        self.chk_master_enabled.setChecked(self.config.master_enabled)
        self.chk_master_enabled.toggled.connect(self._on_master_enabled_toggled)
        grid.addWidget(self.chk_master_enabled, 0, 0, 1, 2)

        self.chk_master_lock = QCheckBox("Lock All Widgets (100% Click-Through in Games)")
        self.chk_master_lock.setToolTip("When locked, mouse clicks pass directly through to games underneath without interference. Uncheck to drag and resize widgets on desktop.")
        self.chk_master_lock.setChecked(self.config.master_locked)
        self.chk_master_lock.toggled.connect(self._on_master_lock_toggled)
        grid.addWidget(self.chk_master_lock, 0, 2, 1, 2)

        grid.addWidget(QLabel("Update Frequency:"), 1, 0)
        self.spin_refresh = QSpinBox()
        self.spin_refresh.setRange(300, 5000)
        self.spin_refresh.setSingleStep(250)
        self.spin_refresh.setValue(self.config.refresh_rate_ms)
        self.spin_refresh.valueChanged.connect(self._on_refresh_rate_changed)
        grid.addWidget(self.spin_refresh, 1, 1)

        c_layout.addLayout(grid)

        # Quick Widget Visibility Checklist
        grp_vis = QGroupBox("Quick Widget Visibility Toggles")
        grp_vis.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {COLORS['primary']}; border: 1px solid {COLORS['border_light']}; border-radius: 4px; margin-top: 8px; padding-top: 12px; }}")
        vis_layout = QGridLayout(grp_vis)
        vis_layout.setSpacing(8)

        self.vis_checkboxes: Dict[str, QCheckBox] = {}
        for idx, (stat_id, item) in enumerate(self.config.stats.items()):
            row = idx // 4
            col = idx % 4
            chk = QCheckBox(item.name)
            chk.setChecked(item.enabled and item.mode != DisplayMode.DONT_SHOW)
            chk.toggled.connect(lambda checked, s=stat_id: self._on_quick_vis_toggled(s, checked))
            vis_layout.addWidget(chk, row, col)
            self.vis_checkboxes[stat_id] = chk

        c_layout.addWidget(grp_vis)
        layout.addWidget(card)
        layout.addStretch()
        return widget

    def _update_status_banner(self):
        if self.banner_frame.layout():
            QWidget().setLayout(self.banner_frame.layout())

        b_layout = QHBoxLayout(self.banner_frame)
        b_layout.setContentsMargins(12, 8, 12, 8)

        if self.config.master_enabled:
            self.banner_frame.setStyleSheet(f"background-color: {COLORS['success_bg']}; border: 1px solid {COLORS['success']}; border-radius: 4px;")
            lbl = QLabel("● Statistics Overlay is ACTIVE — Floating widgets are visible on desktop.")
            lbl.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold; font-size: 12px;")
        else:
            self.banner_frame.setStyleSheet(f"background-color: rgba(90, 107, 127, 0.12); border: 1px solid {COLORS['border_light']}; border-radius: 4px;")
            lbl = QLabel("○ Statistics Overlay is DISABLED — No widgets are rendered and telemetry is paused.")
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: bold; font-size: 12px;")

        b_layout.addWidget(lbl)

    def _on_start_overlay_clicked(self):
        self.config.master_enabled = True
        self.chk_master_enabled.setChecked(True)
        self._update_status_banner()
        self.config.save()
        self.overlay_config_changed.emit(self.config)

    def _on_stop_overlay_clicked(self):
        self.config.master_enabled = False
        self.chk_master_enabled.setChecked(False)
        self._update_status_banner()
        self.config.save()
        self.overlay_config_changed.emit(self.config)

    def _on_master_enabled_toggled(self, checked: bool):
        self.config.master_enabled = checked
        self._update_status_banner()
        self.config.save()
        self.overlay_config_changed.emit(self.config)

    def _on_master_lock_toggled(self, checked: bool):
        self.config.master_locked = checked
        self.config.save()
        self.overlay_config_changed.emit(self.config)

    def _on_refresh_rate_changed(self, val: int):
        self.config.refresh_rate_ms = val
        self.config.save()
        self.overlay_config_changed.emit(self.config)

    def _on_quick_vis_toggled(self, stat_id: str, checked: bool):
        if stat_id in self.config.stats:
            item = self.config.stats[stat_id]
            item.enabled = checked
            if checked and item.mode == DisplayMode.DONT_SHOW:
                item.mode = DisplayMode.NUMBERS
            elif not checked:
                item.mode = DisplayMode.DONT_SHOW
            self.config.save()
            self.overlay_config_changed.emit(self.config)
            self._populate_stats_table()

    def _on_reset_overlay_settings(self):
        self.config.apply_preset("Performance")
        self.config.master_enabled = False
        self.config.save()
        self._update_status_banner()
        self.chk_master_enabled.setChecked(False)
        self._populate_stats_table()
        self._populate_positioning_table()
        self.overlay_config_changed.emit(self.config)
        self.show_toast("Overlay settings restored to standard performance defaults (disabled).", "info")

    # --- SUBSECTION 2: INDIVIDUAL STATISTICS ---

    def _build_statistics_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setProperty("class", "ContentCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(14, 12, 14, 12)
        c_layout.setSpacing(10)

        top_bar = QHBoxLayout()
        title_box = QVBoxLayout()
        t_title = QLabel("Individual Statistic Customization")
        t_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['primary']};")
        desc = QLabel("Each metric operates as an independent floating window. Switch display mode directly, or click Configure for deep customization.")
        desc.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        title_box.addWidget(t_title)
        title_box.addWidget(desc)
        top_bar.addLayout(title_box)
        top_bar.addStretch()

        self.input_stat_search = QLineEdit()
        self.input_stat_search.setPlaceholderText("Search metrics...")
        self.input_stat_search.setFixedWidth(160)
        self.input_stat_search.textChanged.connect(self._filter_stat_cards)
        top_bar.addWidget(self.input_stat_search)

        self.combo_stat_filter = QComboBox()
        self.combo_stat_filter.addItems(["All Categories", "System", "Performance", "Network"])
        self.combo_stat_filter.currentIndexChanged.connect(self._filter_stat_cards)
        top_bar.addWidget(self.combo_stat_filter)

        self.chk_stat_enabled_only = QCheckBox("Active Only")
        self.chk_stat_enabled_only.toggled.connect(self._filter_stat_cards)
        top_bar.addWidget(self.chk_stat_enabled_only)

        c_layout.addLayout(top_bar)

        # Scroll Area for Card-Based Statistic Rows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: 1px solid {COLORS['border']}; border-radius: 4px; background-color: {COLORS['bg_surface']}; }}")

        self.stats_cards_container = QWidget()
        self.stats_cards_container.setStyleSheet("background-color: transparent;")
        self.stats_cards_layout = QVBoxLayout(self.stats_cards_container)
        self.stats_cards_layout.setContentsMargins(8, 8, 8, 8)
        self.stats_cards_layout.setSpacing(6)

        scroll.setWidget(self.stats_cards_container)
        c_layout.addWidget(scroll)

        # Hidden table for backward compatibility
        self.table_stats = QTableWidget()
        self.table_stats.setVisible(False)

        self._populate_stats_table()
        layout.addWidget(card)
        return widget

    def _populate_stats_table(self):
        while self.stats_cards_layout.count():
            item = self.stats_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.stat_card_widgets: Dict[str, QFrame] = {}

        cat_colors = {
            "performance": (COLORS["primary"], COLORS["primary_subtle"]),
            "system": (COLORS["purple"], "rgba(176, 124, 250, 0.12)"),
            "network": (COLORS["success"], COLORS["success_bg"])
        }

        for stat_id, item in self.config.stats.items():
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_elevated']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                    padding: 3px;
                }}
                QFrame:hover {{
                    border-color: {COLORS['border_light']};
                }}
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(10, 6, 10, 6)
            card_layout.setSpacing(12)

            # 1. Category Pill
            cat_fg, cat_bg = cat_colors.get(item.category.lower(), (COLORS["primary"], COLORS["primary_subtle"]))
            lbl_cat = QLabel(item.category.upper())
            lbl_cat.setFixedWidth(75)
            lbl_cat.setAlignment(Qt.AlignCenter)
            lbl_cat.setStyleSheet(f"""
                background-color: {cat_bg};
                color: {cat_fg};
                font-size: 10px;
                font-weight: 800;
                padding: 3px 5px;
                border-radius: 3px;
                border: 1px solid {cat_fg}40;
            """)
            card_layout.addWidget(lbl_cat)

            # 2. Statistic Name
            name_box = QVBoxLayout()
            name_box.setSpacing(1)
            lbl_name = QLabel(item.name)
            lbl_name.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLORS['text_bright']};")
            name_box.addWidget(lbl_name)
            card_layout.addLayout(name_box, stretch=2)

            # 3. Display Mode Selector
            combo = QComboBox()
            combo.setFixedWidth(130)
            combo.addItem("Don't Show", DisplayMode.DONT_SHOW)
            combo.addItem("Numbers", DisplayMode.NUMBERS)
            combo.addItem("Graph", DisplayMode.GRAPH)
            idx = combo.findData(item.mode)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            combo.currentIndexChanged.connect(lambda _, s=stat_id, c=combo: self._on_stat_mode_changed(s, c))
            card_layout.addWidget(combo)

            # 4. Font Size & Dimensions Badge
            dim_str = f"{item.width}×{item.height} px" if item.mode != DisplayMode.GRAPH else f"{item.graph_width}×{item.graph_height} px"
            lbl_spec = QLabel(f"{item.font_size} pt  |  {dim_str}")
            lbl_spec.setAlignment(Qt.AlignCenter)
            lbl_spec.setFixedWidth(130)
            lbl_spec.setStyleSheet(f"""
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_secondary']};
                font-size: 11px;
                font-family: 'Consolas', monospace;
                font-weight: 500;
                padding: 4px 6px;
                border-radius: 3px;
                border: 1px solid {COLORS['border']};
            """)
            card_layout.addWidget(lbl_spec)

            # 5. Accent Color Swatch
            lbl_color = QPushButton(f"  {item.color}  ")
            lbl_color.setFixedWidth(85)
            lbl_color.setStyleSheet(f"""
                QPushButton {{
                    background-color: {item.color};
                    color: #000000;
                    font-weight: 800;
                    font-size: 11px;
                    border: none;
                    border-radius: 3px;
                    padding: 4px;
                }}
                QPushButton:hover {{
                    border: 2px solid #ffffff;
                }}
            """)
            lbl_color.setToolTip("Click to select accent color")
            lbl_color.clicked.connect(lambda _, s=stat_id: self._on_pick_stat_color_direct(s))
            card_layout.addWidget(lbl_color)

            # 6. Configure Button
            btn_cfg = QPushButton("Configure")
            btn_cfg.setProperty("class", "SecondaryButton")
            btn_cfg.setFixedWidth(90)
            btn_cfg.clicked.connect(lambda _, s=stat_id: self._on_open_stat_dialog(s))
            card_layout.addWidget(btn_cfg)

            self.stats_cards_layout.addWidget(card)
            self.stat_card_widgets[stat_id] = card

        self.stats_cards_layout.addStretch()

    def _filter_stat_cards(self):
        query = self.input_stat_search.text().strip().lower()
        cat_filter = self.combo_stat_filter.currentText().lower()
        active_only = self.chk_stat_enabled_only.isChecked()

        for stat_id, card in self.stat_card_widgets.items():
            item = self.config.stats.get(stat_id)
            if not item:
                continue

            matches_search = (not query) or (query in item.name.lower()) or (query in item.category.lower())
            matches_cat = (cat_filter == "all categories") or (item.category.lower() == cat_filter)
            matches_active = (not active_only) or (item.enabled and item.mode != DisplayMode.DONT_SHOW)

            card.setVisible(matches_search and matches_cat and matches_active)

    def _on_stat_mode_changed(self, stat_id: str, combo: QComboBox):
        if stat_id in self.config.stats:
            mode = combo.currentData()
            self.config.stats[stat_id].mode = mode
            self.config.stats[stat_id].enabled = (mode != DisplayMode.DONT_SHOW)
            self.config.save()
            self.overlay_config_changed.emit(self.config)
            if stat_id in self.vis_checkboxes:
                self.vis_checkboxes[stat_id].setChecked(mode != DisplayMode.DONT_SHOW)

    def _on_pick_stat_color_direct(self, stat_id: str):
        if stat_id not in self.config.stats:
            return
        item = self.config.stats[stat_id]
        c = QColorDialog.getColor(QColor(item.color), self, f"Select Accent Color for {item.name}")
        if c.isValid():
            item.color = c.name()
            self.config.save()
            self.overlay_config_changed.emit(self.config)
            self._populate_stats_table()

    def _on_open_stat_dialog(self, stat_id: str):
        if stat_id not in self.config.stats:
            return
        item = self.config.stats[stat_id]
        dlg = StatDetailDialog(item, self)
        if dlg.exec():
            self.config.save()
            self.overlay_config_changed.emit(self.config)
            self._populate_stats_table()
            self._populate_positioning_table()
            if stat_id in self.vis_checkboxes:
                self.vis_checkboxes[stat_id].setChecked(item.enabled and item.mode != DisplayMode.DONT_SHOW)

    # --- SUBSECTION 3: POSITIONING & VISUAL OVERLAY EDITOR ---

    def _build_positioning_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.pos_stack = QStackedWidget()

        # Page 0: Positioning Overview & Coordinates Table
        scroll_overview = QScrollArea()
        scroll_overview.setWidgetResizable(True)
        scroll_overview.setFrameShape(QFrame.NoFrame)
        scroll_overview.setStyleSheet("background: transparent;")

        page_overview = QWidget()
        page_overview.setStyleSheet("background: transparent;")
        o_layout = QVBoxLayout(page_overview)
        o_layout.setSpacing(10)
        o_layout.setContentsMargins(10, 8, 10, 8)

        card = QFrame()
        card.setProperty("class", "ContentCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(14, 12, 14, 12)
        c_layout.setSpacing(10)

        # Header with Title & Resolution
        top_row = QHBoxLayout()
        t_box = QVBoxLayout()
        title = QLabel("Desktop Widget Coordinates & Positioning")
        title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['primary']};")
        subtitle = QLabel("Every statistic is an independent floating transparent window. Align via the Visual Overlay Editor or adjust precise coordinates below.")
        subtitle.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        top_row.addLayout(t_box)
        top_row.addStretch()

        primary = QGuiApplication.primaryScreen()
        res_str = f"{primary.size().width()} × {primary.size().height()} px" if primary else "1366 × 768 px"
        lbl_res = QLabel(f"Display: {res_str}")
        lbl_res.setStyleSheet(f"font-weight: 600; color: {COLORS['text_secondary']}; font-size: 11px; padding: 4px 8px; background-color: {COLORS['bg_input']}; border-radius: 3px; border: 1px solid {COLORS['border']};")
        top_row.addWidget(lbl_res)
        c_layout.addLayout(top_row)

        # High-efficiency Visual Editor Launch Banner
        launch_banner = QFrame()
        launch_banner.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_surface']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 4px;
                padding: 10px;
            }}
        """)
        l_layout = QHBoxLayout(launch_banner)
        l_layout.setContentsMargins(10, 6, 10, 6)

        l_text_box = QVBoxLayout()
        l_title = QLabel("Interactive Visual Overlay Workspace")
        l_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {COLORS['text_bright']};")
        l_desc = QLabel("Displays live desktop preview with edge snapping, 8-point resize handles, and real-time positioning.")
        l_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        l_text_box.addWidget(l_title)
        l_text_box.addWidget(l_desc)
        l_layout.addLayout(l_text_box)
        l_layout.addStretch()

        self.btn_open_visual_editor = QPushButton("Open Visual Overlay Editor")
        self.btn_open_visual_editor.setProperty("class", "PrimaryButton")
        self.btn_open_visual_editor.clicked.connect(self._open_visual_editor)
        l_layout.addWidget(self.btn_open_visual_editor)
        c_layout.addWidget(launch_banner)

        # Quick Layout Preset Buttons Bar
        quick_bar = QHBoxLayout()
        lbl_quick = QLabel("Quick Presets:")
        lbl_quick.setStyleSheet(f"font-weight: 600; color: {COLORS['text_primary']}; font-size: 11px;")
        quick_bar.addWidget(lbl_quick)

        for label, corner in [
            ("Top-Left", "tl"),
            ("Top-Right", "tr"),
            ("4-Corners HUD", "hud"),
            ("Bottom-Left", "bl"),
            ("Bottom-Right", "br")
        ]:
            btn = QPushButton(label)
            btn.setProperty("class", "SecondaryButton")
            btn.clicked.connect(lambda _, c=corner: self._align_preset_corner(c))
            quick_bar.addWidget(btn)

        quick_bar.addStretch()

        btn_reset_all_pos = QPushButton("Reset All Coordinates")
        btn_reset_all_pos.setProperty("class", "SecondaryButton")
        btn_reset_all_pos.clicked.connect(self._on_reset_all_positions)
        quick_bar.addWidget(btn_reset_all_pos)
        c_layout.addLayout(quick_bar)

        # Coordinates Reference Table with Guaranteed Height for all 11 rows
        self.table_pos = QTableWidget()
        self.table_pos.setColumnCount(6)
        self.table_pos.setHorizontalHeaderLabels([
            "Statistic", "X Coordinate", "Y Coordinate", "Quick Snap Corner", "Reset Single", "Lock"
        ])
        self.table_pos.verticalHeader().setVisible(False)
        self.table_pos.verticalHeader().setDefaultSectionSize(44)
        self.table_pos.setAlternatingRowColors(False)
        self.table_pos.setShowGrid(True)
        self.table_pos.setMinimumHeight(520)
        self.table_pos.horizontalHeader().setStretchLastSection(True)

        self._populate_positioning_table()
        c_layout.addWidget(self.table_pos)
        o_layout.addWidget(card)

        scroll_overview.setWidget(page_overview)
        self.pos_stack.addWidget(scroll_overview)

        # Page 1: Embedded Visual Desktop Editor
        self.visual_editor = VisualDesktopEditor(self.config, self)
        self.visual_editor.save_and_apply.connect(self._on_visual_editor_saved)
        self.visual_editor.cancelled.connect(self._on_visual_editor_cancelled)
        self.pos_stack.addWidget(self.visual_editor)

        layout.addWidget(self.pos_stack)
        return widget

    def _on_tab_changed(self, index: int):
        if index == 2:  # Positioning tab
            if hasattr(self, 'visual_editor'):
                self.visual_editor.capture_desktop()
                self.visual_editor._apply_splitter_proportions()

    def _open_visual_editor(self):
        self.visual_editor.working_config = copy.deepcopy(self.config)
        self.visual_editor.original_config = copy.deepcopy(self.config)
        self.visual_editor.canvas.set_config(self.visual_editor.working_config)
        self.visual_editor._history = [copy.deepcopy(self.config.to_dict())]
        self.visual_editor._history_idx = 0
        self.visual_editor._update_undo_redo_ui()
        self.pos_stack.setCurrentIndex(1)
        self.visual_editor.capture_desktop()
        self.visual_editor._apply_splitter_proportions()

    def _on_visual_editor_saved(self, new_config: OverlayConfig):
        self.config = new_config
        self.config.save()
        self.overlay_config_changed.emit(self.config)
        self._populate_stats_table()
        self._populate_positioning_table()
        self.pos_stack.setCurrentIndex(0)
        self.show_toast("Visual overlay layout saved and applied to your desktop.", "success")

    def _on_visual_editor_cancelled(self):
        self.pos_stack.setCurrentIndex(0)

    def _populate_positioning_table(self):
        self.table_pos.setRowCount(0)
        for row, (stat_id, item) in enumerate(self.config.stats.items()):
            self.table_pos.insertRow(row)

            # 0: Name
            s_name = QTableWidgetItem(f"  {item.name} ({item.mode.capitalize()})")
            s_name.setFlags(s_name.flags() ^ Qt.ItemIsEditable)
            s_name.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table_pos.setItem(row, 0, s_name)

            # 1: X Coordinate
            spin_x = QSpinBox()
            spin_x.setRange(0, 7680)
            spin_x.setValue(item.x)
            spin_x.setMinimumHeight(28)
            spin_x.valueChanged.connect(lambda v, s=stat_id: self._on_coord_changed(s, x=v))
            self.table_pos.setCellWidget(row, 1, self._wrap_cell_widget(spin_x, Qt.AlignCenter))

            # 2: Y Coordinate
            spin_y = QSpinBox()
            spin_y.setRange(0, 4320)
            spin_y.setValue(item.y)
            spin_y.setMinimumHeight(28)
            spin_y.valueChanged.connect(lambda v, s=stat_id: self._on_coord_changed(s, y=v))
            self.table_pos.setCellWidget(row, 2, self._wrap_cell_widget(spin_y, Qt.AlignCenter))

            # 3: Quick Snap Corner
            combo_corner = QComboBox()
            combo_corner.addItem("Snap Corner...", "")
            combo_corner.addItem("Top-Left", (24, 24))
            combo_corner.addItem("Top-Right", (1180, 24))
            combo_corner.addItem("Bottom-Left", (24, 700))
            combo_corner.addItem("Bottom-Right", (1180, 700))
            combo_corner.setMinimumHeight(28)
            combo_corner.currentIndexChanged.connect(
                lambda idx, s=stat_id, c=combo_corner, sx=spin_x, sy=spin_y: self._on_snap_corner(s, c, sx, sy)
            )
            self.table_pos.setCellWidget(row, 3, self._wrap_cell_widget(combo_corner, Qt.AlignCenter))

            # 4: Reset single button
            btn_res = QPushButton("Reset Pos")
            btn_res.setProperty("class", "SecondaryButton")
            btn_res.setMinimumHeight(28)
            btn_res.clicked.connect(lambda _, s=stat_id, sx=spin_x, sy=spin_y: self._on_reset_single_pos(s, sx, sy))
            self.table_pos.setCellWidget(row, 4, self._wrap_cell_widget(btn_res, Qt.AlignCenter))

            # 5: Lock checkbox
            chk_lock = QCheckBox("Lock")
            chk_lock.setChecked(item.is_locked)
            chk_lock.toggled.connect(lambda chk, s=stat_id: self._on_single_lock_toggled(s, chk))
            self.table_pos.setCellWidget(row, 5, self._wrap_cell_widget(chk_lock, Qt.AlignCenter))

        self._adjust_table_columns()

    def _adjust_table_columns(self):
        w = max(700, self.table_pos.viewport().width())
        self.table_pos.setColumnWidth(0, int(w * 0.28))
        self.table_pos.setColumnWidth(1, int(w * 0.15))
        self.table_pos.setColumnWidth(2, int(w * 0.15))
        self.table_pos.setColumnWidth(3, max(150, int(w * 0.24)))
        self.table_pos.setColumnWidth(4, max(85, int(w * 0.10)))
        self.table_pos.setColumnWidth(5, max(55, int(w * 0.08)))

    def _align_preset_corner(self, corner: str):
        primary = QGuiApplication.primaryScreen()
        screen_w = primary.size().width() if primary else 1366
        screen_h = primary.size().height() if primary else 768

        enabled_stats = [item for item in self.config.stats.values() if item.mode != DisplayMode.DONT_SHOW]
        if not enabled_stats:
            enabled_stats = list(self.config.stats.values())[:4]

        if corner == "tl":
            cur_y = 24
            for item in enabled_stats:
                item.x = 24
                item.y = cur_y
                cur_y += (item.graph_height if item.mode == DisplayMode.GRAPH else item.height) + 12
        elif corner == "tr":
            cur_y = 24
            for item in enabled_stats:
                w = item.graph_width if item.mode == DisplayMode.GRAPH else item.width
                item.x = max(24, screen_w - w - 24)
                item.y = cur_y
                cur_y += (item.graph_height if item.mode == DisplayMode.GRAPH else item.height) + 12
        elif corner == "bl":
            cur_y = screen_h - 60
            for item in reversed(enabled_stats):
                h = item.graph_height if item.mode == DisplayMode.GRAPH else item.height
                item.x = 24
                item.y = max(24, cur_y - h)
                cur_y -= (h + 12)
        elif corner == "br":
            cur_y = screen_h - 60
            for item in reversed(enabled_stats):
                w = item.graph_width if item.mode == DisplayMode.GRAPH else item.width
                h = item.graph_height if item.mode == DisplayMode.GRAPH else item.height
                item.x = max(24, screen_w - w - 24)
                item.y = max(24, cur_y - h)
                cur_y -= (h + 12)
        elif corner == "hud":
            corners = [
                (24, 24),
                (max(24, screen_w - 220), 24),
                (24, max(24, screen_h - 80)),
                (max(24, screen_w - 220), max(24, screen_h - 80))
            ]
            for idx, item in enumerate(enabled_stats):
                cx, cy = corners[idx % 4]
                item.x = cx
                item.y = cy

        self.config.save()
        self.overlay_config_changed.emit(self.config)
        self._populate_stats_table()
        self._populate_positioning_table()


    def _on_coord_changed(self, stat_id: str, x: Optional[int] = None, y: Optional[int] = None):
        if stat_id in self.config.stats:
            item = self.config.stats[stat_id]
            if x is not None: item.x = x
            if y is not None: item.y = y
            self.config.save()
            self.overlay_config_changed.emit(self.config)

    def _on_snap_corner(self, stat_id: str, combo: QComboBox, spin_x: QSpinBox, spin_y: QSpinBox):
        data = combo.currentData()
        if data and isinstance(data, tuple):
            nx, ny = data
            spin_x.setValue(nx)
            spin_y.setValue(ny)
            combo.setCurrentIndex(0)

    def _on_reset_single_pos(self, stat_id: str, spin_x: QSpinBox, spin_y: QSpinBox):
        catalog = get_default_stats_catalog()
        if stat_id in catalog:
            def_item = catalog[stat_id]
            spin_x.setValue(def_item.x)
            spin_y.setValue(def_item.y)

    def _on_single_lock_toggled(self, stat_id: str, locked: bool):
        if stat_id in self.config.stats:
            self.config.stats[stat_id].is_locked = locked
            self.config.save()
            self.overlay_config_changed.emit(self.config)

    def _on_reset_all_positions(self):
        catalog = get_default_stats_catalog()
        for stat_id, def_item in catalog.items():
            if stat_id in self.config.stats:
                self.config.stats[stat_id].x = def_item.x
                self.config.stats[stat_id].y = def_item.y
        self.config.save()
        self._populate_positioning_table()
        self.overlay_config_changed.emit(self.config)
        self.show_toast("All floating widgets returned to default screen positions.", "info")

    # --- SUBSECTION 4: APPEARANCE ---

    def _build_appearance_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        card = QFrame()
        card.setProperty("class", "ContentCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        c_layout.setSpacing(12)

        t_title = QLabel("Floating Widget Appearance & Transparency")
        t_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['primary']};")
        c_layout.addWidget(t_title)

        grid = QGridLayout()
        grid.setSpacing(12)

        # Transparent Background Master
        self.chk_transparent = QCheckBox("Genuinely Transparent Background (No heavy boxes or borders)")
        self.chk_transparent.setChecked(self.config.transparent_bg)
        self.chk_transparent.toggled.connect(self._on_appearance_changed)
        grid.addWidget(self.chk_transparent, 0, 0, 1, 2)

        # Subtle background toggle
        self.chk_subtle_bg = QCheckBox("Enable Optional Subtle Tinted Background for Readability")
        self.chk_subtle_bg.setChecked(not self.config.transparent_bg)
        self.chk_subtle_bg.toggled.connect(self._on_subtle_bg_toggled)
        grid.addWidget(self.chk_subtle_bg, 1, 0, 1, 2)

        # Global Opacity Slider
        grid.addWidget(QLabel("Widget Master Opacity:"), 2, 0)
        op_box = QHBoxLayout()
        self.slider_master_op = QSlider(Qt.Horizontal)
        self.slider_master_op.setRange(20, 100)
        self.slider_master_op.setValue(int(self.config.global_opacity * 100))
        self.lbl_master_op = QLabel(f"{int(self.config.global_opacity * 100)}%")
        self.slider_master_op.valueChanged.connect(self._on_master_opacity_slider)
        op_box.addWidget(self.slider_master_op)
        op_box.addWidget(self.lbl_master_op)
        grid.addLayout(op_box, 2, 1)

        # Text Drop Shadow Checkbox
        self.chk_shadow = QCheckBox("High-Contrast Text Drop Shadow (Guarantees legibility on any game/wallpaper)")
        self.chk_shadow.setChecked(True)
        self.chk_shadow.toggled.connect(self._on_appearance_changed)
        grid.addWidget(self.chk_shadow, 3, 0, 1, 2)

        c_layout.addLayout(grid)
        layout.addWidget(card)
        layout.addStretch()
        return widget

    def _on_subtle_bg_toggled(self, checked: bool):
        self.config.transparent_bg = not checked
        self.chk_transparent.setChecked(not checked)
        for item in self.config.stats.values():
            item.show_subtle_bg = checked
            item.bg_opacity = 0.35 if checked else 0.0
        self.config.save()
        self.overlay_config_changed.emit(self.config)

    def _on_master_opacity_slider(self, val: int):
        self.lbl_master_op.setText(f"{val}%")
        self.config.global_opacity = val / 100.0
        for item in self.config.stats.values():
            item.opacity = self.config.global_opacity
        self.config.save()
        self.overlay_config_changed.emit(self.config)

    def _on_appearance_changed(self):
        trans = self.chk_transparent.isChecked()
        self.config.transparent_bg = trans
        self.chk_subtle_bg.setChecked(not trans)
        for item in self.config.stats.values():
            item.show_subtle_bg = not trans
            item.bg_opacity = 0.35 if not trans else 0.0
            item.show_shadow = self.chk_shadow.isChecked()
        self.config.save()
        self.overlay_config_changed.emit(self.config)

    # --- SUBSECTION 5: SHORTCUTS ---

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
        title = QLabel("Global Keyboard Shortcuts (All Unassigned by Default)")
        title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['primary']};")
        subtitle = QLabel("Bind global hotkeys to toggle individual widgets or the entire overlay system from any game or application.")
        subtitle.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        top_bar.addLayout(title_box)
        top_bar.addStretch()

        self.btn_unassign_all = QPushButton("Unassign All Shortcuts")
        self.btn_unassign_all.setProperty("class", "SecondaryButton")
        self.btn_unassign_all.clicked.connect(self._on_unassign_all_shortcuts)
        top_bar.addWidget(self.btn_unassign_all)

        c_layout.addLayout(top_bar)

        # Master Shortcut Bar
        m_bar = QHBoxLayout()
        m_bar.addWidget(QLabel("Master Toggle (Enable/Disable All):"))
        self.btn_master_rec = KeyRecorderButton(self.config.master_shortcut)
        self.btn_master_rec.shortcut_recorded.connect(self._on_master_shortcut_recorded)
        m_bar.addWidget(self.btn_master_rec)
        btn_clear_m = QPushButton("Clear")
        btn_clear_m.setProperty("class", "SecondaryButton")
        btn_clear_m.clicked.connect(self._on_clear_master_shortcut)
        m_bar.addWidget(btn_clear_m)
        m_bar.addStretch()
        c_layout.addLayout(m_bar)

        # Shortcuts Table
        self.table_shortcuts = QTableWidget()
        self.table_shortcuts.setColumnCount(4)
        self.table_shortcuts.setHorizontalHeaderLabels([
            "Statistic", "Assigned Shortcut", "Bind Key Action", "Clear"
        ])
        self.table_shortcuts.verticalHeader().setVisible(False)
        self.table_shortcuts.verticalHeader().setDefaultSectionSize(44)
        self.table_shortcuts.setAlternatingRowColors(False)
        self.table_shortcuts.setShowGrid(True)

        self._populate_shortcuts_table()
        c_layout.addWidget(self.table_shortcuts)
        layout.addWidget(card)
        return widget

    def update_telemetry(self, snapshot: Dict[str, Any]):
        """Passes real-time telemetry snapshot to embedded visual editor if active."""
        if hasattr(self, "visual_editor") and self.visual_editor:
            self.visual_editor.update_telemetry(snapshot)

    def _populate_shortcuts_table(self):
        self.table_shortcuts.setRowCount(0)
        for row, (stat_id, item) in enumerate(self.config.stats.items()):
            self.table_shortcuts.insertRow(row)

            # 0: Name
            s_name = QTableWidgetItem(f"  {item.name}")
            s_name.setFlags(s_name.flags() ^ Qt.ItemIsEditable)
            s_name.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table_shortcuts.setItem(row, 0, s_name)

            # 1: Current shortcut display badge
            sc_text = item.shortcut if item.shortcut else "(Unassigned)"
            lbl_badge = QLabel(sc_text)
            lbl_badge.setAlignment(Qt.AlignCenter)
            color_style = f"color: {COLORS['primary']}; font-weight: bold;" if item.shortcut else f"color: {COLORS['text_muted']};"
            lbl_badge.setStyleSheet(f"background-color: {COLORS['bg_input']}; padding: 4px 8px; border-radius: 3px; border: 1px solid {COLORS['border']}; {color_style}")
            lbl_badge.setMinimumHeight(28)
            self.table_shortcuts.setCellWidget(row, 1, self._wrap_cell_widget(lbl_badge, Qt.AlignCenter))

            # 2: Key Recorder Button
            btn_rec = KeyRecorderButton(item.shortcut)
            btn_rec.setMinimumHeight(28)
            btn_rec.shortcut_recorded.connect(
                lambda sc, s=stat_id, l=lbl_badge: self._on_shortcut_recorded(s, sc, l)
            )
            self.table_shortcuts.setCellWidget(row, 2, self._wrap_cell_widget(btn_rec, Qt.AlignCenter))

            # 3: Clear Button
            btn_clear = QPushButton("Clear")
            btn_clear.setProperty("class", "SecondaryButton")
            btn_clear.setMinimumHeight(28)
            btn_clear.clicked.connect(
                lambda _, s=stat_id, b=btn_rec, l=lbl_badge: self._on_shortcut_cleared(s, b, l)
            )
            self.table_shortcuts.setCellWidget(row, 3, self._wrap_cell_widget(btn_clear, Qt.AlignCenter))

    def _on_master_shortcut_recorded(self, shortcut_str: str):
        shortcut_str = shortcut_str.strip()
        for s_id, item in self.config.stats.items():
            if item.shortcut.strip().upper() == shortcut_str.upper():
                self.show_toast(f"Conflict: Shortcut '{shortcut_str}' is already assigned to {item.name}.", "error")
                self.btn_master_rec.setText(self.config.master_shortcut or "(None)")
                return
        self.config.master_shortcut = shortcut_str
        self.config.save()
        self.shortcut_updated.emit("master", shortcut_str)

    def _on_clear_master_shortcut(self):
        self.config.master_shortcut = ""
        self.btn_master_rec.setText("(None)")
        self.config.save()
        self.shortcut_updated.emit("master", "")

    def _on_shortcut_recorded(self, stat_id: str, shortcut_str: str, lbl_badge: QLabel):
        shortcut_str = shortcut_str.strip()
        if shortcut_str:
            if self.config.master_shortcut.strip().upper() == shortcut_str.upper():
                self.show_toast(f"Conflict: Shortcut '{shortcut_str}' is already assigned to Master Overlay Toggle.", "error")
                self._populate_shortcuts_table()
                return
            for other_id, other_item in self.config.stats.items():
                if other_id != stat_id and other_item.shortcut.strip().upper() == shortcut_str.upper():
                    self.show_toast(f"Conflict: Shortcut '{shortcut_str}' is already assigned to {other_item.name}.", "error")
                    self._populate_shortcuts_table()
                    return

        if stat_id in self.config.stats:
            self.config.stats[stat_id].shortcut = shortcut_str
            lbl_badge.setText(shortcut_str if shortcut_str else "(Unassigned)")
            lbl_badge.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold; background-color: {COLORS['bg_input']}; padding: 4px 8px; border-radius: 3px; border: 1px solid {COLORS['border']};")
            self.config.save()
            self.shortcut_updated.emit(stat_id, shortcut_str)

    def _on_shortcut_cleared(self, stat_id: str, btn_rec: KeyRecorderButton, lbl_badge: QLabel):
        if stat_id in self.config.stats:
            self.config.stats[stat_id].shortcut = ""
            btn_rec.setText("(None)")
            lbl_badge.setText("(Unassigned)")
            lbl_badge.setStyleSheet(f"color: {COLORS['text_muted']}; background-color: {COLORS['bg_input']}; padding: 4px 8px; border-radius: 3px; border: 1px solid {COLORS['border']};")
            self.config.save()
            self.shortcut_updated.emit(stat_id, "")

    def _on_unassign_all_shortcuts(self):
        self.config.master_shortcut = ""
        self.btn_master_rec.setText("(None)")
        self.shortcut_updated.emit("master", "")
        for stat_id, item in self.config.stats.items():
            item.shortcut = ""
            self.shortcut_updated.emit(stat_id, "")
        self.config.save()
        self._populate_shortcuts_table()
        self.show_toast("All keyboard shortcuts have been unassigned.", "info")

    # --- SUBSECTION 6: PRESETS ---

    def _build_presets_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        card = QFrame()
        card.setProperty("class", "ContentCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        c_layout.setSpacing(12)

        p_title = QLabel("Multi-Window Overlay Layout Presets")
        p_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['primary']};")
        c_layout.addWidget(p_title)

        h_box = QHBoxLayout()
        self.list_presets = QListWidget()
        self._refresh_presets_list()
        h_box.addWidget(self.list_presets)

        actions_box = QVBoxLayout()
        actions_box.setSpacing(8)

        self.btn_apply_preset = QPushButton("Apply Selected Preset")
        self.btn_apply_preset.setProperty("class", "PrimaryButton")
        self.btn_apply_preset.clicked.connect(self._on_apply_preset)
        actions_box.addWidget(self.btn_apply_preset)

        self.btn_save_custom_preset = QPushButton("Save Current as Preset...")
        self.btn_save_custom_preset.setProperty("class", "SecondaryButton")
        self.btn_save_custom_preset.clicked.connect(self._on_save_custom_preset)
        actions_box.addWidget(self.btn_save_custom_preset)

        self.btn_delete_preset = QPushButton("Delete Custom Preset")
        self.btn_delete_preset.setProperty("class", "SecondaryButton")
        self.btn_delete_preset.clicked.connect(self._on_delete_custom_preset)
        actions_box.addWidget(self.btn_delete_preset)

        actions_box.addSpacing(16)

        btn_exp = QPushButton("Export to JSON...")
        btn_exp.setProperty("class", "SecondaryButton")
        btn_exp.clicked.connect(self._on_export_presets_json)
        actions_box.addWidget(btn_exp)

        btn_imp = QPushButton("Import from JSON...")
        btn_imp.setProperty("class", "SecondaryButton")
        btn_imp.clicked.connect(self._on_import_presets_json)
        actions_box.addWidget(btn_imp)

        actions_box.addStretch()
        h_box.addLayout(actions_box)

        c_layout.addLayout(h_box)
        layout.addWidget(card)
        return widget

    def _refresh_presets_list(self):
        self.list_presets.clear()
        for p in ["Minimal", "Performance", "Detailed"]:
            self.list_presets.addItem(f"{p} (Built-in)")
        for cp in self.config.custom_presets.keys():
            self.list_presets.addItem(f"{cp} (Custom)")

    def _on_apply_preset(self):
        sel = self.list_presets.currentItem()
        if not sel: return
        name = sel.text().split(" ")[0]
        self.config.apply_preset(name)
        self.config.save()
        self._populate_stats_table()
        self._populate_positioning_table()
        self.overlay_config_changed.emit(self.config)
        self.show_toast(f"Preset '{name}' applied successfully.", "success")

    def _on_save_custom_preset(self):
        name, ok = QInputDialog.getText(self, "Save Custom Preset", "Enter a unique preset name:")
        if ok and name.strip():
            clean = name.strip()
            self.config.save_custom_preset(clean)
            self._refresh_presets_list()
            self.show_toast(f"Preset '{clean}' saved.", "success")

    def _on_delete_custom_preset(self):
        sel = self.list_presets.currentItem()
        if not sel or "(Built-in)" in sel.text():
            return
        name = sel.text().split(" ")[0]
        if self.config.delete_custom_preset(name):
            self._refresh_presets_list()
            self.show_toast(f"Preset '{name}' removed.", "info")

    def _on_export_presets_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Overlay Configuration", "netvision_overlay_config.json", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.config.to_dict(), f, indent=2)
                self.show_toast(f"Configuration exported to {Path(path).name}.", "success")
            except Exception as e:
                self.show_toast(f"Export Error: {e}", "error")

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
                self._populate_positioning_table()
                self._populate_shortcuts_table()
                self.overlay_config_changed.emit(self.config)
                self.show_toast("Overlay configuration imported successfully.", "success")
            except Exception as e:
                self.show_toast(f"Import Error: {e}", "error")

    # --- SUBSECTION 7: NETWORK THRESHOLDS & LOCATIONS ---

    def _build_thresholds_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # General Monitoring Defaults
        gen_card = QFrame()
        gen_card.setProperty("class", "ContentCard")
        g_layout = QVBoxLayout(gen_card)
        g_layout.setContentsMargins(16, 12, 16, 12)

        g_title = QLabel("General & Monitoring Defaults")
        g_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['primary']};")
        g_layout.addWidget(g_title)

        g_grid = QGridLayout()
        g_grid.setSpacing(10)

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
        grid.setSpacing(10)

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

        self.btn_add_loc = QPushButton("Add Location")
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

        self.config.apply_preset("Performance")
        self.config.master_enabled = False
        self.config.save()
        self._populate_stats_table()
        self._populate_positioning_table()
        self._populate_shortcuts_table()
        self.overlay_config_changed.emit(self.config)

        self.request_restore_defaults.emit()
        self.show_toast("System thresholds and overlay settings restored to defaults.", "info")

    def _on_save_all_clicked(self):
        s_exc = self.spin_s_exc.value()
        s_good = self.spin_s_good.value()
        s_fair = self.spin_s_fair.value()
        if not (s_exc > s_good > s_fair):
            self.show_toast("Validation Error: Wi-Fi Signal must be Excellent > Good > Fair.", "error")
            return

        l_exc = self.spin_l_exc.value()
        l_good = self.spin_l_good.value()
        l_fair = self.spin_l_fair.value()
        if not (l_exc < l_good < l_fair):
            self.show_toast("Validation Error: Latency must be Excellent < Good < Fair.", "error")
            return

        p_good = self.spin_p_good.value()
        p_fair = self.spin_p_fair.value()
        if not (p_good < p_fair):
            self.show_toast("Validation Error: Packet Loss must be Good < Fair.", "error")
            return

        d_exc = self.spin_d_exc.value()
        d_good = self.spin_d_good.value()
        d_fair = self.spin_d_fair.value()
        if not (d_exc > d_good > d_fair):
            self.show_toast("Validation Error: Download Speed must be Excellent > Good > Fair.", "error")
            return

        self.btn_save_all.setEnabled(False)
        self.btn_save_all.setText("Saving...")

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

        self.config.save()
        self.overlay_config_changed.emit(self.config)
        self.request_save_settings.emit(payload)

        self.show_toast("Settings saved successfully!", "success")
        self.btn_save_all.setText("Save All Changes")
        self.btn_save_all.setEnabled(True)
