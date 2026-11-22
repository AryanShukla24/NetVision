"""
NetVision - Independent Floating Statistic Window
Lightweight, genuinely transparent, frameless, always-on-top desktop widget.
Desktop widgets are strictly locked during normal use to prevent accidental movement.
All editing and repositioning is done through the Visual Overlay Editor in Settings.
"""

from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPoint, QRect, Signal
from PySide6.QtGui import (
    QColor, QFont, QMouseEvent, QPainter, QPen, QPaintEvent
)

from netvision.config import COLORS
from netvision.core.overlay_config import StatItemConfig, DisplayMode
from netvision.ui.overlay.mini_graph import MiniGraphWidget


class FloatingStatWidget(QWidget):
    """
    Independent floating desktop widget displaying a single statistic.
    Features genuine transparency, crisp monospace text, text shadows, and desktop lock.
    """

    position_changed = Signal(str, int, int)
    size_changed = Signal(str, int, int)

    def __init__(self, item: StatItemConfig, master_locked: bool = True, parent=None):
        super().__init__(
            parent,
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.item = item
        self.stat_id = item.stat_id
        # STRICT REQUIREMENT: Locked during normal desktop use to prevent accidental drags
        self.master_locked = master_locked

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setStyleSheet("background: transparent; border: none;")

        self._build_ui()
        self.apply_config(self.item)

    def _build_ui(self):
        self.setObjectName(f"FloatingWidget_{self.stat_id}")
        self.layout_box = QVBoxLayout(self)
        self.layout_box.setContentsMargins(6, 4, 6, 4)
        self.layout_box.setSpacing(2)

        # 1. Title Label
        self.lbl_title = QLabel(self.item.name, self)
        font_title = QFont("Segoe UI", max(8, self.item.font_size - 3), QFont.Bold)
        self.lbl_title.setFont(font_title)
        self.lbl_title.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; border: none;")
        self.layout_box.addWidget(self.lbl_title)

        # Title text drop shadow for legibility over light wallpapers/games
        shadow_title = QGraphicsDropShadowEffect(self)
        shadow_title.setBlurRadius(4)
        shadow_title.setColor(QColor(0, 0, 0, 240))
        shadow_title.setOffset(1, 1)
        self.lbl_title.setGraphicsEffect(shadow_title)

        # 2. Value Label with Monospace Font
        self.lbl_val = QLabel("--", self)
        font_val = QFont("Consolas", self.item.font_size, QFont.Bold)
        self.lbl_val.setFont(font_val)
        self.lbl_val.setStyleSheet(f"color: {self.item.color}; background: transparent; border: none;")
        self.layout_box.addWidget(self.lbl_val)

        # Value text drop shadow for 100% legibility on white, dark, or game backgrounds
        shadow_val = QGraphicsDropShadowEffect(self)
        shadow_val.setBlurRadius(5)
        shadow_val.setColor(QColor(0, 0, 0, 240))
        shadow_val.setOffset(1, 1)
        self.lbl_val.setGraphicsEffect(shadow_val)

        # 3. Graph Widget (Created lazily if in Graph mode)
        self.graph_widget: Optional[MiniGraphWidget] = None

    def apply_config(self, item: StatItemConfig):
        """Updates geometry, colors, fonts, and display mode."""
        self.item = item
        self.setWindowOpacity(self.item.opacity)

        w = self.item.graph_width if self.item.mode == DisplayMode.GRAPH else self.item.width
        h = self.item.graph_height if self.item.mode == DisplayMode.GRAPH else self.item.height
        self.setGeometry(self.item.x, self.item.y, max(90, w), max(32, h))

        # Typography & Colors
        self.lbl_title.setFont(QFont("Segoe UI", max(8, self.item.font_size - 3), QFont.Bold))
        self.lbl_val.setFont(QFont("Consolas", self.item.font_size, QFont.Bold))
        self.lbl_val.setStyleSheet(f"color: {self.item.color}; background: transparent; border: none;")

        # Mode switching
        if self.item.mode == DisplayMode.GRAPH:
            self.lbl_title.hide()
            self.lbl_val.hide()
            if not self.graph_widget:
                self.graph_widget = MiniGraphWidget(
                    title=self.item.name,
                    unit=self.item.unit,
                    color=self.item.color,
                    scale_mode=self.item.graph_scale_mode,
                    min_val=self.item.graph_min,
                    max_val=self.item.graph_max,
                    history_len=self.item.history_len,
                    transparent_bg=not self.item.show_subtle_bg,
                    parent=self
                )
                self.layout_box.addWidget(self.graph_widget)
            self.graph_widget.set_transparent_bg(not self.item.show_subtle_bg)
            self.graph_widget.set_color(self.item.color)
            self.graph_widget.set_scale(self.item.graph_scale_mode, self.item.graph_min, self.item.graph_max)
            self.graph_widget.show()
        else:
            if self.graph_widget:
                self.graph_widget.hide()
            self.lbl_title.show()
            self.lbl_val.show()

        self.update()

    def set_master_locked(self, locked: bool):
        self.master_locked = locked

    def update_value(self, display_str: str, history: List[float], val: float):
        """Updates widget telemetry data in real time."""
        self.lbl_val.setText(display_str)
        if self.graph_widget and self.item.mode == DisplayMode.GRAPH:
            self.graph_widget.set_data(history, current_val=val, display_str=display_str)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.width(), self.height()

        # Background: Genuinely transparent by default!
        # Only draw background if the user explicitly enabled subtle background tint
        if self.item.show_subtle_bg and self.item.bg_opacity > 0:
            bg_alpha = int(self.item.bg_opacity * 255)
            painter.fillRect(0, 0, w, h, QColor(16, 21, 28, bg_alpha))
            painter.setPen(QPen(QColor(30, 42, 56, max(30, bg_alpha)), 1))
            painter.drawRoundedRect(0, 0, w - 1, h - 1, self.item.border_radius, self.item.border_radius)
