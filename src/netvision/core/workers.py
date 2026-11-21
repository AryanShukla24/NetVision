"""
NetVision - Background Thread Workers
Decouples heavy network operations (ICMP probes, socket bandwidth testing,
Wi-Fi scanning, repeated academic experiments) from the main GUI thread using QThread.
Maintains persistent references to running threads and supports clean cancellation.
"""

import time
import logging
from typing import List, Optional, Dict, Any
from PySide6.QtCore import QThread, Signal

from netvision.core.wifi_scanner import WifiScanner
from netvision.core.speed_tester import SpeedTester
from netvision.core.latency_monitor import LatencyMonitor
from netvision.core.signal_monitor import SignalMonitor
from netvision.database.models import (
    WifiNetwork, SpeedTestResult, LatencyTestResult,
    SignalLogEntry, ExperimentRun, ConnectedInterfaceInfo
)
from netvision.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class InterfaceRefreshWorker(QThread):
    """Lightweight background worker for querying active Wi-Fi interface metadata."""
    refreshed = Signal(object)  # ConnectedInterfaceInfo

    def __init__(self):
        super().__init__()
        self.scanner = WifiScanner()

    def run(self):
        try:
            info = self.scanner.get_connected_interface()
            self.refreshed.emit(info)
        except Exception as e:
            logger.exception("Error in InterfaceRefreshWorker: %s", e)
            self.refreshed.emit(ConnectedInterfaceInfo(state="disconnected"))


class WifiScanWorker(QThread):
    """Background worker for 802.11 spectrum scanning via wlanapi and netsh."""
    scan_completed = Signal(list, object)  # (List[WifiNetwork], Optional[str])

    def __init__(self, location_label: str = "Default", db_manager: Optional[DatabaseManager] = None):
        super().__init__()
        self.location_label = location_label
        self.db = db_manager
        self.scanner = WifiScanner()

    def run(self):
        try:
            networks, error = self.scanner.scan_networks()
            if self.db and networks:
                try:
                    conn_info = self.scanner.last_connected_info or self.scanner.get_connected_interface()
                    self.db.save_scan_session(
                        networks=networks,
                        active_interface=conn_info.interface_name,
                        location_label=self.location_label
                    )
                except Exception as e:
                    logger.error(f"Error persisting scan session: {e}")
            self.scan_completed.emit(networks, error)
        except Exception as e:
            logger.exception("Error in WifiScanWorker")
            self.scan_completed.emit([], str(e))


class SpeedTestWorker(QThread):
    """Background worker for WAN throughput tests against CDN edge infrastructure."""
    progress = Signal(str, float, float)  # phase_name, percent, current_speed_mbps
    finished = Signal(SpeedTestResult)

    def __init__(
        self,
        network_ssid: str = "",
        location_label: str = "Default",
        db_manager: Optional[DatabaseManager] = None
    ):
        super().__init__()
        self.network_ssid = network_ssid
        self.location_label = location_label
        self.db = db_manager
        self.tester = SpeedTester()

    def abort(self):
        self.tester.abort()

    def run(self):
        try:
            ssid = self.network_ssid
            if not ssid:
                try:
                    info = WifiScanner().get_connected_interface()
                    ssid = info.ssid if info.state == "connected" else ""
                except Exception as e:
                    logger.warning("Could not resolve active SSID before speed test: %s", e)
            result = self.tester.run_speed_test(
                progress_callback=lambda ph, pct, sp: self.progress.emit(ph, pct, sp),
                network_ssid=ssid,
                location_label=self.location_label
            )
            if self.db:
                try:
                    self.db.save_speed_test(result)
                except Exception as e:
                    logger.error(f"Error persisting speed test: {e}")
            self.finished.emit(result)
        except Exception as e:
            logger.exception("Error in SpeedTestWorker")
            failed_res = SpeedTestResult(
                download_mbps=None,
                upload_mbps=None,
                ping_ms=None,
                jitter_ms=None,
                status="failed",
                error_message=str(e),
                network_ssid=self.network_ssid,
                location_label=self.location_label
            )
            if self.db:
                try:
                    self.db.save_speed_test(failed_res)
                except Exception:
                    pass
            self.finished.emit(failed_res)


class LatencyTestWorker(QThread):
    """Background worker for ICMP echo probes or TCP 3-way handshake probes."""
    probe_step = Signal(int, int, object)  # step, total, Optional[float]
    finished = Signal(LatencyTestResult)

    def __init__(
        self,
        target_host: str = "8.8.8.8",
        count: int = 10,
        network_ssid: str = "",
        location_label: str = "Default",
        method: str = "ICMP",
        db_manager: Optional[DatabaseManager] = None
    ):
        super().__init__()
        self.target_host = target_host
        self.count = count
        self.network_ssid = network_ssid
        self.location_label = location_label
        self.method = method
        self.db = db_manager
        self.monitor = LatencyMonitor(target_host=target_host, method=method)
        self._should_stop = False

    def abort(self):
        self._should_stop = True

    def run(self):
        try:
            ssid = self.network_ssid
            if not ssid:
                try:
                    info = WifiScanner().get_connected_interface()
                    ssid = info.ssid if info.state == "connected" else ""
                except Exception as e:
                    logger.warning("Could not resolve active SSID before latency test: %s", e)
            result = self.monitor.run_test(
                count=self.count,
                progress_callback=lambda s, t, r: self.probe_step.emit(s, t, r),
                should_stop=lambda: self._should_stop,
                network_ssid=ssid,
                location_label=self.location_label
            )
            if self.db:
                try:
                    self.db.save_latency_test(result)
                except Exception as e:
                    logger.error(f"Error persisting latency test: {e}")
            self.finished.emit(result)
        except Exception as e:
            logger.exception("Error in LatencyTestWorker")
            failed_res = LatencyTestResult(
                target_host=self.target_host,
                ping_count=0,
                min_rtt_ms=None,
                max_rtt_ms=None,
                avg_rtt_ms=None,
                jitter_ms=None,
                packet_loss_percent=100.0,
                method=self.method,
                status="failed",
                network_ssid=self.network_ssid,
                location_label=self.location_label
            )
            if self.db:
                try:
                    self.db.save_latency_test(failed_res)
                except Exception:
                    pass
            self.finished.emit(failed_res)


class SignalMonitorWorker(QThread):
    """Background worker for continuous polling of active Wi-Fi signal quality."""
    signal_sample = Signal(SignalLogEntry, dict)  # entry, stability_summary
    connection_changed = Signal(bool, str)        # is_connected, ssid_or_reason

    def __init__(
        self,
        interval_sec: int = 2,
        location_label: str = "Default",
        db_manager: Optional[DatabaseManager] = None
    ):
        super().__init__()
        self.interval_sec = max(1, interval_sec)
        self.location_label = location_label
        self.monitor = SignalMonitor(db_manager=db_manager)
        self._is_running = True
        self._last_connected_state: Optional[bool] = None

    def stop(self):
        self._is_running = False

    def clear_history(self):
        self.monitor.clear_history()

    def run(self):
        while self._is_running:
            entry, is_conn, info = self.monitor.monitor_tick(location_label=self.location_label)

            if is_conn != self._last_connected_state:
                self._last_connected_state = is_conn
                reason = info.ssid if is_conn else "Wi-Fi Disconnected"
                self.connection_changed.emit(is_conn, reason)

            if is_conn and entry:
                stability = self.monitor.get_stability_summary()
                self.signal_sample.emit(entry, stability)

            # Sleep in small slices to allow rapid thread stopping
            for _ in range(self.interval_sec * 10):
                if not self._is_running:
                    break
                time.sleep(0.1)


class ExperimentWorker(QThread):
    """Background worker running repeated academic trials under defined test conditions."""
    trial_finished = Signal(ExperimentRun, int)  # run_obj, total_trials
    experiment_finished = Signal(bool)           # was_completed (True) or aborted (False)

    def __init__(
        self,
        experiment_id: str,
        condition_label: str,
        trials_count: int = 5,
        target_host: str = "8.8.8.8",
        location_label: str = "",
        db_manager: Optional[DatabaseManager] = None
    ):
        super().__init__()
        self.experiment_id = experiment_id
        self.condition_label = condition_label
        self.trials_count = max(1, trials_count)
        self.target_host = target_host
        self.location_label = location_label or condition_label
        self.db = db_manager
        self.scanner = WifiScanner()
        self.speed_tester = SpeedTester()
        self.latency_monitor = LatencyMonitor(target_host=target_host)
        self._abort = False

    def abort(self):
        self._abort = True
        self.speed_tester.abort()

    def run(self):
        completed_all = True
        for run_no in range(1, self.trials_count + 1):
            if self._abort:
                completed_all = False
                break

            # 1. Capture Wi-Fi Signal genuinely
            info = self.scanner.get_connected_interface()
            is_connected = (info.state == "connected" and bool(info.ssid))
            signal_pct: Optional[int] = info.signal_percent if is_connected else None
            ssid = info.ssid if is_connected else "Disconnected"

            # 2. Capture Ping & Jitter
            lat_res = self.latency_monitor.run_test(
                count=5,
                interval_sec=0.2,
                should_stop=lambda: self._abort
            )
            if self._abort:
                completed_all = False
                break

            # 3. Capture Throughput (only if connected)
            if is_connected:
                speed_res = self.speed_tester.run_speed_test(
                    network_ssid=ssid,
                    location_label=self.location_label
                )
                down_mbps = speed_res.download_mbps
                up_mbps = speed_res.upload_mbps
            else:
                down_mbps = None
                up_mbps = None

            if self._abort:
                completed_all = False
                break

            run = ExperimentRun(
                experiment_id=self.experiment_id,
                condition_label=self.condition_label,
                run_number=run_no,
                network_ssid=ssid,
                location_label=self.location_label,
                signal_percent=signal_pct,
                ping_ms=lat_res.avg_rtt_ms,
                jitter_ms=lat_res.jitter_ms,
                packet_loss_percent=lat_res.packet_loss_percent,
                download_mbps=down_mbps,
                upload_mbps=up_mbps,
                target_host=self.target_host,
                status="completed"
            )

            if self.db:
                try:
                    self.db.save_experiment_run(run)
                except Exception as e:
                    logger.error(f"Error saving experiment run: {e}")

            self.trial_finished.emit(run, self.trials_count)
            for _ in range(8):
                if self._abort:
                    completed_all = False
                    break
                time.sleep(0.1)

        self.experiment_finished.emit(completed_all)
