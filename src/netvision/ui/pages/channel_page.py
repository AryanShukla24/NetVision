"""
NetVision - Wi-Fi Channel Analyzer Page (Feature 6)
Analyzes RF channel occupancy, co-channel interference, and visualizes crowded channels
with non-overlapping channel recommendations for both 2.4 GHz and 5 GHz bands.
"""

from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from netvision.ui.components.chart_widget import ChartWidget
from netvision.config import COLORS


class ChannelPage(QWidget):
    """Channel Analyzer page displaying 2.4 GHz and 5 GHz RF channel distributions."""

    request_refresh = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Wi-Fi Spectrum & Channel Congestion Analyzer")
        title.setProperty("class", "PageTitle")
        subtitle = QLabel("Airtime distribution, co-channel interference detection, and evidence-based recommendations")
        subtitle.setProperty("class", "PageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_refresh = QPushButton("Analyze Spectrum")
        self.btn_refresh.setProperty("class", "PrimaryButton")
        self.btn_refresh.clicked.connect(self.request_refresh.emit)
        header_layout.addWidget(self.btn_refresh)

        main_layout.addLayout(header_layout)

        # Recommendation Banner Card
        self.banner_card = QFrame()
        self.banner_card.setProperty("class", "ContentCard")
        banner_layout = QVBoxLayout(self.banner_card)
        banner_layout.setContentsMargins(16, 12, 16, 12)

        self.lbl_rec_title = QLabel("RF Channel Optimization Advice")
        self.lbl_rec_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {COLORS['primary']};")
        self.lbl_rec_body = QLabel(
            "Scan nearby networks to discover which Wi-Fi channels have the least co-channel interference. "
            "Note: Actual channel switching must be performed via your router's administration web interface."
        )
        self.lbl_rec_body.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        self.lbl_rec_body.setWordWrap(True)

        self.lbl_disclaimer = QLabel(
            "<b>Hardware Scope Disclaimer:</b> NetVision evaluates 802.11 beacon frames via the standard OS Wi-Fi adapter. "
            "It cannot detect non-802.11 RF energy (such as microwave ovens, Bluetooth frequency hopping, or analog cameras)."
        )
        self.lbl_disclaimer.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; margin-top: 4px;")
        self.lbl_disclaimer.setWordWrap(True)

        banner_layout.addWidget(self.lbl_rec_title)
        banner_layout.addWidget(self.lbl_rec_body)
        banner_layout.addWidget(self.lbl_disclaimer)
        main_layout.addWidget(self.banner_card)

        # Tab Widget for 2.4 GHz vs 5 GHz
        self.tabs = QTabWidget()

        # Tab 1: 2.4 GHz
        tab_24 = QWidget()
        l_24 = QVBoxLayout(tab_24)
        l_24.setContentsMargins(12, 12, 12, 12)
        self.chart_24 = ChartWidget(
            title="2.4 GHz Channels (Non-Overlapping: 1, 6, 11)",
            xlabel="Wi-Fi Channel Number",
            ylabel="Discovered Access Points",
            parent=self
        )
        l_24.addWidget(self.chart_24)

        self.table_24 = self._create_channel_table()
        l_24.addWidget(self.table_24)
        self.tabs.addTab(tab_24, "2.4 GHz Spectrum")

        # Tab 2: 5 GHz
        tab_5 = QWidget()
        l_5 = QVBoxLayout(tab_5)
        l_5.setContentsMargins(12, 12, 12, 12)
        self.chart_5 = ChartWidget(
            title="5 GHz Channels (36, 40, 44, 48, 149, 153, etc.)",
            xlabel="Wi-Fi Channel Number",
            ylabel="Discovered Access Points",
            parent=self
        )
        l_5.addWidget(self.chart_5)

        self.table_5 = self._create_channel_table()
        l_5.addWidget(self.table_5)
        self.tabs.addTab(tab_5, "5 GHz Spectrum")

        main_layout.addWidget(self.tabs)

    def _create_channel_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Channel", "Active APs", "Congestion Level", "Average Signal", "SSIDs on Channel"])
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setMaximumHeight(160)
        return table

    def display_analysis(self, analysis_result: Dict[str, Any]):
        """Renders channel analysis data into charts and tables."""
        band_24 = analysis_result.get("band_24", {})
        band_5 = analysis_result.get("band_5", {})

        # Check for empty data
        has_24 = band_24.get("has_data", True)
        has_5 = band_5.get("has_data", True)

        if not has_24 and not has_5:
            self.lbl_rec_body.setText(
                "<b>No Wi-Fi scan data available:</b> Trigger an active scan or ensure your wireless interface is connected."
            )
            self.chart_24.clear(title="2.4 GHz Spectrum (No Data)")
            self.chart_5.clear(title="5 GHz Spectrum (No Data)")
            self.table_24.setRowCount(0)
            self.table_5.setRowCount(0)
            return

        # Update Banner
        rec_24 = band_24.get("recommended_channel")
        rec_5 = band_5.get("recommended_channel")
        reason_24 = band_24.get("reasoning", "")
        reason_5 = band_5.get("reasoning", "5 GHz provides wider non-overlapping channels.")
        
        rec_24_str = f"Channel {rec_24}" if rec_24 else "No data"
        rec_5_str = f"Channel {rec_5}" if rec_5 else "No data"

        self.lbl_rec_body.setText(
            f"<b>2.4 GHz Recommendation:</b> {rec_24_str}. {reason_24}<br/>"
            f"<b>5 GHz Recommendation:</b> {rec_5_str}. {reason_5}"
        )

        # 2.4 GHz Chart & Table
        ch_data_24 = band_24.get("channels", [])
        if ch_data_24:
            cats_24 = [f"Ch {c['channel']}" for c in ch_data_24]
            vals_24 = [c["count"] for c in ch_data_24]
            colors_24 = [
                COLORS["danger"] if c["count"] > 3 else (
                    COLORS["warning"] if c["count"] > 1 else COLORS["success"]
                ) for c in ch_data_24
            ]
            self.chart_24.plot_bars(
                cats_24, vals_24,
                title="2.4 GHz AP Distribution (Lower is Better)",
                xlabel="Channel",
                ylabel="Number of Networks",
                colors=colors_24
            )
        else:
            self.chart_24.clear(title="2.4 GHz Spectrum (No 2.4 GHz Networks Found)")
        self._populate_table(self.table_24, ch_data_24)

        # 5 GHz Chart & Table
        ch_data_5 = band_5.get("channels", [])
        if ch_data_5:
            cats_5 = [f"Ch {c['channel']}" for c in ch_data_5]
            vals_5 = [c["count"] for c in ch_data_5]
            colors_5 = [
                COLORS["danger"] if c["count"] > 3 else (
                    COLORS["warning"] if c["count"] > 1 else COLORS["success"]
                ) for c in ch_data_5
            ]
            self.chart_5.plot_bars(
                cats_5, vals_5,
                title="5 GHz AP Distribution (Lower is Better)",
                xlabel="Channel",
                ylabel="Number of Networks",
                colors=colors_5
            )
        else:
            self.chart_5.clear(title="5 GHz Spectrum (No 5 GHz Networks Found)")
        self._populate_table(self.table_5, ch_data_5)

    def _populate_table(self, table: QTableWidget, data: List[Dict[str, Any]]):
        table.setRowCount(len(data))
        for row, item in enumerate(data):
            ch_item = QTableWidgetItem(f"Channel {item['channel']}")
            cnt_item = QTableWidgetItem(str(item["count"]))
            cong_item = QTableWidgetItem(item["congestion"])

            if item["congestion"] == "Clear":
                cong_item.setForeground(QColor(COLORS["success"]))
            elif item["congestion"] == "Low":
                cong_item.setForeground(QColor(COLORS["primary"]))
            elif item["congestion"] == "Moderate":
                cong_item.setForeground(QColor(COLORS["warning"]))
            else:
                cong_item.setForeground(QColor(COLORS["danger"]))

            sig_str = f"{item['avg_signal']}%" if item.get('avg_signal') is not None else "—"
            sig_item = QTableWidgetItem(sig_str)
            ssids_item = QTableWidgetItem(", ".join(item["networks"][:5]) if item.get("networks") else "None")

            table.setItem(row, 0, ch_item)
            table.setItem(row, 1, cnt_item)
            table.setItem(row, 2, cong_item)
            table.setItem(row, 3, sig_item)
            table.setItem(row, 4, ssids_item)
