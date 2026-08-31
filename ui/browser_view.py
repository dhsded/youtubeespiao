"""
Integrated Chromium Web Browser Component.
Features:
- Stable Live Player Feed (Modo Player Limpo / Cinema Estável) with zero DOM jumping, no sidebar shifting, and smooth transitions.
- Dual View Modes: '🎬 Player Estável' (clean focused 16:9 player) vs '🌐 Página Completa' (full YouTube desktop page).
- '🔴 Seguir Varredura ao Vivo' checkbox toggle to lock or follow live video stream.
- High-DPI Zoom Controls (🔍+, 🔍-, Reset).
- One-click launch in External Desktop Browser (Chrome/Edge/Firefox).
- Full Dark/Light theme adaptability.
"""

import re
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QProgressBar, QLabel, QFrame, QCheckBox
)
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWebEngineWidgets import QWebEngineView

class BrowserView(QWidget):
    def __init__(self, default_url: str = "https://www.youtube.com", parent=None):
        super().__init__(parent)
        self.default_url = default_url
        self.zoom_factor = 0.90
        self.clean_player_mode = True
        self.follow_live_stream = True
        self.current_video_id: Optional[str] = None
        self.current_raw_url: str = default_url

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
        live_layout.setContentsMargins(8, 3, 8, 3)
        live_layout.setSpacing(10)

        self.lbl_live_badge = QLabel("🌐 NAVEGADOR INTEGRADO")
        self.lbl_live_badge.setStyleSheet("color: #38BDF8; font-weight: 800; font-size: 11px; letter-spacing: 0.5px;")
        live_layout.addWidget(self.lbl_live_badge)

        self.lbl_live_title = QLabel("Pronto para navegação ou acompanhamento ao vivo.")
        self.lbl_live_title.setStyleSheet("color: #94A3B8; font-weight: 600; font-size: 12px;")
        live_layout.addWidget(self.lbl_live_title, 1)

        # Follow Live Stream Checkbox
        self.chk_follow_live = QCheckBox("🔴 Acompanhar Varredura em Tempo Real")
        self.chk_follow_live.setChecked(True)
        self.chk_follow_live.setStyleSheet("color: #38BDF8; font-weight: 700; font-size: 11px;")
        self.chk_follow_live.toggled.connect(self._on_follow_live_toggled)
        live_layout.addWidget(self.chk_follow_live)

        # Toggle Mode Button (Clean Player vs Full Page)
        self.btn_mode_toggle = QPushButton("🎬 Modo: Player Estável")
        self.btn_mode_toggle.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #38BDF8;
                border: 1px solid #334155;
                font-weight: 700;
                font-size: 11px;
                padding: 3px 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0284C7;
                color: #FFFFFF;
            }
        """)
        self.btn_mode_toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_mode_toggle.setToolTip("Alternar entre Player Estável (sem elementos pulando) e Página Completa do YouTube")
        self.btn_mode_toggle.clicked.connect(self._toggle_player_mode)
        live_layout.addWidget(self.btn_mode_toggle)

        layout.addWidget(self.live_status_bar)

        # 2. Navigation Bar
        self.toolbar_widget = QWidget()
        self.toolbar_widget.setObjectName("browser_toolbar")
        self.toolbar_widget.setStyleSheet("background-color: #131B2A; border-bottom: 1px solid #222F44; padding: 5px 8px;")
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

        nav_layout.addWidget(self.btn_back)
        nav_layout.addWidget(self.btn_forward)
        nav_layout.addWidget(self.btn_reload)
        nav_layout.addWidget(self.btn_home)

        # URL Input Bar
        self.url_bar = QLineEdit()
        self.url_bar.setObjectName("browser_url_bar")
        self.url_bar.setPlaceholderText("Digite uma URL ou termo de pesquisa...")
        self.url_bar.returnPressed.connect(self._on_url_entered)
        nav_layout.addWidget(self.url_bar, 1)

        # Go Button
        self.btn_go = QPushButton("Ir")
        self.btn_go.setFixedWidth(38)
        self.btn_go.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_go.clicked.connect(self._on_url_entered)
        nav_layout.addWidget(self.btn_go)

        # Zoom Controls
        self.btn_zoom_out = QPushButton("🔍 -")
        self.btn_zoom_out.setFixedWidth(36)
        self.btn_zoom_out.setToolTip("Diminuir Zoom (Afastar visão)")
        self.btn_zoom_out.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_zoom_out.clicked.connect(self._zoom_out)

        self.btn_zoom_reset = QPushButton("90%")
        self.btn_zoom_reset.setFixedWidth(50)
        self.btn_zoom_reset.setToolTip("Restaurar Zoom Padrão (90% / 100%)")
        self.btn_zoom_reset.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_zoom_reset.clicked.connect(self._zoom_reset)

        self.btn_zoom_in = QPushButton("🔍 +")
        self.btn_zoom_in.setFixedWidth(36)
        self.btn_zoom_in.setToolTip("Aumentar Zoom (Aproximar)")
        self.btn_zoom_in.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_zoom_in.clicked.connect(self._zoom_in)

        nav_layout.addWidget(self.btn_zoom_out)
        nav_layout.addWidget(self.btn_zoom_reset)
        nav_layout.addWidget(self.btn_zoom_in)

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

        # Load initial page
        self.navigate_to(self.default_url)

    @staticmethod
    def extract_youtube_video_id(url: str) -> Optional[str]:
        """Extract 11-char YouTube video ID from various URL formats."""
        if not url:
            return None
        if "youtu.be/" in url:
            match = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
            return match.group(1) if match else None
        elif "youtube.com/watch" in url:
            match = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url)
            return match.group(1) if match else None
        elif "youtube.com/embed/" in url:
            match = re.search(r"youtube\.com/embed/([a-zA-Z0-9_-]{11})", url)
            return match.group(1) if match else None
        return None

    def _render_clean_player_html(self, video_id: str, title: str) -> str:
        """
        Renders a fixed-aspect 16:9 theater player without ads, sidebar clickbait,
        or jumpy comments for zero visual flicker during mining.
        """
        embed_src = f"https://www.youtube-nocookie.com/embed/{video_id}?autoplay=1&mute=1&rel=0&modestbranding=1&controls=1"
        safe_title = title.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    background-color: #0B0F17;
                    color: #F8FAFC;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    overflow: hidden;
                    padding: 18px;
                }}
                .player-card {{
                    width: 100%;
                    max-width: 1040px;
                    display: flex;
                    flex-direction: column;
                    background-color: #131B2A;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 16px 36px rgba(0, 0, 0, 0.6);
                    border: 1px solid #222F44;
                }}
                .video-box {{
                    position: relative;
                    width: 100%;
                    padding-bottom: 56.25%; /* 16:9 HD */
                    background-color: #000000;
                }}
                .video-box iframe {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    border: 0;
                }}
                .info-bar {{
                    padding: 12px 18px;
                    background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 12px;
                }}
                .title-txt {{
                    font-size: 14px;
                    font-weight: 700;
                    color: #38BDF8;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    flex: 1;
                }}
                .live-pill {{
                    background-color: #DC2626;
                    color: #FFFFFF;
                    font-size: 11px;
                    font-weight: 800;
                    padding: 4px 10px;
                    border-radius: 12px;
                    letter-spacing: 0.5px;
                    white-space: nowrap;
                    box-shadow: 0 0 10px rgba(220, 38, 38, 0.5);
                }}
            </style>
        </head>
        <body>
            <div class="player-card">
                <div class="video-box">
                    <iframe src="{embed_src}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
                </div>
                <div class="info-bar">
                    <div class="title-txt">🎬 {safe_title}</div>
                    <div class="live-pill">🔴 MINERANDO AO VIVO</div>
                </div>
            </div>
        </body>
        </html>
        """

    def _on_follow_live_toggled(self, checked: bool):
        self.follow_live_stream = checked

    def _toggle_player_mode(self):
        self.clean_player_mode = not self.clean_player_mode
        if self.clean_player_mode:
            self.btn_mode_toggle.setText("🎬 Modo: Player Estável")
            if self.current_video_id:
                html = self._render_clean_player_html(self.current_video_id, self.lbl_live_title.text().replace("Analisando: ", ""))
                self.web_view.setHtml(html)
        else:
            self.btn_mode_toggle.setText("🌐 Modo: Página Completa")
            if self.current_raw_url:
                self.web_view.load(QUrl(self.current_raw_url))

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
        if not self.follow_live_stream:
            return

        self.lbl_live_badge.setText("🔴 MINERANDO AO VIVO")
        self.lbl_live_badge.setStyleSheet("color: #EF4444; font-weight: 800; font-size: 11px;")
        self.lbl_live_title.setText(f"Analisando: {title}")
        self.current_raw_url = url
        self.url_bar.setText(url)

        vid_id = self.extract_youtube_video_id(url)
        self.current_video_id = vid_id

        if vid_id and self.clean_player_mode:
            # Render stable zero-flicker 16:9 theater player
            html = self._render_clean_player_html(vid_id, title)
            self.web_view.setHtml(html, QUrl("https://www.youtube.com"))
        else:
            # Full desktop page
            self.navigate_to(url)

    def navigate_to(self, url: str):
        """Navigate to specified URL, automatically prepending protocol if missing."""
        clean_url = url.strip()
        if not clean_url:
            return

        self.current_raw_url = clean_url
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
        if self.clean_player_mode and self.current_video_id:
            html = self._render_clean_player_html(self.current_video_id, self.lbl_live_title.text().replace("Analisando: ", ""))
            self.web_view.setHtml(html)
        else:
            self.web_view.reload()

    def _open_in_external_browser(self):
        from PyQt6.QtGui import QDesktopServices
        clean_url = self.current_raw_url.strip() if self.current_raw_url else self.url_bar.text().strip()
        if clean_url:
            if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
                clean_url = "https://" + clean_url
            QDesktopServices.openUrl(QUrl(clean_url))

    def _on_web_url_changed(self, qurl: QUrl):
        if not self.clean_player_mode or not self.current_video_id:
            self.url_bar.setText(qurl.toString())

    def _on_load_started(self):
        self.progress_bar.setValue(10)
        self.progress_bar.show()

    def _on_load_progress(self, progress: int):
        self.progress_bar.setValue(progress)

    def _on_load_finished(self, ok: bool):
        self.progress_bar.hide()
