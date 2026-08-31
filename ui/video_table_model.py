"""
Video Table and Domain Table UI Components.
Features:
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
    QFrame, QHeaderView, QLineEdit, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QColor, QFont, QCursor, QPixmap, QImage
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from core.metrics_calculator import format_number

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
    """High quality asynchronous thumbnail loader with caching."""
    _pixmap_cache: Dict[str, QPixmap] = {}
    _net_manager: Optional[QNetworkAccessManager] = None

    def __init__(self, url: str, width: int = 180, height: int = 101, parent=None):
        super().__init__(parent)
        self.url = url
        self.target_width = width
        self.target_height = height
        self.setFixedSize(width, height)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #0F172A; border-radius: 6px; border: 1px solid #334155;")

        if AsyncThumbnailLabel._net_manager is None:
            AsyncThumbnailLabel._net_manager = QNetworkAccessManager()

        self._load_thumbnail()

    def _load_thumbnail(self):
        if not self.url:
            self.setText("Sem Imagem")
            return

        if self.url in AsyncThumbnailLabel._pixmap_cache:
            self.setPixmap(AsyncThumbnailLabel._pixmap_cache[self.url])
            return

        self.setText("Carregando...")
        req = QNetworkRequest(QUrl(self.url))
        reply = AsyncThumbnailLabel._net_manager.get(req)
        reply.finished.connect(lambda: self._on_reply_finished(reply))

    def _on_reply_finished(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            img = QImage()
            if img.loadFromData(data):
                scaled = QPixmap.fromImage(img).scaled(
                    self.target_width,
                    self.target_height,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                AsyncThumbnailLabel._pixmap_cache[self.url] = scaled
                self.setPixmap(scaled)
            else:
                self.setText("Erro Img")
        else:
            self.setText("Erro")
        reply.deleteLater()


class VideoTableView(QWidget):
    """
    Paginated interactive table for mined videos with 180x101 thumbnails,
    Traffic Metrics, Upload Date ('Data de Envio'), and Discovered Domains summary.
    """
    open_video_requested = pyqtSignal(str)

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

        # 1. Top Filter & Search Bar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.chk_filter_avail = QCheckBox("🟢 Mostrar apenas vídeos com domínios/IGs disponíveis")
        self.chk_filter_avail.setStyleSheet("font-weight: 700; color: #10B981;")
        self.chk_filter_avail.toggled.connect(self._on_filter_toggled)
        toolbar.addWidget(self.chk_filter_avail)

        toolbar.addStretch()

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("🔍 Filtrar resultados na lista...")
        self.input_search.setFixedWidth(240)
        self.input_search.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.input_search)

        layout.addLayout(toolbar)

        # 2. Main Video Table
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Miniatura",
            "Título do Vídeo",
            "Canal",
            "Total Views",
            "Views / Hora",
            "Views / Dia",
            "Views / Mês",
            "Views / Ano",
            "Data de Envio",
            "Domínios / IGs",
            "Ações"
        ])
        
        # Large rows for 180x101 thumbnails with interactive resizing & movable columns
        self.table.verticalHeader().setDefaultSectionSize(115)
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setSectionsMovable(True)

        header = self.table.horizontalHeader()
        header.setSectionsMovable(True)
        for i in range(11):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

        # Generous default widths
        self.table.setColumnWidth(0, 205)  # Miniatura (Large 180px + padding)
        self.table.setColumnWidth(1, 330)  # Título
        self.table.setColumnWidth(2, 160)  # Canal
        self.table.setColumnWidth(3, 110)  # Total Views
        self.table.setColumnWidth(4, 110)  # Views / Hora
        self.table.setColumnWidth(5, 110)  # Views / Dia
        self.table.setColumnWidth(6, 110)  # Views / Mês
        self.table.setColumnWidth(7, 110)  # Views / Ano
        self.table.setColumnWidth(8, 120)  # Data de Envio
        self.table.setColumnWidth(9, 140)  # Domínios
        self.table.setColumnWidth(10, 110) # Ações

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

    def set_videos(self, videos: List[Dict[str, Any]]):
        self.raw_videos_data = videos
        self._apply_filter_and_render()

    def _on_filter_toggled(self, checked: bool):
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
            thumb_layout = QHBoxLayout(thumb_widget)
            thumb_layout.setContentsMargins(6, 6, 6, 6)
            thumb_lbl = AsyncThumbnailLabel(v.get("thumbnail", ""), width=180, height=101)
            thumb_layout.addWidget(thumb_lbl)
            self.table.setCellWidget(row, 0, thumb_widget)

            # 1. Title
            title_item = QTableWidgetItem(v.get("title", ""))
            title_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            title_item.setToolTip(v.get("title", ""))
            self.table.setItem(row, 1, title_item)

            # 2. Channel
            channel_item = QTableWidgetItem(v.get("channel_name", ""))
            channel_item.setToolTip(v.get("channel_name", ""))
            self.table.setItem(row, 2, channel_item)

            # 3. Total Views
            v_views = m.get("view_count", 0)
            views_item = NumericTableWidgetItem(m.get("view_count_formatted", "0"), v_views)
            views_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            views_item.setForeground(QColor("#0284C7"))
            self.table.setItem(row, 3, views_item)

            # 4. Hourly Average
            hourly_views = m.get("hourly_views", 0)
            hourly_item = NumericTableWidgetItem(m.get("hourly_views_formatted", "0/h"), hourly_views)
            hourly_item.setForeground(QColor("#D97706"))
            hourly_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(row, 4, hourly_item)

            # 5. Daily Average
            daily_views = m.get("daily_views", 0)
            daily_item = NumericTableWidgetItem(m.get("daily_views_formatted", "0/dia"), daily_views)
            daily_item.setForeground(QColor("#16A34A"))
            daily_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(row, 5, daily_item)

            # 6. Monthly Average
            monthly_views = m.get("monthly_views", 0)
            monthly_item = NumericTableWidgetItem(m.get("monthly_views_formatted", "0/mês"), monthly_views)
            self.table.setItem(row, 6, monthly_item)

            # 7. Yearly Average
            yearly_views = m.get("yearly_views", 0)
            yearly_item = NumericTableWidgetItem(m.get("yearly_views_formatted", "0/ano"), yearly_views)
            self.table.setItem(row, 7, yearly_item)

            # 8. Publish Date (Data de Envio)
            pub_date = m.get("publish_date", "Recente")
            date_item = QTableWidgetItem(pub_date)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            date_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.table.setItem(row, 8, date_item)

            # 9. Domains / IGs Badge Summary
            dom_summary = f"🟢 {avail_cnt} | 🟡 {inact_cnt} | Total: {len(domains)}"
            dom_item = NumericTableWidgetItem(dom_summary, avail_cnt * 1000000 + len(domains))
            if avail_cnt > 0:
                dom_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                dom_item.setForeground(QColor("#16A34A"))
            self.table.setItem(row, 9, dom_item)

            # 10. Action Buttons Widget
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(6, 4, 6, 4)
            action_layout.setSpacing(6)

            btn_open = QPushButton("▶ Assistir")
            btn_open.setObjectName("btn_table_action")
            btn_open.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            v_url = v.get("url", "")
            btn_open.clicked.connect(lambda _, u=v_url: self.open_video_requested.emit(u))

            action_layout.addWidget(btn_open)
            self.table.setCellWidget(row, 10, action_widget)

        self.table.setSortingEnabled(True)


class DomainTableView(QWidget):
    """
    Paginated interactive table for discovered domains and Instagram handles.
    Features:
    - Grouped by Domain: Shows exact count of videos where the domain appears.
    - Cumulative Daily Traffic Sum (Soma total do tráfego diário gerado em todos os vídeos associados).
    - Prioritizes AVAILABLE (🟢) domains/IGs on TOP with highest cumulative traffic.
    """
    buy_domain_requested = pyqtSignal(str)
    open_video_requested = pyqtSignal(str)

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
        toolbar.setSpacing(12)

        toolbar.addWidget(QLabel("Filtrar por Status:"))
        self.combo_filter = QComboBox()
        self.combo_filter.addItem("Todos os Resultados", 0)
        self.combo_filter.addItem("🟢 Apenas Disponíveis (Domínios)", 1)
        self.combo_filter.addItem("📸 Contas Instagram Livres / Deletadas", 2)
        self.combo_filter.addItem("🟡 Domínios Inativos", 3)
        self.combo_filter.addItem("🔴 Domínios Ativos / Em Uso", 4)
        self.combo_filter.currentIndexChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.combo_filter)

        toolbar.addStretch()

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("🔍 Buscar domínio, extensão ou termo...")
        self.input_search.setFixedWidth(260)
        self.input_search.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.input_search)

        layout.addLayout(toolbar)

        # 2. Main Domain Table (13 Columns with Video Count & Cumulative Traffic)
        self.table = QTableWidget()
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "Status",
            "Tipo",
            "Domínio / Conta IG",
            "Vídeos Presente",
            "Soma Tráfego Diário",
            "Soma Views Totais",
            "Vídeo Principal",
            "Data de Envio",
            "Views / Hora (Soma)",
            "Views / Mês (Soma)",
            "Views / Ano (Soma)",
            "Detalhes / WHOIS",
            "Ação de Compra / Claim"
        ])

        header = self.table.horizontalHeader()
        header.setSectionsMovable(True)
        for i in range(13):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setSectionsMovable(True)

        # Generous default widths
        self.table.setColumnWidth(0, 140)  # Status
        self.table.setColumnWidth(1, 110)  # Tipo
        self.table.setColumnWidth(2, 220)  # Domínio / IG
        self.table.setColumnWidth(3, 130)  # Vídeos Presente
        self.table.setColumnWidth(4, 155)  # Soma Tráfego Diário
        self.table.setColumnWidth(5, 140)  # Soma Views Totais
        self.table.setColumnWidth(6, 260)  # Vídeo Principal
        self.table.setColumnWidth(7, 115)  # Data de Envio
        self.table.setColumnWidth(8, 120)  # Views/Hora
        self.table.setColumnWidth(9, 120)  # Views/Mês
        self.table.setColumnWidth(10, 120) # Views/Ano
        self.table.setColumnWidth(11, 230) # Detalhes
        self.table.setColumnWidth(12, 160) # Ação

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
                "source_location": d.get("source_location", "")
            }

            if key not in grouped_dict:
                grouped_dict[key] = {
                    **d,
                    "video_count": 1,
                    "associated_videos": [video_entry],
                    "total_daily_views": d_views,
                    "total_view_count": t_views,
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

            # 3. Video Count (Vídeos Onde Aparece)
            v_cnt_text = f"🎯 {v_cnt} vídeos" if v_cnt > 1 else "🎯 1 vídeo"
            v_cnt_item = NumericTableWidgetItem(v_cnt_text, v_cnt)
            v_cnt_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            if v_cnt > 1:
                v_cnt_item.setForeground(QColor("#7C3AED")) # Highlight purple for multi-video domains!
            
            # Rich Tooltip listing all videos
            tooltip_vids = "\n".join([f"• {v.get('video_title')} ({format_number(v.get('daily_views', 0))}/dia)" for v in assoc_vids[:8]])
            if len(assoc_vids) > 8:
                tooltip_vids += f"\n...e mais {len(assoc_vids) - 8} vídeos"
            v_cnt_item.setToolTip(f"Presente em {v_cnt} vídeos:\n{tooltip_vids}")
            self.table.setItem(row, 3, v_cnt_item)

            # 4. Cumulative Daily Traffic Sum (Soma Tráfego Diário)
            tot_daily = d.get("total_daily_views", 0)
            daily_formatted = f"🔥 {format_number(round(tot_daily, 1))}/dia"
            daily_item = NumericTableWidgetItem(daily_formatted, tot_daily)
            daily_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            daily_item.setForeground(QColor("#16A34A"))
            daily_item.setToolTip(f"Soma total do tráfego diário gerado por todos os {v_cnt} vídeos que contêm este domínio.")
            self.table.setItem(row, 4, daily_item)

            # 5. Cumulative Total Views (Soma Views Totais)
            tot_views = d.get("total_view_count", 0)
            tot_views_formatted = f"{format_number(tot_views)}"
            tot_views_item = NumericTableWidgetItem(tot_views_formatted, tot_views)
            tot_views_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            tot_views_item.setForeground(QColor("#0284C7"))
            tot_views_item.setToolTip(f"Soma de todas as visualizações acumuladas dos {v_cnt} vídeos associados.")
            self.table.setItem(row, 5, tot_views_item)

            # 6. Associated / Primary Video Title
            v_title = d.get("video_title", "")
            title_item = QTableWidgetItem(v_title)
            title_item.setToolTip(f"{v_title}\nCanal: {d.get('channel_name', '')}\nLink: {d.get('video_url', '')}")
            self.table.setItem(row, 6, title_item)

            # 7. Upload Date (Data de Envio)
            pub_date = d.get("video_metrics", {}).get("publish_date", "Recente")
            date_item = QTableWidgetItem(pub_date)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            date_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.table.setItem(row, 7, date_item)

            # 8. Cumulative Views per Hour
            tot_hourly = d.get("total_hourly_views", 0)
            hourly_item = NumericTableWidgetItem(f"{format_number(round(tot_hourly, 1))}/h", tot_hourly)
            hourly_item.setForeground(QColor("#D97706"))
            self.table.setItem(row, 8, hourly_item)

            # 9. Cumulative Views per Month
            tot_monthly = d.get("total_monthly_views", 0)
            monthly_item = NumericTableWidgetItem(f"{format_number(round(tot_monthly, 1))}/mês", tot_monthly)
            self.table.setItem(row, 9, monthly_item)

            # 10. Cumulative Views per Year
            tot_yearly = d.get("total_yearly_views", 0)
            yearly_item = NumericTableWidgetItem(f"{format_number(round(tot_yearly, 1))}/ano", tot_yearly)
            self.table.setItem(row, 10, yearly_item)

            # 11. Details / WHOIS with Source Location Badge
            src_list = d.get("source_locations", [d.get("source_location", "")])
            src_label = ", ".join([s for s in src_list if s])
            raw_details = d.get("details", "")
            display_details = f"[{src_label}] {raw_details}" if src_label else raw_details
            details_item = QTableWidgetItem(display_details)
            details_item.setToolTip(f"Origem(ns): {src_label}\n{raw_details}")
            self.table.setItem(row, 11, details_item)

            # 12. Action Button
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(6, 4, 6, 4)
            action_layout.setSpacing(6)

            buy_link = d.get("buy_link", "")
            reg_name = d.get("registrar_name", "Registrador")
            v_url = d.get("video_url", "")

            btn_watch = QPushButton("▶ Vídeo")
            btn_watch.setObjectName("btn_table_action")
            btn_watch.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_watch.clicked.connect(lambda _, u=v_url: self.open_video_requested.emit(u))
            action_layout.addWidget(btn_watch)

            if buy_link and status == "Disponível":
                btn_buy = QPushButton(f"🛒 Registrar ({reg_name})")
                btn_buy.setObjectName("btn_table_buy")
                btn_buy.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_buy.clicked.connect(lambda _, l=buy_link: self.buy_domain_requested.emit(l))
                action_layout.addWidget(btn_buy)

            self.table.setCellWidget(row, 12, action_widget)

        self.table.setSortingEnabled(True)
