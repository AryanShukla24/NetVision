"""
NetVision - History & Analytics Page (Feature 7)
Displays historical speed tests, latency probes, and signal observations from SQLite.
Provides filtering by date/location/network, time-series trend charts, and record deletion.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox, QTabWidget, QDateEdit, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QDate

from netvision.ui.components.chart_widget import ChartWidget
from netvision.config import COLORS


class HistoryPage(QWidget):
    """History and Analytics page."""

    request_refresh = Signal()
    request_delete_record = Signal(str, int)  # table_name, record_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.raw_speed_data: List[Dict[str, Any]] = []
        self.raw_latency_data: List[Dict[str, Any]] = []
        self.raw_signal_data: List[Dict[str, Any]] = []
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Historical Analytics & Telemetry Archive")
        title.setProperty("class", "PageTitle")
        subtitle = QLabel("Persistent SQLite audit records of past speed tests, latency checks, and RF signals")
        subtitle.setProperty("class", "PageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_refresh = QPushButton("⟳  Refresh Records")
        self.btn_refresh.setProperty("class", "SecondaryButton")
        self.btn_refresh.clicked.connect(self.request_refresh.emit)
        header_layout.addWidget(self.btn_refresh)

        main_layout.addLayout(header_layout)

        # Filter Bar
        filter_bar = QFrame()
        filter_bar.setProperty("class", "ContentCard")
        f_layout = QHBoxLayout(filter_bar)
        f_layout.setContentsMargins(12, 10, 12, 10)
        f_layout.setSpacing(10)

        lbl_filter = QLabel("Search:")
        lbl_filter.setStyleSheet(f"color: {COLORS['text_secondary']};")
        f_layout.addWidget(lbl_filter)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Search by SSID, Location, or Server...")
        self.input_search.textChanged.connect(self._apply_filters)
        f_layout.addWidget(self.input_search)

        lbl_loc = QLabel("Location:")
        lbl_loc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        f_layout.addWidget(lbl_loc)

        self.combo_loc_filter = QComboBox()
        self.combo_loc_filter.addItem("All Locations")
        self.combo_loc_filter.currentIndexChanged.connect(self._apply_filters)
        f_layout.addWidget(self.combo_loc_filter)

        # Date Range Filter
        self.chk_date_filter = QCheckBox("Date Filter:")
        self.chk_date_filter.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.chk_date_filter.toggled.connect(self._apply_filters)
        f_layout.addWidget(self.chk_date_filter)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.dateChanged.connect(self._apply_filters)
        f_layout.addWidget(self.date_from)

        lbl_to = QLabel("to")
        lbl_to.setStyleSheet(f"color: {COLORS['text_muted']};")
        f_layout.addWidget(lbl_to)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate().addDays(1))
        self.date_to.dateChanged.connect(self._apply_filters)
        f_layout.addWidget(self.date_to)

        main_layout.addWidget(filter_bar)

        # Trend Chart
        chart_card = QFrame()
        chart_card.setProperty("class", "ContentCard")
        c_layout = QVBoxLayout(chart_card)
        c_layout.setContentsMargins(10, 10, 10, 10)
        self.chart = ChartWidget(
            title="Download Speed & Latency History",
            xlabel="Test Index",
            ylabel="Metrics",
            parent=self
        )
        c_layout.addWidget(self.chart)
        main_layout.addWidget(chart_card)

        # Tabbed Tables: Speed Tests / Latency Tests / Signal Logs
        self.tabs = QTabWidget()

        # Tab 1: Speed Tests Table
        self.table_speed = self._create_table(["ID", "Timestamp", "Location", "SSID", "Download (Mbps)", "Upload (Mbps)", "Ping (ms)", "Status", "Actions"])
        self.tabs.addTab(self.table_speed, "Speed Tests")

        # Tab 2: Latency Tests Table
        self.table_latency = self._create_table(["ID", "Timestamp", "Location", "Target Host", "Method", "Avg RTT (ms)", "Jitter (ms)", "Loss (%)", "Status", "Actions"])
        self.tabs.addTab(self.table_latency, "Latency & Ping Tests")

        # Tab 3: Signal Logs Table
        self.table_signal = self._create_table(["ID", "Timestamp", "Location", "SSID", "Signal %", "Channel", "Band", "Actions"])
        self.tabs.addTab(self.table_signal, "Signal Logs")

        main_layout.addWidget(self.tabs)

    def _create_table(self, headers: List[str]) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for i in range(len(headers)):
            if i != 1:
                table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        return table

    def set_locations(self, locations: List[str]):
        """Populates the location filter dropdown."""
        curr = self.combo_loc_filter.currentText()
        self.combo_loc_filter.clear()
        self.combo_loc_filter.addItem("All Locations")
        self.combo_loc_filter.addItems(locations)
        if curr in locations:
            self.combo_loc_filter.setCurrentText(curr)

    def update_history_data(
        self,
        speed_tests: List[Dict[str, Any]],
        latency_tests: List[Dict[str, Any]],
        signal_logs: List[Dict[str, Any]]
    ):
        """Sets data from DB and updates views."""
        self.raw_speed_data = speed_tests
        self.raw_latency_data = latency_tests
        self.raw_signal_data = signal_logs
        self._apply_filters()

    def _apply_filters(self):
        query = self.input_search.text().strip().lower()
        selected_loc = self.combo_loc_filter.currentText()
        use_date = self.chk_date_filter.isChecked()
        from_str = self.date_from.date().toString("yyyy-MM-dd")
        to_str = self.date_to.date().toString("yyyy-MM-dd")

        def match(row: Dict[str, Any]) -> bool:
            if selected_loc != "All Locations":
                if row.get("location_label") != selected_loc:
                    return False
            if use_date:
                ts = str(row.get("timestamp", ""))[:10]
                if ts and (ts < from_str or ts > to_str):
                    return False
            if query:
                combined = " ".join(str(v) for v in row.values()).lower()
                return query in combined
            return True

        filtered_speed = [r for r in self.raw_speed_data if match(r)]
        filtered_latency = [r for r in self.raw_latency_data if match(r)]
        filtered_signal = [r for r in self.raw_signal_data if match(r)]

        self._populate_speed_table(filtered_speed)
        self._populate_latency_table(filtered_latency)
        self._populate_signal_table(filtered_signal)
        self._update_trend_chart(filtered_speed)

    def _populate_speed_table(self, rows: List[Dict[str, Any]]):
        self.table_speed.setRowCount(len(rows))
        for r_idx, r in enumerate(rows):
            rec_id = r["id"]
            d_str = f"{r['download_mbps']:.1f}" if r.get('download_mbps') is not None else "—"
            u_str = f"{r['upload_mbps']:.1f}" if r.get('upload_mbps') is not None else "—"
            p_str = f"{r['ping_ms']:.1f}" if r.get('ping_ms') is not None else "—"
            status = r.get("status", "completed")

            self.table_speed.setItem(r_idx, 0, QTableWidgetItem(str(rec_id)))
            self.table_speed.setItem(r_idx, 1, QTableWidgetItem(r.get("timestamp", "")[:19].replace("T", " ")))
            self.table_speed.setItem(r_idx, 2, QTableWidgetItem(r.get("location_label", "Default")))
            self.table_speed.setItem(r_idx, 3, QTableWidgetItem(r.get("network_ssid", "")))
            self.table_speed.setItem(r_idx, 4, QTableWidgetItem(d_str))
            self.table_speed.setItem(r_idx, 5, QTableWidgetItem(u_str))
            self.table_speed.setItem(r_idx, 6, QTableWidgetItem(p_str))
            self.table_speed.setItem(r_idx, 7, QTableWidgetItem(status))

            # Delete button
            btn_del = QPushButton("Delete")
            btn_del.setProperty("class", "DangerButton")
            btn_del.setStyleSheet("padding: 2px 6px; font-size: 11px;")
            btn_del.clicked.connect(lambda _, tbl="speed_tests", rid=rec_id: self._confirm_delete(tbl, rid))
            self.table_speed.setCellWidget(r_idx, 8, btn_del)

    def _populate_latency_table(self, rows: List[Dict[str, Any]]):
        self.table_latency.setRowCount(len(rows))
        for r_idx, r in enumerate(rows):
            rec_id = r["id"]
            rtt_str = f"{r['avg_rtt_ms']:.1f}" if r.get('avg_rtt_ms') is not None else "—"
            jit_str = f"{r['jitter_ms']:.1f}" if r.get('jitter_ms') is not None else "—"
            loss_str = f"{r['packet_loss_percent']:.1f}%" if r.get('packet_loss_percent') is not None else "—"
            method = r.get("method", "ICMP")
            status = r.get("status", "completed")

            self.table_latency.setItem(r_idx, 0, QTableWidgetItem(str(rec_id)))
            self.table_latency.setItem(r_idx, 1, QTableWidgetItem(r.get("timestamp", "")[:19].replace("T", " ")))
            self.table_latency.setItem(r_idx, 2, QTableWidgetItem(r.get("location_label", "Default")))
            self.table_latency.setItem(r_idx, 3, QTableWidgetItem(r.get("target_host", "")))
            self.table_latency.setItem(r_idx, 4, QTableWidgetItem(method))
            self.table_latency.setItem(r_idx, 5, QTableWidgetItem(rtt_str))
            self.table_latency.setItem(r_idx, 6, QTableWidgetItem(jit_str))
            self.table_latency.setItem(r_idx, 7, QTableWidgetItem(loss_str))
            self.table_latency.setItem(r_idx, 8, QTableWidgetItem(status))

            btn_del = QPushButton("Delete")
            btn_del.setProperty("class", "DangerButton")
            btn_del.setStyleSheet("padding: 2px 6px; font-size: 11px;")
            btn_del.clicked.connect(lambda _, tbl="latency_tests", rid=rec_id: self._confirm_delete(tbl, rid))
            self.table_latency.setCellWidget(r_idx, 9, btn_del)

    def _populate_signal_table(self, rows: List[Dict[str, Any]]):
        self.table_signal.setRowCount(len(rows))
        for r_idx, r in enumerate(rows):
            rec_id = r["id"]
            sig_str = f"{r['signal_percent']}%" if r.get('signal_percent') is not None else "—"
            self.table_signal.setItem(r_idx, 0, QTableWidgetItem(str(rec_id)))
            self.table_signal.setItem(r_idx, 1, QTableWidgetItem(r.get("timestamp", "")[:19].replace("T", " ")))
            self.table_signal.setItem(r_idx, 2, QTableWidgetItem(r.get("location_label", "Default")))
            self.table_signal.setItem(r_idx, 3, QTableWidgetItem(r.get("network_ssid", "")))
            self.table_signal.setItem(r_idx, 4, QTableWidgetItem(sig_str))
            self.table_signal.setItem(r_idx, 5, QTableWidgetItem(str(r.get("channel", ""))))
            self.table_signal.setItem(r_idx, 6, QTableWidgetItem(r.get("frequency_band", "")))

            btn_del = QPushButton("Delete")
            btn_del.setProperty("class", "DangerButton")
            btn_del.setStyleSheet("padding: 2px 6px; font-size: 11px;")
            btn_del.clicked.connect(lambda _, tbl="signal_logs", rid=rec_id: self._confirm_delete(tbl, rid))
            self.table_signal.setCellWidget(r_idx, 7, btn_del)

    def _confirm_delete(self, table_name: str, record_id: int):
        reply = QMessageBox.question(
            self,
            "Confirm Record Deletion",
            f"Are you sure you want to permanently delete record #{record_id} from {table_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.request_delete_record.emit(table_name, record_id)

    def _update_trend_chart(self, speed_rows: List[Dict[str, Any]]):
        # Exclude failed tests and preserve gaps for nulls
        completed_rows = [r for r in speed_rows if r.get("status", "completed") == "completed"]
        if not completed_rows:
            self.chart.clear(title="No completed speed test records to display", xlabel="Index", ylabel="Throughput (Mbps)")
            return

        sorted_rows = sorted(completed_rows, key=lambda x: x["id"])
        x_indices = list(range(1, len(sorted_rows) + 1))
        downloads = [
            r["download_mbps"] if r.get("download_mbps") is not None else float('nan')
            for r in sorted_rows
        ]

        self.chart.clear(title="Historical Download Throughput (Mbps)", xlabel="Test Run #", ylabel="Download (Mbps)")
        self.chart.plot_line(
            x_indices,
            downloads,
            label="Download Speed (Mbps)",
            color=COLORS["primary"]
        )
