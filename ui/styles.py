"""
Enterprise Professional Theme System for YouTube Espião.
Includes Dark and Light Modes with subtle, high-contrast, modern corporate aesthetics.
Ensures 100% legibility in both White (Light) and Dark themes.
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
    border: 1px solid #222F44;
    border-radius: 6px;
    padding: 7px 10px;
    color: #F8FAFC;
    font-size: 13px;
    selection-background-color: #2563EB;
}

QLineEdit:focus {
    border-color: #3B82F6;
    background-color: #0F172A;
}

QComboBox {
    background-color: #0B0F17;
    border: 1px solid #222F44;
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
    border-left: 1px solid #222F44;
}

QComboBox QAbstractItemView {
    background-color: #131B2A;
    color: #F8FAFC;
    border: 1px solid #3B82F6;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    padding: 4px;
}

QSpinBox {
    background-color: #0B0F17;
    border: 1px solid #222F44;
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
    color: #CBD5E1;
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

/* Buttons */
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
    background-color: #334155;
    border-color: #475569;
}

QPushButton:pressed {
    background-color: #0F172A;
}

QPushButton:disabled {
    background-color: #1E293B;
    color: #64748B;
    border-color: #334155;
}

/* Action Buttons */
QPushButton#btn_start_action {
    background-color: #2563EB;
    color: #FFFFFF;
    border: 1px solid #3B82F6;
    font-weight: 700;
}

QPushButton#btn_start_action:hover {
    background-color: #1D4ED8;
}

QPushButton#btn_pause_action {
    background-color: #D97706;
    color: #FFFFFF;
    border: 1px solid #F59E0B;
    font-weight: 700;
}

QPushButton#btn_pause_action:hover {
    background-color: #B45309;
}

QPushButton#btn_stop_action {
    background-color: #DC2626;
    color: #FFFFFF;
    border: 1px solid #EF4444;
    font-weight: 700;
}

QPushButton#btn_stop_action:hover {
    background-color: #B91C1C;
}

QPushButton#btn_help_action {
    background-color: #0284C7;
    color: #FFFFFF;
    font-weight: 800;
    font-size: 12px;
    padding: 6px 14px;
    border-radius: 6px;
    border: 1px solid #38BDF8;
}

QPushButton#btn_help_action:hover {
    background-color: #0EA5E9;
}

QPushButton#btn_theme_toggle {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #334155;
    font-weight: 700;
    font-size: 12px;
}

QPushButton#btn_success {
    background-color: #059669;
    color: #FFFFFF;
    border: 1px solid #10B981;
    font-weight: 600;
}

QPushButton#btn_success:hover {
    background-color: #047857;
}

QPushButton#btn_table_action {
    background-color: #1E293B;
    color: #38BDF8;
    border: 1px solid #0284C7;
    font-weight: 700;
    padding: 4px 10px;
}

QPushButton#btn_table_action:hover {
    background-color: #0284C7;
    color: #FFFFFF;
}

QPushButton#btn_table_buy {
    background-color: #059669;
    color: #FFFFFF;
    border: 1px solid #10B981;
    font-weight: 700;
    padding: 4px 10px;
}

QPushButton#btn_table_buy:hover {
    background-color: #10B981;
}

/* Tables */
QTableWidget {
    background-color: #0F172A;
    color: #F8FAFC;
    gridline-color: #1E293B;
    border: 1px solid #222F44;
    border-radius: 6px;
    selection-background-color: #1E3A8A;
    selection-color: #FFFFFF;
}

QTableWidget::item {
    padding: 6px;
    color: #F8FAFC;
}

QHeaderView::section {
    background-color: #131B2A;
    color: #94A3B8;
    padding: 8px;
    font-weight: 700;
    font-size: 12px;
    border: 1px solid #222F44;
    text-transform: uppercase;
}

QHeaderView::section:hover {
    background-color: #1E293B;
    color: #F8FAFC;
}

/* Logs */
QPlainTextEdit#log_view {
    background-color: #080C14;
    color: #10B981;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    border: 1px solid #222F44;
    border-radius: 6px;
    padding: 8px;
}

/* Pagination Bar */
QFrame#pagination_bar {
    background-color: #131B2A;
    border: 1px solid #222F44;
    border-radius: 6px;
}

/* Browser Specific */
QLineEdit#browser_url_bar {
    background-color: #0B0F17;
    border: 1px solid #222F44;
    border-radius: 6px;
    padding: 6px 12px;
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
    color: #334155;
    font-size: 13px;
    font-weight: 600;
}

QLabel#header_version {
    color: #64748B;
    font-size: 11px;
    font-weight: 700;
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
    color: #334155;
    padding: 10px 22px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 700;
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
    color: #475569;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel#stat_val_videos {
    color: #0F172A;
    font-size: 26px;
    font-weight: 900;
}

QLabel#stat_val_views {
    color: #0284C7;
    font-size: 26px;
    font-weight: 900;
}

QLabel#stat_val_domains {
    color: #7C3AED;
    font-size: 26px;
    font-weight: 900;
}

QLabel#stat_val_available {
    color: #15803D;
    font-size: 26px;
    font-weight: 900;
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
    font-weight: 600;
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
    font-weight: 700;
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

QSpinBox {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 5px 2px 5px 6px;
    color: #0F172A;
    font-weight: 800;
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
    color: #0F172A;
    font-size: 13px;
    font-weight: 700;
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
    font-weight: 700;
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

/* Action Buttons */
QPushButton#btn_start_action {
    background-color: #2563EB;
    color: #FFFFFF;
    border: 1px solid #1D4ED8;
    font-weight: 800;
}

QPushButton#btn_start_action:hover {
    background-color: #1D4ED8;
}

QPushButton#btn_pause_action {
    background-color: #D97706;
    color: #FFFFFF;
    border: 1px solid #B45309;
    font-weight: 800;
}

QPushButton#btn_pause_action:hover {
    background-color: #B45309;
}

QPushButton#btn_stop_action {
    background-color: #DC2626;
    color: #FFFFFF;
    border: 1px solid #B91C1C;
    font-weight: 800;
}

QPushButton#btn_stop_action:hover {
    background-color: #B91C1C;
}

QPushButton#btn_help_action {
    background-color: #0284C7;
    color: #FFFFFF;
    font-weight: 800;
    font-size: 12px;
    padding: 6px 14px;
    border-radius: 6px;
    border: 1px solid #0369A1;
}

QPushButton#btn_help_action:hover {
    background-color: #0369A1;
}

QPushButton#btn_theme_toggle {
    background-color: #E2E8F0;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    font-weight: 800;
    font-size: 12px;
}

QPushButton#btn_success {
    background-color: #16A34A;
    color: #FFFFFF;
    border: 1px solid #15803D;
    font-weight: 700;
}

QPushButton#btn_success:hover {
    background-color: #15803D;
}

QPushButton#btn_table_action {
    background-color: #F0F9FF;
    color: #0284C7;
    border: 1px solid #BAE6FD;
    font-weight: 800;
    padding: 4px 10px;
}

QPushButton#btn_table_action:hover {
    background-color: #0284C7;
    color: #FFFFFF;
}

QPushButton#btn_table_buy {
    background-color: #16A34A;
    color: #FFFFFF;
    border: 1px solid #15803D;
    font-weight: 800;
    padding: 4px 10px;
}

QPushButton#btn_table_buy:hover {
    background-color: #15803D;
}

/* Tables */
QTableWidget {
    background-color: #FFFFFF;
    color: #0F172A;
    gridline-color: #E2E8F0;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    selection-background-color: #DBEAFE;
    selection-color: #1E3A8A;
}

QTableWidget::item {
    padding: 6px;
    color: #0F172A;
}

QHeaderView::section {
    background-color: #F1F5F9;
    color: #334155;
    padding: 8px;
    font-weight: 800;
    font-size: 12px;
    border: 1px solid #CBD5E1;
    text-transform: uppercase;
}

QHeaderView::section:hover {
    background-color: #E2E8F0;
    color: #0F172A;
}

/* Logs */
QPlainTextEdit#log_view {
    background-color: #F8FAFC;
    color: #065F46;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    font-weight: 700;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 8px;
}

/* Pagination Bar */
QFrame#pagination_bar {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
}

/* Browser Specific */
QLineEdit#browser_url_bar {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
    color: #0F172A;
    font-weight: 600;
}

QLineEdit#browser_url_bar:focus {
    border-color: #2563EB;
    background-color: #FFFFFF;
}

QWidget#browser_toolbar, QFrame#browser_live_bar {
    background-color: #FFFFFF !important;
    border-bottom: 1px solid #CBD5E1 !important;
}
"""
