"""
NetVision - Location-Based Comparison Page (Feature 8)
Compares empirical Wi-Fi signal, throughput, latency, and packet loss
across arbitrary user-selected locations without artificial sample limits.
Handles unequal sample counts, excludes failed runs, and never represents missing data as zero.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout,
    QListWidget, QListWidgetItem, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal

from netvision.ui.components.chart_widget import ChartWidget
from netvision.config import COLORS


class ComparisonPage(QWidget):
    """Location-based comparative performance dashboard."""

    request_refresh = Signal(list)  # passes list of selected location names

    def __init__(self, parent=None):
        super().__init__(parent)
        self.available_locations: List[str] = []
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Cross-Location Comparative Analytics")
        title.setProperty("class", "PageTitle")
        subtitle = QLabel("Multi-environment comparison of signal quality, download throughput, and latency across custom user locations")
        subtitle.setProperty("class", "PageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.setProperty("class", "SecondaryButton")
        self.btn_select_all.clicked.connect(self._select_all_locations)
        header_layout.addWidget(self.btn_select_all)

        self.btn_refresh = QPushButton("⟳ Compare Selected")
        self.btn_refresh.setProperty("class", "PrimaryButton")
        self.btn_refresh.clicked.connect(self._on_compare_clicked)
        header_layout.addWidget(self.btn_refresh)

        main_layout.addLayout(header_layout)

        # Location Selection Bar
        selector_card = QFrame()
        selector_card.setProperty("class", "ContentCard")
        sel_layout = QVBoxLayout(selector_card)
        sel_layout.setContentsMargins(14, 10, 14, 10)

        sel_hdr = QLabel("Select Locations to Include in Comparison:")
        sel_hdr.setStyleSheet("font-size: 13px; font-weight: 600; color: #f8fafc;")
        sel_layout.addWidget(sel_hdr)

        self.list_locations = QListWidget()
        self.list_locations.setSelectionMode(QAbstractItemView.NoSelection)
        self.list_locations.setMaximumHeight(85)
        self.list_locations.setStyleSheet(f"background-color: {COLORS['bg_dark']}; border: 1px solid {COLORS['border']}; border-radius: 6px;")
        sel_layout.addWidget(self.list_locations)

        main_layout.addWidget(selector_card)

        # Side-by-Side Comparison Charts Grid
        charts_grid = QGridLayout()
        charts_grid.setSpacing(14)

        self.chart_signal = ChartWidget(
            title="Average Signal Quality by Location (%)",
            xlabel="Location",
            ylabel="Signal Quality (%)",
            parent=self
        )
        self.chart_speed = ChartWidget(
            title="Average Download Throughput by Location (Mbps)",
            xlabel="Location",
            ylabel="Download (Mbps)",
            parent=self
        )
        self.chart_latency = ChartWidget(
            title="Average Round-Trip Latency by Location (ms - Lower is Better)",
            xlabel="Location",
            ylabel="Ping (ms)",
            parent=self
        )

        charts_grid.addWidget(self.chart_signal, 0, 0)
        charts_grid.addWidget(self.chart_speed, 0, 1)
        charts_grid.addWidget(self.chart_latency, 1, 0, 1, 2)

        main_layout.addLayout(charts_grid)

        # Comparative Summary Table with separate sample counts
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Location Label", "Signal Samples", "Avg Signal %",
            "Speed Tests", "Avg Download (Mbps)", "Avg Upload (Mbps)",
            "Ping Tests", "Avg Latency (ms)"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 8):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setMaximumHeight(180)

        main_layout.addWidget(self.table)

    def set_locations(self, locations: List[str]):
        """Populates the checkable locations list."""
        self.available_locations = locations
        self.list_locations.clear()
        for loc in locations:
            item = QListWidgetItem(loc)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.list_locations.addItem(item)

    def _select_all_locations(self):
        for i in range(self.list_locations.count()):
            self.list_locations.item(i).setCheckState(Qt.Checked)

    def get_selected_locations(self) -> List[str]:
        selected = []
        for i in range(self.list_locations.count()):
            item = self.list_locations.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.text())
        return selected

    def _on_compare_clicked(self):
        locs = self.get_selected_locations()
        self.request_refresh.emit(locs)

    def display_comparison(
        self,
        speed_tests: List[Dict[str, Any]],
        latency_tests: List[Dict[str, Any]],
        signal_logs: List[Dict[str, Any]],
        selected_locations: Optional[List[str]] = None
    ):
        """
        Aggregates metrics strictly by selected locations.
        Excludes failed runs, weights latency averages by probe count,
        and never graphs missing metrics as zero.
        """
        active_locs = selected_locations if selected_locations else self.get_selected_locations()
        if not active_locs:
            active_locs = self.available_locations

        loc_data = {
            loc: {
                "signals": [],
                "downloads": [],
                "uploads": [],
                "latency_weighted_sum": 0.0,
                "latency_probe_sum": 0,
                "latencies_raw": [],
                "losses": []
            }
            for loc in active_locs
        }

        # 1. Aggregate Signal Logs
        for s in signal_logs:
            loc = s.get("location_label")
            if loc in loc_data:
                sig = s.get("signal_percent")
                if sig is not None and sig > 0:
                    loc_data[loc]["signals"].append(sig)

        # 2. Aggregate Speed Tests (only completed tests)
        for sp in speed_tests:
            loc = sp.get("location_label")
            if loc in loc_data and sp.get("status") == "completed":
                d = sp.get("download_mbps")
                u = sp.get("upload_mbps")
                if d is not None:
                    loc_data[loc]["downloads"].append(d)
                if u is not None:
                    loc_data[loc]["uploads"].append(u)

        # 3. Aggregate Latency Tests (weighted by probe count)
        for l in latency_tests:
            loc = l.get("location_label")
            if loc in loc_data and l.get("status") == "completed":
                avg_rtt = l.get("avg_rtt_ms")
                probes = l.get("ping_count", 1) or 1
                loss = l.get("packet_loss_percent")

                if avg_rtt is not None and probes > 0:
                    loc_data[loc]["latency_weighted_sum"] += (avg_rtt * probes)
                    loc_data[loc]["latency_probe_sum"] += probes
                    loc_data[loc]["latencies_raw"].append(avg_rtt)
                if loss is not None:
                    loc_data[loc]["losses"].append(loss)

        # Prepare Chart Data (Omit locations with NO data from bars so they never show fake 0 bars)
        sorted_locs = sorted(loc_data.keys())

        # Signal Chart
        sig_locs = []
        sig_vals = []
        for loc in sorted_locs:
            s_list = loc_data[loc]["signals"]
            if s_list:
                sig_locs.append(loc)
                sig_vals.append(round(sum(s_list) / len(s_list), 1))

        if sig_locs:
            self.chart_signal.plot_bars(
                categories=sig_locs,
                values=sig_vals,
                title="Avg Wi-Fi Signal Quality (%)",
                ylabel="Signal %",
                colors=[COLORS["primary"]] * len(sig_locs)
            )
        else:
            self.chart_signal.clear(title="No signal records for selected locations", ylabel="%")

        # Download Speed Chart
        spd_locs = []
        spd_vals = []
        for loc in sorted_locs:
            d_list = loc_data[loc]["downloads"]
            if d_list:
                spd_locs.append(loc)
                spd_vals.append(round(sum(d_list) / len(d_list), 1))

        if spd_locs:
            self.chart_speed.plot_bars(
                categories=spd_locs,
                values=spd_vals,
                title="Avg WAN Download Speed (Mbps)",
                ylabel="Download (Mbps)",
                colors=[COLORS["success"]] * len(spd_locs)
            )
        else:
            self.chart_speed.clear(title="No speed test records for selected locations", ylabel="Mbps")

        # Latency Chart
        lat_locs = []
        lat_vals = []
        for loc in sorted_locs:
            d = loc_data[loc]
            if d["latency_probe_sum"] > 0:
                weighted_avg = d["latency_weighted_sum"] / d["latency_probe_sum"]
                lat_locs.append(loc)
                lat_vals.append(round(weighted_avg, 1))

        if lat_locs:
            self.chart_latency.plot_bars(
                categories=lat_locs,
                values=lat_vals,
                title="Avg Latency (ms - Lower is Better)",
                ylabel="Ping (ms)",
                colors=[COLORS["warning"]] * len(lat_locs)
            )
        else:
            self.chart_latency.clear(title="No latency records for selected locations", ylabel="ms")

        # Populate Summary Table with separate sample counts
        self.table.setRowCount(len(sorted_locs))
        for row, loc in enumerate(sorted_locs):
            d = loc_data[loc]
            sig_cnt = len(d["signals"])
            sig_avg = f"{sum(d['signals']) / sig_cnt:.1f}%" if sig_cnt > 0 else "—"

            spd_cnt = len(d["downloads"])
            down_avg = f"{sum(d['downloads']) / spd_cnt:.1f} Mbps" if spd_cnt > 0 else "—"
            up_avg = f"{sum(d['uploads']) / len(d['uploads']):.1f} Mbps" if d["uploads"] else "—"

            lat_cnt = len(d["latencies_raw"])
            if d["latency_probe_sum"] > 0:
                lat_avg = f"{(d['latency_weighted_sum'] / d['latency_probe_sum']):.1f} ms"
            else:
                lat_avg = "—"

            self.table.setItem(row, 0, QTableWidgetItem(loc))
            self.table.setItem(row, 1, QTableWidgetItem(str(sig_cnt)))
            self.table.setItem(row, 2, QTableWidgetItem(sig_avg))
            self.table.setItem(row, 3, QTableWidgetItem(str(spd_cnt)))
            self.table.setItem(row, 4, QTableWidgetItem(down_avg))
            self.table.setItem(row, 5, QTableWidgetItem(up_avg))
            self.table.setItem(row, 6, QTableWidgetItem(str(lat_cnt)))
            self.table.setItem(row, 7, QTableWidgetItem(lat_avg))
