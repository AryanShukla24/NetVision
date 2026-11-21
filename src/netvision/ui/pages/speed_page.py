"""
NetVision - Network Speed Test Page (Feature 4)
Performs true internet bandwidth tests (Download & Upload Mbps, Ping RTT),
provides real-time progress indicators, and charts throughput history.
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QGridLayout, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from netvision.ui.components.cards import MetricCard
from netvision.ui.components.chart_widget import ChartWidget
from netvision.database.models import SpeedTestResult
from netvision.config import COLORS


class SpeedPage(QWidget):
    """Network Speed Test Page."""

    request_start_test = Signal(str)  # passes location_label
    request_stop_test = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_testing = False
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Network Speed & Bandwidth Test")
        title.setProperty("class", "PageTitle")
        subtitle = QLabel("Measure WAN download and upload throughput against verified CDN edge endpoints")
        subtitle.setProperty("class", "PageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Location selector
        lbl_loc = QLabel("Location Label:")
        lbl_loc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header_layout.addWidget(lbl_loc)

        self.combo_location = QComboBox()
        self.combo_location.setEditable(True)
        self.combo_location.setMinimumWidth(150)
        header_layout.addWidget(self.combo_location)

        # Start / Stop Buttons
        self.btn_start = QPushButton("🚀  Start Speed Test")
        self.btn_start.setProperty("class", "PrimaryButton")
        self.btn_start.clicked.connect(self._on_start_clicked)
        header_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("⏹  Stop Test")
        self.btn_stop.setProperty("class", "DangerButton")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        header_layout.addWidget(self.btn_stop)

        main_layout.addLayout(header_layout)

        # Progress Section
        progress_card = QFrame()
        progress_card.setProperty("class", "ContentCard")
        prog_layout = QVBoxLayout(progress_card)
        prog_layout.setContentsMargins(16, 12, 16, 12)

        self.lbl_phase = QLabel("Ready to test. Speeds depend on server, route, and network congestion.")
        self.lbl_phase.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; font-weight: 500;")
        prog_layout.addWidget(self.lbl_phase)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        prog_layout.addWidget(self.progress_bar)

        main_layout.addWidget(progress_card)

        # Metric Cards Grid
        grid = QGridLayout()
        grid.setSpacing(12)

        self.card_download = MetricCard("Download Speed", "--", "Active chunk throughput", "Mbps")
        self.card_upload = MetricCard("Upload Speed", "--", "Outbound stream throughput", "Mbps")
        self.card_ping = MetricCard("Latency (Ping)", "--", "Edge RTT", "ms")
        self.card_server = MetricCard("Target Edge Server", "--", "CDN Endpoint")

        grid.addWidget(self.card_download, 0, 0)
        grid.addWidget(self.card_upload, 0, 1)
        grid.addWidget(self.card_ping, 0, 2)
        grid.addWidget(self.card_server, 0, 3)

        main_layout.addLayout(grid)

        # Throughput Chart
        chart_card = QFrame()
        chart_card.setProperty("class", "ContentCard")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(12, 12, 12, 12)

        self.chart = ChartWidget(
            title="Download vs Upload Throughput Comparison",
            xlabel="Metric",
            ylabel="Throughput (Mbps)",
            parent=self
        )
        chart_layout.addWidget(self.chart)

        main_layout.addWidget(chart_card)

    def set_locations(self, locations: List[str]):
        """Populates the location combo box."""
        current = self.combo_location.currentText()
        self.combo_location.clear()
        self.combo_location.addItems(locations)
        if current in locations:
            self.combo_location.setCurrentText(current)

    def _on_start_clicked(self):
        loc = self.combo_location.currentText().strip() or "Default"
        self.is_testing = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)
        self.lbl_phase.setText("Initializing test connection...")
        self.request_start_test.emit(loc)

    def _on_stop_clicked(self):
        self.lbl_phase.setText("Cancelling test...")
        self.btn_stop.setEnabled(False)
        self.request_stop_test.emit()

    def update_progress(self, phase: str, percent: float, current_speed_mbps: float):
        """Called as test progresses."""
        self.lbl_phase.setText(f"{phase} ({percent:.0f}%)")
        self.progress_bar.setValue(int(percent))
        if "Download" in phase and current_speed_mbps > 0:
            self.card_download.set_value(f"{current_speed_mbps:.1f}", "Active transfer...")
        elif "Upload" in phase and current_speed_mbps > 0:
            self.card_upload.set_value(f"{current_speed_mbps:.1f}", "Active transfer...")

    def display_result(self, result: SpeedTestResult):
        """Called upon speed test finish."""
        self.is_testing = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.setValue(100 if result.status == "completed" else 0)

        if result.status == "completed":
            self.lbl_phase.setText(f"✓ Test completed successfully in {result.duration_sec or 0.0:.1f}s.")
            self.lbl_phase.setStyleSheet(f"color: {COLORS['success']}; font-weight: 600;")
            
            d_val = f"{result.download_mbps:.1f}" if result.download_mbps is not None else "—"
            u_val = f"{result.upload_mbps:.1f}" if result.upload_mbps is not None else "—"
            p_val = f"{result.ping_ms:.1f}" if result.ping_ms is not None else "—"
            
            self.card_download.set_value(d_val, "Completed")
            self.card_upload.set_value(u_val, "Completed")
            self.card_ping.set_value(p_val, "Server ping")
            self.card_server.set_value(result.server_name or "CDN Edge", f"Location: {result.location_label}")

            # Plot comparison bars only for non-null measurements
            cats = []
            vals = []
            if result.download_mbps is not None:
                cats.append("Download Speed")
                vals.append(result.download_mbps)
            if result.upload_mbps is not None:
                cats.append("Upload Speed")
                vals.append(result.upload_mbps)

            if cats:
                self.chart.plot_bars(
                    categories=cats,
                    values=vals,
                    title="Measured Throughput (Mbps)",
                    ylabel="Mbps",
                    colors=[COLORS["primary"], COLORS["purple"]][:len(cats)]
                )
        elif result.status == "cancelled":
            self.lbl_phase.setText("Test cancelled by user.")
            self.lbl_phase.setStyleSheet(f"color: {COLORS['warning']};")
            self.card_download.set_value("—", "Cancelled")
            self.card_upload.set_value("—", "Cancelled")
            self.card_ping.set_value("—", "Cancelled")
            self.card_server.set_value(result.server_name or "—", "Cancelled")
            self.chart.clear(title="Test Cancelled", ylabel="Mbps")
        else:
            self.lbl_phase.setText(f"Speed test error: {result.error_message or 'Measurement failed'}")
            self.lbl_phase.setStyleSheet(f"color: {COLORS['danger']};")
            self.card_download.set_value("—", "Failed")
            self.card_upload.set_value("—", "Failed")
            self.card_ping.set_value("—", "Failed")
            self.card_server.set_value("—", "Failed")
            self.chart.clear(title="Test Failed", ylabel="Mbps")
