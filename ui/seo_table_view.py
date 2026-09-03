"""
SEO Authority & Backlink Metrics Interactive Table (Métricas SEO: DA / PA / Backlinks).
Dedicated high-precision dashboard for evaluating expired domains with:
- Movable drag-and-drop columns (reordenação interativa de colunas com salvamento de layout).
- Batch and on-demand calculation of DA (Domain Authority), PA (Page Authority),
  Backlinks, Referring Domains, and Spam Score.
- 1-Click deep audit buttons (Moz Open Site Explorer, Ahrefs Backlink Checker, Semrush).
- Batch copy, search filtering, and multi-selection exclusion integration.
"""

import os
import json
import math
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QComboBox, QHeaderView, QMenu, QMessageBox, QApplication,
    QProgressBar, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QThread, QUrl
from PyQt6.QtGui import QColor, QFont, QCursor, QDesktopServices, QAction

from core.seo_metrics_service import SeoMetricsService
from core.metrics_calculator import format_number


class NumericTableWidgetItem(QTableWidgetItem):
    """Sortable table widget item by underlying numerical value."""
    def __init__(self, display_text: str, sort_value: float):
        super().__init__(display_text)
        self.sort_value = sort_value

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self.sort_value < other.sort_value
        return super().__lt__(other)


class SeoWorkerThread(QThread):
    """Background worker to analyze domain metrics without UI latency."""
    domain_analyzed = pyqtSignal(dict)
    all_finished = pyqtSignal()

    def __init__(self, domains: List[Dict[str, Any]], force_refresh: bool = False):
        super().__init__()
        self.domains = domains
        self.force_refresh = force_refresh
        self.service = SeoMetricsService()
        self._is_running = True

    def run(self):
        for d in self.domains:
            if not self._is_running:
                break
            dom_name = d.get("root_domain") or d.get("domain") or d.get("display_name") or ""
            if not dom_name:
                continue
            clean_dom = self.service.clean_domain(dom_name)
            if clean_dom:
                v_cnt = d.get("video_count", 1)
                daily_v = d.get("total_daily_views", 0)
                tot_v = d.get("total_view_count", 0)
                res = self.service.analyze_domain(
                    clean_dom,
                    video_count=v_cnt,
                    total_daily_views=daily_v,
                    total_views=tot_v,
                    force_refresh=self.force_refresh
                )
                self.domain_analyzed.emit(res)
                self.msleep(60) # Smooth pacing
        self.all_finished.emit()

    def stop(self):
        self._is_running = False


class SeoAuthorityTableView(QWidget):
    """
    Dedicated view for SEO Domain Authority (DA), Page Authority (PA),
    Backlink counts, and Referring Domains evaluation.
    """
    buy_domain_requested = pyqtSignal(str)
    domain_excluded_requested = pyqtSignal(str)
    domains_excluded_requested = pyqtSignal(list)
    manage_exclusions_requested = pyqtSignal()

    COLUMN_HEADERS = [
        "Status",
        "Domínio / Link",
        "DA (Autoridade)",
        "PA (Página)",
        "Backlinks",
        "Ref. Domains",
        "Qtd Vídeos",
        "Tráfego / Dia",
        "Spam Score",
        "Última Análise",
        "Ações SEO"
    ]

    LAYOUT_CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".yt_espiao_seo_layout.json")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.raw_seo_data: Dict[str, Dict[str, Any]] = {}
        self.filtered_seo_data: List[Dict[str, Any]] = []
        self.service = SeoMetricsService()

        self.current_page = 1
        self.page_size = 25
        self.search_filter_text = ""
        self.worker: Optional[SeoWorkerThread] = None

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 1. Top Controls Bar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        # Batch Measure Button
        self.btn_measure_all = QPushButton("⚡ Medir Todos os Domínios")
        self.btn_measure_all.setObjectName("btn_table_buy")
        self.btn_measure_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_measure_all.setToolTip("Calcular e auditar DA, PA, Backlinks e RefDomains de todos os domínios disponíveis na tabela")
        self.btn_measure_all.clicked.connect(self._measure_all_domains)
        toolbar.addWidget(self.btn_measure_all)

        # Copy All Domains Button
        self.btn_copy_all = QPushButton("📋 Copiar Todos os Domínios")
        self.btn_copy_all.setObjectName("btn_table_action")
        self.btn_copy_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_copy_all.setToolTip("Copiar lista limpa de todos os domínios disponíveis para a área de transferência (para colar em Moz/Ahrefs)")
        self.btn_copy_all.clicked.connect(self._copy_all_domains)
        toolbar.addWidget(self.btn_copy_all)

        # Manage Exclusions Button
        self.btn_exclusions = QPushButton("🚫 Excluir Domínios...")
        self.btn_exclusions.setObjectName("btn_table_action")
        self.btn_exclusions.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_exclusions.setToolTip("Adicionar domínios à lista de exclusão para nunca mais minerá-los")
        self.btn_exclusions.clicked.connect(self.manage_exclusions_requested.emit)
        toolbar.addWidget(self.btn_exclusions)

        # Reset Column Order Button
        self.btn_reset_cols = QPushButton("🔄 Restaurar Ordem das Colunas")
        self.btn_reset_cols.setObjectName("btn_table_action")
        self.btn_reset_cols.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_reset_cols.setToolTip("Restaurar a disposição original padrão das colunas")
        self.btn_reset_cols.clicked.connect(self._reset_column_order)
        toolbar.addWidget(self.btn_reset_cols)

        # Columns Visibility Menu Button
        self.btn_columns = QPushButton("👁️ Colunas")
        self.btn_columns.setObjectName("btn_table_action")
        self.btn_columns.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_columns.setToolTip("Exibir ou ocultar colunas da tabela")
        self.btn_columns.clicked.connect(self._show_column_menu)
        toolbar.addWidget(self.btn_columns)

        toolbar.addStretch()

        # Search Bar
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("🔍 Filtrar domínio ou termo...")
        self.input_search.setFixedWidth(230)
        self.input_search.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.input_search)

        layout.addLayout(toolbar)

        # Progress bar for batch measurement
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { border: none; background: #1E293B; border-radius: 3px; } QProgressBar::chunk { background: #38BDF8; border-radius: 3px; }")
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # 2. Main SEO Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_table_context_menu)

        # Enable Interactive Drag-and-Drop Column Reordering
        header = self.table.horizontalHeader()
        header.setSectionsMovable(True) # USER REQUIREMENT: Permite arrastar e alterar a posição de qualquer coluna!
        header.setDragEnabled(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.sectionMoved.connect(self._save_column_order)
        header.sectionClicked.connect(self._on_header_section_clicked)

        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Domain stretches
        header.setSectionsClickable(True)

        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setSortingEnabled(False)
        self.table.cellClicked.connect(self._on_cell_clicked)

        layout.addWidget(self.table)

        # 3. Bottom Pagination Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        self.lbl_stats = QLabel("0 domínios disponíveis aguardando análise")
        self.lbl_stats.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 600;")
        bottom_bar.addWidget(self.lbl_stats)

        bottom_bar.addStretch()

        self.lbl_hint_drag = QLabel("💡 Dica: Você pode clicar e arrastar qualquer cabeçalho de coluna para alterar sua posição")
        self.lbl_hint_drag.setStyleSheet("color: #64748B; font-size: 11px; font-style: italic;")
        bottom_bar.addWidget(self.lbl_hint_drag)

        bottom_bar.addStretch()

        self.btn_prev_page = QPushButton("◀ Anterior")
        self.btn_prev_page.setObjectName("btn_pagination")
        self.btn_prev_page.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_prev_page.clicked.connect(self._prev_page)
        bottom_bar.addWidget(self.btn_prev_page)

        self.lbl_page_info = QLabel("Página 1 de 1")
        self.lbl_page_info.setStyleSheet("font-weight: 700; color: #FFFFFF;")
        bottom_bar.addWidget(self.lbl_page_info)

        self.btn_next_page = QPushButton("Próxima ▶")
        self.btn_next_page.setObjectName("btn_pagination")
        self.btn_next_page.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_next_page.clicked.connect(self._next_page)
        bottom_bar.addWidget(self.btn_next_page)

        layout.addLayout(bottom_bar)

        # Restore saved column positions if any
        self._load_column_order()

    def add_domain(self, domain_dict: Dict[str, Any]):
        """Add or update an available domain in the SEO table."""
        dom_name = domain_dict.get("root_domain") or domain_dict.get("display_name") or ""
        clean_dom = self.service.clean_domain(dom_name)
        if not clean_dom:
            return

        # Skip Instagram profiles from domain authority table (domains only)
        if domain_dict.get("is_instagram"):
            return

        v_cnt = domain_dict.get("video_count", 1)
        tot_daily = domain_dict.get("total_daily_views", domain_dict.get("video_metrics", {}).get("daily_views", 0))
        tot_views = domain_dict.get("total_view_count", domain_dict.get("video_metrics", {}).get("view_count", 0))

        if clean_dom in self.raw_seo_data:
            existing = self.raw_seo_data[clean_dom]
            existing["video_count"] = max(existing.get("video_count", 1), v_cnt)
            existing["total_daily_views"] = max(existing.get("total_daily_views", 0), tot_daily)
            existing["total_views"] = max(existing.get("total_views", 0), tot_views)
        else:
            # Generate instant baseline metrics
            analysis = self.service.analyze_domain(
                clean_dom,
                video_count=v_cnt,
                total_daily_views=tot_daily,
                total_views=tot_views,
                force_refresh=False
            )
            self.raw_seo_data[clean_dom] = {
                **domain_dict,
                **analysis,
                "domain": clean_dom
            }

        self._apply_filter_and_render()

    def set_domains(self, domains_list: List[Dict[str, Any]]):
        """Populate table with a list of domains."""
        for d in domains_list:
            if d.get("status") == "Disponível" and not d.get("is_instagram"):
                self.add_domain(d)

    def clear_domains(self):
        """Clear all SEO data."""
        self.raw_seo_data.clear()
        self.filtered_seo_data.clear()
        self._render_current_page()

    def _apply_filter_and_render(self):
        all_items = list(self.raw_seo_data.values())

        if self.search_filter_text:
            t = self.search_filter_text
            filtered = [
                d for d in all_items
                if t in d.get("domain", "").lower()
                or t in d.get("display_name", "").lower()
            ]
        else:
            filtered = all_items

        # Priority Sort: Highest DA first, then Daily Views
        filtered.sort(key=lambda x: (x.get("da", 0), x.get("total_daily_views", 0), x.get("backlinks", 0)), reverse=True)
        self.filtered_seo_data = filtered
        self._render_current_page()

    def _render_current_page(self):
        total_items = len(self.filtered_seo_data)
        total_pages = max(1, math.ceil(total_items / self.page_size))

        if self.current_page > total_pages:
            self.current_page = total_pages
        if self.current_page < 1:
            self.current_page = 1

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_items)
        page_items = self.filtered_seo_data[start_idx:end_idx]

        self.table.setRowCount(len(page_items))

        for row, d in enumerate(page_items):
            # 0. Status Badge
            status_item = QTableWidgetItem("🟢 Disponível")
            status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            status_item.setForeground(QColor("#10B981"))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, status_item)

            # 1. Domain (Interactive Link)
            dom_name = d.get("domain", "")
            domain_item = QTableWidgetItem(f"{dom_name} ↗")
            domain_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
            domain_font.setUnderline(True)
            domain_item.setFont(domain_font)
            domain_item.setForeground(QColor("#38BDF8"))
            domain_item.setToolTip(f"🌐 Clique para abrir '{dom_name}' diretamente no seu navegador")
            domain_item.setData(Qt.ItemDataRole.UserRole, d)
            self.table.setItem(row, 1, domain_item)

            # 2. DA (Domain Authority)
            da_val = d.get("da", 0)
            da_badge = d.get("da_badge", "⚪ --")
            da_item = NumericTableWidgetItem(f"{da_val}  ({da_badge})", da_val)
            da_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            da_item.setForeground(QColor(d.get("da_color", "#38BDF8")))
            da_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            da_item.setToolTip(f"Domain Authority (DA): {da_val}/100\n{da_badge}")
            self.table.setItem(row, 2, da_item)

            # 3. PA (Page Authority)
            pa_val = d.get("pa", 0)
            pa_item = NumericTableWidgetItem(str(pa_val), pa_val)
            pa_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            pa_item.setForeground(QColor("#A855F7"))
            pa_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            pa_item.setToolTip(f"Page Authority (PA): {pa_val}/100")
            self.table.setItem(row, 3, pa_item)

            # 4. Backlinks
            bl_val = d.get("backlinks", 0)
            bl_fmt = d.get("backlinks_formatted", format_number(bl_val))
            bl_item = NumericTableWidgetItem(bl_fmt, bl_val)
            bl_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            bl_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            bl_item.setToolTip(f"Total estimado de backlinks: {bl_val:,}")
            self.table.setItem(row, 4, bl_item)

            # 5. Ref. Domains
            ref_val = d.get("ref_domains", 0)
            ref_fmt = d.get("ref_domains_formatted", format_number(ref_val))
            ref_item = NumericTableWidgetItem(ref_fmt, ref_val)
            ref_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            ref_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            ref_item.setToolTip(f"Domínios únicos de referência (RefDomains): {ref_val:,}")
            self.table.setItem(row, 5, ref_item)

            # 6. Qtd Vídeos
            v_cnt = d.get("video_count", 1)
            v_item = NumericTableWidgetItem(f"🎬 {v_cnt}", v_cnt)
            v_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            v_item.setFont(QFont("Segoe UI", 9))
            self.table.setItem(row, 6, v_item)

            # 7. Tráfego / Dia
            daily = d.get("total_daily_views", 0)
            daily_item = NumericTableWidgetItem(f"🔥 {format_number(daily)}/dia", daily)
            daily_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            daily_item.setForeground(QColor("#10B981"))
            daily_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 7, daily_item)

            # 8. Spam Score
            spam = d.get("spam_score", 1)
            spam_badge = d.get("spam_badge", "🟢 Baixo")
            spam_item = NumericTableWidgetItem(f"{spam}% ({spam_badge})", spam)
            spam_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            spam_item.setForeground(QColor(d.get("spam_color", "#10B981")))
            spam_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 8, spam_item)

            # 9. Última Análise
            analyzed_item = QTableWidgetItem(d.get("analyzed_at", "--"))
            analyzed_item.setFont(QFont("Segoe UI", 8))
            analyzed_item.setForeground(QColor("#64748B"))
            analyzed_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 9, analyzed_item)

            # 10. Action Buttons Widget
            actions_widget = QWidget()
            act_layout = QHBoxLayout(actions_widget)
            act_layout.setContentsMargins(4, 2, 4, 2)
            act_layout.setSpacing(6)
            act_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Single Audit
            btn_audit = QPushButton("⚡ Medir")
            btn_audit.setObjectName("btn_table_action")
            btn_audit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_audit.setToolTip(f"Recalcular métricas SEO para '{dom_name}'")
            btn_audit.clicked.connect(lambda _, dm=dom_name: self._measure_single_domain(dm))
            act_layout.addWidget(btn_audit)

            # Moz Link
            btn_moz = QPushButton("🌐 Moz ↗")
            btn_moz.setObjectName("btn_table_action")
            btn_moz.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_moz.setToolTip(f"Abrir análise completa no Moz Domain Analysis para '{dom_name}'")
            btn_moz.clicked.connect(lambda _, u=d.get("moz_url"): QDesktopServices.openUrl(QUrl(u)))
            act_layout.addWidget(btn_moz)

            # Ahrefs Link
            btn_ahrefs = QPushButton("🔍 Ahrefs ↗")
            btn_ahrefs.setObjectName("btn_table_action")
            btn_ahrefs.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_ahrefs.setToolTip(f"Checar backlinks no Ahrefs Backlink Checker para '{dom_name}'")
            btn_ahrefs.clicked.connect(lambda _, u=d.get("ahrefs_url"): QDesktopServices.openUrl(QUrl(u)))
            act_layout.addWidget(btn_ahrefs)

            # Buy / Claim
            btn_buy = QPushButton("🛒 Registrar ↗")
            btn_buy.setObjectName("btn_table_buy")
            btn_buy.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_buy.setToolTip(f"Abrir no registrador oficial para comprar '{dom_name}'")
            btn_buy.clicked.connect(lambda _, u=d.get("buy_url"): QDesktopServices.openUrl(QUrl(u)))
            act_layout.addWidget(btn_buy)

            self.table.setCellWidget(row, 10, actions_widget)

        # Update labels
        self.lbl_stats.setText(f"Mostrando {len(page_items)} de {total_items} domínios disponíveis analisados")
        self.lbl_page_info.setText(f"Página {self.current_page} de {total_pages}")
        self.btn_prev_page.setEnabled(self.current_page > 1)
        self.btn_next_page.setEnabled(self.current_page < total_pages)

    # ----------------------------------------------------
    # Column Reordering & Layout Persistence (USER REQUIREMENT)
    # ----------------------------------------------------
    def _save_column_order(self):
        """Save customized drag-and-drop column order to persistent disk file."""
        try:
            header = self.table.horizontalHeader()
            visual_indices = [header.visualIndex(i) for i in range(len(self.COLUMN_HEADERS))]
            with open(self.LAYOUT_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"column_order": visual_indices}, f)
        except Exception:
            pass

    def _load_column_order(self):
        """Restore user's preferred column arrangement."""
        if not os.path.exists(self.LAYOUT_CONFIG_FILE):
            return
        try:
            with open(self.LAYOUT_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            order = cfg.get("column_order", [])
            header = self.table.horizontalHeader()
            if len(order) == len(self.COLUMN_HEADERS):
                # Apply saved visual positions
                for logical_col, target_visual in enumerate(order):
                    current_visual = header.visualIndex(logical_col)
                    if current_visual != target_visual:
                        header.moveSection(current_visual, target_visual)
        except Exception:
            pass

    def _reset_column_order(self, silent: bool = False):
        """Reset column arrangement to standard default layout."""
        header = self.table.horizontalHeader()
        for i in range(len(self.COLUMN_HEADERS)):
            current_visual = header.visualIndex(i)
            if current_visual != i:
                header.moveSection(current_visual, i)
        if os.path.exists(self.LAYOUT_CONFIG_FILE):
            try:
                os.remove(self.LAYOUT_CONFIG_FILE)
            except Exception:
                pass
        if not silent:
            QMessageBox.information(self, "Ordem Restaurada", "A disposição das colunas foi restaurada para a ordem padrão!")

    # ----------------------------------------------------
    # Cell Clicks & Actions
    # ----------------------------------------------------
    def _on_cell_clicked(self, row: int, col: int):
        header = self.table.horizontalHeader()
        logical_col = header.logicalIndex(col)
        # Column 1 is Domain link
        if logical_col == 1:
            start_idx = (self.current_page - 1) * self.page_size
            idx = start_idx + row
            if 0 <= idx < len(self.filtered_seo_data):
                d = self.filtered_seo_data[idx]
                dom = d.get("domain")
                if dom:
                    url = f"https://{dom}"
                    QDesktopServices.openUrl(QUrl(url))

    def _measure_single_domain(self, domain: str):
        if domain in self.raw_seo_data:
            item = self.raw_seo_data[domain]
            res = self.service.analyze_domain(
                domain,
                video_count=item.get("video_count", 1),
                total_daily_views=item.get("total_daily_views", 0),
                total_views=item.get("total_views", 0),
                force_refresh=True
            )
            self.raw_seo_data[domain].update(res)
            self._apply_filter_and_render()
            QMessageBox.information(self, "Métricas Atualizadas", f"Métricas de '{domain}' atualizadas com sucesso:\n\n• DA: {res['da']}\n• PA: {res['pa']}\n• Backlinks: {res['backlinks_formatted']}\n• RefDomains: {res['ref_domains_formatted']}")

    def _measure_all_domains(self):
        if not self.raw_seo_data:
            QMessageBox.information(self, "Sem Domínios", "Nenhum domínio disponível para análise no momento.")
            return

        self.btn_measure_all.setEnabled(False)
        self.progress_bar.show()
        self.progress_bar.setValue(0)

        domains_to_analyze = list(self.raw_seo_data.values())
        self.worker = SeoWorkerThread(domains_to_analyze, force_refresh=True)
        self.worker.domain_analyzed.connect(self._on_worker_domain_analyzed)
        self.worker.all_finished.connect(self._on_worker_finished)
        self.worker.start()

    def _on_worker_domain_analyzed(self, res: Dict[str, Any]):
        dom = res.get("domain")
        if dom and dom in self.raw_seo_data:
            self.raw_seo_data[dom].update(res)
            self._apply_filter_and_render()

    def _on_worker_finished(self):
        self.progress_bar.hide()
        self.btn_measure_all.setEnabled(True)
        QMessageBox.information(self, "Análise Concluída", f"Todas as métricas de autoridade (DA, PA, Backlinks) foram calculadas com sucesso para os {len(self.raw_seo_data)} domínios!")

    def _copy_all_domains(self):
        domains = [d.get("domain") for d in self.filtered_seo_data if d.get("domain")]
        if not domains:
            QMessageBox.information(self, "Aviso", "Não há domínios na lista para copiar.")
            return

        text = "\n".join(domains)
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copiado", f"{len(domains)} domínios disponíveis copiados para a área de transferência!\n\nVocê já pode colar na sua ferramenta favorita (Moz, Ahrefs, Semrush, Excel).")

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

    def _on_header_section_clicked(self, logical_index: int):
        pass

    def _on_table_context_menu(self, pos: QPoint):
        item = self.table.itemAt(pos)
        if not item:
            return
        row = item.row()
        start_idx = (self.current_page - 1) * self.page_size
        idx = start_idx + row
        if idx < 0 or idx >= len(self.filtered_seo_data):
            return

        d = self.filtered_seo_data[idx]
        domain = d.get("domain", "")

        menu = QMenu(self)
        menu.setStyleSheet("QMenu { padding: 6px; font-weight: 600; }")

        act_copy = QAction(f"📋 Copiar '{domain}'", menu)
        act_copy.triggered.connect(lambda: QApplication.clipboard().setText(domain))
        menu.addAction(act_copy)

        act_measure = QAction(f"⚡ Atualizar Métricas SEO (DA / PA)", menu)
        act_measure.triggered.connect(lambda: self._measure_single_domain(domain))
        menu.addAction(act_measure)

        menu.addSeparator()

        act_moz = QAction("🌐 Abrir no Moz Domain Analysis ↗", menu)
        act_moz.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(d.get("moz_url"))))
        menu.addAction(act_moz)

        act_ahrefs = QAction("🔍 Abrir no Ahrefs Backlink Checker ↗", menu)
        act_ahrefs.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(d.get("ahrefs_url"))))
        menu.addAction(act_ahrefs)

        act_buy = QAction("🛒 Registrar Domínio Oficialmente ↗", menu)
        act_buy.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(d.get("buy_url"))))
        menu.addAction(act_buy)

        menu.addSeparator()

        act_exclude = QAction(f"🚫 Adicionar '{domain}' à Lista de Exclusão", menu)
        act_exclude.triggered.connect(lambda: self._exclude_domain(domain))
        menu.addAction(act_exclude)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _exclude_domain(self, domain: str):
        from core.domain_extractor import add_to_exclusion_list
        add_to_exclusion_list([domain])
        if domain in self.raw_seo_data:
            del self.raw_seo_data[domain]
        self._apply_filter_and_render()
        self.domain_excluded_requested.emit(domain)

    def _on_search_changed(self, text: str):
        self.search_filter_text = text.strip().lower()
        self.current_page = 1
        self._apply_filter_and_render()

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_current_page()

    def _next_page(self):
        total_pages = max(1, math.ceil(len(self.filtered_seo_data) / self.page_size))
        if self.current_page < total_pages:
            self.current_page += 1
            self._render_current_page()
