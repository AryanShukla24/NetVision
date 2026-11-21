"""
NetVision - Professional Dark Theme & Stylesheet (QSS)
Modern desktop design system inspired by slate/zinc Tailwind color palettes.
"""

from netvision.config import COLORS

DARK_THEME_QSS = f"""
/* Global Reset and Main Window */
QMainWindow, QWidget {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}}

/* Sidebar Styling */
#Sidebar {{
    background-color: {COLORS['bg_surface']};
    border-right: 1px solid {COLORS['border']};
    min-width: 230px;
    max-width: 250px;
}}

#SidebarHeader {{
    padding: 16px 12px;
    border-bottom: 1px solid {COLORS['border']};
}}

#SidebarAppTitle {{
    font-size: 18px;
    font-weight: 700;
    color: {COLORS['primary']};
}}

#SidebarAppSubtitle {{
    font-size: 11px;
    color: {COLORS['text_muted']};
}}

/* Navigation Buttons */
QPushButton.NavButton {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    text-align: left;
    padding: 10px 14px;
    border-radius: 8px;
    border: none;
    font-size: 13px;
    font-weight: 500;
    margin: 2px 8px;
}}

QPushButton.NavButton:hover {{
    background-color: {COLORS['bg_surface_hover']};
    color: {COLORS['text_primary']};
}}

QPushButton.NavButton:checked, QPushButton.NavButton[active="true"] {{
    background-color: {COLORS['primary_dark']};
    color: #ffffff;
    font-weight: 600;
}}

/* Card Containers */
QFrame.MetricCard, QFrame.ContentCard {{
    background-color: {COLORS['bg_surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    padding: 14px;
}}

QFrame.MetricCard:hover {{
    border-color: {COLORS['border_light']};
}}

/* Typography */
QLabel.CardTitle {{
    color: {COLORS['text_muted']};
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QLabel.CardValue {{
    color: {COLORS['text_primary']};
    font-size: 24px;
    font-weight: 700;
    margin-top: 4px;
}}

QLabel.CardSubtitle {{
    color: {COLORS['text_secondary']};
    font-size: 11px;
    margin-top: 2px;
}}

QLabel.PageTitle {{
    font-size: 22px;
    font-weight: 700;
    color: {COLORS['text_primary']};
}}

QLabel.PageSubtitle {{
    font-size: 13px;
    color: {COLORS['text_secondary']};
    margin-bottom: 10px;
}}

/* Standard Push Buttons */
QPushButton.PrimaryButton {{
    background-color: {COLORS['primary_dark']};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
}}

QPushButton.PrimaryButton:hover {{
    background-color: {COLORS['primary']};
    color: #0f172a;
}}

QPushButton.PrimaryButton:pressed {{
    background-color: #0369a1;
}}

QPushButton.PrimaryButton:disabled {{
    background-color: #334155;
    color: #64748b;
}}

QPushButton.SecondaryButton {{
    background-color: {COLORS['bg_surface']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 500;
}}

QPushButton.SecondaryButton:hover {{
    background-color: {COLORS['bg_surface_hover']};
    border-color: {COLORS['border_light']};
}}

QPushButton.DangerButton {{
    background-color: rgba(239, 68, 68, 0.2);
    color: {COLORS['danger']};
    border: 1px solid {COLORS['danger']};
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
}}

QPushButton.DangerButton:hover {{
    background-color: {COLORS['danger']};
    color: #ffffff;
}}

/* Form Inputs */
QLineEdit, QComboBox, QSpinBox {{
    background-color: #090d16;
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 7px 10px;
    selection-background-color: {COLORS['primary_dark']};
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border-color: {COLORS['primary']};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_surface']};
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['primary_dark']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 4px;
}}

/* Tables */
QTableWidget {{
    background-color: {COLORS['bg_surface']};
    gridline-color: {COLORS['border']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['primary_dark']};
    selection-color: #ffffff;
}}

QHeaderView::section {{
    background-color: #141e30;
    color: {COLORS['text_secondary']};
    padding: 8px;
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    font-weight: 600;
    font-size: 12px;
}}

QTableWidget::item {{
    padding: 6px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: {COLORS['bg_dark']};
    width: 8px;
    border-radius: 4px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['border_light']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {COLORS['bg_dark']};
    height: 8px;
    border-radius: 4px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background: {COLORS['border']};
    min-width: 20px;
    border-radius: 4px;
}}

/* Progress Bar */
QProgressBar {{
    background-color: #090d16;
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    text-align: center;
    color: {COLORS['text_primary']};
    font-weight: 600;
    height: 18px;
}}

QProgressBar::chunk {{
    background-color: {COLORS['primary']};
    border-radius: 5px;
}}

/* Tabs */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['bg_surface']};
    top: -1px;
}}

QTabBar::tab {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['bg_surface']};
    color: {COLORS['primary']};
    font-weight: 600;
}}
"""
