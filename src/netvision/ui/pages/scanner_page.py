"""
NetVision - Wi-Fi Scanner Page (Feature 2)
Discovers nearby wireless access points using Windows-native netsh commands,
provides live search filtering, sorting by signal strength, and saves scan sessions.
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from PySide6.QtGui import QColor
from netvision.database.models import WifiNetwork
from netvision.config import COLORS


class ScannerPage(QWidget):
    """Page displaying discovered wireless access points."""

    request_scan = Signal(str)  # passes location_label

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_networks: List[WifiNetwork] = []
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Nearby Wi-Fi Network Scanner")
        title.setProperty("class", "PageTitle")
        subtitle = QLabel("Passive discovery of surrounding 802.11 access points, channels, and signal qualities")
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
        self.combo_location.setMinimumWidth(160)
        header_layout.addWidget(self.combo_location)

        self.btn_scan = QPushButton("Scan Networks")
        self.btn_scan.setProperty("class", "PrimaryButton")
        self.btn_scan.clicked.connect(self._on_scan_clicked)
        header_layout.addWidget(self.btn_scan)

        main_layout.addLayout(header_layout)

        # Progress / Status Banner
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indeterminate loading
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Ready to scan.")
        self.lbl_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        main_layout.addWidget(self.lbl_status)

        # Filter & Sort Controls
        control_bar = QFrame()
        control_bar.setProperty("class", "ContentCard")
        ctrl_layout = QHBoxLayout(control_bar)
        ctrl_layout.setContentsMargins(12, 10, 12, 10)

        lbl_filter = QLabel("Filter:")
        lbl_filter.setStyleSheet(f"color: {COLORS['text_secondary']};")
        ctrl_layout.addWidget(lbl_filter)

        self.input_filter = QLineEdit()
        self.input_filter.setPlaceholderText("Filter by SSID, Channel, or Band...")
        self.input_filter.textChanged.connect(self._apply_filter_and_sort)
        ctrl_layout.addWidget(self.input_filter)

        lbl_sort = QLabel("Sort By:")
        lbl_sort.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-left: 15px;")
        ctrl_layout.addWidget(lbl_sort)

        self.combo_sort = QComboBox()
        self.combo_sort.addItems([
            "Signal Quality (High to Low)",
            "Signal Quality (Low to High)",
            "Channel (Ascending)",
            "SSID (A-Z)"
        ])
        self.combo_sort.currentIndexChanged.connect(self._apply_filter_and_sort)
        ctrl_layout.addWidget(self.combo_sort)

        main_layout.addWidget(control_bar)

        # Networks Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Status", "SSID", "Signal %", "Category", "Channel", "Band", "Security", "Radio Standard", "BSSID"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        main_layout.addWidget(self.table)

    def set_locations(self, locations: List[str]):
        """Populates the location combo box."""
        current = self.combo_location.currentText()
        self.combo_location.clear()
        self.combo_location.addItems(locations)
        if current in locations:
            self.combo_location.setCurrentText(current)

    def _on_scan_clicked(self):
        loc = self.combo_location.currentText().strip() or "Default"
        self.btn_scan.setEnabled(False)
        self.progress_bar.show()
        self.lbl_status.setText("Scanning wireless spectrum via Windows Wi-Fi subsystem...")
        self.request_scan.emit(loc)

    def display_networks(self, networks: List[WifiNetwork], error: Optional[str] = None):
        """Called by controller after scan completion."""
        self.btn_scan.setEnabled(True)
        self.progress_bar.hide()

        if error:
            self.lbl_status.setText(f"Scan Warning: {error}")
            self.lbl_status.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px;")
            self.all_networks = networks
            self._render_table(networks)
            return

        self.all_networks = networks
        self.lbl_status.setText(f"Found {len(networks)} wireless access point(s) in range.")
        self.lbl_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px;")
        self._apply_filter_and_sort()

    def _apply_filter_and_sort(self):
        query = self.input_filter.text().strip().lower()
        filtered = []

        for n in self.all_networks:
            if not query:
                filtered.append(n)
            elif (query in n.ssid.lower() or
                  query in str(n.channel) or
                  query in n.frequency_band.lower() or
                  query in n.bssid.lower()):
                filtered.append(n)

        sort_mode = self.combo_sort.currentIndex()
        if sort_mode == 0:  # Signal High to Low
            filtered.sort(key=lambda x: x.signal_percent, reverse=True)
        elif sort_mode == 1:  # Signal Low to High
            filtered.sort(key=lambda x: x.signal_percent, reverse=False)
        elif sort_mode == 2:  # Channel
            filtered.sort(key=lambda x: x.channel)
        elif sort_mode == 3:  # SSID
            filtered.sort(key=lambda x: x.ssid.lower())

        self._render_table(filtered)

    def _render_table(self, networks: List[WifiNetwork]):
        self.table.setRowCount(len(networks))

        for row, net in enumerate(networks):
            # Status icon
            status_text = "● Connected" if net.is_connected else "Available"
            status_item = QTableWidgetItem(status_text)
            if net.is_connected:
                status_item.setForeground(QColor(COLORS['primary']))

            ssid_item = QTableWidgetItem(net.ssid)
            if net.is_connected:
                ssid_item.setForeground(QColor(COLORS['primary']))

            sig_item = QTableWidgetItem(f"{net.signal_percent}%")
            cat_item = QTableWidgetItem(net.signal_category)

            # Signal color coding
            if net.signal_percent >= 75:
                cat_item.setForeground(QColor(COLORS['success']))
            elif net.signal_percent >= 50:
                cat_item.setForeground(QColor(COLORS['primary']))
            elif net.signal_percent >= 30:
                cat_item.setForeground(QColor(COLORS['warning']))
            else:
                cat_item.setForeground(QColor(COLORS['danger']))

            ch_item = QTableWidgetItem(str(net.channel) if net.channel > 0 else "--")
            band_item = QTableWidgetItem(net.frequency_band)
            sec_item = QTableWidgetItem(net.security_type)
            radio_item = QTableWidgetItem(net.radio_type)
            bssid_item = QTableWidgetItem(net.bssid)

            self.table.setItem(row, 0, status_item)
            self.table.setItem(row, 1, ssid_item)
            self.table.setItem(row, 2, sig_item)
            self.table.setItem(row, 3, cat_item)
            self.table.setItem(row, 4, ch_item)
            self.table.setItem(row, 5, band_item)
            self.table.setItem(row, 6, sec_item)
            self.table.setItem(row, 7, radio_item)
            self.table.setItem(row, 8, bssid_item)
