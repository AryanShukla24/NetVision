"""
NetVision - Real Desktop Overlay Drag-and-Drop Visual Editor
Provides an interactive canvas over the user's authentic Windows desktop wallpaper
and visible windows. Supports 8-point resizing, edge snapping, dynamic alignment
guides, multi-monitor geometry, zoom controls, undo/redo history, and real-time
bidirectional inspector synchronization.
"""

from typing import Dict, Any, Optional, Tuple, List
import copy
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSpinBox, QSlider, QCheckBox, QComboBox,
    QScrollArea, QSplitter, QColorDialog, QTableWidget, QTableWidgetItem,
    QStackedWidget, QButtonGroup
)
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPixmap, QMouseEvent,
    QGuiApplication, QKeySequence, QShortcut
)

from netvision.config import COLORS
from netvision.core.overlay_config import (
    OverlayConfig, DisplayMode, StatItemConfig, get_default_stats_catalog
)
from netvision.ui.components.icons import get_icon
from netvision.ui.overlay.desktop_capture import (
    capture_desktop_preview, get_available_monitors
)

logger = logging.getLogger(__name__)

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


class InteractiveDesktopCanvas(QWidget):
    """
    Renders the user's authentic desktop wallpaper / live screen capture with
    scaled overlay widgets. Supports selection, dragging, 8-point resizing,
    edge snapping, alignment guidelines, and zoom factor scaling.
    """

    widget_selected = Signal(str)
    geometry_modified = Signal(str)

    def __init__(self, config: OverlayConfig, screen_res: Tuple[int, int] = (1366, 768), parent=None):
        super().__init__(parent)
        self.config = config
        self.res_w, self.res_h = screen_res
        self.snap_to_edges = True
        self.show_guides = True
        self.zoom_factor = 1.0  # 1.0 = Fit to window; > 1.0 = zoomed

        self.selected_stat_id: Optional[str] = None
        self._hovered_stat_id: Optional[str] = None

        # Drag & resize state
        self._active_handle = HANDLE_NONE
        self._is_dragging = False
        self._drag_start_screen = QPoint()
        self._orig_widget_rect = QRect()  # In desktop coordinates

        # Alignment guides: list of (is_vertical: bool, desktop_coord: int)
        self._active_guides: List[Tuple[bool, int]] = []

        # Real desktop background capture pixmap
        self.desktop_pixmap: Optional[QPixmap] = None
        self.capture_status = "Resolving desktop..."

        # Live telemetry preview cache
        self._telemetry_cache: Dict[str, Any] = {
            "fps": {"display": "60 FPS", "val": 60.0},
            "cpu": {"display": "18.4%", "val": 18.4},
            "gpu": {"display": "24.1%", "val": 24.1},
            "ram": {"display": "6.2 GB", "val": 6.2},
            "net_io": {"display": "4.8 MB/s", "val": 4.8},
            "wifi_signal": {"display": "84%", "val": 84.0},
            "ping": {"display": "14 ms", "val": 14.0},
            "jitter": {"display": "1.8 ms", "val": 1.8},
            "packet_loss": {"display": "0.0%", "val": 0.0},
            "download_speed": {"display": "94.2 Mbps", "val": 94.2},
            "upload_speed": {"display": "42.0 Mbps", "val": 42.0},
        }

        self.setMouseTracking(True)
        self.setMinimumSize(480, 280)
        self.setFocusPolicy(Qt.StrongFocus)

    def set_config(self, config: OverlayConfig):
        self.config = config
        self.update()

    def set_desktop_pixmap(self, pixmap: Optional[QPixmap], status_desc: str = ""):
        self.desktop_pixmap = pixmap
        self.capture_status = status_desc or "Live Desktop"
        self.update()

    def set_resolution(self, res_w: int, res_h: int):
        self.res_w = max(640, res_w)
        self.res_h = max(480, res_h)
        self.update()

    def set_zoom(self, factor: float):
        self.zoom_factor = max(0.4, min(2.5, factor))
        self.update()

    def get_desktop_rect(self) -> QRect:
        """Calculates centered, aspect-ratio-preserved desktop preview bounds."""
        cw, ch = self.width(), self.height()
        pad = 8
        avail_w = max(100, cw - (pad * 2))
        avail_h = max(100, ch - (pad * 2))

        aspect = self.res_w / self.res_h
        if (avail_w / avail_h) > aspect:
            h = int(avail_h * self.zoom_factor)
            w = int(h * aspect)
        else:
            w = int(avail_w * self.zoom_factor)
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

    def _cursor_for_handle(self, handle_id: int) -> Qt.CursorShape:
        if handle_id in (HANDLE_TL, HANDLE_BR):
            return Qt.SizeFDiagCursor
        if handle_id in (HANDLE_TR, HANDLE_BL):
            return Qt.SizeBDiagCursor
        if handle_id in (HANDLE_T, HANDLE_B):
            return Qt.SizeVerCursor
        if handle_id in (HANDLE_L, HANDLE_R):
            return Qt.SizeHorCursor
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

        # 2. Check if clicking directly on any widget to select or drag
        clicked_stat_id = None
        for stat_id, item in reversed(list(self.config.stats.items())):
            if item.mode == DisplayMode.DONT_SHOW:
                continue
            r = self._get_widget_canvas_rect(dr, stat_id)
            if r and r.contains(pos):
                clicked_stat_id = stat_id
                break

        if clicked_stat_id:
            self.selected_stat_id = clicked_stat_id
            self.widget_selected.emit(clicked_stat_id)
            item = self.config.stats[clicked_stat_id]

            if not item.is_locked:
                self._is_dragging = True
                self._drag_start_screen = pos
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

        # Hover state and cursor update
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

        # 1. Dragging widget
        if self._is_dragging and self.selected_stat_id:
            item = self.config.stats[self.selected_stat_id]
            dx = int((pos.x() - self._drag_start_screen.x()) / scale_x)
            dy = int((pos.y() - self._drag_start_screen.y()) / scale_y)

            new_x = self._orig_widget_rect.x() + dx
            new_y = self._orig_widget_rect.y() + dy

            # Snap to desktop edges & alignment guides
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
            min_w, min_h = 80, 28

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

    def keyPressEvent(self, event):
        """Keyboard nudging: Arrow keys (1px), Shift+Arrow (10px)."""
        if not self.selected_stat_id:
            super().keyPressEvent(event)
            return

        item = self.config.stats.get(self.selected_stat_id)
        if not item or item.is_locked:
            super().keyPressEvent(event)
            return

        step = 10 if (event.modifiers() & Qt.ShiftModifier) else 1
        key = event.key()

        if key == Qt.Key_Left:
            item.x = max(0, item.x - step)
        elif key == Qt.Key_Right:
            item.x = min(self.res_w - 40, item.x + step)
        elif key == Qt.Key_Up:
            item.y = max(0, item.y - step)
        elif key == Qt.Key_Down:
            item.y = min(self.res_h - 20, item.y + step)
        elif key == Qt.Key_Delete:
            item.mode = DisplayMode.DONT_SHOW
            item.enabled = False
        else:
            super().keyPressEvent(event)
            return

        self.geometry_modified.emit(self.selected_stat_id)
        self.update()
        event.accept()

    def _apply_desktop_snapping(self, moving_id: str, x: int, y: int, w: int, h: int) -> Tuple[int, int]:
        """Snaps to screen borders and aligns with other widgets."""
        self._active_guides.clear()
        snap_thresh = 14

        # Desktop Edge Snapping
        if self.snap_to_edges:
            if abs(x - 20) <= snap_thresh:
                x = 20
                self._active_guides.append((True, 20))
            if abs((x + w) - (self.res_w - 20)) <= snap_thresh:
                x = self.res_w - 20 - w
                self._active_guides.append((True, self.res_w - 20))

            if abs(y - 20) <= snap_thresh:
                y = 20
                self._active_guides.append((False, 20))
            if abs((y + h) - (self.res_h - 20)) <= snap_thresh:
                y = self.res_h - 20 - h
                self._active_guides.append((False, self.res_h - 20))

        # Alignment Guides with other widgets
        if self.show_guides:
            for s_id, o in self.config.stats.items():
                if s_id == moving_id or o.mode == DisplayMode.DONT_SHOW:
                    continue
                ow = o.graph_width if o.mode == DisplayMode.GRAPH else o.width
                oh = o.graph_height if o.mode == DisplayMode.GRAPH else o.height

                # Vertical alignments
                if abs(x - o.x) <= snap_thresh:
                    x = o.x
                    self._active_guides.append((True, x))
                elif abs((x + w) - (o.x + ow)) <= snap_thresh:
                    x = o.x + ow - w
                    self._active_guides.append((True, o.x + ow))

                # Horizontal alignments
                if abs(y - o.y) <= snap_thresh:
                    y = o.y
                    self._active_guides.append((False, y))
                elif abs((y + h) - (o.y + oh)) <= snap_thresh:
                    y = o.y + oh - h
                    self._active_guides.append((False, o.y + oh))

        return max(0, min(self.res_w - w, x)), max(0, min(self.res_h - h, y))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        cw, ch = self.width(), self.height()
        painter.fillRect(0, 0, cw, ch, QColor(16, 21, 28))

        dr = self.get_desktop_rect()

        # 1. Draw Real Desktop Wallpaper / Screen Capture
        if self.desktop_pixmap and not self.desktop_pixmap.isNull():
            painter.drawPixmap(dr, self.desktop_pixmap)
            # Subtle dark glass wash to enhance widget readability during placement
            painter.fillRect(dr, QColor(0, 0, 0, 35))
            pen_border = QPen(QColor(COLORS["primary"]), 2)
            painter.setPen(pen_border)
            painter.drawRect(dr)

            # Live watermark badge
            font_badge = QFont("Segoe UI", 9, QFont.Bold)
            painter.setFont(font_badge)
            painter.setPen(QColor(COLORS["success"]))
            badge_text = f"● {self.capture_status} ({self.res_w} × {self.res_h})"
            painter.drawText(dr.right() - painter.fontMetrics().horizontalAdvance(badge_text) - 12, dr.bottom() - 12, badge_text)
        else:
            painter.fillRect(dr, QColor(21, 29, 39))
            pen_border = QPen(QColor(COLORS["border_light"]), 1.5)
            painter.setPen(pen_border)
            painter.drawRect(dr)

        # 2. Draw Dynamic Alignment Guides (Red / Cyan dashed lines)
        scale_x = dr.width() / self.res_w
        scale_y = dr.height() / self.res_h

        if self._active_guides:
            guide_pen = QPen(QColor(COLORS["danger"]), 1, Qt.DashLine)
            painter.setPen(guide_pen)
            for is_vert, d_coord in self._active_guides:
                if is_vert:
                    cx = dr.x() + int(d_coord * scale_x)
                    painter.drawLine(cx, dr.top(), cx, dr.bottom())
                else:
                    cy = dr.y() + int(d_coord * scale_y)
                    painter.drawLine(dr.left(), cy, dr.right(), cy)

        # 3. Draw All Enabled Statistic Widgets
        for stat_id, item in self.config.stats.items():
            if item.mode == DisplayMode.DONT_SHOW:
                continue

            wr = self._get_widget_canvas_rect(dr, stat_id)
            if not wr:
                continue

            is_sel = (stat_id == self.selected_stat_id)
            is_hov = (stat_id == self._hovered_stat_id)

            # Card Background
            if item.show_subtle_bg:
                bg_a = int(item.bg_opacity * 255)
                painter.fillRect(wr, QColor(16, 21, 28, max(50, bg_a)))
                painter.setPen(QPen(QColor(30, 42, 56, max(60, bg_a)), 1))
                painter.drawRoundedRect(wr, 4, 4)
            else:
                painter.fillRect(wr, QColor(16, 21, 28, 45))
                painter.setPen(QPen(QColor(34, 184, 207, 80), 1, Qt.DashLine))
                painter.drawRoundedRect(wr, 4, 4)

            # Widget Title
            font_title = QFont("Segoe UI", max(8, int(item.font_size * scale_y * 0.8)), QFont.Bold)
            painter.setFont(font_title)
            if item.show_shadow:
                painter.setPen(QColor(0, 0, 0, 220))
                painter.drawText(wr.left() + 7, wr.top() + int(wr.height() * 0.38) + 1, item.name)

            painter.setPen(QColor(COLORS["text_bright"]))
            painter.drawText(wr.left() + 6, wr.top() + int(wr.height() * 0.38), item.name)

            # Telemetry Value / Sparkline Preview
            t_data = self._telemetry_cache.get(stat_id, {})
            disp_str = t_data.get("display", "--")

            if item.mode == DisplayMode.GRAPH:
                accent = QColor(item.color)
                painter.setPen(QPen(accent, 1.8))
                mid = wr.top() + int(wr.height() * 0.68)
                painter.drawLine(wr.left() + 8, mid + 2, wr.left() + int(wr.width() * 0.3), mid - 8)
                painter.drawLine(wr.left() + int(wr.width() * 0.3), mid - 8, wr.left() + int(wr.width() * 0.6), mid + 6)
                painter.drawLine(wr.left() + int(wr.width() * 0.6), mid + 6, wr.right() - 8, mid - 4)

                font_val = QFont("Consolas", max(8, int(item.font_size * scale_y * 0.85)), QFont.Bold)
                painter.setFont(font_val)
                if item.show_shadow:
                    painter.setPen(QColor(0, 0, 0, 220))
                    painter.drawText(wr.right() - painter.fontMetrics().horizontalAdvance(disp_str) - 7, wr.top() + int(wr.height() * 0.38) + 1, disp_str)
                painter.setPen(accent)
                painter.drawText(wr.right() - painter.fontMetrics().horizontalAdvance(disp_str) - 8, wr.top() + int(wr.height() * 0.38), disp_str)
            else:
                font_val = QFont("Consolas", max(9, int(item.font_size * scale_y * 1.05)), QFont.Bold)
                painter.setFont(font_val)
                if item.show_shadow:
                    painter.setPen(QColor(0, 0, 0, 220))
                    painter.drawText(wr.left() + 7, wr.bottom() - 5, disp_str)
                painter.setPen(QColor(item.color))
                painter.drawText(wr.left() + 6, wr.bottom() - 6, disp_str)

            # 4. Selection Highlight & 8-Point Resize Handles
            if is_sel:
                pen_sel = QPen(QColor(COLORS["primary"]), 2)
                painter.setPen(pen_sel)
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(wr, 4, 4)

                painter.setBrush(QColor(255, 255, 255))
                painter.setPen(QPen(QColor(COLORS["primary_dark"]), 1.5))
                for h_rect in self._get_resize_handles(wr).values():
                    painter.drawRect(h_rect)
            elif is_hov:
                painter.setPen(QPen(QColor(COLORS["primary"]), 1, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(wr, 4, 4)


class VisualDesktopEditor(QWidget):
    """
    World-class Drag-and-Drop Visual Overlay Editor.
    Features:
    - Real Windows desktop preview (authentic wallpaper and live windows)
    - 8-point interactive resize handles and drag-and-drop
    - Edge snapping and alignment guidelines
    - Undo/Redo history stack
    - Inspector properties panel with live bidirectional synchronization
    - Integrated coordinates table view toggle
    - Multi-monitor detection and resolution switching
    """

    save_and_apply = Signal(OverlayConfig)
    cancelled = Signal()

    def __init__(self, config: OverlayConfig, parent=None):
        super().__init__(parent)
        self.working_config = copy.deepcopy(config)
        self.original_config = copy.deepcopy(config)

        # Detect primary monitor resolution
        primary = QGuiApplication.primaryScreen()
        if primary:
            geo = primary.geometry()
            self.detected_res = (geo.width(), geo.height())
        else:
            self.detected_res = (1366, 768)

        self.current_screen_idx = 0
        self.desktop_pixmap: Optional[QPixmap] = None

        # Undo / Redo history stack
        self._history: List[Dict[str, Any]] = []
        self._history_idx = -1

        self._build_ui()
        self._record_history()
        self.capture_desktop()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # --- Top Toolbar ---
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background-color: {COLORS['bg_surface']}; border: 1px solid {COLORS['border']}; border-radius: 4px; padding: 2px;")
        t_layout = QHBoxLayout(toolbar)
        t_layout.setContentsMargins(6, 4, 6, 4)
        t_layout.setSpacing(6)

        # Save & Apply
        self.btn_save = QPushButton("Save & Apply")
        self.btn_save.setIcon(get_icon("save", 16, "#10151C", "#10151C"))
        self.btn_save.setProperty("class", "PrimaryButton")
        self.btn_save.clicked.connect(self._on_save_clicked)
        t_layout.addWidget(self.btn_save)

        # Cancel
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setIcon(get_icon("cancel", 16))
        self.btn_cancel.setProperty("class", "SecondaryButton")
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        t_layout.addWidget(self.btn_cancel)

        t_layout.addSpacing(6)

        # Undo / Redo
        self.btn_undo = QPushButton("Undo")
        self.btn_undo.setIcon(get_icon("undo", 16))
        self.btn_undo.setProperty("class", "SecondaryButton")
        self.btn_undo.clicked.connect(self._on_undo)
        t_layout.addWidget(self.btn_undo)

        self.btn_redo = QPushButton("Redo")
        self.btn_redo.setIcon(get_icon("redo", 16))
        self.btn_redo.setProperty("class", "SecondaryButton")
        self.btn_redo.clicked.connect(self._on_redo)
        t_layout.addWidget(self.btn_redo)

        t_layout.addSpacing(6)

        # Reset Controls
        self.btn_reset_sel = QPushButton("Reset Stat")
        self.btn_reset_sel.setProperty("class", "SecondaryButton")
        self.btn_reset_sel.clicked.connect(self._on_reset_selected)
        t_layout.addWidget(self.btn_reset_sel)

        self.btn_reset_all = QPushButton("Reset All")
        self.btn_reset_all.setProperty("class", "SecondaryButton")
        self.btn_reset_all.clicked.connect(self._on_reset_all)
        t_layout.addWidget(self.btn_reset_all)

        t_layout.addStretch()

        # Desktop Wallpaper & Window Capture Controls
        self.btn_refresh_preview = QPushButton("Refresh Desktop")
        self.btn_refresh_preview.setIcon(get_icon("refresh", 16))
        self.btn_refresh_preview.setProperty("class", "SecondaryButton")
        self.btn_refresh_preview.setToolTip("Captures current Windows wallpaper and visible applications")
        self.btn_refresh_preview.clicked.connect(self.capture_desktop)
        t_layout.addWidget(self.btn_refresh_preview)

        # Zoom Controls
        btn_zoom_out = QPushButton()
        btn_zoom_out.setIcon(get_icon("zoom_out", 16))
        btn_zoom_out.setToolTip("Zoom Out")
        btn_zoom_out.setProperty("class", "SecondaryButton")
        btn_zoom_out.clicked.connect(lambda: self.canvas.set_zoom(self.canvas.zoom_factor - 0.15))
        t_layout.addWidget(btn_zoom_out)

        btn_zoom_fit = QPushButton()
        btn_zoom_fit.setIcon(get_icon("zoom_fit", 16))
        btn_zoom_fit.setToolTip("Fit to Window")
        btn_zoom_fit.setProperty("class", "SecondaryButton")
        btn_zoom_fit.clicked.connect(lambda: self.canvas.set_zoom(1.0))
        t_layout.addWidget(btn_zoom_fit)

        btn_zoom_in = QPushButton()
        btn_zoom_in.setIcon(get_icon("zoom_in", 16))
        btn_zoom_in.setToolTip("Zoom In")
        btn_zoom_in.setProperty("class", "SecondaryButton")
        btn_zoom_in.clicked.connect(lambda: self.canvas.set_zoom(self.canvas.zoom_factor + 0.15))
        t_layout.addWidget(btn_zoom_in)

        # View Switcher (Canvas vs Table)
        self.btn_toggle_view = QPushButton("Table View")
        self.btn_toggle_view.setIcon(get_icon("table", 16))
        self.btn_toggle_view.setProperty("class", "SecondaryButton")
        self.btn_toggle_view.setCheckable(True)
        self.btn_toggle_view.clicked.connect(self._toggle_view_mode)
        t_layout.addWidget(self.btn_toggle_view)

        t_layout.addSpacing(6)

        # Monitor Selector
        lbl_mon = QLabel("Monitor:")
        lbl_mon.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        t_layout.addWidget(lbl_mon)

        self.combo_screen = QComboBox()
        self._populate_monitors()
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

        # Snapping Checkboxes
        self.chk_snap = QCheckBox("Snap")
        self.chk_snap.setChecked(True)
        self.chk_snap.toggled.connect(lambda chk: setattr(self.canvas, "snap_to_edges", chk))
        t_layout.addWidget(self.chk_snap)

        self.chk_guides = QCheckBox("Guides")
        self.chk_guides.setChecked(True)
        self.chk_guides.toggled.connect(lambda chk: setattr(self.canvas, "show_guides", chk))
        t_layout.addWidget(self.chk_guides)

        main_layout.addWidget(toolbar)

        # --- Main Workspace Stack: View 0 = Splitter (Canvas + Inspector), View 1 = Coordinates Table ---
        self.view_stack = QStackedWidget()

        # View 0: Interactive Canvas + Properties Panel
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {COLORS['border']}; width: 2px; }}")

        self.canvas = InteractiveDesktopCanvas(self.working_config, self.detected_res, self)
        self.canvas.widget_selected.connect(self._on_widget_selected)
        self.canvas.geometry_modified.connect(self._on_geometry_modified)
        self.splitter.addWidget(self.canvas)

        self.prop_panel = self._build_properties_panel()
        self.splitter.addWidget(self.prop_panel)
        self.view_stack.addWidget(self.splitter)

        # View 1: Coordinates Reference Table
        self.table_view_widget = self._build_table_view()
        self.view_stack.addWidget(self.table_view_widget)

        main_layout.addWidget(self.view_stack)

        # Pre-populate table
        self._sync_table_from_config()

        # Apply 78% Canvas / 22% Inspector ratio
        QTimer.singleShot(50, self._apply_splitter_proportions)

        # Shortcuts
        QShortcut(QKeySequence.Undo, self, self._on_undo)
        QShortcut(QKeySequence.Redo, self, self._on_redo)

    def _populate_monitors(self):
        self.combo_screen.clear()
        monitors = get_available_monitors()
        for mon in monitors:
            self.combo_screen.addItem(mon["label"], mon["index"])

    def _apply_splitter_proportions(self):
        w = self.width()
        if w > 400:
            self.splitter.setSizes([int(w * 0.77), int(w * 0.23)])

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_splitter_proportions()

    def capture_desktop(self):
        """Captures the user's authentic desktop wallpaper and open windows."""
        screen_idx = self.combo_screen.currentData() or 0
        target_res = self.combo_res.currentData() or self.detected_res

        # Pass parent window to prevent recursive capture loop
        top_window = self.window() if self.isVisible() else None
        pix, desc = capture_desktop_preview(screen_idx, target_res, exclude_widget=top_window)

        if pix and not pix.isNull():
            self.desktop_pixmap = pix
            self.canvas.set_desktop_pixmap(pix, desc)
            self.canvas.set_resolution(target_res[0], target_res[1])
        else:
            self.canvas.set_desktop_pixmap(None, "Canvas Grid")

    def _on_screen_changed(self):
        self.current_screen_idx = self.combo_screen.currentData() or 0
        screens = QGuiApplication.screens()
        if 0 <= self.current_screen_idx < len(screens):
            geo = screens[self.current_screen_idx].geometry()
            self.detected_res = (geo.width(), geo.height())
            self.canvas.set_resolution(geo.width(), geo.height())
        self.capture_desktop()

    def _on_res_changed(self):
        res = self.combo_res.currentData()
        if res:
            self.canvas.set_resolution(res[0], res[1])

    def _toggle_view_mode(self, checked: bool):
        if checked:
            self.btn_toggle_view.setText("Canvas View")
            self.btn_toggle_view.setIcon(get_icon("monitor", 16))
            self._sync_table_from_config()
            self.view_stack.setCurrentIndex(1)
        else:
            self.btn_toggle_view.setText("Table View")
            self.btn_toggle_view.setIcon(get_icon("table", 16))
            self.view_stack.setCurrentIndex(0)

    # --- Inspector Panel ---

    def _build_properties_panel(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background-color: {COLORS['bg_surface']}; border-left: 1px solid {COLORS['border']};")

        panel = QWidget()
        panel.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # Header Badge
        self.lbl_prop_title = QLabel("Widget Inspector")
        self.lbl_prop_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {COLORS['primary']};")
        layout.addWidget(self.lbl_prop_title)

        self.lbl_selected_name = QLabel("Active: None")
        self.lbl_selected_name.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {COLORS['text_bright']};")
        layout.addWidget(self.lbl_selected_name)

        self.lbl_prop_desc = QLabel("Select any statistic on the canvas to configure.")
        self.lbl_prop_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        layout.addWidget(self.lbl_prop_desc)

        # Form Container for enable/disable state
        self.form_widget = QWidget()
        form_layout = QVBoxLayout(self.form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(8)

        # Position Group
        grp_pos = QFrame()
        grp_pos.setStyleSheet(f"background-color: {COLORS['bg_elevated']}; border: 1px solid {COLORS['border']}; border-radius: 4px; padding: 6px;")
        g_pos = QGridLayout(grp_pos)
        g_pos.setSpacing(6)

        g_pos.addWidget(QLabel("Position X:"), 0, 0)
        self.spin_x = QSpinBox()
        self.spin_x.setRange(0, 7680)
        self.spin_x.valueChanged.connect(self._on_prop_coord_changed)
        g_pos.addWidget(self.spin_x, 0, 1)

        g_pos.addWidget(QLabel("Position Y:"), 1, 0)
        self.spin_y = QSpinBox()
        self.spin_y.setRange(0, 4320)
        self.spin_y.valueChanged.connect(self._on_prop_coord_changed)
        g_pos.addWidget(self.spin_y, 1, 1)

        g_pos.addWidget(QLabel("Width:"), 2, 0)
        self.spin_w = QSpinBox()
        self.spin_w.setRange(80, 1920)
        self.spin_w.valueChanged.connect(self._on_prop_size_changed)
        g_pos.addWidget(self.spin_w, 2, 1)

        g_pos.addWidget(QLabel("Height:"), 3, 0)
        self.spin_h = QSpinBox()
        self.spin_h.setRange(28, 1080)
        self.spin_h.valueChanged.connect(self._on_prop_size_changed)
        g_pos.addWidget(self.spin_h, 3, 1)

        form_layout.addWidget(grp_pos)

        # Styling Group
        grp_style = QFrame()
        grp_style.setStyleSheet(f"background-color: {COLORS['bg_elevated']}; border: 1px solid {COLORS['border']}; border-radius: 4px; padding: 6px;")
        g_style = QGridLayout(grp_style)
        g_style.setSpacing(6)

        g_style.addWidget(QLabel("Font Size:"), 0, 0)
        self.spin_font = QSpinBox()
        self.spin_font.setRange(8, 48)
        self.spin_font.valueChanged.connect(self._on_prop_font_changed)
        g_style.addWidget(self.spin_font, 0, 1)

        g_style.addWidget(QLabel("Mode:"), 1, 0)
        self.combo_mode = QComboBox()
        self.combo_mode.addItem("Don't Show", DisplayMode.DONT_SHOW)
        self.combo_mode.addItem("Numbers", DisplayMode.NUMBERS)
        self.combo_mode.addItem("Graph", DisplayMode.GRAPH)
        self.combo_mode.currentIndexChanged.connect(self._on_prop_mode_changed)
        g_style.addWidget(self.combo_mode, 1, 1)

        g_style.addWidget(QLabel("Accent Color:"), 2, 0)
        self.btn_color = QPushButton("Pick Color")
        self.btn_color.setProperty("class", "SecondaryButton")
        self.btn_color.clicked.connect(self._on_pick_color)
        g_style.addWidget(self.btn_color, 2, 1)

        g_style.addWidget(QLabel("Opacity:"), 3, 0)
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(10, 100)
        self.slider_opacity.valueChanged.connect(self._on_prop_opacity_changed)
        g_style.addWidget(self.slider_opacity, 3, 1)

        self.chk_subtle_bg = QCheckBox("Subtle Background")
        self.chk_subtle_bg.toggled.connect(self._on_prop_bg_toggled)
        g_style.addWidget(self.chk_subtle_bg, 4, 0, 1, 2)

        self.chk_lock = QCheckBox("Lock Position")
        self.chk_lock.toggled.connect(self._on_prop_lock_toggled)
        g_style.addWidget(self.chk_lock, 5, 0, 1, 2)

        form_layout.addWidget(grp_style)

        # Quick Alignment Tools
        lbl_align = QLabel("Alignment & Snapping Tools")
        lbl_align.setStyleSheet(f"font-weight: 700; color: {COLORS['text_primary']}; font-size: 11px;")
        form_layout.addWidget(lbl_align)

        grp_align = QFrame()
        grp_align.setStyleSheet(f"background-color: {COLORS['bg_elevated']}; border: 1px solid {COLORS['border']}; border-radius: 4px; padding: 4px;")
        g_align = QGridLayout(grp_align)
        g_align.setSpacing(4)

        for label, icon_name, func, r, c in [
            ("Left", "align_left", self._align_left, 0, 0),
            ("Center", "align_center", self._align_center, 0, 1),
            ("Right", "align_right", self._align_right, 0, 2),
            ("Top", "align_top", self._align_top, 1, 0),
            ("Middle", "align_center", self._align_middle, 1, 1),
            ("Bottom", "align_bottom", self._align_bottom, 1, 2),
        ]:
            b = QPushButton(label)
            b.setIcon(get_icon(icon_name, 14))
            b.setProperty("class", "SecondaryButton")
            b.clicked.connect(func)
            g_align.addWidget(b, r, c)

        form_layout.addWidget(grp_align)

        # Quick Corner Snaps
        grp_corners = QFrame()
        grp_corners.setStyleSheet(f"background-color: {COLORS['bg_elevated']}; border: 1px solid {COLORS['border']}; border-radius: 4px; padding: 4px;")
        g_cor = QGridLayout(grp_corners)
        g_cor.setSpacing(4)

        for label, corner, r, c in [
            ("Top-Left", "tl", 0, 0),
            ("Top-Right", "tr", 0, 1),
            ("Bottom-Left", "bl", 1, 0),
            ("Bottom-Right", "br", 1, 1),
        ]:
            b = QPushButton(label)
            b.setProperty("class", "SecondaryButton")
            b.clicked.connect(lambda _, cor=corner: self._snap_selected_to_corner(cor))
            g_cor.addWidget(b, r, c)

        form_layout.addWidget(grp_corners)
        layout.addWidget(self.form_widget)
        self.form_widget.setEnabled(False)
        layout.addStretch()

        scroll.setWidget(panel)
        return scroll

    # --- Coordinates Table View ---

    def _build_table_view(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        card = QFrame()
        card.setProperty("class", "ContentCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(12, 10, 12, 10)
        c_layout.setSpacing(8)

        t_lbl = QLabel("Precise Coordinates Table (All 11 Statistics)")
        t_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {COLORS['primary']};")
        c_layout.addWidget(t_lbl)

        self.table_pos = QTableWidget()
        self.table_pos.setColumnCount(6)
        self.table_pos.setHorizontalHeaderLabels([
            "Statistic", "X Coordinate", "Y Coordinate", "Quick Snap Corner", "Reset Position", "Lock"
        ])
        self.table_pos.verticalHeader().setVisible(False)
        self.table_pos.verticalHeader().setDefaultSectionSize(44)
        self.table_pos.setShowGrid(True)
        self.table_pos.setMinimumHeight(520)
        self.table_pos.horizontalHeader().setStretchLastSection(True)

        c_layout.addWidget(self.table_pos)
        layout.addWidget(card)
        return container

    def _sync_table_from_config(self):
        self.table_pos.setRowCount(0)
        for row, (stat_id, item) in enumerate(self.working_config.stats.items()):
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
            spin_x.valueChanged.connect(lambda v, s=stat_id: self._on_table_coord_changed(s, x=v))
            self.table_pos.setCellWidget(row, 1, self._wrap_widget(spin_x))

            # 2: Y Coordinate
            spin_y = QSpinBox()
            spin_y.setRange(0, 4320)
            spin_y.setValue(item.y)
            spin_y.valueChanged.connect(lambda v, s=stat_id: self._on_table_coord_changed(s, y=v))
            self.table_pos.setCellWidget(row, 2, self._wrap_widget(spin_y))

            # 3: Snap Corner
            combo = QComboBox()
            combo.addItem("Snap Corner...", "")
            combo.addItem("Top-Left", (24, 24))
            combo.addItem("Top-Right", (1180, 24))
            combo.addItem("Bottom-Left", (24, 700))
            combo.addItem("Bottom-Right", (1180, 700))
            combo.currentIndexChanged.connect(lambda idx, s=stat_id, c=combo, sx=spin_x, sy=spin_y: self._on_table_snap_corner(s, c, sx, sy))
            self.table_pos.setCellWidget(row, 3, self._wrap_widget(combo))

            # 4: Reset
            btn_res = QPushButton("Reset Pos")
            btn_res.setProperty("class", "SecondaryButton")
            btn_res.clicked.connect(lambda _, s=stat_id, sx=spin_x, sy=spin_y: self._on_table_reset_single(s, sx, sy))
            self.table_pos.setCellWidget(row, 4, self._wrap_widget(btn_res))

            # 5: Lock
            chk = QCheckBox("Lock")
            chk.setChecked(item.is_locked)
            chk.toggled.connect(lambda c, s=stat_id: self._on_table_lock_toggled(s, c))
            self.table_pos.setCellWidget(row, 5, self._wrap_widget(chk))

        self._adjust_table_columns()

    def _wrap_widget(self, w: QWidget) -> QWidget:
        container = QWidget()
        l = QHBoxLayout(container)
        l.setContentsMargins(6, 4, 6, 4)
        l.setAlignment(Qt.AlignCenter)
        l.addWidget(w)
        return container

    def _adjust_table_columns(self):
        w = max(700, self.table_pos.viewport().width())
        self.table_pos.setColumnWidth(0, int(w * 0.28))
        self.table_pos.setColumnWidth(1, int(w * 0.15))
        self.table_pos.setColumnWidth(2, int(w * 0.15))
        self.table_pos.setColumnWidth(3, max(150, int(w * 0.24)))
        self.table_pos.setColumnWidth(4, max(85, int(w * 0.10)))
        self.table_pos.setColumnWidth(5, max(55, int(w * 0.08)))

    def _on_table_coord_changed(self, stat_id: str, x: Optional[int] = None, y: Optional[int] = None):
        if stat_id in self.working_config.stats:
            item = self.working_config.stats[stat_id]
            if x is not None: item.x = x
            if y is not None: item.y = y
            self.canvas.update()
            self._record_history()

    def _on_table_snap_corner(self, stat_id: str, combo: QComboBox, sx: QSpinBox, sy: QSpinBox):
        pos = combo.currentData()
        if pos and isinstance(pos, tuple):
            sx.setValue(pos[0])
            sy.setValue(pos[1])
            self._on_table_coord_changed(stat_id, x=pos[0], y=pos[1])

    def _on_table_reset_single(self, stat_id: str, sx: QSpinBox, sy: QSpinBox):
        defaults = get_default_stats_catalog()
        if stat_id in defaults:
            def_item = defaults[stat_id]
            sx.setValue(def_item.x)
            sy.setValue(def_item.y)
            self._on_table_coord_changed(stat_id, x=def_item.x, y=def_item.y)

    def _on_table_lock_toggled(self, stat_id: str, locked: bool):
        if stat_id in self.working_config.stats:
            self.working_config.stats[stat_id].is_locked = locked

    # --- Inspector Panel Synchronization ---

    def _on_widget_selected(self, stat_id: str):
        self.canvas.selected_stat_id = stat_id
        if not stat_id or stat_id not in self.working_config.stats:
            self.lbl_selected_name.setText("Active: None")
            self.lbl_prop_title.setText("Widget Inspector")
            self.lbl_prop_desc.setText("Select any statistic on the canvas to configure.")
            self.form_widget.setEnabled(False)
            return

        item = self.working_config.stats[stat_id]
        self.lbl_selected_name.setText(f"Active: {item.name}")
        self.lbl_prop_title.setText(f"{item.name} ({item.category.capitalize()})")
        self.lbl_prop_desc.setText(f"Metric ID: {stat_id}")
        self.form_widget.setEnabled(True)

        self.spin_x.blockSignals(True)
        self.spin_y.blockSignals(True)
        self.spin_w.blockSignals(True)
        self.spin_h.blockSignals(True)
        self.spin_font.blockSignals(True)
        self.combo_mode.blockSignals(True)
        self.slider_opacity.blockSignals(True)
        self.chk_subtle_bg.blockSignals(True)
        self.chk_lock.blockSignals(True)

        self.spin_x.setValue(item.x)
        self.spin_y.setValue(item.y)
        w = item.graph_width if item.mode == DisplayMode.GRAPH else item.width
        h = item.graph_height if item.mode == DisplayMode.GRAPH else item.height
        self.spin_w.setValue(w)
        self.spin_h.setValue(h)
        self.spin_font.setValue(item.font_size)

        idx = self.combo_mode.findData(item.mode)
        if idx >= 0: self.combo_mode.setCurrentIndex(idx)

        self.btn_color.setStyleSheet(f"background-color: {item.color}; color: #000000; font-weight: bold;")
        self.slider_opacity.setValue(int(item.opacity * 100))
        self.chk_subtle_bg.setChecked(item.show_subtle_bg)
        self.chk_lock.setChecked(item.is_locked)

        self.spin_x.blockSignals(False)
        self.spin_y.blockSignals(False)
        self.spin_w.blockSignals(False)
        self.spin_h.blockSignals(False)
        self.spin_font.blockSignals(False)
        self.combo_mode.blockSignals(False)
        self.slider_opacity.blockSignals(False)
        self.chk_subtle_bg.blockSignals(False)
        self.chk_lock.blockSignals(False)

    def _on_geometry_modified(self, stat_id: str):
        if stat_id == self.canvas.selected_stat_id:
            self._on_widget_selected(stat_id)
        self._record_history()

    def _on_prop_coord_changed(self):
        s_id = self.canvas.selected_stat_id
        if s_id and s_id in self.working_config.stats:
            item = self.working_config.stats[s_id]
            item.x = self.spin_x.value()
            item.y = self.spin_y.value()
            self.canvas.update()
            self._record_history()

    def _on_prop_size_changed(self):
        s_id = self.canvas.selected_stat_id
        if s_id and s_id in self.working_config.stats:
            item = self.working_config.stats[s_id]
            w = self.spin_w.value()
            h = self.spin_h.value()
            if item.mode == DisplayMode.GRAPH:
                item.graph_width = w
                item.graph_height = h
            else:
                item.width = w
                item.height = h
            self.canvas.update()
            self._record_history()

    def _on_prop_font_changed(self, val: int):
        s_id = self.canvas.selected_stat_id
        if s_id and s_id in self.working_config.stats:
            self.working_config.stats[s_id].font_size = val
            self.canvas.update()
            self._record_history()

    def _on_prop_mode_changed(self):
        s_id = self.canvas.selected_stat_id
        if s_id and s_id in self.working_config.stats:
            mode = self.combo_mode.currentData()
            item = self.working_config.stats[s_id]
            item.mode = mode
            item.enabled = (mode != DisplayMode.DONT_SHOW)
            self.canvas.update()
            self._record_history()

    def _on_pick_color(self):
        s_id = self.canvas.selected_stat_id
        if not s_id or s_id not in self.working_config.stats:
            return
        item = self.working_config.stats[s_id]
        chosen = QColorDialog.getColor(QColor(item.color), self, f"Select Accent Color - {item.name}")
        if chosen.isValid():
            hex_c = chosen.name()
            item.color = hex_c
            self.btn_color.setStyleSheet(f"background-color: {hex_c}; color: #000000; font-weight: bold;")
            self.canvas.update()
            self._record_history()

    def _on_prop_opacity_changed(self, val: int):
        s_id = self.canvas.selected_stat_id
        if s_id and s_id in self.working_config.stats:
            self.working_config.stats[s_id].opacity = val / 100.0
            self.canvas.update()
            self._record_history()

    def _on_prop_bg_toggled(self, checked: bool):
        s_id = self.canvas.selected_stat_id
        if s_id and s_id in self.working_config.stats:
            self.working_config.stats[s_id].show_subtle_bg = checked
            self.canvas.update()
            self._record_history()

    def _on_prop_lock_toggled(self, checked: bool):
        s_id = self.canvas.selected_stat_id
        if s_id and s_id in self.working_config.stats:
            self.working_config.stats[s_id].is_locked = checked

    # --- Alignment Tools ---

    def _align_left(self):
        s_id = self.canvas.selected_stat_id
        if s_id and s_id in self.working_config.stats:
            self.working_config.stats[s_id].x = 24
            self._on_geometry_modified(s_id)

    def _align_center(self):
        s_id = self.canvas.selected_stat_id
        if s_id and s_id in self.working_config.stats:
            item = self.working_config.stats[s_id]
            w = item.graph_width if item.mode == DisplayMode.GRAPH else item.width
            self.working_config.stats[s_id].x = (self.canvas.res_w - w) // 2
            self._on_geometry_modified(s_id)

    def _align_right(self):
        s_id = self.canvas.selected_stat_id
        if s_id and s_id in self.working_config.stats:
            item = self.working_config.stats[s_id]
            w = item.graph_width if item.mode == DisplayMode.GRAPH else item.width
            self.working_config.stats[s_id].x = self.canvas.res_w - w - 24
            self._on_geometry_modified(s_id)

    def _align_top(self):
        s_id = self.canvas.selected_stat_id
        if s_id and s_id in self.working_config.stats:
            self.working_config.stats[s_id].y = 24
            self._on_geometry_modified(s_id)

    def _align_middle(self):
        s_id = self.canvas.selected_stat_id
        if s_id and s_id in self.working_config.stats:
            item = self.working_config.stats[s_id]
            h = item.graph_height if item.mode == DisplayMode.GRAPH else item.height
            self.working_config.stats[s_id].y = (self.canvas.res_h - h) // 2
            self._on_geometry_modified(s_id)

    def _align_bottom(self):
        s_id = self.canvas.selected_stat_id
        if s_id and s_id in self.working_config.stats:
            item = self.working_config.stats[s_id]
            h = item.graph_height if item.mode == DisplayMode.GRAPH else item.height
            self.working_config.stats[s_id].y = self.canvas.res_h - h - 24
            self._on_geometry_modified(s_id)

    def _snap_selected_to_corner(self, corner: str):
        s_id = self.canvas.selected_stat_id
        if not s_id or s_id not in self.working_config.stats:
            return
        item = self.working_config.stats[s_id]
        w = item.graph_width if item.mode == DisplayMode.GRAPH else item.width
        h = item.graph_height if item.mode == DisplayMode.GRAPH else item.height

        if corner == "tl":
            item.x, item.y = 24, 24
        elif corner == "tr":
            item.x, item.y = self.canvas.res_w - w - 24, 24
        elif corner == "bl":
            item.x, item.y = 24, self.canvas.res_h - h - 24
        elif corner == "br":
            item.x, item.y = self.canvas.res_w - w - 24, self.canvas.res_h - h - 24

        self._on_geometry_modified(s_id)

    # --- Undo / Redo History ---

    def _record_history(self):
        snapshot = copy.deepcopy(self.working_config.to_dict())
        if self._history_idx >= 0 and self._history[self._history_idx] == snapshot:
            return

        self._history = self._history[:self._history_idx + 1]
        self._history.append(snapshot)
        if len(self._history) > 30:
            self._history.pop(0)
        self._history_idx = len(self._history) - 1
        self._update_undo_redo_ui()

    def _on_undo(self):
        if self._history_idx > 0:
            self._history_idx -= 1
            self.working_config = OverlayConfig.from_dict(copy.deepcopy(self._history[self._history_idx]))
            self.canvas.set_config(self.working_config)
            if self.canvas.selected_stat_id:
                self._on_widget_selected(self.canvas.selected_stat_id)
            self._update_undo_redo_ui()

    def _on_redo(self):
        if self._history_idx < len(self._history) - 1:
            self._history_idx += 1
            self.working_config = OverlayConfig.from_dict(copy.deepcopy(self._history[self._history_idx]))
            self.canvas.set_config(self.working_config)
            if self.canvas.selected_stat_id:
                self._on_widget_selected(self.canvas.selected_stat_id)
            self._update_undo_redo_ui()

    def _update_undo_redo_ui(self):
        self.btn_undo.setEnabled(self._history_idx > 0)
        self.btn_redo.setEnabled(self._history_idx < len(self._history) - 1)

    # --- Save / Cancel / Resets ---

    def _on_reset_selected(self):
        s_id = self.canvas.selected_stat_id
        if not s_id or s_id not in self.working_config.stats:
            return
        catalog = get_default_stats_catalog()
        if s_id in catalog:
            def_item = catalog[s_id]
            cur = self.working_config.stats[s_id]
            cur.x = def_item.x
            cur.y = def_item.y
            cur.width = def_item.width
            cur.height = def_item.height
            cur.graph_width = def_item.graph_width
            cur.graph_height = def_item.graph_height
            self._on_geometry_modified(s_id)

    def _on_reset_all(self):
        catalog = get_default_stats_catalog()
        for stat_id, def_item in catalog.items():
            if stat_id in self.working_config.stats:
                cur = self.working_config.stats[stat_id]
                cur.x = def_item.x
                cur.y = def_item.y
                cur.width = def_item.width
                cur.height = def_item.height
                cur.graph_width = def_item.graph_width
                cur.graph_height = def_item.graph_height
        self.canvas.update()
        if self.canvas.selected_stat_id:
            self._on_widget_selected(self.canvas.selected_stat_id)
        self._record_history()

    def _on_save_clicked(self):
        self.save_and_apply.emit(self.working_config)

    def _on_cancel_clicked(self):
        self.working_config = copy.deepcopy(self.original_config)
        self.canvas.set_config(self.working_config)
        self.cancelled.emit()


# Backward compatibility alias for tests
SimulatedDesktopCanvas = InteractiveDesktopCanvas
