"""
Main Application Window.
Features:
- Hunter Panel, Chromium Web Browser View, Settings & Whitelist, and Didactic Help Center.
- Instant Dark/Light Mode switching with 100% crystal-clear contrast.
- System Tray Minimization: Allows the app to run seamlessly in the background with notifications.
"""

import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QFrame, QPushButton, QApplication,
    QSystemTrayIcon, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import (
    QFont, QCursor, QIcon, QAction,
    QPainter, QBrush, QPen, QColor, QPixmap
)

from typing import Optional, Dict
from ui.styles import DARK_THEME, LIGHT_THEME
from core.instance_manager import InstanceManager, get_instance_color
from ui.hunter_tab import HunterTab
from ui.browser_view import BrowserView
from ui.settings_tab import SettingsTab
from ui.help_dialog import HelpDialog

class MainWindow(QMainWindow):
    def __init__(self, initial_target: Optional[str] = None, autostart: bool = False):
        super().__init__()
        self.instance_number = InstanceManager.get_instance_number()
        self.setWindowTitle(f"YouTube Espião v3.2.0 #{self.instance_number} — Rastreador de Domínios Expirados")
        self.resize(1380, 890)
        self.setMinimumSize(1040, 700)
        
        self.is_dark_mode = True
        self.setStyleSheet(DARK_THEME)

        self._init_ui()
        self._init_tray_icon()

        if initial_target:
            self.hunter_tab.input_target.setText(initial_target)

        if autostart:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1200, self.hunter_tab._on_start_or_resume)

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

        # Top Instance Identification Badge with Clean YouTube Studio Pill Style
        color_cfg = get_instance_color(self.instance_number)
        self.badge_instance = QLabel(f"🔢 INSTÂNCIA #{self.instance_number}")
        self.badge_instance.setObjectName("badge_instance")
        self.badge_instance.setStyleSheet(f"""
            QLabel#badge_instance {{
                background-color: #1F1F1F;
                color: {color_cfg['start']};
                font-weight: 800;
                font-size: 11px;
                padding: 4px 10px;
                border-radius: 12px;
                border: 1px solid {color_cfg['start']};
                letter-spacing: 0.5px;
            }}
        """)

        header_layout.addWidget(lbl_logo)
        header_layout.addWidget(self.badge_instance)
        header_layout.addWidget(lbl_subtitle)
        header_layout.addStretch()

        # ➕ Nova Instância Button
        self.btn_new_instance = QPushButton("➕ Nova Instância")
        self.btn_new_instance.setObjectName("btn_new_instance")
        self.btn_new_instance.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_new_instance.setToolTip("Abrir uma nova janela/instância independente do programa sem sair da atual.")
        self.btn_new_instance.clicked.connect(self._spawn_new_instance)
        header_layout.addWidget(self.btn_new_instance)

        # Help Button
        self.btn_help = QPushButton("📖 Ajuda")
        self.btn_help.setObjectName("btn_help_action")
        self.btn_help.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_help.setToolTip("Abrir manual didático explicando todas as fórmulas, métricas e validação de domínios livres.")
        self.btn_help.clicked.connect(self._open_help_dialog)
        header_layout.addWidget(self.btn_help)

        # Theme Switcher Button
        self.btn_theme = QPushButton("☀️ Modo Claro")
        self.btn_theme.setObjectName("btn_theme_toggle")
        self.btn_theme.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_theme.clicked.connect(self._toggle_theme)
        header_layout.addWidget(self.btn_theme)

        # Minimize to Tray Button
        self.btn_minimize_tray = QPushButton("📥 Minimizar")
        self.btn_minimize_tray.setObjectName("btn_tray_action")
        self.btn_minimize_tray.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_minimize_tray.setToolTip("Ocultar a janela na bandeja do sistema mantendo a execução em segundo plano.")
        self.btn_minimize_tray.clicked.connect(self._minimize_to_tray)
        header_layout.addWidget(self.btn_minimize_tray)

        # Close Completely Button
        self.btn_close_app = QPushButton("❌ Fechar")
        self.btn_close_app.setObjectName("btn_close_action")
        self.btn_close_app.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close_app.setToolTip("Encerrar todos os processos e fechar este aplicativo totalmente.")
        self.btn_close_app.clicked.connect(self._force_quit)
        header_layout.addWidget(self.btn_close_app)

        lbl_version = QLabel("v3.2.0")
        lbl_version.setObjectName("header_version")
        header_layout.addWidget(lbl_version)

        main_layout.addWidget(header)

        # 2. Main Tab Widget
        self.main_tabs = QTabWidget()
        self.main_tabs.setObjectName("main_app_tabs")

        # Tab 1: Hunter Tab
        self.hunter_tab = HunterTab()
        self.hunter_tab.navigate_url_requested.connect(self._on_navigate_to_browser)
        self.hunter_tab.live_video_stream.connect(self._on_live_video_stream)
        self.hunter_tab.switch_to_browser_tab.connect(lambda: self.main_tabs.setCurrentIndex(1))
        self.main_tabs.addTab(self.hunter_tab, "🎯 Painel Espião & Mineração")

        # Tab 2: Integrated Web Browser (Chromium)
        self.browser_view = BrowserView()
        self.main_tabs.addTab(self.browser_view, "🌐 Navegador Web Integrado")

        # Tab 3: Settings & Whitelist
        self.settings_tab = SettingsTab()
        self.main_tabs.addTab(self.settings_tab, "⚙️ Configurações & Whitelist")

        main_layout.addWidget(self.main_tabs, 1)

    def _create_tray_icon_with_badge(self, instance_num: int) -> QIcon:
        """Dynamically render a crisp, high-visibility instance number badge onto the system tray icon."""
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, "assets", "icon.png")
        if not os.path.exists(icon_path):
            icon_path = "assets/icon.png"

        pixmap = QPixmap(icon_path) if os.path.exists(icon_path) else QPixmap()
        if pixmap.isNull():
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor("#0F172A"))
        else:
            pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw circular instance badge on top right
        badge_size = 28
        badge_x = 64 - badge_size
        badge_y = 0

        # Unique color per instance number
        color_cfg = get_instance_color(instance_num)

        # Dark border
        painter.setPen(QPen(QColor("#0F172A"), 3))
        painter.setBrush(QBrush(QColor(color_cfg["tray"])))
        painter.drawEllipse(badge_x, badge_y, badge_size, badge_size)

        # Draw bold instance number
        painter.setPen(QColor(color_cfg["text"]))
        font = QFont("Segoe UI", 13, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(badge_x, badge_y, badge_size, badge_size, Qt.AlignmentFlag.AlignCenter, str(instance_num))
        painter.end()

        return QIcon(pixmap)

    def _init_tray_icon(self):
        """Initialize System Tray Icon with background execution menu and dynamic instance badge."""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Set dynamic tray icon with clear instance number badge
        tray_icon = self._create_tray_icon_with_badge(self.instance_number)
        self.tray_icon.setIcon(tray_icon)

        tray_menu = QMenu()

        action_restore = QAction(f"🎯 Abrir YouTube Espião #{self.instance_number}", self)
        action_restore.triggered.connect(self._restore_from_tray)
        tray_menu.addAction(action_restore)

        tray_menu.addSeparator()

        action_start = QAction("🚀 Iniciar / Retomar Varredura", self)
        action_start.triggered.connect(self.hunter_tab._on_start_or_resume)
        tray_menu.addAction(action_start)

        action_pause = QAction("⏸️ Pausar Varredura", self)
        action_pause.triggered.connect(self.hunter_tab._on_toggle_pause)
        tray_menu.addAction(action_pause)

        action_stop = QAction("⏹ Parar Varredura", self)
        action_stop.triggered.connect(self.hunter_tab._on_stop_completely)
        tray_menu.addAction(action_stop)

        tray_menu.addSeparator()

        action_quit = QAction("❌ Fechar Programa Totalmente", self)
        action_quit.triggered.connect(self._force_quit)
        tray_menu.addAction(action_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip(f"YouTube Espião #{self.instance_number} — Mineração em segundo plano")
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self._restore_from_tray()

    def _restore_from_tray(self):
        if hasattr(self, "hunter_tab"):
            self.hunter_tab.set_background_mode(False)
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _optimize_memory_for_background(self):
        """Release unused RAM pages and throttle timers to achieve ultra-low background CPU and memory footprint."""
        import gc
        gc.collect()
        import sys
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
            except Exception:
                pass
        if hasattr(self, "hunter_tab"):
            self.hunter_tab.set_background_mode(True)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized():
                # Standard minimize to Windows Taskbar: keep window in taskbar and throttle background resources
                self._optimize_memory_for_background()
            elif not self.isMinimized():
                if hasattr(self, "hunter_tab"):
                    self.hunter_tab.set_background_mode(False)
        super().changeEvent(event)

    def _minimize_to_tray(self):
        """Explicitly hide window into the system tray area."""
        self.hide()
        self._optimize_memory_for_background()

    def closeEvent(self, event):
        # If crawler is currently active, prompt user with choices
        if hasattr(self, "hunter_tab") and self.hunter_tab.crawler_thread and self.hunter_tab.crawler_thread.isRunning():
            msg = QMessageBox(self)
            msg.setWindowTitle("Fechar YouTube Espião")
            msg.setText("<b>A mineração de vídeos está em andamento.</b><br><br>O que você deseja fazer?")
            btn_close = msg.addButton("❌ Fechar Totalmente", QMessageBox.ButtonRole.DestructiveRole)
            btn_tray = msg.addButton("📥 Minimizar na Bandeja", QMessageBox.ButtonRole.AcceptRole)
            btn_cancel = msg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
            msg.setDefaultButton(btn_tray)
            msg.exec()

            if msg.clickedButton() == btn_close:
                event.accept()
                self._force_quit()
            elif msg.clickedButton() == btn_tray:
                event.ignore()
                self.hide()
                self._optimize_memory_for_background()
            else:
                event.ignore()
        else:
            event.accept()
            self._force_quit()

    def _force_quit(self):
        """Completely stop all workers, release instance slot, and terminate the application immediately."""
        try:
            if hasattr(self, "hunter_tab") and self.hunter_tab.crawler_thread:
                self.hunter_tab.crawler_thread.stop()
        except Exception:
            pass
        
        try:
            InstanceManager.release_instance()
        except Exception:
            pass

        try:
            if hasattr(self, "tray_icon"):
                self.tray_icon.hide()
        except Exception:
            pass

        try:
            QApplication.instance().quit()
        except Exception:
            pass

        # Force immediate termination of all child processes and process tree
        import os
        import sys
        import subprocess
        try:
            pid = os.getpid()
            if sys.platform == "win32":
                subprocess.Popen(f"taskkill /F /T /PID {pid}", shell=True, creationflags=0x08000000)
        except Exception:
            pass
        os._exit(0)

    def _open_help_dialog(self):
        """Open the Didactic Help & Methodology Dialog with current theme styling."""
        dialog = HelpDialog(self, is_dark_mode=self.is_dark_mode)
        dialog.exec()

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

    def _on_live_video_stream(self, url: str, title: str, video_data: Optional[Dict] = None):
        """Update live video feed in embedded browser and monitor with rich intelligence in real-time."""
        self.browser_view.set_live_video(url, title, video_data)

    def _spawn_new_instance(self):
        """Spawns a new independent instance of the program without needing to manually launch the exe."""
        success = InstanceManager.spawn_new_instance()
        if not success:
            QMessageBox.warning(
                self,
                "Nova Instância",
                "Não foi possível iniciar uma nova instância automaticamente. Tente abrir o executável diretamente."
            )
