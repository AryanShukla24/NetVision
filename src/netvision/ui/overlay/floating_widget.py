"""
NetVision - Independent Floating Statistic Window
Lightweight, genuinely transparent, frameless, always-on-top desktop widget.
Each statistic window is independently positioned, resized, moved, and customized.
"""

from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect,
    QSizeGrip
)
from PySide6.QtCore import Qt, QPoint, QRect, Signal
from PySide6.QtGui import (
    QColor, QFont, QMouseEvent, QPainter, QPen, QBrush, QCursor, QPaintEvent
)

from netvision.core.overlay_config import StatItemConfig, DisplayMode
from netvision.ui.overlay.mini_graph import MiniGraphWidget


class FloatingStatWidget(QWidget):
    """
    Independent floating desktop widget displaying a single statistic.
    Features genuinely transparent background, free desktop dragging,
    independent resizing, and crisp text shadow rendering.
    """

    position_changed = Signal(str, int, int)
    size_changed = Signal(str, int, int)

    def __init__(self, item: StatItemConfig, master_locked: bool = False, parent=None):
        super().__init__(
            parent,
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.item = item
        self.stat_id = item.stat_id
        self.master_locked = master_locked

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setMouseTracking(True)

        self._is_dragging = False
        self._is_resizing = False
        self._drag_start_pos = QPoint()
        self._orig_geom = QRect()
        self._hovered = False

        self._build_ui()
        self.apply_config(self.item)

    def _build_ui(self):
        self.setObjectName(f"FloatingWidget_{self.stat_id}")
        self.layout_box = QVBoxLayout(self)
        self.layout_box.setContentsMargins(6, 4, 6, 4)
        self.layout_box.setSpacing(2)

        # 1. Title Label
        self.lbl_title = QLabel(self.item.name)
        font_title = QFont("Segoe UI", max(8, self.item.font_size - 3), QFont.Bold)
        self.lbl_title.setFont(font_title)
        self.lbl_title.setStyleSheet("color: #94a3b8;")
        self.layout_box.addWidget(self.lbl_title)

        # 2. Value Label
        self.lbl_val = QLabel("--")
        font_val = QFont("Segoe UI", self.item.font_size, QFont.Bold)
        self.lbl_val.setFont(font_val)
        self.lbl_val.setStyleSheet(f"color: {self.item.color};")
        self.layout_box.addWidget(self.lbl_val)

        # Add text drop shadow for 100% legibility on white, dark, or game backgrounds
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(5)
        shadow.setColor(QColor(0, 0, 0, 220))
        shadow.setOffset(1, 1)
        self.lbl_val.setGraphicsEffect(shadow)

        # 3. Graph Widget (Created lazily if in Graph mode)
        self.graph_widget: Optional[MiniGraphWidget] = None

    def apply_config(self, item: StatItemConfig):
        """Updates geometry, colors, fonts, and display mode."""
        self.item = item
        self.setWindowOpacity(self.item.opacity)

        w = self.item.graph_width if self.item.mode == DisplayMode.GRAPH else self.item.width
        h = self.item.graph_height if self.item.mode == DisplayMode.GRAPH else self.item.height
        self.setGeometry(self.item.x, self.item.y, max(100, w), max(36, h))

        # Typography & Colors
        self.lbl_title.setFont(QFont("Segoe UI", max(8, self.item.font_size - 3), QFont.Bold))
        self.lbl_val.setFont(QFont("Segoe UI", self.item.font_size, QFont.Bold))
        self.lbl_val.setStyleSheet(f"color: {self.item.color};")

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
                    parent=self
                )
                self.layout_box.addWidget(self.graph_widget)
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

    # --- Mouse Drag-and-Drop & Resizing ---

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def _is_on_resize_handle(self, pos: QPoint) -> bool:
        """Checks if cursor is over the bottom-right resize corner."""
        w, h = self.width(), self.height()
        return (w - 14 <= pos.x() <= w) and (h - 14 <= pos.y() <= h)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and not (self.master_locked or self.item.is_locked):
            self._orig_geom = self.geometry()
            self._drag_start_pos = event.globalPosition().toPoint()
            if self._is_on_resize_handle(event.pos()):
                self._is_resizing = True
            else:
                self._is_dragging = True
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (self.master_locked or self.item.is_locked):
            if self._is_on_resize_handle(event.pos()) or self._is_resizing:
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.SizeAllCursor if self._hovered else Qt.ArrowCursor)

        if self._is_dragging:
            cur = event.globalPosition().toPoint()
            delta = cur - self._drag_start_pos
            nx = self._orig_geom.x() + delta.x()
            ny = self._orig_geom.y() + delta.y()
            self.move(nx, ny)
            self.item.x = nx
            self.item.y = ny
            event.accept()

        elif self._is_resizing:
            cur = event.globalPosition().toPoint()
            delta = cur - self._drag_start_pos
            nw = max(90, self._orig_geom.width() + delta.x())
            nh = max(34, self._orig_geom.height() + delta.y())
            self.resize(nw, nh)
            if self.item.mode == DisplayMode.GRAPH:
                self.item.graph_width = nw
                self.item.graph_height = nh
            else:
                self.item.width = nw
                self.item.height = nh
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if self._is_dragging:
                self._is_dragging = False
                self.position_changed.emit(self.stat_id, self.x(), self.y())
            elif self._is_resizing:
                self._is_resizing = False
                self.size_changed.emit(self.stat_id, self.width(), self.height())
            event.accept()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.width(), self.height()

        # 1. Background (Truly transparent by default, or subtle background if enabled)
        if self.item.show_subtle_bg:
            bg_alpha = int(self.item.bg_opacity * 255)
            if bg_alpha > 0:
                painter.fillRect(0, 0, w, h, QColor(15, 23, 42, bg_alpha))
                painter.setPen(QPen(QColor(51, 65, 85, max(40, bg_alpha)), 1))
                painter.drawRoundedRect(0, 0, w - 1, h - 1, self.item.border_radius, self.item.border_radius)

        # 2. Subtle hover guide (Shows gentle outline when hovered so user knows they can drag it)
        if self._hovered and not (self.master_locked or self.item.is_locked):
            painter.setPen(QPen(QColor(56, 189, 248, 120), 1, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(1, 1, w - 2, h - 2, 4, 4)

            # Resize grip lines in bottom-right corner
            painter.setPen(QPen(QColor(56, 189, 248, 180), 1.5))
            painter.drawLine(w - 10, h - 3, w - 3, h - 10)
            painter.drawLine(w - 6, h - 3, w - 3, h - 6)
