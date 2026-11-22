"""
NetVision - Main Application Window
Modern desktop interface integrating sidebar navigation, QStackedWidget pages,
background QThread orchestration, and safe application lifecycle management.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QStackedWidget, QFrame, QScrollArea, QMessageBox, QStatusBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QCloseEvent

from netvision.config import APP_NAME, APP_SUBTITLE, APP_VERSION, COLORS, APP_ICON_PNG, APP_ICON_ICO
from netvision.database.db_manager import DatabaseManager
from netvision.database.models import ConnectedInterfaceInfo
from netvision.core.wifi_scanner import WifiScanner
from netvision.core.channel_analyzer import ChannelAnalyzer
from netvision.core.recommendation_engine import RecommendationEngine
from netvision.core.reporter import ReportGenerator
from netvision.core.workers import (
    InterfaceRefreshWorker, WifiScanWorker, SpeedTestWorker,
    LatencyTestWorker, SignalMonitorWorker, ExperimentWorker
)
from netvision.core.overlay_config import OverlayConfig
from netvision.core.stats_collector import StatisticsCollector
from netvision.core.shortcut_manager import GlobalShortcutManager
from netvision.ui.overlay.overlay_manager import OverlayManager

# Import Pages
from netvision.ui.pages.dashboard_page import DashboardPage
from netvision.ui.pages.scanner_page import ScannerPage
from netvision.ui.pages.signal_page import SignalPage
from netvision.ui.pages.speed_page import SpeedPage
from netvision.ui.pages.latency_page import LatencyPage
from netvision.ui.pages.channel_page import ChannelPage
from netvision.ui.pages.history_page import HistoryPage
from netvision.ui.pages.comparison_page import ComparisonPage
from netvision.ui.pages.experiment_page import ExperimentPage
from netvision.ui.pages.reports_page import ReportsPage
from netvision.ui.pages.settings_page import SettingsPage
from netvision.ui.pages.about_page import AboutPage

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main window with sidebar navigation and background controller."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — {APP_SUBTITLE} (v{APP_VERSION})")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 680)

        # Set consistent application icon
        if APP_ICON_PNG.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PNG)))
        elif APP_ICON_ICO.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_ICO)))

        self.db = db_manager or DatabaseManager()
        self.scanner = WifiScanner()
        self._latest_conn_info: Optional[ConnectedInterfaceInfo] = None
        self._closing: bool = False

        # Load overlay configuration and initialize real-time collector & multi-window manager
        self.overlay_config = OverlayConfig.load()
        self.stats_collector = StatisticsCollector(
            ping_target="8.8.8.8",
            sample_interval_ms=self.overlay_config.refresh_rate_ms,
            parent=self
        )
        self.overlay_manager = OverlayManager(self.overlay_config, self.stats_collector, parent=self)
        self.shortcut_manager = GlobalShortcutManager(self)

        # Active workers tracking for safe lifecycle and clean shutdown
        self.active_refresh_worker: Optional[InterfaceRefreshWorker] = None
        self.active_scan_worker: Optional[WifiScanWorker] = None
        self.active_speed_worker: Optional[SpeedTestWorker] = None
        self.active_latency_worker: Optional[LatencyTestWorker] = None
        self.active_signal_worker: Optional[SignalMonitorWorker] = None
        self.active_experiment_worker: Optional[ExperimentWorker] = None

        self._nav_buttons: List[QPushButton] = []
        self._build_ui()
        self._wire_signals()
        self._refresh_locations_across_pages()
        self._register_all_configured_shortcuts()

        # Overlay is disabled by default; only start if explicitly enabled in saved config
        if self.overlay_config.master_enabled:
            self.overlay_manager.start_overlay()

        # Load persisted settings from database
        persisted_settings = self.db.get_all_settings()
        if persisted_settings:
            self.page_settings.load_settings(persisted_settings)

        # Delayed initial refresh after UI display
        QTimer.singleShot(300, self.refresh_dashboard_data)

    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar Navigation
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        s_layout = QVBoxLayout(sidebar)
        s_layout.setContentsMargins(10, 16, 10, 16)
        s_layout.setSpacing(4)

        # App Branding Header
        header_frame = QFrame()
        header_frame.setObjectName("SidebarHeader")
        h_layout = QVBoxLayout(header_frame)
        h_layout.setContentsMargins(8, 0, 8, 12)
        h_layout.setSpacing(2)

        lbl_title = QLabel(APP_NAME)
        lbl_title.setObjectName("SidebarAppTitle")
        lbl_subtitle = QLabel(APP_SUBTITLE)
        lbl_subtitle.setObjectName("SidebarAppSubtitle")
        lbl_subtitle.setWordWrap(True)

        h_layout.addWidget(lbl_title)
        h_layout.addWidget(lbl_subtitle)
        s_layout.addWidget(header_frame)

        # Nav Buttons List
        nav_items = [
            ("📊 Dashboard", 0),
            ("📡 Wi-Fi Scanner", 1),
            ("📶 Signal Analyzer", 2),
            ("🚀 Speed Test", 3),
            ("⏱ Latency Monitor", 4),
            ("📻 Channel Analyzer", 5),
            ("📈 History & Analytics", 6),
            ("📍 Location Comparison", 7),
            ("🔬 Academic Experiment", 8),
            ("📄 Audit Reports", 9),
            ("⚙ Settings", 10),
            ("ℹ About NetVision", 11),
        ]

        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setProperty("class", "NavButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, idx=index: self.switch_page(idx))
            s_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        s_layout.addStretch()

        # Bottom build info
        lbl_ver = QLabel(f"v{APP_VERSION} | Windows 10/11 Native")
        lbl_ver.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; padding: 8px;")
        s_layout.addWidget(lbl_ver)

        main_layout.addWidget(sidebar)

        # 2. Main Content Pages (QStackedWidget)
        self.stack = QStackedWidget()

        self.page_dashboard = DashboardPage(self)
        self.page_scanner = ScannerPage(self)
        self.page_signal = SignalPage(self)
        self.page_speed = SpeedPage(self)
        self.page_latency = LatencyPage(self)
        self.page_channel = ChannelPage(self)
        self.page_history = HistoryPage(self)
        self.page_comparison = ComparisonPage(self)
        self.page_experiment = ExperimentPage(self)
        self.page_reports = ReportsPage(self)
        self.page_settings = SettingsPage(overlay_config=self.overlay_config, parent=self)
        self.page_about = AboutPage(self)

        self.stack.addWidget(self.page_dashboard)    # 0
        self.stack.addWidget(self.page_scanner)      # 1
        self.stack.addWidget(self.page_signal)       # 2
        self.stack.addWidget(self.page_speed)        # 3
        self.stack.addWidget(self.page_latency)      # 4
        self.stack.addWidget(self.page_channel)      # 5
        self.stack.addWidget(self.page_history)      # 6
        self.stack.addWidget(self.page_comparison)   # 7
        self.stack.addWidget(self.page_experiment)   # 8
        self.stack.addWidget(self.page_reports)      # 9
        self.stack.addWidget(self.page_settings)     # 10
        self.stack.addWidget(self.page_about)        # 11

        main_layout.addWidget(self.stack)

        # Select first page
        self.switch_page(0)

        # Status Bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"background-color: {COLORS['bg_surface']}; color: {COLORS['text_secondary']}; border-top: 1px solid {COLORS['border']};")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. System network subsystem initialized.")

    def switch_page(self, index: int):
        """Switches the active stacked page and updates sidebar button states."""
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            is_active = (i == index)
            btn.setChecked(is_active)
            btn.setProperty("active", "true" if is_active else "false")
            btn.setStyle(btn.style())  # Refresh stylesheet

        # Only run periodic dashboard polling while Dashboard is actually visible
        self.page_dashboard.set_auto_refresh_active(index == 0 and not self._closing)

        # Trigger passive view refreshes on visit (never spawn blocking OS scans on tab click)
        if index == 5:  # Channel Analyzer
            self._run_channel_analysis(trigger_scan_if_empty=False)
        elif index == 6:  # History
            self._refresh_history_page()
        elif index == 7:  # Comparison
            self._refresh_comparison_page()
        elif index == 8:  # Academic Experiment
            self._load_saved_experiments()
        elif index == 9:  # Reports
            self._refresh_reports_page()

    def _wire_signals(self):
        """Connects signals between page widgets, workers, and database."""
        # Dashboard
        self.page_dashboard.request_refresh.connect(self.refresh_dashboard_data)
        self.page_dashboard.request_quick_test.connect(self._run_quick_test)

        # Scanner
        self.page_scanner.request_scan.connect(self.start_wifi_scan)

        # Signal Analyzer
        self.page_signal.request_start_monitoring.connect(self.start_signal_monitoring)
        self.page_signal.request_stop_monitoring.connect(self.stop_signal_monitoring)
        self.page_signal.request_clear_history.connect(self._clear_signal_history)

        # Speed Test
        self.page_speed.request_start_test.connect(self.start_speed_test)
        self.page_speed.request_stop_test.connect(self.stop_speed_test)

        # Latency Monitor
        self.page_latency.request_start_ping.connect(self.start_latency_test)
        self.page_latency.request_stop_ping.connect(self.stop_latency_test)

        # Channel Analyzer
        self.page_channel.request_refresh.connect(lambda: self._run_channel_analysis(trigger_scan_if_empty=True))

        # History Page
        self.page_history.request_refresh.connect(self._refresh_history_page)
        self.page_history.request_delete_record.connect(self._delete_history_record)

        # Comparison Page
        self.page_comparison.request_refresh.connect(self._refresh_comparison_page)

        # Academic Experiment
        self.page_experiment.request_run_experiment.connect(self.start_experiment)
        self.page_experiment.request_stop_experiment.connect(self.stop_experiment)
        self.page_experiment.request_load_saved_experiments.connect(self._load_saved_experiments)

        # Reports Page
        self.page_reports.request_export_pdf.connect(self.export_pdf_report)
        self.page_reports.request_export_csv.connect(self.export_csv_report)

        # Settings Page
        self.page_settings.request_add_location.connect(self.add_custom_location)
        self.page_settings.request_save_settings.connect(self._save_app_settings)
        self.page_settings.request_restore_defaults.connect(self._restore_app_settings)
        self.page_settings.overlay_config_changed.connect(self._on_overlay_config_changed)
        self.page_settings.shortcut_updated.connect(self._on_stat_shortcut_updated)
        self.stats_collector.stats_updated.connect(self.page_settings.update_telemetry)

        # Global Hotkey Trigger Dispatcher
        self.shortcut_manager.shortcut_triggered.connect(self._on_stat_shortcut_triggered)

    def _on_overlay_config_changed(self, config: OverlayConfig):
        self.overlay_config = config
        self.overlay_manager.apply_config(config)

    def _on_stat_shortcut_updated(self, stat_id: str, shortcut_str: str):
        if shortcut_str:
            self.shortcut_manager.register_shortcut(stat_id, shortcut_str)
        else:
            self.shortcut_manager.unregister_shortcut(stat_id)

    def _on_stat_shortcut_triggered(self, stat_id: str):
        if stat_id == "master":
            self.overlay_manager.toggle_overlay()
            self.page_settings.chk_master_enabled.setChecked(self.overlay_config.master_enabled)
        else:
            self.overlay_manager.toggle_stat_visibility(stat_id)
            if stat_id in self.page_settings.vis_checkboxes:
                is_vis = self.overlay_config.stats[stat_id].enabled
                self.page_settings.vis_checkboxes[stat_id].setChecked(is_vis)

    def _register_all_configured_shortcuts(self):
        if self.overlay_config.master_shortcut:
            self.shortcut_manager.register_shortcut("master", self.overlay_config.master_shortcut)
        for stat_id, item in self.overlay_config.stats.items():
            if item.shortcut:
                self.shortcut_manager.register_shortcut(stat_id, item.shortcut)

    def _refresh_locations_across_pages(self):
        """Updates location combo boxes across all pages."""
        locs = self.db.get_locations()
        self.page_scanner.set_locations(locs)
        self.page_signal.set_locations(locs)
        self.page_speed.set_locations(locs)
        self.page_latency.set_locations(locs)
        self.page_history.set_locations(locs)
        self.page_comparison.set_locations(locs)
        self.page_experiment.set_locations(locs)
        self.page_settings.set_locations(locs)

    def add_custom_location(self, name: str):
        """Adds a location tag and refreshes all dropdowns."""
        self.db.add_location(name)
        self._refresh_locations_across_pages()
        self.status_bar.showMessage(f"Location '{name}' added successfully.", 4000)

    def _save_app_settings(self, settings: dict):
        """Persists configured thresholds and defaults into database."""
        for key, value in settings.items():
            self.db.set_setting(key, str(value))
        self.status_bar.showMessage("Application settings saved to database.", 3500)

    def _restore_app_settings(self):
        """Restores default system settings."""
        self.page_settings.load_settings({})
        self.status_bar.showMessage("Default settings restored.", 3500)

    # --- Feature 1: Dashboard Controller ---

    def _apply_dashboard_data(self, conn_info: ConnectedInterfaceInfo):
        """Applies refreshed interface info and latest DB test metrics to Dashboard."""
        self._latest_conn_info = conn_info
        self.page_dashboard.update_interface_info(conn_info)

        latest_speed = self.db.get_latest_speed_test()
        latest_latency = self.db.get_latest_latency_test()
        self.page_dashboard.update_latest_tests(latest_speed, latest_latency)

        if self.stack.currentIndex() == 9:
            self._render_reports_recommendations(conn_info)

        self.status_bar.showMessage(
            f"Active: {conn_info.ssid or 'Disconnected'} | IP: {conn_info.ipv4_address}",
            5000
        )

    def refresh_dashboard_data(self):
        """Asynchronously queries active Wi-Fi interface without blocking UI or overlapping refreshes."""
        if self._closing:
            return
        if self.active_refresh_worker and self.active_refresh_worker.isRunning():
            return

        worker = InterfaceRefreshWorker()
        self.active_refresh_worker = worker
        worker.refreshed.connect(self._on_interface_refreshed)
        worker.start()

    def _on_interface_refreshed(self, conn_info: ConnectedInterfaceInfo):
        worker = self.active_refresh_worker
        if worker:
            worker.wait(500)
            worker.deleteLater()
            self.active_refresh_worker = None
        if self._closing:
            return
        self._apply_dashboard_data(conn_info)

    def _run_quick_test(self):
        """Runs a fast latency probe for quick status without overlapping active latency probes."""
        if self.active_latency_worker and self.active_latency_worker.isRunning():
            self.status_bar.showMessage("A latency test is already running.", 3000)
            return
        self.status_bar.showMessage("Running quick latency test...")
        self.start_latency_test("8.8.8.8", 5, "QuickTest")

    # --- Feature 2: Wi-Fi Scanner Controller ---

    def start_wifi_scan(self, location_label: str):
        if self._closing:
            return
        if self.active_scan_worker and self.active_scan_worker.isRunning():
            return
        worker = WifiScanWorker(location_label=location_label, db_manager=self.db)
        self.active_scan_worker = worker
        worker.scan_completed.connect(self._on_wifi_scan_completed)
        worker.start()

    def _on_wifi_scan_completed(self, networks: list, error: Optional[str]):
        worker = self.active_scan_worker
        conn_info = worker.scanner.last_connected_info if worker else None
        if worker:
            worker.wait(500)
            worker.deleteLater()
            self.active_scan_worker = None
        if self._closing:
            return
        self.page_scanner.display_networks(networks, error)
        if conn_info is not None:
            self._apply_dashboard_data(conn_info)
        else:
            self.refresh_dashboard_data()
        if self.stack.currentIndex() == 5:
            self._run_channel_analysis(trigger_scan_if_empty=False)
        self.status_bar.showMessage(f"Scan complete. Discovered {len(networks)} networks.", 4000)

    # --- Feature 3: Signal Analyzer Controller ---

    def start_signal_monitoring(self, location_label: str, interval_sec: int):
        if self._closing:
            return
        self.stop_signal_monitoring()
        worker = SignalMonitorWorker(
            interval_sec=interval_sec,
            location_label=location_label,
            db_manager=self.db
        )
        self.active_signal_worker = worker
        worker.signal_sample.connect(self.page_signal.add_signal_sample)
        worker.connection_changed.connect(self.page_signal.on_connection_changed)
        worker.start()
        self.status_bar.showMessage("Continuous signal monitoring active.")

    def stop_signal_monitoring(self):
        worker = self.active_signal_worker
        if worker:
            try:
                worker.signal_sample.disconnect()
            except Exception:
                pass
            try:
                worker.connection_changed.disconnect()
            except Exception:
                pass
            worker.stop()
            if worker.isRunning():
                worker.wait(3000)
            worker.deleteLater()
            self.active_signal_worker = None
            if not self._closing:
                self.status_bar.showMessage("Signal monitoring stopped.", 3000)

    def _clear_signal_history(self):
        if self.active_signal_worker:
            self.active_signal_worker.clear_history()

    # --- Feature 4: Speed Test Controller ---

    def start_speed_test(self, location_label: str):
        if self._closing:
            return
        if self.active_speed_worker and self.active_speed_worker.isRunning():
            return
        ssid = (
            self._latest_conn_info.ssid
            if self._latest_conn_info and self._latest_conn_info.state == "connected"
            else ""
        )

        worker = SpeedTestWorker(
            network_ssid=ssid,
            location_label=location_label,
            db_manager=self.db
        )
        self.active_speed_worker = worker
        worker.progress.connect(self.page_speed.update_progress)
        worker.finished.connect(self._on_speed_test_finished)
        worker.start()
        self.status_bar.showMessage("Speed test running...")

    def stop_speed_test(self):
        if self.active_speed_worker and self.active_speed_worker.isRunning():
            self.active_speed_worker.abort()
        else:
            self.page_speed.btn_start.setEnabled(True)
            self.page_speed.btn_stop.setEnabled(False)

    def _on_speed_test_finished(self, result):
        worker = self.active_speed_worker
        if worker:
            worker.wait(500)
            worker.deleteLater()
            self.active_speed_worker = None
        if self._closing:
            return
        self.page_speed.display_result(result)
        self.refresh_dashboard_data()
        self.status_bar.showMessage("Speed test concluded.", 4000)

    # --- Feature 5: Latency Monitor Controller ---

    def start_latency_test(self, target_host: str, count: int, location_label: str, method: str = "ICMP"):
        if self._closing:
            return
        if self.active_latency_worker and self.active_latency_worker.isRunning():
            return
        ssid = (
            self._latest_conn_info.ssid
            if self._latest_conn_info and self._latest_conn_info.state == "connected"
            else ""
        )

        worker = LatencyTestWorker(
            target_host=target_host,
            count=count,
            network_ssid=ssid,
            location_label=location_label,
            method=method,
            db_manager=self.db
        )
        self.active_latency_worker = worker
        worker.probe_step.connect(self.page_latency.add_probe_result)
        worker.finished.connect(self._on_latency_test_finished)
        worker.start()
        self.status_bar.showMessage(f"Sending {method} probes to {target_host}...")

    def stop_latency_test(self):
        if self.active_latency_worker and self.active_latency_worker.isRunning():
            self.active_latency_worker.abort()
        else:
            self.page_latency.is_monitoring = False
            self.page_latency.btn_toggle.setEnabled(True)
            self.page_latency.btn_toggle.setText("▶  Start Probing")
            self.page_latency.btn_toggle.setProperty("class", "PrimaryButton")
            self.page_latency.btn_toggle.setStyle(self.page_latency.btn_toggle.style())

    def _on_latency_test_finished(self, result):
        worker = self.active_latency_worker
        if worker:
            worker.wait(500)
            worker.deleteLater()
            self.active_latency_worker = None
        if self._closing:
            return
        self.page_latency.display_final_result(result)
        self.refresh_dashboard_data()
        self.status_bar.showMessage("Latency probing complete.", 4000)

    # --- Feature 6: Channel Analyzer Controller ---

    def _run_channel_analysis(self, trigger_scan_if_empty: bool = False):
        networks = self.db.get_latest_networks()
        if not networks and trigger_scan_if_empty:
            self.status_bar.showMessage("No saved scan yet — running background Wi-Fi scan...", 4000)
            self.start_wifi_scan("Default")
        analysis = ChannelAnalyzer.analyze_channels(networks)
        self.page_channel.display_analysis(analysis)

    # --- Feature 7: History Page Controller ---

    def _refresh_history_page(self):
        speed_tests = self.db.get_speed_tests(limit=50)
        latency_tests = self.db.get_latency_tests(limit=50)
        signal_logs = self.db.get_signal_logs(limit=100)
        self.page_history.update_history_data(speed_tests, latency_tests, signal_logs)

    def _delete_history_record(self, table_name: str, record_id: int):
        self.db.delete_record(table_name, record_id)
        self._refresh_history_page()
        self.status_bar.showMessage(f"Record #{record_id} deleted from {table_name}.", 3000)

    # --- Feature 8: Comparison Page Controller ---

    def _refresh_comparison_page(self, locations: Optional[List[str]] = None):
        if locations:
            speed_tests = self.db.get_speed_tests_by_locations(locations)
            latency_tests = self.db.get_latency_tests_by_locations(locations)
            signal_logs = self.db.get_signal_logs_by_locations(locations)
        else:
            speed_tests = self.db.get_speed_tests(limit=100)
            latency_tests = self.db.get_latency_tests(limit=100)
            signal_logs = self.db.get_signal_logs(limit=200)
        self.page_comparison.display_comparison(speed_tests, latency_tests, signal_logs)

    # --- Feature 18: Academic Experiment Controller ---

    def start_experiment(
        self,
        experiment_id: str,
        condition_label: str,
        trials_count: int,
        target_host: str = "8.8.8.8",
        location_label: str = ""
    ):
        if self._closing:
            return
        if self.active_experiment_worker and self.active_experiment_worker.isRunning():
            return
        worker = ExperimentWorker(
            experiment_id=experiment_id,
            condition_label=condition_label,
            trials_count=trials_count,
            target_host=target_host,
            location_label=location_label or condition_label,
            db_manager=self.db
        )
        self.active_experiment_worker = worker
        worker.trial_finished.connect(self.page_experiment.add_trial_run)
        worker.experiment_finished.connect(self._on_experiment_finished)
        worker.start()
        self.status_bar.showMessage(f"Executing repeated experiment: {condition_label}")

    def stop_experiment(self):
        if self.active_experiment_worker and self.active_experiment_worker.isRunning():
            self.active_experiment_worker.abort()
        else:
            self.page_experiment.btn_run.setEnabled(True)
            self.page_experiment.btn_stop.setEnabled(False)

    def _on_experiment_finished(self, was_completed: bool):
        worker = self.active_experiment_worker
        if worker:
            worker.wait(500)
            worker.deleteLater()
            self.active_experiment_worker = None
        if self._closing:
            return
        self.page_experiment.experiment_completed(was_completed)
        self._load_saved_experiments()

    def _load_saved_experiments(self):
        """Fetches archived experiments from database and displays them."""
        exps = self.db.get_saved_experiments()
        self.page_experiment.display_saved_experiments(exps)

    # --- Feature 10: Reports Controller ---

    def _render_reports_recommendations(self, conn_info: ConnectedInterfaceInfo):
        speed = self.db.get_latest_speed_test()
        latency = self.db.get_latest_latency_test()
        channel_data = ChannelAnalyzer.analyze_channels(self.db.get_latest_networks())
        recs = RecommendationEngine.evaluate(conn_info, speed, latency, channel_data)
        self.page_reports.display_recommendations(recs)

    def _refresh_reports_page(self):
        conn_info = self._latest_conn_info or ConnectedInterfaceInfo(state="disconnected")
        self._render_reports_recommendations(conn_info)
        if self._latest_conn_info is None:
            self.refresh_dashboard_data()

    def export_pdf_report(self):
        conn_info = self._latest_conn_info or self.scanner.get_connected_interface()
        self._latest_conn_info = conn_info
        speed = self.db.get_latest_speed_test()
        latency = self.db.get_latest_latency_test()
        channel_data = ChannelAnalyzer.analyze_channels(self.db.get_latest_networks())
        recs = RecommendationEngine.evaluate(conn_info, speed, latency, channel_data)

        summary = {
            "ssid": conn_info.ssid or "Not Connected",
            "bssid": conn_info.bssid or "N/A",
            "signal": conn_info.signal_percent if conn_info.state == "connected" else None,
            "signal_category": "Good" if (conn_info.signal_percent or 0) >= 50 else "Poor",
            "channel": conn_info.channel,
            "band": conn_info.frequency_band,
            "ip": conn_info.ipv4_address,
            "gateway": conn_info.gateway or "Unavailable"
        }
        speed_tests = self.db.get_speed_tests(limit=20)
        latency_tests = self.db.get_latency_tests(limit=20)
        rec_dicts = [r.to_dict() for r in recs]

        try:
            pdf_path = ReportGenerator.export_pdf(
                summary_info=summary,
                speed_tests=speed_tests,
                latency_tests=latency_tests,
                recommendations=rec_dicts
            )
            self.page_reports.on_export_completed(pdf_path, "pdf")
        except Exception as e:
            logger.exception("PDF export failed")
            QMessageBox.critical(self, "PDF Export Error", f"Failed to generate PDF: {e}")

    def export_csv_report(self):
        speed_tests = self.db.get_speed_tests(limit=100)
        latency_tests = self.db.get_latency_tests(limit=100)
        signal_logs = self.db.get_signal_logs(limit=200)

        try:
            csv_path = ReportGenerator.export_csv(
                speed_tests=speed_tests,
                latency_tests=latency_tests,
                signal_logs=signal_logs
            )
            self.page_reports.on_export_completed(csv_path, "csv")
        except Exception as e:
            logger.exception("CSV export failed")
            QMessageBox.critical(self, "CSV Export Error", f"Failed to generate CSV: {e}")

    # --- Safe Shutdown ---

    def closeEvent(self, event: QCloseEvent):
        """Safely stops timers and terminates all background threads before exit."""
        self._closing = True
        self.page_dashboard.stop_timer()

        # Shutdown overlay and telemetry services
        if hasattr(self, "stats_collector") and self.stats_collector:
            self.stats_collector.clean_up()
        if hasattr(self, "shortcut_manager") and self.shortcut_manager:
            self.shortcut_manager.clean_up()
        if hasattr(self, "overlay_manager") and self.overlay_manager:
            self.overlay_manager.close_all()

        self.stop_signal_monitoring()
        self.stop_speed_test()
        self.stop_latency_test()
        self.stop_experiment()

        for attr in (
            "active_refresh_worker",
            "active_scan_worker",
            "active_speed_worker",
            "active_latency_worker",
            "active_experiment_worker",
        ):
            worker = getattr(self, attr, None)
            if worker is not None:
                if worker.isRunning():
                    worker.wait(3000)
                worker.deleteLater()
                setattr(self, attr, None)

        event.accept()
