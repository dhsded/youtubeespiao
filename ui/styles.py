"""
Enterprise Professional Theme System for YouTube Espião.
Includes Dark and Light Modes with subtle, high-contrast, modern corporate aesthetics.
"""

DARK_THEME = """
/* ================= GLOBAL BASE (DARK) ================= */
QMainWindow, QWidget {
    background-color: #0B0F17;
    color: #F1F5F9;
    font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    font-size: 13px;
}

/* Header Bar */
QFrame#header_bar {
    background-color: #131B2A;
    border: 1px solid #222F44;
    border-radius: 8px;
    padding: 6px;
}

QLabel#header_logo {
    color: #3B82F6;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: 0.5px;
}

QLabel#header_subtitle {
    color: #94A3B8;
    font-size: 13px;
    font-weight: 500;
}

QLabel#header_version {
    color: #64748B;
    font-size: 11px;
    font-weight: 600;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #222F44;
    background-color: #0F172A;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #131B2A;
    color: #94A3B8;
    padding: 10px 22px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #222F44;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #2563EB;
    color: #FFFFFF;
    border-color: #3B82F6;
}

QTabBar::tab:hover:!selected {
    background-color: #1C273C;
    color: #F1F5F9;
}

/* Sub Tabs */
QTabWidget#results_tabs::pane {
    border: 1px solid #222F44;
    background-color: #0D1424;
    border-radius: 8px;
}

/* Stat Cards (Dark) */
QFrame#stat_card {
    background-color: #131B2A;
    border: 1px solid #222F44;
    border-radius: 8px;
}

QFrame#stat_card:hover {
    border-color: #3B82F6;
}

QFrame#stat_card_available {
    background-color: #064E3B;
    border: 1.5px solid #10B981;
    border-radius: 8px;
}

QLabel#stat_title {
    color: #94A3B8;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel#stat_val_videos {
    color: #FFFFFF;
    font-size: 26px;
    font-weight: 800;
}

QLabel#stat_val_views {
    color: #38BDF8;
    font-size: 26px;
    font-weight: 800;
}

QLabel#stat_val_domains {
    color: #A78BFA;
    font-size: 26px;
    font-weight: 800;
}

QLabel#stat_val_available {
    color: #34D399;
    font-size: 26px;
    font-weight: 800;
}

/* Control Panel */
QFrame#controls_container {
    background-color: #131B2A;
    border: 1px solid #222F44;
    border-radius: 8px;
    padding: 12px;
}

/* Inputs & Combos */
QLineEdit {
    background-color: #0B0F17;
    border: 1px solid #2D3D58;
    border-radius: 6px;
    padding: 7px 10px;
    color: #F8FAFC;
    font-size: 13px;
    selection-background-color: #2563EB;
}

QLineEdit:focus {
    border-color: #3B82F6;
    background-color: #0E1626;
}

QComboBox {
    background-color: #0B0F17;
    border: 1px solid #2D3D58;
    border-radius: 6px;
    padding: 6px 10px;
    color: #F8FAFC;
    font-weight: 600;
    font-size: 13px;
    min-height: 22px;
}

QComboBox:focus, QComboBox:hover {
    border-color: #3B82F6;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid #2D3D58;
}

QComboBox QAbstractItemView {
    background-color: #131B2A;
    color: #F8FAFC;
    border: 1px solid #3B82F6;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    padding: 4px;
}

/* SpinBox with spacious text area for 4-digit years */
QSpinBox {
    background-color: #0B0F17;
    border: 1px solid #2D3D58;
    border-radius: 6px;
    padding: 5px 2px 5px 6px;
    color: #F8FAFC;
    font-weight: bold;
    font-size: 13px;
    min-height: 22px;
}

QSpinBox:focus {
    border-color: #3B82F6;
}

QSpinBox::up-button, QSpinBox::down-button {
    width: 16px;
    border: none;
    background: transparent;
}

QCheckBox {
    color: #E2E8F0;
    font-size: 13px;
    font-weight: 600;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #475569;
    background-color: #0B0F17;
}

QCheckBox::indicator:checked {
    background-color: #2563EB;
    border-color: #3B82F6;
}

/* Modern Professional Buttons */
QPushButton {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #2D3D58;
    border-color: #475569;
}

QPushButton:pressed {
    background-color: #162032;
}

QPushButton:disabled {
    background-color: #131B2A;
    color: #475569;
    border-color: #1E293B;
}

/* Primary Start Button */
QPushButton#btn_start_action {
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: 700;
    border: 1px solid #3B82F6;
    padding: 7px 20px;
}

QPushButton#btn_start_action:hover {
    background-color: #1D4ED8;
}

/* Pause Button */
QPushButton#btn_pause_action {
    background-color: #D97706;
    color: #FFFFFF;
    font-weight: 700;
    border: 1px solid #F59E0B;
}

QPushButton#btn_pause_action:hover {
    background-color: #B45309;
}

/* Stop Button */
QPushButton#btn_stop_action {
    background-color: #DC2626;
    color: #FFFFFF;
    font-weight: 700;
    border: 1px solid #EF4444;
}

QPushButton#btn_stop_action:hover {
    background-color: #B91C1C;
}

/* Theme Toggle Button */
QPushButton#btn_theme_toggle {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #334155;
    font-weight: 700;
    padding: 6px 14px;
    border-radius: 6px;
}

QPushButton#btn_theme_toggle:hover {
    background-color: #2D3D58;
    border-color: #3B82F6;
}

/* Success / Export Button */
QPushButton#btn_success {
    background-color: #15803D;
    color: #FFFFFF;
    font-weight: 700;
    border: 1px solid #16A34A;
    font-size: 12px;
    padding: 7px 15px;
}

QPushButton#btn_success:hover {
    background-color: #166534;
}

/* Action Inside Table Button */
QPushButton#btn_table_action {
    background-color: #0284C7;
    color: #FFFFFF;
    font-weight: 600;
    padding: 6px 14px;
    font-size: 12px;
    border: none;
    border-radius: 4px;
}

QPushButton#btn_table_action:hover {
    background-color: #0369A1;
}

/* Tables (Professional Dark) */
QTableWidget, QTableView {
    background-color: #0D1424;
    gridline-color: #1A2438;
    border: 1px solid #1E293B;
    border-radius: 8px;
    color: #F1F5F9;
    selection-background-color: #1E3A8A;
    selection-color: #FFFFFF;
    alternate-background-color: #111A2E;
    font-size: 13px;
}

QHeaderView::section {
    background-color: #0B0F17;
    color: #94A3B8;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #222F44;
    border-right: 1px solid #1A2438;
    font-weight: 700;
    font-size: 12px;
}

QHeaderView::section:hover {
    background-color: #131B2A;
    color: #F8FAFC;
}

/* Thumbnail inside Table */
QLabel#thumbnail_label {
    border-radius: 6px;
    border: 1px solid #283548;
    background-color: #1E293B;
}

/* Status Label in Hunter */
QLabel#status_label {
    color: #94A3B8;
    font-size: 13px;
    font-weight: 600;
}

/* Log View (Dark) */
QPlainTextEdit#log_view {
    background-color: #0B0F17;
    color: #A5B4FC;
    font-family: 'Consolas', monospace;
    font-size: 12px;
    border: 1px solid #222F44;
    border-radius: 8px;
    padding: 8px;
}

/* Progress Bar */
QProgressBar {
    background-color: #0B0F17;
    border: 1px solid #222F44;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    color: #FFFFFF;
    font-size: 10px;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #2563EB;
    border-radius: 5px;
}

/* Pagination Bar */
QFrame#pagination_bar {
    background-color: #131B2A;
    border: 1px solid #222F44;
    border-radius: 6px;
    padding: 4px;
}

/* Scrollbars */
QScrollBar:vertical {
    background-color: #0B0F17;
    width: 10px;
    margin: 0;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #222F44;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #3B82F6;
}

QScrollBar:horizontal {
    background-color: #0B0F17;
    height: 10px;
    margin: 0;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #222F44;
    min-width: 20px;
    border-radius: 5px;
}

/* Browser Address Bar */
QLineEdit#browser_url_bar {
    background-color: #131B2A;
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 7px 16px;
    font-size: 13px;
    color: #F8FAFC;
}

QLineEdit#browser_url_bar:focus {
    border-color: #2563EB;
    background-color: #0B0F17;
}
"""


LIGHT_THEME = """
/* ================= GLOBAL BASE (LIGHT) ================= */
QMainWindow, QWidget {
    background-color: #F1F5F9;
    color: #0F172A;
    font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    font-size: 13px;
}

/* Header Bar */
QFrame#header_bar {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 6px;
}

QLabel#header_logo {
    color: #2563EB;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: 0.5px;
}

QLabel#header_subtitle {
    color: #64748B;
    font-size: 13px;
    font-weight: 500;
}

QLabel#header_version {
    color: #94A3B8;
    font-size: 11px;
    font-weight: 600;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #CBD5E1;
    background-color: #FFFFFF;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #E2E8F0;
    color: #475569;
    padding: 10px 22px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #CBD5E1;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #2563EB;
    color: #FFFFFF;
    border-color: #2563EB;
}

QTabBar::tab:hover:!selected {
    background-color: #CBD5E1;
    color: #0F172A;
}

/* Sub Tabs */
QTabWidget#results_tabs::pane {
    border: 1px solid #CBD5E1;
    background-color: #FFFFFF;
    border-radius: 8px;
}

/* Stat Cards (Light) */
QFrame#stat_card {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
}

QFrame#stat_card:hover {
    border-color: #2563EB;
}

QFrame#stat_card_available {
    background-color: #DCFCE7;
    border: 1.5px solid #16A34A;
    border-radius: 8px;
}

QLabel#stat_title {
    color: #64748B;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel#stat_val_videos {
    color: #0F172A;
    font-size: 26px;
    font-weight: 800;
}

QLabel#stat_val_views {
    color: #0284C7;
    font-size: 26px;
    font-weight: 800;
}

QLabel#stat_val_domains {
    color: #7C3AED;
    font-size: 26px;
    font-weight: 800;
}

QLabel#stat_val_available {
    color: #16A34A;
    font-size: 26px;
    font-weight: 800;
}

/* Control Panel */
QFrame#controls_container {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 12px;
}

/* Inputs & Combos */
QLineEdit {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 7px 10px;
    color: #0F172A;
    font-size: 13px;
    selection-background-color: #2563EB;
}

QLineEdit:focus {
    border-color: #2563EB;
    background-color: #FFFFFF;
}

QComboBox {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 6px 10px;
    color: #0F172A;
    font-weight: 600;
    font-size: 13px;
    min-height: 22px;
}

QComboBox:focus, QComboBox:hover {
    border-color: #2563EB;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid #CBD5E1;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #2563EB;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    padding: 4px;
}

/* SpinBox with spacious text area for 4-digit years */
QSpinBox {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 5px 2px 5px 6px;
    color: #0F172A;
    font-weight: bold;
    font-size: 13px;
    min-height: 22px;
}

QSpinBox:focus {
    border-color: #2563EB;
}

QSpinBox::up-button, QSpinBox::down-button {
    width: 16px;
    border: none;
    background: transparent;
}

QCheckBox {
    color: #334155;
    font-size: 13px;
    font-weight: 600;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #94A3B8;
    background-color: #F8FAFC;
}

QCheckBox::indicator:checked {
    background-color: #2563EB;
    border-color: #2563EB;
}

/* Buttons */
QPushButton {
    background-color: #E2E8F0;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #CBD5E1;
    border-color: #94A3B8;
}

QPushButton:pressed {
    background-color: #94A3B8;
}

QPushButton:disabled {
    background-color: #F1F5F9;
    color: #94A3B8;
    border-color: #E2E8F0;
}

/* Primary Start Button */
QPushButton#btn_start_action {
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: 700;
    border: 1px solid #1D4ED8;
    padding: 7px 20px;
}

QPushButton#btn_start_action:hover {
    background-color: #1D4ED8;
}

/* Pause Button */
QPushButton#btn_pause_action {
    background-color: #D97706;
    color: #FFFFFF;
    font-weight: 700;
    border: 1px solid #B45309;
}

QPushButton#btn_pause_action:hover {
    background-color: #B45309;
}

/* Stop Button */
QPushButton#btn_stop_action {
    background-color: #DC2626;
    color: #FFFFFF;
    font-weight: 700;
    border: 1px solid #B91C1C;
}

QPushButton#btn_stop_action:hover {
    background-color: #B91C1C;
}

/* Theme Toggle Button */
QPushButton#btn_theme_toggle {
    background-color: #E2E8F0;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    font-weight: 700;
    padding: 6px 14px;
    border-radius: 6px;
}

QPushButton#btn_theme_toggle:hover {
    background-color: #CBD5E1;
    border-color: #2563EB;
}

/* Success / Export Button */
QPushButton#btn_success {
    background-color: #16A34A;
    color: #FFFFFF;
    font-weight: 700;
    border: 1px solid #15803D;
    font-size: 12px;
    padding: 7px 15px;
}

QPushButton#btn_success:hover {
    background-color: #15803D;
}

/* Action Inside Table Button */
QPushButton#btn_table_action {
    background-color: #0284C7;
    color: #FFFFFF;
    font-weight: 600;
    padding: 6px 14px;
    font-size: 12px;
    border: none;
    border-radius: 4px;
}

QPushButton#btn_table_action:hover {
    background-color: #0369A1;
}

/* Tables (Professional Light) */
QTableWidget, QTableView {
    background-color: #FFFFFF;
    gridline-color: #E2E8F0;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    color: #0F172A;
    selection-background-color: #DBEAFE;
    selection-color: #1E3A8A;
    alternate-background-color: #F8FAFC;
    font-size: 13px;
}

QHeaderView::section {
    background-color: #F1F5F9;
    color: #475569;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #CBD5E1;
    border-right: 1px solid #E2E8F0;
    font-weight: 700;
    font-size: 12px;
}

QHeaderView::section:hover {
    background-color: #E2E8F0;
    color: #0F172A;
}

/* Thumbnail inside Table */
QLabel#thumbnail_label {
    border-radius: 6px;
    border: 1px solid #CBD5E1;
    background-color: #F1F5F9;
}

/* Status Label in Hunter */
QLabel#status_label {
    color: #475569;
    font-size: 13px;
    font-weight: 600;
}

/* Log View (Light) */
QPlainTextEdit#log_view {
    background-color: #FFFFFF;
    color: #1E293B;
    font-family: 'Consolas', monospace;
    font-size: 12px;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 8px;
}

/* Progress Bar */
QProgressBar {
    background-color: #E2E8F0;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    color: #0F172A;
    font-size: 10px;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #2563EB;
    border-radius: 5px;
}

/* Pagination Bar */
QFrame#pagination_bar {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 4px;
}

/* Scrollbars */
QScrollBar:vertical {
    background-color: #F1F5F9;
    width: 10px;
    margin: 0;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #CBD5E1;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #2563EB;
}

QScrollBar:horizontal {
    background-color: #F1F5F9;
    height: 10px;
    margin: 0;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #CBD5E1;
    min-width: 20px;
    border-radius: 5px;
}

/* Browser Address Bar */
QLineEdit#browser_url_bar {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 16px;
    padding: 7px 16px;
    font-size: 13px;
    color: #0F172A;
}

QLineEdit#browser_url_bar:focus {
    border-color: #2563EB;
    background-color: #FFFFFF;
}
"""
