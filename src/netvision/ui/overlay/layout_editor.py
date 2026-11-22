"""
NetVision - Visual Drag-and-Resize Overlay Editor
Dedicated interactive canvas for freeform positioning, 8-handle resizing,
alignment guides, optional grid snapping, undo/redo, and live preview.
"""

from typing import Dict, List, Optional, Tuple, Any
import copy
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
    QSlider, QScrollArea, QColorDialog, QSplitter, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt, QPoint, QRect, Signal, QSize
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QMouseEvent,
    QCursor, QPaintEvent
)

from netvision.core.overlay_config import OverlayConfig, StatItemConfig, DisplayMode
from netvision.ui.overlay.mini_graph import MiniGraphWidget


HANDLE_NONE = 0
HANDLE_TL = 1
HANDLE_T = 2
HANDLE_TR = 3
HANDLE_R = 4
HANDLE_BR = 5
HANDLE_B = 6
HANDLE_BL = 7
HANDLE_L = 8
HANDLE_SIZE = 7


class DraggableCardWidget(QFrame):
    """
    Interactive card on the editor canvas supporting free dragging and 8-point resizing.
    """

    selected = Signal(str)
    geometry_changed = Signal(str, QRect)

    def __init__(self, item: StatItemConfig, parent=None):
        super().__init__(parent)
        self.item = item
        self.stat_id = item.stat_id
        self.is_selected = False

        self._resizing_handle = HANDLE_NONE
        self._is_dragging = False
        self._drag_start_pos = QPoint()
        self._orig_geometry = QRect()

        self.setMouseTracking(True)
        self._build_content()
        self.update_geometry_from_item()

    def _build_content(self):
        self.layout_box = QVBoxLayout(self)
        self.layout_box.setContentsMargins(8, 6, 8, 6)
        self.layout_box.setSpacing(2)

        self.lbl_title = QLabel(self.item.name, self)
        self.lbl_title.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold;")
        self.layout_box.addWidget(self.lbl_title)

        self.lbl_value = QLabel("--", self)
        self.lbl_value.setStyleSheet(f"color: {self.item.color}; font-size: 13px; font-weight: bold;")
        self.layout_box.addWidget(self.lbl_value)

        self.graph_preview: Optional[MiniGraphWidget] = None
        self._sync_mode_view()

    def _sync_mode_view(self):
        if self.item.mode == DisplayMode.GRAPH:
            self.lbl_value.hide()
            if not self.graph_preview:
                self.graph_preview = MiniGraphWidget(
                    title=self.item.name,
                    unit=self.item.unit,
                    color=self.item.color,
                    parent=self
                )
                self.layout_box.addWidget(self.graph_preview)
            self.graph_preview.show()
        else:
            if self.graph_preview:
                self.graph_preview.hide()
            self.lbl_value.show()

    def update_geometry_from_item(self):
        self.setGeometry(self.item.x, self.item.y, self.item.width, self.item.height)
        self.lbl_value.setStyleSheet(f"color: {self.item.color}; font-size: {self.item.font_size}px; font-weight: bold;")
        self._sync_mode_view()
        self.update()

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update()

    def set_preview_data(self, display_str: str, history: List[float], val: float):
        self.lbl_value.setText(display_str)
        if self.graph_preview and self.item.mode == DisplayMode.GRAPH:
            self.graph_preview.set_data(history, current_val=val, display_str=display_str)

    # --- 8-Handle Resizing and Drag Hit-Testing ---

    def _get_handle_rects(self) -> Dict[int, QRect]:
        w, h = self.width(), self.height()
        s = HANDLE_SIZE
        hs = s // 2
        return {
            HANDLE_TL: QRect(0, 0, s, s),
            HANDLE_T: QRect((w // 2) - hs, 0, s, s),
            HANDLE_TR: QRect(w - s, 0, s, s),
            HANDLE_R: QRect(w - s, (h // 2) - hs, s, s),
            HANDLE_BR: QRect(w - s, h - s, s, s),
            HANDLE_B: QRect((w // 2) - hs, h - s, s, s),
            HANDLE_BL: QRect(0, h - s, s, s),
            HANDLE_L: QRect(0, (h // 2) - hs, s, s),
        }

    def _hit_test_handle(self, pt: QPoint) -> int:
        if not self.is_selected:
            return HANDLE_NONE
        for handle_id, rect in self._get_handle_rects().items():
            if rect.contains(pt):
                return handle_id
        return HANDLE_NONE

    def _cursor_for_handle(self, handle: int) -> Qt.CursorShape:
        if handle in (HANDLE_TL, HANDLE_BR):
            return Qt.SizeFDiagCursor
        elif handle in (HANDLE_TR, HANDLE_BL):
            return Qt.SizeBDiagCursor
        elif handle in (HANDLE_L, HANDLE_R):
            return Qt.SizeHorCursor
        elif handle in (HANDLE_T, HANDLE_B):
            return Qt.SizeVerCursor
        return Qt.ArrowCursor

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.selected.emit(self.stat_id)
            handle = self._hit_test_handle(event.pos())
            self._orig_geometry = self.geometry()
            self._drag_start_pos = event.globalPosition().toPoint()

            if handle != HANDLE_NONE:
                self._resizing_handle = handle
            else:
                self._is_dragging = True
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (self._is_dragging or self._resizing_handle != HANDLE_NONE):
            handle = self._hit_test_handle(event.pos())
            if handle != HANDLE_NONE:
                self.setCursor(self._cursor_for_handle(handle))
            else:
                self.setCursor(Qt.SizeAllCursor if self.is_selected else Qt.ArrowCursor)
            return

        cur_global = event.globalPosition().toPoint()
        dx = cur_global.x() - self._drag_start_pos.x()
        dy = cur_global.y() - self._drag_start_pos.y()
        orig = self._orig_geometry
        parent_canvas: EditorCanvasWidget = self.parentWidget()

        if self._is_dragging:
            new_x = orig.x() + dx
            new_y = orig.y() + dy
            if parent_canvas:
                new_x, new_y = parent_canvas.apply_snapping(self.stat_id, new_x, new_y, orig.width(), orig.height())
            self.move(new_x, new_y)
            self.item.x = new_x
            self.item.y = new_y
            self.geometry_changed.emit(self.stat_id, self.geometry())

        elif self._resizing_handle != HANDLE_NONE:
            nx, ny, nw, nh = orig.x(), orig.y(), orig.width(), orig.height()
            min_w, min_h = 100, 36

            if self._resizing_handle in (HANDLE_R, HANDLE_TR, HANDLE_BR):
                nw = max(min_w, orig.width() + dx)
            if self._resizing_handle in (HANDLE_B, HANDLE_BL, HANDLE_BR):
                nh = max(min_h, orig.height() + dy)
            if self._resizing_handle in (HANDLE_L, HANDLE_TL, HANDLE_BL):
                diff = min(dx, orig.width() - min_w)
                nx = orig.x() + diff
                nw = orig.width() - diff
            if self._resizing_handle in (HANDLE_T, HANDLE_TL, HANDLE_TR):
                diff = min(dy, orig.height() - min_h)
                ny = orig.y() + diff
                nh = orig.height() - diff

            if parent_canvas and parent_canvas.snap_to_grid:
                grid = parent_canvas.grid_size
                nw = max(min_w, round(nw / grid) * grid)
                nh = max(min_h, round(nh / grid) * grid)

            self.setGeometry(nx, ny, nw, nh)
            self.item.x = nx
            self.item.y = ny
            self.item.width = nw
            self.item.height = nh
            if self.item.mode == DisplayMode.GRAPH:
                self.item.graph_width = nw
                self.item.graph_height = nh
            self.geometry_changed.emit(self.stat_id, self.geometry())

        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            was_active = self._is_dragging or (self._resizing_handle != HANDLE_NONE)
            self._is_dragging = False
            self._resizing_handle = HANDLE_NONE
            if was_active:
                parent_canvas: EditorCanvasWidget = self.parentWidget()
                if parent_canvas:
                    parent_canvas.record_history_state()
                    parent_canvas.clear_guides()
            event.accept()

    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.width(), self.height()

        # Normal background & border
        if self.is_selected:
            # Active selection highlight
            pen_sel = QPen(QColor(56, 189, 248), 2)  # Sky 400
            painter.setPen(pen_sel)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(1, 1, w - 2, h - 2, 6, 6)

            # Draw 8 resize handles
            painter.setBrush(QColor(255, 255, 255))
            painter.setPen(QPen(QColor(56, 189, 248), 1))
            for rect in self._get_handle_rects().values():
                painter.drawRect(rect)
        else:
            pen = QPen(QColor(51, 65, 85, 140), 1)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(0, 0, w - 1, h - 1, 6, 6)


class EditorCanvasWidget(QWidget):
    """
    Interactive canvas displaying the overlay bounds, grid, alignment guides,
    and draggable statistic cards.
    """

    item_selected = Signal(str)
    layout_changed = Signal()

    def __init__(self, config: OverlayConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.snap_to_grid = config.snap_to_grid
        self.grid_size = config.grid_size
        self.show_guides = config.show_alignment_guides

        self.cards: Dict[str, DraggableCardWidget] = {}
        self.selected_stat_id: Optional[str] = None

        # Guide lines: (is_vertical: bool, coord: int)
        self._active_guides: List[Tuple[bool, int]] = []

        # Undo / Redo History
        self._history_stack: List[Dict[str, Any]] = []
        self._history_index: int = -1

        self.setMouseTracking(True)
        self._init_canvas()
        self.record_history_state()

    def _init_canvas(self):
        self.setMinimumSize(self.config.window_width + 40, self.config.window_height + 40)
        self.rebuild_cards()

    def rebuild_cards(self):
        for c in self.cards.values():
            c.deleteLater()
        self.cards.clear()

        for stat_id, item in self.config.stats.items():
            if item.mode == DisplayMode.DONT_SHOW:
                continue
            card = DraggableCardWidget(item, self)
            card.selected.connect(self.select_item)
            card.geometry_changed.connect(self._on_item_geometry_changed)
            card.show()
            self.cards[stat_id] = card

        if self.selected_stat_id and self.selected_stat_id in self.cards:
            self.cards[self.selected_stat_id].set_selected(True)
        self.update()

    def select_item(self, stat_id: str):
        self.selected_stat_id = stat_id
        for s_id, card in self.cards.items():
            card.set_selected(s_id == stat_id)
        self.item_selected.emit(stat_id)
        self.update()

    def _on_item_geometry_changed(self, stat_id: str, geom: QRect):
        self.layout_changed.emit()
        self.update()

    def apply_snapping(self, moving_stat_id: str, x: int, y: int, w: int, h: int) -> Tuple[int, int]:
        """Snaps coordinate to grid and checks for alignment guide lines against other cards."""
        self._active_guides.clear()
        snap_dist = 6

        # 1. Grid Snapping
        if self.snap_to_grid:
            x = round(x / self.grid_size) * self.grid_size
            y = round(y / self.grid_size) * self.grid_size

        # 2. Alignment Guides against other cards
        if self.show_guides:
            mid_x = x + (w // 2)
            right_x = x + w
            mid_y = y + (h // 2)
            bot_y = y + h

            for other_id, other_card in self.cards.items():
                if other_id == moving_stat_id:
                    continue
                og = other_card.geometry()
                o_mid_x = og.x() + (og.width() // 2)
                o_right_x = og.x() + og.width()
                o_mid_y = og.y() + (og.height() // 2)
                o_bot_y = og.y() + og.height()

                # Vertical alignments
                if abs(x - og.x()) <= snap_dist:
                    x = og.x()
                    self._active_guides.append((True, x))
                elif abs(mid_x - o_mid_x) <= snap_dist:
                    x = o_mid_x - (w // 2)
                    self._active_guides.append((True, o_mid_x))
                elif abs(right_x - o_right_x) <= snap_dist:
                    x = o_right_x - w
                    self._active_guides.append((True, o_right_x))

                # Horizontal alignments
                if abs(y - og.y()) <= snap_dist:
                    y = og.y()
                    self._active_guides.append((False, y))
                elif abs(mid_y - o_mid_y) <= snap_dist:
                    y = o_mid_y - (h // 2)
                    self._active_guides.append((False, o_mid_y))
                elif abs(bot_y - o_bot_y) <= snap_dist:
                    y = o_bot_y - h
                    self._active_guides.append((False, o_bot_y))

        # Clamp inside reasonable canvas bounds
        x = max(8, x)
        y = max(8, y)
        return x, y

    def clear_guides(self):
        self._active_guides.clear()
        self.update()

    # --- Undo / Redo Stack Management ---

    def record_history_state(self):
        snapshot = {
            "window_width": self.config.window_width,
            "window_height": self.config.window_height,
            "stats": {k: copy.deepcopy(v.to_dict()) for k, v in self.config.stats.items()}
        }
        # Truncate forward history if recording new action after undo
        if self._history_index < len(self._history_stack) - 1:
            self._history_stack = self._history_stack[:self._history_index + 1]

        self._history_stack.append(snapshot)
        self._history_index = len(self._history_stack) - 1
        # Limit stack size
        if len(self._history_stack) > 30:
            self._history_stack.pop(0)
            self._history_index -= 1

    def can_undo(self) -> bool:
        return self._history_index > 0

    def can_redo(self) -> bool:
        return self._history_index < len(self._history_stack) - 1

    def undo(self):
        if self.can_undo():
            self._history_index -= 1
            self._restore_state(self._history_stack[self._history_index])

    def redo(self):
        if self.can_redo():
            self._history_index += 1
            self._restore_state(self._history_stack[self._history_index])

    def _restore_state(self, state: Dict[str, Any]):
        self.config.window_width = state.get("window_width", self.config.window_width)
        self.config.window_height = state.get("window_height", self.config.window_height)
        stats_data = state.get("stats", {})
        for s_id, s_dict in stats_data.items():
            if s_id in self.config.stats:
                self.config.stats[s_id] = StatItemConfig.from_dict(s_dict)
        self.rebuild_cards()
        self.layout_changed.emit()

    def update_live_telemetry(self, snapshot: Dict[str, Any]):
        for stat_id, data in snapshot.items():
            if stat_id in self.cards:
                display_str = data.get("display", "--")
                history = data.get("history", [])
                val = data.get("val", 0.0)
                self.cards[stat_id].set_preview_data(display_str, history, val)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        cw, ch = self.width(), self.height()

        # Canvas workspace background
        painter.fillRect(0, 0, cw, ch, QColor(15, 23, 42))  # Slate 900

        # Draw grid dots
        if self.snap_to_grid:
            grid_pen = QPen(QColor(51, 65, 85, 90), 1)
            painter.setPen(grid_pen)
            step = max(8, self.grid_size)
            for gx in range(0, cw, step):
                for gy in range(0, ch, step):
                    painter.drawPoint(gx, gy)

        # Draw Overlay Window Outer Boundary Frame
        b_pen = QPen(QColor(56, 189, 248, 120), 1, Qt.DashLine)
        painter.setPen(b_pen)
        painter.setBrush(QColor(30, 41, 59, 100))
        painter.drawRect(0, 0, self.config.window_width, self.config.window_height)

        # Draw Overlay Frame Label
        font_lbl = QFont("Segoe UI", 9)
        painter.setFont(font_lbl)
        painter.setPen(QColor(148, 163, 184))
        painter.drawText(
            self.config.window_width - 150,
            self.config.window_height - 8,
            f"Overlay Bounds: {self.config.window_width}x{self.config.window_height}"
        )

        # Draw Alignment Guide Lines
        if self.show_guides and self._active_guides:
            guide_pen = QPen(QColor(244, 63, 94, 200), 1, Qt.SolidLine)
            painter.setPen(guide_pen)
            for is_vert, pos in self._active_guides:
                if is_vert:
                    painter.drawLine(pos, 0, pos, ch)
                else:
                    painter.drawLine(0, pos, cw, pos)


class OverlayLayoutEditor(QWidget):
    """
    Main Visual Layout Editor widget containing toolbar, interactive canvas,
    and a fine-tuning properties sidebar.
    """

    layout_saved = Signal(OverlayConfig)

    def __init__(self, config: OverlayConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Top Control Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #1e293b; border-radius: 6px; padding: 4px;")
        t_layout = QHBoxLayout(toolbar)
        t_layout.setContentsMargins(8, 4, 8, 4)
        t_layout.setSpacing(10)

        # Undo / Redo buttons
        self.btn_undo = QPushButton("↶ Undo")
        self.btn_undo.setProperty("class", "SecondaryButton")
        self.btn_undo.clicked.connect(self._on_undo)
        t_layout.addWidget(self.btn_undo)

        self.btn_redo = QPushButton("↷ Redo")
        self.btn_redo.setProperty("class", "SecondaryButton")
        self.btn_redo.clicked.connect(self._on_redo)
        t_layout.addWidget(self.btn_redo)

        # Reset Layout button
        self.btn_reset = QPushButton("↺ Reset Layout")
        self.btn_reset.setProperty("class", "SecondaryButton")
        self.btn_reset.clicked.connect(self._on_reset_layout)
        t_layout.addWidget(self.btn_reset)

        t_layout.addSpacing(12)

        # Grid Snapping Toggle & Size
        self.chk_snap = QCheckBox("Snap to Grid")
        self.chk_snap.setChecked(self.config.snap_to_grid)
        self.chk_snap.toggled.connect(self._on_snap_toggled)
        t_layout.addWidget(self.chk_snap)

        t_layout.addWidget(QLabel("Grid:"))
        self.spin_grid = QSpinBox()
        self.spin_grid.setRange(4, 32)
        self.spin_grid.setValue(self.config.grid_size)
        self.spin_grid.valueChanged.connect(self._on_grid_size_changed)
        t_layout.addWidget(self.spin_grid)

        # Alignment Guides Toggle
        self.chk_guides = QCheckBox("Alignment Guides")
        self.chk_guides.setChecked(self.config.show_alignment_guides)
        self.chk_guides.toggled.connect(self._on_guides_toggled)
        t_layout.addWidget(self.chk_guides)

        # Live Preview Mode Toggle
        self.chk_live_preview = QCheckBox("Live Telemetry")
        self.chk_live_preview.setChecked(True)
        t_layout.addWidget(self.chk_live_preview)

        t_layout.addStretch()

        # Canvas Resize dimensions
        t_layout.addWidget(QLabel("Overlay Size:"))
        self.spin_win_w = QSpinBox()
        self.spin_win_w.setRange(200, 1920)
        self.spin_win_w.setValue(self.config.window_width)
        self.spin_win_w.valueChanged.connect(self._on_win_size_changed)
        t_layout.addWidget(self.spin_win_w)

        t_layout.addWidget(QLabel("x"))
        self.spin_win_h = QSpinBox()
        self.spin_win_h.setRange(100, 1080)
        self.spin_win_h.setValue(self.config.window_height)
        self.spin_win_h.valueChanged.connect(self._on_win_size_changed)
        t_layout.addWidget(self.spin_win_h)

        main_layout.addWidget(toolbar)

        # Middle Area: Splitter between Canvas and Properties Panel
        splitter = QSplitter(Qt.Horizontal)

        # Left / Center: Scrollable Canvas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #0f172a; border: 1px solid #334155; border-radius: 6px;")
        self.canvas = EditorCanvasWidget(self.config)
        self.canvas.item_selected.connect(self._on_item_selected)
        self.canvas.layout_changed.connect(self._on_canvas_layout_changed)
        scroll.setWidget(self.canvas)
        splitter.addWidget(scroll)

        # Right: Item Properties Panel
        prop_panel = self._build_properties_panel()
        splitter.addWidget(prop_panel)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)
        self._update_undo_redo_buttons()

    def _build_properties_panel(self) -> QWidget:
        panel = QFrame()
        panel.setProperty("class", "ContentCard")
        panel.setMinimumWidth(240)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        p_title = QLabel("Statistic Properties")
        p_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(p_title)

        self.lbl_prop_item = QLabel("Select a statistic to customize")
        self.lbl_prop_item.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(self.lbl_prop_item)

        grid = QGridLayout()
        grid.setSpacing(8)

        # Display Mode
        grid.addWidget(QLabel("Display Mode:"), 0, 0)
        self.combo_mode = QComboBox()
        self.combo_mode.addItem("Don't Show", DisplayMode.DONT_SHOW)
        self.combo_mode.addItem("Numbers", DisplayMode.NUMBERS)
        self.combo_mode.addItem("Graph", DisplayMode.GRAPH)
        self.combo_mode.currentIndexChanged.connect(self._on_prop_mode_changed)
        grid.addWidget(self.combo_mode, 0, 1)

        # X & Y Pos
        grid.addWidget(QLabel("Position X:"), 1, 0)
        self.spin_x = QSpinBox()
        self.spin_x.setRange(0, 2000)
        self.spin_x.valueChanged.connect(self._on_prop_geom_changed)
        grid.addWidget(self.spin_x, 1, 1)

        grid.addWidget(QLabel("Position Y:"), 2, 0)
        self.spin_y = QSpinBox()
        self.spin_y.setRange(0, 2000)
        self.spin_y.valueChanged.connect(self._on_prop_geom_changed)
        grid.addWidget(self.spin_y, 2, 1)

        # Width & Height
        grid.addWidget(QLabel("Width:"), 3, 0)
        self.spin_w = QSpinBox()
        self.spin_w.setRange(60, 600)
        self.spin_w.valueChanged.connect(self._on_prop_geom_changed)
        grid.addWidget(self.spin_w, 3, 1)

        grid.addWidget(QLabel("Height:"), 4, 0)
        self.spin_h = QSpinBox()
        self.spin_h.setRange(24, 300)
        self.spin_h.valueChanged.connect(self._on_prop_geom_changed)
        grid.addWidget(self.spin_h, 4, 1)

        # Font Size
        grid.addWidget(QLabel("Font Size:"), 5, 0)
        self.spin_font = QSpinBox()
        self.spin_font.setRange(9, 32)
        self.spin_font.valueChanged.connect(self._on_prop_style_changed)
        grid.addWidget(self.spin_font, 5, 1)

        # Padding
        grid.addWidget(QLabel("Padding:"), 6, 0)
        self.spin_pad = QSpinBox()
        self.spin_pad.setRange(2, 24)
        self.spin_pad.valueChanged.connect(self._on_prop_style_changed)
        grid.addWidget(self.spin_pad, 6, 1)

        # Color picker button
        grid.addWidget(QLabel("Accent Color:"), 7, 0)
        self.btn_color = QPushButton("Pick Color")
        self.btn_color.clicked.connect(self._on_pick_color)
        grid.addWidget(self.btn_color, 7, 1)

        # Graph Scale Mode
        grid.addWidget(QLabel("Graph Scale:"), 8, 0)
        self.combo_scale = QComboBox()
        self.combo_scale.addItem("Auto Scaling", "auto")
        self.combo_scale.addItem("Fixed (0-100)", "fixed")
        self.combo_scale.currentIndexChanged.connect(self._on_prop_style_changed)
        grid.addWidget(self.combo_scale, 8, 1)

        layout.addLayout(grid)
        layout.addStretch()

        return panel

    def _on_item_selected(self, stat_id: str):
        item = self.config.stats.get(stat_id)
        if not item:
            return
        self.lbl_prop_item.setText(f"Editing: {item.name}")
        
        idx = self.combo_mode.findData(item.mode)
        if idx >= 0:
            self.combo_mode.blockSignals(True)
            self.combo_mode.setCurrentIndex(idx)
            self.combo_mode.blockSignals(False)

        for spin, val in (
            (self.spin_x, item.x),
            (self.spin_y, item.y),
            (self.spin_w, item.width),
            (self.spin_h, item.height),
            (self.spin_font, item.font_size),
            (self.spin_pad, item.padding),
        ):
            spin.blockSignals(True)
            spin.setValue(val)
            spin.blockSignals(False)

        idx_s = self.combo_scale.findData(item.graph_scale_mode)
        if idx_s >= 0:
            self.combo_scale.blockSignals(True)
            self.combo_scale.setCurrentIndex(idx_s)
            self.combo_scale.blockSignals(False)

        self.btn_color.setStyleSheet(f"background-color: {item.color}; color: #000; font-weight: bold;")

    def _on_prop_mode_changed(self):
        stat_id = self.canvas.selected_stat_id
        if not stat_id or stat_id not in self.config.stats:
            return
        mode = self.combo_mode.currentData()
        self.config.stats[stat_id].mode = mode
        self.canvas.rebuild_cards()
        self.canvas.record_history_state()
        self._on_canvas_layout_changed()

    def _on_prop_geom_changed(self):
        stat_id = self.canvas.selected_stat_id
        if not stat_id or stat_id not in self.config.stats:
            return
        item = self.config.stats[stat_id]
        item.x = self.spin_x.value()
        item.y = self.spin_y.value()
        item.width = self.spin_w.value()
        item.height = self.spin_h.value()
        if item.mode == DisplayMode.GRAPH:
            item.graph_width = item.width
            item.graph_height = item.height

        if stat_id in self.canvas.cards:
            self.canvas.cards[stat_id].update_geometry_from_item()
        self._on_canvas_layout_changed()

    def _on_prop_style_changed(self):
        stat_id = self.canvas.selected_stat_id
        if not stat_id or stat_id not in self.config.stats:
            return
        item = self.config.stats[stat_id]
        item.font_size = self.spin_font.value()
        item.padding = self.spin_pad.value()
        item.graph_scale_mode = self.combo_scale.currentData()
        if stat_id in self.canvas.cards:
            self.canvas.cards[stat_id].update_geometry_from_item()
        self._on_canvas_layout_changed()

    def _on_pick_color(self):
        stat_id = self.canvas.selected_stat_id
        if not stat_id or stat_id not in self.config.stats:
            return
        item = self.config.stats[stat_id]
        c = QColorDialog.getColor(QColor(item.color), self, "Select Statistic Color")
        if c.isValid():
            item.color = c.name()
            self.btn_color.setStyleSheet(f"background-color: {item.color}; color: #000; font-weight: bold;")
            if stat_id in self.canvas.cards:
                self.canvas.cards[stat_id].update_geometry_from_item()
            self.canvas.record_history_state()
            self._on_canvas_layout_changed()

    def _on_snap_toggled(self, checked: bool):
        self.config.snap_to_grid = checked
        self.canvas.snap_to_grid = checked
        self.canvas.update()

    def _on_grid_size_changed(self, val: int):
        self.config.grid_size = val
        self.canvas.grid_size = val
        self.canvas.update()

    def _on_guides_toggled(self, checked: bool):
        self.config.show_alignment_guides = checked
        self.canvas.show_guides = checked
        self.canvas.update()

    def _on_win_size_changed(self):
        self.config.window_width = self.spin_win_w.value()
        self.config.window_height = self.spin_win_h.value()
        self.canvas.setMinimumSize(self.config.window_width + 40, self.config.window_height + 40)
        self.canvas.update()
        self._on_canvas_layout_changed()

    def _on_undo(self):
        self.canvas.undo()
        self._update_undo_redo_buttons()

    def _on_redo(self):
        self.canvas.redo()
        self._update_undo_redo_buttons()

    def _update_undo_redo_buttons(self):
        self.btn_undo.setEnabled(self.canvas.can_undo())
        self.btn_redo.setEnabled(self.canvas.can_redo())

    def _on_reset_layout(self):
        self.config.apply_preset("Detailed")
        self.spin_win_w.setValue(self.config.window_width)
        self.spin_win_h.setValue(self.config.window_height)
        self.canvas.rebuild_cards()
        self.canvas.record_history_state()
        self._on_canvas_layout_changed()

    def _on_canvas_layout_changed(self):
        self._update_undo_redo_buttons()
        self.layout_saved.emit(self.config)

    def update_telemetry(self, snapshot: Dict[str, Any]):
        if self.chk_live_preview.isChecked():
            self.canvas.update_live_telemetry(snapshot)
