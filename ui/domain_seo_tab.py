import math
import csv
import os
import webbrowser
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QLineEdit, QComboBox, QFrame, QFileDialog, QMenu, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QColor, QCursor, QAction

# Assuming this exists, fallback if not
try:
    from core.domain_seo_service import DomainSEOService, load_api_key
except ImportError:
    pass


class SEOAnalysisThread(QThread):
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    domain_analyzed = pyqtSignal(dict)  # single domain result
    finished_analysis = pyqtSignal(list)  # all results
    
    def __init__(self, domains: List[str], seo_service):
        super().__init__()
        self.domains = domains
        self.seo_service = seo_service
    
    def run(self):
        results = self.seo_service.bulk_analyze(
            self.domains,
            on_progress=lambda cur, tot, msg: self.progress_updated.emit(cur, tot, msg)
        )
        self.finished_analysis.emit(results)


class DomainSEOTab(QWidget):
    """
    Aba de Análise SEO para domínios disponíveis.
    """
    open_url_requested = pyqtSignal(str)
    analyze_requested = pyqtSignal()

    COLUMN_HEADERS = [
        "Domínio", "📊 DA", "📈 PageRank", "🔗 Ref. Domains", "📅 Idade",
        "🗓️ Criação", "🗓️ Expiração", "🏛️ Registrar", "📸 Snapshots",
        "📆 1º Snapshot", "📡 DNS Records", "📧 Email", "🏅 Score SEO",
        "🎯 Nota", "💰 Valor Est.", "🎬 Vídeos", "🔥 Tráfego/Dia", "Ação"
    ]
    
    COLUMN_WIDTHS = [
        180, 65, 80, 100, 110,
        100, 100, 130, 80,
        100, 85, 60, 80,
        55, 90, 65, 95, 200
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.domains_data: List[Dict[str, Any]] = []
        self.filtered_data: List[Dict[str, Any]] = []
        
        self.current_page = 1
        self.page_size = 25
        self.search_text = ""
        
        self.seo_service = None  # Instantiated as needed or injected
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # --- Toolbar ---
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.btn_analyze_all = QPushButton("🔍 Analisar Todos os Disponíveis")
        self.btn_analyze_all.setObjectName("btn_start_action")
        self.btn_analyze_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_analyze_all.clicked.connect(self._on_analyze_all)
        toolbar.addWidget(self.btn_analyze_all)
        
        self.btn_reanalyze = QPushButton("🔄 Re-analisar Selecionado")
        self.btn_reanalyze.setObjectName("btn_table_action")
        self.btn_reanalyze.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_reanalyze.clicked.connect(self._on_reanalyze_selected)
        toolbar.addWidget(self.btn_reanalyze)
        
        self.btn_export = QPushButton("📥 Exportar CSV")
        self.btn_export.setObjectName("btn_table_action")
        self.btn_export.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export.clicked.connect(self._export_csv)
        toolbar.addWidget(self.btn_export)
        
        toolbar.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(150)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        toolbar.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #AAAAAA; font-weight: bold;")
        toolbar.addWidget(self.lbl_status)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("🔍 Buscar domínio...")
        self.input_search.setFixedWidth(200)
        self.input_search.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.input_search)

        layout.addLayout(toolbar)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setSortingEnabled(False)
        self.table.verticalHeader().setVisible(False)
        
        header = self.table.horizontalHeader()
        header.setSectionsMovable(True)
        for i in range(len(self.COLUMN_HEADERS)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            self.table.setColumnWidth(i, self.COLUMN_WIDTHS[i])
            
        layout.addWidget(self.table)

        # --- Pagination ---
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

        p_layout.addWidget(QLabel("Domínios por página:"))
        self.combo_page_size = QComboBox()
        self.combo_page_size.addItem("10", 10)
        self.combo_page_size.addItem("25", 25)
        self.combo_page_size.addItem("50", 50)
        self.combo_page_size.addItem("100", 100)
        self.combo_page_size.setCurrentIndex(1)
        self.combo_page_size.currentIndexChanged.connect(self._on_page_size_changed)
        p_layout.addWidget(self.combo_page_size)

        layout.addWidget(self.pagination_frame)

    def add_domain(self, domain_data: Dict[str, Any]):
        """Adiciona um domínio se ele estiver disponível e não for duplicado."""
        if domain_data.get("status") != "Disponível":
            return
            
        root_domain = domain_data.get("root_domain", "")
        # Verifica duplicata
        if any(d.get("root_domain") == root_domain for d in self.domains_data):
            # Atualizar vídeo/tráfego se for o mesmo domínio?
            for d in self.domains_data:
                if d.get("root_domain") == root_domain:
                    d["video_count"] = d.get("video_count", 0) + domain_data.get("video_count", 1)
                    d["total_daily_views"] = d.get("total_daily_views", 0) + domain_data.get("total_daily_views", 0)
            self._apply_filter_and_render()
            return
            
        new_data = {
            "root_domain": root_domain,
            "display_name": domain_data.get("display_name", root_domain),
            "video_count": domain_data.get("video_count", 1),
            "total_daily_views": domain_data.get("total_daily_views", 0),
            "buy_link": domain_data.get("buy_link", f"https://www.namecheap.com/domains/registration/results/?domain={root_domain}")
        }
        self.domains_data.append(new_data)
        self._apply_filter_and_render()

    def set_seo_results(self, results: List[Dict[str, Any]]):
        """Recebe resultados da análise em lote e atualiza a tabela."""
        for res in results:
            dom = res.get("domain", "")
            self.update_domain_seo(dom, res)
        self._apply_filter_and_render()
        
        self.progress_bar.hide()
        self.lbl_status.setText("✅ Análise concluída")
        self.btn_analyze_all.setEnabled(True)

    def update_domain_seo(self, domain: str, seo_data: Dict[str, Any]):
        """Atualiza os dados de SEO de um único domínio na tabela."""
        for d in self.domains_data:
            if d.get("root_domain") == domain:
                d.update(seo_data)
                break
        self._apply_filter_and_render()

    def _on_analyze_all(self):
        """Inicia a análise de todos os domínios listados (que ainda não foram analisados ou forçado)."""
        self.analyze_requested.emit()
        
        try:
            from core.domain_seo_service import DomainSEOService, load_api_key
            
            # Pega domínios disponíveis na tela (filtrados ou todos?)
            domains_to_analyze = [d.get("root_domain") for d in self.domains_data if "da" not in d]
            if not domains_to_analyze:
                self.lbl_status.setText("Todos já analisados. Use Re-analisar para forçar.")
                return

            api_key = load_api_key()
            if not self.seo_service:
                self.seo_service = DomainSEOService(api_key=api_key)
                
            self.btn_analyze_all.setEnabled(False)
            self.progress_bar.show()
            self.progress_bar.setMaximum(len(domains_to_analyze))
            self.progress_bar.setValue(0)
            self.lbl_status.setText("Iniciando análise...")
            
            self.thread = SEOAnalysisThread(domains_to_analyze, self.seo_service)
            self.thread.progress_updated.connect(self._on_progress_update)
            self.thread.finished_analysis.connect(self.set_seo_results)
            self.thread.start()
            
        except Exception as e:
            self.lbl_status.setText(f"Erro: {str(e)}")

    def _on_reanalyze_selected(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        domain_item = self.table.item(row, 0)
        if not domain_item:
            return
            
        domain = domain_item.text()
        
        try:
            from core.domain_seo_service import DomainSEOService, load_api_key
            api_key = load_api_key()
            if not self.seo_service:
                self.seo_service = DomainSEOService(api_key=api_key)
                
            self.lbl_status.setText(f"Analisando {domain}...")
            
            self.thread = SEOAnalysisThread([domain], self.seo_service)
            self.thread.finished_analysis.connect(self.set_seo_results)
            self.thread.start()
        except Exception as e:
            self.lbl_status.setText(f"Erro: {str(e)}")

    def _on_progress_update(self, current: int, total: int, msg: str):
        self.progress_bar.setValue(current)
        self.lbl_status.setText(msg)

    def _on_search_changed(self, text: str):
        self.search_text = text.strip().lower()
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
        total_pages = max(1, math.ceil(len(self.filtered_data) / self.page_size))
        if self.current_page < total_pages:
            self.current_page += 1
            self._render_current_page()

    def _apply_filter_and_render(self):
        if self.search_text:
            self.filtered_data = [
                d for d in self.domains_data
                if self.search_text in d.get("root_domain", "").lower()
                or self.search_text in d.get("display_name", "").lower()
            ]
        else:
            self.filtered_data = self.domains_data[:]
            
        self._render_current_page()

    def _create_item(self, text: str, bold=False, color=None) -> QTableWidgetItem:
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if bold:
            item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        if color:
            item.setForeground(QColor(color))
        return item

    def _render_current_page(self):
        total_items = len(self.filtered_data)
        total_pages = max(1, math.ceil(total_items / self.page_size))
        
        if self.current_page > total_pages:
            self.current_page = total_pages
        if self.current_page < 1:
            self.current_page = 1

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_items = self.filtered_data[start_idx:end_idx]

        self.lbl_page_info.setText(f"Página {self.current_page} de {total_pages} (Exibindo {len(page_items)} de {total_items} domínios)")
        self.btn_prev_page.setEnabled(self.current_page > 1)
        self.btn_next_page.setEnabled(self.current_page < total_pages)

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(page_items))

        for row, d in enumerate(page_items):
            # 0: Domínio
            domain_str = d.get("root_domain", "")
            item_dom = self._create_item(domain_str, bold=True)
            item_dom.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 0, item_dom)
            
            # 1: DA
            da = d.get("da", "-")
            da_color = None
            if isinstance(da, (int, float)):
                if da >= 50: da_color = "#16A34A" # Verde
                elif da >= 20: da_color = "#D97706" # Laranja
                else: da_color = "#DC2626" # Vermelho
            self.table.setItem(row, 1, self._create_item(da, bold=True, color=da_color))
            
            # 2: PageRank
            self.table.setItem(row, 2, self._create_item(d.get("pagerank", "-")))
            
            # 3: Ref. Domains
            self.table.setItem(row, 3, self._create_item(d.get("ref_domains", "-")))
            
            # 4: Idade
            idade = d.get("age_formatted", d.get("age", "-"))
            self.table.setItem(row, 4, self._create_item(idade))
            
            # 5: Criação
            self.table.setItem(row, 5, self._create_item(d.get("creation_date", "-")))
            
            # 6: Expiração
            self.table.setItem(row, 6, self._create_item(d.get("expiration_date", "-")))
            
            # 7: Registrar
            self.table.setItem(row, 7, self._create_item(d.get("registrar", "-")))
            
            # 8: Snapshots
            self.table.setItem(row, 8, self._create_item(d.get("snapshots", "-")))
            
            # 9: 1º Snapshot
            self.table.setItem(row, 9, self._create_item(d.get("first_snapshot", "-")))
            
            # 10: DNS Records
            dns_count = d.get("dns_records_count", "-")
            self.table.setItem(row, 10, self._create_item(dns_count))
            
            # 11: Email
            has_email = d.get("has_email", False)
            email_text = "✅" if has_email else "❌"
            if "has_email" not in d:
                email_text = "-"
            self.table.setItem(row, 11, self._create_item(email_text))
            
            # 12: Score SEO
            score = d.get("seo_score", "-")
            self.table.setItem(row, 12, self._create_item(score, bold=True))
            
            # 13: Nota
            nota = d.get("grade", "-")
            nota_color = None
            if nota == 'A': nota_color = "#16A34A"
            elif nota == 'B': nota_color = "#2563EB"
            elif nota == 'C': nota_color = "#D97706"
            elif nota == 'D': nota_color = "#DC2626"
            elif nota == 'F': nota_color = "#6B7280"
            self.table.setItem(row, 13, self._create_item(nota, bold=True, color=nota_color))
            
            # 14: Valor Est.
            valor = d.get("est_value", "-")
            if isinstance(valor, (int, float)):
                valor_str = f"${valor:,.0f}"
            else:
                valor_str = str(valor)
            self.table.setItem(row, 14, self._create_item(valor_str, bold=True, color="#16A34A" if valor != "-" else None))
            
            # 15: Vídeos
            v_count = d.get("video_count", 0)
            self.table.setItem(row, 15, self._create_item(v_count))
            
            # 16: Tráfego/Dia
            t_day = d.get("total_daily_views", 0)
            self.table.setItem(row, 16, self._create_item(t_day, color="#D97706" if t_day > 0 else None))
            
            # 17: Ação
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(4)
            
            # Analisar
            btn_analyze = QPushButton("🔍")
            btn_analyze.setToolTip("Analisar este domínio")
            btn_analyze.setObjectName("btn_table_action")
            btn_analyze.setFixedSize(30, 26)
            btn_analyze.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_analyze.clicked.connect(lambda _, dom=domain_str: self._analyze_single(dom))
            action_layout.addWidget(btn_analyze)
            
            # Wayback
            btn_wb = QPushButton("🌐")
            btn_wb.setToolTip("Abrir no Wayback Machine")
            btn_wb.setObjectName("btn_table_action")
            btn_wb.setFixedSize(30, 26)
            btn_wb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_wb.clicked.connect(lambda _, dom=domain_str: self.open_url_requested.emit(f"https://web.archive.org/web/*/{dom}"))
            action_layout.addWidget(btn_wb)
            
            # Registrar
            btn_buy = QPushButton("🛒 Registrar")
            btn_buy.setObjectName("btn_table_buy")
            btn_buy.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            buy_link = d.get("buy_link", f"https://www.namecheap.com/domains/registration/results/?domain={domain_str}")
            btn_buy.clicked.connect(lambda _, lnk=buy_link: self.open_url_requested.emit(lnk))
            action_layout.addWidget(btn_buy)
            
            action_layout.addStretch()
            self.table.setCellWidget(row, 17, action_widget)

        self.table.setSortingEnabled(True)
        
    def _analyze_single(self, domain: str):
        try:
            from core.domain_seo_service import DomainSEOService, load_api_key
            api_key = load_api_key()
            if not self.seo_service:
                self.seo_service = DomainSEOService(api_key=api_key)
                
            self.lbl_status.setText(f"Analisando {domain}...")
            
            self.thread = SEOAnalysisThread([domain], self.seo_service)
            self.thread.finished_analysis.connect(self.set_seo_results)
            self.thread.start()
        except Exception as e:
            self.lbl_status.setText(f"Erro: {str(e)}")

    def _export_csv(self):
        if not self.domains_data:
            self.lbl_status.setText("Nenhum dado para exportar.")
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "Exportar Dados SEO", "", "CSV Files (*.csv)")
        if not path:
            return
            
        try:
            with open(path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(self.COLUMN_HEADERS[:-1]) # exclude 'Ação'
                
                # Write rows
                for d in self.domains_data:
                    writer.writerow([
                        d.get("root_domain", ""),
                        d.get("da", ""),
                        d.get("pagerank", ""),
                        d.get("ref_domains", ""),
                        d.get("age_formatted", d.get("age", "")),
                        d.get("creation_date", ""),
                        d.get("expiration_date", ""),
                        d.get("registrar", ""),
                        d.get("snapshots", ""),
                        d.get("first_snapshot", ""),
                        d.get("dns_records_count", ""),
                        "Sim" if d.get("has_email") else "Não",
                        d.get("seo_score", ""),
                        d.get("grade", ""),
                        d.get("est_value", ""),
                        d.get("video_count", 0),
                        d.get("total_daily_views", 0)
                    ])
            self.lbl_status.setText(f"✅ Exportado para {os.path.basename(path)}")
        except Exception as e:
            self.lbl_status.setText(f"Erro ao exportar: {str(e)}")
