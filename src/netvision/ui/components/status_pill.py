"""
NetVision - Status Pill Widget
Renders a colored badge indicating network health status:
Excellent (Green), Good (Blue), Fair (Amber), Poor (Red), Disconnected (Gray).
"""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from netvision.config import COLORS


class StatusPill(QLabel):
    """Pill badge showing connection health state."""

    STYLE_MAP = {
        "Excellent": {
            "bg": "rgba(52, 211, 153, 0.15)",
            "border": "#34d399",
            "text": "#34d399"
        },
        "Good": {
            "bg": "rgba(56, 189, 248, 0.15)",
            "border": "#38bdf8",
            "text": "#38bdf8"
        },
        "Fair": {
            "bg": "rgba(251, 191, 36, 0.15)",
            "border": "#fbbf24",
            "text": "#fbbf24"
        },
        "Poor": {
            "bg": "rgba(248, 113, 113, 0.15)",
            "border": "#f87171",
            "text": "#f87171"
        },
        "Disconnected": {
            "bg": "rgba(100, 116, 139, 0.15)",
            "border": "#64748b",
            "text": "#94a3b8"
        }
    }

    def __init__(self, status: str = "Disconnected", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStatus(status)

    def setStatus(self, status: str):
        style = self.STYLE_MAP.get(status, self.STYLE_MAP["Disconnected"])
        self.setText(f"●  {status}")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {style['bg']};
                color: {style['text']};
                border: 1px solid {style['border']};
                border-radius: 12px;
                padding: 4px 12px;
                font-weight: 600;
                font-size: 11px;
            }}
        """)
