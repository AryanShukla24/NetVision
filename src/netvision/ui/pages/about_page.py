"""
NetVision - About & System Diagnostics Page
Displays technical architecture specifications, host environment telemetry,
and software component information for the desktop application.
"""

import sys
import platform
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt

from netvision.config import (
    APP_NAME, APP_SUBTITLE, APP_VERSION, COLORS,
    USER_DATA_DIR, DEFAULT_DB_PATH, LOG_FILE_PATH
)


class AboutPage(QWidget):
    """About & Technical System Information Page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        title_box = QVBoxLayout()
        title = QLabel(f"{APP_NAME} — {APP_SUBTITLE}")
        title.setProperty("class", "PageTitle")
        subtitle = QLabel(f"Version {APP_VERSION} | Windows 10 & 11 Native 64-bit Diagnostic Suite")
        subtitle.setProperty("class", "PageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        main_layout.addLayout(title_box)

        # Scroll Area for Content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(0, 0, 10, 0)
        c_layout.setSpacing(16)

        # Technical Architecture Card
        card_overview = QFrame()
        card_overview.setProperty("class", "ContentCard")
        o_layout = QVBoxLayout(card_overview)
        o_title = QLabel("System Architecture & Diagnostic Capabilities")
        o_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['primary']};")
        o_layout.addWidget(o_title)

        summary_text = (
            "<b>NetVision</b> is a modular network quality analyzer designed for Windows desktop environments. "
            "It integrates low-level OS telemetry, asynchronous ICMP diagnostics, and high-throughput chunked CDN measurements "
            "into a unified desktop interface.<br/><br/>"
            "<b>Core Technical Components:</b><br/>"
            "• <b>Hardware Radio Inspection:</b> Queries the Windows Native WLAN API (<code>wlanapi.dll</code>) and WLAN AutoConfig service to scan active 802.11 spectrum channels, extract connected BSSIDs, and identify frequency bands.<br/>"
            "• <b>Measurement Integrity Engine:</b> Strictly separates Layer 3 ICMP echo probing from Layer 4 TCP connection timing, preventing false-positive loss masking. Computes genuine RFC 3550 interarrival jitter.<br/>"
            "• <b>Decoupled Multithreading:</b> All slow network I/O operations execute inside dedicated <code>QThread</code> background workers, communicating with the UI thread strictly via Qt Signals and Slots.<br/>"
            "• <b>Isolated Relational Persistence:</b> Utilizes SQLite 3 with Write-Ahead Logging (WAL) and automated schema migrations, storing user databases and telemetry in <code>%LOCALAPPDATA%\\NetVision\\</code>."
        )
        lbl_sum = QLabel(summary_text)
        lbl_sum.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px; line-height: 1.5;")
        lbl_sum.setWordWrap(True)
        o_layout.addWidget(lbl_sum)
        c_layout.addWidget(card_overview)

        # Host Runtime Telemetry Card
        card_telemetry = QFrame()
        card_telemetry.setProperty("class", "ContentCard")
        t_layout = QVBoxLayout(card_telemetry)
        t_title = QLabel("Runtime Environment & Host Telemetry")
        t_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['success']};")
        t_layout.addWidget(t_title)

        telemetry_grid = QGridLayout()
        telemetry_grid.setHorizontalSpacing(24)
        telemetry_grid.setVerticalSpacing(8)

        items = [
            ("Operating System", platform.platform()),
            ("Python Runtime", f"{sys.version.split()[0]} ({platform.architecture()[0]})"),
            ("UI Framework", "PySide6 / Qt 6.8"),
            ("User Data Path", str(USER_DATA_DIR)),
            ("Active Database", str(DEFAULT_DB_PATH)),
            ("Log Destination", str(LOG_FILE_PATH))
        ]

        for row, (k, v) in enumerate(items):
            k_lbl = QLabel(f"<b>{k}:</b>")
            k_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
            v_lbl = QLabel(str(v))
            v_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px;")
            v_lbl.setWordWrap(True)
            telemetry_grid.addWidget(k_lbl, row, 0)
            telemetry_grid.addWidget(v_lbl, row, 1)

        t_layout.addLayout(telemetry_grid)
        c_layout.addWidget(card_telemetry)

        # Open Source & Compliance Card
        card_credits = QFrame()
        card_credits.setProperty("class", "ContentCard")
        cr_layout = QVBoxLayout(card_credits)
        cr_title = QLabel("Software Components & Open Source Credits")
        cr_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['purple']};")
        cr_layout.addWidget(cr_title)

        credits_text = (
            "Built with open-source technologies: <b>PySide6</b> (Qt for Python), <b>Matplotlib</b>, "
            "<b>ReportLab PDF Toolkit</b>, <b>Requests</b>, <b>NumPy</b>, and <b>Pandas</b>.<br/>"
            "Designed and engineered for BTech Computer Science & Engineering Network Quality Analysis."
        )
        lbl_credits = QLabel(credits_text)
        lbl_credits.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; line-height: 1.5;")
        lbl_credits.setWordWrap(True)
        cr_layout.addWidget(lbl_credits)
        c_layout.addWidget(card_credits)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)
