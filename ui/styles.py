"""
Modern YouTube-Inspired Theme System for YouTube Espião.
Features:
- Clean, minimal, standardized aesthetics modeled after YouTube & YouTube Studio.
- No harsh neon rainbow gradients; coherent Charcoal, Slate, Graphite, and YouTube Red color palette.
- High-contrast typography and effortless legibility in both Dark and Light modes.
- Pixel-perfect components: pill chips, flat cards, sleek inputs, and refined data tables.
"""

DARK_THEME = """
/* ================= GLOBAL BASE (YOUTUBE DARK) ================= */
QMainWindow, QWidget {
    background-color: #0F0F0F;
    color: #F1F1F1;
    font-family: 'Segoe UI', 'Roboto', 'Inter', -apple-system, sans-serif;
    font-size: 13px;
}

/* Tooltip */
QToolTip {
    background-color: #212121;
    color: #FFFFFF;
    border: 1px solid #3F3F3F;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 12px;
}

/* Header Bar */
QFrame#header_bar {
    background-color: #0F0F0F;
    border-bottom: 1px solid #272727;
    padding: 8px 12px;
}

QLabel#header_logo {
    color: #FFFFFF;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: 0.5px;
}

QLabel#header_subtitle {
    color: #AAAAAA;
    font-size: 12px;
    font-weight: 500;
}

QLabel#header_version {
    color: #717171;
    font-size: 11px;
    font-weight: 700;
    background-color: #1F1F1F;
    border: 1px solid #333333;
    padding: 2px 8px;
    border-radius: 10px;
}

/* Tabs (YouTube Chips Style) */
QTabWidget::pane {
    border: 1px solid #272727;
    background-color: #0F0F0F;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #212121;
    color: #AAAAAA;
    padding: 9px 20px;
    margin-right: 6px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #2F2F2F;
}

QTabBar::tab:selected {
    background-color: #CC0000;
    color: #FFFFFF;
    border-color: #FF0000;
    font-weight: 700;
}

QTabBar::tab:hover:!selected {
    background-color: #2F2F2F;
    color: #F1F1F1;
}

/* Sub Tabs */
QTabWidget#results_tabs::pane {
    border: 1px solid #272727;
    background-color: #121212;
    border-radius: 8px;
}

/* Stat Cards (YouTube Studio Metrics) */
QFrame#stat_card {
    background-color: #181818;
    border: 1px solid #272727;
    border-radius: 8px;
}

QFrame#stat_card:hover {
    border-color: #3F3F3F;
}

QFrame#stat_card_available {
    background-color: #112217;
    border: 1px solid #16A34A;
    border-radius: 8px;
}

QFrame#stat_card_available:hover {
    border-color: #22C55E;
}

QFrame#stat_card_instagram {
    background-color: #210F23;
    border: 1px solid #D946EF;
    border-radius: 8px;
}

QFrame#stat_card_instagram:hover {
    border-color: #F43F5E;
}

QLabel#stat_title {
    color: #AAAAAA;
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
    color: #F1F1F1;
    font-size: 26px;
    font-weight: 800;
}

QLabel#stat_val_domains {
    color: #F1F1F1;
    font-size: 26px;
    font-weight: 800;
}

QLabel#stat_val_available {
    color: #4ADE80;
    font-size: 26px;
    font-weight: 800;
}

QLabel#stat_val_instagram {
    color: #F472B6;
    font-size: 26px;
    font-weight: 800;
}

/* Control Panel */
QFrame#controls_container {
    background-color: #181818;
    border: 1px solid #272727;
    border-radius: 8px;
    padding: 10px;
}

/* Inputs & Combos */
QLineEdit {
    background-color: #121212;
    border: 1px solid #272727;
    border-radius: 6px;
    padding: 7px 12px;
    color: #F1F1F1;
    font-size: 13px;
    selection-background-color: #CC0000;
    selection-color: #FFFFFF;
}

QLineEdit:hover {
    border-color: #3F3F3F;
}

QLineEdit:focus {
    border-color: #CC0000;
    background-color: #181818;
}

QComboBox {
    background-color: #121212;
    border: 1px solid #272727;
    border-radius: 6px;
    padding: 6px 12px;
    color: #F1F1F1;
    font-weight: 600;
    font-size: 13px;
    min-height: 22px;
}

QComboBox:hover {
    border-color: #3F3F3F;
}

QComboBox:focus {
    border-color: #CC0000;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid #272727;
}

QComboBox QAbstractItemView {
    background-color: #1F1F1F;
    color: #F1F1F1;
    border: 1px solid #383838;
    selection-background-color: #2F2F2F;
    selection-color: #FFFFFF;
    padding: 4px;
}

QSpinBox {
    background-color: #121212;
    border: 1px solid #272727;
    border-radius: 6px;
    padding: 5px 4px 5px 8px;
    color: #F1F1F1;
    font-weight: bold;
    font-size: 13px;
    min-height: 22px;
}

QSpinBox:hover {
    border-color: #3F3F3F;
}

QSpinBox:focus {
    border-color: #CC0000;
}

QSpinBox::up-button, QSpinBox::down-button {
    width: 16px;
    border: none;
    background: transparent;
}

QCheckBox {
    color: #CCCCCC;
    font-size: 13px;
    font-weight: 600;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #3F3F3F;
    background-color: #121212;
}

QCheckBox::indicator:hover {
    border-color: #666666;
}

QCheckBox::indicator:checked {
    background-color: #CC0000;
    border-color: #FF0000;
}

/* Buttons (YouTube Studio Flat Style) */
QPushButton {
    background-color: #272727;
    color: #F1F1F1;
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #3F3F3F;
    border-color: #555555;
    color: #FFFFFF;
}

QPushButton:pressed {
    background-color: #181818;
}

QPushButton:disabled {
    background-color: #1F1F1F;
    color: #555555;
    border-color: #272727;
}

/* Action Buttons */
QPushButton#btn_start_action {
    background-color: #CC0000;
    color: #FFFFFF;
    border: 1px solid #FF0000;
    font-weight: 800;
    letter-spacing: 0.5px;
}

QPushButton#btn_start_action:hover {
    background-color: #E60000;
    border-color: #FF3333;
}

QPushButton#btn_start_action:pressed {
    background-color: #990000;
}

QPushButton#btn_pause_action {
    background-color: #272727;
    color: #FBBF24;
    border: 1px solid #B45309;
    font-weight: 700;
}

QPushButton#btn_pause_action:hover {
    background-color: #38250A;
    border-color: #F59E0B;
}

QPushButton#btn_stop_action {
    background-color: #272727;
    color: #F87171;
    border: 1px solid #991B1B;
    font-weight: 700;
}

QPushButton#btn_stop_action:hover {
    background-color: #3B1C1C;
    border-color: #EF4444;
}

QPushButton#btn_new_instance {
    background-color: #212121;
    color: #FFFFFF;
    border: 1px solid #CC0000;
    font-weight: 700;
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 6px;
}

QPushButton#btn_new_instance:hover {
    background-color: #CC0000;
    border-color: #FF0000;
}

QPushButton#btn_help_action {
    background-color: #212121;
    color: #E5E5E5;
    font-weight: 700;
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 6px;
    border: 1px solid #383838;
}

QPushButton#btn_help_action:hover {
    background-color: #333333;
    color: #FFFFFF;
    border-color: #555555;
}

QPushButton#btn_theme_toggle {
    background-color: #212121;
    color: #E5E5E5;
    border: 1px solid #383838;
    font-weight: 700;
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 6px;
}

QPushButton#btn_theme_toggle:hover {
    background-color: #333333;
    color: #FFFFFF;
    border-color: #555555;
}

QPushButton#btn_tray_action {
    background-color: #212121;
    color: #E5E5E5;
    font-weight: 700;
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 6px;
    border: 1px solid #383838;
}

QPushButton#btn_tray_action:hover {
    background-color: #333333;
    color: #FFFFFF;
    border-color: #555555;
}

QPushButton#btn_close_action {
    background-color: #212121;
    color: #EF4444;
    font-weight: 700;
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 6px;
    border: 1px solid #7F1D1D;
}

QPushButton#btn_close_action:hover {
    background-color: #991B1B;
    color: #FFFFFF;
    border-color: #DC2626;
}

QPushButton#btn_success {
    background-color: #14532D;
    color: #86EFAC;
    border: 1px solid #16A34A;
    font-weight: 700;
}

QPushButton#btn_success:hover {
    background-color: #16A34A;
    color: #FFFFFF;
}

QPushButton#btn_table_action {
    background-color: #212121;
    color: #E5E5E5;
    border: 1px solid #383838;
    font-weight: 700;
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 4px;
    min-height: 26px;
}

QPushButton#btn_table_action:hover {
    background-color: #333333;
    color: #FFFFFF;
    border-color: #555555;
}

QPushButton#btn_table_buy {
    background-color: #14532D;
    color: #86EFAC;
    border: 1px solid #16A34A;
    font-weight: 700;
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 4px;
    min-height: 26px;
}

QPushButton#btn_table_buy:hover {
    background-color: #16A34A;
    color: #FFFFFF;
}

QPushButton#btn_table_purple {
    background-color: #212121;
    color: #AAAAAA;
    border: 1px solid #383838;
    font-weight: 700;
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 4px;
    min-height: 26px;
}

QPushButton#btn_table_purple:hover {
    background-color: #333333;
    color: #FFFFFF;
}

/* Tables (YouTube Studio Grid) */
QTableWidget {
    background-color: #121212;
    color: #F1F1F1;
    gridline-color: #222222;
    border: 1px solid #272727;
    border-radius: 6px;
    selection-background-color: #282828;
    selection-color: #FFFFFF;
}

QTableWidget::item {
    padding: 4px 8px;
    color: #F1F1F1;
}

QHeaderView::section {
    background-color: #181818;
    color: #AAAAAA;
    padding: 6px 8px;
    font-weight: 700;
    font-size: 11px;
    border: 1px solid #272727;
    text-transform: uppercase;
}

QHeaderView::section:hover {
    background-color: #222222;
    color: #FFFFFF;
}

/* Logs */
QPlainTextEdit#log_view {
    background-color: #0A0A0A;
    color: #4ADE80;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    border: 1px solid #272727;
    border-radius: 6px;
    padding: 8px;
}

/* Pagination Bar */
QFrame#pagination_bar {
    background-color: #181818;
    border: 1px solid #272727;
    border-radius: 6px;
}

/* Context Menus */
QMenu {
    background-color: #1F1F1F;
    color: #F1F1F1;
    border: 1px solid #383838;
    padding: 4px;
    border-radius: 6px;
}

QMenu::item {
    padding: 6px 20px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #2F2F2F;
    color: #FFFFFF;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #0F0F0F;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #333333;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #555555;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Browser Specific */
QLineEdit#browser_url_bar {
    background-color: #121212;
    border: 1px solid #272727;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
    color: #F1F1F1;
}

QLineEdit#browser_url_bar:focus {
    border-color: #CC0000;
    background-color: #181818;
}

QWidget#browser_toolbar, QFrame#browser_live_bar {
    background-color: #181818 !important;
    border-bottom: 1px solid #272727 !important;
}
"""


LIGHT_THEME = """
/* ================= GLOBAL BASE (YOUTUBE LIGHT) ================= */
QMainWindow, QWidget {
    background-color: #F9F9F9;
    color: #0F0F0F;
    font-family: 'Segoe UI', 'Roboto', 'Inter', -apple-system, sans-serif;
    font-size: 13px;
}

/* Tooltip */
QToolTip {
    background-color: #FFFFFF;
    color: #0F0F0F;
    border: 1px solid #CCCCCC;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 12px;
}

/* Header Bar */
QFrame#header_bar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E5E5E5;
    padding: 8px 12px;
}

QLabel#header_logo {
    color: #0F0F0F;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: 0.5px;
}

QLabel#header_subtitle {
    color: #606060;
    font-size: 12px;
    font-weight: 500;
}

QLabel#header_version {
    color: #606060;
    font-size: 11px;
    font-weight: 700;
    background-color: #F2F2F2;
    border: 1px solid #E5E5E5;
    padding: 2px 8px;
    border-radius: 10px;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #E5E5E5;
    background-color: #FFFFFF;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #F2F2F2;
    color: #606060;
    padding: 9px 20px;
    margin-right: 6px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #E5E5E5;
}

QTabBar::tab:selected {
    background-color: #CC0000;
    color: #FFFFFF;
    border-color: #CC0000;
    font-weight: 700;
}

QTabBar::tab:hover:!selected {
    background-color: #E5E5E5;
    color: #0F0F0F;
}

/* Sub Tabs */
QTabWidget#results_tabs::pane {
    border: 1px solid #E5E5E5;
    background-color: #FFFFFF;
    border-radius: 8px;
}

/* Stat Cards (Light) */
QFrame#stat_card {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E5;
    border-radius: 8px;
}

QFrame#stat_card:hover {
    border-color: #CCCCCC;
}

QFrame#stat_card_available {
    background-color: #F0FDF4;
    border: 1px solid #22C55E;
    border-radius: 8px;
}

QFrame#stat_card_available:hover {
    border-color: #16A34A;
}

QFrame#stat_card_instagram {
    background-color: #FDF4FF;
    border: 1px solid #D946EF;
    border-radius: 8px;
}

QFrame#stat_card_instagram:hover {
    border-color: #E1306C;
}

QLabel#stat_title {
    color: #606060;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel#stat_val_videos {
    color: #0F0F0F;
    font-size: 26px;
    font-weight: 800;
}

QLabel#stat_val_views {
    color: #0F0F0F;
    font-size: 26px;
    font-weight: 800;
}

QLabel#stat_val_domains {
    color: #0F0F0F;
    font-size: 26px;
    font-weight: 800;
}

QLabel#stat_val_available {
    color: #16A34A;
    font-size: 26px;
    font-weight: 800;
}

QLabel#stat_val_instagram {
    color: #C026D3;
    font-size: 26px;
    font-weight: 800;
}

/* Control Panel */
QFrame#controls_container {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E5;
    border-radius: 8px;
    padding: 10px;
}

/* Inputs & Combos */
QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 6px;
    padding: 7px 12px;
    color: #0F0F0F;
    font-size: 13px;
    selection-background-color: #CC0000;
    selection-color: #FFFFFF;
}

QLineEdit:hover {
    border-color: #999999;
}

QLineEdit:focus {
    border-color: #CC0000;
    background-color: #FFFFFF;
}

QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 6px;
    padding: 6px 12px;
    color: #0F0F0F;
    font-weight: 600;
    font-size: 13px;
    min-height: 22px;
}

QComboBox:hover {
    border-color: #999999;
}

QComboBox:focus {
    border-color: #CC0000;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid #CCCCCC;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #0F0F0F;
    border: 1px solid #CCCCCC;
    selection-background-color: #F2F2F2;
    selection-color: #0F0F0F;
    padding: 4px;
}

QSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 6px;
    padding: 5px 4px 5px 8px;
    color: #0F0F0F;
    font-weight: bold;
    font-size: 13px;
    min-height: 22px;
}

QSpinBox:hover {
    border-color: #999999;
}

QSpinBox:focus {
    border-color: #CC0000;
}

QSpinBox::up-button, QSpinBox::down-button {
    width: 16px;
    border: none;
    background: transparent;
}

QCheckBox {
    color: #0F0F0F;
    font-size: 13px;
    font-weight: 600;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #CCCCCC;
    background-color: #FFFFFF;
}

QCheckBox::indicator:hover {
    border-color: #999999;
}

QCheckBox::indicator:checked {
    background-color: #CC0000;
    border-color: #CC0000;
}

/* Buttons */
QPushButton {
    background-color: #F2F2F2;
    color: #0F0F0F;
    border: 1px solid #E5E5E5;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #E5E5E5;
    border-color: #CCCCCC;
}

QPushButton:pressed {
    background-color: #D5D5D5;
}

QPushButton:disabled {
    background-color: #F8F8F8;
    color: #AAAAAA;
    border-color: #EEEEEE;
}

/* Action Buttons */
QPushButton#btn_start_action {
    background-color: #CC0000;
    color: #FFFFFF;
    border: 1px solid #CC0000;
    font-weight: 800;
    letter-spacing: 0.5px;
}

QPushButton#btn_start_action:hover {
    background-color: #E60000;
    border-color: #E60000;
}

QPushButton#btn_start_action:pressed {
    background-color: #990000;
}

QPushButton#btn_pause_action {
    background-color: #F2F2F2;
    color: #B45309;
    border: 1px solid #F59E0B;
    font-weight: 700;
}

QPushButton#btn_pause_action:hover {
    background-color: #FEF3C7;
}

QPushButton#btn_stop_action {
    background-color: #F2F2F2;
    color: #DC2626;
    border: 1px solid #EF4444;
    font-weight: 700;
}

QPushButton#btn_stop_action:hover {
    background-color: #FEE2E2;
}

QPushButton#btn_new_instance {
    background-color: #F2F2F2;
    color: #0F0F0F;
    border: 1px solid #CC0000;
    font-weight: 700;
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 6px;
}

QPushButton#btn_new_instance:hover {
    background-color: #CC0000;
    color: #FFFFFF;
}

QPushButton#btn_help_action {
    background-color: #F2F2F2;
    color: #0F0F0F;
    font-weight: 700;
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 6px;
    border: 1px solid #E5E5E5;
}

QPushButton#btn_help_action:hover {
    background-color: #E5E5E5;
}

QPushButton#btn_theme_toggle {
    background-color: #F2F2F2;
    color: #0F0F0F;
    border: 1px solid #E5E5E5;
    font-weight: 700;
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 6px;
}

QPushButton#btn_theme_toggle:hover {
    background-color: #E5E5E5;
}

QPushButton#btn_tray_action {
    background-color: #F2F2F2;
    color: #0F0F0F;
    font-weight: 700;
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 6px;
    border: 1px solid #E5E5E5;
}

QPushButton#btn_tray_action:hover {
    background-color: #E5E5E5;
}

QPushButton#btn_close_action {
    background-color: #F2F2F2;
    color: #DC2626;
    font-weight: 700;
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 6px;
    border: 1px solid #FCA5A5;
}

QPushButton#btn_close_action:hover {
    background-color: #DC2626;
    color: #FFFFFF;
    border-color: #DC2626;
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
    background-color: #F2F2F2;
    color: #0F0F0F;
    border: 1px solid #E5E5E5;
    font-weight: 700;
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 4px;
    min-height: 26px;
}

QPushButton#btn_table_action:hover {
    background-color: #E5E5E5;
}

QPushButton#btn_table_buy {
    background-color: #DCFCE7;
    color: #15803D;
    border: 1px solid #86EFAC;
    font-weight: 700;
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 4px;
    min-height: 26px;
}

QPushButton#btn_table_buy:hover {
    background-color: #16A34A;
    color: #FFFFFF;
}

QPushButton#btn_table_purple {
    background-color: #F2F2F2;
    color: #606060;
    border: 1px solid #E5E5E5;
    font-weight: 700;
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 4px;
    min-height: 26px;
}

QPushButton#btn_table_purple:hover {
    background-color: #E5E5E5;
    color: #0F0F0F;
}

/* Tables */
QTableWidget {
    background-color: #FFFFFF;
    color: #0F0F0F;
    gridline-color: #EEEEEE;
    border: 1px solid #E5E5E5;
    border-radius: 6px;
    selection-background-color: #F2F2F2;
    selection-color: #0F0F0F;
}

QTableWidget::item {
    padding: 6px;
    color: #0F0F0F;
}

QHeaderView::section {
    background-color: #F8F8F8;
    color: #606060;
    padding: 8px;
    font-weight: 700;
    font-size: 11px;
    border: 1px solid #E5E5E5;
    text-transform: uppercase;
}

QHeaderView::section:hover {
    background-color: #EEEEEE;
    color: #0F0F0F;
}

/* Logs */
QPlainTextEdit#log_view {
    background-color: #FAFAFA;
    color: #166534;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    font-weight: 700;
    border: 1px solid #E5E5E5;
    border-radius: 6px;
    padding: 8px;
}

/* Pagination Bar */
QFrame#pagination_bar {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E5;
    border-radius: 6px;
}

/* Context Menus */
QMenu {
    background-color: #FFFFFF;
    color: #0F0F0F;
    border: 1px solid #CCCCCC;
    padding: 4px;
    border-radius: 6px;
}

QMenu::item {
    padding: 6px 20px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #F2F2F2;
    color: #0F0F0F;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #F9F9F9;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #CCCCCC;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #999999;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Browser Specific */
QLineEdit#browser_url_bar {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
    color: #0F0F0F;
    font-weight: 600;
}

QLineEdit#browser_url_bar:focus {
    border-color: #CC0000;
    background-color: #FFFFFF;
}

QWidget#browser_toolbar, QFrame#browser_live_bar {
    background-color: #FFFFFF !important;
    border-bottom: 1px solid #E5E5E5 !important;
}
"""
