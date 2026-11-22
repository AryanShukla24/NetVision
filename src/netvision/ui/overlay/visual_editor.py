"""
NetVision - Visual Overlay Desktop Editor
Interactive simulated desktop canvas allowing users to visually reposition
and resize floating statistic widgets with alignment guides, edge snapping,
properties panel, undo/redo, and isolated edit/preview states.
"""

from typing import Dict, List, Optional, Tuple, Any
import copy
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSpinBox, QComboBox, QCheckBox,
    QSlider, QColorDialog, QSplitter, QScrollArea, QGroupBox,
    QApplication
)
from PySide6.QtCore import Qt, QPoint, QRect, Signal, QSize, QTimer
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QMouseEvent,
    QCursor, QPaintEvent, QGuiApplication, QPixmap, QScreen
)

logger = logging.getLogger(__name__)

from netvision.core.overlay_config import (
    OverlayConfig, StatItemConfig, DisplayMode, get_default_stats_catalog
)
from netvision.ui.overlay.mini_graph import MiniGraphWidget

# Handle identifiers for 8-point resizing
HANDLE_NONE = 0
HANDLE_TL = 1
HANDLE_T = 2
HANDLE_TR = 3
HANDLE_R = 4
HANDLE_BR = 5
HANDLE_B = 6
HANDLE_BL = 7
HANDLE_L = 8
HANDLE_SIZE = 8


class SimulatedDesktopCanvas(QWidget):
    """
    Renders a scaled simulation of the user's actual desktop workspace.
    Widgets appear at their true proportional coordinates and can be
    interactively clicked, dragged, and resized with 8-point handles.
    """

    widget_selected = Signal(str)
    geometry_modified = Signal(str)

    def __init__(self, config: OverlayConfig, screen_res: Tuple[int, int] = (1366, 768), parent=None):
        super().__init__(parent)
        self.config = config
        self.res_w, self.res_h = screen_res
        self.snap_to_edges = True
        self.show_guides = True
        self.live_telemetry_active = True

        self.selected_stat_id: Optional[str] = None
        self._hovered_stat_id: Optional[str] = None

        # Drag & resize state
        self._active_handle = HANDLE_NONE
        self._is_dragging = False
        self._drag_start_screen = QPoint()
        self._orig_widget_rect = QRect()  # In true desktop coordinates

        # Alignment guides: list of (is_vertical: bool, desktop_coord: int)
        self._active_guides: List[Tuple[bool, int]] = []

        # Latest telemetry snapshot cache for live preview
        self._telemetry_cache: Dict[str, Any] = {}

        # Real desktop background capture pixmap
        self.desktop_pixmap: Optional[QPixmap] = None

        self.setMouseTracking(True)
        self.setMinimumSize(540, 320)

    def set_desktop_pixmap(self, pixmap: Optional[QPixmap]):
        self.desktop_pixmap = pixmap
        self.update()

    def set_resolution(self, res_w: int, res_h: int):
        self.res_w = max(640, res_w)
        self.res_h = max(480, res_h)
        self.update()

    def set_config(self, config: OverlayConfig):
        self.config = config
        self.update()

    def get_desktop_rect(self) -> QRect:
        """Calculates centered, aspect-ratio-preserved desktop preview bounds."""
        cw, ch = self.width(), self.height()
        pad = 6  # Maximized preview workspace
        avail_w = max(100, cw - (pad * 2))
        avail_h = max(100, ch - (pad * 2))

        aspect = self.res_w / self.res_h
        if (avail_w / avail_h) > aspect:
            h = avail_h
            w = int(h * aspect)
        else:
            w = avail_w
            h = int(w / aspect)

        x = (cw - w) // 2
        y = (ch - h) // 2
        return QRect(x, y, w, h)

    def desktop_to_canvas_rect(self, dr: QRect, desktop_x: int, desktop_y: int, desktop_w: int, desktop_h: int) -> QRect:
        """Converts desktop screen coordinates to canvas pixels."""
        scale_x = dr.width() / self.res_w
        scale_y = dr.height() / self.res_h
        cx = dr.x() + int(desktop_x * scale_x)
        cy = dr.y() + int(desktop_y * scale_y)
        cw = max(55, int(desktop_w * scale_x))
        ch = max(22, int(desktop_h * scale_y))
        return QRect(cx, cy, cw, ch)

    def canvas_to_desktop_pos(self, dr: QRect, cx: int, cy: int) -> Tuple[int, int]:
        """Converts canvas pixel coordinate back to true desktop screen coordinates."""
        scale_x = dr.width() / self.res_w
        scale_y = dr.height() / self.res_h
        dx = int((cx - dr.x()) / scale_x)
        dy = int((cy - dr.y()) / scale_y)
        return dx, dy

    def canvas_to_desktop_size(self, dr: QRect, cw: int, ch: int) -> Tuple[int, int]:
        scale_x = dr.width() / self.res_w
        scale_y = dr.height() / self.res_h
        dw = int(cw / scale_x)
        dh = int(ch / scale_y)
        return dw, dh

    def _get_widget_canvas_rect(self, dr: QRect, stat_id: str) -> Optional[QRect]:
        item = self.config.stats.get(stat_id)
        if not item or item.mode == DisplayMode.DONT_SHOW:
            return None
        w = item.graph_width if item.mode == DisplayMode.GRAPH else item.width
        h = item.graph_height if item.mode == DisplayMode.GRAPH else item.height
        return self.desktop_to_canvas_rect(dr, item.x, item.y, w, h)

    def _get_resize_handles(self, r: QRect) -> Dict[int, QRect]:
        s = HANDLE_SIZE
        hs = s // 2
        return {
            HANDLE_TL: QRect(r.left() - hs, r.top() - hs, s, s),
            HANDLE_T: QRect(r.center().x() - hs, r.top() - hs, s, s),
            HANDLE_TR: QRect(r.right() - hs, r.top() - hs, s, s),
            HANDLE_R: QRect(r.right() - hs, r.center().y() - hs, s, s),
            HANDLE_BR: QRect(r.right() - hs, r.bottom() - hs, s, s),
            HANDLE_B: QRect(r.center().x() - hs, r.bottom() - hs, s, s),
            HANDLE_BL: QRect(r.left() - hs, r.bottom() - hs, s, s),
            HANDLE_L: QRect(r.left() - hs, r.center().y() - hs, s, s),
        }

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
        if event.button() != Qt.LeftButton:
            return

        dr = self.get_desktop_rect()
        pos = event.pos()

        # 1. Check if clicking on resize handles of selected widget
        if self.selected_stat_id:
            sel_rect = self._get_widget_canvas_rect(dr, self.selected_stat_id)
            if sel_rect:
                for h_id, h_rect in self._get_resize_handles(sel_rect).items():
                    if h_rect.contains(pos):
                        self._active_handle = h_id
                        self._drag_start_screen = pos
                        item = self.config.stats[self.selected_stat_id]
                        w = item.graph_width if item.mode == DisplayMode.GRAPH else item.width
                        h = item.graph_height if item.mode == DisplayMode.GRAPH else item.height
                        self._orig_widget_rect = QRect(item.x, item.y, w, h)
                        event.accept()
                        return

        # 2. Check if clicking on any enabled widget to select and drag
        clicked_id = None
        for stat_id, item in reversed(list(self.config.stats.items())):
            if item.mode == DisplayMode.DONT_SHOW:
                continue
            r = self._get_widget_canvas_rect(dr, stat_id)
            if r and r.contains(pos):
                clicked_id = stat_id
                break

        if clicked_id:
            self.selected_stat_id = clicked_id
            self.widget_selected.emit(clicked_id)
            self._is_dragging = True
            self._drag_start_screen = pos
            item = self.config.stats[clicked_id]
            w = item.graph_width if item.mode == DisplayMode.GRAPH else item.width
            h = item.graph_height if item.mode == DisplayMode.GRAPH else item.height
            self._orig_widget_rect = QRect(item.x, item.y, w, h)
        else:
            self.selected_stat_id = None
            self.widget_selected.emit("")

        self.update()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        dr = self.get_desktop_rect()
        pos = event.pos()

        # Update cursor when hovering over resize handles
        if not (self._is_dragging or self._active_handle != HANDLE_NONE):
            cursor_set = False
            if self.selected_stat_id:
                sel_rect = self._get_widget_canvas_rect(dr, self.selected_stat_id)
                if sel_rect:
                    for h_id, h_rect in self._get_resize_handles(sel_rect).items():
                        if h_rect.contains(pos):
                            self.setCursor(self._cursor_for_handle(h_id))
                            cursor_set = True
                            break
            if not cursor_set:
                hovered = None
                for stat_id, item in self.config.stats.items():
                    if item.mode == DisplayMode.DONT_SHOW:
                        continue
                    r = self._get_widget_canvas_rect(dr, stat_id)
                    if r and r.contains(pos):
                        hovered = stat_id
                        break
                self._hovered_stat_id = hovered
                self.setCursor(Qt.SizeAllCursor if hovered else Qt.ArrowCursor)
            return

        scale_x = dr.width() / self.res_w
        scale_y = dr.height() / self.res_h

        # 1. Dragging widget to reposition
        if self._is_dragging and self.selected_stat_id:
            item = self.config.stats[self.selected_stat_id]
            dx = int((pos.x() - self._drag_start_screen.x()) / scale_x)
            dy = int((pos.y() - self._drag_start_screen.y()) / scale_y)

            new_x = self._orig_widget_rect.x() + dx
            new_y = self._orig_widget_rect.y() + dy

            # Apply edge snapping and alignment guides
            new_x, new_y = self._apply_desktop_snapping(
                self.selected_stat_id, new_x, new_y,
                self._orig_widget_rect.width(), self._orig_widget_rect.height()
            )

            item.x = new_x
            item.y = new_y
            self.geometry_modified.emit(self.selected_stat_id)
            self.update()

        # 2. Resizing widget with 8 handles
        elif self._active_handle != HANDLE_NONE and self.selected_stat_id:
            item = self.config.stats[self.selected_stat_id]
            dx = int((pos.x() - self._drag_start_screen.x()) / scale_x)
            dy = int((pos.y() - self._drag_start_screen.y()) / scale_y)
            orig = self._orig_widget_rect

            nx, ny, nw, nh = orig.x(), orig.y(), orig.width(), orig.height()
            min_w, min_h = 90, 32

            if self._active_handle in (HANDLE_R, HANDLE_TR, HANDLE_BR):
                nw = max(min_w, orig.width() + dx)
            if self._active_handle in (HANDLE_B, HANDLE_BL, HANDLE_BR):
                nh = max(min_h, orig.height() + dy)
            if self._active_handle in (HANDLE_L, HANDLE_TL, HANDLE_BL):
                diff = min(dx, orig.width() - min_w)
                nx = orig.x() + diff
                nw = orig.width() - diff
            if self._active_handle in (HANDLE_T, HANDLE_TL, HANDLE_TR):
                diff = min(dy, orig.height() - min_h)
                ny = orig.y() + diff
                nh = orig.height() - diff

            item.x = max(0, nx)
            item.y = max(0, ny)
            if item.mode == DisplayMode.GRAPH:
                item.graph_width = nw
                item.graph_height = nh
            else:
                item.width = nw
                item.height = nh

            self.geometry_modified.emit(self.selected_stat_id)
            self.update()

        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            self._active_handle = HANDLE_NONE
            self._active_guides.clear()
            self.update()
            event.accept()

    def _apply_desktop_snapping(self, moving_id: str, x: int, y: int, w: int, h: int) -> Tuple[int, int]:
        """Snaps to screen borders and aligns with other widgets on the simulated desktop."""
        self._active_guides.clear()
        snap_thresh = 14

        # 1. Desktop Edge Snapping
        if self.snap_to_edges:
            # Snap to left edge
            if abs(x - 20) <= snap_thresh:
                x = 20
                self._active_guides.append((True, 20))
            # Snap to right edge
            if abs((x + w) - (self.res_w - 20)) <= snap_thresh:
                x = self.res_w - 20 - w
                self._active_guides.append((True, self.res_w - 20))
            # Snap to top edge
            if abs(y - 20) <= snap_thresh:
                y = 20
                self._active_guides.append((False, 20))
            # Snap to bottom edge
            if abs((y + h) - (self.res_h - 20)) <= snap_thresh:
                y = self.res_h - 20 - h
                self._active_guides.append((False, self.res_h - 20))

        # 2. Alignment with other widgets
        if self.show_guides:
            mid_x = x + (w // 2)
            right_x = x + w
            mid_y = y + (h // 2)
            bot_y = y + h

            for other_id, other_item in self.config.stats.items():
                if other_id == moving_id or other_item.mode == DisplayMode.DONT_SHOW:
                    continue
                ow = other_item.graph_width if other_item.mode == DisplayMode.GRAPH else other_item.width
                oh = other_item.graph_height if other_item.mode == DisplayMode.GRAPH else other_item.height

                # Vertical column alignments
                if abs(x - other_item.x) <= snap_thresh:
                    x = other_item.x
                    self._active_guides.append((True, x))
                elif abs(right_x - (other_item.x + ow)) <= snap_thresh:
                    x = other_item.x + ow - w
                    self._active_guides.append((True, other_item.x + ow))

                # Horizontal row alignments
                if abs(y - other_item.y) <= snap_thresh:
                    y = other_item.y
                    self._active_guides.append((False, y))
                elif abs(bot_y - (other_item.y + oh)) <= snap_thresh:
                    y = other_item.y + oh - h
                    self._active_guides.append((False, other_item.y + oh))

        # Clamp inside resolution bounds
        x = max(0, min(self.res_w - w, x))
        y = max(0, min(self.res_h - h, y))
        return x, y

    def update_live_telemetry(self, snapshot: Dict[str, Any]):
        self._telemetry_cache = snapshot
        if self.live_telemetry_active:
            self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        cw, ch = self.width(), self.height()
        painter.fillRect(0, 0, cw, ch, QColor(11, 15, 25))

        # Draw Simulated Desktop Workspace
        dr = self.get_desktop_rect()

        # Draw Desktop Workspace (Live capture or simulated fallback)
        dr = self.get_desktop_rect()

        if self.desktop_pixmap and not self.desktop_pixmap.isNull():
            # Actual live desktop capture preview
            painter.drawPixmap(dr, self.desktop_pixmap)
            # Subtle glass tint overlay to guarantee widget readability against any background
            painter.fillRect(dr, QColor(0, 0, 0, 35))
            pen_border = QPen(QColor(56, 189, 248, 200), 2)
            painter.setPen(pen_border)
            painter.drawRect(dr)

            # Live watermark badge
            font_watermark = QFont("Segoe UI", 9, QFont.Bold)
            painter.setFont(font_watermark)
            painter.setPen(QColor(52, 211, 153))
            wm_text = f"● Live Desktop Preview ({self.res_w} × {self.res_h})"
            painter.drawText(dr.right() - painter.fontMetrics().horizontalAdvance(wm_text) - 12, dr.bottom() - 12, wm_text)
        else:
            # Fallback high-tech simulated dark grid
            painter.fillRect(dr, QColor(15, 23, 42))
            pen_border = QPen(QColor(56, 189, 248, 140), 1.5)
            painter.setPen(pen_border)
            painter.drawRect(dr)

            font_watermark = QFont("Segoe UI", 9, QFont.Bold)
            painter.setFont(font_watermark)
            painter.setPen(QColor(148, 163, 184))
            wm_text = f"Simulated Display ({self.res_w} × {self.res_h})"
            painter.drawText(dr.right() - painter.fontMetrics().horizontalAdvance(wm_text) - 12, dr.bottom() - 12, wm_text)

        # Draw Alignment Guide Lines (Cyan/Red)
        scale_x = dr.width() / self.res_w
        scale_y = dr.height() / self.res_h

        if self._active_guides:
            guide_pen = QPen(QColor(244, 63, 94, 220), 1, Qt.DashLine)
            painter.setPen(guide_pen)
            for is_vert, d_coord in self._active_guides:
                if is_vert:
                    cx = dr.x() + int(d_coord * scale_x)
                    painter.drawLine(cx, dr.top(), cx, dr.bottom())
                else:
                    cy = dr.y() + int(d_coord * scale_y)
                    painter.drawLine(dr.left(), cy, dr.right(), cy)

        # Draw Each Enabled Statistic Widget on the Desktop
        for stat_id, item in self.config.stats.items():
            if item.mode == DisplayMode.DONT_SHOW:
                continue

            wr = self._get_widget_canvas_rect(dr, stat_id)
            if not wr:
                continue

            is_sel = (stat_id == self.selected_stat_id)
            is_hov = (stat_id == self._hovered_stat_id)

            # 1. Widget Card Background (Transparent or subtle)
            if item.show_subtle_bg:
                bg_a = int(item.bg_opacity * 255)
                painter.fillRect(wr, QColor(15, 23, 42, max(50, bg_a)))
                painter.setPen(QPen(QColor(51, 65, 85, max(60, bg_a)), 1))
                painter.drawRoundedRect(wr, 4, 4)
            else:
                # Genuinely transparent mode: render light subtle outline so user sees bounds in preview
                painter.fillRect(wr, QColor(15, 23, 42, 45))
                painter.setPen(QPen(QColor(56, 189, 248, 90), 1, Qt.DashLine))
                painter.drawRoundedRect(wr, 4, 4)

            # 2. Widget Content
            font_title = QFont("Segoe UI", max(8, int(item.font_size * scale_y * 0.8)), QFont.Bold)
            painter.setFont(font_title)

            # Drop shadow for readability over live wallpaper
            if item.show_shadow:
                painter.setPen(QColor(0, 0, 0, 220))
                painter.drawText(wr.left() + 7, wr.top() + int(wr.height() * 0.38) + 1, item.name)

            painter.setPen(QColor(241, 245, 249))
            painter.drawText(wr.left() + 6, wr.top() + int(wr.height() * 0.38), item.name)

            # Telemetry Value / Sparkline Preview
            t_data = self._telemetry_cache.get(stat_id, {})
            disp_str = t_data.get("display", "--")

            if item.mode == DisplayMode.GRAPH:
                # Sparkline in preview
                accent = QColor(item.color)
                painter.setPen(QPen(accent, 1.8))
                mid = wr.top() + int(wr.height() * 0.68)
                painter.drawLine(wr.left() + 8, mid + 2, wr.left() + int(wr.width() * 0.3), mid - 8)
                painter.drawLine(wr.left() + int(wr.width() * 0.3), mid - 8, wr.left() + int(wr.width() * 0.6), mid + 6)
                painter.drawLine(wr.left() + int(wr.width() * 0.6), mid + 6, wr.right() - 8, mid - 4)

                font_val = QFont("Segoe UI", max(8, int(item.font_size * scale_y * 0.85)), QFont.Bold)
                painter.setFont(font_val)
                if item.show_shadow:
                    painter.setPen(QColor(0, 0, 0, 220))
                    painter.drawText(wr.right() - painter.fontMetrics().horizontalAdvance(disp_str) - 7, wr.top() + int(wr.height() * 0.38) + 1, disp_str)
                painter.setPen(accent)
                painter.drawText(wr.right() - painter.fontMetrics().horizontalAdvance(disp_str) - 8, wr.top() + int(wr.height() * 0.38), disp_str)
            else:
                # Numerical value
                font_val = QFont("Segoe UI", max(9, int(item.font_size * scale_y * 1.05)), QFont.Bold)
                painter.setFont(font_val)
                if item.show_shadow:
                    painter.setPen(QColor(0, 0, 0, 220))
                    painter.drawText(wr.left() + 7, wr.bottom() - 5, disp_str)
                painter.setPen(QColor(item.color))
                painter.drawText(wr.left() + 6, wr.bottom() - 6, disp_str)

            # 3. Selection Highlight & 8-Point Resize Handles
            if is_sel:
                pen_sel = QPen(QColor(56, 189, 248), 2)
                painter.setPen(pen_sel)
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(wr, 4, 4)

                # Draw 8 resize handles
                painter.setBrush(QColor(255, 255, 255))
                painter.setPen(QPen(QColor(2, 132, 199), 1.5))
                for h_rect in self._get_resize_handles(wr).values():
                    painter.drawRect(h_rect)
            elif is_hov:
                painter.setPen(QPen(QColor(56, 189, 248, 160), 1, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(wr, 4, 4)


class VisualDesktopEditor(QWidget):
    """
    Complete Visual Overlay Editor widget with Simulated Desktop Canvas,
    Top Controls Toolbar (Save, Cancel, Undo, Redo, Presets), and Right Properties Panel.
    """

    save_and_apply = Signal(OverlayConfig)
    cancelled = Signal()

    def __init__(self, config: OverlayConfig, parent=None):
        super().__init__(parent)
        # Working copy for isolated edits
        self.working_config = copy.deepcopy(config)
        self.original_config = copy.deepcopy(config)

        # Detect primary monitor resolution
        primary = QGuiApplication.primaryScreen()
        if primary:
            geo = primary.geometry()
            self.detected_res = (geo.width(), geo.height())
        else:
            self.detected_res = (1366, 768)

        # Screen capture state
        self.selected_screen = primary
        self.desktop_pixmap: Optional[QPixmap] = None

        # Gentle auto-capture timer (runs every 3.5s only while editor is visible)
        self.auto_capture_timer = QTimer(self)
        self.auto_capture_timer.setInterval(3500)
        self.auto_capture_timer.timeout.connect(self.capture_desktop)

        # Undo / Redo history stack
        self._history: List[Dict[str, Any]] = []
        self._history_idx = -1

        self._build_ui()
        self._record_history()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # --- Top Toolbar ---
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #0b111e; border: 1px solid #1e293b; border-radius: 6px; padding: 4px;")
        t_layout = QHBoxLayout(toolbar)
        t_layout.setContentsMargins(8, 4, 8, 4)
        t_layout.setSpacing(8)

        # Save & Apply (Prominent Green)
        self.btn_save = QPushButton("💾 Save & Apply")
        self.btn_save.setProperty("class", "PrimaryButton")
        self.btn_save.setStyleSheet("background-color: #059669; font-weight: bold; min-height: 28px;")
        self.btn_save.clicked.connect(self._on_save_clicked)
        t_layout.addWidget(self.btn_save)

        # Cancel Button
        self.btn_cancel = QPushButton("✕ Cancel")
        self.btn_cancel.setProperty("class", "SecondaryButton")
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        t_layout.addWidget(self.btn_cancel)

        t_layout.addSpacing(8)

        # Undo / Redo
        self.btn_undo = QPushButton("↶ Undo")
        self.btn_undo.setProperty("class", "SecondaryButton")
        self.btn_undo.clicked.connect(self._on_undo)
        t_layout.addWidget(self.btn_undo)

        self.btn_redo = QPushButton("↷ Redo")
        self.btn_redo.setProperty("class", "SecondaryButton")
        self.btn_redo.clicked.connect(self._on_redo)
        t_layout.addWidget(self.btn_redo)

        t_layout.addSpacing(8)

        # Reset Controls
        self.btn_reset_sel = QPushButton("↺ Reset Stat")
        self.btn_reset_sel.setProperty("class", "SecondaryButton")
        self.btn_reset_sel.clicked.connect(self._on_reset_selected)
        t_layout.addWidget(self.btn_reset_sel)

        self.btn_reset_all = QPushButton("↺ Reset All")
        self.btn_reset_all.setProperty("class", "SecondaryButton")
        self.btn_reset_all.clicked.connect(self._on_reset_all)
        t_layout.addWidget(self.btn_reset_all)

        t_layout.addStretch()

        # Desktop Live Capture Controls
        self.btn_refresh_preview = QPushButton("⟳ Refresh Desktop")
        self.btn_refresh_preview.setProperty("class", "SecondaryButton")
        self.btn_refresh_preview.setToolTip("Capture current live desktop and applications")
        self.btn_refresh_preview.clicked.connect(self.capture_desktop)
        t_layout.addWidget(self.btn_refresh_preview)

        self.chk_auto_capture = QCheckBox("Live Auto-Refresh")
        self.chk_auto_capture.setChecked(False)
        self.chk_auto_capture.setToolTip("Periodically re-captures desktop preview every 3.5s")
        self.chk_auto_capture.toggled.connect(self._on_auto_capture_toggled)
        t_layout.addWidget(self.chk_auto_capture)

        # Monitor Selector
        t_layout.addWidget(QLabel("Monitor:"))
        self.combo_screen = QComboBox()
        screens = QGuiApplication.screens()
        for idx, s in enumerate(screens):
            geo = s.geometry()
            tag = " (Primary)" if s == QGuiApplication.primaryScreen() else ""
            self.combo_screen.addItem(f"Display {idx + 1}{tag} ({geo.width()}×{geo.height()})", s)
        self.combo_screen.currentIndexChanged.connect(self._on_screen_changed)
        t_layout.addWidget(self.combo_screen)

        # Resolution Selector
        self.combo_res = QComboBox()
        self.combo_res.addItem(f"Native ({self.detected_res[0]}×{self.detected_res[1]})", self.detected_res)
        self.combo_res.addItem("1080p (1920×1080)", (1920, 1080))
        self.combo_res.addItem("1440p (2560×1440)", (2560, 1440))
        self.combo_res.addItem("4K UHD (3840×2160)", (3840, 2160))
        self.combo_res.addItem("WXGA (1366×768)", (1366, 768))
        self.combo_res.currentIndexChanged.connect(self._on_res_changed)
        t_layout.addWidget(self.combo_res)

        # Snapping Checkbox
        self.chk_snap = QCheckBox("Snap Edges")
        self.chk_snap.setChecked(True)
        self.chk_snap.toggled.connect(self._on_snap_toggled)
        t_layout.addWidget(self.chk_snap)

        main_layout.addWidget(toolbar)

        # --- Center: Splitter (Desktop Canvas 78% on Left, Properties 22% on Right) ---
        self.splitter = QSplitter(Qt.Horizontal)

        # Canvas
        self.canvas = SimulatedDesktopCanvas(self.working_config, screen_res=self.detected_res, parent=self)
        self.canvas.widget_selected.connect(self._on_widget_selected)
        self.canvas.geometry_modified.connect(self._on_canvas_modified)
        self.splitter.addWidget(self.canvas)

        # Properties Panel wrapped in ScrollArea to prevent clipping on small displays
        prop_panel = self._build_properties_panel()
        self.splitter.addWidget(prop_panel)
        self.splitter.setStretchFactor(0, 4)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([850, 250])

        main_layout.addWidget(self.splitter)
        self._update_undo_redo_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.capture_desktop()
        if hasattr(self, "chk_auto_capture") and self.chk_auto_capture.isChecked():
            self.auto_capture_timer.start()
        QTimer.singleShot(40, self._apply_splitter_proportions)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.auto_capture_timer.stop()

    def _apply_splitter_proportions(self):
        w = self.width()
        if w > 400:
            self.splitter.setSizes([int(w * 0.77), int(w * 0.23)])

    def capture_desktop(self):
        """Captures actual desktop background and visible applications where supported."""
        screen = self.selected_screen or QGuiApplication.primaryScreen()
        if screen:
            try:
                pix = screen.grabWindow(0)
                if not pix.isNull():
                    self.desktop_pixmap = pix
                    self.canvas.set_desktop_pixmap(pix)
                    geo = screen.geometry()
                    self.canvas.set_resolution(geo.width(), geo.height())
                    return
            except Exception as e:
                logger.warning(f"Desktop capture exception: {e}")
        self.canvas.set_desktop_pixmap(None)

    def _on_auto_capture_toggled(self, checked: bool):
        if checked:
            self.auto_capture_timer.start()
            self.capture_desktop()
        else:
            self.auto_capture_timer.stop()

    def _on_screen_changed(self):
        screen = self.combo_screen.currentData()
        if screen:
            self.selected_screen = screen
            self.capture_desktop()

    def _build_properties_panel(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background-color: transparent;")

        panel = QFrame()
        panel.setProperty("class", "ContentCard")
        panel.setMinimumWidth(230)
        p_layout = QVBoxLayout(panel)
        p_layout.setContentsMargins(10, 10, 10, 10)
        p_layout.setSpacing(8)

        p_title = QLabel("Widget Inspector")
        p_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #38bdf8;")
        p_layout.addWidget(p_title)

        self.lbl_selected_name = QLabel("Click any widget on desktop to inspect & edit")
        self.lbl_selected_name.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.lbl_selected_name.setWordWrap(True)
        p_layout.addWidget(self.lbl_selected_name)

        self.form_widget = QWidget()
        grid = QGridLayout(self.form_widget)
        grid.setContentsMargins(0, 4, 0, 4)
        grid.setSpacing(8)

        # Display Mode
        grid.addWidget(QLabel("Display Mode:"), 0, 0)
        self.combo_mode = QComboBox()
        self.combo_mode.addItem("Don't Show", DisplayMode.DONT_SHOW)
        self.combo_mode.addItem("Numbers", DisplayMode.NUMBERS)
        self.combo_mode.addItem("Graph", DisplayMode.GRAPH)
        self.combo_mode.currentIndexChanged.connect(self._on_prop_mode_changed)
        grid.addWidget(self.combo_mode, 0, 1)

        # Coordinates
        grid.addWidget(QLabel("Desktop X:"), 1, 0)
        self.spin_x = QSpinBox()
        self.spin_x.setRange(0, 7680)
        self.spin_x.valueChanged.connect(self._on_prop_geom_changed)
        grid.addWidget(self.spin_x, 1, 1)

        grid.addWidget(QLabel("Desktop Y:"), 2, 0)
        self.spin_y = QSpinBox()
        self.spin_y.setRange(0, 4320)
        self.spin_y.valueChanged.connect(self._on_prop_geom_changed)
        grid.addWidget(self.spin_y, 2, 1)

        # Dimensions
        grid.addWidget(QLabel("Width (px):"), 3, 0)
        self.spin_w = QSpinBox()
        self.spin_w.setRange(60, 800)
        self.spin_w.valueChanged.connect(self._on_prop_geom_changed)
        grid.addWidget(self.spin_w, 3, 1)

        grid.addWidget(QLabel("Height (px):"), 4, 0)
        self.spin_h = QSpinBox()
        self.spin_h.setRange(24, 400)
        self.spin_h.valueChanged.connect(self._on_prop_geom_changed)
        grid.addWidget(self.spin_h, 4, 1)

        # Typography
        grid.addWidget(QLabel("Font Size:"), 5, 0)
        self.spin_font = QSpinBox()
        self.spin_font.setRange(9, 36)
        self.spin_font.valueChanged.connect(self._on_prop_style_changed)
        grid.addWidget(self.spin_font, 5, 1)

        # Color
        grid.addWidget(QLabel("Accent Color:"), 6, 0)
        self.btn_color = QPushButton("Pick Color")
        self.btn_color.setProperty("class", "SecondaryButton")
        self.btn_color.clicked.connect(self._on_pick_color)
        grid.addWidget(self.btn_color, 6, 1)

        p_layout.addWidget(self.form_widget)

        # Quick Corner Snap Buttons
        grp_corners = QGroupBox("Corner Placement")
        grp_corners.setStyleSheet("QGroupBox { font-size: 11px; font-weight: bold; color: #94a3b8; border: 1px solid #1e293b; border-radius: 6px; margin-top: 6px; padding-top: 10px; }")
        c_grid = QGridLayout(grp_corners)
        c_grid.setSpacing(6)

        btn_tl = QPushButton("Top-Left")
        btn_tl.setProperty("class", "SecondaryButton")
        btn_tl.clicked.connect(lambda: self._snap_selected_corner(20, 20))
        c_grid.addWidget(btn_tl, 0, 0)

        btn_tr = QPushButton("Top-Right")
        btn_tr.setProperty("class", "SecondaryButton")
        btn_tr.clicked.connect(lambda: self._snap_selected_corner(self.canvas.res_w - 200, 20))
        c_grid.addWidget(btn_tr, 0, 1)

        btn_bl = QPushButton("Bottom-Left")
        btn_bl.setProperty("class", "SecondaryButton")
        btn_bl.clicked.connect(lambda: self._snap_selected_corner(20, self.canvas.res_h - 75))
        c_grid.addWidget(btn_bl, 1, 0)

        btn_br = QPushButton("Bottom-Right")
        btn_br.setProperty("class", "SecondaryButton")
        btn_br.clicked.connect(lambda: self._snap_selected_corner(self.canvas.res_w - 200, self.canvas.res_h - 75))
        c_grid.addWidget(btn_br, 1, 1)

        p_layout.addWidget(grp_corners)
        p_layout.addStretch()

        self.form_widget.setEnabled(False)
        scroll.setWidget(panel)
        return scroll
        p_layout.addStretch()

        self.form_widget.setEnabled(False)
        return panel

    def _on_widget_selected(self, stat_id: str):
        if not stat_id or stat_id not in self.working_config.stats:
            self.lbl_selected_name.setText("Click any widget on the desktop to inspect & edit")
            self.form_widget.setEnabled(False)
            self.canvas.selected_stat_id = None
            return

        self.canvas.selected_stat_id = stat_id
        item = self.working_config.stats[stat_id]
        self.lbl_selected_name.setText(f"Active: {item.name} ({item.category.capitalize()})")
        self.form_widget.setEnabled(True)

        # Sync controls without triggering signals
        self.combo_mode.blockSignals(True)
        idx = self.combo_mode.findData(item.mode)
        if idx >= 0: self.combo_mode.setCurrentIndex(idx)
        self.combo_mode.blockSignals(False)

        for spin, val in (
            (self.spin_x, item.x),
            (self.spin_y, item.y),
            (self.spin_w, item.graph_width if item.mode == DisplayMode.GRAPH else item.width),
            (self.spin_h, item.graph_height if item.mode == DisplayMode.GRAPH else item.height),
            (self.spin_font, item.font_size),
        ):
            spin.blockSignals(True)
            spin.setValue(val)
            spin.blockSignals(False)

        self.btn_color.setStyleSheet(f"background-color: {item.color}; color: #000; font-weight: bold; border-radius: 4px;")

    def _on_canvas_modified(self, stat_id: str):
        if stat_id and stat_id == self.canvas.selected_stat_id:
            item = self.working_config.stats[stat_id]
            self.spin_x.blockSignals(True)
            self.spin_y.blockSignals(True)
            self.spin_w.blockSignals(True)
            self.spin_h.blockSignals(True)
            self.spin_x.setValue(item.x)
            self.spin_y.setValue(item.y)
            w = item.graph_width if item.mode == DisplayMode.GRAPH else item.width
            h = item.graph_height if item.mode == DisplayMode.GRAPH else item.height
            self.spin_w.setValue(w)
            self.spin_h.setValue(h)
            self.spin_x.blockSignals(False)
            self.spin_y.blockSignals(False)
            self.spin_w.blockSignals(False)
            self.spin_h.blockSignals(False)
        self._record_history()

    def _on_prop_mode_changed(self):
        stat_id = self.canvas.selected_stat_id
        if not stat_id or stat_id not in self.working_config.stats: return
        item = self.working_config.stats[stat_id]
        item.mode = self.combo_mode.currentData()
        item.enabled = (item.mode != DisplayMode.DONT_SHOW)
        self.canvas.update()
        self._record_history()

    def _on_prop_geom_changed(self):
        stat_id = self.canvas.selected_stat_id
        if not stat_id or stat_id not in self.working_config.stats: return
        item = self.working_config.stats[stat_id]
        item.x = self.spin_x.value()
        item.y = self.spin_y.value()
        if item.mode == DisplayMode.GRAPH:
            item.graph_width = self.spin_w.value()
            item.graph_height = self.spin_h.value()
        else:
            item.width = self.spin_w.value()
            item.height = self.spin_h.value()
        self.canvas.update()
        self._record_history()

    def _on_prop_style_changed(self):
        stat_id = self.canvas.selected_stat_id
        if not stat_id or stat_id not in self.working_config.stats: return
        self.working_config.stats[stat_id].font_size = self.spin_font.value()
        self.canvas.update()

    def _on_pick_color(self):
        stat_id = self.canvas.selected_stat_id
        if not stat_id or stat_id not in self.working_config.stats: return
        item = self.working_config.stats[stat_id]
        c = QColorDialog.getColor(QColor(item.color), self, f"Select Accent Color for {item.name}")
        if c.isValid():
            item.color = c.name()
            self.btn_color.setStyleSheet(f"background-color: {item.color}; color: #000; font-weight: bold; border-radius: 4px;")
            self.canvas.update()
            self._record_history()

    def _snap_selected_corner(self, x: int, y: int):
        stat_id = self.canvas.selected_stat_id
        if not stat_id or stat_id not in self.working_config.stats: return
        item = self.working_config.stats[stat_id]
        item.x = max(0, x)
        item.y = max(0, y)
        self.spin_x.setValue(item.x)
        self.spin_y.setValue(item.y)
        self.canvas.update()
        self._record_history()

    def _on_res_changed(self):
        data = self.combo_res.currentData()
        if data and isinstance(data, tuple):
            self.canvas.set_resolution(data[0], data[1])

    def _on_snap_toggled(self, checked: bool):
        self.canvas.snap_to_edges = checked

    # --- History & Undo / Redo ---

    def _record_history(self):
        state = copy.deepcopy(self.working_config.to_dict())
        if self._history_idx < len(self._history) - 1:
            self._history = self._history[:self._history_idx + 1]
        self._history.append(state)
        self._history_idx = len(self._history) - 1
        if len(self._history) > 25:
            self._history.pop(0)
            self._history_idx -= 1
        self._update_undo_redo_ui()

    def _on_undo(self):
        if self._history_idx > 0:
            self._history_idx -= 1
            self.working_config = OverlayConfig.from_dict(self._history[self._history_idx])
            self.canvas.set_config(self.working_config)
            if self.canvas.selected_stat_id:
                self._on_widget_selected(self.canvas.selected_stat_id)
            self._update_undo_redo_ui()

    def _on_redo(self):
        if self._history_idx < len(self._history) - 1:
            self._history_idx += 1
            self.working_config = OverlayConfig.from_dict(self._history[self._history_idx])
            self.canvas.set_config(self.working_config)
            if self.canvas.selected_stat_id:
                self._on_widget_selected(self.canvas.selected_stat_id)
            self._update_undo_redo_ui()

    def _update_undo_redo_ui(self):
        self.btn_undo.setEnabled(self._history_idx > 0)
        self.btn_redo.setEnabled(self._history_idx < len(self._history) - 1)

    def _on_reset_selected(self):
        stat_id = self.canvas.selected_stat_id
        if not stat_id: return
        catalog = get_default_stats_catalog()
        if stat_id in catalog and stat_id in self.working_config.stats:
            def_item = catalog[stat_id]
            item = self.working_config.stats[stat_id]
            item.x = def_item.x
            item.y = def_item.y
            item.width = def_item.width
            item.height = def_item.height
            item.graph_width = def_item.graph_width
            item.graph_height = def_item.graph_height
            self._on_widget_selected(stat_id)
            self.canvas.update()
            self._record_history()

    def _on_reset_all(self):
        catalog = get_default_stats_catalog()
        for stat_id, def_item in catalog.items():
            if stat_id in self.working_config.stats:
                item = self.working_config.stats[stat_id]
                item.x = def_item.x
                item.y = def_item.y
        if self.canvas.selected_stat_id:
            self._on_widget_selected(self.canvas.selected_stat_id)
        self.canvas.update()
        self._record_history()

    # --- Save & Cancel Actions ---

    def _on_save_clicked(self):
        self.save_and_apply.emit(self.working_config)

    def _on_cancel_clicked(self):
        self.cancelled.emit()

    def update_telemetry(self, snapshot: Dict[str, Any]):
        self.canvas.update_live_telemetry(snapshot)
