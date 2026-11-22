"""
NetVision - Windows Native Desktop Capture & Wallpaper Resolution Engine
Fetches the user's authentic desktop wallpaper and live open application windows.
Handles multi-monitor geometry, recursive self-capture exclusion, DPI scaling,
and graceful fallback to exact cached Windows desktop wallpaper files.
"""

import os
import sys
import ctypes
from typing import Optional, Tuple, List
import logging
from PySide6.QtGui import QGuiApplication, QPixmap, QImage, QColor, QPainter, QScreen
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


def get_available_monitors() -> List[dict]:
    """Enumerates all active display monitors with geometry, scaling, and names."""
    monitors = []
    screens = QGuiApplication.screens()
    primary = QGuiApplication.primaryScreen()

    for idx, screen in enumerate(screens):
        geo = screen.geometry()
        dpr = screen.devicePixelRatio()
        is_pri = (screen == primary)
        monitors.append({
            "index": idx,
            "screen": screen,
            "name": screen.name() or f"Display {idx + 1}",
            "x": geo.x(),
            "y": geo.y(),
            "width": geo.width(),
            "height": geo.height(),
            "dpr": dpr,
            "is_primary": is_pri,
            "label": f"Display {idx + 1}{' (Primary)' if is_pri else ''} — {geo.width()}×{geo.height()}"
        })
    return monitors


def get_windows_active_wallpaper_path() -> Optional[str]:
    """Retrieves the file path of the currently active desktop wallpaper on Windows."""
    # 1. Query Windows API via SystemParametersInfoW
    try:
        user32 = ctypes.windll.user32
        buf = ctypes.create_unicode_buffer(512)
        SPI_GETDESKWALLPAPER = 0x0073
        if user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, 512, buf, 0):
            wall_path = buf.value.strip()
            if wall_path and os.path.exists(wall_path):
                return wall_path
    except Exception as e:
        logger.debug(f"SystemParametersInfoW wallpaper query failed: {e}")

    # 2. Query Windows Themes directory in %APPDATA%
    try:
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            transcoded = os.path.join(appdata, "Microsoft", "Windows", "Themes", "TranscodedWallpaper")
            if os.path.exists(transcoded):
                return transcoded
    except Exception as e:
        logger.debug(f"TranscodedWallpaper check failed: {e}")

    # 3. Query Windows Registry
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop") as key:
            val, _ = winreg.QueryValueEx(key, "Wallpaper")
            if val and os.path.exists(val):
                return val
    except Exception as e:
        logger.debug(f"Registry wallpaper query failed: {e}")

    return None


def get_cached_resolution_wallpaper(target_w: int, target_h: int) -> Optional[str]:
    """Checks if Windows has pre-cached a cropped wallpaper for the exact monitor resolution."""
    try:
        appdata = os.environ.get("APPDATA", "")
        if not appdata:
            return None
        cached_dir = os.path.join(appdata, "Microsoft", "Windows", "Themes", "CachedFiles")
        if os.path.exists(cached_dir):
            target_tag = f"{target_w}_{target_h}"
            for fname in os.listdir(cached_dir):
                if target_tag in fname:
                    cand = os.path.join(cached_dir, fname)
                    if os.path.exists(cand):
                        return cand
    except Exception as e:
        logger.debug(f"Cached resolution wallpaper check failed: {e}")
    return None


def is_pixmap_effectively_blank(pixmap: QPixmap, sample_step: int = 40) -> bool:
    """Verifies whether a captured pixmap is completely black/empty or has real graphics."""
    if pixmap.isNull() or pixmap.width() <= 0 or pixmap.height() <= 0:
        return True
    img = pixmap.toImage()
    w, h = img.width(), img.height()

    for y in range(0, h, sample_step):
        for x in range(0, w, sample_step):
            pixel = img.pixel(x, y) & 0x00FFFFFF
            if pixel != 0:
                return False
    return True


def render_fitted_wallpaper(image_path: str, target_w: int, target_h: int) -> Optional[QPixmap]:
    """Loads a wallpaper file and fits it with aspect ratio preservation (crop-fill)."""
    src_pix = QPixmap(image_path)
    if src_pix.isNull():
        return None

    # Scaled with AspectRatioByExpanding and centered
    scaled = src_pix.scaled(
        target_w, target_h,
        Qt.KeepAspectRatioByExpanding,
        Qt.SmoothTransformation
    )

    out = QPixmap(target_w, target_h)
    out.fill(QColor(16, 21, 28))
    painter = QPainter(out)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

    sx = max(0, (scaled.width() - target_w) // 2)
    sy = max(0, (scaled.height() - target_h) // 2)
    painter.drawPixmap(0, 0, scaled, sx, sy, target_w, target_h)
    painter.end()

    return out


def capture_desktop_preview(
    screen_idx: int = 0,
    target_res: Optional[Tuple[int, int]] = None,
    exclude_widget: Optional[QWidget] = None
) -> Tuple[Optional[QPixmap], str]:
    """
    Captures or resolves the user's real desktop wallpaper and live open windows.
    Returns: (QPixmap, status_description)
    """
    screens = QGuiApplication.screens()
    if not screens:
        return None, "No active displays detected"

    if screen_idx < 0 or screen_idx >= len(screens):
        screen_idx = 0

    screen = screens[screen_idx]
    geo = screen.geometry()
    screen_w = target_res[0] if target_res else geo.width()
    screen_h = target_res[1] if target_res else geo.height()

    # Step 1: Attempt live screen capture via screen.grabWindow(0)
    live_pix: Optional[QPixmap] = None
    try:
        # Exclude NetVision editor from capturing itself recursively
        if exclude_widget and exclude_widget.isVisible():
            orig_opacity = exclude_widget.windowOpacity()
            exclude_widget.setWindowOpacity(0.0)
            QGuiApplication.processEvents()
            live_pix = screen.grabWindow(0)
            exclude_widget.setWindowOpacity(orig_opacity)
            QGuiApplication.processEvents()
        else:
            live_pix = screen.grabWindow(0)
    except Exception as e:
        logger.warning(f"Live desktop grab exception: {e}")

    # Check if live capture produced genuine content (not blank black screen)
    if live_pix and not is_pixmap_effectively_blank(live_pix):
        if (live_pix.width(), live_pix.height()) != (screen_w, screen_h):
            live_pix = live_pix.scaled(screen_w, screen_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return live_pix, "Live Desktop (Screen & Windows)"

    # Step 2: Screen grab returned black or blank -> Load User's Actual Desktop Wallpaper
    cached_wall = get_cached_resolution_wallpaper(screen_w, screen_h)
    if cached_wall:
        wall_pix = render_fitted_wallpaper(cached_wall, screen_w, screen_h)
        if wall_pix and not wall_pix.isNull():
            return wall_pix, "Active Windows Wallpaper (Fitted)"

    wall_path = get_windows_active_wallpaper_path()
    if wall_path:
        wall_pix = render_fitted_wallpaper(wall_path, screen_w, screen_h)
        if wall_pix and not wall_pix.isNull():
            return wall_pix, "Active Windows Wallpaper (Direct)"

    # Step 3: High-tech instrumentation fallback if system wallpaper cannot be read
    fallback = QPixmap(screen_w, screen_h)
    fallback.fill(QColor(16, 21, 28))
    painter = QPainter(fallback)
    painter.setPen(QColor(30, 42, 56))
    grid_sz = 32
    for x in range(0, screen_w, grid_sz):
        painter.drawLine(x, 0, x, screen_h)
    for y in range(0, screen_h, grid_sz):
        painter.drawLine(0, y, screen_w, y)
    painter.end()

    return fallback, "System Desktop Canvas"
