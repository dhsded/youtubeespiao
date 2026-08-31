"""
Hunter Panel (Painel Espião) - Core mining, domain & Instagram analysis interface.
Features:
- Prioritization by View Count (Vídeos Mais Vistos).
- Date & Year Range Filters (Global / Sem ano definido, Ano Específico, Intervalo de Anos, Recentes).
- Global Multi-Language Search (12+ languages translated automatically).
- Clean Dark/Light theme adaptability.
"""

import os
import time
from typing import List, Dict, Any, Optional, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QSpinBox, QProgressBar,
    QTabWidget, QPlainTextEdit, QFrame, QFileDialog, QMessageBox,
    QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QCursor

from core.youtube_crawler import YouTubeCrawler
from core.translator import get_language_list, expand_queries_for_language
from core.metrics_calculator import format_number
from core.exporter import DataExporter
from ui.video_table_model import VideoTableView, DomainTableView
from ui.settings_tab import APP_SETTINGS

class CrawlerThread(QThread):
    """Background worker thread supporting Multi-Language, Date Filters, and Global search."""
    video_found = pyqtSignal(dict)
    domain_found = pyqtSignal(dict)
    progress_updated = pyqtSignal(int, int, str)
    finished_crawl = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        keywords: List[str],
        selected_lang: str,
        date_filter: str,
        year_range: Optional[Tuple[int, int]],
        max_videos: int,
        sort_by: str = "view_count",
        loop_24h: bool = False,
        parent=None
    ):
        super().__init__(parent)
        self.keywords = [k.strip() for k in keywords if k.strip()]
        self.selected_lang = selected_lang
        self.date_filter = date_filter
        self.year_range = year_range
        self.max_videos = max_videos
        self.sort_by = sort_by
        self.loop_24h = loop_24h
        self.crawler = YouTubeCrawler(
            proxy_url=APP_SETTINGS.get("proxy_url"),
            min_delay=APP_SETTINGS.get("min_delay", 1.0),
            max_delay=APP_SETTINGS.get("max_delay", 2.5)
        )
        self._is_interrupted = False
        self._is_paused = False

    def pause(self):
        self._is_paused = True

    def resume(self):
        self._is_paused = False

    def stop(self):
        self._is_interrupted = True
        self._is_paused = False
        if self.crawler:
            self.crawler.stop()

    def _wait_if_paused(self):
        while self._is_paused:
            if self._is_interrupted:
                break
            time.sleep(0.3)

    def run(self):
        try:
            total_vids_count = 0
            total_doms_count = 0
            total_avail_count = 0
            cycle = 1

            while True:
                for kw in self.keywords:
                    if self._is_interrupted:
                        break
                    
                    lang_tasks = expand_queries_for_language(kw, self.selected_lang)

                    for task in lang_tasks:
                        if self._is_interrupted:
                            break

                        self._wait_if_paused()
                        
                        flag = task.get("flag", "🌐")
                        lang_name = task.get("lang_name", "")
                        query = task.get("query", kw)
                        hl = task.get("hl", "pt")
                        gl = task.get("gl", "BR")

                        task_label = f"{flag} {lang_name} ('{query}')"
                        self.progress_updated.emit(0, self.max_videos, f"[Ciclo {cycle}] {task_label}...")

                        def on_prog_wrapped(cur, tot, msg):
                            self._wait_if_paused()
                            self.progress_updated.emit(cur, tot, f"[Ciclo {cycle}] {msg}")

                        results = self.crawler.process_keyword(
                            keyword=query,
                            max_videos=self.max_videos,
                            sort_by=self.sort_by,
                            date_filter=self.date_filter,
                            year_range=self.year_range,
                            hl=hl,
                            gl=gl,
                            display_label=f"{flag} {lang_name}",
                            on_video_processed=lambda v: self.video_found.emit(v),
                            on_domain_found=lambda d: self.domain_found.emit(d),
                            on_progress=on_prog_wrapped
                        )

                        total_vids_count += results.get("total_videos", 0)
                        total_doms_count += results.get("total_domains", 0)
                        total_avail_count += results.get("available_domains", 0)

                        if not self._is_interrupted and len(lang_tasks) > 1:
                            time.sleep(2.0)

                    if not self._is_interrupted and len(self.keywords) > 1:
                        time.sleep(2.5)

                if not self.loop_24h or self._is_interrupted:
                    break

                cycle += 1
                self.progress_updated.emit(100, 100, f"Ciclo {cycle-1} concluído. Aguardando 15s antes do próximo ciclo...")
                for _ in range(15):
                    if self._is_interrupted:
                        break
                    self._wait_if_paused()
                    time.sleep(1.0)

            self.finished_crawl.emit({
                "total_videos": total_vids_count,
                "total_domains": total_doms_count,
                "available_domains": total_avail_count
            })

        except Exception as e:
            self.error_occurred.emit(str(e))


class HunterTab(QWidget):
    """Main Hunting Dashboard with Multi-Language, Date Filters, and Theme Compatibility."""
    navigate_url_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.crawler_thread: Optional[CrawlerThread] = None
        self.is_paused = False
        
        self.all_videos: List[Dict[str, Any]] = []
        self.all_domains: List[Dict[str, Any]] = []

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(12)

        # 1. Top Stat Cards
        main_layout.addLayout(self._create_stats_header())

        # 2. Controls Panel Container
        main_layout.addWidget(self._create_controls_panel())

        # 3. Status Message & Progress Bar
        status_bar_layout = QVBoxLayout()
        status_bar_layout.setSpacing(4)

        self.status_label = QLabel("Pronto para iniciar a mineração. Digite termos e clique em 'Iniciar Busca'.")
        self.status_label.setObjectName("status_label")
        status_bar_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        status_bar_layout.addWidget(self.progress_bar)

        main_layout.addLayout(status_bar_layout)

        # 4. Tabbed Results View
        self.results_tabs = QTabWidget()
        self.results_tabs.setObjectName("results_tabs")

        # Tab 1: Mined Videos
        self.video_table = VideoTableView()
        self.video_table.open_video_requested.connect(self._on_navigate_requested)
        self.results_tabs.addTab(self.video_table, "🏆 Vídeos Minerados & Métricas de Tráfego")

        # Tab 2: Discovered Domains & Instagrams
        domain_container = QWidget()
        domain_layout = QVBoxLayout(domain_container)
        domain_layout.setContentsMargins(8, 10, 8, 8)
        domain_layout.setSpacing(10)

        self.domain_table = DomainTableView()
        self.domain_table.buy_domain_requested.connect(self._on_navigate_requested)
        self.domain_table.open_video_requested.connect(self._on_navigate_requested)
        domain_layout.addWidget(self.domain_table)

        self.results_tabs.addTab(domain_container, "💎 Domínios & Instagrams Expirados")

        # Tab 3: Real-time logs
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("log_view")
        self.log_view.setReadOnly(True)
        self.results_tabs.addTab(self.log_view, "📜 Logs em Tempo Real")

        main_layout.addWidget(self.results_tabs, 1)

        # 5. Bottom Toolbar
        main_layout.addLayout(self._create_bottom_toolbar())

    def _create_stats_header(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)

        self.card_videos, self.val_videos = self._build_stat_card("VÍDEOS MINERADOS", "0", "stat_card", "stat_val_videos")
        self.card_views, self.val_views = self._build_stat_card("VIEWS TOTAIS", "0", "stat_card", "stat_val_views")
        self.card_domains, self.val_domains = self._build_stat_card("DOMÍNIOS / IGs", "0", "stat_card", "stat_val_domains")
        self.card_avail, self.val_avail = self._build_stat_card("🟢 DISPONÍVEIS P/ COMPRA", "0", "stat_card_available", "stat_val_available")

        layout.addWidget(self.card_videos)
        layout.addWidget(self.card_views)
        layout.addWidget(self.card_domains)
        layout.addWidget(self.card_avail)
        return layout

    def _build_stat_card(self, title: str, init_val: str, frame_id: str, val_id: str) -> (QFrame, QLabel):
        frame = QFrame()
        frame.setObjectName(frame_id)
        f_layout = QVBoxLayout(frame)
        f_layout.setContentsMargins(18, 12, 18, 12)
        f_layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("stat_title")
        
        lbl_val = QLabel(init_val)
        lbl_val.setObjectName(val_id)

        f_layout.addWidget(lbl_title)
        f_layout.addWidget(lbl_val)
        return frame, lbl_val

    def _create_controls_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("controls_container")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(14, 12, 14, 12)
        panel_layout.setSpacing(10)

        # Row 1: Search Inputs, Language, Date Filter, Custom Years, Sort
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.input_keyword = QLineEdit()
        self.input_keyword.setPlaceholderText("Digite termos de busca (ex: GTA, dropshipping, marketing digital)...")
        self.input_keyword.setMinimumWidth(220)
        self.input_keyword.returnPressed.connect(self._on_start_or_resume)
        row1.addWidget(self.input_keyword, 3)

        # Language Selector
        self.combo_lang = QComboBox()
        for l in get_language_list():
            self.combo_lang.addItem(l["label"], l["code"])
        self.combo_lang.setMinimumWidth(180)
        self.combo_lang.setMaximumWidth(230)
        row1.addWidget(self.combo_lang)

        # Date & Year Range Selector
        self.combo_date = QComboBox()
        self.combo_date.addItem("🌐 Todas as Datas (Global)", "all_time")
        self.combo_date.addItem("📅 Ano de 2026 (Atual)", "2026")
        self.combo_date.addItem("📆 Ano de 2025", "2025")
        self.combo_date.addItem("📆 Ano de 2024", "2024")
        self.combo_date.addItem("📆 Ano de 2023", "2023")
        self.combo_date.addItem("📆 Ano de 2022", "2022")
        self.combo_date.addItem("📆 Ano de 2021", "2021")
        self.combo_date.addItem("📆 Ano de 2020", "2020")
        self.combo_date.addItem("📆 Ano de 2019", "2019")
        self.combo_date.addItem("📆 Ano de 2018", "2018")
        self.combo_date.addItem("🎯 Intervalo de Anos...", "custom_range")
        self.combo_date.addItem("⏱️ Este Mês", "this_month")
        self.combo_date.addItem("🗓️ Esta Semana", "this_week")
        self.combo_date.addItem("🔥 Últimas 24 Horas", "today")
        self.combo_date.setMinimumWidth(190)
        self.combo_date.setMaximumWidth(240)
        self.combo_date.currentIndexChanged.connect(self._on_date_filter_changed)
        row1.addWidget(self.combo_date)

        # Custom Year Range Controls (Spacious 95px width with centered text)
        self.widget_custom_years = QWidget()
        custom_yr_layout = QHBoxLayout(self.widget_custom_years)
        custom_yr_layout.setContentsMargins(2, 0, 2, 0)
        custom_yr_layout.setSpacing(4)
        
        lbl_de = QLabel("De:")
        lbl_de.setStyleSheet("font-weight: bold;")
        custom_yr_layout.addWidget(lbl_de)
        
        self.spin_year_start = QSpinBox()
        self.spin_year_start.setRange(2006, 2026)
        self.spin_year_start.setValue(2020)
        self.spin_year_start.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_year_start.setFixedWidth(95)
        custom_yr_layout.addWidget(self.spin_year_start)
        
        lbl_ate = QLabel("Até:")
        lbl_ate.setStyleSheet("font-weight: bold;")
        custom_yr_layout.addWidget(lbl_ate)
        
        self.spin_year_end = QSpinBox()
        self.spin_year_end.setRange(2006, 2026)
        self.spin_year_end.setValue(2026)
        self.spin_year_end.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_year_end.setFixedWidth(95)
        custom_yr_layout.addWidget(self.spin_year_end)
        
        self.widget_custom_years.setVisible(False)
        row1.addWidget(self.widget_custom_years)

        # Sort Selection (Default: Mais Vistos / view_count)
        self.combo_sort = QComboBox()
        self.combo_sort.addItem("🔥 Mais Vistos (Padrão)", "view_count")
        self.combo_sort.addItem("🎯 Relevância", "relevance")
        self.combo_sort.addItem("📅 Mais Recentes", "upload_date")
        self.combo_sort.setMinimumWidth(180)
        self.combo_sort.setMaximumWidth(220)
        row1.addWidget(self.combo_sort)

        panel_layout.addLayout(row1)

        # Row 2: Limits, Checkboxes, Action Buttons
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        lbl_lim = QLabel("Limite de Vídeos:")
        lbl_lim.setStyleSheet("font-weight: 600;")
        row2.addWidget(lbl_lim)

        self.spin_max = QSpinBox()
        self.spin_max.setRange(5, 10000)
        self.spin_max.setValue(50)
        self.spin_max.setSingleStep(25)
        self.spin_max.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_max.setFixedWidth(90)
        row2.addWidget(self.spin_max)

        self.chk_unlimited = QCheckBox("♾️ Máximo")
        self.chk_unlimited.setToolTip("Busca o maior número possível de vídeos retornados.")
        self.chk_unlimited.toggled.connect(lambda checked: self.spin_max.setEnabled(not checked))
        row2.addWidget(self.chk_unlimited)

        self.chk_mode_24h = QCheckBox("🔄 Modo 24h")
        self.chk_mode_24h.setToolTip("Executa em ciclos contínuos com pausas seguras anti-bloqueio.")
        row2.addWidget(self.chk_mode_24h)

        row2.addSpacing(15)

        # 1. INICIAR BUTTON
        self.btn_start = QPushButton("🚀 Iniciar Busca")
        self.btn_start.setObjectName("btn_start_action")
        self.btn_start.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_start.clicked.connect(self._on_start_or_resume)
        row2.addWidget(self.btn_start)

        # 2. PAUSAR BUTTON
        self.btn_pause = QPushButton("⏸️ Pausar")
        self.btn_pause.setObjectName("btn_pause_action")
        self.btn_pause.setEnabled(False)
        self.btn_pause.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_pause.clicked.connect(self._on_toggle_pause)
        row2.addWidget(self.btn_pause)

        # 3. PARAR BUTTON
        self.btn_stop = QPushButton("⏹ Parar")
        self.btn_stop.setObjectName("btn_stop_action")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_stop.clicked.connect(self._on_stop_completely)
        row2.addWidget(self.btn_stop)

        row2.addStretch()
        panel_layout.addLayout(row2)

        return panel

    def _on_date_filter_changed(self):
        code = self.combo_date.currentData()
        self.widget_custom_years.setVisible(code == "custom_range")

    def _create_bottom_toolbar(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.btn_export_pdf = QPushButton("📑 Exportar PDF")
        self.btn_export_pdf.setObjectName("btn_success")
        self.btn_export_pdf.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export_pdf.clicked.connect(self._export_pdf)
        layout.addWidget(self.btn_export_pdf)

        self.btn_export_excel = QPushButton("📊 Exportar Excel (.xlsx)")
        self.btn_export_excel.setObjectName("btn_success")
        self.btn_export_excel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export_excel.clicked.connect(self._export_excel)
        layout.addWidget(self.btn_export_excel)

        self.btn_export_csv = QPushButton("📄 Exportar CSV")
        self.btn_export_csv.setObjectName("btn_success")
        self.btn_export_csv.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export_csv.clicked.connect(self._export_csv)
        layout.addWidget(self.btn_export_csv)

        self.btn_export_json = QPushButton("📋 Exportar JSON")
        self.btn_export_json.setObjectName("btn_success")
        self.btn_export_json.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export_json.clicked.connect(self._export_json)
        layout.addWidget(self.btn_export_json)

        layout.addStretch()

        self.btn_clear = QPushButton("🗑️ Limpar Resultados")
        self.btn_clear.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_clear.clicked.connect(self._clear_results)
        layout.addWidget(self.btn_clear)

        return layout

    def _on_start_or_resume(self):
        if self.is_paused and self.crawler_thread and self.crawler_thread.isRunning():
            self.is_paused = False
            self.crawler_thread.resume()
            self.btn_start.setText("🚀 Mineração Ativa")
            self.btn_start.setEnabled(False)
            self.btn_pause.setText("⏸️ Pausar")
            self.status_label.setText("Mineração retomada...")
            self._append_log("▶ Mineração retomada.")
            return

        raw_text = self.input_keyword.text().strip()
        if not raw_text:
            QMessageBox.warning(self, "Atenção", "Por favor, digite pelo menos uma palavra-chave para minerar.")
            return

        keywords = [k.strip() for k in raw_text.replace("\n", ",").replace(";", ",").split(",") if k.strip()]
        selected_lang = self.combo_lang.currentData()
        date_filter = self.combo_date.currentData()
        year_range = (self.spin_year_start.value(), self.spin_year_end.value()) if date_filter == "custom_range" else None
        max_vids = 5000 if self.chk_unlimited.isChecked() else self.spin_max.value()
        sort_by = self.combo_sort.currentData()
        loop_24h = self.chk_mode_24h.isChecked()

        self.is_paused = False
        self.btn_start.setEnabled(False)
        self.btn_start.setText("🚀 Mineração Ativa")
        self.btn_pause.setEnabled(True)
        self.btn_pause.setText("⏸️ Pausar")
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Iniciando varredura por mais vistos ({self.combo_date.currentText()})...")
        self._append_log(f"--- 🚀 Mineração Iniciada ({len(keywords)} termos | Período: {self.combo_date.currentText()} | Ordenação: {self.combo_sort.currentText()}) ---")

        self.crawler_thread = CrawlerThread(
            keywords=keywords,
            selected_lang=selected_lang,
            date_filter=date_filter,
            year_range=year_range,
            max_videos=max_vids,
            sort_by=sort_by,
            loop_24h=loop_24h,
            parent=self
        )
        self.crawler_thread.video_found.connect(self._on_video_found)
        self.crawler_thread.domain_found.connect(self._on_domain_found)
        self.crawler_thread.progress_updated.connect(self._on_progress_updated)
        self.crawler_thread.finished_crawl.connect(self._on_finished_crawl)
        self.crawler_thread.error_occurred.connect(self._on_error_occurred)
        self.crawler_thread.start()

    def _on_toggle_pause(self):
        if not self.crawler_thread or not self.crawler_thread.isRunning():
            return

        if not self.is_paused:
            self.is_paused = True
            self.crawler_thread.pause()
            self.btn_pause.setText("▶ Retomar")
            self.btn_start.setEnabled(True)
            self.btn_start.setText("▶ Retomar Busca")
            self.status_label.setText("⏸️ Mineração Pausada. Clique em 'Retomar' para prosseguir.")
            self._append_log("⏸️ Mineração pausada pelo usuário.")
        else:
            self.is_paused = False
            self.crawler_thread.resume()
            self.btn_pause.setText("⏸️ Pausar")
            self.btn_start.setEnabled(False)
            self.btn_start.setText("🚀 Mineração Ativa")
            self.status_label.setText("Mineração retomada...")
            self._append_log("▶ Mineração retomada.")

    def _on_stop_completely(self):
        if self.crawler_thread and self.crawler_thread.isRunning():
            self.status_label.setText("Encerrando totalmente a varredura...")
            self._append_log("⏹️ Encerrando processo totalmente...")
            self.crawler_thread.stop()
            self.is_paused = False
            self.btn_start.setEnabled(True)
            self.btn_start.setText("🚀 Iniciar Busca")
            self.btn_pause.setEnabled(False)
            self.btn_stop.setEnabled(False)

    def _on_video_found(self, video_dict: Dict[str, Any]):
        v_id = video_dict.get("id")
        if any(v.get("id") == v_id for v in self.all_videos):
            return
        self.all_videos.append(video_dict)
        # Always prioritize highest views count first
        self.all_videos.sort(key=lambda x: x["metrics"]["view_count"], reverse=True)
        self.video_table.set_videos(self.all_videos)
        self._update_stat_cards()
        self._append_log(f"📹 Vídeo minerado: {video_dict['title'][:45]}... ({video_dict['metrics']['view_count_formatted']} views)")

    def _on_domain_found(self, domain_dict: Dict[str, Any]):
        d_root = domain_dict.get("root_domain")
        v_id = domain_dict.get("video_id")
        if any(d.get("root_domain") == d_root and d.get("video_id") == v_id for d in self.all_domains):
            return
        self.all_domains.append(domain_dict)
        self.domain_table.set_domains(self.all_domains)
        self._update_stat_cards()
        badge = domain_dict.get("badge_icon", "")
        status = domain_dict.get("status", "")
        name = domain_dict.get("display_name") or domain_dict.get("root_domain", "")
        self._append_log(f"  {badge} {name} -> {status} ({domain_dict.get('source_location')})")

    def _on_progress_updated(self, current: int, total: int, message: str):
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
        self.status_label.setText(message)

    def _on_finished_crawl(self, summary: Dict[str, Any]):
        self.btn_start.setEnabled(True)
        self.btn_start.setText("🚀 Iniciar Busca")
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.is_paused = False
        self.progress_bar.setValue(100)
        self.status_label.setText(f"Varredura concluída! {len(self.all_videos)} vídeos e {len(self.all_domains)} oportunidades analisadas.")
        self._append_log(f"✅ Mineração finalizada! Disponíveis: {summary.get('available_domains', 0)} | Total: {summary.get('total_domains', 0)}")
        QMessageBox.information(
            self,
            "Mineração Concluída",
            f"Varredura finalizada com sucesso!\n\n"
            f"• Vídeos analisados: {len(self.all_videos)}\n"
            f"• Domínios / Contas IG encontradas: {len(self.all_domains)}\n"
            f"• Oportunidades DISPONÍVEIS para compra/claim: {summary.get('available_domains', 0)}"
        )

    def _on_error_occurred(self, err_msg: str):
        self.btn_start.setEnabled(True)
        self.btn_start.setText("🚀 Iniciar Busca")
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.is_paused = False
        self.status_label.setText(f"Erro: {err_msg}")
        self._append_log(f"❌ Erro na varredura: {err_msg}")
        QMessageBox.critical(self, "Erro na Varredura", f"Ocorreu um erro:\n{err_msg}")

    def _update_stat_cards(self):
        total_vids = len(self.all_videos)
        total_views = sum(v.get("metrics", {}).get("view_count", 0) for v in self.all_videos)
        total_doms = len(self.all_domains)
        avail_doms = sum(1 for d in self.all_domains if d.get("status") == "Disponível")

        self.val_videos.setText(str(total_vids))
        self.val_views.setText(format_number(total_views))
        self.val_domains.setText(str(total_doms))
        self.val_avail.setText(str(avail_doms))

    def _append_log(self, text: str):
        self.log_view.appendPlainText(text)

    def _on_navigate_requested(self, url: str):
        self.navigate_url_requested.emit(url)

    def _clear_results(self):
        self.all_videos.clear()
        self.all_domains.clear()
        self.video_table.set_videos([])
        self.domain_table.set_domains([])
        if self.crawler_thread and self.crawler_thread.crawler:
            self.crawler_thread.crawler.clear_seen_videos()
        self.log_view.clear()
        self.progress_bar.setValue(0)
        self._update_stat_cards()
        self.status_label.setText("Resultados limpos.")

    def _export_pdf(self):
        if not self.all_videos and not self.all_domains:
            QMessageBox.warning(self, "Exportar", "Não há dados minerados para exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Relatório PDF", "Relatorio_YouTube_Espiao.pdf", "PDF Files (*.pdf)")
        if path:
            try:
                DataExporter.export_to_pdf(path, self.all_domains, self.all_videos)
                QMessageBox.information(self, "Sucesso", f"Relatório PDF salvo com sucesso em:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro na Exportação", str(e))

    def _export_excel(self):
        if not self.all_videos and not self.all_domains:
            QMessageBox.warning(self, "Exportar", "Não há dados minerados para exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Relatório Excel", "Relatorio_YouTube_Espiao.xlsx", "Excel Files (*.xlsx)")
        if path:
            try:
                DataExporter.export_to_excel(path, self.all_domains, self.all_videos)
                QMessageBox.information(self, "Sucesso", f"Relatório salvo com sucesso em:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro na Exportação", str(e))

    def _export_csv(self):
        if not self.all_domains:
            QMessageBox.warning(self, "Exportar", "Não há registros encontrados para exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Oportunidades CSV", "Oportunidades_Expiradas.csv", "CSV Files (*.csv)")
        if path:
            try:
                DataExporter.export_to_csv(path, self.all_domains)
                QMessageBox.information(self, "Sucesso", f"Arquivo CSV salvo com sucesso em:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro na Exportação", str(e))

    def _export_json(self):
        if not self.all_videos and not self.all_domains:
            QMessageBox.warning(self, "Exportar", "Não há dados para exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Dados JSON", "Dados_Mineracao.json", "JSON Files (*.json)")
        if path:
            try:
                DataExporter.export_to_json(path, self.all_domains, self.all_videos)
                QMessageBox.information(self, "Sucesso", f"Arquivo JSON salvo com sucesso em:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro na Exportação", str(e))
