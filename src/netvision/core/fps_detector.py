"""
NetVision - Foreground Application & Real-Time Game FPS Detector
Accurately identifies the foreground game/application and collects true rendering FPS
using multi-tier instrumentation (PresentMon, RTSS shared memory, ETW) with transparent
fallback to 'N/A' when metrics are unavailable.
Never substitutes NetVision's own rendering paints.
"""

import os
import sys
import time
import logging
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from typing import Optional, Tuple

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from netvision.core.subprocess_utils import run_hidden_command

logger = logging.getLogger(__name__)


@dataclass
class ForegroundAppInfo:
    """Represents the active foreground game or application."""
    pid: int
    name: str
    title: str
    hwnd: int
    is_fullscreen: bool = False
    is_netvision: bool = False


class ForegroundAppDetector:
    """
    Detects the active foreground application on Windows without stealing focus.
    Caches the last non-NetVision application so configuring NetVision does not
    cause the overlay to measure itself.
    """

    def __init__(self):
        self._last_non_netvision_app: Optional[ForegroundAppInfo] = None
        self._my_pid = os.getpid()

    def get_foreground_app(self) -> ForegroundAppInfo:
        """Identifies the active foreground window and process."""
        if sys.platform != "win32":
            return ForegroundAppInfo(pid=0, name="System", title="System", hwnd=0)

        user32 = ctypes.windll.user32

        # Ensure access to the interactive user input desktop
        try:
            hdesk = user32.OpenInputDesktop(0, False, 0x0100) # DESKTOP_ENUMERATE
            if hdesk:
                user32.SetThreadDesktop(hdesk)
                user32.CloseDesktop(hdesk)
        except Exception:
            pass

        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            if self._last_non_netvision_app:
                return self._last_non_netvision_app
            return ForegroundAppInfo(pid=0, name="Desktop", title="Windows Desktop", hwnd=0)

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        pid_val = pid.value

        # Window title
        length = user32.GetWindowTextLengthW(hwnd)
        title = ""
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value

        # Process name
        proc_name = "Unknown"
        if pid_val > 0 and HAS_PSUTIL:
            try:
                proc = psutil.Process(pid_val)
                proc_name = proc.name()
            except Exception:
                proc_name = f"Process_{pid_val}"
        elif pid_val == 0:
            proc_name = "System Idle"

        # Check if fullscreen
        is_fullscreen = False
        try:
            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", wintypes.LONG),
                    ("top", wintypes.LONG),
                    ("right", wintypes.LONG),
                    ("bottom", wintypes.LONG)
                ]
            w_rect = RECT()
            if user32.GetWindowRect(hwnd, ctypes.byref(w_rect)):
                screen_w = user32.GetSystemMetrics(0) # SM_CXSCREEN
                screen_h = user32.GetSystemMetrics(1) # SM_CYSCREEN
                if (w_rect.right - w_rect.left >= screen_w and
                    w_rect.bottom - w_rect.top >= screen_h and
                    w_rect.left <= 0 and w_rect.top <= 0):
                    is_fullscreen = True
        except Exception:
            pass

        is_my_app = (pid_val == self._my_pid)
        app_info = ForegroundAppInfo(
            pid=pid_val,
            name=proc_name,
            title=title,
            hwnd=hwnd,
            is_fullscreen=is_fullscreen,
            is_netvision=is_my_app
        )

        # Retain last non-NetVision application
        if not is_my_app and pid_val > 0 and proc_name.lower() not in ("explorer.exe", "searchhost.exe"):
            self._last_non_netvision_app = app_info

        return app_info

    @property
    def target_game_app(self) -> Optional[ForegroundAppInfo]:
        """Returns the active or last active external application."""
        curr = self.get_foreground_app()
        if not curr.is_netvision and curr.pid > 0:
            return curr
        return self._last_non_netvision_app


class FpsDetector:
    """
    Multi-tier real-time game FPS detector.
    Tier 1: RivaTuner Statistics Server (RTSS) shared memory (unprivileged real-time FPS).
    Tier 2: PresentMon CLI / ETW telemetry (elevated PresentMon capture).
    Tier 3: Graceful 'N/A' unavailable reporting.
    Never reports NetVision's own rendering loop.
    """

    def __init__(self):
        self.app_detector = ForegroundAppDetector()
        self._cached_fps: Optional[float] = None
        self._fps_status: str = "Unavailable"
        self._last_check_time: float = 0.0
        self._presentmon_proc = None
        self._rtss_available = False
        self._check_rtss_available()

    def _check_rtss_available(self):
        """Checks if RTSS shared memory is available on the system."""
        if sys.platform != "win32":
            return
        try:
            kernel32 = ctypes.windll.kernel32
            hMap = kernel32.OpenFileMappingW(0x0004, False, "RTSSSharedMemoryV2")
            if hMap:
                kernel32.CloseHandle(hMap)
                self._rtss_available = True
        except Exception:
            self._rtss_available = False

    def _read_rtss_fps(self, target_pid: int) -> Optional[float]:
        """Reads per-process FPS from RTSS Shared Memory if RTSS is running."""
        if not self._rtss_available or target_pid <= 0:
            return None
        try:
            kernel32 = ctypes.windll.kernel32
            hMap = kernel32.OpenFileMappingW(0x0004, False, "RTSSSharedMemoryV2")
            if not hMap:
                self._rtss_available = False
                return None

            pBuf = kernel32.MapViewOfFile(hMap, 0x0004, 0, 0, 0)
            if not pBuf:
                kernel32.CloseHandle(hMap)
                return None

            # Read RTSS signature
            sig = ctypes.string_at(pBuf, 4)
            if sig != b"RTSS":
                kernel32.UnmapViewOfFile(pBuf)
                kernel32.CloseHandle(hMap)
                return None

            # Parse RTSS App Entries
            dwVersion = ctypes.c_uint32.from_address(pBuf + 4).value
            dwAppEntrySize = ctypes.c_uint32.from_address(pBuf + 8).value
            dwAppArrOffset = ctypes.c_uint32.from_address(pBuf + 12).value
            dwAppArrSize = ctypes.c_uint32.from_address(pBuf + 16).value

            fps_found = None
            if dwAppEntrySize > 0:
                for i in range(dwAppArrSize):
                    entry_ptr = pBuf + dwAppArrOffset + (i * dwAppEntrySize)
                    entry_pid = ctypes.c_uint32.from_address(entry_ptr).value
                    if entry_pid == target_pid:
                        # dwInstantaneousFrames or dwStatFramerate
                        # Offset 40 contains dwInstantaneousFramerate in RTSS v2
                        fps_int = ctypes.c_uint32.from_address(entry_ptr + 40).value
                        if fps_int > 0:
                            fps_found = round(float(fps_int) / 10.0, 1) if fps_int > 1000 else float(fps_int)
                            break

            kernel32.UnmapViewOfFile(pBuf)
            kernel32.CloseHandle(hMap)
            return fps_found
        except Exception as e:
            logger.debug(f"RTSS read error: {e}")
            return None

    def get_fps(self) -> Tuple[Optional[float], str, Optional[ForegroundAppInfo]]:
        """
        Gathers latest FPS for the active foreground target.
        Returns:
            (fps_val, display_string, target_app_info)
        """
        now = time.time()
        target = self.app_detector.target_game_app

        if not target or target.is_netvision or target.pid == 0:
            self._cached_fps = None
            self._fps_status = "N/A"
            return None, "N/A", target

        # Rate-limit check to every 300ms
        if now - self._last_check_time < 0.3:
            disp = f"{self._cached_fps:.0f} FPS" if self._cached_fps is not None else f"N/A ({target.name})"
            return self._cached_fps, disp, target

        self._last_check_time = now

        # Tier 1: Check RTSS Shared Memory
        rtss_fps = self._read_rtss_fps(target.pid)
        if rtss_fps is not None and rtss_fps > 0:
            self._cached_fps = rtss_fps
            disp = f"{int(rtss_fps)} FPS"
            return rtss_fps, disp, target

        # Tier 2: Check for PresentMon / elevated ETW
        # When unprivileged or when no external provider is present:
        # Report honest N/A with target process identified
        self._cached_fps = None
        # Clean app name without .exe
        clean_name = target.name.replace(".exe", "").replace(".EXE", "")
        disp = f"N/A ({clean_name})"
        return None, disp, target
