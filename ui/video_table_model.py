"""
Table models and view components for mined YouTube videos and domain/Instagram results.
Features:
- Large HD Video Thumbnails using dedicated cell widget (180x101 px).
- Integrated Pagination (10, 25, 50, 100, Todos) with page navigation.
- Real-time Filter: "🟢 Apenas com Domínios / IGs Disponíveis".
- 100% User-Resizable Columns and Rows (Interactive dragging of borders).
- Smart Priority Sorting (Disponíveis on top, ordered by views/hour/day).
"""

import math
from typing import List, Dict, Any, Optional, Union
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QFrame, QComboBox, QCheckBox,
    QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QFont, QCursor, QPixmap, QIcon

THUMBNAIL_CACHE: Dict[str, QPixmap] = {}

def load_pixmap_from_url(url: str, width: int = 180, height: int = 101) -> Optional[QPixmap]:
    """Fetch and cache scaled high-resolution pixmaps for video thumbnails."""
    if not url:
        return None
    if url in THUMBNAIL_CACHE:
        return THUMBNAIL_CACHE[url]

    try:
        resp = requests.get(url, timeout=3.0)
        if resp.status_code == 200:
            pix = QPixmap()
            pix.loadFromData(resp.content)
            scaled = pix.scaled(
                width, height,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            THUMBNAIL_CACHE[url] = scaled
            return scaled
    except Exception:
        pass
    return None


class ThumbnailWidget(QWidget):
    """Container for displaying high-resolution thumbnails centered inside cells."""
    def __init__(self, pixmap: Optional[QPixmap], parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_thumb = QLabel()
        self.lbl_thumb.setObjectName("thumbnail_label")
        self.lbl_thumb.setFixedSize(180, 101)
        self.lbl_thumb.setScaledContents(True)
        if pixmap:
            self.lbl_thumb.setPixmap(pixmap)
        
        layout.addWidget(self.lbl_thumb)


class VideoTableView(QWidget):
    """
    Paginated interactive table for mined YouTube videos with large thumbnails
    and quick filter for available opportunities.
    """
    open_video_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.raw_videos_data: List[Dict[str, Any]] = []
        self.filtered_videos_data: List[Dict[str, Any]] = []
        
        # Pagination state
        self.current_page = 1
        self.page_size = 25
        self.only_available_filter = False
        self.search_filter_text = ""

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 1. Top Filter & Search Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.chk_only_available = QCheckBox("🟢 Mostrar apenas vídeos com domínios/IGs disponíveis")
        self.chk_only_available.setStyleSheet("font-weight: 700;")
        self.chk_only_available.toggled.connect(self._on_filter_toggled)
        toolbar.addWidget(self.chk_only_available)

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
            "Data",
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
        self.table.setColumnWidth(8, 100)  # Data
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
        end_idx = min(start_idx + self.page_size, total_items)
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

            # 0. Large HD Thumbnail (180x101)
            thumb_pix = load_pixmap_from_url(v.get("thumbnail", ""), width=180, height=101)
            thumb_widget = ThumbnailWidget(thumb_pix)
            self.table.setCellWidget(row, 0, thumb_widget)

            # 1. Title
            title_item = QTableWidgetItem(v.get("title", ""))
            title_item.setToolTip(v.get("title", ""))
            title_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(row, 1, title_item)

            # 2. Channel
            channel_item = QTableWidgetItem(v.get("channel_name", ""))
            self.table.setItem(row, 2, channel_item)

            # 3. Total Views
            view_cnt = m.get("view_count", 0)
            views_item = NumericTableWidgetItem(m.get("view_count_formatted", "0"), view_cnt)
            views_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            views_item.setForeground(QColor("#0284C7"))
            self.table.setItem(row, 3, views_item)

            # 4. Hourly Views
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

            # 8. Publish Date
            date_item = QTableWidgetItem(m.get("publish_date", ""))
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
    Prioritizes AVAILABLE (🟢) domains/IGs on TOP.
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
        layout.setSpacing(6)

        # 1. Filter bar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        toolbar.addWidget(QLabel("Filtrar:"))
        self.combo_domain_filter = QComboBox()
        self.combo_domain_filter.addItems([
            "Todos os Resultados",
            "🟢 Apenas Domínios Disponíveis / Expirados",
            "📸 Apenas Instagrams Disponíveis / Deletados",
            "🟡 Apenas Inativos (DNS Caído)",
            "🔴 Apenas Ativos"
        ])
        self.combo_domain_filter.currentIndexChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.combo_domain_filter)

        toolbar.addStretch()

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("🔍 Filtrar por domínio ou termo...")
        self.input_search.setFixedWidth(240)
        self.input_search.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.input_search)

        layout.addLayout(toolbar)

        # 2. Main Domain Table
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Status",
            "Tipo",
            "Domínio / Conta IG",
            "Vídeo Associado",
            "Views / Hora",
            "Views / Dia",
            "Views / Mês",
            "Views / Ano",
            "Total Views",
            "Detalhes / WHOIS",
            "Ação de Compra / Claim"
        ])

        header = self.table.horizontalHeader()
        header.setSectionsMovable(True)
        for i in range(11):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setSectionsMovable(True)

        # Generous default widths
        self.table.setColumnWidth(0, 140)  # Status
        self.table.setColumnWidth(1, 120)  # Tipo
        self.table.setColumnWidth(2, 230)  # Domínio / IG
        self.table.setColumnWidth(3, 320)  # Vídeo
        self.table.setColumnWidth(4, 110)  # Views/Hora
        self.table.setColumnWidth(5, 110)  # Views/Dia
        self.table.setColumnWidth(6, 110)  # Views/Mês
        self.table.setColumnWidth(7, 110)  # Views/Ano
        self.table.setColumnWidth(8, 110)  # Total Views
        self.table.setColumnWidth(9, 250)  # Detalhes
        self.table.setColumnWidth(10, 160) # Ação

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
        def get_domain_priority_key(d: Dict[str, Any]):
            status = d.get("status", "")
            prio = 0 if status == "Disponível" else (1 if status == "Inativo" else 2)
            m = d.get("video_metrics", {})
            hourly = m.get("hourly_views", 0)
            daily = m.get("daily_views", 0)
            total = m.get("view_count", 0)
            return (prio, -hourly, -daily, -total)

        self.raw_domains_data = sorted(domains, key=get_domain_priority_key)
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
            filtered = [d for d in filtered if d.get("status") == "Disponível" and d.get("is_instagram")]
        elif self.status_filter == 3:
            filtered = [d for d in filtered if d.get("status") == "Inativo"]
        elif self.status_filter == 4:
            filtered = [d for d in filtered if d.get("status") == "Ativo"]

        if self.search_filter_text:
            filtered = [
                d for d in filtered
                if self.search_filter_text in d.get("root_domain", "").lower()
                or self.search_filter_text in d.get("video_title", "").lower()
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
        end_idx = min(start_idx + self.page_size, total_items)
        page_items = self.filtered_domains_data[start_idx:end_idx]

        self.lbl_page_info.setText(f"Página {self.current_page} de {total_pages} (Exibindo {len(page_items)} de {total_items} registros)")
        self.btn_prev_page.setEnabled(self.current_page > 1)
        self.btn_next_page.setEnabled(self.current_page < total_pages)

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(page_items))

        for row, d in enumerate(page_items):
            status = d.get("status", "Desconhecido")
            badge_icon = d.get("badge_icon", "⚪")
            metrics = d.get("video_metrics", {})
            is_ig = d.get("is_instagram", False)

            # 0. Status
            prio_val = 1 if status == "Disponível" else (2 if status == "Inativo" else 3)
            status_text = f"{badge_icon} {status}"
            status_item = NumericTableWidgetItem(status_text, prio_val)
            if status == "Disponível":
                status_item.setForeground(QColor("#16A34A"))
            elif status == "Inativo":
                status_item.setForeground(QColor("#D97706"))
            else:
                status_item.setForeground(QColor("#DC2626"))
            status_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(row, 0, status_item)

            # 1. Type
            type_label = "📸 Instagram" if is_ig else "🌐 Domínio"
            type_item = QTableWidgetItem(type_label)
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

            # 3. Associated Video Title
            v_title = d.get("video_title", "")
            title_item = QTableWidgetItem(v_title)
            title_item.setToolTip(f"{v_title}\nCanal: {d.get('channel_name', '')}\nLink: {d.get('video_url', '')}")
            self.table.setItem(row, 3, title_item)

            # 4. Views per Hour
            hourly_v = metrics.get("hourly_views", 0)
            hourly_item = NumericTableWidgetItem(metrics.get("hourly_views_formatted", "0/h"), hourly_v)
            hourly_item.setForeground(QColor("#D97706"))
            hourly_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(row, 4, hourly_item)

            # 5. Views per Day
            daily_v = metrics.get("daily_views", 0)
            daily_item = NumericTableWidgetItem(metrics.get("daily_views_formatted", "0/dia"), daily_v)
            daily_item.setForeground(QColor("#16A34A"))
            daily_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(row, 5, daily_item)

            # 6. Views per Month
            monthly_v = metrics.get("monthly_views", 0)
            monthly_item = NumericTableWidgetItem(metrics.get("monthly_views_formatted", "0/mês"), monthly_v)
            self.table.setItem(row, 6, monthly_item)

            # 7. Views per Year
            yearly_v = metrics.get("yearly_views", 0)
            yearly_item = NumericTableWidgetItem(metrics.get("yearly_views_formatted", "0/ano"), yearly_v)
            self.table.setItem(row, 7, yearly_item)

            # 8. Total Views
            v_views = metrics.get("view_count", 0)
            views_item = NumericTableWidgetItem(metrics.get("view_count_formatted", "0"), v_views)
            views_item.setForeground(QColor("#0284C7"))
            views_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(row, 8, views_item)

            # 9. Details / WHOIS
            details_item = QTableWidgetItem(d.get("details", ""))
            details_item.setToolTip(d.get("details", ""))
            self.table.setItem(row, 9, details_item)

            # 10. Action Button
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

            if is_ig:
                if status == "Disponível":
                    btn_claim = QPushButton("📸 Criar IG")
                    btn_claim.setObjectName("btn_success")
                    btn_claim.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                    btn_claim.clicked.connect(lambda _, l=buy_link: self.buy_domain_requested.emit(l))
                    action_layout.addWidget(btn_claim)
                else:
                    btn_ig = QPushButton("📸 Ver IG")
                    btn_ig.setObjectName("btn_table_action")
                    btn_ig.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                    btn_ig.clicked.connect(lambda _, l=buy_link: self.buy_domain_requested.emit(l))
                    action_layout.addWidget(btn_ig)
            else:
                if status == "Disponível":
                    btn_buy = QPushButton(f"🛒 Comprar ({reg_name})")
                    btn_buy.setObjectName("btn_success")
                    btn_buy.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                    btn_buy.clicked.connect(lambda _, l=buy_link: self.buy_domain_requested.emit(l))
                    action_layout.addWidget(btn_buy)
                else:
                    btn_whois = QPushButton("🔍 Consultar")
                    btn_whois.setObjectName("btn_table_action")
                    btn_whois.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                    btn_whois.clicked.connect(lambda _, l=buy_link: self.buy_domain_requested.emit(l))
                    action_layout.addWidget(btn_whois)

            self.table.setCellWidget(row, 10, action_widget)

        self.table.setSortingEnabled(True)


class NumericTableWidgetItem(QTableWidgetItem):
    """Custom TableWidgetItem that sorts numerically instead of alphabetically."""
    def __init__(self, display_text: str, sort_value: Union[float, int]):
        super().__init__(display_text)
        self.sort_value = sort_value

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self.sort_value < other.sort_value
        return super().__lt__(other)
