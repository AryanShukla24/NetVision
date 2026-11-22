"""
NetVision - Individual Statistic Detail Configuration Dialog
Dedicated modal dialog for deep customization of a floating statistic widget:
display mode, font size, width/height, graph dimensions, screen position coordinates,
quick corner placement, transparency, subtle background, and text shadow.
"""

from typing import Optional, Tuple
import copy
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSpinBox, QComboBox, QCheckBox,
    QColorDialog, QSlider, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from netvision.config import COLORS
from netvision.core.overlay_config import StatItemConfig, DisplayMode, get_default_stats_catalog


class StatDetailDialog(QDialog):
    """
    Dedicated modal dialog for fine-grained configuration of an individual statistic widget.
    """

    def __init__(self, item: StatItemConfig, parent=None):
        super().__init__(parent)
        self.item = item
        self.working_item = copy.deepcopy(item)
        self.setWindowTitle(f"Configure Statistic — {item.name}")
        self.setMinimumWidth(520)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_dark']};
                color: #f8fafc;
            }}
            QGroupBox {{
                font-weight: 700;
                font-size: 12px;
                color: #38bdf8;
                border: 1px solid rgba(51, 65, 85, 0.7);
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 14px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }}
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # Header with Category Pill and Name
        header = QHBoxLayout()
        cat_badge = QLabel(self.working_item.category.upper())
        cat_badge.setStyleSheet("""
            background-color: rgba(2, 132, 199, 0.25);
            color: #38bdf8;
            font-size: 11px;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 4px;
            border: 1px solid rgba(56, 189, 248, 0.4);
        """)
        header.addWidget(cat_badge)

        name_lbl = QLabel(self.working_item.name)
        name_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #ffffff;")
        header.addWidget(name_lbl)
        header.addStretch()

        self.chk_enabled = QCheckBox("Statistic Active")
        self.chk_enabled.setChecked(self.working_item.enabled and self.working_item.mode != DisplayMode.DONT_SHOW)
        self.chk_enabled.setStyleSheet("font-weight: 600; color: #34d399;")
        self.chk_enabled.toggled.connect(self._on_enabled_toggled)
        header.addWidget(self.chk_enabled)

        layout.addLayout(header)

        # 1. Display Mode & Typography Group
        grp_display = QGroupBox("Display Mode & Typography")
        d_layout = QGridLayout(grp_display)
        d_layout.setSpacing(12)

        d_layout.addWidget(QLabel("Display Mode:"), 0, 0)
        self.combo_mode = QComboBox()
        self.combo_mode.addItem("Don't Show (Disabled)", DisplayMode.DONT_SHOW)
        self.combo_mode.addItem("Numbers Only", DisplayMode.NUMBERS)
        self.combo_mode.addItem("Real-Time Graph", DisplayMode.GRAPH)
        idx = self.combo_mode.findData(self.working_item.mode)
        if idx >= 0:
            self.combo_mode.setCurrentIndex(idx)
        self.combo_mode.currentIndexChanged.connect(self._on_mode_changed)
        d_layout.addWidget(self.combo_mode, 0, 1)

        d_layout.addWidget(QLabel("Font Size (pt):"), 0, 2)
        self.spin_font = QSpinBox()
        self.spin_font.setRange(9, 36)
        self.spin_font.setValue(self.working_item.font_size)
        d_layout.addWidget(self.spin_font, 0, 3)

        d_layout.addWidget(QLabel("Accent Color:"), 1, 0)
        color_box = QHBoxLayout()
        self.lbl_color_swatch = QLabel(f" {self.working_item.color} ")
        self.lbl_color_swatch.setAlignment(Qt.AlignCenter)
        self.lbl_color_swatch.setStyleSheet(f"background-color: {self.working_item.color}; color: #000; font-weight: bold; border-radius: 4px; padding: 3px 8px;")
        color_box.addWidget(self.lbl_color_swatch)

        self.btn_pick_color = QPushButton("Choose Color...")
        self.btn_pick_color.setProperty("class", "SecondaryButton")
        self.btn_pick_color.clicked.connect(self._on_pick_color)
        color_box.addWidget(self.btn_pick_color)
        d_layout.addLayout(color_box, 1, 1, 1, 3)

        layout.addWidget(grp_display)

        # 2. Dimensions & Desktop Coordinates Group
        grp_geom = QGroupBox("Dimensions & Screen Position")
        g_layout = QGridLayout(grp_geom)
        g_layout.setSpacing(12)

        # Numbers dimensions
        g_layout.addWidget(QLabel("Widget Width (Numbers):"), 0, 0)
        self.spin_w = QSpinBox()
        self.spin_w.setRange(80, 800)
        self.spin_w.setValue(self.working_item.width)
        g_layout.addWidget(self.spin_w, 0, 1)

        g_layout.addWidget(QLabel("Widget Height (Numbers):"), 0, 2)
        self.spin_h = QSpinBox()
        self.spin_h.setRange(24, 400)
        self.spin_h.setValue(self.working_item.height)
        g_layout.addWidget(self.spin_h, 0, 3)

        # Graph dimensions
        g_layout.addWidget(QLabel("Graph Width:"), 1, 0)
        self.spin_gw = QSpinBox()
        self.spin_gw.setRange(120, 1200)
        self.spin_gw.setValue(self.working_item.graph_width)
        g_layout.addWidget(self.spin_gw, 1, 1)

        g_layout.addWidget(QLabel("Graph Height:"), 1, 2)
        self.spin_gh = QSpinBox()
        self.spin_gh.setRange(40, 600)
        self.spin_gh.setValue(self.working_item.graph_height)
        g_layout.addWidget(self.spin_gh, 1, 3)

        # Coordinates
        g_layout.addWidget(QLabel("Desktop X Coordinate:"), 2, 0)
        self.spin_x = QSpinBox()
        self.spin_x.setRange(0, 7680)
        self.spin_x.setValue(self.working_item.x)
        g_layout.addWidget(self.spin_x, 2, 1)

        g_layout.addWidget(QLabel("Desktop Y Coordinate:"), 2, 2)
        self.spin_y = QSpinBox()
        self.spin_y.setRange(0, 4320)
        self.spin_y.setValue(self.working_item.y)
        g_layout.addWidget(self.spin_y, 2, 3)

        # Quick corner placement buttons
        g_layout.addWidget(QLabel("Quick Corner Snap:"), 3, 0)
        c_bar = QHBoxLayout()
        for label, (cx, cy) in [
            ("Top-Left", (24, 24)),
            ("Top-Right", (1180, 24)),
            ("Bottom-Left", (24, 700)),
            ("Bottom-Right", (1180, 700))
        ]:
            btn = QPushButton(label)
            btn.setProperty("class", "SecondaryButton")
            btn.clicked.connect(lambda _, x=cx, y=cy: self._snap_coords(x, y))
            c_bar.addWidget(btn)
        g_layout.addLayout(c_bar, 3, 1, 1, 3)

        layout.addWidget(grp_geom)

        # 3. Styling, Opacity & Transparency Group
        grp_style = QGroupBox("Appearance & Transparency")
        s_layout = QGridLayout(grp_style)
        s_layout.setSpacing(12)

        self.chk_subtle_bg = QCheckBox("Show Subtle Tinted Background")
        self.chk_subtle_bg.setChecked(self.working_item.show_subtle_bg)
        s_layout.addWidget(self.chk_subtle_bg, 0, 0, 1, 2)

        self.chk_shadow = QCheckBox("High-Contrast Text Drop Shadow")
        self.chk_shadow.setChecked(self.working_item.show_shadow)
        s_layout.addWidget(self.chk_shadow, 0, 2, 1, 2)

        s_layout.addWidget(QLabel("Widget Opacity:"), 1, 0)
        op_box = QHBoxLayout()
        self.slider_op = QSlider(Qt.Horizontal)
        self.slider_op.setRange(20, 100)
        self.slider_op.setValue(int(self.working_item.opacity * 100))
        self.lbl_op_val = QLabel(f"{int(self.working_item.opacity * 100)}%")
        self.slider_op.valueChanged.connect(lambda v: self.lbl_op_val.setText(f"{v}%"))
        op_box.addWidget(self.slider_op)
        op_box.addWidget(self.lbl_op_val)
        s_layout.addLayout(op_box, 1, 1, 1, 3)

        self.chk_lock = QCheckBox("Lock Position on Desktop (Prevent accidental drag)")
        self.chk_lock.setChecked(self.working_item.is_locked)
        s_layout.addWidget(self.chk_lock, 2, 0, 1, 4)

        layout.addWidget(grp_style)

        # Bottom Action Bar
        btn_bar = QHBoxLayout()
        self.btn_reset = QPushButton("↺ Reset to Default")
        self.btn_reset.setProperty("class", "SecondaryButton")
        self.btn_reset.clicked.connect(self._on_reset_to_default)
        btn_bar.addWidget(self.btn_reset)

        btn_bar.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setProperty("class", "SecondaryButton")
        self.btn_cancel.clicked.connect(self.reject)
        btn_bar.addWidget(self.btn_cancel)

        self.btn_apply = QPushButton("✔ Save & Apply")
        self.btn_apply.setProperty("class", "PrimaryButton")
        self.btn_apply.setDefault(True)
        self.btn_apply.clicked.connect(self._on_apply_clicked)
        btn_bar.addWidget(self.btn_apply)

        layout.addLayout(btn_bar)

    def _on_enabled_toggled(self, checked: bool):
        if not checked:
            idx = self.combo_mode.findData(DisplayMode.DONT_SHOW)
            if idx >= 0:
                self.combo_mode.setCurrentIndex(idx)
        else:
            if self.combo_mode.currentData() == DisplayMode.DONT_SHOW:
                idx = self.combo_mode.findData(DisplayMode.NUMBERS)
                if idx >= 0:
                    self.combo_mode.setCurrentIndex(idx)

    def _on_mode_changed(self):
        mode = self.combo_mode.currentData()
        self.chk_enabled.blockSignals(True)
        self.chk_enabled.setChecked(mode != DisplayMode.DONT_SHOW)
        self.chk_enabled.blockSignals(False)

    def _on_pick_color(self):
        c = QColorDialog.getColor(QColor(self.working_item.color), self, f"Select Accent Color for {self.working_item.name}")
        if c.isValid():
            self.working_item.color = c.name()
            self.lbl_color_swatch.setText(f" {self.working_item.color} ")
            self.lbl_color_swatch.setStyleSheet(
                f"background-color: {self.working_item.color}; color: #000; font-weight: bold; border-radius: 4px; padding: 3px 8px;"
            )

    def _snap_coords(self, x: int, y: int):
        self.spin_x.setValue(x)
        self.spin_y.setValue(y)

    def _on_reset_to_default(self):
        catalog = get_default_stats_catalog()
        if self.working_item.stat_id in catalog:
            def_item = catalog[self.working_item.stat_id]
            self.spin_w.setValue(def_item.width)
            self.spin_h.setValue(def_item.height)
            self.spin_gw.setValue(def_item.graph_width)
            self.spin_gh.setValue(def_item.graph_height)
            self.spin_x.setValue(def_item.x)
            self.spin_y.setValue(def_item.y)
            self.spin_font.setValue(def_item.font_size)
            idx = self.combo_mode.findData(def_item.mode)
            if idx >= 0:
                self.combo_mode.setCurrentIndex(idx)
            self.chk_enabled.setChecked(def_item.enabled and def_item.mode != DisplayMode.DONT_SHOW)
            self.chk_subtle_bg.setChecked(def_item.show_subtle_bg)
            self.slider_op.setValue(int(def_item.opacity * 100))
            self.chk_lock.setChecked(def_item.is_locked)
            self.working_item.color = def_item.color
            self.lbl_color_swatch.setText(f" {def_item.color} ")
            self.lbl_color_swatch.setStyleSheet(
                f"background-color: {def_item.color}; color: #000; font-weight: bold; border-radius: 4px; padding: 3px 8px;"
            )

    def _on_apply_clicked(self):
        # Commit UI values to original item
        mode = self.combo_mode.currentData()
        self.item.mode = mode
        self.item.enabled = self.chk_enabled.isChecked() and (mode != DisplayMode.DONT_SHOW)
        self.item.font_size = self.spin_font.value()
        self.item.color = self.working_item.color
        self.item.width = self.spin_w.value()
        self.item.height = self.spin_h.value()
        self.item.graph_width = self.spin_gw.value()
        self.item.graph_height = self.spin_gh.value()
        self.item.x = self.spin_x.value()
        self.item.y = self.spin_y.value()
        self.item.show_subtle_bg = self.chk_subtle_bg.isChecked()
        self.item.show_shadow = self.chk_shadow.isChecked()
        self.item.opacity = self.slider_op.value() / 100.0
        self.item.is_locked = self.chk_lock.isChecked()
        self.accept()
