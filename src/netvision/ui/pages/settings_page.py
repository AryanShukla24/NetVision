"""
NetVision - Settings Page (Feature 11)
Allows configuring evaluation thresholds, default ping target,
sampling intervals, and managing custom location labels.
Validates input threshold ordering and persists values to SQLite app_settings.
"""

from typing import List, Dict, Any, Optional
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSpinBox, QDoubleSpinBox, QLineEdit,
    QListWidget, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, Signal

from netvision.config import DEFAULT_THRESHOLDS, DEFAULT_PING_TARGETS, COLORS


class SettingsPage(QWidget):
    """Application settings and custom location manager."""

    request_save_settings = Signal(dict)
    request_restore_defaults = Signal()
    request_add_location = Signal(str)

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
        title = QLabel("System Settings & Threshold Configuration")
        title.setProperty("class", "PageTitle")
        subtitle = QLabel("Tune quality categorization thresholds, default network targets, and custom location labels")
        subtitle.setProperty("class", "PageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_restore = QPushButton("↺ Restore Defaults")
        self.btn_restore.setProperty("class", "SecondaryButton")
        self.btn_restore.clicked.connect(self._on_restore_clicked)
        header_layout.addWidget(self.btn_restore)

        self.btn_save = QPushButton("💾 Save Changes")
        self.btn_save.setProperty("class", "PrimaryButton")
        self.btn_save.clicked.connect(self._on_save_clicked)
        header_layout.addWidget(self.btn_save)

        main_layout.addLayout(header_layout)

        # General & Monitoring Options Card
        gen_card = QFrame()
        gen_card.setProperty("class", "ContentCard")
        g_layout = QVBoxLayout(gen_card)
        g_layout.setContentsMargins(16, 14, 16, 14)

        g_title = QLabel("General & Monitoring Defaults")
        g_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #38bdf8;")
        g_layout.addWidget(g_title)

        g_grid = QGridLayout()
        g_grid.setSpacing(12)

        lbl_target = QLabel("Default Ping Target Host:")
        self.input_default_target = QLineEdit("8.8.8.8")
        self.input_default_target.setPlaceholderText("8.8.8.8 or 1.1.1.1")

        lbl_interval = QLabel("Signal Monitor Polling Interval (seconds):")
        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(1, 10)
        self.spin_interval.setValue(2)

        g_grid.addWidget(lbl_target, 0, 0)
        g_grid.addWidget(self.input_default_target, 0, 1)
        g_grid.addWidget(lbl_interval, 0, 2)
        g_grid.addWidget(self.spin_interval, 0, 3)

        g_layout.addLayout(g_grid)
        main_layout.addWidget(gen_card)

        # Quality Evaluation Thresholds Card
        thresh_card = QFrame()
        thresh_card.setProperty("class", "ContentCard")
        t_layout = QVBoxLayout(thresh_card)
        t_layout.setContentsMargins(16, 14, 16, 14)

        t_title = QLabel("Network Quality Evaluation Thresholds")
        t_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #38bdf8;")
        t_layout.addWidget(t_title)

        grid = QGridLayout()
        grid.setSpacing(12)

        # Signal Thresholds
        lbl_s_exc = QLabel("Wi-Fi Signal Excellent (>= %):")
        lbl_s_good = QLabel("Wi-Fi Signal Good (>= %):")
        lbl_s_fair = QLabel("Wi-Fi Signal Fair (>= %):")

        self.spin_s_exc = QSpinBox()
        self.spin_s_exc.setRange(50, 100)
        self.spin_s_exc.setValue(DEFAULT_THRESHOLDS["signal"]["excellent"])

        self.spin_s_good = QSpinBox()
        self.spin_s_good.setRange(30, 90)
        self.spin_s_good.setValue(DEFAULT_THRESHOLDS["signal"]["good"])

        self.spin_s_fair = QSpinBox()
        self.spin_s_fair.setRange(10, 70)
        self.spin_s_fair.setValue(DEFAULT_THRESHOLDS["signal"]["fair"])

        grid.addWidget(lbl_s_exc, 0, 0)
        grid.addWidget(self.spin_s_exc, 0, 1)
        grid.addWidget(lbl_s_good, 0, 2)
        grid.addWidget(self.spin_s_good, 0, 3)
        grid.addWidget(lbl_s_fair, 0, 4)
        grid.addWidget(self.spin_s_fair, 0, 5)

        # Latency Thresholds
        lbl_l_exc = QLabel("Ping Latency Excellent (<= ms):")
        lbl_l_good = QLabel("Ping Latency Good (<= ms):")
        lbl_l_fair = QLabel("Ping Latency Fair (<= ms):")

        self.spin_l_exc = QSpinBox()
        self.spin_l_exc.setRange(5, 50)
        self.spin_l_exc.setValue(DEFAULT_THRESHOLDS["latency"]["excellent"])

        self.spin_l_good = QSpinBox()
        self.spin_l_good.setRange(20, 100)
        self.spin_l_good.setValue(DEFAULT_THRESHOLDS["latency"]["good"])

        self.spin_l_fair = QSpinBox()
        self.spin_l_fair.setRange(50, 250)
        self.spin_l_fair.setValue(DEFAULT_THRESHOLDS["latency"]["fair"])

        grid.addWidget(lbl_l_exc, 1, 0)
        grid.addWidget(self.spin_l_exc, 1, 1)
        grid.addWidget(lbl_l_good, 1, 2)
        grid.addWidget(self.spin_l_good, 1, 3)
        grid.addWidget(lbl_l_fair, 1, 4)
        grid.addWidget(self.spin_l_fair, 1, 5)

        # Packet Loss Thresholds
        lbl_p_good = QLabel("Packet Loss Good (<= %):")
        lbl_p_fair = QLabel("Packet Loss Fair (<= %):")

        self.spin_p_good = QDoubleSpinBox()
        self.spin_p_good.setRange(0.0, 5.0)
        self.spin_p_good.setSingleStep(0.5)
        self.spin_p_good.setValue(DEFAULT_THRESHOLDS["packet_loss"]["good"])

        self.spin_p_fair = QDoubleSpinBox()
        self.spin_p_fair.setRange(1.0, 15.0)
        self.spin_p_fair.setSingleStep(0.5)
        self.spin_p_fair.setValue(DEFAULT_THRESHOLDS["packet_loss"]["fair"])

        grid.addWidget(lbl_p_good, 2, 0)
        grid.addWidget(self.spin_p_good, 2, 1)
        grid.addWidget(lbl_p_fair, 2, 2)
        grid.addWidget(self.spin_p_fair, 2, 3)

        # Download Speed Thresholds
        lbl_d_exc = QLabel("Download Speed Excellent (>= Mbps):")
        lbl_d_good = QLabel("Download Speed Good (>= Mbps):")
        lbl_d_fair = QLabel("Download Speed Fair (>= Mbps):")

        self.spin_d_exc = QDoubleSpinBox()
        self.spin_d_exc.setRange(10.0, 500.0)
        self.spin_d_exc.setValue(DEFAULT_THRESHOLDS["download_speed"]["excellent"])

        self.spin_d_good = QDoubleSpinBox()
        self.spin_d_good.setRange(5.0, 200.0)
        self.spin_d_good.setValue(DEFAULT_THRESHOLDS["download_speed"]["good"])

        self.spin_d_fair = QDoubleSpinBox()
        self.spin_d_fair.setRange(1.0, 50.0)
        self.spin_d_fair.setValue(DEFAULT_THRESHOLDS["download_speed"]["fair"])

        grid.addWidget(lbl_d_exc, 3, 0)
        grid.addWidget(self.spin_d_exc, 3, 1)
        grid.addWidget(lbl_d_good, 3, 2)
        grid.addWidget(self.spin_d_good, 3, 3)
        grid.addWidget(lbl_d_fair, 3, 4)
        grid.addWidget(self.spin_d_fair, 3, 5)

        t_layout.addLayout(grid)
        main_layout.addWidget(thresh_card)

        # Custom Locations Card
        loc_card = QFrame()
        loc_card.setProperty("class", "ContentCard")
        l_layout = QVBoxLayout(loc_card)
        l_layout.setContentsMargins(16, 14, 16, 14)

        l_title = QLabel("Custom Environment Location Labels")
        l_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #38bdf8;")
        l_layout.addWidget(l_title)

        add_bar = QHBoxLayout()
        self.input_new_loc = QLineEdit()
        self.input_new_loc.setPlaceholderText("Enter custom location label (e.g. CS Lab 3, Library 2nd Floor, Room 402)...")
        add_bar.addWidget(self.input_new_loc)

        self.btn_add_loc = QPushButton("+ Add Location")
        self.btn_add_loc.setProperty("class", "SecondaryButton")
        self.btn_add_loc.clicked.connect(self._on_add_loc_clicked)
        add_bar.addWidget(self.btn_add_loc)
        l_layout.addLayout(add_bar)

        self.list_locations = QListWidget()
        self.list_locations.setMaximumHeight(110)
        l_layout.addWidget(self.list_locations)

        main_layout.addWidget(loc_card)
        main_layout.addStretch()

    def set_locations(self, locations: List[str]):
        """Populates existing locations list."""
        self.list_locations.clear()
        for loc in locations:
            self.list_locations.addItem(loc)

    def load_settings(self, settings_dict: Dict[str, Any]):
        """Populates UI controls with saved settings."""
        if not settings_dict:
            return

        if "default_ping_target" in settings_dict:
            self.input_default_target.setText(settings_dict["default_ping_target"])

        if "sampling_interval_sec" in settings_dict:
            try:
                self.spin_interval.setValue(int(settings_dict["sampling_interval_sec"]))
            except ValueError:
                pass

        if "thresholds_json" in settings_dict:
            try:
                th = json.loads(settings_dict["thresholds_json"])
                sig = th.get("signal", {})
                if "excellent" in sig: self.spin_s_exc.setValue(int(sig["excellent"]))
                if "good" in sig: self.spin_s_good.setValue(int(sig["good"]))
                if "fair" in sig: self.spin_s_fair.setValue(int(sig["fair"]))

                lat = th.get("latency", {})
                if "excellent" in lat: self.spin_l_exc.setValue(int(lat["excellent"]))
                if "good" in lat: self.spin_l_good.setValue(int(lat["good"]))
                if "fair" in lat: self.spin_l_fair.setValue(int(lat["fair"]))

                loss = th.get("packet_loss", {})
                if "good" in loss: self.spin_p_good.setValue(float(loss["good"]))
                if "fair" in loss: self.spin_p_fair.setValue(float(loss["fair"]))

                spd = th.get("download_speed", {})
                if "excellent" in spd: self.spin_d_exc.setValue(float(spd["excellent"]))
                if "good" in spd: self.spin_d_good.setValue(float(spd["good"]))
                if "fair" in spd: self.spin_d_fair.setValue(float(spd["fair"]))
            except Exception:
                pass

    def _on_add_loc_clicked(self):
        name = self.input_new_loc.text().strip()
        if not name:
            return
        self.input_new_loc.clear()
        self.request_add_location.emit(name)

    def _on_restore_clicked(self):
        """Restores default values across all controls."""
        self.spin_s_exc.setValue(DEFAULT_THRESHOLDS["signal"]["excellent"])
        self.spin_s_good.setValue(DEFAULT_THRESHOLDS["signal"]["good"])
        self.spin_s_fair.setValue(DEFAULT_THRESHOLDS["signal"]["fair"])

        self.spin_l_exc.setValue(DEFAULT_THRESHOLDS["latency"]["excellent"])
        self.spin_l_good.setValue(DEFAULT_THRESHOLDS["latency"]["good"])
        self.spin_l_fair.setValue(DEFAULT_THRESHOLDS["latency"]["fair"])

        self.spin_p_good.setValue(DEFAULT_THRESHOLDS["packet_loss"]["good"])
        self.spin_p_fair.setValue(DEFAULT_THRESHOLDS["packet_loss"]["fair"])

        self.spin_d_exc.setValue(DEFAULT_THRESHOLDS["download_speed"]["excellent"])
        self.spin_d_good.setValue(DEFAULT_THRESHOLDS["download_speed"]["good"])
        self.spin_d_fair.setValue(DEFAULT_THRESHOLDS["download_speed"]["fair"])

        self.input_default_target.setText("8.8.8.8")
        self.spin_interval.setValue(2)

        self.request_restore_defaults.emit()
        QMessageBox.information(self, "Defaults Restored", "Thresholds and monitoring settings reset to standard defaults.")

    def _on_save_clicked(self):
        """Validates threshold orderings and emits validated settings payload."""
        # 1. Validate Signal Threshold Ordering (excellent > good > fair)
        s_exc = self.spin_s_exc.value()
        s_good = self.spin_s_good.value()
        s_fair = self.spin_s_fair.value()
        if not (s_exc > s_good > s_fair):
            QMessageBox.warning(
                self,
                "Invalid Threshold Ordering",
                f"Wi-Fi Signal thresholds must satisfy: Excellent ({s_exc}%) > Good ({s_good}%) > Fair ({s_fair}%)."
            )
            return

        # 2. Validate Latency Threshold Ordering (excellent < good < fair)
        l_exc = self.spin_l_exc.value()
        l_good = self.spin_l_good.value()
        l_fair = self.spin_l_fair.value()
        if not (l_exc < l_good < l_fair):
            QMessageBox.warning(
                self,
                "Invalid Threshold Ordering",
                f"Latency thresholds must satisfy: Excellent ({l_exc} ms) < Good ({l_good} ms) < Fair ({l_fair} ms)."
            )
            return

        # 3. Validate Packet Loss Ordering (good < fair)
        p_good = self.spin_p_good.value()
        p_fair = self.spin_p_fair.value()
        if not (p_good < p_fair):
            QMessageBox.warning(
                self,
                "Invalid Threshold Ordering",
                f"Packet loss thresholds must satisfy: Good ({p_good}%) < Fair ({p_fair}%)."
            )
            return

        # 4. Validate Download Speed Ordering (excellent > good > fair)
        d_exc = self.spin_d_exc.value()
        d_good = self.spin_d_good.value()
        d_fair = self.spin_d_fair.value()
        if not (d_exc > d_good > d_fair):
            QMessageBox.warning(
                self,
                "Invalid Threshold Ordering",
                f"Download speed thresholds must satisfy: Excellent ({d_exc} Mbps) > Good ({d_good} Mbps) > Fair ({d_fair} Mbps)."
            )
            return

        target_host = self.input_default_target.text().strip() or "8.8.8.8"
        interval = self.spin_interval.value()

        thresholds = {
            "signal": {"excellent": s_exc, "good": s_good, "fair": s_fair, "poor": 0},
            "latency": {"excellent": l_exc, "good": l_good, "fair": l_fair, "poor": l_fair * 2},
            "packet_loss": {"excellent": 0.0, "good": p_good, "fair": p_fair, "poor": p_fair * 1.5},
            "download_speed": {"excellent": d_exc, "good": d_good, "fair": d_fair, "poor": 0.0}
        }

        payload = {
            "thresholds_json": json.dumps(thresholds),
            "default_ping_target": target_host,
            "sampling_interval_sec": str(interval)
        }

        self.request_save_settings.emit(payload)
