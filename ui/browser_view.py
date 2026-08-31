"""
Integrated Chromium Web Browser Component.
Provides a standard web browser view with navigation bar, address bar,
and one-click integration with YouTube and domain registrars.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QProgressBar, QLabel, QToolBar
)
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView

class BrowserView(QWidget):
    def __init__(self, default_url: str = "https://www.youtube.com", parent=None):
        super().__init__(parent)
        self.default_url = default_url
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Navigation Bar
        self.toolbar_widget = QWidget()
        self.toolbar_widget.setStyleSheet("background-color: #1E293B; border-bottom: 1px solid #334155; padding: 6px;")
        nav_layout = QHBoxLayout(self.toolbar_widget)
        nav_layout.setContentsMargins(8, 4, 8, 4)
        nav_layout.setSpacing(8)

        # Nav Buttons
        self.btn_back = QPushButton("◀")
        self.btn_back.setFixedWidth(34)
        self.btn_back.setToolTip("Voltar")
        self.btn_back.clicked.connect(self._go_back)

        self.btn_forward = QPushButton("▶")
        self.btn_forward.setFixedWidth(34)
        self.btn_forward.setToolTip("Avançar")
        self.btn_forward.clicked.connect(self._go_forward)

        self.btn_reload = QPushButton("🔄")
        self.btn_reload.setFixedWidth(34)
        self.btn_reload.setToolTip("Recarregar Página")
        self.btn_reload.clicked.connect(self._reload_page)

        self.btn_home = QPushButton("🏠 YouTube")
        self.btn_home.setToolTip("Ir para o YouTube")
        self.btn_home.clicked.connect(lambda: self.navigate_to("https://www.youtube.com"))

        # URL Input Bar
        self.url_bar = QLineEdit()
        self.url_bar.setObjectName("browser_url_bar")
        self.url_bar.setPlaceholderText("Digite uma URL ou termo de pesquisa...")
        self.url_bar.returnPressed.connect(self._on_url_entered)

        # Go Button
        self.btn_go = QPushButton("Ir")
        self.btn_go.setFixedWidth(45)
        self.btn_go.clicked.connect(self._on_url_entered)

        # Quick Links
        self.btn_reg_br = QPushButton("🇧🇷 Registro.br")
        self.btn_reg_br.setToolTip("Abrir Registro.br")
        self.btn_reg_br.clicked.connect(lambda: self.navigate_to("https://registro.br"))

        self.btn_namecheap = QPushButton("🌐 Namecheap")
        self.btn_namecheap.setToolTip("Abrir Namecheap")
        self.btn_namecheap.clicked.connect(lambda: self.navigate_to("https://www.namecheap.com"))

        nav_layout.addWidget(self.btn_back)
        nav_layout.addWidget(self.btn_forward)
        nav_layout.addWidget(self.btn_reload)
        nav_layout.addWidget(self.btn_home)
        nav_layout.addWidget(self.url_bar, 1)
        nav_layout.addWidget(self.btn_go)
        nav_layout.addWidget(self.btn_reg_br)
        nav_layout.addWidget(self.btn_namecheap)

        layout.addWidget(self.toolbar_widget)

        # 2. Loading Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: transparent;
            }
            QProgressBar::chunk {
                background-color: #6366F1;
            }
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # 3. WebEngine View (Chromium)
        self.web_view = QWebEngineView()
        self.web_view.urlChanged.connect(self._on_url_changed)
        self.web_view.loadProgress.connect(self._on_load_progress)
        self.web_view.loadStarted.connect(self._on_load_started)
        self.web_view.loadFinished.connect(self._on_load_finished)

        layout.addWidget(self.web_view, 1)

        # Initial Load
        self.navigate_to(self.default_url)

    def navigate_to(self, url: str):
        """Navigate to the specified URL."""
        if not url:
            return
        url_str = url.strip()
        if not url_str.startswith("http://") and not url_str.startswith("https://"):
            if "." in url_str and not " " in url_str:
                url_str = "https://" + url_str
            else:
                # Search Google / YouTube
                url_str = f"https://www.google.com/search?q={url_str}"

        self.url_bar.setText(url_str)
        self.web_view.load(QUrl(url_str))

    def _on_url_entered(self):
        url = self.url_bar.text()
        self.navigate_to(url)

    def _on_url_changed(self, qurl: QUrl):
        self.url_bar.setText(qurl.toString())

    def _on_load_started(self):
        self.progress_bar.setValue(0)
        self.progress_bar.show()

    def _on_load_progress(self, progress: int):
        self.progress_bar.setValue(progress)

    def _on_load_finished(self, success: bool):
        self.progress_bar.hide()

    def _go_back(self):
        if self.web_view.history().canGoBack():
            self.web_view.back()

    def _go_forward(self):
        if self.web_view.history().canGoForward():
            self.web_view.forward()

    def _reload_page(self):
        self.web_view.reload()
