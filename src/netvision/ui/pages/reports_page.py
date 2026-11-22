"""
NetVision - Report Generation Page (Feature 10)
Exports complete network audits, speed test logs, and telemetry into styled PDF and CSV formats.
Includes quick open folder button and live report summary preview.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from netvision.config import REPORTS_DIR, COLORS
from netvision.core.recommendation_engine import Recommendation


class ReportsPage(QWidget):
    """Reports generation and export page."""

    request_export_pdf = Signal()
    request_export_csv = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_pdf_path: Optional[Path] = None
        self.last_csv_path: Optional[Path] = None
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Audit Reports & Data Export")
        title.setProperty("class", "PageTitle")
        subtitle = QLabel("Generate academic audit reports in PDF and raw CSV formats for college presentation")
        subtitle.setProperty("class", "PageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_open_folder = QPushButton("Open Reports Folder")
        self.btn_open_folder.setProperty("class", "SecondaryButton")
        self.btn_open_folder.clicked.connect(self._open_reports_folder)
        header_layout.addWidget(self.btn_open_folder)

        main_layout.addLayout(header_layout)

        # Export Action Card
        action_card = QFrame()
        action_card.setProperty("class", "ContentCard")
        a_layout = QHBoxLayout(action_card)
        a_layout.setContentsMargins(18, 16, 18, 16)

        info_box = QVBoxLayout()
        lbl_card_title = QLabel("Export Network Diagnostic Reports")
        lbl_card_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['text_bright']};")
        lbl_card_sub = QLabel("Includes active link metadata, throughput measurements, latency statistics, and rule-based diagnostic advice.")
        lbl_card_sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        info_box.addWidget(lbl_card_title)
        info_box.addWidget(lbl_card_sub)
        a_layout.addLayout(info_box)
        a_layout.addStretch()

        self.btn_pdf = QPushButton("Generate PDF Report")
        self.btn_pdf.setProperty("class", "PrimaryButton")
        self.btn_pdf.clicked.connect(self.request_export_pdf.emit)
        a_layout.addWidget(self.btn_pdf)

        self.btn_csv = QPushButton("Export Raw CSV")
        self.btn_csv.setProperty("class", "SecondaryButton")
        self.btn_csv.clicked.connect(self.request_export_csv.emit)
        a_layout.addWidget(self.btn_csv)

        main_layout.addWidget(action_card)

        # Status Label
        self.lbl_status = QLabel("Click 'Generate PDF Report' or 'Export Raw CSV' to produce report files.")
        self.lbl_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        main_layout.addWidget(self.lbl_status)

        # Diagnostic Recommendations Section
        recs_card = QFrame()
        recs_card.setProperty("class", "ContentCard")
        r_layout = QVBoxLayout(recs_card)
        r_layout.setContentsMargins(16, 14, 16, 14)

        lbl_recs_hdr = QLabel("Current Rule-Based Diagnostic Recommendations")
        lbl_recs_hdr.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {COLORS['primary']};")
        r_layout.addWidget(lbl_recs_hdr)

        self.table_recs = QTableWidget()
        self.table_recs.setColumnCount(4)
        self.table_recs.setHorizontalHeaderLabels(["Severity", "Diagnostic Finding", "Observed Evidence", "Actionable Engineering Advice"])
        self.table_recs.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table_recs.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_recs.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_recs.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_recs.verticalHeader().setVisible(False)
        self.table_recs.setEditTriggers(QTableWidget.NoEditTriggers)
        r_layout.addWidget(self.table_recs)

        main_layout.addWidget(recs_card)

    def _open_reports_folder(self):
        """Opens reports output folder in Windows File Explorer."""
        try:
            os.startfile(str(REPORTS_DIR))
        except Exception as e:
            QMessageBox.warning(self, "Open Folder Error", f"Could not open directory: {e}")

    def display_recommendations(self, recs: List[Recommendation]):
        """Populates the diagnostic findings table."""
        self.table_recs.setRowCount(len(recs))
        for row, rec in enumerate(recs):
            sev_item = QTableWidgetItem(rec.severity.upper())
            if rec.severity == "Critical":
                sev_item.setForeground(Qt.red)
            elif rec.severity == "Warning":
                sev_item.setForeground(Qt.yellow)
            elif rec.severity == "Good":
                sev_item.setForeground(Qt.green)
            else:
                sev_item.setForeground(Qt.cyan)

            self.table_recs.setItem(row, 0, sev_item)
            self.table_recs.setItem(row, 1, QTableWidgetItem(rec.title))
            self.table_recs.setItem(row, 2, QTableWidgetItem(rec.evidence))
            self.table_recs.setItem(row, 3, QTableWidgetItem(rec.advice))

    def on_export_completed(self, file_path: Path, format_type: str):
        """Notification callback after export completes."""
        self.lbl_status.setText(f"{format_type.upper()} successfully saved to: {file_path.name}")
        self.lbl_status.setStyleSheet(f"color: {COLORS['success']}; font-weight: 600;")
        QMessageBox.information(
            self,
            f"{format_type.upper()} Export Successful",
            f"Audit file generated successfully:\n\n{file_path}\n\nYou can access it in the 'reports_output' folder."
        )
