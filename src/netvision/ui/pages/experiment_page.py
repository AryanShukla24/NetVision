"""
NetVision - Academic Experiment Page (Feature 18)
Facilitates rigorous multi-trial network experimentation for Computer Networks college viva.
Supports repeated runs (5+ trials per condition), spread/variance calculations,
and correlation analysis between Wi-Fi signal quality and measured throughput/latency.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QGridLayout, QMessageBox, QTabWidget
)
from PySide6.QtCore import Qt, Signal

from netvision.ui.components.cards import MetricCard
from netvision.ui.components.chart_widget import ChartWidget
from netvision.database.models import ExperimentRun
from netvision.core.experiment_analytics import summarize_experiment_runs
from netvision.config import COLORS, DEFAULT_PING_TARGETS


class ExperimentPage(QWidget):
    """Academic experimentation workflow page."""

    request_run_experiment = Signal(str, str, int, str, str)  # experiment_id, condition_label, trials_count, target_host, location_label
    request_stop_experiment = Signal()
    request_load_saved_experiments = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_running = False
        self.current_runs: List[ExperimentRun] = []
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Computer Networks Lab: Empirical Quality Experiment")
        title.setProperty("class", "PageTitle")
        subtitle = QLabel("Multi-trial scientific evaluation: Quantifying the impact of physical signal quality on throughput & jitter")
        subtitle.setProperty("class", "PageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # Main Tabs: Live Experiment vs Saved Archives
        self.tabs = QTabWidget()

        # --- Tab 1: Live Multi-Trial Experiment ---
        tab_live = QWidget()
        l_live = QVBoxLayout(tab_live)
        l_live.setContentsMargins(8, 12, 8, 8)
        l_live.setSpacing(14)

        # Setup Card
        setup_card = QFrame()
        setup_card.setProperty("class", "ContentCard")
        s_layout = QGridLayout(setup_card)
        s_layout.setContentsMargins(16, 12, 16, 12)
        s_layout.setHorizontalSpacing(16)
        s_layout.setVerticalSpacing(8)

        lbl_cond = QLabel("Condition / Distance:")
        lbl_cond.setStyleSheet(f"color: {COLORS['text_secondary']};")
        s_layout.addWidget(lbl_cond, 0, 0)

        self.combo_condition = QComboBox()
        self.combo_condition.setEditable(True)
        self.combo_condition.setMinimumWidth(200)
        self.combo_condition.addItems([
            "Condition A (Near Router / Line-of-Sight)",
            "Condition B (Across Room / Wall Barrier)",
            "Condition C (Far Distance / Severe Attenuation)",
            "Condition D (Heavy Co-Channel Congestion)"
        ])
        s_layout.addWidget(self.combo_condition, 0, 1)

        lbl_target = QLabel("Ping Host:")
        lbl_target.setStyleSheet(f"color: {COLORS['text_secondary']};")
        s_layout.addWidget(lbl_target, 0, 2)

        self.combo_target = QComboBox()
        self.combo_target.setEditable(True)
        for t in DEFAULT_PING_TARGETS:
            self.combo_target.addItem(t["host"])
        s_layout.addWidget(self.combo_target, 0, 3)

        lbl_loc = QLabel("Location Label:")
        lbl_loc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        s_layout.addWidget(lbl_loc, 1, 0)

        self.combo_location = QComboBox()
        self.combo_location.setEditable(True)
        s_layout.addWidget(self.combo_location, 1, 1)

        lbl_trials = QLabel("Repeated Trials:")
        lbl_trials.setStyleSheet(f"color: {COLORS['text_secondary']};")
        s_layout.addWidget(lbl_trials, 1, 2)

        self.spin_trials = QSpinBox()
        self.spin_trials.setRange(3, 10)
        self.spin_trials.setValue(5)
        s_layout.addWidget(self.spin_trials, 1, 3)

        # Action buttons
        btn_box = QHBoxLayout()
        self.btn_run = QPushButton("Execute Repeated Experiment")
        self.btn_run.setProperty("class", "PrimaryButton")
        self.btn_run.clicked.connect(self._on_run_clicked)
        btn_box.addWidget(self.btn_run)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setProperty("class", "DangerButton")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        btn_box.addWidget(self.btn_stop)

        s_layout.addLayout(btn_box, 0, 4, 2, 1)
        l_live.addWidget(setup_card)

        # Progress Indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        l_live.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Ready to execute multi-trial experiment.")
        self.lbl_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        l_live.addWidget(self.lbl_status)

        # Statistical Summary Cards
        grid = QGridLayout()
        grid.setSpacing(12)

        self.card_signal_stat = MetricCard("Mean Signal (±σ)", "--", "Physical layer RSSI", "%")
        self.card_speed_stat = MetricCard("Mean Download (±σ)", "--", "Transport throughput", "Mbps")
        self.card_latency_stat = MetricCard("Mean Latency (±σ)", "--", "Round-trip time", "ms")
        self.card_jitter_stat = MetricCard("Mean Jitter (±σ)", "--", "Packet arrival variance", "ms")

        grid.addWidget(self.card_signal_stat, 0, 0)
        grid.addWidget(self.card_speed_stat, 0, 1)
        grid.addWidget(self.card_latency_stat, 0, 2)
        grid.addWidget(self.card_jitter_stat, 0, 3)
        l_live.addLayout(grid)

        # Experiment Charts Grid (Spread & Correlation)
        charts_grid = QGridLayout()
        charts_grid.setSpacing(14)

        self.chart_trials = ChartWidget(
            title="Trial-by-Trial Download Throughput & Latency",
            xlabel="Trial Run #",
            ylabel="Performance Metric",
            parent=self
        )
        self.chart_correlation = ChartWidget(
            title="Signal Quality vs Download Speed Correlation",
            xlabel="Signal Quality (%)",
            ylabel="Download Throughput (Mbps)",
            parent=self
        )

        charts_grid.addWidget(self.chart_trials, 0, 0)
        charts_grid.addWidget(self.chart_correlation, 0, 1)
        l_live.addLayout(charts_grid)

        # Table of Trial Runs
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Trial #", "Condition", "Signal %", "Download (Mbps)", "Upload (Mbps)", "Ping (ms)", "Jitter (ms)", "Loss %"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for i in (0, 2, 3, 4, 5, 6, 7):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setMaximumHeight(150)
        l_live.addWidget(self.table)

        self.tabs.addTab(tab_live, "Live Experiment Execution")

        # --- Tab 2: Saved Experiments Archive ---
        tab_archive = QWidget()
        l_arch = QVBoxLayout(tab_archive)
        l_arch.setContentsMargins(8, 12, 8, 8)
        l_arch.setSpacing(12)

        arch_hdr = QHBoxLayout()
        arch_lbl = QLabel("Archived Experiment Sessions Recorded in Database")
        arch_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #f8fafc;")
        arch_hdr.addWidget(arch_lbl)
        arch_hdr.addStretch()

        self.btn_refresh_archive = QPushButton("Refresh Archive")
        self.btn_refresh_archive.setProperty("class", "SecondaryButton")
        self.btn_refresh_archive.clicked.connect(self.request_load_saved_experiments.emit)
        arch_hdr.addWidget(self.btn_refresh_archive)
        l_arch.addLayout(arch_hdr)

        self.table_archive = QTableWidget()
        self.table_archive.setColumnCount(8)
        self.table_archive.setHorizontalHeaderLabels([
            "Experiment ID", "Condition", "Trials", "Target Host", "Timestamp", "Avg Signal", "Avg Download", "Avg Ping"
        ])
        self.table_archive.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_archive.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for i in range(2, 8):
            self.table_archive.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table_archive.verticalHeader().setVisible(False)
        self.table_archive.setEditTriggers(QTableWidget.NoEditTriggers)
        l_arch.addWidget(self.table_archive)

        self.tabs.addTab(tab_archive, "Saved Experiments Archive")

        main_layout.addWidget(self.tabs)

    def set_locations(self, locations: List[str]):
        """Populates the location combo box."""
        current = self.combo_location.currentText()
        self.combo_location.clear()
        self.combo_location.addItems(locations)
        if current in locations:
            self.combo_location.setCurrentText(current)

    def _on_run_clicked(self):
        cond = self.combo_condition.currentText().strip() or "Standard Condition"
        trials = self.spin_trials.value()
        target = self.combo_target.currentText().strip() or "8.8.8.8"
        loc = self.combo_location.currentText().strip() or cond

        self.is_running = True
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.current_runs.clear()
        self.table.setRowCount(0)
        self.progress_bar.setRange(0, trials)
        self.progress_bar.setValue(0)
        self.lbl_status.setText(f"Starting repeated experiment (Trial 1/{trials})...")

        exp_id = f"EXP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        self.request_run_experiment.emit(exp_id, cond, trials, target, loc)

    def _on_stop_clicked(self):
        self.lbl_status.setText("Aborting experiment...")
        self.btn_stop.setEnabled(False)
        self.request_stop_experiment.emit()

    def add_trial_run(self, run: ExperimentRun, total_trials: int):
        """Called as each individual run finishes."""
        self.current_runs.append(run)
        step = len(self.current_runs)
        self.progress_bar.setValue(step)

        down_txt = f"{run.download_mbps:.1f} Mbps" if run.download_mbps is not None else "—"
        ping_txt = f"{run.ping_ms:.1f} ms" if run.ping_ms is not None else "—"
        self.lbl_status.setText(f"Trial {step}/{total_trials} finished. Download: {down_txt}, Ping: {ping_txt}")

        # Insert row into table
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(f"Trial {run.run_number}"))
        self.table.setItem(row, 1, QTableWidgetItem(run.condition_label))
        self.table.setItem(row, 2, QTableWidgetItem(f"{run.signal_percent}%" if run.signal_percent is not None else "—"))
        self.table.setItem(row, 3, QTableWidgetItem(f"{run.download_mbps:.1f} Mbps" if run.download_mbps is not None else "—"))
        self.table.setItem(row, 4, QTableWidgetItem(f"{run.upload_mbps:.1f} Mbps" if run.upload_mbps is not None else "—"))
        self.table.setItem(row, 5, QTableWidgetItem(f"{run.ping_ms:.1f} ms" if run.ping_ms is not None else "—"))
        self.table.setItem(row, 6, QTableWidgetItem(f"{run.jitter_ms:.1f} ms" if run.jitter_ms is not None else "—"))
        self.table.setItem(row, 7, QTableWidgetItem(f"{run.packet_loss_percent:.1f}%" if run.packet_loss_percent is not None else "—"))

        self._update_analytics()

    def experiment_completed(self, was_completed: bool = True):
        """Called when all trials conclude or abort."""
        self.is_running = False
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)

        if was_completed:
            self.lbl_status.setText(f"Experiment completed. Collected {len(self.current_runs)} empirical trial measurements.")
            self.lbl_status.setStyleSheet(f"color: {COLORS['success']}; font-weight: 600;")
        else:
            self.lbl_status.setText(f"Experiment stopped. Collected {len(self.current_runs)} partial measurements.")
            self.lbl_status.setStyleSheet(f"color: {COLORS['warning']}; font-weight: 600;")

        self._update_analytics()

    def _update_analytics(self):
        if not self.current_runs:
            return

        summary = summarize_experiment_runs(self.current_runs)

        # Update cards
        if summary["mean_signal"] is not None:
            self.card_signal_stat.set_value(f"{summary['mean_signal']:.1f}%", f"Spread σ: ±{summary['stdev_signal']:.1f}%")
        else:
            self.card_signal_stat.set_value("No data", "")

        if summary["mean_download"] is not None:
            self.card_speed_stat.set_value(f"{summary['mean_download']:.1f}", f"Spread σ: ±{summary['stdev_download']:.1f} Mbps")
        else:
            self.card_speed_stat.set_value("No data", "")

        if summary["mean_latency"] is not None:
            self.card_latency_stat.set_value(f"{summary['mean_latency']:.1f}", f"Spread σ: ±{summary['stdev_latency']:.1f} ms")
        else:
            self.card_latency_stat.set_value("No data", "")

        if summary["mean_jitter"] is not None:
            self.card_jitter_stat.set_value(f"{summary['mean_jitter']:.1f}", f"Spread σ: ±{summary['stdev_jitter']:.1f} ms")
        else:
            self.card_jitter_stat.set_value("No data", "")

        # Chart 1: Trials comparison
        x_indices = [r.run_number for r in self.current_runs]
        downloads = [r.download_mbps if r.download_mbps is not None else float('nan') for r in self.current_runs]
        self.chart_trials.clear(title="Trial-by-Trial Download Throughput", xlabel="Trial #", ylabel="Download (Mbps)")
        self.chart_trials.plot_line(
            x_indices,
            downloads,
            label="Download Speed (Mbps)",
            color=COLORS["primary"]
        )

        # Chart 2: Correlation (Signal % vs Download Mbps) using genuine scatter plot
        paired_signals = [float(r.signal_percent) for r in self.current_runs if r.signal_percent is not None and r.download_mbps is not None]
        paired_downloads = [r.download_mbps for r in self.current_runs if r.signal_percent is not None and r.download_mbps is not None]

        r_title = f"Correlation: {summary['r_interpretation']}"
        self.chart_correlation.clear(
            title=r_title,
            xlabel="Signal Quality (%)",
            ylabel="Download (Mbps)"
        )
        if paired_signals and paired_downloads:
            self.chart_correlation.plot_scatter(
                paired_signals,
                paired_downloads,
                label="Trial Observations",
                color=COLORS["success"],
                xlim=(0, 105)
            )

    def display_saved_experiments(self, experiments: List[Dict[str, Any]]):
        """Populates the saved experiments table."""
        self.table_archive.setRowCount(len(experiments))
        for row, exp in enumerate(experiments):
            self.table_archive.setItem(row, 0, QTableWidgetItem(exp.get("experiment_id", "")))
            self.table_archive.setItem(row, 1, QTableWidgetItem(exp.get("condition_label", "")))
            self.table_archive.setItem(row, 2, QTableWidgetItem(str(exp.get("trials_count", ""))))
            self.table_archive.setItem(row, 3, QTableWidgetItem(exp.get("target_host", "")))
            self.table_archive.setItem(row, 4, QTableWidgetItem(str(exp.get("start_time", ""))[:16]))
            
            sig = exp.get("avg_signal")
            self.table_archive.setItem(row, 5, QTableWidgetItem(f"{sig:.1f}%" if sig is not None else "—"))
            
            down = exp.get("avg_download")
            self.table_archive.setItem(row, 6, QTableWidgetItem(f"{down:.1f} Mbps" if down is not None else "—"))
            
            lat = exp.get("avg_latency")
            self.table_archive.setItem(row, 7, QTableWidgetItem(f"{lat:.1f} ms" if lat is not None else "—"))
