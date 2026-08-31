"""
Main Application Window.
Integrates the Hunter Panel, Chromium Web Browser View, and Settings with instant Dark/Light Mode switching.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QFrame, QPushButton, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor

from ui.styles import DARK_THEME, LIGHT_THEME
from ui.hunter_tab import HunterTab
from ui.browser_view import BrowserView
from ui.settings_tab import SettingsTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Espião & Hunter Browser — Rastreador de Domínios Expirados")
        self.resize(1380, 890)
        self.setMinimumSize(1040, 700)
        
        self.is_dark_mode = True
        self.setStyleSheet(DARK_THEME)

        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 10, 12, 12)
        main_layout.setSpacing(10)

        # 1. Header Bar
        header = QFrame()
        header.setObjectName("header_bar")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 6, 14, 6)
        header_layout.setSpacing(12)

        lbl_logo = QLabel("🎯 YOUTUBE ESPIÃO & HUNTER BROWSER")
        lbl_logo.setObjectName("header_logo")
        
        lbl_subtitle = QLabel("•  Minerador de Vídeos, Métricas & Validador de Domínios Expirados")
        lbl_subtitle.setObjectName("header_subtitle")

        header_layout.addWidget(lbl_logo)
        header_layout.addWidget(lbl_subtitle)
        header_layout.addStretch()

        # Theme Switcher Button
        self.btn_theme = QPushButton("☀️ Modo Claro")
        self.btn_theme.setObjectName("btn_theme_toggle")
        self.btn_theme.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_theme.clicked.connect(self._toggle_theme)
        header_layout.addWidget(self.btn_theme)

        lbl_version = QLabel("v1.3.0")
        lbl_version.setObjectName("header_version")
        header_layout.addWidget(lbl_version)

        main_layout.addWidget(header)

        # 2. Main Tab Widget
        self.main_tabs = QTabWidget()
        self.main_tabs.setObjectName("main_app_tabs")

        # Tab 1: Hunter Tab
        self.hunter_tab = HunterTab()
        self.hunter_tab.navigate_url_requested.connect(self._on_navigate_to_browser)
        self.main_tabs.addTab(self.hunter_tab, "🎯 Painel Espião & Mineração")

        # Tab 2: Integrated Web Browser (Chromium)
        self.browser_view = BrowserView()
        self.main_tabs.addTab(self.browser_view, "🌐 Navegador Web Integrado")

        # Tab 3: Settings & Whitelist
        self.settings_tab = SettingsTab()
        self.main_tabs.addTab(self.settings_tab, "⚙️ Configurações & Whitelist")

        main_layout.addWidget(self.main_tabs, 1)

    def _toggle_theme(self):
        """Toggle between Dark and Light themes instantly across the entire application."""
        app = QApplication.instance()
        if self.is_dark_mode:
            # Switch to Light Mode
            self.is_dark_mode = False
            theme = LIGHT_THEME
            self.btn_theme.setText("🌙 Modo Escuro")
        else:
            # Switch to Dark Mode
            self.is_dark_mode = True
            theme = DARK_THEME
            self.btn_theme.setText("☀️ Modo Claro")

        self.setStyleSheet(theme)
        if app:
            app.setStyleSheet(theme)

    def _on_navigate_to_browser(self, url: str):
        """Navigate to URL in embedded browser and switch to Browser tab."""
        self.browser_view.navigate_to(url)
        self.main_tabs.setCurrentIndex(1)
