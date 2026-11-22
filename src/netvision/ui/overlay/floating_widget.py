"""
NetVision - Independent Floating Statistic Window
Lightweight, genuinely transparent, frameless, always-on-top desktop widget.
In Normal Mode:
  - 100% click-through via native Windows extended window styles (WS_EX_TRANSPARENT).
  - Clicks, right-clicks, and mouse motion pass straight through to the underlying game.
  - Zero mouse focus stealing, zero keyboard interference.
In Editing Mode:
  - Mouse interaction is enabled.
  - Widgets can be dragged across the desktop, resized via corner handles, and positioned.
Exiting Editing Mode immediately restores full click-through protection.
"""

import sys
import logging
import ctypes
from ctypes import wintypes
from typing import Optional, List

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPoint, QRect, Signal
from PySide6.QtGui import (
    QColor, QFont, QMouseEvent, QPainter, QPen, QPaintEvent, QShowEvent, QCursor
)

from netvision.config import COLORS
from netvision.core.overlay_config import StatItemConfig, DisplayMode
from netvision.ui.overlay.mini_graph import MiniGraphWidget

logger = logging.getLogger(__name__)

# Win32 Extended Window Styles Constants
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_FRAMECHANGED = 0x0020


class FloatingStatWidget(QWidget):
    """
    Independent floating desktop widget displaying a single statistic.
    Features genuine transparency, crisp monospace text, text shadows, and
    robust native Windows click-through behavior.
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
        self.master_locked = master_locked
        self.editing_mode = False

        # Dragging and resizing state (for editing mode)
        self._is_dragging = False
        self._is_resizing = False
        self._drag_start_pos = QPoint()
        self._resize_start_pos = QPoint()
        self._orig_size = self.size()

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setStyleSheet("background: transparent; border: none;")

        self._build_ui()
        self.apply_config(self.item)

        # Apply initial click-through
        self.set_click_through(self.master_locked)

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

    def set_click_through(self, enabled: bool):
        """
        Toggles native Windows click-through behavior via WS_EX_TRANSPARENT.
        When enabled (Normal Mode):
          All mouse clicks and movements pass completely through to the game underneath.
        When disabled (Editing Mode):
          Mouse clicks are captured for dragging, resizing, and selection.
        """
        self.setAttribute(Qt.WA_TransparentForMouseEvents, enabled)

        if sys.platform == "win32":
            try:
                hwnd = int(self.winId())
                user32 = ctypes.windll.user32
                if hwnd and user32.IsWindow(hwnd):
                    user32 = ctypes.windll.user32
                    if ctypes.sizeof(ctypes.c_void_p) == 8:
                        user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
                        user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
                        user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
                        user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
                        GetWindowLong = user32.GetWindowLongPtrW
                        SetWindowLong = user32.SetWindowLongPtrW
                    else:
                        user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
                        user32.GetWindowLongW.restype = ctypes.c_long
                        user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
                        user32.SetWindowLongW.restype = ctypes.c_long
                        GetWindowLong = user32.GetWindowLongW
                        SetWindowLong = user32.SetWindowLongW

                    ex = GetWindowLong(hwnd, GWL_EXSTYLE)
                    if enabled:
                        new_ex = (ex | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_LAYERED | WS_EX_TOOLWINDOW)
                    else:
                        new_ex = (ex & ~WS_EX_TRANSPARENT) | WS_EX_NOACTIVATE | WS_EX_LAYERED | WS_EX_TOOLWINDOW

                    SetWindowLong(hwnd, GWL_EXSTYLE, new_ex)
                    user32.SetWindowPos(
                        hwnd, 0, 0, 0, 0, 0,
                        SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_FRAMECHANGED
                    )
            except Exception as e:
                logger.debug(f"Failed to update click-through window styles: {e}")

    def set_editing_mode(self, editing: bool):
        """Enables or disables interactive on-desktop positioning and resizing."""
        self.editing_mode = editing
        self.set_click_through(not editing)
        if editing:
            self.setCursor(QCursor(Qt.SizeAllCursor))
        else:
            self.unsetCursor()
        self.update()

    def set_master_locked(self, locked: bool):
        self.master_locked = locked
        if not self.editing_mode:
            self.set_click_through(locked)

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        # Re-assert click-through styles after native window creation
        if not self.editing_mode:
            self.set_click_through(True)

    def mousePressEvent(self, event: QMouseEvent):
        if not self.editing_mode:
            event.ignore()
            return

        if event.button() == Qt.LeftButton:
            rect = self.rect()
            # Bottom-right corner resize handle (14x14 area)
            handle_rect = QRect(rect.width() - 14, rect.height() - 14, 14, 14)
            if handle_rect.contains(event.pos()):
                self._is_resizing = True
                self._resize_start_pos = event.globalPosition().toPoint()
                self._orig_size = self.size()
            else:
                self._is_dragging = True
                self._drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.editing_mode:
            event.ignore()
            return

        if self._is_resizing:
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            new_w = max(90, self._orig_size.width() + delta.x())
            new_h = max(32, self._orig_size.height() + delta.y())
            self.resize(new_w, new_h)
            self.item.width = new_w
            self.item.height = new_h
            if self.item.mode == DisplayMode.GRAPH:
                self.item.graph_width = new_w
                self.item.graph_height = new_h
            self.size_changed.emit(self.stat_id, new_w, new_h)
            event.accept()
        elif self._is_dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_start_pos
            self.move(new_pos)
            self.item.x = new_pos.x()
            self.item.y = new_pos.y()
            self.position_changed.emit(self.stat_id, new_pos.x(), new_pos.y())
            event.accept()
        else:
            # Change cursor if hovering over resize corner
            rect = self.rect()
            handle_rect = QRect(rect.width() - 14, rect.height() - 14, 14, 14)
            if handle_rect.contains(event.pos()):
                self.setCursor(QCursor(Qt.SizeFDiagCursor))
            else:
                self.setCursor(QCursor(Qt.SizeAllCursor))

    def mouseReleaseEvent(self, event: QMouseEvent):
        if not self.editing_mode:
            event.ignore()
            return

        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            self._is_resizing = False
            event.accept()

    def update_value(self, display_str: str, history: List[float], val: Optional[float] = None):
        """Updates widget telemetry data in real time."""
        self.lbl_val.setText(display_str)
        if self.graph_widget and self.item.mode == DisplayMode.GRAPH:
            current_float = val if val is not None else 0.0
            self.graph_widget.set_data(history, current_val=current_float, display_str=display_str)

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

        # Editing Mode Visual Guides
        if self.editing_mode:
            pen = QPen(QColor(34, 184, 207), 1, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(0, 0, w - 1, h - 1)
            # Resize Grip in bottom-right corner
            painter.fillRect(w - 10, h - 10, 8, 8, QColor(34, 184, 207, 200))
