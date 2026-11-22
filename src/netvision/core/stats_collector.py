"""
NetVision - High-Performance Real-Time Statistics Collector
Gathers system performance (FPS, CPU, GPU, RAM) and network telemetry
(Wi-Fi Signal, Ping, Jitter, Packet Loss, Throughput, Download/Upload)
using non-blocking asynchronous sampling and native APIs.
"""

import time
import math
import collections
import logging
import ctypes
from ctypes import wintypes
from typing import Dict, Any, Optional, Deque

from PySide6.QtCore import QObject, Signal, QTimer, QThread

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from netvision.core.subprocess_utils import run_hidden_command, run_subprocess
from netvision.core.wifi_scanner import WifiScanner

logger = logging.getLogger(__name__)


# --- Windows Native Win32 API structures for CPU & RAM fallback ---

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_uint64),
        ("ullAvailPhys", ctypes.c_uint64),
        ("ullTotalPageFile", ctypes.c_uint64),
        ("ullAvailPageFile", ctypes.c_uint64),
        ("ullTotalVirtual", ctypes.c_uint64),
        ("ullAvailVirtual", ctypes.c_uint64),
        ("sullAvailExtendedVirtual", ctypes.c_uint64),
    ]


class FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", wintypes.DWORD),
        ("dwHighDateTime", wintypes.DWORD)
    ]


def _filetime_to_int(ft: FILETIME) -> int:
    return (ft.dwHighDateTime << 32) + ft.dwLowDateTime


class NativeSystemMetrics:
    """Windows native ctypes metrics collector when external packages are unavailable."""

    def __init__(self):
        self._kernel32 = ctypes.windll.kernel32
        self._prev_idle = 0
        self._prev_kernel = 0
        self._prev_user = 0
        self._init_cpu()

    def _init_cpu(self):
        idle = FILETIME()
        kernel = FILETIME()
        user = FILETIME()
        if self._kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            self._prev_idle = _filetime_to_int(idle)
            self._prev_kernel = _filetime_to_int(kernel)
            self._prev_user = _filetime_to_int(user)

    def get_cpu_percent(self) -> float:
        idle = FILETIME()
        kernel = FILETIME()
        user = FILETIME()
        if not self._kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            return 0.0

        i_int = _filetime_to_int(idle)
        k_int = _filetime_to_int(kernel)
        u_int = _filetime_to_int(user)

        d_idle = i_int - self._prev_idle
        d_kernel = k_int - self._prev_kernel
        d_user = u_int - self._prev_user

        self._prev_idle = i_int
        self._prev_kernel = k_int
        self._prev_user = u_int

        sys_time = d_kernel + d_user
        if sys_time <= 0:
            return 0.0

        cpu_usage = (sys_time - d_idle) * 100.0 / sys_time
        return max(0.0, min(100.0, round(cpu_usage, 1)))

    def get_memory_info(self) -> Dict[str, Any]:
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if self._kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            total_gb = stat.ullTotalPhys / (1024 ** 3)
            used_gb = (stat.ullTotalPhys - stat.ullAvailPhys) / (1024 ** 3)
            return {
                "percent": float(stat.dwMemoryLoad),
                "used_gb": round(used_gb, 2),
                "total_gb": round(total_gb, 2)
            }
        return {"percent": 0.0, "used_gb": 0.0, "total_gb": 0.0}


class WindowsGpuHelper:
    """
    Lightweight, safe Windows GPU utilization reader using PDH counter or WMI query.
    Falls back gracefully without raising exceptions or creating console windows.
    """

    def __init__(self):
        self._query = None
        self._counter = None
        self._pdh_available = False
        self._last_val = 0.0
        self._last_query_time = 0.0
        self._init_pdh()

    def _init_pdh(self):
        try:
            self._pdh = ctypes.windll.pdh
            # Basic sanity check
            self._pdh_available = True
        except Exception:
            self._pdh_available = False

    def get_gpu_percent(self) -> float:
        now = time.time()
        # Query at most once every 1.0 second to keep system overhead minimal
        if now - self._last_query_time < 0.8:
            return self._last_val

        self._last_query_time = now
        val = self._sample_gpu()
        self._last_val = val
        return val

    def _sample_gpu(self) -> float:
        # Use fast PowerShell one-liner or PDH if possible, or fallback safely
        # Note: run_subprocess uses CREATE_NO_WINDOW so no black box ever pops up!
        try:
            cmd = [
                "powershell", "-NoProfile", "-NonInteractive", "-Command",
                "try { $samples = (Get-Counter '\\GPU Engine(*engtype_3D)\\Utilization Percentage' -ErrorAction SilentlyContinue).CounterSamples; ($samples | Measure-Object -Property CookedValue -Sum).Sum } catch { 0 }"
            ]
            res = run_subprocess(cmd, timeout=1.2)
            if res.returncode == 0 and res.stdout.strip():
                raw = float(res.stdout.strip())
                return max(0.0, min(100.0, round(raw, 1)))
        except Exception:
            pass
        return self._last_val


class StatisticsCollector(QObject):
    """
    Real-time statistics collector managing high-resolution ring buffers
    and non-blocking background telemetry sampling.
    """

    stats_updated = Signal(dict)

    def __init__(self, ping_target: str = "8.8.8.8", sample_interval_ms: int = 1000, parent=None):
        super().__init__(parent)
        self.ping_target = ping_target
        self.sample_interval_ms = sample_interval_ms
        self.is_running = False

        self._native_sys = NativeSystemMetrics()
        self._gpu_helper = WindowsGpuHelper()
        self._wifi_scanner = WifiScanner()

        # FPS Tracking
        self._fps_frame_count = 0
        self._fps_last_time = time.time()
        self._current_fps = 60.0

        # Network I/O Tracking
        self._last_net_time = time.time()
        self._last_bytes_sent = 0
        self._last_bytes_recv = 0
        self._init_net_io()

        # Ping & Jitter history
        self._ping_history: Deque[float] = collections.deque(maxlen=30)
        self._loss_window: Deque[bool] = collections.deque(maxlen=20)

        # Ring buffers for each of the 11 metrics (history up to 120 points)
        self.history_buffers: Dict[str, Deque[float]] = {
            "fps": collections.deque(maxlen=120),
            "cpu": collections.deque(maxlen=120),
            "gpu": collections.deque(maxlen=120),
            "ram": collections.deque(maxlen=120),
            "net_io": collections.deque(maxlen=120),
            "wifi_signal": collections.deque(maxlen=120),
            "ping": collections.deque(maxlen=120),
            "jitter": collections.deque(maxlen=120),
            "packet_loss": collections.deque(maxlen=120),
            "download_speed": collections.deque(maxlen=120),
            "upload_speed": collections.deque(maxlen=120),
        }

        # Cached latest snapshot
        self._current_stats: Dict[str, Any] = {}

        # Sampling Timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._collect_sample)

    def _init_net_io(self):
        if HAS_PSUTIL:
            try:
                io = psutil.net_io_counters()
                self._last_bytes_sent = io.bytes_sent
                self._last_bytes_recv = io.bytes_recv
            except Exception:
                pass

    def start(self, interval_ms: Optional[int] = None):
        """Starts periodic statistics collection."""
        if interval_ms:
            self.sample_interval_ms = interval_ms
        self.is_running = True
        self._timer.start(self.sample_interval_ms)
        # Immediate first sample
        self._collect_sample()

    def stop(self):
        """Stops statistics collection cleanly."""
        self.is_running = False
        self._timer.stop()

    def set_interval(self, interval_ms: int):
        self.sample_interval_ms = max(300, min(10000, interval_ms))
        if self.is_running:
            self._timer.setInterval(self.sample_interval_ms)

    def record_frame_tick(self):
        """Called by the overlay window when a visual frame renders to calculate real FPS."""
        self._fps_frame_count += 1
        now = time.time()
        elapsed = now - self._fps_last_time
        if elapsed >= 0.5:
            self._current_fps = round(self._fps_frame_count / elapsed, 1)
            self._fps_frame_count = 0
            self._fps_last_time = now

    def _collect_sample(self):
        """Gathers latest values across all 11 metrics in a single pass."""
        now = time.time()

        # 1. FPS
        fps_val = max(1.0, min(240.0, self._current_fps))

        # 2. CPU Usage
        if HAS_PSUTIL:
            try:
                cpu_val = psutil.cpu_percent(interval=None)
            except Exception:
                cpu_val = self._native_sys.get_cpu_percent()
        else:
            cpu_val = self._native_sys.get_cpu_percent()

        # 3. GPU Usage
        gpu_val = self._gpu_helper.get_gpu_percent()

        # 4. RAM Usage
        if HAS_PSUTIL:
            try:
                vmem = psutil.virtual_memory()
                ram_percent = round(vmem.percent, 1)
                ram_used_gb = round(vmem.used / (1024 ** 3), 2)
                ram_total_gb = round(vmem.total / (1024 ** 3), 2)
            except Exception:
                m = self._native_sys.get_memory_info()
                ram_percent, ram_used_gb, ram_total_gb = m["percent"], m["used_gb"], m["total_gb"]
        else:
            m = self._native_sys.get_memory_info()
            ram_percent, ram_used_gb, ram_total_gb = m["percent"], m["used_gb"], m["total_gb"]

        # 5. Network I/O Throughput
        net_io_kb = 0.0
        down_kb = 0.0
        up_kb = 0.0
        if HAS_PSUTIL:
            try:
                io = psutil.net_io_counters()
                d_time = max(0.1, now - self._last_net_time)
                d_recv = max(0, io.bytes_recv - self._last_bytes_recv)
                d_sent = max(0, io.bytes_sent - self._last_bytes_sent)
                self._last_bytes_recv = io.bytes_recv
                self._last_bytes_sent = io.bytes_sent
                self._last_net_time = now
                
                down_kb = round((d_recv / 1024.0) / d_time, 1)
                up_kb = round((d_sent / 1024.0) / d_time, 1)
                net_io_kb = round(down_kb + up_kb, 1)
            except Exception:
                pass

        # 6. Wi-Fi Signal Quality
        wifi_sig = 0.0
        ssid = "N/A"
        try:
            conn = self._wifi_scanner.get_connected_interface()
            if conn and conn.state == "connected" and conn.signal_percent is not None:
                wifi_sig = float(conn.signal_percent)
                ssid = conn.ssid or "Connected"
            else:
                ssid = "Disconnected"
        except Exception:
            pass

        # 7, 8, 9. Latency / Ping, Jitter, Packet Loss
        ping_val, jitter_val, loss_val = self._probe_ping()

        # 10, 11. Download & Upload Speeds (Mbps)
        # Convert real-time through-put to Mbps
        down_mbps = round(down_kb * 8.0 / 1024.0, 2)
        up_mbps = round(up_kb * 8.0 / 1024.0, 2)

        # Store in historical ring buffers
        self.history_buffers["fps"].append(fps_val)
        self.history_buffers["cpu"].append(cpu_val)
        self.history_buffers["gpu"].append(gpu_val)
        self.history_buffers["ram"].append(ram_percent)
        self.history_buffers["net_io"].append(net_io_kb)
        self.history_buffers["wifi_signal"].append(wifi_sig)
        self.history_buffers["ping"].append(ping_val)
        self.history_buffers["jitter"].append(jitter_val)
        self.history_buffers["packet_loss"].append(loss_val)
        self.history_buffers["download_speed"].append(down_mbps)
        self.history_buffers["upload_speed"].append(up_mbps)

        # Build comprehensive snapshot payload
        snapshot = {
            "fps": {
                "val": fps_val,
                "display": f"{int(fps_val)} FPS",
                "history": list(self.history_buffers["fps"])
            },
            "cpu": {
                "val": cpu_val,
                "display": f"{cpu_val:.1f}%",
                "history": list(self.history_buffers["cpu"])
            },
            "gpu": {
                "val": gpu_val,
                "display": f"{gpu_val:.1f}%",
                "history": list(self.history_buffers["gpu"])
            },
            "ram": {
                "val": ram_percent,
                "display": f"{ram_percent:.1f}% ({ram_used_gb}/{ram_total_gb} GB)",
                "history": list(self.history_buffers["ram"])
            },
            "net_io": {
                "val": net_io_kb,
                "display": f"↓ {down_kb:.0f} KB/s  ↑ {up_kb:.0f} KB/s",
                "history": list(self.history_buffers["net_io"])
            },
            "wifi_signal": {
                "val": wifi_sig,
                "display": f"{int(wifi_sig)}% ({ssid})",
                "history": list(self.history_buffers["wifi_signal"])
            },
            "ping": {
                "val": ping_val,
                "display": f"{ping_val:.1f} ms" if ping_val > 0 else "Timeout",
                "history": list(self.history_buffers["ping"])
            },
            "jitter": {
                "val": jitter_val,
                "display": f"{jitter_val:.1f} ms",
                "history": list(self.history_buffers["jitter"])
            },
            "packet_loss": {
                "val": loss_val,
                "display": f"{loss_val:.1f}%",
                "history": list(self.history_buffers["packet_loss"])
            },
            "download_speed": {
                "val": down_mbps,
                "display": f"{down_mbps:.2f} Mbps",
                "history": list(self.history_buffers["download_speed"])
            },
            "upload_speed": {
                "val": up_mbps,
                "display": f"{up_mbps:.2f} Mbps",
                "history": list(self.history_buffers["upload_speed"])
            },
        }

        self._current_stats = snapshot
        self.stats_updated.emit(snapshot)

    def _probe_ping(self) -> (float, float, float):
        """
        Sends 1 fast Windows ping probe (non-blocking subprocess with CREATE_NO_WINDOW).
        Calculates ping, jitter, and packet loss from sliding window.
        """
        target = self.ping_target or "8.8.8.8"
        cmd = ["ping", "-n", "1", "-w", "750", target]
        try:
            res = run_subprocess(cmd, timeout=0.9)
            if res.returncode == 0 and "time=" in res.stdout.lower():
                # Extract time=<N>ms
                import re
                m = re.search(r"time[<=](\d+(?:\.\d+)?)ms", res.stdout, re.IGNORECASE)
                if m:
                    latency = float(m.group(1))
                    self._ping_history.append(latency)
                    self._loss_window.append(False)
                else:
                    self._loss_window.append(False)
                    latency = self._ping_history[-1] if self._ping_history else 20.0
            else:
                self._loss_window.append(True)
                latency = 0.0
        except Exception:
            self._loss_window.append(True)
            latency = 0.0

        # Calculate jitter (mean absolute consecutive difference)
        if len(self._ping_history) >= 2:
            diffs = [
                abs(self._ping_history[i] - self._ping_history[i - 1])
                for i in range(1, len(self._ping_history))
            ]
            jitter = round(sum(diffs) / len(diffs), 1)
        else:
            jitter = 0.0

        # Calculate sliding loss %
        if self._loss_window:
            loss_pct = round(
                (sum(1 for lost in self._loss_window if lost) / len(self._loss_window)) * 100.0,
                1
            )
        else:
            loss_pct = 0.0

        cur_ping = self._ping_history[-1] if self._ping_history else 0.0
        return cur_ping, jitter, loss_pct
