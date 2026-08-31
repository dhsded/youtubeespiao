"""
Integrated Chromium Web Browser Component.
Features:
- Real-time live preview of videos being analyzed during mining.
- Zoom controls (🔍+, 🔍-, 100% Reset) with high-DPI scaling to prevent cramped YouTube UI.
- Address bar with quick links to Registro.br, Namecheap, and YouTube.
- Dark and Light theme adaptability.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QProgressBar, QLabel, QToolBar, QFrame
)
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWebEngineWidgets import QWebEngineView

class BrowserView(QWidget):
    def __init__(self, default_url: str = "https://www.youtube.com", parent=None):
        super().__init__(parent)
        self.default_url = default_url
        self.zoom_factor = 0.90  # Default spacious zoom to prevent squished layouts
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Top Live Status Bar (Real-Time HUD)
        self.live_status_bar = QFrame()
        self.live_status_bar.setObjectName("browser_live_bar")
        self.live_status_bar.setStyleSheet("background-color: #0F172A; border-bottom: 1px solid #222F44; padding: 4px 10px;")
        live_layout = QHBoxLayout(self.live_status_bar)
        live_layout.setContentsMargins(8, 2, 8, 2)
        live_layout.setSpacing(8)

        self.lbl_live_badge = QLabel("🌐 NAVEGADOR INTEGRADO")
        self.lbl_live_badge.setStyleSheet("color: #38BDF8; font-weight: 800; font-size: 11px; letter-spacing: 0.5px;")
        live_layout.addWidget(self.lbl_live_badge)

        self.lbl_live_title = QLabel("Pronto para navegação ou acompanhamento ao vivo.")
        self.lbl_live_title.setStyleSheet("color: #94A3B8; font-weight: 600; font-size: 12px;")
        live_layout.addWidget(self.lbl_live_title, 1)

        layout.addWidget(self.live_status_bar)

        # 2. Navigation Bar
        self.toolbar_widget = QWidget()
        self.toolbar_widget.setObjectName("browser_toolbar")
        self.toolbar_widget.setStyleSheet("background-color: #131B2A; border-bottom: 1px solid #222F44; padding: 6px;")
        nav_layout = QHBoxLayout(self.toolbar_widget)
        nav_layout.setContentsMargins(8, 4, 8, 4)
        nav_layout.setSpacing(6)

        # Nav Buttons
        self.btn_back = QPushButton("◀")
        self.btn_back.setFixedWidth(32)
        self.btn_back.setToolTip("Voltar")
        self.btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_back.clicked.connect(self._go_back)

        self.btn_forward = QPushButton("▶")
        self.btn_forward.setFixedWidth(32)
        self.btn_forward.setToolTip("Avançar")
        self.btn_forward.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_forward.clicked.connect(self._go_forward)

        self.btn_reload = QPushButton("🔄")
        self.btn_reload.setFixedWidth(32)
        self.btn_reload.setToolTip("Recarregar Página")
        self.btn_reload.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_reload.clicked.connect(self._reload_page)

        self.btn_home = QPushButton("🏠 YouTube")
        self.btn_home.setToolTip("Ir para a página inicial do YouTube")
        self.btn_home.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_home.clicked.connect(lambda: self.navigate_to("https://www.youtube.com"))

        # URL Input Bar
        self.url_bar = QLineEdit()
        self.url_bar.setObjectName("browser_url_bar")
        self.url_bar.setPlaceholderText("Digite uma URL ou termo de pesquisa...")
        self.url_bar.returnPressed.connect(self._on_url_entered)

        # Go Button
        self.btn_go = QPushButton("Ir")
        self.btn_go.setFixedWidth(40)
        self.btn_go.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_go.clicked.connect(self._on_url_entered)

        # Zoom Controls
        self.btn_zoom_out = QPushButton("🔍 -")
        self.btn_zoom_out.setFixedWidth(36)
        self.btn_zoom_out.setToolTip("Diminuir Zoom (Afastar visão)")
        self.btn_zoom_out.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_zoom_out.clicked.connect(self._zoom_out)

        self.btn_zoom_reset = QPushButton("90%")
        self.btn_zoom_reset.setFixedWidth(50)
        self.btn_zoom_reset.setToolTip("Restaurar Zoom Padrão (100%)")
        self.btn_zoom_reset.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_zoom_reset.clicked.connect(self._zoom_reset)

        self.btn_zoom_in = QPushButton("🔍 +")
        self.btn_zoom_in.setFixedWidth(36)
        self.btn_zoom_in.setToolTip("Aumentar Zoom (Aproximar)")
        self.btn_zoom_in.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_zoom_in.clicked.connect(self._zoom_in)

        # Open in External Desktop Browser (Chrome/Edge/Firefox)
        self.btn_open_ext = QPushButton("🚀 Abrir no Chrome/Edge")
        self.btn_open_ext.setObjectName("btn_open_ext_browser")
        self.btn_open_ext.setToolTip("Abrir a página atual no seu navegador padrão externo (Chrome, Edge, Firefox, Brave)")
        self.btn_open_ext.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_open_ext.clicked.connect(self._open_in_external_browser)
        nav_layout.addWidget(self.btn_open_ext)

        # Quick Links
        self.btn_reg_br = QPushButton("🇧🇷 Registro.br")
        self.btn_reg_br.setToolTip("Abrir Registro.br")
        self.btn_reg_br.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_reg_br.clicked.connect(lambda: self.navigate_to("https://registro.br"))

        self.btn_namecheap = QPushButton("🌐 Namecheap")
        self.btn_namecheap.setToolTip("Abrir Namecheap")
        self.btn_namecheap.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_namecheap.clicked.connect(lambda: self.navigate_to("https://www.namecheap.com"))

        nav_layout.addWidget(self.btn_back)
        nav_layout.addWidget(self.btn_forward)
        nav_layout.addWidget(self.btn_reload)
        nav_layout.addWidget(self.btn_home)
        nav_layout.addWidget(self.url_bar, 1)
        nav_layout.addWidget(self.btn_go)
        nav_layout.addWidget(self.btn_zoom_out)
        nav_layout.addWidget(self.btn_zoom_reset)
        nav_layout.addWidget(self.btn_zoom_in)
        nav_layout.addWidget(self.btn_reg_br)
        nav_layout.addWidget(self.btn_namecheap)

        layout.addWidget(self.toolbar_widget)

        # 3. Loading Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: transparent;
            }
            QProgressBar::chunk {
                background-color: #2563EB;
            }
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # 4. WebEngine View (Chromium)
        self.web_view = QWebEngineView()
        self.web_view.setZoomFactor(self.zoom_factor)
        self.web_view.urlChanged.connect(self._on_web_url_changed)
        self.web_view.loadStarted.connect(self._on_load_started)
        self.web_view.loadProgress.connect(self._on_load_progress)
        self.web_view.loadFinished.connect(self._on_load_finished)
        layout.addWidget(self.web_view, 1)

        # Load default
        self.navigate_to(self.default_url)

    def _zoom_in(self):
        self.zoom_factor = min(2.0, round(self.zoom_factor + 0.1, 2))
        self.web_view.setZoomFactor(self.zoom_factor)
        self.btn_zoom_reset.setText(f"{int(self.zoom_factor * 100)}%")

    def _zoom_out(self):
        self.zoom_factor = max(0.5, round(self.zoom_factor - 0.1, 2))
        self.web_view.setZoomFactor(self.zoom_factor)
        self.btn_zoom_reset.setText(f"{int(self.zoom_factor * 100)}%")

    def _zoom_reset(self):
        self.zoom_factor = 1.0 if self.zoom_factor != 1.0 else 0.90
        self.web_view.setZoomFactor(self.zoom_factor)
        self.btn_zoom_reset.setText(f"{int(self.zoom_factor * 100)}%")

    def set_live_video(self, url: str, title: str):
        """Update live status and load current analyzed video in real-time."""
        self.lbl_live_badge.setText("🔴 MINERANDO AO VIVO")
        self.lbl_live_badge.setStyleSheet("color: #EF4444; font-weight: 800; font-size: 11px;")
        self.lbl_live_title.setText(f"Analisando: {title}")
        self.navigate_to(url)

    def navigate_to(self, url: str):
        """Navigate to specified URL, automatically prepending protocol if missing."""
        clean_url = url.strip()
        if not clean_url:
            return

        if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
            if "." in clean_url and " " not in clean_url:
                clean_url = "https://" + clean_url
            else:
                clean_url = f"https://www.google.com/search?q={clean_url}"

        self.url_bar.setText(clean_url)
        self.web_view.load(QUrl(clean_url))

    def _on_url_entered(self):
        self.navigate_to(self.url_bar.text())

    def _go_back(self):
        self.web_view.back()

    def _go_forward(self):
        self.web_view.forward()

    def _reload_page(self):
        self.web_view.reload()

    def _open_in_external_browser(self):
        from PyQt6.QtGui import QDesktopServices
        clean_url = self.url_bar.text().strip()
        if clean_url:
            if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
                clean_url = "https://" + clean_url
            QDesktopServices.openUrl(QUrl(clean_url))

    def _on_web_url_changed(self, qurl: QUrl):
        self.url_bar.setText(qurl.toString())

    def _on_load_started(self):
        self.progress_bar.setValue(0)
        self.progress_bar.show()

    def _on_load_progress(self, progress: int):
        self.progress_bar.setValue(progress)

    def _on_load_finished(self, success: bool):
        self.progress_bar.hide()
        self.web_view.setZoomFactor(self.zoom_factor)
