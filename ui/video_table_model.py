"""
Video Table and Domain Table UI Components with High-Precision Traffic & 90-Day Metrics.
Features:
- 90-Day Recent Traffic ('Views nos Últimos 90 Dias') to reveal active evergreen velocity.
- VPH (Views Per Hour) with calibrated decay modeling.
- Show/Hide Columns Manager (Botão '👁️ Colunas' e menu contextual no cabeçalho para exibir/ocultar qualquer coluna).
- Domain Aggregation & Cumulative Traffic Calculation (Soma do tráfego diário total gerado em múltiplos vídeos).
- 'Qtd de Vídeos Onde Aparece' (contagem precisa de vídeos onde cada domínio foi encontrado).
- Large HD Thumbnails (180x101 px) with async caching.
- Explicit 'Data de Envio' (Video Upload Date) Column across all tables.
- Drag & Drop column reorganization (Movable interactive headers).
- Full Dark/Light theme adaptability with crisp typography.
- Status filters (Disponíveis, Inativos, Instagram, etc.).
- Pagination with customizable page sizes.
- Direct quick links for purchasing domains and opening YouTube videos.
"""

import math
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QComboBox,
    QFrame, QHeaderView, QLineEdit, QCheckBox, QMenu, QDialog,
    QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QPoint
from PyQt6.QtGui import QColor, QFont, QCursor, QPixmap, QImage, QAction
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from core.metrics_calculator import format_number, format_vph
from core.trademark_validator import analyze_trademark_risk

class NumericTableWidgetItem(QTableWidgetItem):
    """Custom TableWidgetItem for accurate numeric/chronological sorting."""
    def __init__(self, text: str, sort_value: float):
        super().__init__(text)
        self.sort_value = sort_value
        self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self.sort_value < other.sort_value
        return super().__lt__(other)


class AsyncThumbnailLabel(QLabel):
    """Asynchronous thumbnail loader with LRU bounded memory cache and custom dimensions."""
    _network_manager = None
    _pixmap_cache = {}  # (URL, width, height) -> QPixmap
    _CACHE_MAX_SIZE = 500  # Evict oldest when exceeding 500 thumbnails to protect RAM

    def __init__(self, url: str = "", parent=None, width: int = 176, height: int = 99, **kwargs):
        if isinstance(url, QWidget):
            parent = url
            url = ""
        super().__init__(parent)
        self.target_width = width
        self.target_height = height
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #0F172A; border-radius: 6px;")
        self.setFixedSize(self.target_width, self.target_height)
        if AsyncThumbnailLabel._network_manager is None:
            AsyncThumbnailLabel._network_manager = QNetworkAccessManager()
        if url:
            self.load_thumbnail(url)

    def load_thumbnail(self, url: str):
        if not url:
            self.setText("Sem Foto")
            return

        cache_key = (url, self.target_width, self.target_height)
        if cache_key in AsyncThumbnailLabel._pixmap_cache:
            self.setPixmap(AsyncThumbnailLabel._pixmap_cache[cache_key])
            return

        self.setText("Carregando...")
        req = QNetworkRequest(QUrl(url))
        reply = AsyncThumbnailLabel._network_manager.get(req)
        reply.finished.connect(lambda: self._on_thumbnail_loaded(reply, url))

    def _on_thumbnail_loaded(self, reply: QNetworkReply, url: str):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            img_data = reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(img_data):
                scaled = pixmap.scaled(
                    self.target_width, self.target_height,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                cache_key = (url, self.target_width, self.target_height)
                if len(AsyncThumbnailLabel._pixmap_cache) >= AsyncThumbnailLabel._CACHE_MAX_SIZE:
                    AsyncThumbnailLabel._pixmap_cache.pop(next(iter(AsyncThumbnailLabel._pixmap_cache)))
                AsyncThumbnailLabel._pixmap_cache[cache_key] = scaled
                self.setPixmap(scaled)
            else:
                self.setText("Erro Img")
        else:
            self.setText("Indisponível")
        reply.deleteLater()


class VideoTableView(QWidget):
    """
    Paginated, high-performance interactive table for discovered YouTube videos.
    """
    open_video_requested = pyqtSignal(str)

    COLUMN_HEADERS = [
        "Miniatura",
        "Título do Vídeo",
        "Canal",
        "Visualizações Totais",
        "Views nos Últimos 90 Dias",
        "⚡ VPH (Views/Hora)",
        "Tráfego Diário Estimado",
        "Views / Mês (Estimado)",
        "Views / Ano (Estimado)",
        "Data de Envio",
        "Domínios Encontrados",
        "Ação"
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.raw_videos_data: List[Dict[str, Any]] = []
        self.filtered_videos_data: List[Dict[str, Any]] = []
        
        self.current_page = 1
        self.page_size = 25
        self.only_available_filter = False
        self.search_filter_text = ""

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 1. Top Filters & Search Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.chk_only_available = QCheckBox("🟢 Apenas com Domínios/IGs Disponíveis")
        self.chk_only_available.setObjectName("chk_available_only")
        self.chk_only_available.setStyleSheet("font-weight: 700; color: #10B981;")
        self.chk_only_available.toggled.connect(self._on_available_filter_toggled)
        toolbar.addWidget(self.chk_only_available)

        toolbar.addStretch()

        # Column Visibility Selector Button
        self.btn_columns = QPushButton("👁️ Colunas")
        self.btn_columns.setObjectName("btn_table_action")
        self.btn_columns.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_columns.setToolTip("Exibir ou ocultar colunas da tabela")
        self.btn_columns.clicked.connect(self._show_column_menu)
        toolbar.addWidget(self.btn_columns)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("🔍 Buscar vídeo, canal ou domínio...")
        self.input_search.setFixedWidth(240)
        self.input_search.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.input_search)

        layout.addLayout(toolbar)

        # 2. Main Video Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)
        
        header = self.table.horizontalHeader()
        header.setSectionsMovable(True)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._on_header_context_menu)

        for i in range(len(self.COLUMN_HEADERS)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

        self.table.verticalHeader().setDefaultSectionSize(112)
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setSectionsMovable(True)

        # Optimized comfortable default widths
        self.table.setColumnWidth(0, 185) # Thumbnail (176x99)
        self.table.setColumnWidth(1, 300) # Title
        self.table.setColumnWidth(2, 160) # Channel
        self.table.setColumnWidth(3, 135) # Views Totais
        self.table.setColumnWidth(4, 140) # Views 90 Dias
        self.table.setColumnWidth(5, 120) # VPH
        self.table.setColumnWidth(6, 135) # Daily Views
        self.table.setColumnWidth(7, 110) # Monthly Views (Optional)
        self.table.setColumnWidth(8, 110) # Yearly Views (Optional)
        self.table.setColumnWidth(9, 110) # Publish Date
        self.table.setColumnWidth(10, 160) # Domains summary
        self.table.setColumnWidth(11, 135) # Actions

        # Hide secondary monthly/yearly projections by default to keep clean initial view
        self.table.setColumnHidden(7, True)
        self.table.setColumnHidden(8, True)

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(True)

        layout.addWidget(self.table)

        # 3. Bottom Pagination Bar
        self.pagination_frame = QFrame()
        self.pagination_frame.setObjectName("pagination_bar")
        p_layout = QHBoxLayout(self.pagination_frame)
        p_layout.setContentsMargins(8, 4, 8, 4)
        p_layout.setSpacing(10)

        self.btn_prev_page = QPushButton("◀ Anterior")
        self.btn_prev_page.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_prev_page.clicked.connect(self._prev_page)
        p_layout.addWidget(self.btn_prev_page)

        self.lbl_page_info = QLabel("Página 1 de 1 (0 vídeos)")
        self.lbl_page_info.setStyleSheet("font-weight: 600;")
        p_layout.addWidget(self.lbl_page_info)

        self.btn_next_page = QPushButton("Próxima ▶")
        self.btn_next_page.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_next_page.clicked.connect(self._next_page)
        p_layout.addWidget(self.btn_next_page)

        p_layout.addStretch()

        p_layout.addWidget(QLabel("Vídeos por página:"))
        self.combo_page_size = QComboBox()
        self.combo_page_size.addItem("10 vídeos", 10)
        self.combo_page_size.addItem("25 vídeos", 25)
        self.combo_page_size.addItem("50 vídeos", 50)
        self.combo_page_size.addItem("100 vídeos", 100)
        self.combo_page_size.setCurrentIndex(1)
        self.combo_page_size.currentIndexChanged.connect(self._on_page_size_changed)
        p_layout.addWidget(self.combo_page_size)

        layout.addWidget(self.pagination_frame)

    def _show_column_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { padding: 6px; font-weight: 600; }")
        
        for i, header_text in enumerate(self.COLUMN_HEADERS):
            action = QAction(header_text, menu)
            action.setCheckable(True)
            action.setChecked(not self.table.isColumnHidden(i))
            action.toggled.connect(lambda checked, col=i: self.table.setColumnHidden(col, not checked))
            menu.addAction(action)

        self.btn_columns.mapToGlobal(QPoint(0, self.btn_columns.height()))
        menu.exec(self.btn_columns.mapToGlobal(QPoint(0, self.btn_columns.height())))

    def _on_header_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { padding: 6px; font-weight: 600; }")
        
        for i, header_text in enumerate(self.COLUMN_HEADERS):
            action = QAction(f"Exibir '{header_text}'", menu)
            action.setCheckable(True)
            action.setChecked(not self.table.isColumnHidden(i))
            action.toggled.connect(lambda checked, col=i: self.table.setColumnHidden(col, not checked))
            menu.addAction(action)

        header = self.table.horizontalHeader()
        menu.exec(header.mapToGlobal(pos))

    def set_videos(self, videos_data: List[Dict[str, Any]]):
        self.raw_videos_data = videos_data
        self.current_page = 1
        self._apply_filter_and_render()

    def _on_available_filter_toggled(self, checked: bool):
        self.only_available_filter = checked
        self.current_page = 1
        self._apply_filter_and_render()

    def _on_search_changed(self, text: str):
        self.search_filter_text = text.strip().lower()
        self.current_page = 1
        self._apply_filter_and_render()

    def _on_page_size_changed(self):
        self.page_size = self.combo_page_size.currentData()
        self.current_page = 1
        self._apply_filter_and_render()

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_current_page()

    def _next_page(self):
        total_pages = max(1, math.ceil(len(self.filtered_videos_data) / self.page_size))
        if self.current_page < total_pages:
            self.current_page += 1
            self._render_current_page()

    def _apply_filter_and_render(self):
        filtered = self.raw_videos_data

        if self.only_available_filter:
            filtered = [
                v for v in filtered
                if any(d.get("status") == "Disponível" for d in v.get("domains", []))
            ]

        if self.search_filter_text:
            filtered = [
                v for v in filtered
                if self.search_filter_text in v.get("title", "").lower()
                or self.search_filter_text in v.get("channel_name", "").lower()
                or any(self.search_filter_text in d.get("root_domain", "").lower()
                       or self.search_filter_text in d.get("display_name", "").lower()
                       or self.search_filter_text in d.get("details", "").lower()
                       for d in v.get("domains", []))
            ]

        self.filtered_videos_data = filtered
        self._render_current_page()

    def _render_current_page(self):
        total_items = len(self.filtered_videos_data)
        total_pages = max(1, math.ceil(total_items / self.page_size))
        
        if self.current_page > total_pages:
            self.current_page = total_pages
        if self.current_page < 1:
            self.current_page = 1

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_items = self.filtered_videos_data[start_idx:end_idx]

        self.lbl_page_info.setText(f"Página {self.current_page} de {total_pages} (Exibindo {len(page_items)} de {total_items} vídeos)")
        self.btn_prev_page.setEnabled(self.current_page > 1)
        self.btn_next_page.setEnabled(self.current_page < total_pages)

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(page_items))

        for row, v in enumerate(page_items):
            m = v.get("metrics", {})
            domains = v.get("domains", [])
            avail_cnt = sum(1 for d in domains if d.get("status") == "Disponível")
            inact_cnt = sum(1 for d in domains if d.get("status") == "Inativo")

            # 0. HD Thumbnail Widget (180x101 px)
            thumb_widget = QWidget()
            thumb_layout = QVBoxLayout(thumb_widget)
            thumb_layout.setContentsMargins(4, 4, 4, 4)
            thumb_lbl = AsyncThumbnailLabel()
            thumb_lbl.setFixedSize(176, 99)
            thumb_lbl.load_thumbnail(v.get("thumbnail", ""))
            thumb_layout.addWidget(thumb_lbl)
            self.table.setCellWidget(row, 0, thumb_widget)

            # 1. Video Title
            title_item = QTableWidgetItem(v.get("title", ""))
            title_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            title_item.setToolTip(f"{v.get('title', '')}\n\nCanal: {v.get('channel_name', '')}")
            self.table.setItem(row, 1, title_item)

            # 2. Channel Name
            channel_item = QTableWidgetItem(v.get("channel_name", ""))
            channel_item.setFont(QFont("Segoe UI", 9))
            self.table.setItem(row, 2, channel_item)

            # 3. Total Lifetime Views
            tot_views = m.get("view_count", 0)
            views_item = NumericTableWidgetItem(m.get("view_count_formatted", str(tot_views)), tot_views)
            views_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            views_item.setForeground(QColor("#0284C7"))
            views_item.setToolTip(f"Total de visualizações acumuladas: {tot_views:,}")
            self.table.setItem(row, 3, views_item)

            # 4. Views in the Last 90 Days
            v_90d = m.get("views_90d", tot_views)
            v90d_formatted = m.get("views_90d_formatted", format_number(v_90d))
            v90d_item = NumericTableWidgetItem(f"⚡ {v90d_formatted}", v_90d)
            v90d_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            v90d_item.setForeground(QColor("#8B5CF6"))
            v90d_item.setToolTip(f"Visualizações estimadas nos últimos 90 dias: {v_90d:,}")
            self.table.setItem(row, 4, v90d_item)

            # 5. VPH (Views Per Hour)
            h_views = m.get("hourly_views", 0)
            vph_item = NumericTableWidgetItem(m.get("hourly_views_formatted", format_vph(h_views)), h_views)
            vph_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            vph_item.setForeground(QColor("#D97706"))
            vph_item.setToolTip(
                f"⚡ Velocidade Recente: {h_views:.2f} views/hora\n"
                f"Vitalidade de Tráfego: {m.get('velocity_badge', '')}\n"
                f"{m.get('vitality_desc', '')}"
            )
            self.table.setItem(row, 5, vph_item)

            # 6. Daily Views (Views/Dia)
            d_views = m.get("daily_views", 0)
            daily_item = NumericTableWidgetItem(m.get("daily_views_formatted", f"🔥 {d_views}/dia"), d_views)
            daily_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            daily_item.setForeground(QColor("#16A34A"))
            self.table.setItem(row, 6, daily_item)

            # 7. Monthly Views (Views/Mês)
            m_views = m.get("monthly_views", 0)
            month_item = NumericTableWidgetItem(m.get("monthly_views_formatted", f"{m_views}/mês"), m_views)
            self.table.setItem(row, 7, month_item)

            # 8. Yearly Views (Views/Ano)
            y_views = m.get("yearly_views", 0)
            year_item = NumericTableWidgetItem(m.get("yearly_views_formatted", f"{y_views}/ano"), y_views)
            self.table.setItem(row, 8, year_item)

            # 9. Explicit Upload Date (Data de Envio)
            pub_date = m.get("publish_date", "Recente")
            date_item = QTableWidgetItem(pub_date)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            date_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.table.setItem(row, 9, date_item)

            # 10. Domains / IGs Badge Summary
            dom_summary = f"🟢 {avail_cnt} | 🟡 {inact_cnt} | Total: {len(domains)}"
            dom_item = NumericTableWidgetItem(dom_summary, avail_cnt * 1000000 + len(domains))
            if avail_cnt > 0:
                dom_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                dom_item.setForeground(QColor("#16A34A"))
            self.table.setItem(row, 10, dom_item)

            # 11. Action Buttons Widget
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_open = QPushButton("▶ Assistir ↗")
            btn_open.setObjectName("btn_table_action")
            btn_open.setToolTip("Abrir vídeo no YouTube no seu navegador padrão")
            btn_open.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            v_url = v.get("url", "")
            btn_open.clicked.connect(lambda _, u=v_url: self.open_video_requested.emit(u))

            action_layout.addWidget(btn_open)
            self.table.setCellWidget(row, 11, action_widget)

        self.table.setSortingEnabled(True)

    def set_search_query(self, text: str):
        """Set search query programmatically and filter the table."""
        self.input_search.setText(text)
        self._on_search_changed(text)


class AssociatedVideosDialog(QDialog):
    """Modal dialog displaying the full list of videos linking to a specific domain."""
    def __init__(self, domain_name: str, associated_videos: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.domain_name = domain_name
        self.associated_videos = associated_videos
        self.setWindowTitle(f"🎯 Vídeos com o Link: {domain_name}")
        self.resize(980, 520)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Info Card
        header_card = QFrame()
        header_card.setObjectName("card")
        header_card.setStyleSheet("background-color: #131B2A; border: 1px solid #222F44; border-radius: 8px; padding: 10px;")
        h_layout = QHBoxLayout(header_card)

        lbl_icon = QLabel("🎬")
        lbl_icon.setStyleSheet("font-size: 24px;")
        h_layout.addWidget(lbl_icon)

        v_info = QVBoxLayout()
        lbl_dom = QLabel(f"Domínio / Link: <span style='color: #38BDF8; font-weight: 800;'>{self.domain_name}</span>")
        lbl_dom.setStyleSheet("font-size: 14px; font-weight: 600;")
        lbl_count = QLabel(f"Encontrado em <b>{len(self.associated_videos)}</b> vídeo(s) no YouTube")
        lbl_count.setStyleSheet("color: #94A3B8; font-size: 12px;")
        v_info.addWidget(lbl_dom)
        v_info.addWidget(lbl_count)
        h_layout.addLayout(v_info)

        h_layout.addStretch()

        # Action: Filter in main table
        btn_filter_main = QPushButton("🔍 Filtrar na Tabela Principal")
        btn_filter_main.setObjectName("btn_table_action")
        btn_filter_main.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_filter_main.clicked.connect(self._on_filter_main_clicked)
        h_layout.addWidget(btn_filter_main)

        # Copy all URLs
        btn_copy_all = QPushButton("📋 Copiar Todos os Links")
        btn_copy_all.setObjectName("btn_table_action")
        btn_copy_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_copy_all.clicked.connect(self._on_copy_urls_clicked)
        h_layout.addWidget(btn_copy_all)

        layout.addWidget(header_card)

        # Table
        table = QTableWidget()
        headers = ["Título do Vídeo", "Canal", "Data Envio", "Total Views", "Views 90d", "Tráfego Diário", "⚡ VPH", "Origem", "Ação"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(headers)):
            table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        table.setRowCount(len(self.associated_videos))
        table.verticalHeader().setDefaultSectionSize(46)
        table.verticalHeader().setVisible(True)

        for row, v in enumerate(self.associated_videos):
            title_item = QTableWidgetItem(v.get("video_title", "Vídeo"))
            title_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            title_item.setToolTip(v.get("video_title", ""))
            table.setItem(row, 0, title_item)

            channel_item = QTableWidgetItem(v.get("channel_name", ""))
            table.setItem(row, 1, channel_item)

            date_item = QTableWidgetItem(v.get("publish_date", "Recente"))
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 2, date_item)

            views_tot = v.get("view_count", 0)
            tot_item = NumericTableWidgetItem(format_number(views_tot), views_tot)
            tot_item.setForeground(QColor("#0284C7"))
            tot_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            table.setItem(row, 3, tot_item)

            views_90d = v.get("views_90d", views_tot)
            v90d_item = NumericTableWidgetItem(format_number(views_90d), views_90d)
            v90d_item.setForeground(QColor("#8B5CF6"))
            v90d_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            table.setItem(row, 4, v90d_item)

            d_views = v.get("daily_views", 0)
            daily_item = NumericTableWidgetItem(f"🔥 {format_number(round(d_views, 1))}/dia", d_views)
            daily_item.setForeground(QColor("#16A34A"))
            daily_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            table.setItem(row, 5, daily_item)

            h_views = v.get("hourly_views", round(d_views / 24.0, 1))
            vph_item = NumericTableWidgetItem(f"⚡ {format_number(round(h_views, 1))} VPH", h_views)
            vph_item.setForeground(QColor("#D97706"))
            vph_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            table.setItem(row, 6, vph_item)

            src_item = QTableWidgetItem(v.get("source_location", "Descrição"))
            table.setItem(row, 7, src_item)

            # Action Button
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_watch = QPushButton("▶ Assistir ↗")
            btn_watch.setObjectName("btn_table_action")
            btn_watch.setToolTip("Abrir no navegador padrão externo")
            btn_watch.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            v_url = v.get("video_url", "")
            btn_watch.clicked.connect(lambda _, u=v_url: self._on_watch_clicked(u))
            action_layout.addWidget(btn_watch)
            table.setCellWidget(row, 8, action_widget)

        layout.addWidget(table, 1)

        # Bottom Bar
        bottom_layout = QHBoxLayout()
        lbl_hint = QLabel("💡 Dica: Você pode abrir múltiplos vídeos ou filtrá-los na tabela principal de mineração.")
        lbl_hint.setStyleSheet("color: #94A3B8; font-size: 11px;")
        bottom_layout.addWidget(lbl_hint)
        bottom_layout.addStretch()

        btn_close = QPushButton("Fechar")
        btn_close.setFixedWidth(110)
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.clicked.connect(self.accept)
        bottom_layout.addWidget(btn_close)

        layout.addLayout(bottom_layout)

    def _on_watch_clicked(self, url: str):
        from PyQt6.QtGui import QDesktopServices
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _on_copy_urls_clicked(self):
        urls = [v.get("video_url", "") for v in self.associated_videos if v.get("video_url")]
        if urls:
            QApplication.clipboard().setText("\n".join(urls))
            QMessageBox.information(self, "Copiado", f"{len(urls)} links de vídeos copiados para a área de transferência!")

    def _on_filter_main_clicked(self):
        p = self.parent()
        if p and hasattr(p, "filter_videos_by_domain_requested"):
            p.filter_videos_by_domain_requested.emit(self.domain_name)
        self.accept()


class DomainTableView(QWidget):
    """
    Paginated interactive table for discovered domains and Instagram handles with Trademark Risk Intelligence.
    Features:
    - ⚖️ Segurança de Marca / Trademark Risk Badge (Identifica marcas notórias registradas, riscos de UDRP/INPI).
    - Expandable Drill-Down for multi-video domains ('🎯 Ver (X)').
    - 90-Day Traffic Sum ('Soma Views 90 Dias') across multiple videos.
    - Show/Hide Column Manager (Botão '👁️ Colunas' e menu contextual no cabeçalho).
    - Grouped by Domain: Shows exact count of videos where the domain appears.
    - Cumulative Daily Traffic Sum (Soma total do tráfego diário gerado em todos os vídeos associados).
    - Prioritizes AVAILABLE (🟢) domains/IGs on TOP with highest cumulative traffic.
    """
    buy_domain_requested = pyqtSignal(str)
    open_video_requested = pyqtSignal(str)
    domain_excluded_requested = pyqtSignal(str)
    filter_videos_by_domain_requested = pyqtSignal(str)

    COLUMN_HEADERS = [
        "Status",
        "Tipo",
        "Domínio / Conta IG",
        "⚖️ Segurança de Marca",
        "Vídeos Presente",
        "Soma Tráfego Diário",
        "Soma Views 90 Dias",
        "Soma Views Totais",
        "Vídeo Principal",
        "Data de Envio",
        "⚡ VPH Soma (Views/Hora)",
        "Views / Mês (Soma)",
        "Views / Ano (Soma)",
        "Detalhes / WHOIS",
        "Ação de Compra / Claim"
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.raw_domains_data: List[Dict[str, Any]] = []
        self.filtered_domains_data: List[Dict[str, Any]] = []
        
        self.current_page = 1
        self.page_size = 25
        self.status_filter = 0
        self.search_filter_text = ""

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 1. Top Filters & Search Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        toolbar.addWidget(QLabel("Filtrar por Status:"))
        self.combo_filter = QComboBox()
        self.combo_filter.addItem("Todos os Resultados", 0)
        self.combo_filter.addItem("🟢 Apenas Disponíveis (Domínios)", 1)
        self.combo_filter.addItem("📸 Contas Instagram Livres / Deletadas", 2)
        self.combo_filter.addItem("🟡 Domínios Inativos", 3)
        self.combo_filter.addItem("🔴 Domínios Ativos / Em Uso", 4)
        self.combo_filter.addItem("🛡️ Apenas Seguros (Livre de Marcas Registradas)", 5)
        self.combo_filter.currentIndexChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.combo_filter)

        toolbar.addStretch()

        # Column Visibility Selector Button
        self.btn_columns = QPushButton("👁️ Colunas")
        self.btn_columns.setObjectName("btn_table_action")
        self.btn_columns.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_columns.setToolTip("Exibir ou ocultar colunas da tabela")
        self.btn_columns.clicked.connect(self._show_column_menu)
        toolbar.addWidget(self.btn_columns)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("🔍 Buscar domínio ou termo...")
        self.input_search.setFixedWidth(220)
        self.input_search.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.input_search)

        layout.addLayout(toolbar)

        # 2. Main Domain Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_table_context_menu)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        header = self.table.horizontalHeader()
        header.setSectionsMovable(True)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._on_header_context_menu)

        for i in range(len(self.COLUMN_HEADERS)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

        self.table.verticalHeader().setDefaultSectionSize(54)
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setSectionsMovable(True)

        # Optimized spacious and comfortable default widths
        self.table.setColumnWidth(0, 130)  # Status
        self.table.setColumnWidth(1, 105)  # Tipo
        self.table.setColumnWidth(2, 220)  # Domínio / IG
        self.table.setColumnWidth(3, 155)  # ⚖️ Segurança de Marca
        self.table.setColumnWidth(4, 130)  # Vídeos Presente
        self.table.setColumnWidth(5, 145)  # Soma Tráfego Diário
        self.table.setColumnWidth(6, 140)  # Soma Views 90 Dias
        self.table.setColumnWidth(7, 135)  # Soma Views Totais
        self.table.setColumnWidth(8, 260)  # Vídeo Principal
        self.table.setColumnWidth(9, 110)  # Data de Envio
        self.table.setColumnWidth(10, 110) # Views/Hora
        self.table.setColumnWidth(11, 110) # Views/Mês (Optional)
        self.table.setColumnWidth(12, 110) # Views/Ano (Optional)
        self.table.setColumnWidth(13, 190) # Detalhes
        self.table.setColumnWidth(14, 330) # Ações (Spacious 330px width for all action buttons)

        # Hide redundant monthly/yearly projections by default to keep clean initial view
        self.table.setColumnHidden(11, True)
        self.table.setColumnHidden(12, True)

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(True)

        layout.addWidget(self.table)

        # 3. Bottom Pagination Bar
        self.pagination_frame = QFrame()
        self.pagination_frame.setObjectName("pagination_bar")
        p_layout = QHBoxLayout(self.pagination_frame)
        p_layout.setContentsMargins(8, 4, 8, 4)
        p_layout.setSpacing(10)

        self.btn_prev_page = QPushButton("◀ Anterior")
        self.btn_prev_page.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_prev_page.clicked.connect(self._prev_page)
        p_layout.addWidget(self.btn_prev_page)

        self.lbl_page_info = QLabel("Página 1 de 1 (0 domínios)")
        self.lbl_page_info.setStyleSheet("font-weight: 600;")
        p_layout.addWidget(self.lbl_page_info)

        self.btn_next_page = QPushButton("Próxima ▶")
        self.btn_next_page.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_next_page.clicked.connect(self._next_page)
        p_layout.addWidget(self.btn_next_page)

        p_layout.addStretch()

        p_layout.addWidget(QLabel("Itens por página:"))
        self.combo_page_size = QComboBox()
        self.combo_page_size.addItem("10 por página", 10)
        self.combo_page_size.addItem("25 por página", 25)
        self.combo_page_size.addItem("50 por página", 50)
        self.combo_page_size.addItem("100 por página", 100)
        self.combo_page_size.addItem("Todos", 999999)
        self.combo_page_size.setCurrentIndex(1)
        self.combo_page_size.currentIndexChanged.connect(self._on_page_size_changed)
        p_layout.addWidget(self.combo_page_size)

        layout.addWidget(self.pagination_frame)

    def _show_column_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { padding: 6px; font-weight: 600; }")
        for i, name in enumerate(self.COLUMN_HEADERS):
            action = QAction(name, menu)
            action.setCheckable(True)
            action.setChecked(not self.table.isColumnHidden(i))
            action.toggled.connect(lambda checked, col=i: self.table.setColumnHidden(col, not checked))
            menu.addAction(action)
        menu.exec(self.btn_columns.mapToGlobal(QPoint(0, self.btn_columns.height())))

    def _on_header_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { padding: 6px; font-weight: 600; }")
        for i, name in enumerate(self.COLUMN_HEADERS):
            action = QAction(name, menu)
            action.setCheckable(True)
            action.setChecked(not self.table.isColumnHidden(i))
            action.toggled.connect(lambda checked, col=i: self.table.setColumnHidden(col, not checked))
            menu.addAction(action)
        menu.exec(self.table.horizontalHeader().mapToGlobal(pos))

    def set_domains(self, domains: List[Dict[str, Any]]):
        """Aggregate occurrences of the same domain across multiple videos and calculate cumulative traffic."""
        grouped_dict: Dict[str, Dict[str, Any]] = {}

        for d in domains:
            key = d.get("root_domain", "").strip().lower()
            if not key:
                continue

            v_metrics = d.get("video_metrics", {})
            d_views = v_metrics.get("daily_views", 0)
            t_views = v_metrics.get("view_count", 0)
            v_90d = v_metrics.get("views_90d", t_views)
            h_views = v_metrics.get("hourly_views", 0)
            m_views = v_metrics.get("monthly_views", 0)
            y_views = v_metrics.get("yearly_views", 0)

            video_entry = {
                "video_id": d.get("video_id"),
                "video_title": d.get("video_title", ""),
                "video_url": d.get("video_url", ""),
                "channel_name": d.get("channel_name", ""),
                "publish_date": v_metrics.get("publish_date", ""),
                "daily_views": d_views,
                "view_count": t_views,
                "views_90d": v_90d,
                "source_location": d.get("source_location", "")
            }

            if key not in grouped_dict:
                tm_risk = d.get("trademark_risk") or analyze_trademark_risk(d.get("display_name") or d.get("root_domain") or "")
                grouped_dict[key] = {
                    **d,
                    "trademark_risk": tm_risk,
                    "video_count": 1,
                    "associated_videos": [video_entry],
                    "total_daily_views": d_views,
                    "total_view_count": t_views,
                    "total_views_90d": v_90d,
                    "total_hourly_views": h_views,
                    "total_monthly_views": m_views,
                    "total_yearly_views": y_views,
                    "source_locations": [d.get("source_location", "")]
                }
            else:
                existing = grouped_dict[key]
                v_id = d.get("video_id")
                if not any(v.get("video_id") == v_id for v in existing["associated_videos"]):
                    existing["video_count"] += 1
                    existing["associated_videos"].append(video_entry)
                    existing["total_daily_views"] += d_views
                    existing["total_view_count"] += t_views
                    existing["total_views_90d"] += v_90d
                    existing["total_hourly_views"] += h_views
                    existing["total_monthly_views"] += m_views
                    existing["total_yearly_views"] += y_views
                    if d.get("source_location") not in existing["source_locations"]:
                        existing["source_locations"].append(d.get("source_location", ""))

        aggregated_list = list(grouped_dict.values())

        def get_domain_priority_key(d: Dict[str, Any]):
            status = d.get("status", "")
            prio = 0 if status == "Disponível" else (1 if status == "Inativo" else 2)
            v_cnt = d.get("video_count", 1)
            daily = d.get("total_daily_views", 0)
            total = d.get("total_view_count", 0)
            return (prio, -v_cnt, -daily, -total)

        self.raw_domains_data = sorted(aggregated_list, key=get_domain_priority_key)
        self._apply_filter_and_render()

    def _on_filter_changed(self, idx: int):
        self.status_filter = idx
        self.current_page = 1
        self._apply_filter_and_render()

    def _on_search_changed(self, text: str):
        self.search_filter_text = text.strip().lower()
        self.current_page = 1
        self._apply_filter_and_render()

    def _on_page_size_changed(self):
        self.page_size = self.combo_page_size.currentData()
        self.current_page = 1
        self._apply_filter_and_render()

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_current_page()

    def _next_page(self):
        total_pages = max(1, math.ceil(len(self.filtered_domains_data) / self.page_size))
        if self.current_page < total_pages:
            self.current_page += 1
            self._render_current_page()

    def _apply_filter_and_render(self):
        filtered = self.raw_domains_data

        if self.status_filter == 1:
            filtered = [d for d in filtered if d.get("status") == "Disponível" and not d.get("is_instagram")]
        elif self.status_filter == 2:
            filtered = [d for d in filtered if d.get("is_instagram") and d.get("status") == "Disponível"]
        elif self.status_filter == 3:
            filtered = [d for d in filtered if d.get("status") == "Inativo"]
        elif self.status_filter == 4:
            filtered = [d for d in filtered if d.get("status") == "Ativo"]
        elif self.status_filter == 5:
            # Only Available & 100% Safe from Trademarks
            filtered = [
                d for d in filtered
                if d.get("status") == "Disponível"
                and (d.get("trademark_risk") or analyze_trademark_risk(d.get("display_name") or d.get("root_domain") or "")).get("is_safe", True)
            ]

        if self.search_filter_text:
            filtered = [
                d for d in filtered
                if self.search_filter_text in d.get("root_domain", "").lower()
                or self.search_filter_text in d.get("video_title", "").lower()
                or self.search_filter_text in d.get("display_name", "").lower()
            ]

        self.filtered_domains_data = filtered
        self._render_current_page()

    def _render_current_page(self):
        total_items = len(self.filtered_domains_data)
        total_pages = max(1, math.ceil(total_items / self.page_size))

        if self.current_page > total_pages:
            self.current_page = total_pages
        if self.current_page < 1:
            self.current_page = 1

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_items = self.filtered_domains_data[start_idx:end_idx]

        self.lbl_page_info.setText(f"Página {self.current_page} de {total_pages} (Exibindo {len(page_items)} de {total_items} domínios únicos)")
        self.btn_prev_page.setEnabled(self.current_page > 1)
        self.btn_next_page.setEnabled(self.current_page < total_pages)

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(page_items))

        for row, d in enumerate(page_items):
            status = d.get("status", "Desconhecido")
            is_ig = d.get("is_instagram", False)
            v_cnt = d.get("video_count", 1)
            assoc_vids = d.get("associated_videos", [])

            # 0. Status Badge
            badge_icon = d.get("badge_icon", "⚪")
            status_text = f"{badge_icon} {status}"
            status_item = QTableWidgetItem(status_text)
            status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            if status == "Disponível":
                status_item.setForeground(QColor("#16A34A"))
            elif status == "Inativo":
                status_item.setForeground(QColor("#D97706"))
            else:
                status_item.setForeground(QColor("#DC2626"))
            self.table.setItem(row, 0, status_item)

            # 1. Type
            type_text = "📸 Instagram" if is_ig else "🌐 Domínio"
            type_item = QTableWidgetItem(type_text)
            type_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            if is_ig:
                type_item.setForeground(QColor("#EC4899"))
            else:
                type_item.setForeground(QColor("#0284C7"))
            self.table.setItem(row, 1, type_item)

            # 2. Target Name / Root Domain
            display_name = d.get("display_name") or d.get("root_domain", "")
            domain_item = QTableWidgetItem(display_name)
            domain_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            if status == "Disponível":
                domain_item.setForeground(QColor("#16A34A"))
            self.table.setItem(row, 2, domain_item)

            # 3. Trademark & Brand Safety Badge (NEW!)
            tm = d.get("trademark_risk") or analyze_trademark_risk(display_name)
            is_safe = tm.get("is_safe", True)
            tm_color = tm.get("color", "#16A34A")
            tm_badge = tm.get("badge_short", "🟢 Seguro")
            
            tm_item = QTableWidgetItem(tm_badge)
            tm_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            tm_item.setForeground(QColor(tm_color))
            tm_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tm_item.setToolTip(
                f"{tm.get('badge')}\n\n"
                f"⚖️ Parecer de Risco Jurídico:\n{tm.get('legal_advice')}\n\n"
                f"Marcas Notórias Relacionadas: {tm.get('matched_names')}\n"
                f"Clique com o botão direito para consultar no INPI ou WIPO."
            )
            self.table.setItem(row, 3, tm_item)

            # 4. Video Count (Vídeos Onde Aparece) - Clean Centered Interactive Button
            v_cnt_widget = QWidget()
            v_cnt_layout = QHBoxLayout(v_cnt_widget)
            v_cnt_layout.setContentsMargins(4, 4, 4, 4)
            v_cnt_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_expand = QPushButton(f"🎯 Ver ({v_cnt})")
            btn_expand.setObjectName("btn_table_action")
            btn_expand.setToolTip(f"Buscar e mostrar todos os {v_cnt} vídeos onde o link '{display_name}' foi encontrado")
            btn_expand.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_expand.clicked.connect(lambda _, n=display_name, vids=assoc_vids: self._open_associated_videos_dialog(n, vids))
            v_cnt_layout.addWidget(btn_expand)

            self.table.setCellWidget(row, 4, v_cnt_widget)

            # 5. Cumulative Daily Traffic Sum (Soma Tráfego Diário)
            tot_daily = d.get("total_daily_views", 0)
            daily_formatted = f"🔥 {format_number(round(tot_daily, 1))}/dia"
            daily_item = NumericTableWidgetItem(daily_formatted, tot_daily)
            daily_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            daily_item.setForeground(QColor("#16A34A"))
            daily_item.setToolTip(f"Soma total do tráfego diário gerado por todos os {v_cnt} vídeos que contêm este domínio.")
            self.table.setItem(row, 5, daily_item)

            # 6. Cumulative 90-Day Views Sum (Soma Views 90 Dias)
            tot_90d = d.get("total_views_90d", d.get("total_view_count", 0))
            views_90d_formatted = f"⚡ {format_number(tot_90d)}"
            views_90d_item = NumericTableWidgetItem(views_90d_formatted, tot_90d)
            views_90d_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            views_90d_item.setForeground(QColor("#8B5CF6"))
            views_90d_item.setToolTip(f"Soma das visualizações recentes estimadas nos últimos 90 dias de todos os vídeos associados.")
            self.table.setItem(row, 6, views_90d_item)

            # 7. Cumulative Total Views (Soma Views Totais)
            tot_views = d.get("total_view_count", 0)
            tot_views_formatted = f"{format_number(tot_views)}"
            tot_views_item = NumericTableWidgetItem(tot_views_formatted, tot_views)
            tot_views_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            tot_views_item.setForeground(QColor("#0284C7"))
            tot_views_item.setToolTip(f"Soma de todas as visualizações acumuladas dos {v_cnt} vídeos associados.")
            self.table.setItem(row, 7, tot_views_item)

            # 8. Associated / Primary Video Title
            v_title = d.get("video_title", "")
            title_item = QTableWidgetItem(v_title)
            title_item.setToolTip(f"{v_title}\nCanal: {d.get('channel_name', '')}\nLink: {d.get('video_url', '')}")
            self.table.setItem(row, 8, title_item)

            # 9. Upload Date (Data de Envio)
            pub_date = d.get("video_metrics", {}).get("publish_date", "Recente")
            date_item = QTableWidgetItem(pub_date)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            date_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.table.setItem(row, 9, date_item)

            # 10. Cumulative Views per Hour (⚡ VPH Soma)
            tot_hourly = d.get("total_hourly_views", 0)
            hourly_item = NumericTableWidgetItem(format_vph(tot_hourly), tot_hourly)
            hourly_item.setForeground(QColor("#D97706"))
            hourly_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            hourly_item.setToolTip(f"Soma da velocidade horária recente de todos os {v_cnt} vídeos associados: {tot_hourly:.2f} views/hora.")
            self.table.setItem(row, 10, hourly_item)

            # 11. Cumulative Views per Month
            tot_monthly = d.get("total_monthly_views", 0)
            monthly_item = NumericTableWidgetItem(f"{format_number(round(tot_monthly, 1))}/mês", tot_monthly)
            self.table.setItem(row, 11, monthly_item)

            # 12. Cumulative Views per Year
            tot_yearly = d.get("total_yearly_views", 0)
            yearly_item = NumericTableWidgetItem(f"{format_number(round(tot_yearly, 1))}/ano", tot_yearly)
            self.table.setItem(row, 12, yearly_item)

            # 13. Details / WHOIS with Source Location Badge
            src_list = d.get("source_locations", [d.get("source_location", "")])
            src_label = ", ".join([s for s in src_list if s])
            raw_details = d.get("details", "")
            display_details = f"[{src_label}] {raw_details}" if src_label else raw_details
            details_item = QTableWidgetItem(display_details)
            details_item.setToolTip(f"Origem(ns): {src_label}\n{raw_details}")
            self.table.setItem(row, 13, details_item)

            # 14. Action Buttons Widget (Spacious & Clean Layout)
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            action_layout.setSpacing(5)

            buy_link = d.get("buy_link", "")
            reg_name = d.get("registrar_name", "Registrador")
            v_url = d.get("video_url", "")

            # 1. Action: Associated Videos
            btn_show_vids = QPushButton(f"🎬 {v_cnt} Vídeos")
            btn_show_vids.setObjectName("btn_table_action")
            btn_show_vids.setToolTip(f"Buscar e mostrar todos os {v_cnt} vídeos com o link '{display_name}'")
            btn_show_vids.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_show_vids.clicked.connect(lambda _, n=display_name, vids=assoc_vids: self._open_associated_videos_dialog(n, vids))
            action_layout.addWidget(btn_show_vids)

            # 2. Action: Watch Video
            btn_watch = QPushButton("▶ Vídeo ↗")
            btn_watch.setObjectName("btn_table_action")
            btn_watch.setToolTip("Abrir vídeo de origem no YouTube no seu navegador padrão (Chrome/Edge)")
            btn_watch.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_watch.clicked.connect(lambda _, u=v_url: self.open_video_requested.emit(u))
            action_layout.addWidget(btn_watch)

            # 3. Action: Register Domain or Claim IG
            if buy_link and status == "Disponível":
                btn_buy = QPushButton("🛒 Registrar ↗")
                btn_buy.setObjectName("btn_table_buy")
                btn_buy.setToolTip(f"Registrar este domínio no {reg_name}")
                btn_buy.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_buy.clicked.connect(lambda _, l=buy_link: self.buy_domain_requested.emit(l))
                action_layout.addWidget(btn_buy)
            elif is_ig and status == "Disponível":
                ig_url = f"https://www.instagram.com/{display_name.replace('@', '')}"
                btn_buy = QPushButton("📸 Reivindicar ↗")
                btn_buy.setObjectName("btn_table_buy")
                btn_buy.setToolTip("Abrir perfil no Instagram no seu navegador padrão (Chrome/Edge)")
                btn_buy.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_buy.clicked.connect(lambda _, l=ig_url: self.buy_domain_requested.emit(l))
                action_layout.addWidget(btn_buy)

            # 4. Action: Exclusion / Blacklist Button
            btn_exclude = QPushButton("🚫")
            btn_exclude.setObjectName("btn_table_action")
            btn_exclude.setToolTip(f"Adicionar '{display_name}' à lista de exclusão (ignorar para sempre)")
            btn_exclude.setStyleSheet("""
                QPushButton {
                    background-color: #1E293B;
                    color: #EF4444;
                    border: 1px solid #475569;
                    font-weight: 800;
                    font-size: 11px;
                    padding: 2px 6px;
                    border-radius: 4px;
                    min-height: 26px;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                    color: #FFFFFF;
                }
            """)
            btn_exclude.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_exclude.clicked.connect(lambda _, name=display_name, raw=d.get("root_domain", ""): self._on_exclude_domain(name, raw))
            action_layout.addWidget(btn_exclude)

            self.table.setCellWidget(row, 14, action_widget)

        self.table.setSortingEnabled(True)

    def _on_cell_double_clicked(self, row: int, col: int):
        """Double clicking any domain row opens its associated videos modal."""
        start_idx = (self.current_page - 1) * self.page_size
        idx = start_idx + row
        if 0 <= idx < len(self.filtered_domains_data):
            d = self.filtered_domains_data[idx]
            name = d.get("display_name") or d.get("root_domain", "")
            vids = d.get("associated_videos", [])
            self._open_associated_videos_dialog(name, vids)

    def _open_associated_videos_dialog(self, domain_name: str, associated_videos: List[Dict[str, Any]]):
        """Open modal dialog detailing all associated videos for this domain."""
        dialog = AssociatedVideosDialog(domain_name, associated_videos, self)
        dialog.exec()

    def _show_trademark_info_dialog(self, domain_name: str, tm: Dict[str, Any]):
        """Show informative dialog detailing trademark legal assessment."""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        
        is_safe = tm.get("is_safe", True)
        title = f"⚖️ Análise de Segurança de Marca: {domain_name}"
        icon = QMessageBox.Icon.Information if is_safe else QMessageBox.Icon.Warning
        
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setIcon(icon)
        msg.setText(f"<b>Domínio / Conta:</b> <span style='color: #38BDF8;'>{domain_name}</span><br><br>"
                    f"<b>Status de Risco:</b> {tm.get('badge')}<br><br>"
                    f"<b>Parecer Jurídico:</b><br>{tm.get('legal_advice')}<br><br>"
                    f"<b>Marcas Notórias Relacionadas:</b> {tm.get('matched_names')}")
        
        btn_inpi = msg.addButton("Consultar INPI ↗", QMessageBox.ButtonRole.ActionRole)
        btn_wipo = msg.addButton("Consultar WIPO ↗", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("Fechar", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        if msg.clickedButton() == btn_inpi:
            QDesktopServices.openUrl(QUrl(tm.get("inpi_url", "https://busca.inpi.gov.br/pePI/servlet/MarcasServletController")))
        elif msg.clickedButton() == btn_wipo:
            QDesktopServices.openUrl(QUrl(tm.get("wipo_url", "https://branddb.wipo.int/")))

    def _on_table_context_menu(self, pos: QPoint):
        item = self.table.itemAt(pos)
        if not item:
            return
        row = item.row()
        start_idx = (self.current_page - 1) * self.page_size
        idx = start_idx + row
        if idx < 0 or idx >= len(self.filtered_domains_data):
            return

        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl

        d = self.filtered_domains_data[idx]
        display_name = d.get("display_name") or d.get("root_domain", "")
        root_domain = d.get("root_domain", "")
        buy_link = d.get("buy_link", "")
        v_url = d.get("video_url", "")
        assoc_vids = d.get("associated_videos", [])
        tm = d.get("trademark_risk") or analyze_trademark_risk(display_name)

        menu = QMenu(self)
        menu.setStyleSheet("QMenu { padding: 6px; font-weight: 600; }")

        action_copy = QAction(f"📋 Copiar '{display_name}'", menu)
        action_copy.triggered.connect(lambda: QApplication.clipboard().setText(display_name))
        menu.addAction(action_copy)

        action_vids = QAction(f"🎯 Buscar e Mostrar Todos os Vídeos com este Link ({len(assoc_vids)})", menu)
        action_vids.triggered.connect(lambda: self._open_associated_videos_dialog(display_name, assoc_vids))
        menu.addAction(action_vids)

        action_filter_tab = QAction(f"🔍 Filtrar Tabela Principal de Vídeos por '{display_name}'", menu)
        action_filter_tab.triggered.connect(lambda: self.filter_videos_by_domain_requested.emit(display_name))
        menu.addAction(action_filter_tab)

        menu.addSeparator()

        # Trademark & Legal actions
        action_legal_info = QAction("⚖️ Ver Parecer Jurídico de Risco de Marca", menu)
        action_legal_info.triggered.connect(lambda: self._show_trademark_info_dialog(display_name, tm))
        menu.addAction(action_legal_info)

        action_inpi = QAction("🔎 Consultar Marca no INPI (Brasil) ↗", menu)
        action_inpi.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(tm.get("inpi_url", "https://busca.inpi.gov.br/pePI/servlet/MarcasServletController"))))
        menu.addAction(action_inpi)

        action_wipo = QAction("🌐 Consultar Marca no WIPO Brand Database ↗", menu)
        action_wipo.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(tm.get("wipo_url", "https://branddb.wipo.int/"))))
        menu.addAction(action_wipo)

        menu.addSeparator()

        if buy_link:
            action_buy = QAction("🛒 Abrir Link de Compra / Claim ↗", menu)
            action_buy.triggered.connect(lambda: self.buy_domain_requested.emit(buy_link))
            menu.addAction(action_buy)

        if v_url:
            action_watch = QAction("▶ Assistir Vídeo Principal ↗", menu)
            action_watch.triggered.connect(lambda: self.open_video_requested.emit(v_url))
            menu.addAction(action_watch)

        menu.addSeparator()

        action_exclude = QAction("🚫 Adicionar à Lista de Exclusão (Ignorar Domínio)", menu)
        action_exclude.triggered.connect(lambda: self._on_exclude_domain(display_name, root_domain))
        menu.addAction(action_exclude)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _on_exclude_domain(self, display_name: str, root_domain: str):
        target = root_domain or display_name
        clean_target = target.replace("📸 @", "").replace("@", "").strip()
        reply = QMessageBox.question(
            self,
            "Adicionar à Lista de Exclusão",
            f"Deseja adicionar o domínio '{clean_target}' à Lista de Exclusão?\n\n"
            f"• Ele será removido imediatamente desta tabela.\n"
            f"• Ele nunca mais aparecerá nesta ou em futuras varreduras.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            from core.domain_extractor import add_to_exclusion_list
            add_to_exclusion_list(clean_target)
            self.domain_excluded_requested.emit(clean_target)
