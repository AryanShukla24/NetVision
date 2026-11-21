"""
NetVision - Signal Analyzer Page (Feature 3)
Tracks connected Wi-Fi radio signal percentage over time, plots a live time-series
graph, computes stability statistics, and logs samples tagged with custom locations.
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QGridLayout, QSpinBox
)
from PySide6.QtCore import Qt, Signal

from netvision.ui.components.cards import MetricCard
from netvision.ui.components.chart_widget import ChartWidget
from netvision.database.models import SignalLogEntry, ConnectedInterfaceInfo
from netvision.config import COLORS


class SignalPage(QWidget):
    """Signal Analyzer page with real-time continuous signal polling and stability analysis."""

    request_start_monitoring = Signal(str, int)  # location_label, interval_sec
    request_stop_monitoring = Signal()
    request_clear_history = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_monitoring = False
        self._sample_counter: int = 0
        self._x_indices: List[int] = []
        self._y_signals: List[int] = []
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Wi-Fi Signal & RF Stability Analyzer")
        title.setProperty("class", "PageTitle")
        subtitle = QLabel("Continuous signal strength sampling, stability deviation, and location logging")
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

        # Interval selector
        lbl_int = QLabel("Interval (sec):")
        lbl_int.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header_layout.addWidget(lbl_int)

        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(1, 10)
        self.spin_interval.setValue(2)
        header_layout.addWidget(self.spin_interval)

        # Start / Stop Toggle
        self.btn_toggle = QPushButton("▶  Start Monitoring")
        self.btn_toggle.setProperty("class", "PrimaryButton")
        self.btn_toggle.clicked.connect(self._on_toggle_clicked)
        header_layout.addWidget(self.btn_toggle)

        main_layout.addLayout(header_layout)

        # Metrics Strip
        grid = QGridLayout()
        grid.setSpacing(12)

        self.card_current = MetricCard("Current Signal", "--", "Active link percentage", "%")
        self.card_avg = MetricCard("Average Signal", "--", "Session mean", "%")
        self.card_std = MetricCard("Signal Stability", "--", "Std. deviation", "σ")
        self.card_range = MetricCard("Signal Spread", "--", "Min to Max swing", "%")

        grid.addWidget(self.card_current, 0, 0)
        grid.addWidget(self.card_avg, 0, 1)
        grid.addWidget(self.card_std, 0, 2)
        grid.addWidget(self.card_range, 0, 3)

        main_layout.addLayout(grid)

        # Chart Card
        chart_card = QFrame()
        chart_card.setProperty("class", "ContentCard")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(12, 12, 12, 12)

        chart_hdr = QHBoxLayout()
        self.lbl_chart_title = QLabel("Live Signal Fluctuation Over Time")
        self.lbl_chart_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #f8fafc;")
        chart_hdr.addWidget(self.lbl_chart_title)
        chart_hdr.addStretch()

        self.btn_clear = QPushButton("Clear History")
        self.btn_clear.setProperty("class", "SecondaryButton")
        self.btn_clear.clicked.connect(self.clear_chart)
        chart_hdr.addWidget(self.btn_clear)
        chart_layout.addLayout(chart_hdr)

        self.chart = ChartWidget(
            title="",
            xlabel="Sample Index",
            ylabel="Signal Quality (%)",
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
            loc = self.combo_location.currentText().strip() or "Default"
            interval = self.spin_interval.value()
            self.is_monitoring = True
            self.btn_toggle.setText("⏹  Stop Monitoring")
            self.btn_toggle.setProperty("class", "DangerButton")
            self.btn_toggle.setStyle(self.btn_toggle.style())  # Refresh stylesheet
            self.request_start_monitoring.emit(loc, interval)
        else:
            self.is_monitoring = False
            self.btn_toggle.setText("▶  Start Monitoring")
            self.btn_toggle.setProperty("class", "PrimaryButton")
            self.btn_toggle.setStyle(self.btn_toggle.style())
            self.request_stop_monitoring.emit()

    def add_signal_sample(self, entry: SignalLogEntry, stability: dict):
        """Receives a new signal entry from background worker and updates graph."""
        self._sample_counter += 1
        self._x_indices.append(self._sample_counter)
        self._y_signals.append(entry.signal_percent)

        # Keep last 50 points on graph for crisp responsiveness
        if len(self._x_indices) > 50:
            self._x_indices.pop(0)
            self._y_signals.pop(0)

        # Update cards
        self.card_current.set_value(str(entry.signal_percent), f"SSID: {entry.network_ssid}")
        self.card_avg.set_value(str(stability.get("mean", 0.0)), "Session average")
        self.card_std.set_value(str(stability.get("std_dev", 0.0)), stability.get("stability_label", "Unknown"))
        self.card_range.set_value(f"{stability.get('min', 0)} - {stability.get('max', 0)}", f"Range: {stability.get('range', 0)}%")

        # Re-plot
        self.chart.clear(xlabel="Sample Index", ylabel="Signal Quality (%)")
        self.chart.plot_line(
            self._x_indices,
            self._y_signals,
            label=f"{entry.network_ssid} ({entry.signal_percent}%)",
            color=COLORS["primary"],
            ylim=(0, 105)
        )

    def on_connection_changed(self, is_connected: bool, ssid: str):
        """Handles connection drop or reconnect during monitoring."""
        if not is_connected:
            self.lbl_chart_title.setText("Live Signal Fluctuation — Wi-Fi Disconnected")
            self.card_current.set_value("--", "Wi-Fi Disconnected")
        else:
            self.lbl_chart_title.setText(f"Live Signal Fluctuation — {ssid}")

    def clear_chart(self):
        """Resets the graph and in-memory sample points."""
        self._sample_counter = 0
        self._x_indices.clear()
        self._y_signals.clear()
        self.chart.clear(xlabel="Sample Index", ylabel="Signal Quality (%)")
        self.card_current.set_value("--", "")
        self.card_avg.set_value("--", "")
        self.card_std.set_value("--", "")
        self.card_range.set_value("--", "")
        self.request_clear_history.emit()
