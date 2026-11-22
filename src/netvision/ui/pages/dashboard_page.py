"""
NetVision - Dashboard Page (Feature 1)
Displays active connection status, physical link metrics, IP address,
latest speed and latency measurements, and quick-test trigger.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer

from netvision.ui.components.cards import MetricCard
from netvision.ui.components.status_pill import StatusPill
from netvision.database.models import ConnectedInterfaceInfo, SpeedTestResult, LatencyTestResult
from netvision.config import COLORS


class DashboardPage(QWidget):
    """Main dashboard page."""

    request_refresh = Signal()
    request_quick_test = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._setup_timer()

    def _setup_timer(self):
        """Auto-refresh link details every 5 seconds while Dashboard is active."""
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(5000)
        self._refresh_timer.timeout.connect(self.request_refresh.emit)
        self._refresh_timer.start()

    def set_auto_refresh_active(self, active: bool):
        """Starts or pauses the periodic dashboard refresh timer."""
        if active:
            if not self._refresh_timer.isActive():
                self._refresh_timer.start()
        else:
            if self._refresh_timer.isActive():
                self._refresh_timer.stop()

    def stop_timer(self):
        """Stops the auto-refresh timer permanently on shutdown."""
        if self._refresh_timer.isActive():
            self._refresh_timer.stop()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Header Row
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Network Status & Health Overview")
        title.setProperty("class", "PageTitle")
        subtitle = QLabel("Real-time physical link parameters and latest performance metrics")
        subtitle.setProperty("class", "PageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_refresh = QPushButton("Refresh Link")
        self.btn_refresh.setProperty("class", "SecondaryButton")
        self.btn_refresh.clicked.connect(self.request_refresh.emit)
        header_layout.addWidget(self.btn_refresh)

        self.btn_quick_test = QPushButton("Quick Test")
        self.btn_quick_test.setProperty("class", "PrimaryButton")
        self.btn_quick_test.clicked.connect(self.request_quick_test.emit)
        header_layout.addWidget(self.btn_quick_test)

        main_layout.addLayout(header_layout)

        # Hero Banner: Active Connection Status
        hero_card = QFrame()
        hero_card.setProperty("class", "ContentCard")
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(18, 14, 18, 14)

        left_hero = QVBoxLayout()
        self.lbl_connected_ssid = QLabel("Connected: Scanning...")
        self.lbl_connected_ssid.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {COLORS['text_bright']};")
        self.lbl_details = QLabel("Interface: Unknown | Band: Unknown | Channel: -- | IP: --")
        self.lbl_details.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        left_hero.addWidget(self.lbl_connected_ssid)
        left_hero.addWidget(self.lbl_details)
        hero_layout.addLayout(left_hero)

        hero_layout.addStretch()

        right_hero = QVBoxLayout()
        right_hero.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_pill = StatusPill("Disconnected")
        right_hero.addWidget(self.status_pill)
        hero_layout.addLayout(right_hero)

        main_layout.addWidget(hero_card)

        # Metric Cards Grid (6 cards)
        grid = QGridLayout()
        grid.setSpacing(12)

        self.card_signal = MetricCard("Wi-Fi Signal Quality", "--", "Signal quality (%)", "%")
        self.card_download = MetricCard("Download Speed", "Not tested", "Latest WAN Throughput", "Mbps")
        self.card_upload = MetricCard("Upload Speed", "Not tested", "Latest Uplink Throughput", "Mbps")
        self.card_latency = MetricCard("Round-Trip Ping", "Not tested", "Average RTT to Target", "ms")
        self.card_jitter = MetricCard("Network Jitter", "Not tested", "RTT Variation Stability", "ms")
        self.card_loss = MetricCard("Packet Loss", "Not tested", "Unanswered Probe Ratio", "%")

        grid.addWidget(self.card_signal, 0, 0)
        grid.addWidget(self.card_download, 0, 1)
        grid.addWidget(self.card_upload, 0, 2)
        grid.addWidget(self.card_latency, 1, 0)
        grid.addWidget(self.card_jitter, 1, 1)
        grid.addWidget(self.card_loss, 1, 2)

        main_layout.addLayout(grid)

        # Technical Details Card
        tech_card = QFrame()
        tech_card.setProperty("class", "ContentCard")
        tech_layout = QVBoxLayout(tech_card)
        tech_title = QLabel("Active Radio & Gateway Parameters")
        tech_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {COLORS['text_bright']};")
        tech_layout.addWidget(tech_title)

        tech_grid = QGridLayout()
        tech_grid.setContentsMargins(0, 10, 0, 0)
        tech_grid.setHorizontalSpacing(30)
        tech_grid.setVerticalSpacing(8)

        self.lbl_bssid = QLabel("BSSID: --")
        self.lbl_radio = QLabel("Radio Standard: --")
        self.lbl_security = QLabel("Security: --")
        self.lbl_rx_rate = QLabel("Receive Link Rate: --")
        self.lbl_tx_rate = QLabel("Transmit Link Rate: --")
        self.lbl_ip = QLabel("Local IPv4: --")
        self.lbl_gateway = QLabel("Default Gateway: --")
        self.lbl_dns = QLabel("DNS Servers: --")

        for lbl in (self.lbl_bssid, self.lbl_radio, self.lbl_security, self.lbl_rx_rate, self.lbl_tx_rate, self.lbl_ip, self.lbl_gateway, self.lbl_dns):
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")

        tech_grid.addWidget(self.lbl_bssid, 0, 0)
        tech_grid.addWidget(self.lbl_radio, 0, 1)
        tech_grid.addWidget(self.lbl_security, 1, 0)
        tech_grid.addWidget(self.lbl_rx_rate, 1, 1)
        tech_grid.addWidget(self.lbl_tx_rate, 2, 0)
        tech_grid.addWidget(self.lbl_ip, 2, 1)
        tech_grid.addWidget(self.lbl_gateway, 3, 0)
        tech_grid.addWidget(self.lbl_dns, 3, 1)

        tech_layout.addLayout(tech_grid)
        main_layout.addWidget(tech_card)

        main_layout.addStretch()

    def update_interface_info(self, info: ConnectedInterfaceInfo):
        """Updates UI with parsed Wi-Fi interface details."""
        if info.state == "connected" and info.ssid:
            self.lbl_connected_ssid.setText(f"Connected: {info.ssid}")
            self.lbl_details.setText(
                f"Interface: {info.interface_name} | Band: {info.frequency_band} | "
                f"Channel: {info.channel} | IP: {info.ipv4_address}"
            )
            # Signal category & status pill
            if info.signal_percent >= 75:
                status = "Excellent"
            elif info.signal_percent >= 50:
                status = "Good"
            elif info.signal_percent >= 30:
                status = "Fair"
            else:
                status = "Poor"

            self.status_pill.setStatus(status)
            self.card_signal.set_value(str(info.signal_percent), f"Category: {status}")
            self.lbl_bssid.setText(f"BSSID: {info.bssid or 'Unknown'}")
            self.lbl_radio.setText(f"Radio Standard: {info.radio_type or 'Unknown'}")
            self.lbl_security.setText(f"Security: {info.authentication or 'Unknown'} / {info.cipher}")
            self.lbl_rx_rate.setText(f"Receive Link Rate: {info.receive_rate_mbps} Mbps")
            self.lbl_tx_rate.setText(f"Transmit Link Rate: {info.transmit_rate_mbps} Mbps")
            self.lbl_ip.setText(f"Local IPv4: {info.ipv4_address}")
            self.lbl_gateway.setText(f"Default Gateway: {info.gateway or 'Unavailable'}")
            dns_str = ", ".join(info.dns_servers) if info.dns_servers else "Unavailable"
            self.lbl_dns.setText(f"DNS Servers: {dns_str}")
        else:
            self.lbl_connected_ssid.setText("Wi-Fi Interface Disconnected")
            self.lbl_details.setText(f"Local IPv4: {info.ipv4_address} (Offline / Disconnected)")
            self.status_pill.setStatus("Disconnected")
            self.card_signal.set_value("--", "No connection")
            self.lbl_bssid.setText("BSSID: --")
            self.lbl_radio.setText("Radio Standard: --")
            self.lbl_security.setText("Security: --")
            self.lbl_rx_rate.setText("Receive Link Rate: --")
            self.lbl_tx_rate.setText("Transmit Link Rate: --")
            self.lbl_ip.setText(f"Local IPv4: {info.ipv4_address}")
            self.lbl_gateway.setText(f"Default Gateway: {info.gateway or 'Unavailable'}")
            self.lbl_dns.setText("DNS Servers: --")

    def update_latest_tests(self, speed: SpeedTestResult = None, latency: LatencyTestResult = None):
        """Updates card values from database historical records."""
        if speed and speed.status == "completed":
            down_str = f"{speed.download_mbps:.1f}" if speed.download_mbps is not None else "--"
            up_str = f"{speed.upload_mbps:.1f}" if speed.upload_mbps is not None else "--"
            ts_sub = f"Server: {speed.server_name}"
            if speed.timestamp:
                ts_sub += f" ({speed.timestamp[:16]})"
            self.card_download.set_value(down_str, ts_sub)
            self.card_upload.set_value(up_str, f"Duration: {speed.duration_sec}s")
        else:
            self.card_download.set_value("Not tested", "Run speed test to measure")
            self.card_upload.set_value("Not tested", "Run speed test to measure")

        if latency and latency.status == "completed":
            rtt_str = f"{latency.avg_rtt_ms:.1f}" if latency.avg_rtt_ms is not None else "No data"
            jit_str = f"{latency.jitter_ms:.1f}" if latency.jitter_ms is not None else "No data"
            loss_str = f"{latency.packet_loss_percent:.1f}" if latency.packet_loss_percent is not None else "No data"
            
            ts_sub = f"Host: {latency.target_host} ({latency.method})"
            if latency.timestamp:
                ts_sub += f" • {latency.timestamp[:16]}"
                
            self.card_latency.set_value(rtt_str, ts_sub)
            self.card_jitter.set_value(jit_str, "RFC 3550 interarrival jitter")
            self.card_loss.set_value(loss_str, f"Probes: {latency.ping_count}")
        elif latency and latency.status == "failed":
            self.card_latency.set_value("No data", f"Failed ({latency.target_host})")
            self.card_jitter.set_value("No data", "")
            self.card_loss.set_value("100.0", f"Probes: {latency.ping_count} (100% loss)")
        else:
            self.card_latency.set_value("Not tested", "Run latency test to measure")
            self.card_jitter.set_value("Not tested", "")
            self.card_loss.set_value("Not tested", "")

    def update_live_telemetry(self, snapshot: dict):
        """Consumes centralized telemetry from StatisticsCollector."""
        # Live Wi-Fi signal
        wifi = snapshot.get("wifi_signal", {})
        val = wifi.get("val")
        disp = wifi.get("display", "")
        if val is not None:
            status = "Good" if val >= 50 else ("Fair" if val >= 30 else "Poor")
            self.card_signal.set_value(str(int(val)), f"Live RF: {disp}")
            self.status_pill.setStatus(status)
        elif "Ethernet" in disp:
            self.card_signal.set_value("Wired", "Ethernet connection active")
            self.status_pill.setStatus("Good")

        # Live Ping & Jitter
        ping = snapshot.get("ping", {})
        ping_val = ping.get("val")
        if ping_val is not None and self.card_latency.value_label.text() in ("--", "Not tested", "No data"):
            self.card_latency.set_value(f"{ping_val:.1f}", "Live ICMP gateway")

        jitter = snapshot.get("jitter", {})
        jit_val = jitter.get("val")
        if jit_val is not None and jit_val > 0 and self.card_jitter.value_label.text() in ("--", "Not tested", "No data"):
            self.card_jitter.set_value(f"{jit_val:.1f}", "RFC 3550 interarrival jitter")

        loss = snapshot.get("packet_loss", {})
        loss_val = loss.get("val")
        if loss_val is not None and self.card_loss.value_label.text() in ("--", "Not tested", "No data"):
            self.card_loss.set_value(f"{loss_val:.1f}", "Probe window loss")
