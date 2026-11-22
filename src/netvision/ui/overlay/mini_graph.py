"""
NetVision - High-Performance QPainter Sparkline Mini Graph Widget
Renders real-time telemetry graphs with anti-aliasing, gradient area fill,
and zero Matplotlib overhead. Optimized for sub-millisecond redraws.
"""

from typing import List, Optional
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QLinearGradient, QFont, QPaintEvent
)


class MiniGraphWidget(QWidget):
    """
    Ultra-lightweight real-time sparkline graph drawn using native QPainter.
    """

    def __init__(
        self,
        title: str = "",
        unit: str = "",
        color: str = "#38bdf8",
        scale_mode: str = "auto",
        min_val: float = 0.0,
        max_val: float = 100.0,
        history_len: int = 60,
        parent=None
    ):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.color_hex = color
        self.scale_mode = scale_mode
        self.fixed_min = min_val
        self.fixed_max = max_val
        self.history_len = history_len

        self._data: List[float] = []
        self._current_val: float = 0.0
        self._display_override: Optional[str] = None

        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setMinimumSize(120, 50)

    def set_data(self, history: List[float], current_val: Optional[float] = None, display_str: Optional[str] = None):
        """Updates graph data points and requests a repaint."""
        self._data = list(history)[-self.history_len:]
        if current_val is not None:
            self._current_val = current_val
        elif self._data:
            self._current_val = self._data[-1]
        self._display_override = display_str
        self.update()

    def set_color(self, color_hex: str):
        self.color_hex = color_hex
        self.update()

    def set_scale(self, scale_mode: str, min_val: float = 0.0, max_val: float = 100.0):
        self.scale_mode = scale_mode
        self.fixed_min = min_val
        self.fixed_max = max_val
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        w = self.width()
        h = self.height()

        # Background container
        bg_color = QColor(15, 23, 42, 210)  # Slate 900 with high opacity
        painter.fillRect(0, 0, w, h, bg_color)

        # Border
        border_pen = QPen(QColor(51, 65, 85, 180), 1)  # Slate 700
        painter.setPen(border_pen)
        painter.drawRoundedRect(0, 0, w - 1, h - 1, 6, 6)

        # Header: Title on left, Value on right
        font_title = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(font_title)
        painter.setPen(QColor(226, 232, 240))  # Slate 200
        painter.drawText(8, 16, self.title)

        font_val = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(font_val)
        accent = QColor(self.color_hex)
        painter.setPen(accent)

        if self._display_override:
            val_text = self._display_override
        elif self.unit == "%" or self.unit == "FPS":
            val_text = f"{self._current_val:.1f} {self.unit}"
        elif self.unit == "ms":
            val_text = f"{self._current_val:.1f} ms"
        elif self.unit in ("Mbps", "KB/s"):
            val_text = f"{self._current_val:.2f} {self.unit}"
        else:
            val_text = f"{self._current_val:.1f} {self.unit}".strip()

        painter.drawText(w - painter.fontMetrics().horizontalAdvance(val_text) - 8, 16, val_text)

        # Graph plot area dimensions
        pad_x = 8
        top_y = 22
        bot_y = h - 6
        plot_w = w - (pad_x * 2)
        plot_h = bot_y - top_y

        if plot_h <= 5 or plot_w <= 10:
            return

        # Grid lines (mid line)
        grid_pen = QPen(QColor(51, 65, 85, 90), 1, Qt.DashLine)
        painter.setPen(grid_pen)
        mid_y = top_y + (plot_h / 2.0)
        painter.drawLine(pad_x, int(mid_y), w - pad_x, int(mid_y))

        if not self._data or len(self._data) < 2:
            return

        # Determine min and max scale
        if self.scale_mode == "fixed":
            min_y = self.fixed_min
            max_y = self.fixed_max
        else:
            min_y = min(self._data)
            max_y = max(self._data)
            # Add small padding so flat lines don't clamp
            diff = max_y - min_y
            if diff < 1.0:
                min_y = max(0.0, min_y - 1.0)
                max_y = max_y + 1.0

        range_y = max(0.001, max_y - min_y)

        # Build coordinate points
        pts: List[QPointF] = []
        n_pts = len(self._data)
        step_x = plot_w / max(1, n_pts - 1)

        for i, val in enumerate(self._data):
            clamped = max(min_y, min(max_y, val))
            norm = (clamped - min_y) / range_y
            px = pad_x + (i * step_x)
            py = bot_y - (norm * plot_h)
            pts.append(QPointF(px, py))

        # 1. Draw gradient area underneath line
        grad = QLinearGradient(0, top_y, 0, bot_y)
        c_top = QColor(self.color_hex)
        c_top.setAlpha(70)
        c_bot = QColor(self.color_hex)
        c_bot.setAlpha(8)
        grad.setColorAt(0.0, c_top)
        grad.setColorAt(1.0, c_bot)

        poly_pts = [QPointF(pad_x, bot_y)] + pts + [QPointF(pts[-1].x(), bot_y)]
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawPolygon(poly_pts)

        # 2. Draw sparkline
        line_pen = QPen(accent, 1.8)
        line_pen.setCapStyle(Qt.RoundCap)
        line_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(line_pen)
        painter.setBrush(Qt.NoBrush)

        for i in range(len(pts) - 1):
            painter.drawLine(pts[i], pts[i + 1])

        # 3. Draw active point at head
        last_pt = pts[-1]
        painter.setPen(QPen(QColor(255, 255, 255), 1.5))
        painter.setBrush(accent)
        painter.drawEllipse(last_pt, 2.5, 2.5)
