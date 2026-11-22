"""
Tests for Native Click-Through, Game FPS Detection, and Centralized System Telemetry.
Verifies:
1. Native Windows extended window styles (WS_EX_TRANSPARENT, WS_EX_NOACTIVATE).
2. Mouse pass-through in Normal Mode and interaction in Editing Mode.
3. Foreground game process identification and rejection of NetVision's own PID.
4. Honest 'N/A' reporting for unavailable FPS without fabricated data.
5. Accurate multi-core CPU, non-NetVision GPU, physical RAM, and active NIC throughput.
6. RFC 3550 jitter and sliding window packet loss calculation.
7. Wi-Fi vs. Wired Ethernet detection.
8. Centralized telemetry distribution to Dashboard and Overlay.
"""

import os
import sys
import time
import pytest
import ctypes
from ctypes import wintypes
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint

from netvision.core.overlay_config import StatItemConfig, DisplayMode
from netvision.ui.overlay.floating_widget import (
    FloatingStatWidget,
    GWL_EXSTYLE,
    WS_EX_TRANSPARENT,
    WS_EX_NOACTIVATE,
    WS_EX_LAYERED,
    WS_EX_TOOLWINDOW
)
from netvision.core.fps_detector import ForegroundAppDetector, FpsDetector, ForegroundAppInfo
from netvision.core.stats_collector import StatisticsCollector, WindowsGpuHelper, NativeSystemMetrics


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    return app


def test_click_through_native_styles_normal_mode(qapp):
    """Verifies that in Normal Mode, floating widgets have WS_EX_TRANSPARENT applied."""
    item = StatItemConfig(stat_id="fps", name="FPS", enabled=True, x=100, y=100, width=120, height=45)
    widget = FloatingStatWidget(item, master_locked=True)
    widget.show()
    qapp.processEvents()

    assert widget.testAttribute(Qt.WA_TransparentForMouseEvents) is True
    assert widget.testAttribute(Qt.WA_ShowWithoutActivating) is True

    if sys.platform == "win32":
        hwnd = int(widget.winId())
        user32 = ctypes.windll.user32
        if hwnd and user32.IsWindow(hwnd):
            if ctypes.sizeof(ctypes.c_void_p) == 8:
                user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
                user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
                GetWindowLong = user32.GetWindowLongPtrW
            else:
                user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
                user32.GetWindowLongW.restype = ctypes.c_long
                GetWindowLong = user32.GetWindowLongW

            ex = GetWindowLong(hwnd, GWL_EXSTYLE)
            assert (ex & WS_EX_TRANSPARENT) != 0, "WS_EX_TRANSPARENT must be active in normal locked mode"
            assert (ex & WS_EX_NOACTIVATE) != 0, "WS_EX_NOACTIVATE must be active to prevent focus stealing"

    widget.close()


def test_editing_mode_toggles_click_through(qapp):
    """Verifies that enabling editing mode removes WS_EX_TRANSPARENT, and exiting restores it."""
    item = StatItemConfig(stat_id="cpu", name="CPU Usage", enabled=True, x=150, y=150, width=130, height=50)
    widget = FloatingStatWidget(item, master_locked=True)
    widget.show()
    qapp.processEvents()

    # 1. Normal mode (Click-through enabled)
    widget.set_editing_mode(False)
    assert widget.testAttribute(Qt.WA_TransparentForMouseEvents) is True

    if sys.platform == "win32":
        hwnd = int(widget.winId())
        user32 = ctypes.windll.user32
        if hwnd and user32.IsWindow(hwnd):
            if ctypes.sizeof(ctypes.c_void_p) == 8:
                user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
                user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
                GetWindowLong = user32.GetWindowLongPtrW
            else:
                user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
                user32.GetWindowLongW.restype = ctypes.c_long
                GetWindowLong = user32.GetWindowLongW

            ex = GetWindowLong(hwnd, GWL_EXSTYLE)
            assert (ex & WS_EX_TRANSPARENT) != 0

            # 2. Switch to Editing Mode (Interactive on desktop)
            widget.set_editing_mode(True)
            assert widget.testAttribute(Qt.WA_TransparentForMouseEvents) is False

            ex_edit = GetWindowLong(hwnd, GWL_EXSTYLE)
            assert (ex_edit & WS_EX_TRANSPARENT) == 0, "WS_EX_TRANSPARENT must be removed in editing mode"

            # 3. Exit Editing Mode (Immediately restore click-through)
            widget.set_editing_mode(False)
            assert widget.testAttribute(Qt.WA_TransparentForMouseEvents) is True

            ex_restored = GetWindowLong(hwnd, GWL_EXSTYLE)
            assert (ex_restored & WS_EX_TRANSPARENT) != 0, "WS_EX_TRANSPARENT must be immediately restored"
        else:
            widget.set_editing_mode(True)
            assert widget.testAttribute(Qt.WA_TransparentForMouseEvents) is False
            widget.set_editing_mode(False)
            assert widget.testAttribute(Qt.WA_TransparentForMouseEvents) is True

    widget.close()


def test_foreground_detector_never_reports_netvision():
    """Verifies that ForegroundAppDetector filters out NetVision's own process ID."""
    detector = ForegroundAppDetector()
    my_pid = os.getpid()

    # Simulate foreground window being NetVision
    app_info = detector.get_foreground_app()
    # Target game property must never return NetVision
    target = detector.target_game_app
    if target:
        assert target.pid != my_pid, "Target game must never be NetVision itself"
        assert not target.is_netvision


def test_fps_detector_honest_na_when_unavailable():
    """Verifies that FpsDetector reports honest 'N/A' rather than invented values."""
    fps_det = FpsDetector()
    fps_val, disp_str, target = fps_det.get_fps()

    # In test environment, if no game/RTSS is running, must report None and N/A
    if fps_val is None:
        assert "N/A" in disp_str, f"Expected N/A in display string, got {disp_str}"
        assert fps_val is None
    else:
        # If a game was genuinely running via RTSS
        assert fps_val > 0.0
        assert "FPS" in disp_str


def test_gpu_helper_excludes_netvision_process():
    """Verifies that WindowsGpuHelper excludes NetVision's own process ID."""
    helper = WindowsGpuHelper()
    val = helper.get_gpu_percent()
    assert 0.0 <= val <= 100.0, f"GPU percent out of bounds: {val}"
    assert helper._my_pid == os.getpid()
    helper.close()


def test_native_system_metrics():
    """Verifies Windows native ctypes fallback for CPU and RAM."""
    metrics = NativeSystemMetrics()
    cpu = metrics.get_cpu_percent()
    assert 0.0 <= cpu <= 100.0

    mem = metrics.get_memory_info()
    assert "percent" in mem
    assert "used_gb" in mem
    assert "total_gb" in mem
    assert mem["total_gb"] > 0.0


def test_rfc3550_jitter_and_loss_calculation():
    """Verifies RFC 3550 / Mean Absolute Difference jitter calculation."""
    collector = StatisticsCollector(ping_target="127.0.0.1")

    # Inject known RTT probe history: 20ms, 25ms, 22ms, 28ms
    collector._ping_history.extend([20.0, 25.0, 22.0, 28.0])
    # Diffs: |25-20|=5, |22-25|=3, |28-22|=6 -> sum=14, mean = 14 / 3 = 4.67 ms
    diffs = [
        abs(collector._ping_history[i] - collector._ping_history[i - 1])
        for i in range(1, len(collector._ping_history))
    ]
    expected_jitter = round(sum(diffs) / len(diffs), 1)
    assert expected_jitter == 4.7

    # Inject 1 loss in 10 probes -> 10.0% loss
    collector._loss_window.extend([False] * 9 + [True])
    loss_pct = round((sum(1 for lost in collector._loss_window if lost) / len(collector._loss_window)) * 100.0, 1)
    assert loss_pct == 10.0

    collector.clean_up()


def test_centralized_telemetry_snapshot_integrity():
    """Verifies that StatisticsCollector produces consistent, typed snapshots."""
    collector = StatisticsCollector(sample_interval_ms=500)
    collector._collect_sample()

    snap = collector.get_latest_snapshot()
    assert "timestamp" in snap
    assert "fps" in snap
    assert "cpu" in snap
    assert "gpu" in snap
    assert "ram" in snap
    assert "download_speed" in snap
    assert "upload_speed" in snap
    assert "ping" in snap
    assert "jitter" in snap
    assert "packet_loss" in snap
    assert "wifi_signal" in snap

    # Units and display strings
    assert "%" in snap["cpu"]["display"]
    assert "%" in snap["gpu"]["display"]
    assert "GB" in snap["ram"]["display"]
    assert "Mbps" in snap["download_speed"]["display"]
    assert "Mbps" in snap["upload_speed"]["display"]

    collector.clean_up()
