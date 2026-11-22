"""
NetVision - Professional Dark Modern Theme & Stylesheet (QSS)
Engineered network instrumentation styling inspired by professional telemetry interfaces.
Provides consistent typography, high contrast, non-clipped inputs/dropdowns,
and eliminates generic bubbly SaaS card aesthetics.
"""

from pathlib import Path
from netvision.config import COLORS

_ICONS_DIR = Path(__file__).parent.parent / "resources" / "icons"
CHEVRON_DOWN_PATH = (_ICONS_DIR / "chevron_down.png").as_posix()
CHEVRON_DOWN_HOVER_PATH = (_ICONS_DIR / "chevron_down_hover.png").as_posix()

DARK_THEME_QSS = f"""
/* Global Reset and Main Window */
QMainWindow {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    font-family: 'Inter', 'IBM Plex Sans', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 13px;
}}

QWidget {{
    color: {COLORS['text_primary']};
    font-family: 'Inter', 'IBM Plex Sans', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 13px;
}}

/* Sidebar Navigation */
#Sidebar {{
    background-color: {COLORS['bg_surface']};
    border-right: 1px solid {COLORS['border']};
    min-width: 230px;
    max-width: 250px;
}}

#SidebarHeader {{
    padding: 16px 14px 12px 14px;
    border-bottom: 1px solid {COLORS['border']};
    margin-bottom: 6px;
}}

#SidebarAppTitle {{
    font-size: 18px;
    font-weight: 800;
    color: {COLORS['primary']};
    letter-spacing: 0.5px;
}}

#SidebarAppSubtitle {{
    font-size: 11px;
    color: {COLORS['text_secondary']};
    line-height: 1.3;
    margin-top: 2px;
}}

/* Navigation Buttons with subtle left accent border */
QPushButton.NavButton {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    text-align: left;
    padding: 8px 12px;
    border-radius: 4px;
    border: none;
    border-left: 3px solid transparent;
    font-size: 12px;
    font-weight: 500;
    margin: 1px 6px;
    min-height: 20px;
}}

QPushButton.NavButton:hover {{
    background-color: {COLORS['bg_surface_hover']};
    color: {COLORS['text_bright']};
}}

QPushButton.NavButton:checked, QPushButton.NavButton[active="true"] {{
    background-color: {COLORS['bg_elevated']};
    border-left: 3px solid {COLORS['primary']};
    color: {COLORS['text_bright']};
    font-weight: 600;
}}

/* Metric & Content Cards with restrained borders */
QFrame.MetricCard, QFrame.ContentCard {{
    background-color: {COLORS['bg_elevated']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 12px;
}}

QFrame.MetricCard:hover {{
    border-color: {COLORS['border_light']};
}}

/* Typography */
QLabel {{
    color: {COLORS['text_primary']};
}}

QLabel.CardTitle {{
    color: {COLORS['text_secondary']};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.4px;
}}

QLabel.CardValue {{
    color: {COLORS['text_bright']};
    font-family: 'Consolas', 'Cascadia Mono', 'JetBrains Mono', monospace;
    font-size: 20px;
    font-weight: 700;
    margin-top: 3px;
}}

QLabel.CardSubtitle {{
    color: {COLORS['text_muted']};
    font-size: 11px;
    margin-top: 2px;
}}

QLabel.PageTitle {{
    font-size: 18px;
    font-weight: 700;
    color: {COLORS['text_bright']};
    letter-spacing: 0.2px;
}}

QLabel.PageSubtitle {{
    font-size: 12px;
    color: {COLORS['text_secondary']};
    margin-bottom: 4px;
}}

/* Buttons */
QPushButton.PrimaryButton {{
    background-color: {COLORS['primary']};
    color: #0b1118;
    border: 1px solid {COLORS['primary_dark']};
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: 700;
    font-size: 12px;
    min-height: 28px;
}}

QPushButton.PrimaryButton:hover {{
    background-color: #36C5DB;
}}

QPushButton.PrimaryButton:pressed {{
    background-color: {COLORS['primary_dark']};
}}

QPushButton.PrimaryButton:disabled {{
    background-color: {COLORS['bg_surface']};
    border-color: {COLORS['border']};
    color: {COLORS['text_muted']};
}}

QPushButton.SecondaryButton {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: 500;
    font-size: 12px;
    min-height: 28px;
}}

QPushButton.SecondaryButton:hover {{
    background-color: {COLORS['bg_surface_hover']};
    border-color: {COLORS['primary']};
    color: {COLORS['text_bright']};
}}

QPushButton.SecondaryButton:pressed {{
    background-color: {COLORS['bg_dark']};
}}

QPushButton.DangerButton {{
    background-color: {COLORS['danger_bg']};
    color: {COLORS['danger']};
    border: 1px solid {COLORS['danger']};
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: 600;
    font-size: 12px;
    min-height: 28px;
}}

QPushButton.DangerButton:hover {{
    background-color: {COLORS['danger']};
    color: #ffffff;
}}

/* Form Inputs with Proper Vertical Centering */
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_input']};
    color: {COLORS['text_bright']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 5px 8px;
    font-size: 12px;
    font-family: 'Consolas', 'Cascadia Mono', 'Segoe UI', monospace;
    min-height: 28px;
    selection-background-color: {COLORS['primary_dark']};
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {COLORS['border_focus']};
}}

/* Dropdowns with generous height, clearly visible arrow, and non-clipped text */
QComboBox {{
    background-color: {COLORS['bg_input']};
    color: {COLORS['text_bright']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px 34px 6px 12px;
    font-size: 12px;
    min-height: 28px;
    selection-background-color: {COLORS['primary_dark']};
}}

QComboBox:hover {{
    border-color: {COLORS['border_light']};
}}

QComboBox:focus {{
    border-color: {COLORS['border_focus']};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 26px;
    border-left: 1px solid {COLORS['border']};
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
    background-color: transparent;
}}

QComboBox::drop-down:hover {{
    background-color: {COLORS['primary_subtle']};
}}

QComboBox::down-arrow {{
    image: url('{CHEVRON_DOWN_PATH}');
    width: 12px;
    height: 12px;
}}

QComboBox::down-arrow:hover {{
    image: url('{CHEVRON_DOWN_HOVER_PATH}');
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['primary_dark']};
    selection-color: #ffffff;
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    padding: 4px;
    outline: none;
}}

QComboBox QAbstractItemView::item {{
    min-height: 26px;
    padding: 4px 8px;
    border-radius: 2px;
}}

QComboBox QAbstractItemView::item:selected {{
    background-color: {COLORS['primary_dark']};
    color: #ffffff;
}}

/* Tables: Professional Instrumentation Table Styling */
QTableWidget {{
    background-color: {COLORS['bg_surface']};
    alternate-background-color: {COLORS['bg_dark']};
    gridline-color: {COLORS['border']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['primary_subtle']};
    selection-color: {COLORS['text_bright']};
    outline: none;
}}

QTableWidget::item {{
    color: {COLORS['text_primary']};
    padding: 4px 8px;
    border: none;
}}

QTableWidget::item:selected {{
    background-color: {COLORS['primary_subtle']};
    color: {COLORS['text_bright']};
}}

QTableWidget::item:hover {{
    background-color: {COLORS['bg_surface_hover']};
}}

QHeaderView::section {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_secondary']};
    padding: 6px 8px;
    border: none;
    border-bottom: 2px solid {COLORS['border']};
    border-right: 1px solid {COLORS['border']};
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.3px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: {COLORS['bg_dark']};
    width: 6px;
    border-radius: 3px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['border_light']};
    min-height: 24px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['primary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {COLORS['bg_dark']};
    height: 6px;
    border-radius: 3px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background: {COLORS['border_light']};
    min-width: 24px;
    border-radius: 3px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {COLORS['primary']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Status Bar */
QStatusBar {{
    background-color: {COLORS['bg_surface']};
    color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['border']};
    font-size: 11px;
    padding: 3px;
}}

/* Checkboxes */
QCheckBox {{
    color: {COLORS['text_primary']};
    spacing: 6px;
    font-size: 12px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid {COLORS['border_light']};
    background-color: {COLORS['bg_input']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['primary_dark']};
    border-color: {COLORS['primary']};
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    background: {COLORS['bg_dark']};
    border-radius: 4px;
    padding: 8px;
}}

QTabBar::tab {{
    background: {COLORS['bg_surface']};
    color: {COLORS['text_secondary']};
    padding: 7px 14px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-weight: 500;
    font-size: 12px;
    border: 1px solid {COLORS['border']};
    border-bottom: none;
}}

QTabBar::tab:selected {{
    background: {COLORS['bg_elevated']};
    color: {COLORS['text_bright']};
    font-weight: 600;
    border-top: 2px solid {COLORS['primary']};
}}

QTabBar::tab:hover:!selected {{
    background: {COLORS['bg_surface_hover']};
    color: {COLORS['text_bright']};
}}
"""
