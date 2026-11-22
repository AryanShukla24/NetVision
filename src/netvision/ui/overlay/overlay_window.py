"""
NetVision - Real-Time Floating Statistics Overlay Window
Frameless, translucent, always-on-top window displaying freely positioned
numerical badges and sparkline graphs with real-time updates.
"""

from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QLabel, QFrame, QHBoxLayout, QVBoxLayout, QPushButton,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPoint, Signal, QRect
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPaintEvent, QPainter, QPen

from netvision.core.overlay_config import OverlayConfig, DisplayMode, StatItemConfig
from netvision.ui.overlay.mini_graph import MiniGraphWidget


class NumberBadgeCard(QFrame):
    """Card widget for displaying statistics in numerical mode."""

    def __init__(self, item: StatItemConfig, parent=None):
        super().__init__(parent)
        self.item = item
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("NumberBadgeCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(self.item.padding, self.item.padding // 2, self.item.padding, self.item.padding // 2)
        layout.setSpacing(2)

        # Title Label
        self.lbl_title = QLabel(self.item.name)
        font_title = QFont("Segoe UI", max(8, self.item.font_size - 3))
        self.lbl_title.setFont(font_title)
        self.lbl_title.setStyleSheet("color: #94a3b8; font-weight: 600;")
        layout.addWidget(self.lbl_title)

        # Value Label
        self.lbl_val = QLabel("--")
        font_val = QFont("Segoe UI", self.item.font_size, QFont.Bold)
        self.lbl_val.setFont(font_val)
        self.lbl_val.setStyleSheet(f"color: {self.item.color};")
        layout.addWidget(self.lbl_val)

        self.update_style()

    def update_style(self):
        self.setStyleSheet(f"""
            QFrame#NumberBadgeCard {{
                background-color: rgba(15, 23, 42, 215);
                border: 1px solid rgba(51, 65, 85, 180);
                border-radius: 6px;
            }}
        """)
        self.lbl_val.setStyleSheet(f"color: {self.item.color}; font-weight: bold;")
        self.lbl_title.setFont(QFont("Segoe UI", max(8, self.item.font_size - 3)))
        self.lbl_val.setFont(QFont("Segoe UI", self.item.font_size, QFont.Bold))

    def set_value(self, display_str: str):
        self.lbl_val.setText(display_str)


class StatisticsOverlayWindow(QWidget):
    """
    Independent floating desktop overlay window displaying customized statistics.
    """

    request_open_settings = Signal()
    window_moved = Signal(int, int)

    def __init__(self, config: OverlayConfig, parent=None):
        super().__init__(
            parent,
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.config = config

        self._drag_pos = QPoint()
        self._is_dragging = False

        self._number_cards: Dict[str, NumberBadgeCard] = {}
        self._graph_cards: Dict[str, MiniGraphWidget] = {}

        self._build_ui()
        self.apply_config(self.config)

    def _build_ui(self):
        self.setObjectName("StatisticsOverlayWindow")
        self.setGeometry(
            self.config.window_x,
            self.config.window_y,
            self.config.window_width,
            self.config.window_height
        )

        # Container Widget with border & background
        self.container = QWidget(self)
        self.container.setObjectName("OverlayContainer")

        # Top Control / Title Bar
        self.top_bar = QWidget(self.container)
        self.top_bar.setGeometry(0, 0, self.width(), 24)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(8, 2, 8, 2)
        top_layout.setSpacing(6)

        self.lbl_bar_title = QLabel("NetVision Overlay")
        self.lbl_bar_title.setStyleSheet("color: #64748b; font-size: 10px; font-weight: bold;")
        top_layout.addWidget(self.lbl_bar_title)

        top_layout.addStretch()

        # Lock toggle button
        self.btn_lock = QPushButton("🔓" if not self.config.locked else "🔒")
        self.btn_lock.setFixedSize(18, 18)
        self.btn_lock.setToolTip("Lock / Unlock Window Position")
        self.btn_lock.setStyleSheet("background: transparent; border: none; font-size: 11px; color: #94a3b8;")
        self.btn_lock.clicked.connect(self._toggle_lock)
        top_layout.addWidget(self.btn_lock)

        # Settings button
        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setFixedSize(18, 18)
        self.btn_settings.setToolTip("Open Overlay Settings")
        self.btn_settings.setStyleSheet("background: transparent; border: none; font-size: 11px; color: #94a3b8;")
        self.btn_settings.clicked.connect(self.request_open_settings.emit)
        top_layout.addWidget(self.btn_settings)

        # Hide button
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(18, 18)
        self.btn_close.setToolTip("Hide Overlay")
        self.btn_close.setStyleSheet("background: transparent; border: none; font-size: 11px; color: #94a3b8;")
        self.btn_close.clicked.connect(self.hide)
        top_layout.addWidget(self.btn_close)

    def apply_config(self, config: OverlayConfig):
        """Re-applies geometry, styles, and statistic widgets based on active config."""
        self.config = config
        self.setWindowOpacity(self.config.opacity)

        # Update window geometry
        self.setGeometry(
            self.config.window_x,
            self.config.window_y,
            self.config.window_width,
            self.config.window_height
        )
        self.container.setGeometry(0, 0, self.width(), self.height())
        self.top_bar.setGeometry(0, 0, self.width(), 24)

        # Update styling
        self.container.setStyleSheet(f"""
            QWidget#OverlayContainer {{
                background-color: rgba(15, 23, 42, 230);
                border: 1px solid rgba(51, 65, 85, 200);
                border-radius: 8px;
            }}
        """)
        self.btn_lock.setText("🔒" if self.config.locked else "🔓")

        # Clean existing widgets
        for card in self._number_cards.values():
            card.deleteLater()
        for g_card in self._graph_cards.values():
            g_card.deleteLater()
        self._number_cards.clear()
        self._graph_cards.clear()

        # Instantiate widgets for each enabled statistic
        for stat_id, item in self.config.stats.items():
            if not item.enabled or item.mode == DisplayMode.DONT_SHOW:
                continue

            if item.mode == DisplayMode.NUMBERS:
                card = NumberBadgeCard(item, self.container)
                card.setGeometry(item.x, item.y, item.width, item.height)
                card.show()
                self._number_cards[stat_id] = card

            elif item.mode == DisplayMode.GRAPH:
                graph = MiniGraphWidget(
                    title=item.name,
                    unit=item.unit,
                    color=item.color,
                    scale_mode=item.graph_scale_mode,
                    min_val=item.graph_min,
                    max_val=item.graph_max,
                    history_len=item.history_len,
                    parent=self.container
                )
                graph.setGeometry(item.x, item.y, item.width, item.height)
                graph.show()
                self._graph_cards[stat_id] = graph

    def update_metrics(self, snapshot: Dict[str, Any]):
        """Receives real-time telemetry snapshot and updates all visible widgets."""
        for stat_id, data in snapshot.items():
            display_str = data.get("display", "--")
            val = data.get("val", 0.0)
            history = data.get("history", [])

            if stat_id in self._number_cards:
                self._number_cards[stat_id].set_value(display_str)

            if stat_id in self._graph_cards:
                self._graph_cards[stat_id].set_data(history, current_val=val, display_str=display_str)

    def toggle_stat_visibility(self, stat_id: str):
        """Toggles an individual statistic on/off while preserving its mode."""
        if stat_id in self.config.stats:
            item = self.config.stats[stat_id]
            item.enabled = not item.enabled
            self.apply_config(self.config)
            self.config.save()

    def _toggle_lock(self):
        self.config.locked = not self.config.locked
        self.btn_lock.setText("🔒" if self.config.locked else "🔓")
        self.config.save()

    # --- Mouse Drag-to-Reposition Logic ---

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and not self.config.locked:
            self._is_dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_dragging and not self.config.locked:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos)
            self.config.window_x = new_pos.x()
            self.config.window_y = new_pos.y()
            self.window_moved.emit(new_pos.x(), new_pos.y())
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._is_dragging:
            self._is_dragging = False
            self.config.save()
            event.accept()
