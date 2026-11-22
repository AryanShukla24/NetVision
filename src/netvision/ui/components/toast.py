"""
NetVision - Modern Non-Blocking Toast Notification System
Provides animated, non-blocking feedback (success, error, info) that slides/fades in
and automatically dismisses after a timeout.
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QColor, QFont

from netvision.config import COLORS


class ToastNotification(QWidget):
    """
    Non-blocking toast message overlay displayed on top of parent window.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.SubWindow | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._fade_out)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity", self)
        self.anim.setDuration(220)

        self._build_ui()
        self.hide()

    def _build_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(18, 10, 18, 10)
        self.main_layout.setSpacing(12)

        self.lbl_icon = QLabel("✔")
        self.lbl_icon.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.main_layout.addWidget(self.lbl_icon)

        self.lbl_msg = QLabel("Settings saved successfully")
        self.lbl_msg.setStyleSheet("font-size: 13px; font-weight: 600; color: #f8fafc;")
        self.main_layout.addWidget(self.lbl_msg)

    def show_toast(self, message: str, toast_type: str = "success", duration_ms: int = 3500):
        self.lbl_msg.setText(message)

        if toast_type == "success":
            self.lbl_icon.setText("✔")
            self.lbl_icon.setStyleSheet("color: #34d399; font-size: 16px; font-weight: 900;")
            self.setStyleSheet("""
                background-color: #0b1426;
                border: 1px solid #34d399;
                border-radius: 8px;
            """)
        elif toast_type == "error":
            self.lbl_icon.setText("⚠")
            self.lbl_icon.setStyleSheet("color: #f87171; font-size: 16px; font-weight: 900;")
            self.setStyleSheet("""
                background-color: #1a0f1a;
                border: 1px solid #ef4444;
                border-radius: 8px;
            """)
        else: # info
            self.lbl_icon.setText("ℹ")
            self.lbl_icon.setStyleSheet("color: #38bdf8; font-size: 16px; font-weight: 900;")
            self.setStyleSheet("""
                background-color: #091322;
                border: 1px solid #38bdf8;
                border-radius: 8px;
            """)

        self.adjustSize()
        self._position_toast()
        self.show()
        self.raise_()

        # Fade in
        self.anim.stop()
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(1.0)
        self.anim.start()

        self._dismiss_timer.start(duration_ms)

    def show_message(self, message: str, toast_type: str = "success", duration_ms: int = 3500):
        """Alias for show_toast."""
        self.show_toast(message, toast_type=toast_type, duration_ms=duration_ms)

    def _position_toast(self):
        if self.parent():
            pw = self.parent().width()
            w = self.width()
            x = max(20, (pw - w) // 2)
            y = 24
            self.move(x, y)

    def _fade_out(self):
        self.anim.stop()
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(0.0)
        try:
            self.anim.finished.disconnect(self._on_fade_finished)
        except Exception:
            pass
        self.anim.finished.connect(self._on_fade_finished)
        self.anim.start()

    def _on_fade_finished(self):
        if self.opacity_effect.opacity() == 0.0:
            self.hide()
