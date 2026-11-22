"""
NetVision - Status Pill Widget
Renders an engineered badge indicating network health status:
Excellent (Green), Good (Teal), Fair (Amber), Poor (Red), Disconnected (Muted Gray).
"""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from netvision.config import COLORS


class StatusPill(QLabel):
    """Pill badge showing connection health state."""

    STYLE_MAP = {
        "Excellent": {
            "bg": "rgba(57, 217, 138, 0.12)",
            "border": "#39D98A",
            "text": "#39D98A"
        },
        "Good": {
            "bg": "rgba(34, 184, 207, 0.12)",
            "border": "#22B8CF",
            "text": "#22B8CF"
        },
        "Fair": {
            "bg": "rgba(245, 185, 66, 0.12)",
            "border": "#F5B942",
            "text": "#F5B942"
        },
        "Poor": {
            "bg": "rgba(240, 100, 100, 0.12)",
            "border": "#F06464",
            "text": "#F06464"
        },
        "Disconnected": {
            "bg": "rgba(90, 107, 127, 0.15)",
            "border": "#5A6B7F",
            "text": "#8291A3"
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
                border-radius: 4px;
                padding: 3px 10px;
                font-weight: 600;
                font-size: 11px;
            }}
        """)
