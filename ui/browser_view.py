"""
Integrated Chromium Web Browser & Anti-Flicker Live Mining Monitor.
Features:
- Anti-Flicker Live Mining Monitor with Rich Video Intelligence (Channel, Upload Date, 90-Day Views, VPH, Daily Pace, and Extracted Domains).
- Multi-Instance Support: Isolated per-process Chromium storage profiles allowing infinite simultaneous windows.
- Dual View Modes: '📺 Monitor Anti-Flicker HD' (live stream feed without browser reload) vs '🌐 Navegador Web Livre' (full Chromium engine).
- High-DPI Zoom Controls (🔍+, 🔍-, Reset).
- One-click launch in External Desktop Browser (Chrome/Edge/Firefox).
- Full Dark/Light theme adaptability.
"""

import os
import re
import tempfile
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit,
    QPushButton, QProgressBar, QLabel, QFrame, QCheckBox,
    QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QFont, QPixmap
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from ui.video_table_model import AsyncThumbnailLabel

class LiveMonitorCard(QWidget):
    """Zero-flicker native HUD card displaying real-time video mining stream with rich intelligence."""
    play_in_browser_requested = pyqtSignal(str)
    open_external_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_url = "https://www.youtube.com"
        self.current_title = "Aguardando início da mineração..."
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Center Card Container
        self.card = QFrame()
        self.card.setObjectName("live_monitor_card")
        self.card.setStyleSheet("""
            QFrame#live_monitor_card {
                background-color: #131B2A;
                border: 1px solid #222F44;
                border-radius: 12px;
                padding: 14px;
            }
        """)
        self.card.setFixedWidth(720)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(10)

        # 1. Top Badge & HUD Header
        header_layout = QHBoxLayout()
        self.badge_live = QLabel("🔴 MINERANDO AO VIVO")
        self.badge_live.setStyleSheet("""
            background-color: #DC2626;
            color: #FFFFFF;
            font-size: 11px;
            font-weight: 800;
            padding: 4px 10px;
            border-radius: 12px;
            letter-spacing: 0.5px;
        """)
        header_layout.addWidget(self.badge_live)

        self.lbl_status = QLabel("Acompanhando fluxo de extração e análise de tráfego...")
        self.lbl_status.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 600;")
        header_layout.addWidget(self.lbl_status, 1)

        card_layout.addLayout(header_layout)

        # 2. Large HD Thumbnail Preview (480x270 16:9)
        thumb_container = QHBoxLayout()
        thumb_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label = AsyncThumbnailLabel("", width=440, height=247)
        self.thumb_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.thumb_label.mousePressEvent = lambda e: self.play_in_browser_requested.emit(self.current_url)
        thumb_container.addWidget(self.thumb_label)
        card_layout.addLayout(thumb_container)

        # 3. Video Title
        self.lbl_title = QLabel(self.current_title)
        self.lbl_title.setObjectName("live_monitor_title")
        self.lbl_title.setWordWrap(True)
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color: #38BDF8; margin-top: 2px;")
        card_layout.addWidget(self.lbl_title)

        # 4. Rich Video Details Matrix
        self.stats_frame = QFrame()
        self.stats_frame.setStyleSheet("""
            QFrame {
                background-color: #0F172A;
                border: 1px solid #1E293B;
                border-radius: 8px;
                padding: 6px;
            }
        """)
        stats_grid = QGridLayout(self.stats_frame)
        stats_grid.setContentsMargins(10, 8, 10, 8)
        stats_grid.setHorizontalSpacing(14)
        stats_grid.setVerticalSpacing(6)

        # Col 0: Channel & Upload Date
        self.lbl_channel = QLabel("📺 Canal: --")
        self.lbl_channel.setStyleSheet("color: #E2E8F0; font-size: 11px; font-weight: 700;")
        stats_grid.addWidget(self.lbl_channel, 0, 0)

        self.lbl_pubdate = QLabel("📅 Envio: --")
        self.lbl_pubdate.setStyleSheet("color: #94A3B8; font-size: 11px;")
        stats_grid.addWidget(self.lbl_pubdate, 1, 0)

        # Col 1: Total Views & 90-Day Views
        self.lbl_views_tot = QLabel("👁️ Total Views: --")
        self.lbl_views_tot.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 700;")
        stats_grid.addWidget(self.lbl_views_tot, 0, 1)

        self.lbl_views_90d = QLabel("⚡ Views 90d: --")
        self.lbl_views_90d.setStyleSheet("color: #8B5CF6; font-size: 11px; font-weight: 700;")
        stats_grid.addWidget(self.lbl_views_90d, 1, 1)

        # Col 2: VPH Velocity & Daily Traffic
        self.lbl_vph = QLabel("⏱️ VPH: --")
        self.lbl_vph.setStyleSheet("color: #F59E0B; font-size: 11px; font-weight: 800;")
        stats_grid.addWidget(self.lbl_vph, 0, 2)

        self.lbl_daily = QLabel("🔥 Tráfego: --")
        self.lbl_daily.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 800;")
        stats_grid.addWidget(self.lbl_daily, 1, 2)

        card_layout.addWidget(self.stats_frame)

        # 5. Discovered Domains Badge Bar
        self.lbl_domains_badge = QLabel("💎 Oportunidades: Nenhuma nesta varredura")
        self.lbl_domains_badge.setStyleSheet("color: #CBD5E1; font-size: 11px; font-weight: 600; text-align: center;")
        self.lbl_domains_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.lbl_domains_badge)

        # 6. Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_play_internal = QPushButton("▶ Assistir no Navegador Integrado")
        self.btn_play_internal.setObjectName("btn_monitor_play")
        self.btn_play_internal.setStyleSheet("""
            QPushButton#btn_monitor_play {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2563EB, stop:1 #1D4ED8);
                color: #FFFFFF;
                font-weight: 800;
                font-size: 12px;
                padding: 7px 16px;
                border-radius: 6px;
            }
            QPushButton#btn_monitor_play:hover {
                background: #3B82F6;
            }
        """)
        self.btn_play_internal.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_play_internal.clicked.connect(lambda: self.play_in_browser_requested.emit(self.current_url))
        btn_layout.addWidget(self.btn_play_internal)

        self.btn_open_external = QPushButton("🚀 Abrir no Chrome/Edge ↗")
        self.btn_open_external.setObjectName("btn_monitor_ext")
        self.btn_open_external.setStyleSheet("""
            QPushButton#btn_monitor_ext {
                background-color: #1E293B;
                color: #38BDF8;
                border: 1px solid #334155;
                font-weight: 700;
                font-size: 12px;
                padding: 7px 16px;
                border-radius: 6px;
            }
            QPushButton#btn_monitor_ext:hover {
                background-color: #0284C7;
                color: #FFFFFF;
            }
        """)
        self.btn_open_external.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_open_external.clicked.connect(lambda: self.open_external_requested.emit(self.current_url))
        btn_layout.addWidget(self.btn_open_external)

        card_layout.addLayout(btn_layout)
        layout.addWidget(self.card)

    def update_video(self, url: str, title: str, video_data: Optional[Dict[str, Any]] = None):
        """Update live video feed with rich stats and smooth thumbnail transition."""
        self.current_url = url
        self.current_title = title
        self.lbl_title.setText(title)

        # Extract YouTube ID for HD thumbnail
        vid_id = BrowserView.extract_youtube_video_id(url)
        if vid_id:
            thumb_url = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
        else:
            thumb_url = ""

        # Update metadata if available
        if video_data:
            m = video_data.get("metrics", {})
            channel = video_data.get("channel_name", "Canal do YouTube")
            pub_date = m.get("publish_date", "Recente")
            v_tot = m.get("view_count_formatted", "0")
            v_90d = m.get("views_90d_formatted", "0")
            vph_val = m.get("hourly_views_formatted", "0 VPH")
            daily_val = m.get("daily_views_formatted", "0/dia")

            self.lbl_channel.setText(f"📺 Canal: {channel[:25]}")
            self.lbl_pubdate.setText(f"📅 Envio: {pub_date}")
            self.lbl_views_tot.setText(f"👁️ Views: {v_tot}")
            self.lbl_views_90d.setText(f"⚡ 90 Dias: {v_90d}")
            self.lbl_vph.setText(f"⏱️ {vph_val}")
            self.lbl_daily.setText(f"🔥 {daily_val}")

            doms = video_data.get("domains", [])
            avail_cnt = sum(1 for d in doms if d.get("status") == "Disponível")
            if avail_cnt > 0:
                self.lbl_domains_badge.setText(f"💎 Oportunidades: 🟢 {avail_cnt} DISPONÍVEIS p/ Registro | Total: {len(doms)}")
                self.lbl_domains_badge.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 800;")
            elif len(doms) > 0:
                self.lbl_domains_badge.setText(f"💎 Oportunidades: {len(doms)} links analisados (Registrados/Inativos)")
                self.lbl_domains_badge.setStyleSheet("color: #CBD5E1; font-size: 11px; font-weight: 600;")
            else:
                self.lbl_domains_badge.setText("💎 Oportunidades: Nenhum link expirado neste vídeo")
                self.lbl_domains_badge.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 600;")
        else:
            self.lbl_channel.setText("📺 Canal: YouTube")
            self.lbl_pubdate.setText("📅 Envio: Recente")
            self.lbl_views_tot.setText("👁️ Views: Analisando...")
            self.lbl_views_90d.setText("⚡ 90 Dias: --")
            self.lbl_vph.setText("⏱️ VPH: --")
            self.lbl_daily.setText("🔥 Tráfego: --")
            self.lbl_domains_badge.setText("💎 Oportunidades: Analisando links na descrição...")

        # Re-fetch thumbnail smoothly without DOM teardowns
        if thumb_url:
            self.thumb_label.load_thumbnail(thumb_url)
        else:
            self.thumb_label.setText("Sem Foto")


class BrowserView(QWidget):
    def __init__(self, default_url: str = "https://www.youtube.com", parent=None):
        super().__init__(parent)
        self.default_url = default_url
        self.zoom_factor = 0.90
        self.follow_live_stream = True
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

        self.lbl_live_badge = QLabel("🌐 NAVEGADOR & MONITOR")
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

        # View Mode Toggle Button (Monitor Anti-Flicker vs Full Browser)
        self.btn_view_mode = QPushButton("🌐 Abrir Navegador Web Completo")
        self.btn_view_mode.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #38BDF8;
                border: 1px solid #334155;
                font-weight: 700;
                font-size: 11px;
                padding: 4px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0284C7;
                color: #FFFFFF;
            }
        """)
        self.btn_view_mode.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_view_mode.setToolTip("Alternar entre o Monitor de Mineração Anti-Flicker e o Navegador Web Completo")
        self.btn_view_mode.clicked.connect(self._toggle_view_mode)
        live_layout.addWidget(self.btn_view_mode)

        layout.addWidget(self.live_status_bar)

        # 2. Navigation Bar (Used when in Browser Mode)
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

        # Open in External Desktop Browser
        self.btn_open_ext = QPushButton("🚀 Abrir no Chrome/Edge")
        self.btn_open_ext.setObjectName("btn_open_ext_browser")
        self.btn_open_ext.setToolTip("Abrir no seu navegador padrão externo")
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

        # 3. Stacked View Container (Mode 0: Anti-Flicker Monitor Card | Mode 1: Full Chromium Engine)
        self.stack = QStackedWidget()

        # View 0: Native Anti-Flicker Live Monitor
        self.live_monitor = LiveMonitorCard()
        self.live_monitor.play_in_browser_requested.connect(self._on_play_in_browser_clicked)
        self.live_monitor.open_external_requested.connect(self._open_in_external_browser)
        self.stack.addWidget(self.live_monitor)

        # View 1: Full Chromium Web View with Isolated Multi-Instance Profile
        self.web_view_container = QWidget()
        web_layout = QVBoxLayout(self.web_view_container)
        web_layout.setContentsMargins(0, 0, 0, 0)
        web_layout.setSpacing(0)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { border: none; background: transparent; } QProgressBar::chunk { background: #2563EB; }")
        self.progress_bar.hide()
        web_layout.addWidget(self.progress_bar)

        # Multi-Instance Isolated Chromium Profile
        profile_storage = os.path.join(tempfile.gettempdir(), f"yt_espiao_profile_{os.getpid()}")
        self.instance_profile = QWebEngineProfile(f"yt_profile_{os.getpid()}", self)
        self.instance_profile.setPersistentStoragePath(profile_storage)

        self.web_view = QWebEngineView()
        self.instance_page = QWebEnginePage(self.instance_profile, self.web_view)
        self.web_view.setPage(self.instance_page)
        self.web_view.setZoomFactor(self.zoom_factor)
        self.web_view.urlChanged.connect(self._on_web_url_changed)
        self.web_view.loadStarted.connect(self._on_load_started)
        self.web_view.loadProgress.connect(self._on_load_progress)
        self.web_view.loadFinished.connect(self._on_load_finished)
        web_layout.addWidget(self.web_view, 1)

        self.stack.addWidget(self.web_view_container)
        layout.addWidget(self.stack, 1)

        # Start on Anti-Flicker Monitor by default
        self.stack.setCurrentIndex(0)
        self.toolbar_widget.hide()

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

    def _toggle_view_mode(self):
        if self.stack.currentIndex() == 0:
            # Switch to Browser
            self.stack.setCurrentIndex(1)
            self.toolbar_widget.show()
            self.btn_view_mode.setText("📺 Voltar ao Monitor Anti-Flicker")
            if self.current_raw_url:
                self.navigate_to(self.current_raw_url)
        else:
            # Switch to Monitor
            self.stack.setCurrentIndex(0)
            self.toolbar_widget.hide()
            self.btn_view_mode.setText("🌐 Abrir Navegador Web Completo")

    def _on_play_in_browser_clicked(self, url: str):
        """Load video smoothly in integrated Chromium view."""
        self.stack.setCurrentIndex(1)
        self.toolbar_widget.show()
        self.btn_view_mode.setText("📺 Voltar ao Monitor Anti-Flicker")
        self.navigate_to(url)

    def _on_follow_live_toggled(self, checked: bool):
        self.follow_live_stream = checked

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

    def set_live_video(self, url: str, title: str, video_data: Optional[Dict[str, Any]] = None):
        """
        Update live status and stream monitor with rich video intelligence and ZERO visual flickering.
        """
        if not self.follow_live_stream:
            return

        self.lbl_live_badge.setText("🔴 MINERANDO AO VIVO")
        self.lbl_live_badge.setStyleSheet("color: #EF4444; font-weight: 800; font-size: 11px;")
        self.lbl_live_title.setText(f"Analisando: {title}")
        self.current_raw_url = url
        self.url_bar.setText(url)

        # Update native Anti-Flicker Monitor Card smoothly with rich stats
        self.live_monitor.update_video(url, title, video_data)

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
        self.web_view.reload()

    def _open_in_external_browser(self, url: Optional[str] = None):
        from PyQt6.QtGui import QDesktopServices
        target_url = url or self.current_raw_url or self.url_bar.text()
        clean_url = target_url.strip() if target_url else ""
        if clean_url:
            if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
                clean_url = "https://" + clean_url
            QDesktopServices.openUrl(QUrl(clean_url))

    def _on_web_url_changed(self, qurl: QUrl):
        self.url_bar.setText(qurl.toString())

    def _on_load_started(self):
        self.progress_bar.setValue(10)
        self.progress_bar.show()

    def _on_load_progress(self, progress: int):
        self.progress_bar.setValue(progress)

    def _on_load_finished(self, ok: bool):
        self.progress_bar.hide()
