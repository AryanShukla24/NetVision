"""
NetVision - Professional Dark Modern Theme & Stylesheet (QSS)
Clean, polished design system inspired by slate/zinc and modern high-tech developer HUDs.
Provides consistent typography, high contrast, non-clipped inputs/dropdowns,
and eliminates white alternating table rows.
"""

from netvision.config import COLORS

DARK_THEME_QSS = f"""
/* Global Reset and Main Window */
QMainWindow {{
    background-color: {COLORS['bg_dark']};
    color: #f8fafc;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}}

/* Sidebar Navigation */
#Sidebar {{
    background-color: #0b111e;
    border-right: 1px solid rgba(51, 65, 85, 0.6);
    min-width: 236px;
    max-width: 256px;
}}

#SidebarHeader {{
    padding: 18px 14px 14px 14px;
    border-bottom: 1px solid rgba(51, 65, 85, 0.5);
    margin-bottom: 6px;
}}

#SidebarAppTitle {{
    font-size: 19px;
    font-weight: 800;
    color: #38bdf8;
    letter-spacing: 0.5px;
}}

#SidebarAppSubtitle {{
    font-size: 11px;
    color: #94a3b8;
    line-height: 1.3;
    margin-top: 2px;
}}

/* Navigation Buttons with modern active left border */
QPushButton.NavButton {{
    background-color: transparent;
    color: #94a3b8;
    text-align: left;
    padding: 10px 14px;
    border-radius: 6px;
    border: none;
    border-left: 3px solid transparent;
    font-size: 13px;
    font-weight: 500;
    margin: 2px 8px;
    min-height: 22px;
}}

QPushButton.NavButton:hover {{
    background-color: rgba(51, 65, 85, 0.4);
    color: #f8fafc;
}}

QPushButton.NavButton:checked, QPushButton.NavButton[active="true"] {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(2, 132, 199, 0.35), stop:1 rgba(37, 99, 235, 0.15));
    border-left: 3px solid #38bdf8;
    color: #ffffff;
    font-weight: 700;
}}

/* Metric & Content Cards with modern subtle border */
QFrame.MetricCard, QFrame.ContentCard {{
    background-color: #111a2e;
    border: 1px solid rgba(51, 65, 85, 0.7);
    border-radius: 8px;
    padding: 14px;
}}

QFrame.MetricCard:hover {{
    border-color: rgba(56, 189, 248, 0.4);
}}

/* Typography */
QLabel {{
    color: #f8fafc;
}}

QLabel.CardTitle {{
    color: #94a3b8;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}

QLabel.CardValue {{
    color: #ffffff;
    font-size: 24px;
    font-weight: 800;
    margin-top: 4px;
}}

QLabel.CardSubtitle {{
    color: #94a3b8;
    font-size: 11px;
    margin-top: 2px;
}}

QLabel.PageTitle {{
    font-size: 22px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 0.2px;
}}

QLabel.PageSubtitle {{
    font-size: 13px;
    color: #94a3b8;
    margin-bottom: 8px;
}}

/* Buttons */
QPushButton.PrimaryButton {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #2563eb);
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: 600;
    font-size: 13px;
    min-height: 30px;
}}

QPushButton.PrimaryButton:hover {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0ea5e9, stop:1 #3b82f6);
}}

QPushButton.PrimaryButton:pressed {{
    background-color: #0369a1;
}}

QPushButton.PrimaryButton:disabled {{
    background-color: #1e293b;
    color: #64748b;
}}

QPushButton.SecondaryButton {{
    background-color: #162033;
    color: #e2e8f0;
    border: 1px solid rgba(51, 65, 85, 0.8);
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
    font-size: 12px;
    min-height: 28px;
}}

QPushButton.SecondaryButton:hover {{
    background-color: #1e293b;
    border-color: #38bdf8;
    color: #ffffff;
}}

QPushButton.SecondaryButton:pressed {{
    background-color: #0f172a;
}}

QPushButton.DangerButton {{
    background-color: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid rgba(248, 113, 113, 0.5);
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    min-height: 28px;
}}

QPushButton.DangerButton:hover {{
    background-color: #ef4444;
    color: #ffffff;
}}

/* Form Inputs with Proper Vertical Centering and No Text Clipping */
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: #090e17;
    color: #f8fafc;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 13px;
    min-height: 28px;
    selection-background-color: #0284c7;
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: #38bdf8;
}}

/* Dropdowns with generous height and non-clipped text */
QComboBox {{
    background-color: #090e17;
    color: #f8fafc;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 5px 28px 5px 10px;
    font-size: 13px;
    min-height: 28px;
    selection-background-color: #0284c7;
}}

QComboBox:focus {{
    border-color: #38bdf8;
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid rgba(51, 65, 85, 0.5);
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}}

QComboBox QAbstractItemView {{
    background-color: #0d1524;
    color: #f8fafc;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 4px;
    outline: none;
}}

QComboBox QAbstractItemView::item {{
    min-height: 26px;
    padding: 4px 8px;
    border-radius: 4px;
}}

QComboBox QAbstractItemView::item:selected {{
    background-color: #0284c7;
    color: #ffffff;
}}

/* Tables: STRICT FIX for White-on-White Text and Cut-off Columns */
QTableWidget {{
    background-color: #0d1524;
    alternate-background-color: #121c2e;
    gridline-color: rgba(51, 65, 85, 0.4);
    border: 1px solid rgba(51, 65, 85, 0.7);
    border-radius: 6px;
    color: #f8fafc;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
    outline: none;
}}

QTableWidget::item {{
    color: #f8fafc;
    padding: 6px 8px;
    border: none;
}}

QTableWidget::item:selected {{
    background-color: #0284c7;
    color: #ffffff;
}}

QTableWidget::item:hover {{
    background-color: rgba(56, 189, 248, 0.15);
}}

QHeaderView::section {{
    background-color: #090e17;
    color: #94a3b8;
    padding: 8px 10px;
    border: none;
    border-bottom: 2px solid #1e293b;
    border-right: 1px solid rgba(51, 65, 85, 0.3);
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: #090d16;
    width: 6px;
    border-radius: 3px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: #334155;
    min-height: 24px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical:hover {{
    background: #38bdf8;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: #090d16;
    height: 6px;
    border-radius: 3px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background: #334155;
    min-width: 24px;
    border-radius: 3px;
}}

QScrollBar::handle:horizontal:hover {{
    background: #38bdf8;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Status Bar */
QStatusBar {{
    background-color: #080d17;
    color: #94a3b8;
    border-top: 1px solid rgba(51, 65, 85, 0.5);
    font-size: 11px;
    padding: 4px;
}}

/* Checkboxes */
QCheckBox {{
    color: #f8fafc;
    spacing: 8px;
    font-size: 13px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #334155;
    background-color: #090e17;
}}

QCheckBox::indicator:checked {{
    background-color: #0284c7;
    border-color: #38bdf8;
}}
"""
