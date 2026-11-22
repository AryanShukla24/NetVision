"""
NetVision - Latency and Jitter Monitor Page (Feature 5)
Performs real ICMP ping probes, tracks round-trip time (RTT), calculates min/max/average,
RFC 3550 jitter, and packet loss percentage with live charting.
"""

import math
from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QGridLayout, QSpinBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal

from netvision.ui.components.cards import MetricCard
from netvision.ui.components.chart_widget import ChartWidget
from netvision.database.models import LatencyTestResult
from netvision.config import DEFAULT_PING_TARGETS, COLORS


class LatencyPage(QWidget):
    """Latency, Jitter, and Packet Loss Monitor Page."""

    request_start_ping = Signal(str, int, str, str)  # host, count, location_label, method
    request_stop_ping = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_monitoring = False
        self._probe_indices: List[int] = []
        self._rtts: List[float] = []
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Round-Trip Latency & Jitter Monitor")
        title.setProperty("class", "PageTitle")
        subtitle = QLabel("ICMP probe latency, consecutive RTT jitter variance, and packet loss analysis")
        subtitle.setProperty("class", "PageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Target Selector
        lbl_target = QLabel("Target Host:")
        lbl_target.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header_layout.addWidget(lbl_target)

        self.combo_target = QComboBox()
        self.combo_target.setEditable(True)
        self.combo_target.setMinimumWidth(140)
        for t in DEFAULT_PING_TARGETS:
            self.combo_target.addItem(t["host"])
        header_layout.addWidget(self.combo_target)

        # Method Selector
        lbl_method = QLabel("Method:")
        lbl_method.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header_layout.addWidget(lbl_method)

        self.combo_method = QComboBox()
        self.combo_method.addItem("ICMP Ping", "ICMP")
        self.combo_method.addItem("TCP Connect (443)", "TCP_CONNECT")
        header_layout.addWidget(self.combo_method)

        # Probe count selector
        lbl_count = QLabel("Probes:")
        lbl_count.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header_layout.addWidget(lbl_count)

        self.spin_count = QSpinBox()
        self.spin_count.setRange(3, 100)
        self.spin_count.setValue(10)
        header_layout.addWidget(self.spin_count)

        # Location selector
        lbl_loc = QLabel("Location:")
        lbl_loc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header_layout.addWidget(lbl_loc)

        self.combo_location = QComboBox()
        self.combo_location.setEditable(True)
        self.combo_location.setMinimumWidth(120)
        header_layout.addWidget(self.combo_location)

        # Start / Stop Toggle
        self.btn_toggle = QPushButton("Start Probing")
        self.btn_toggle.setProperty("class", "PrimaryButton")
        self.btn_toggle.clicked.connect(self._on_toggle_clicked)
        header_layout.addWidget(self.btn_toggle)

        main_layout.addLayout(header_layout)

        # Progress Indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        main_layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Enter host or IP and click 'Start Probing'.")
        self.lbl_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        main_layout.addWidget(self.lbl_status)

        # Metric Cards (5 cards)
        grid = QGridLayout()
        grid.setSpacing(12)

        self.card_avg = MetricCard("Average Ping", "--", "Mean round-trip time", "ms")
        self.card_min = MetricCard("Minimum Latency", "--", "Best observed RTT", "ms")
        self.card_max = MetricCard("Maximum Latency", "--", "Peak RTT / Spike", "ms")
        self.card_jitter = MetricCard("Network Jitter", "--", "Consecutive RTT variance", "ms")
        self.card_loss = MetricCard("Packet Loss", "--", "Unanswered probe ratio", "%")

        grid.addWidget(self.card_avg, 0, 0)
        grid.addWidget(self.card_min, 0, 1)
        grid.addWidget(self.card_max, 0, 2)
        grid.addWidget(self.card_jitter, 0, 3)
        grid.addWidget(self.card_loss, 0, 4)

        main_layout.addLayout(grid)

        # Live Chart
        chart_card = QFrame()
        chart_card.setProperty("class", "ContentCard")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(12, 12, 12, 12)

        self.chart = ChartWidget(
            title="Probe Response Time (ms)",
            xlabel="Probe Sequence Number",
            ylabel="Round-Trip Time (ms)",
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

    def _on_toggle_clicked(self):
        if not self.is_monitoring:
            host = self.combo_target.currentText().strip() or "8.8.8.8"
            count = self.spin_count.value()
            loc = self.combo_location.currentText().strip() or "Default"
            method = self.combo_method.currentData() or "ICMP"
            self.is_monitoring = True
            self.btn_toggle.setText("Stop Probing")
            self.btn_toggle.setProperty("class", "DangerButton")
            self.btn_toggle.setStyle(self.btn_toggle.style())

            self._probe_indices.clear()
            self._rtts.clear()
            self.chart.clear(xlabel="Probe Sequence Number", ylabel="Round-Trip Time (ms)")
            self.progress_bar.setRange(0, count)
            self.progress_bar.setValue(0)
            self.lbl_status.setText(f"Sending {method} probes to {host}...")
            self.request_start_ping.emit(host, count, loc, method)
        else:
            self.btn_toggle.setEnabled(False)
            self.btn_toggle.setText("Stopping...")
            self.lbl_status.setText("Stopping latency probes...")
            self.request_stop_ping.emit()

    def add_probe_result(self, step: int, total: int, rtt: Optional[float]):
        """Live callback per ping probe."""
        self.progress_bar.setValue(step)
        self._probe_indices.append(step)

        if rtt is not None:
            self._rtts.append(rtt)
            self.lbl_status.setText(f"Probe {step}/{total}: Reply in {rtt} ms")
        else:
            self._rtts.append(float('nan'))  # NaN creates gap in matplotlib line, not zero
            self.lbl_status.setText(f"Probe {step}/{total}: Request timed out (Packet Lost)")

        # Update live chart
        self.chart.clear(xlabel="Probe Sequence Number", ylabel="Round-Trip Time (ms)")
        valid_rtts = [r for r in self._rtts if not math.isnan(r)]
        y_max = max(valid_rtts) * 1.3 if valid_rtts else 100.0

        self.chart.plot_line(
            self._probe_indices,
            self._rtts,
            label=f"RTT to {self.combo_target.currentText()}",
            color=COLORS["primary"],
            ylim=(0, max(50.0, y_max))
        )

    def display_final_result(self, result: LatencyTestResult):
        """Called upon completion of all probes."""
        self.is_monitoring = False
        self.btn_toggle.setEnabled(True)
        self.btn_toggle.setText("Start Probing")
        self.btn_toggle.setProperty("class", "PrimaryButton")
        self.btn_toggle.setStyle(self.btn_toggle.style())
        self.progress_bar.setValue(self.progress_bar.maximum())

        if result.avg_rtt_ms is not None:
            self.lbl_status.setText(
                f"Probing complete ({result.method}). Probes: {result.ping_count} | Avg RTT: {result.avg_rtt_ms:.1f} ms | "
                f"Loss: {result.packet_loss_percent:.1f}% | Jitter: {result.jitter_ms or 0.0:.1f} ms"
            )
            self.lbl_status.setStyleSheet(f"color: {COLORS['success']}; font-weight: 500;")
            self.card_avg.set_value(f"{result.avg_rtt_ms:.1f}", f"Target: {result.target_host}")
            self.card_min.set_value(f"{result.min_rtt_ms:.0f}" if result.min_rtt_ms is not None else "--", "Minimum RTT")
            self.card_max.set_value(f"{result.max_rtt_ms:.0f}" if result.max_rtt_ms is not None else "--", "Peak RTT")
            self.card_jitter.set_value(f"{result.jitter_ms:.1f}" if result.jitter_ms is not None else "No data", "Consecutive variation")
        else:
            self.lbl_status.setText(
                f"Probing completed with 100% packet loss to {result.target_host} ({result.method})."
            )
            self.lbl_status.setStyleSheet(f"color: {COLORS['danger']}; font-weight: 500;")
            self.card_avg.set_value("No data", f"Target: {result.target_host}")
            self.card_min.set_value("No data", "Minimum RTT")
            self.card_max.set_value("No data", "Peak RTT")
            self.card_jitter.set_value("No data", "Insufficient samples")

        loss_str = f"{result.packet_loss_percent:.1f}" if result.packet_loss_percent is not None else "No data"
        self.card_loss.set_value(loss_str, f"Lost: {loss_str}%")
