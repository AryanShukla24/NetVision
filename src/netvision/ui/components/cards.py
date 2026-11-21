"""
NetVision - Metric Card Component
Displays an individual network metric (e.g. Signal, Speed, Latency, Loss)
with clean typography, status pill, and responsive sizing.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from netvision.config import COLORS


class MetricCard(QFrame):
    """Reusable card component displaying a key network performance metric."""

    def __init__(self, title: str, initial_value: str = "--", subtitle: str = "", unit: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("class", "MetricCard")
        self.unit = unit

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        # Header Row
        header_layout = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setProperty("class", "CardTitle")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Value Row
        self.value_label = QLabel(f"{initial_value} {self.unit}".strip())
        self.value_label.setProperty("class", "CardValue")
        layout.addWidget(self.value_label)

        # Subtitle / Trend Row
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setProperty("class", "CardSubtitle")
        layout.addWidget(self.subtitle_label)

    def set_value(self, value: str, subtitle: str = ""):
        """Updates the metric display."""
        if self.unit and value != "--" and not value.endswith(self.unit):
            self.value_label.setText(f"{value} {self.unit}".strip())
        else:
            self.value_label.setText(value)

        if subtitle:
            self.subtitle_label.setText(subtitle)

    def set_highlight_color(self, color_hex: str):
        """Optionally accents the card value text color."""
        self.value_label.setStyleSheet(f"color: {color_hex};")
