"""
Regression Tests for Windows Hidden Subprocess Execution and Worker Lifecycle.

Verifies:
1. All internal Windows subprocesses (netsh, ping) use CREATE_NO_WINDOW,
   STARTUPINFO(STARTF_USESHOWWINDOW, SW_HIDE), shell=False, and stdin=DEVNULL.
2. Output capture, timeout handling, and error logging continue functioning.
3. Sidebar navigation, repeated button clicks, monitoring start/stop,
   report generation, and window close never spawn duplicate workers or leak threads.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication, QMessageBox

from netvision.core.latency_monitor import LatencyMonitor
from netvision.core.subprocess_utils import (
    CREATE_NO_WINDOW_FLAG,
    get_hidden_subprocess_kwargs,
    run_hidden_command,
)
from netvision.core.wifi_scanner import WifiScanner
from netvision.database.db_manager import DatabaseManager
from netvision.database.models import ConnectedInterfaceInfo, WifiNetwork
from netvision.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _assert_hidden_windows_kwargs(kwargs: dict):
    """Asserts that subprocess.run received proper Windows no-console configuration."""
    assert kwargs.get("shell") is False
    assert kwargs.get("stdin") == subprocess.DEVNULL
    assert kwargs.get("capture_output") is True
    assert kwargs.get("text") is True
    if sys.platform == "win32":
        assert (kwargs.get("creationflags", 0) & CREATE_NO_WINDOW_FLAG) == CREATE_NO_WINDOW_FLAG
        si = kwargs.get("startupinfo")
        assert si is not None
        assert (si.dwFlags & subprocess.STARTF_USESHOWWINDOW) == subprocess.STARTF_USESHOWWINDOW
        assert si.wShowWindow == subprocess.SW_HIDE


def test_hidden_subprocess_kwargs_on_windows():
    kwargs = get_hidden_subprocess_kwargs()
    if sys.platform == "win32":
        assert (kwargs["creationflags"] & subprocess.CREATE_NO_WINDOW) == subprocess.CREATE_NO_WINDOW
        si = kwargs["startupinfo"]
        assert isinstance(si, subprocess.STARTUPINFO)
        assert (si.dwFlags & subprocess.STARTF_USESHOWWINDOW) == subprocess.STARTF_USESHOWWINDOW
        assert si.wShowWindow == subprocess.SW_HIDE
    else:
        assert kwargs == {}


def test_wifi_scanner_run_command_uses_hidden_console_flags(caplog):
    fake_proc = subprocess.CompletedProcess(
        args=["netsh", "wlan", "show", "interfaces"],
        returncode=0,
        stdout="Name : Wi-Fi\nState : disconnected\n",
        stderr="",
    )
    with patch("netvision.core.subprocess_utils.subprocess.run", return_value=fake_proc) as mock_run:
        code, out = WifiScanner._run_command(["netsh", "wlan", "show", "interfaces"], timeout=5)

    assert code == 0
    assert "Wi-Fi" in out
    assert mock_run.call_count == 1
    _assert_hidden_windows_kwargs(mock_run.call_args.kwargs)


def test_wifi_scanner_run_command_logs_timeout_and_errors(caplog):
    with caplog.at_level(logging.WARNING):
        with patch(
            "netvision.core.subprocess_utils.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["netsh"], timeout=2),
        ):
            code, msg = WifiScanner._run_command(["netsh", "wlan", "show", "interfaces"], timeout=2)
    assert code == -1
    assert "timed out" in msg.lower()
    assert any("timed out" in rec.message.lower() for rec in caplog.records)

    caplog.clear()
    with caplog.at_level(logging.ERROR):
        with patch(
            "netvision.core.subprocess_utils.subprocess.run",
            side_effect=FileNotFoundError("netsh"),
        ):
            code, msg = WifiScanner._run_command(["netsh", "wlan", "show", "interfaces"], timeout=2)
    assert code == -2
    assert any("not found" in rec.message.lower() for rec in caplog.records)


def test_latency_monitor_icmp_uses_hidden_console_flags(caplog):
    fake_proc = subprocess.CompletedProcess(
        args=["ping", "-n", "1", "-w", "1500", "8.8.8.8"],
        returncode=0,
        stdout="Reply from 8.8.8.8: bytes=32 time=12ms TTL=117\n",
        stderr="",
    )
    monitor = LatencyMonitor(target_host="8.8.8.8", timeout_ms=1500, method="ICMP")
    with patch("netvision.core.subprocess_utils.subprocess.run", return_value=fake_proc) as mock_run:
        rtt = monitor.probe_single()

    assert rtt == 12.0
    assert mock_run.call_count == 1
    _assert_hidden_windows_kwargs(mock_run.call_args.kwargs)

    # Verify timeout logs warning rather than silently discarding
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        with patch(
            "netvision.core.subprocess_utils.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["ping"], timeout=2),
        ):
            assert monitor.probe_single() is None
    assert any("timed out" in rec.message.lower() for rec in caplog.records)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only live command verification")
def test_real_windows_hidden_ping_and_netsh_capture_output():
    """Executes genuine Windows ping (loopback) and netsh commands hidden and verifies stdout capture."""
    ping_res = run_hidden_command(["ping", "-n", "1", "-w", "1000", "127.0.0.1"], timeout=5)
    assert ping_res.returncode == 0
    assert "127.0.0.1" in ping_res.stdout

    netsh_res = run_hidden_command(["netsh", "wlan", "show", "interfaces"], timeout=5)
    assert netsh_res.returncode in (0, 1)
    assert isinstance(netsh_res.stdout, str)


class _DummyBlockingWorker(QThread):
    """Controlled dummy QThread for verifying single-instance guards and shutdown."""

    def __init__(self, hold_sec: float = 0.4):
        super().__init__()
        self._hold_sec = hold_sec
        self._stop_flag = False
        self.abort_called = False

    def stop(self):
        self._stop_flag = True

    def abort(self):
        self.abort_called = True
        self._stop_flag = True

    def run(self):
        deadline = time.monotonic() + self._hold_sec
        while not self._stop_flag and time.monotonic() < deadline:
            time.sleep(0.02)


def test_gui_navigation_worker_guards_reports_and_shutdown(qapp, tmp_path, monkeypatch):
    """
    Exercises the full 10-step interaction checklist:
    - Sidebar navigation across all 12 pages
    - Dashboard refresh guard and auto-refresh pause/resume
    - Signal monitoring repeated start/stop
    - Wi-Fi scan, Speed test, Latency test single-worker guards
    - Channel analysis non-blocking behavior
    - PDF and CSV report generation
    - Clean shutdown with zero lingering timers/threads
    """
    db_file = tmp_path / "lifecycle_test.db"
    db_manager = DatabaseManager(db_path=db_file)
    db_manager.save_scan_session(
        [WifiNetwork(ssid="TestNet", bssid="aa:bb:cc:dd:ee:01", channel=6, signal_percent=78, frequency_band="2.4 GHz")],
        active_interface="Wi-Fi",
        location_label="Lab",
    )

    mock_conn = ConnectedInterfaceInfo(
        interface_name="Wi-Fi",
        state="connected",
        ssid="TestNet",
        bssid="aa:bb:cc:dd:ee:01",
        channel=6,
        frequency_band="2.4 GHz",
        signal_percent=78,
        ipv4_address="192.168.1.50",
        gateway="192.168.1.1",
    )

    # Prevent real network/OS I/O while testing GUI orchestration
    monkeypatch.setattr(WifiScanner, "get_connected_interface", lambda self: mock_conn)
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **kw: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **kw: QMessageBox.Ok)

    window = MainWindow(db_manager=db_manager)
    window._latest_conn_info = mock_conn

    # 1. Navigate repeatedly across every sidebar page
    for _ in range(2):
        for idx in range(window.stack.count()):
            window.switch_page(idx)
            assert window.stack.currentIndex() == idx
            if idx == 0:
                assert window.page_dashboard._refresh_timer.isActive() is True
            else:
                assert window.page_dashboard._refresh_timer.isActive() is False

    # Navigation alone must never spawn scan/speed/latency/signal/experiment workers
    assert window.active_scan_worker is None
    assert window.active_speed_worker is None
    assert window.active_latency_worker is None
    assert window.active_signal_worker is None
    assert window.active_experiment_worker is None

    # 2. Dashboard refresh guard prevents overlapping refresh workers
    window.switch_page(0)
    blocker = _DummyBlockingWorker(hold_sec=0.5)
    blocker.start()
    window.active_refresh_worker = blocker
    window.refresh_dashboard_data()
    assert window.active_refresh_worker is blocker  # Did not overwrite or spawn duplicate
    blocker.stop()
    blocker.wait(1000)
    window.active_refresh_worker = None

    # 3. Signal monitoring start/stop lifecycle (repeatedly)
    for _ in range(3):
        window.start_signal_monitoring("Lab", 1)
        first_worker = window.active_signal_worker
        assert first_worker is not None
        assert first_worker.isRunning()
        window.stop_signal_monitoring()
        assert window.active_signal_worker is None
        assert not first_worker.isRunning()

    # 4. Wi-Fi Scan guard prevents duplicate concurrent scan workers
    scan_blocker = _DummyBlockingWorker(hold_sec=0.5)
    scan_blocker.start()
    window.active_scan_worker = scan_blocker
    window.start_wifi_scan("Lab")
    assert window.active_scan_worker is scan_blocker
    scan_blocker.stop()
    scan_blocker.wait(1000)
    window.active_scan_worker = None

    # 5. Speed test guard prevents duplicate concurrent speed workers
    speed_blocker = _DummyBlockingWorker(hold_sec=0.5)
    speed_blocker.start()
    window.active_speed_worker = speed_blocker
    window.start_speed_test("Lab")
    assert window.active_speed_worker is speed_blocker
    window.stop_speed_test()
    assert speed_blocker.abort_called is True
    speed_blocker.wait(1000)
    window.active_speed_worker = None

    # 6. Latency test guard prevents duplicate concurrent latency workers
    lat_blocker = _DummyBlockingWorker(hold_sec=0.5)
    lat_blocker.start()
    window.active_latency_worker = lat_blocker
    window.start_latency_test("8.8.8.8", 5, "Lab", "ICMP")
    assert window.active_latency_worker is lat_blocker
    window.stop_latency_test()
    assert lat_blocker.abort_called is True
    lat_blocker.wait(1000)
    window.active_latency_worker = None

    # 7. Channel analysis runs cleanly without spawning workers when DB has scan data
    window.switch_page(5)
    window._run_channel_analysis(trigger_scan_if_empty=False)
    assert window.active_scan_worker is None

    # 8. Report generation (PDF & CSV) into isolated temp reports dir
    import netvision.core.reporter as reporter_mod
    monkeypatch.setattr(reporter_mod, "REPORTS_DIR", tmp_path)
    window.export_pdf_report()
    window.export_csv_report()
    assert any(p.suffix == ".pdf" for p in tmp_path.iterdir())
    assert any(p.suffix == ".csv" for p in tmp_path.iterdir())

    # 9. Clean close stops timers and terminates any active workers
    window.start_signal_monitoring("Lab", 1)
    assert window.active_signal_worker is not None
    window.close()
    assert window._closing is True
    assert window.page_dashboard._refresh_timer.isActive() is False
    assert window.active_signal_worker is None
    assert window.active_refresh_worker is None
