"""
Hunter Panel (Painel Espião) - Core mining, channel harvester, domain & Instagram analysis interface.
Features:
- Dual Modes: Search by Keyword OR Search by Channel (single or bulk list of channels).
- Channel Video Harvester (Populares / Recentes / Mais Antigos de Canais).
- Live Video Streaming Signal to Integrated Chromium Browser.
- Recursive Related Videos Search (Niche cluster discovery).
- Prioritization by View Count (Vídeos Mais Vistos).
- High-precision Language Verification & Scoring.
- Explicit 'Data de Envio' across all tables.
- Real-time Telemetry HUD: Elapsed Time, Average speed per video, Estimated time remaining.
- Turbo Ultra-Fast Mode vs Safe Anti-Ban Mode.
- Date & Year Range Filters (Global, Specific Years, Year Ranges, Recents).
- Clean Dark/Light theme adaptability.
"""

import os
import time
import gc
from typing import List, Dict, Any, Optional, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QSpinBox, QProgressBar,
    QTabWidget, QPlainTextEdit, QFrame, QFileDialog, QMessageBox,
    QCheckBox, QDialog, QListWidget, QListWidgetItem, QDialogButtonBox,
    QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QCursor, QIntValidator

from core.youtube_crawler import YouTubeCrawler
from core.translator import get_language_list, expand_queries_for_language, AVAILABLE_LANGUAGES
from core.metrics_calculator import format_number
from core.exporter import DataExporter
from core.autosave_manager import AutoSaveManager
from core.profile_manager import (
    load_default_profile, save_default_profile, launch_instance_with_target,
    get_named_profiles, save_named_profile, delete_named_profile
)
from core.niche_catalog import (
    NICHE_CATALOG, get_available_niches, get_subniches_for_niche,
    generate_queries_for_subniche, get_all_subniches_flat, get_subniche_query_stream
)
from ui.video_table_model import VideoTableView, DomainTableView
from ui.seo_table_view import SeoAuthorityTableView
from ui.settings_tab import APP_SETTINGS

class CountryExclusionDialog(QDialog):
    """Dialog allowing user to select countries/languages to exclude from Global searches."""
    def __init__(self, excluded_codes: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("🚫 Excluir Países / Idiomas da Busca Global")
        self.setMinimumSize(440, 520)
        self.excluded_codes = set(excluded_codes)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        info_lbl = QLabel(
            "Selecione os países/idiomas que deseja <b>EXCLUIR</b> dos resultados globais.<br>"
            "<span style='color: #64748B;'>Os países marcados com ☑ NÃO serão minerados quando o idioma for 'Global'.</span>"
        )
        info_lbl.setWordWrap(True)
        layout.addWidget(info_lbl)

        # Quick action buttons
        btn_box_top = QHBoxLayout()
        btn_select_none = QPushButton("Desmarcar Todos")
        btn_select_none.clicked.connect(self._clear_all)
        btn_box_top.addWidget(btn_select_none)

        btn_common_exclude = QPushButton("Excluir Raros (IN/RU/AR/CN/TR/ID/VI)")
        btn_common_exclude.clicked.connect(self._exclude_rare)
        btn_box_top.addWidget(btn_common_exclude)
        layout.addLayout(btn_box_top)

        self.list_widget = QListWidget()
        self.items_map = {}
        for code, data in AVAILABLE_LANGUAGES.items():
            if code == "global":
                continue
            item = QListWidgetItem(f"{data.get('flag', '')} {data.get('name', code)} ({code.upper()})")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            checked = Qt.CheckState.Checked if (code in self.excluded_codes or code.split("-")[0] in self.excluded_codes) else Qt.CheckState.Unchecked
            item.setCheckState(checked)
            self.list_widget.addItem(item)
            self.items_map[code] = item

        layout.addWidget(self.list_widget)

        btn_dialog = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_dialog.accepted.connect(self.accept)
        btn_dialog.rejected.connect(self.reject)
        layout.addWidget(btn_dialog)

    def _clear_all(self):
        for item in self.items_map.values():
            item.setCheckState(Qt.CheckState.Unchecked)

    def _exclude_rare(self):
        rare = {"hi", "ru", "ar", "zh", "tr", "id", "vi", "ko", "ja"}
        for code, item in self.items_map.items():
            if code in rare:
                item.setCheckState(Qt.CheckState.Checked)

    def get_excluded_codes(self) -> List[str]:
        result = []
        for code, item in self.items_map.items():
            if item.checkState() == Qt.CheckState.Checked:
                result.append(code)
        return result


class DomainExclusionDialog(QDialog):
    """Dialog allowing user to manage domain and Instagram handle exclusions, including multi-item pasting."""
    exclusions_updated = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🚫 Gerenciar Lista de Exclusão de Domínios & Perfis")
        self.setMinimumSize(540, 560)
        self.added_domains: List[str] = []
        self.all_custom_items: List[str] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        info_title = QLabel("🚫 Exclusão de Domínios e Perfis do Instagram")
        info_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #F1F1F1;")
        layout.addWidget(info_title)

        info_lbl = QLabel(
            "Adicione domínios ou perfis para serem <b>ignorados para sempre</b> em todas as varreduras.<br>"
            "<span style='color: #94A3B8;'>Você pode colar vários domínios de uma vez, separados por <b>vírgula</b>, "
            "<b>ponto e vírgula</b> ou <b>quebra de linha</b> (ex: <i>site1.com, site2.com, @perfil_ig</i>).</span>"
        )
        info_lbl.setWordWrap(True)
        layout.addWidget(info_lbl)

        self.txt_input = QPlainTextEdit()
        self.txt_input.setPlaceholderText(
            "Cole ou digite aqui um ou múltiplos domínios/perfis...\n"
            "Exemplo:\n"
            "meusite.com.br, lojaexemplo.com\n"
            "@perfilantigo\n"
            "cursodesativado.org; outrolink.net"
        )
        self.txt_input.setMaximumHeight(100)
        layout.addWidget(self.txt_input)

        btn_add = QPushButton("➕ Adicionar à Lista de Exclusão")
        btn_add.setObjectName("btn_start_action")
        btn_add.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_add.clicked.connect(self._on_add_clicked)
        layout.addWidget(btn_add)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #383838;")
        layout.addWidget(line)

        list_header = QHBoxLayout()
        self.lbl_count = QLabel("📋 Domínios Ignorados Customizados:")
        self.lbl_count.setStyleSheet("font-weight: 700; color: #E2E8F0;")
        list_header.addWidget(self.lbl_count)

        list_header.addStretch()

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("🔍 Filtrar lista...")
        self.input_search.setFixedWidth(180)
        self.input_search.textChanged.connect(self._filter_list)
        list_header.addWidget(self.input_search)
        layout.addLayout(list_header)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.list_widget, 1)

        btn_box = QHBoxLayout()
        self.btn_remove = QPushButton("🗑️ Remover Selecionado(s) da Exclusão")
        self.btn_remove.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_remove.clicked.connect(self._on_remove_clicked)
        btn_box.addWidget(self.btn_remove)

        btn_box.addStretch()

        btn_close = QPushButton("Concluir")
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

        self._load_exclusions()

    def _on_add_clicked(self):
        text = self.txt_input.toPlainText().strip()
        if not text:
            return
        from core.domain_extractor import add_to_exclusion_list, parse_multiple_exclusion_targets
        targets = parse_multiple_exclusion_targets(text)
        if not targets:
            QMessageBox.warning(self, "Aviso", "Nenhum domínio ou perfil válido identificado no texto inserido.")
            return

        add_to_exclusion_list(targets)
        self.added_domains.extend(targets)
        self.txt_input.clear()
        self._load_exclusions()
        self.exclusions_updated.emit(targets)
        QMessageBox.information(
            self,
            "Exclusão Atualizada",
            f"{len(targets)} domínio(s)/perfil(is) adicionado(s) à Lista de Exclusão com sucesso!"
        )

    def _on_remove_clicked(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Aviso", "Selecione ao menos um item na lista para remover da exclusão.")
            return

        targets = [item.text().strip() for item in selected_items if item.text().strip()]
        if not targets:
            return

        from core.domain_extractor import remove_from_exclusion_list
        remove_from_exclusion_list(targets)
        self._load_exclusions()
        QMessageBox.information(
            self,
            "Removido",
            f"{len(targets)} item(ns) removido(s) da Lista de Exclusão!"
        )

    def _load_exclusions(self):
        from core.domain_extractor import get_custom_exclusions
        self.all_custom_items = get_custom_exclusions()
        self.lbl_count.setText(f"📋 Domínios Ignorados Customizados ({len(self.all_custom_items)}):")
        self._filter_list(self.input_search.text())

    def _filter_list(self, query: str = ""):
        self.list_widget.clear()
        q = (query or "").strip().lower()
        for item in self.all_custom_items:
            if not q or q in item.lower():
                self.list_widget.addItem(item)


class CrawlerThread(QThread):
    """Background worker thread supporting Keywords, Channel Harvester, Live Browser Signals & Telemetry."""
    video_found = pyqtSignal(dict)
    domain_found = pyqtSignal(dict)
    live_video_analyzed = pyqtSignal(str, str)
    progress_updated = pyqtSignal(int, int, str)
    active_keyword_changed = pyqtSignal(str, str, int, int)
    finished_crawl = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        keywords: List[str],
        search_mode: str = "keywords",
        selected_lang: str = "pt",
        date_filter: str = "all_time",
        year_range: Optional[Tuple[int, int]] = None,
        max_videos: int = 50,
        min_views: int = 0,
        sort_by: str = "view_count",
        fast_mode: bool = True,
        include_related: bool = True,
        excluded_langs: Optional[List[str]] = None,
        loop_24h: bool = False,
        selected_niche: Optional[str] = None,
        selected_subniche: Optional[str] = None,
        parent=None
    ):
        super().__init__(parent)
        self.keywords = [k.strip() for k in keywords if k.strip()]
        self.search_mode = search_mode
        self.selected_lang = selected_lang
        self.date_filter = date_filter
        self.year_range = year_range
        self.max_videos = max_videos
        self.min_views = min_views
        self.sort_by = sort_by
        self.fast_mode = fast_mode
        self.include_related = include_related
        self.excluded_langs = excluded_langs or []
        self.loop_24h = loop_24h
        self.selected_niche = selected_niche
        self.selected_subniche = selected_subniche
        self.crawler = YouTubeCrawler(
            proxy_url=APP_SETTINGS.get("proxy_url"),
            min_delay=0.1 if fast_mode else APP_SETTINGS.get("min_delay", 1.0),
            max_delay=0.35 if fast_mode else APP_SETTINGS.get("max_delay", 2.5),
            fast_mode=fast_mode
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
                if self.search_mode == "channels":
                    # Channel Mode: Iterate through channels
                    for idx_ch, ch in enumerate(self.keywords):
                        if self._is_interrupted:
                            break
                        self._wait_if_paused()
                        self.active_keyword_changed.emit(ch, "Canal do YouTube", idx_ch + 1, len(self.keywords))
                        self.progress_updated.emit(0, self.max_videos, f"[Ciclo {cycle}] Coletando canal: {ch}...")

                        def on_prog_wrapped_ch(cur, tot, msg):
                            self._wait_if_paused()
                            self.progress_updated.emit(cur, tot, f"[Ciclo {cycle}] {msg}")

                        results = self.crawler.process_channel(
                            channel_identifier=ch,
                            max_videos=self.max_videos,
                            min_views=self.min_views,
                            sort_by=self.sort_by,
                            hl="pt",
                            gl="BR",
                            on_live_video=lambda u, t: self.live_video_analyzed.emit(u, t),
                            on_video_processed=lambda v: self.video_found.emit(v),
                            on_domain_found=lambda d: self.domain_found.emit(d),
                            on_progress=on_prog_wrapped_ch
                        )
                        total_vids_count += results.get("total_videos", 0)
                        total_doms_count += results.get("total_domains", 0)
                        total_avail_count += results.get("available_domains", 0)

                        if not self._is_interrupted and len(self.keywords) > 1:
                            time.sleep(1.0 if self.fast_mode else 2.5)

                elif self.search_mode == "niches":
                    # Nichos & Subnichos Mode: Continuous deep streaming sweep
                    niche_tasks = []
                    if not self.selected_niche or self.selected_niche == "all":
                        niche_tasks = get_all_subniches_flat(deep_expansion=True)
                    else:
                        subniches = get_subniches_for_niche(self.selected_niche)
                        if not self.selected_subniche or self.selected_subniche == "all":
                            for s in subniches:
                                qs = get_subniche_query_stream(self.selected_niche, s)
                                niche_tasks.append({"niche": self.selected_niche, "subniche": s, "queries": qs})
                        else:
                            qs = get_subniche_query_stream(self.selected_niche, self.selected_subniche)
                            niche_tasks.append({"niche": self.selected_niche, "subniche": self.selected_subniche, "queries": qs})

                    target_total = self.max_videos
                    total_tasks = len(niche_tasks)

                    for task_idx, task_info in enumerate(niche_tasks):
                        if self._is_interrupted or (target_total < 10000000 and total_vids_count >= target_total):
                            break
                        n_name = task_info["niche"]
                        s_name = task_info["subniche"]
                        queries = task_info["queries"]

                        for q_idx, q in enumerate(queries):
                            if self._is_interrupted or (target_total < 10000000 and total_vids_count >= target_total):
                                break
                            self._wait_if_paused()

                            remaining_needed = target_total - total_vids_count if target_total < 10000000 else 100
                            per_query_limit = max(15, min(remaining_needed, 100 if target_total > 100 else target_total))

                            total_display = f"{target_total:,}" if target_total < 10000000 else "Ilimitado"
                            self.active_keyword_changed.emit(
                                f"{s_name} - '{q}'",
                                f"{n_name} ({task_idx + 1}/{total_tasks})",
                                total_vids_count + 1,
                                total_display
                            )

                            self.progress_updated.emit(
                                total_vids_count, target_total,
                                f"[Vídeos: {total_vids_count}/{total_display}] {s_name} → '{q}'..."
                            )

                            def on_prog_wrapped_niche(cur, tot, msg):
                                self._wait_if_paused()
                                if "🏁 Varredura concluída" in msg or "ℹ️ Nenhum vídeo" in msg:
                                    return
                                current_cumulative = total_vids_count + cur
                                self.progress_updated.emit(
                                    current_cumulative, target_total,
                                    f"[Ciclo {cycle}] {msg}"
                                )

                            results = self.crawler.process_keyword(
                                keyword=q,
                                target_lang=self.selected_lang,
                                max_videos=per_query_limit,
                                min_views=self.min_views,
                                sort_by=self.sort_by,
                                date_filter=self.date_filter,
                                year_range=self.year_range,
                                include_related=self.include_related,
                                excluded_langs=self.excluded_langs,
                                hl="pt" if self.selected_lang == "pt" else "en",
                                gl="BR" if self.selected_lang == "pt" else "US",
                                display_label=f"{s_name}",
                                on_live_video=lambda u, t: self.live_video_analyzed.emit(u, t),
                                on_video_processed=lambda v: self.video_found.emit(v),
                                on_domain_found=lambda d: self.domain_found.emit(d),
                                on_progress=on_prog_wrapped_niche
                            )

                            vids_found = results.get("total_videos", 0)
                            total_vids_count += vids_found
                            total_doms_count += results.get("total_domains", 0)
                            total_avail_count += results.get("available_domains", 0)

                            if not self._is_interrupted and len(queries) > 1:
                                time.sleep(0.35 if self.fast_mode else 1.2)

                else:
                    # Keyword Mode: Standard search
                    for idx_kw, kw in enumerate(self.keywords):
                        if self._is_interrupted:
                            break
                        
                        lang_tasks = expand_queries_for_language(kw, self.selected_lang, excluded_langs=self.excluded_langs)

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
                            self.active_keyword_changed.emit(query, f"{flag} {lang_name}", idx_kw + 1, len(self.keywords))
                            self.progress_updated.emit(0, self.max_videos, f"[Ciclo {cycle}] {task_label}...")

                            def on_prog_wrapped(cur, tot, msg):
                                self._wait_if_paused()
                                self.progress_updated.emit(cur, tot, f"[Ciclo {cycle}] {msg}")

                            results = self.crawler.process_keyword(
                                keyword=query,
                                target_lang=self.selected_lang,
                                max_videos=self.max_videos,
                                min_views=self.min_views,
                                sort_by=self.sort_by,
                                date_filter=self.date_filter,
                                year_range=self.year_range,
                                include_related=self.include_related,
                                excluded_langs=self.excluded_langs,
                                hl=hl,
                                gl=gl,
                                display_label=f"{flag} {lang_name}",
                                on_live_video=lambda u, t: self.live_video_analyzed.emit(u, t),
                                on_video_processed=lambda v: self.video_found.emit(v),
                                on_domain_found=lambda d: self.domain_found.emit(d),
                                on_progress=on_prog_wrapped
                            )

                            total_vids_count += results.get("total_videos", 0)
                            total_doms_count += results.get("total_domains", 0)
                            total_avail_count += results.get("available_domains", 0)

                            if not self._is_interrupted and len(lang_tasks) > 1:
                                time.sleep(0.8 if self.fast_mode else 2.0)

                        if not self._is_interrupted and len(self.keywords) > 1:
                            time.sleep(1.0 if self.fast_mode else 2.5)

                if not self.loop_24h or self._is_interrupted:
                    break

                cycle += 1
                self.progress_updated.emit(100, 100, f"Ciclo {cycle-1} concluído. Aguardando intervalo...")
                for _ in range(10 if self.fast_mode else 15):
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
    """Main Hunting Dashboard supporting Keywords, Channel Lists, Telemetry, Live Browser & Related Videos."""
    navigate_url_requested = pyqtSignal(str)
    live_video_stream = pyqtSignal(str, str, object)
    switch_to_browser_tab = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.crawler_thread: Optional[CrawlerThread] = None
        self.is_paused = False
        self.excluded_countries: List[str] = []
        
        self.all_videos: List[Dict[str, Any]] = []
        self.all_domains: List[Dict[str, Any]] = []

        # Preventive High-Performance O(1) Sets & Batch Buffers
        self._seen_video_ids: set = set()
        self._seen_domain_keys: set = set()
        self._pending_videos_buffer: List[Dict[str, Any]] = []
        self._pending_domains_buffer: List[Dict[str, Any]] = []
        self._processed_videos_counter: int = 0

        # UI Batch Timer: Flushes updates smoothly to prevent UI freezes
        self._ui_batch_timer = QTimer(self)
        self._ui_batch_timer.setInterval(250)
        self._ui_batch_timer.timeout.connect(self._flush_pending_ui_batch)

        # Auto-Save & Crash Recovery Manager
        self.autosave_manager = AutoSaveManager()
        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(30000) # Save every 30 seconds
        self.autosave_timer.timeout.connect(self._trigger_autosave)
        self.autosave_timer.start()

        # Telemetry State
        self.start_time: float = 0.0
        self.target_video_count: int = 50
        self.is_background_mode: bool = False
        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.setInterval(500)
        self.telemetry_timer.timeout.connect(self._update_telemetry)

        # Mining Activity Pulse Timer (Visual blinking animation when mining is active)
        self.pulse_timer = QTimer(self)
        self.pulse_timer.setInterval(600)
        self.pulse_timer.timeout.connect(self._on_mining_pulse)
        self._pulse_state = False

        self.named_profiles: Dict[str, Dict[str, Any]] = {}

        self._init_ui()
        self._reload_presets_combo()
        self._restore_default_profile(silent=True)
        self._restore_previous_session_if_any()

    def set_background_mode(self, is_bg: bool):
        """Throttle UI updates and timers to minimize background CPU/RAM consumption."""
        self.is_background_mode = is_bg
        if is_bg:
            self.telemetry_timer.setInterval(4000)
            self.pulse_timer.setInterval(2000)
        else:
            self.telemetry_timer.setInterval(500)
            self.pulse_timer.setInterval(600)
            self.all_videos.sort(key=lambda x: x.get("metrics", {}).get("view_count", 0), reverse=True)
            self.video_table.set_videos(self.all_videos)
            self.domain_table.set_domains(self.all_domains)
            self._update_stat_cards()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(12)

        # 1. Top Stat Cards
        main_layout.addLayout(self._create_stats_header())

        # 2. Controls Panel Container
        main_layout.addWidget(self._create_controls_panel())

        # 3. Status Message, Telemetry HUD & Progress Bar
        status_bar_layout = QVBoxLayout()
        status_bar_layout.setSpacing(4)

        status_header_layout = QHBoxLayout()
        self.status_label = QLabel("Pronto para iniciar a mineração. Digite termos ou canais e clique em 'Iniciar Busca'.")
        self.status_label.setObjectName("status_label")
        status_header_layout.addWidget(self.status_label, 1)

        # Real-time Telemetry HUD Label
        self.lbl_telemetry = QLabel("⏱️ Tempo: 00:00  •  ⚡ Média: -- s/vídeo  •  ⏳ Restante: --")
        self.lbl_telemetry.setStyleSheet("color: #38BDF8; font-weight: 700; font-size: 12px;")
        status_header_layout.addWidget(self.lbl_telemetry)

        # Active Keyword / Target HUD Banner (prominent highlight of current mining query)
        self.active_target_card = QFrame()
        self.active_target_card.setObjectName("active_target_card")
        self.active_target_card.setStyleSheet("""
            QFrame#active_target_card {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0F172A, stop:0.5 #1E293B, stop:1 #0F172A);
                border: 2px solid #0284C7;
                border-radius: 8px;
                padding: 6px 12px;
            }
        """)
        active_layout = QHBoxLayout(self.active_target_card)
        active_layout.setContentsMargins(10, 4, 10, 4)
        active_layout.setSpacing(10)

        self.lbl_active_prefix = QLabel("🔍 MINERANDO AGORA:")
        self.lbl_active_prefix.setStyleSheet("color: #38BDF8; font-weight: 800; font-size: 11px; letter-spacing: 0.5px;")
        active_layout.addWidget(self.lbl_active_prefix)

        self.lbl_active_keyword = QLabel("Aguardando início da mineração...")
        self.lbl_active_keyword.setStyleSheet("color: #F8FAFC; font-weight: 800; font-size: 13px;")
        active_layout.addWidget(self.lbl_active_keyword, 1)

        self.lbl_active_progress_pill = QLabel("Termo -- / --")
        self.lbl_active_progress_pill.setStyleSheet("""
            background-color: #0369A1;
            color: #FFFFFF;
            font-weight: 800;
            font-size: 11px;
            padding: 3px 10px;
            border-radius: 10px;
        """)
        active_layout.addWidget(self.lbl_active_progress_pill)

        status_bar_layout.addWidget(self.active_target_card)

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
        self.video_table.open_video_requested.connect(self._on_open_video_requested)
        self.results_tabs.addTab(self.video_table, "🏆 Vídeos Minerados & Métricas de Tráfego")

        # Tab 2: Discovered Domains & Instagrams
        domain_container = QWidget()
        domain_layout = QVBoxLayout(domain_container)
        domain_layout.setContentsMargins(8, 10, 8, 8)
        domain_layout.setSpacing(10)

        self.domain_table = DomainTableView()
        self.domain_table.buy_domain_requested.connect(self._on_buy_domain_requested)
        self.domain_table.open_video_requested.connect(self._on_open_video_requested)
        self.domain_table.domain_excluded_requested.connect(self._on_domain_excluded)
        self.domain_table.domains_excluded_requested.connect(self._on_domains_excluded)
        self.domain_table.manage_exclusions_requested.connect(self._open_domain_exclusion_dialog)
        self.domain_table.filter_videos_by_domain_requested.connect(self._on_filter_videos_by_domain)
        domain_layout.addWidget(self.domain_table)

        self.results_tabs.addTab(domain_container, "💎 Domínios & Instagrams Expirados")

        # Tab 3: SEO Authority Metrics (DA, PA, Backlinks)
        self.seo_table = SeoAuthorityTableView()
        self.seo_table.buy_domain_requested.connect(self._on_buy_domain_requested)
        self.seo_table.domain_excluded_requested.connect(self._on_domain_excluded)
        self.seo_table.domains_excluded_requested.connect(self._on_domains_excluded)
        self.seo_table.manage_exclusions_requested.connect(self._open_domain_exclusion_dialog)
        self.results_tabs.addTab(self.seo_table, "📊 Métricas SEO (DA / PA / Backlinks)")

        # Tab 4: Real-time logs
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("log_view")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(2000)
        self.results_tabs.addTab(self.log_view, "📜 Logs em Tempo Real")

        main_layout.addWidget(self.results_tabs, 1)

        # 5. Bottom Toolbar
        main_layout.addLayout(self._create_bottom_toolbar())

    def _create_stats_header(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(10)

        self.card_videos, self.val_videos = self._build_stat_card("VÍDEOS MINERADOS", "0", "stat_card", "stat_val_videos")
        self.card_views, self.val_views = self._build_stat_card("VIEWS TOTAIS", "0", "stat_card", "stat_val_views")
        self.card_domains, self.val_domains = self._build_stat_card("TOTAL LINKS / IGs", "0", "stat_card", "stat_val_domains")
        self.card_avail, self.val_avail = self._build_stat_card("🟢 DOMÍNIOS P/ COMPRA", "0", "stat_card_available", "stat_val_available")
        self.card_instagram, self.val_instagram = self._build_stat_card("📸 INSTAGRAMS LIVRES", "0", "stat_card_instagram", "stat_val_instagram")

        # Interactive click-to-filter
        for card, tip in [
            (self.card_videos, "Clique para ver a tabela de vídeos"),
            (self.card_domains, "Clique para ver todos os domínios e perfis na tabela"),
            (self.card_avail, "Clique para ver e auditar métricas SEO (DA / PA / Backlinks) dos domínios disponíveis"),
            (self.card_instagram, "Clique para filtrar apenas perfis do Instagram livres"),
        ]:
            card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            card.setToolTip(tip)

        self.card_videos.mousePressEvent = lambda _: self.results_tabs.setCurrentIndex(0)
        self.card_domains.mousePressEvent = lambda _: self._filter_domains_by_type(0)
        self.card_avail.mousePressEvent = lambda _: self._on_card_avail_clicked()
        self.card_instagram.mousePressEvent = lambda _: self._filter_domains_by_type(2)

        layout.addWidget(self.card_videos)
        layout.addWidget(self.card_views)
        layout.addWidget(self.card_domains)
        layout.addWidget(self.card_avail)
        layout.addWidget(self.card_instagram)
        return layout

    def _on_card_avail_clicked(self):
        """Switch directly to SEO Authority Metrics tab (DA / PA / Backlinks) with available domains."""
        self.results_tabs.setCurrentWidget(self.seo_table)
        self.domain_table.combo_filter.setCurrentIndex(1)

    def _filter_domains_by_type(self, filter_index: int):
        """Switch to Domains tab and apply selected filter index."""
        self.results_tabs.setCurrentIndex(1)
        self.domain_table.combo_filter.setCurrentIndex(filter_index)

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
        panel_layout.setContentsMargins(14, 10, 14, 10)
        panel_layout.setSpacing(8)

        # ----------------------------------------------------
        # LINHA 1: Alvo da Busca & Modos de Configuração Salvos
        # ----------------------------------------------------
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        # Mode Selector
        self.combo_mode = QComboBox()
        self.combo_mode.addItem("🎯 Palavras-chave", "keywords")
        self.combo_mode.addItem("📺 Canais do YouTube", "channels")
        self.combo_mode.addItem("🌳 Nichos & Subnichos", "niches")
        self.combo_mode.setMinimumWidth(170)
        self.combo_mode.setMaximumWidth(190)
        self.combo_mode.currentIndexChanged.connect(self._on_search_mode_changed)
        row1.addWidget(self.combo_mode)

        # Search Target Input Bar (for keywords & channels)
        self.input_target = QLineEdit()
        self.input_target.setPlaceholderText("Digite termos de busca ou canais (ex: GTA, dropshipping, receitas fitness)...")
        self.input_target.setMinimumWidth(260)
        self.input_target.returnPressed.connect(self._on_start_or_resume)
        row1.addWidget(self.input_target, 2)

        # Multi-Instance Batch Launcher from .TXT
        self.btn_batch_txt = QPushButton("📂 Lista .TXT")
        self.btn_batch_txt.setObjectName("btn_batch_action")
        self.btn_batch_txt.setToolTip("Carregar arquivo .txt com termos por linha para abrir múltiplas instâncias e minerar automaticamente.")
        self.btn_batch_txt.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_batch_txt.clicked.connect(self._load_batch_txt_file)
        row1.addWidget(self.btn_batch_txt)

        # Niche & Sub-Niche Selectors (for niches mode)
        self.combo_niche = QComboBox()
        self.combo_niche.setMinimumWidth(210)
        self.combo_niche.addItem("🌐 Todos os Nichos", "all")
        for n_name in get_available_niches():
            self.combo_niche.addItem(n_name, n_name)
        self.combo_niche.currentIndexChanged.connect(self._on_niche_changed)
        self.combo_niche.setVisible(False)
        row1.addWidget(self.combo_niche, 1)

        self.combo_subniche = QComboBox()
        self.combo_subniche.setMinimumWidth(210)
        self.combo_subniche.setVisible(False)
        row1.addWidget(self.combo_subniche, 1)
        self._populate_subniches()

        # Saved Preset Mode Selector (Named Profiles List)
        lbl_presets = QLabel("📁 Modo Salvo:")
        lbl_presets.setStyleSheet("font-weight: 600; color: #94A3B8;")
        row1.addWidget(lbl_presets)

        self.combo_presets = QComboBox()
        self.combo_presets.setMinimumWidth(160)
        self.combo_presets.setMaximumWidth(210)
        self.combo_presets.currentIndexChanged.connect(self._on_preset_selected)
        row1.addWidget(self.combo_presets)

        self.btn_save_preset = QPushButton("💾 Salvar")
        self.btn_save_preset.setToolTip("Salvar a configuração atual com um nome personalizado para encontrar na lista.")
        self.btn_save_preset.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save_preset.clicked.connect(self._save_custom_preset_dialog)
        row1.addWidget(self.btn_save_preset)

        self.btn_delete_preset = QPushButton("🗑️")
        self.btn_delete_preset.setToolTip("Excluir o modo de configuração selecionado na lista.")
        self.btn_delete_preset.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_delete_preset.setFixedWidth(34)
        self.btn_delete_preset.clicked.connect(self._delete_selected_preset)
        row1.addWidget(self.btn_delete_preset)

        panel_layout.addLayout(row1)

        # ----------------------------------------------------
        # LINHA 2: Filtros de Localização, Datas & Ordenação
        # ----------------------------------------------------
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        lbl_lang = QLabel("🌍 Idioma:")
        lbl_lang.setStyleSheet("font-weight: 600; color: #94A3B8;")
        row2.addWidget(lbl_lang)

        self.combo_lang = QComboBox()
        for l in get_language_list():
            self.combo_lang.addItem(l["label"], l["code"])
        self.combo_lang.setMinimumWidth(150)
        self.combo_lang.setMaximumWidth(185)
        self.combo_lang.currentIndexChanged.connect(self._on_lang_changed)
        row2.addWidget(self.combo_lang)

        self.btn_exclude_countries = QPushButton("🚫 Países...")
        self.btn_exclude_countries.setToolTip("Configurar países ou idiomas a serem excluídos das buscas globais.")
        self.btn_exclude_countries.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_exclude_countries.clicked.connect(self._open_country_exclusion_dialog)
        row2.addWidget(self.btn_exclude_countries)

        row2.addSpacing(6)

        lbl_dt = QLabel("📅 Filtro de Datas:")
        lbl_dt.setStyleSheet("font-weight: 600; color: #94A3B8;")
        row2.addWidget(lbl_dt)

        self.combo_date = QComboBox()
        self.combo_date.addItem("🌐 Todas as Datas (Global)", "all_time")
        self.combo_date.addItem("📅 Ano de 2026 (Atual)", "2026")
        self.combo_date.addItem("📆 Ano de 2025", "2025")
        self.combo_date.addItem("📆 Ano de 2024", "2024")
        self.combo_date.addItem("📆 Ano de 2023", "2023")
        self.combo_date.addItem("📆 Ano de 2022", "2022")
        self.combo_date.addItem("📆 Ano de 2021", "2021")
        self.combo_date.addItem("📆 Ano de 2020", "2020")
        self.combo_date.addItem("🎯 Intervalo de Anos...", "custom_range")
        self.combo_date.addItem("⏱️ Este Mês", "this_month")
        self.combo_date.addItem("🗓️ Esta Semana", "this_week")
        self.combo_date.addItem("🔥 Últimas 24 Horas", "today")
        self.combo_date.setMinimumWidth(160)
        self.combo_date.setMaximumWidth(190)
        self.combo_date.currentIndexChanged.connect(self._on_date_filter_changed)
        row2.addWidget(self.combo_date)

        # Custom Year Range Controls (agora com tamanho confortável e legível)
        self.widget_custom_years = QWidget()
        custom_yr_layout = QHBoxLayout(self.widget_custom_years)
        custom_yr_layout.setContentsMargins(0, 0, 0, 0)
        custom_yr_layout.setSpacing(5)
        
        lbl_de = QLabel("De:")
        lbl_de.setStyleSheet("font-weight: 700; color: #38BDF8;")
        custom_yr_layout.addWidget(lbl_de)
        
        self.spin_year_start = QSpinBox()
        self.spin_year_start.setRange(2006, 2026)
        self.spin_year_start.setValue(2020)
        self.spin_year_start.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_year_start.setFixedWidth(85)
        self.spin_year_start.setToolTip("Ano inicial (ex: 2020)")
        custom_yr_layout.addWidget(self.spin_year_start)
        
        lbl_ate = QLabel("Até:")
        lbl_ate.setStyleSheet("font-weight: 700; color: #38BDF8;")
        custom_yr_layout.addWidget(lbl_ate)
        
        self.spin_year_end = QSpinBox()
        self.spin_year_end.setRange(2006, 2026)
        self.spin_year_end.setValue(2026)
        self.spin_year_end.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_year_end.setFixedWidth(85)
        self.spin_year_end.setToolTip("Ano final (ex: 2026)")
        custom_yr_layout.addWidget(self.spin_year_end)
        
        self.widget_custom_years.setVisible(False)
        row2.addWidget(self.widget_custom_years)

        row2.addSpacing(6)

        lbl_sort = QLabel("🔥 Ordenar:")
        lbl_sort.setStyleSheet("font-weight: 600; color: #94A3B8;")
        row2.addWidget(lbl_sort)

        self.combo_sort = QComboBox()
        self.combo_sort.addItem("🔥 Mais Vistos", "view_count")
        self.combo_sort.addItem("🎯 Relevância", "relevance")
        self.combo_sort.addItem("📅 Mais Recentes", "upload_date")
        self.combo_sort.setMinimumWidth(135)
        self.combo_sort.setMaximumWidth(160)
        row2.addWidget(self.combo_sort)

        row2.addStretch()

        self.btn_exclude_domains = QPushButton("🛡️ Excluir Domínios...")
        self.btn_exclude_domains.setToolTip("Adicionar múltiplos domínios ou perfis à lista de exclusão permanente.")
        self.btn_exclude_domains.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_exclude_domains.clicked.connect(self._open_domain_exclusion_dialog)
        row2.addWidget(self.btn_exclude_domains)

        panel_layout.addLayout(row2)

        # ----------------------------------------------------
        # LINHA 3: Critérios de Filtragem & Botões de Ação
        # ----------------------------------------------------
        row3 = QHBoxLayout()
        row3.setSpacing(8)

        lbl_lim = QLabel("Limite:")
        lbl_lim.setStyleSheet("font-weight: 600; color: #94A3B8;")
        row3.addWidget(lbl_lim)

        self.spin_max = QSpinBox()
        self.spin_max.setRange(5, 10000000)
        self.spin_max.setValue(50)
        self.spin_max.setSingleStep(500)
        self.spin_max.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_max.setFixedWidth(100)
        row3.addWidget(self.spin_max)

        self.chk_unlimited = QCheckBox("♾️ Todos os Vídeos (até 10M)")
        self.chk_unlimited.setToolTip("Busca todos os vídeos disponíveis do canal ou termo (até 10.000.000).")
        self.chk_unlimited.toggled.connect(lambda checked: self.spin_max.setEnabled(not checked))
        row3.addWidget(self.chk_unlimited)

        row3.addSpacing(6)

        lbl_min_views = QLabel("Mín. Views:")
        lbl_min_views.setStyleSheet("font-weight: 600; color: #94A3B8;")
        row3.addWidget(lbl_min_views)

        self.input_min_views = QLineEdit()
        self.input_min_views.setPlaceholderText("0")
        self.input_min_views.setValidator(QIntValidator(0, 100000000))
        self.input_min_views.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_min_views.setFixedWidth(90)
        self.input_min_views.setToolTip("Mínimo de visualizações do vídeo (ex: 50000).")
        row3.addWidget(self.input_min_views)

        row3.addSpacing(6)

        self.chk_fast_mode = QCheckBox("⚡ Turbo")
        self.chk_fast_mode.setChecked(True)
        self.chk_fast_mode.setToolTip("Mineração ultra-rápida de vídeos (~0.4s por vídeo).")
        row3.addWidget(self.chk_fast_mode)

        self.chk_include_related = QCheckBox("🔗 Relacionados")
        self.chk_include_related.setChecked(True)
        self.chk_include_related.setToolTip("Aprende termos relacionados reais no YouTube e aplica filtro semântico estrito.")
        row3.addWidget(self.chk_include_related)

        self.chk_mode_24h = QCheckBox("🔄 24h")
        self.chk_mode_24h.setToolTip("Executa em ciclos contínuos com pausas seguras anti-bloqueio.")
        row3.addWidget(self.chk_mode_24h)

        row3.addStretch()

        # Action Buttons
        self.btn_start = QPushButton("🚀 Iniciar Busca")
        self.btn_start.setObjectName("btn_start_action")
        self.btn_start.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_start.clicked.connect(self._on_start_or_resume)
        row3.addWidget(self.btn_start)

        self.btn_pause = QPushButton("⏸️ Pausar")
        self.btn_pause.setObjectName("btn_pause_action")
        self.btn_pause.setEnabled(False)
        self.btn_pause.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_pause.clicked.connect(self._on_toggle_pause)
        row3.addWidget(self.btn_pause)

        self.btn_stop = QPushButton("⏹ Parar")
        self.btn_stop.setObjectName("btn_stop_action")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_stop.clicked.connect(self._on_stop_completely)
        row3.addWidget(self.btn_stop)

        self.btn_view_live = QPushButton("🌐 Navegador")
        self.btn_view_live.setObjectName("btn_table_action")
        self.btn_view_live.setToolTip("Alternar para o Navegador Web Integrado.")
        self.btn_view_live.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_view_live.clicked.connect(lambda: self.switch_to_browser_tab.emit())
        row3.addWidget(self.btn_view_live)

        panel_layout.addLayout(row3)
        return panel

    def _reload_presets_combo(self, selected_name: Optional[str] = None):
        """Populate the combo_presets with all available named modes."""
        self.combo_presets.blockSignals(True)
        self.combo_presets.clear()
        self.named_profiles = get_named_profiles()
        for name in self.named_profiles.keys():
            self.combo_presets.addItem(f"📋 {name}", name)
        
        if selected_name and selected_name in self.named_profiles:
            idx = self.combo_presets.findData(selected_name)
            if idx >= 0:
                self.combo_presets.setCurrentIndex(idx)
        self.combo_presets.blockSignals(False)

    def _on_preset_selected(self):
        preset_name = self.combo_presets.currentData()
        if preset_name and preset_name in self.named_profiles:
            prof = self.named_profiles[preset_name]
            self._apply_profile_to_ui(prof)
            self._append_log(f"📁 Modo '{preset_name}' carregado.")

    def _save_custom_preset_dialog(self):
        from PyQt6.QtWidgets import QInputDialog
        current_name = self.combo_presets.currentData() or "Meu Modo"
        default_name = current_name.replace("📋 ", "").replace("⭐ ", "")
        name, ok = QInputDialog.getText(
            self,
            "Salvar Modo de Configuração",
            "Digite um nome para este modo de configuração (ex: Filtro 100k Brasil, Global 2026):",
            QLineEdit.EchoMode.Normal,
            default_name
        )
        if ok and name.strip():
            clean = name.strip()
            prof = self._get_current_profile_from_ui()
            if save_named_profile(clean, prof):
                # Also set as active default profile
                save_default_profile(prof)
                self._reload_presets_combo(selected_name=clean)
                QMessageBox.information(self, "Modo Salvo", f"✅ O modo '{clean}' foi salvo na lista com sucesso!\n\nVocê pode selecioná-lo a qualquer momento no menu 'Modo Salvo'.")

    def _delete_selected_preset(self):
        preset_name = self.combo_presets.currentData()
        if not preset_name or preset_name == "⭐ Modo Padrão":
            QMessageBox.warning(self, "Aviso", "O modo padrão do sistema não pode ser excluído.")
            return

        reply = QMessageBox.question(
            self,
            "Excluir Modo",
            f"Deseja realmente excluir o modo '{preset_name}' da lista?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if delete_named_profile(preset_name):
                self._reload_presets_combo(selected_name="⭐ Modo Padrão")
                self._restore_default_profile(silent=True)
                self._append_log(f"🗑️ Modo '{preset_name}' excluído.")

    def _apply_profile_to_ui(self, profile: Dict[str, Any]):
        """Apply a saved configuration dictionary to the UI elements cleanly."""
        try:
            # Search mode
            mode = profile.get("search_mode", "keywords")
            m_idx = self.combo_mode.findData(mode)
            if m_idx >= 0:
                self.combo_mode.setCurrentIndex(m_idx)

            # Niche & Sub-niche
            niche = profile.get("selected_niche")
            if niche:
                n_idx = self.combo_niche.findData(niche)
                if n_idx >= 0:
                    self.combo_niche.setCurrentIndex(n_idx)
            subniche = profile.get("selected_subniche")
            if subniche:
                s_idx = self.combo_subniche.findData(subniche)
                if s_idx >= 0:
                    self.combo_subniche.setCurrentIndex(s_idx)

            # Language
            lang = profile.get("target_lang", "global")
            l_idx = self.combo_lang.findData(lang)
            if l_idx >= 0:
                self.combo_lang.setCurrentIndex(l_idx)

            # Excluded countries
            self.excluded_countries = profile.get("excluded_countries", [])
            cnt = len(self.excluded_countries)
            if cnt > 0:
                self.btn_exclude_countries.setText(f"🚫 Excluir Países ({cnt})")
                self.btn_exclude_countries.setStyleSheet("QPushButton { background-color: #DC2626; color: #FFFFFF; font-weight: 700; }")
            else:
                self.btn_exclude_countries.setText("🚫 Excluir Países...")
                self.btn_exclude_countries.setStyleSheet("")

            # Date Filter
            d_filter = profile.get("date_filter", "all_time")
            d_idx = self.combo_date.findData(d_filter)
            if d_idx >= 0:
                self.combo_date.setCurrentIndex(d_idx)

            # Years
            self.spin_year_start.setValue(profile.get("year_start", 2020))
            self.spin_year_end.setValue(profile.get("year_end", 2026))

            # Sort By
            sort_by = profile.get("sort_by", "view_count")
            s_idx = self.combo_sort.findData(sort_by)
            if s_idx >= 0:
                self.combo_sort.setCurrentIndex(s_idx)

            # Limits & Views
            self.spin_max.setValue(profile.get("max_videos", 50))
            self.chk_unlimited.setChecked(profile.get("unlimited_videos", False))
            min_v = profile.get("min_views", 0)
            self.input_min_views.setText(str(min_v) if min_v > 0 else "")

            # Checkboxes
            self.chk_fast_mode.setChecked(profile.get("fast_mode", True))
            self.chk_include_related.setChecked(profile.get("include_related", True))
            self.chk_mode_24h.setChecked(profile.get("loop_24h", False))
        except Exception as e:
            pass

    def _get_current_profile_from_ui(self) -> Dict[str, Any]:
        """Extract current active UI settings into a persistent dictionary."""
        return {
            "search_mode": self.combo_mode.currentData(),
            "selected_niche": self.combo_niche.currentData(),
            "selected_subniche": self.combo_subniche.currentData(),
            "target_lang": self.combo_lang.currentData(),
            "excluded_countries": list(self.excluded_countries),
            "date_filter": self.combo_date.currentData(),
            "year_start": self.spin_year_start.value(),
            "year_end": self.spin_year_end.value(),
            "sort_by": self.combo_sort.currentData(),
            "max_videos": self.spin_max.value(),
            "unlimited_videos": self.chk_unlimited.isChecked(),
            "min_views": self.get_min_views(),
            "fast_mode": self.chk_fast_mode.isChecked(),
            "include_related": self.chk_include_related.isChecked(),
            "loop_24h": self.chk_mode_24h.isChecked()
        }

    def _restore_default_profile(self, silent: bool = False):
        prof = load_default_profile()
        self._apply_profile_to_ui(prof)
        if not silent:
            self._append_log("🔄 Configurações padrão restauradas.")

    def _load_batch_txt_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Lista de Termos / Canais (.txt)",
            "",
            "Arquivos de Texto (*.txt);;Todos os Arquivos (*.*)"
        )
        if not file_path or not os.path.exists(file_path):
            return

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Ler Arquivo", f"Não foi possível ler o arquivo:\n{e}")
            return

        if not lines:
            QMessageBox.warning(self, "Arquivo Vazio", "O arquivo selecionado não contém nenhum termo de busca ou canal válido.")
            return

        total = len(lines)
        if total == 1:
            self.input_target.setText(lines[0])
            self._append_log(f"📂 1 termo carregado do arquivo: '{lines[0]}'")
            return

        # Prompt user with clean options
        msg = QMessageBox(self)
        msg.setWindowTitle("Carregar Lista de Termos (.txt)")
        msg.setText(
            f"<b>Foram encontrados {total} termos/canais no arquivo:</b><br>"
            f"<span style='color: #38BDF8;'>{', '.join(lines[:4])}{'...' if total > 4 else ''}</span><br><br>"
            f"Deseja abrir <b>{total} instâncias do YouTube Espião</b> (uma para cada linha) com as configurações padrão atuais e iniciar a busca automática?"
        )
        
        btn_multi = msg.addButton(f"🚀 Abrir {total} Instâncias com Busca Automática", QMessageBox.ButtonRole.AcceptRole)
        btn_single = msg.addButton(f"🎯 Carregar Todos nesta Instância ({total} juntos)", QMessageBox.ButtonRole.ActionRole)
        btn_cancel = msg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        msg.setDefaultButton(btn_multi)
        msg.exec()

        if msg.clickedButton() == btn_multi:
            # 1. Save current settings as default profile so all spawned instances inherit them
            save_default_profile(self._get_current_profile_from_ui())

            # 2. Start 1st term in current instance
            self.input_target.setText(lines[0])
            self._append_log(f"🚀 [Instância Atual] Iniciando busca automática para: '{lines[0]}'")
            QTimer.singleShot(600, self._on_start_or_resume)

            # 3. Launch remaining instances in background
            launched = 1
            for term in lines[1:]:
                time.sleep(0.4)
                if launch_instance_with_target(term, autostart=True):
                    launched += 1
            
            self._append_log(f"✨ {launched} instâncias iniciadas com sucesso a partir do arquivo .txt!")

        elif msg.clickedButton() == btn_single:
            self.input_target.setText(", ".join(lines))
            self._append_log(f"📂 {total} termos carregados na instância atual.")

    def get_min_views(self) -> int:
        """Parse clean integer from input_min_views without formatting errors."""
        raw = self.input_min_views.text().replace(".", "").replace(",", "").strip()
        try:
            return max(0, int(raw)) if raw else 0
        except Exception:
            return 0

    def _on_lang_changed(self):
        code = self.combo_lang.currentData()
        self.btn_exclude_countries.setVisible(code == "global")

    def _open_country_exclusion_dialog(self):
        dialog = CountryExclusionDialog(self.excluded_countries, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.excluded_countries = dialog.get_excluded_codes()
            cnt = len(self.excluded_countries)
            if cnt > 0:
                self.btn_exclude_countries.setText(f"🚫 Excluir Países ({cnt})")
                self.btn_exclude_countries.setStyleSheet("QPushButton { background-color: #DC2626; color: #FFFFFF; font-weight: 700; }")
            else:
                self.btn_exclude_countries.setText("🚫 Excluir Países...")
                self.btn_exclude_countries.setStyleSheet("")

    def _open_domain_exclusion_dialog(self):
        dialog = DomainExclusionDialog(self)
        dialog.exclusions_updated.connect(self._on_domains_excluded)
        dialog.exec()

    def _populate_subniches(self):
        """Populate the sub-niche combo based on currently selected main niche."""
        self.combo_subniche.blockSignals(True)
        self.combo_subniche.clear()
        selected_niche = self.combo_niche.currentData()
        if not selected_niche or selected_niche == "all":
            self.combo_subniche.addItem("⭐ Todos os Subnichos do Catálogo", "all")
        else:
            self.combo_subniche.addItem("⭐ Todos os Subnichos do Nicho", "all")
            sub_list = get_subniches_for_niche(selected_niche)
            for sub in sub_list:
                self.combo_subniche.addItem(sub, sub)
        self.combo_subniche.blockSignals(False)

    def _on_niche_changed(self):
        self._populate_subniches()

    def _on_search_mode_changed(self):
        mode = self.combo_mode.currentData()
        self.combo_sort.clear()

        if mode == "channels":
            self.input_target.setVisible(True)
            self.combo_niche.setVisible(False)
            self.combo_subniche.setVisible(False)
            self.btn_batch_txt.setVisible(True)
            self.input_target.setPlaceholderText("Digite canal ou lista de canais (ex: @canal1, @canal2, https://youtube.com/@canal)...")
            self.combo_lang.setVisible(False)
            self.btn_exclude_countries.setVisible(False)
            self.combo_date.setVisible(False)
            self.widget_custom_years.setVisible(False)
            self.chk_include_related.setVisible(False)
            self.combo_sort.addItem("🔥 Mais Populares (Padrão)", "popular")
            self.combo_sort.addItem("📅 Mais Recentes", "newest")
            self.combo_sort.addItem("⏳ Mais Antigos", "oldest")
        elif mode == "niches":
            self.input_target.setVisible(False)
            self.combo_niche.setVisible(True)
            self.combo_subniche.setVisible(True)
            self.btn_batch_txt.setVisible(False)
            self.combo_lang.setVisible(True)
            self._on_lang_changed()
            self.combo_date.setVisible(True)
            self._on_date_filter_changed()
            self.chk_include_related.setVisible(True)
            self.combo_sort.addItem("🔥 Mais Vistos (Padrão)", "view_count")
            self.combo_sort.addItem("🎯 Relevância", "relevance")
            self.combo_sort.addItem("📅 Mais Recentes", "upload_date")
        else:
            self.input_target.setVisible(True)
            self.combo_niche.setVisible(False)
            self.combo_subniche.setVisible(False)
            self.btn_batch_txt.setVisible(True)
            self.input_target.setPlaceholderText("Digite termos de busca (ex: GTA, dropshipping, marketing digital)...")
            self.combo_lang.setVisible(True)
            self._on_lang_changed()
            self.combo_date.setVisible(True)
            self._on_date_filter_changed()
            self.chk_include_related.setVisible(True)
            self.combo_sort.addItem("🔥 Mais Vistos (Padrão)", "view_count")
            self.combo_sort.addItem("🎯 Relevância", "relevance")
            self.combo_sort.addItem("📅 Mais Recentes", "upload_date")

    def _on_date_filter_changed(self):
        code = self.combo_date.currentData()
        mode = self.combo_mode.currentData()
        is_custom = (code == "custom_range" and mode != "channels")
        self.widget_custom_years.setVisible(is_custom)

    def _update_telemetry(self):
        if self.start_time <= 0 or not self.crawler_thread or not self.crawler_thread.isRunning() or self.is_paused:
            return

        elapsed = time.time() - self.start_time
        mins, secs = divmod(int(elapsed), 60)
        time_str = f"{mins:02d}:{secs:02d}"

        v_count = len(self.all_videos)
        if v_count > 0:
            avg_per_vid = elapsed / v_count
            avg_str = f"{avg_per_vid:.1f}s/vídeo"

            remaining_vids = max(0, self.target_video_count - v_count)
            rem_sec = int(remaining_vids * avg_per_vid)
            rem_mins, rem_s = divmod(rem_sec, 60)
            rem_str = f"~{rem_mins:02d}:{rem_s:02d}" if rem_sec > 0 else "Finalizando..."
        else:
            avg_str = "-- s/vídeo"
            rem_str = "Calculando..."

        self.lbl_telemetry.setText(f"⏱️ Tempo: {time_str}  •  ⚡ Média: {avg_str}  •  ⏳ Restante: {rem_str}")

    def _create_bottom_toolbar(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.btn_export_pdf = QPushButton("📑 Exportar PDF (Disponíveis)")
        self.btn_export_pdf.setObjectName("btn_success")
        self.btn_export_pdf.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export_pdf.setToolTip("Exportar relatório executivo em PDF somente com os domínios e perfis disponíveis")
        self.btn_export_pdf.clicked.connect(self._export_pdf)
        layout.addWidget(self.btn_export_pdf)

        self.btn_export_excel = QPushButton("📊 Exportar Excel (.xlsx)")
        self.btn_export_excel.setObjectName("btn_success")
        self.btn_export_excel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export_excel.setToolTip("Exportar planilha Excel com as oportunidades disponíveis")
        self.btn_export_excel.clicked.connect(self._export_excel)
        layout.addWidget(self.btn_export_excel)

        self.btn_export_txt = QPushButton("📝 Exportar TXT")
        self.btn_export_txt.setObjectName("btn_success")
        self.btn_export_txt.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export_txt.setToolTip("Exportar lista formatada em texto simples (.txt) dos domínios disponíveis")
        self.btn_export_txt.clicked.connect(self._export_txt)
        layout.addWidget(self.btn_export_txt)

        self.btn_export_csv = QPushButton("📄 Exportar CSV")
        self.btn_export_csv.setObjectName("btn_success")
        self.btn_export_csv.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export_csv.setToolTip("Exportar lista formatada em CSV dos domínios disponíveis")
        self.btn_export_csv.clicked.connect(self._export_csv)
        layout.addWidget(self.btn_export_csv)

        self.btn_export_json = QPushButton("📋 Exportar JSON")
        self.btn_export_json.setObjectName("btn_success")
        self.btn_export_json.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export_json.setToolTip("Exportar lista formatada em JSON dos domínios disponíveis")
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
            self.telemetry_timer.start()
            return

        search_mode = self.combo_mode.currentData()
        selected_niche = self.combo_niche.currentData() if search_mode == "niches" else None
        selected_subniche = self.combo_subniche.currentData() if search_mode == "niches" else None

        if search_mode == "niches":
            n_name = self.combo_niche.currentText()
            s_name = self.combo_subniche.currentText()
            targets = [f"{n_name} - {s_name}"]
            raw_text = targets[0]
        else:
            raw_text = self.input_target.text().strip()
            if not raw_text:
                msg = "Por favor, digite um canal ou lista de canais (ex: @canal1, @canal2)." if search_mode == "channels" else "Por favor, digite pelo menos uma palavra-chave."
                QMessageBox.warning(self, "Atenção", msg)
                return
            targets = [k.strip() for k in raw_text.replace("\n", ",").replace(";", ",").split(",") if k.strip()]

        selected_lang = self.combo_lang.currentData() if search_mode in ("keywords", "niches") else "pt"
        date_filter = self.combo_date.currentData() if search_mode in ("keywords", "niches") else "all_time"
        
        # Strictly enforce year boundaries if specified
        if search_mode in ("keywords", "niches"):
            if date_filter == "custom_range":
                s_yr = self.spin_year_start.value()
                e_yr = self.spin_year_end.value()
                year_range = (min(s_yr, e_yr), max(s_yr, e_yr))
            elif str(date_filter).isdigit():
                yr = int(date_filter)
                year_range = (yr, yr)
            else:
                year_range = None
        else:
            year_range = None

        min_views = self.get_min_views()
        max_vids = 10000000 if self.chk_unlimited.isChecked() else self.spin_max.value()
        sort_by = self.combo_sort.currentData()
        fast_mode = self.chk_fast_mode.isChecked()
        include_related = self.chk_include_related.isChecked() if search_mode in ("keywords", "niches") else False
        loop_24h = self.chk_mode_24h.isChecked()

        self.is_paused = False
        self.start_time = time.time()
        self.target_video_count = max_vids * len(targets)
        self.telemetry_timer.start()
        self._ui_batch_timer.start()

        self.btn_start.setEnabled(False)
        self.btn_start.setText("🚀 Mineração Ativa")
        self.btn_pause.setEnabled(True)
        self.btn_pause.setText("⏸️ Pausar")
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)

        if search_mode == "niches":
            mode_title = f"nicho [{targets[0]}]"
        elif search_mode == "channels":
            mode_title = f"canais ({len(targets)} canais)"
        else:
            mode_title = f"termos ({len(targets)} termos)"

        filter_details = []
        if min_views > 0:
            filter_details.append(f"Mín. Views: {min_views:,}")
        if year_range:
            filter_details.append(f"Anos: {year_range[0]}-{year_range[1]}")
        if selected_lang == "global" and self.excluded_countries:
            filter_details.append(f"Excluídos: {len(self.excluded_countries)} países")
        details_str = f" | {' • '.join(filter_details)}" if filter_details else ""

        self.status_label.setText(f"Minerando vídeos de {mode_title} (Turbo: {fast_mode}{details_str})...")
        self._append_log(f"--- 🚀 Mineração Iniciada [Modo: {self.combo_mode.currentText()}] ({mode_title} | Turbo: {fast_mode}{details_str}) ---")

        self.crawler_thread = CrawlerThread(
            keywords=targets,
            search_mode=search_mode,
            selected_lang=selected_lang,
            date_filter=date_filter,
            year_range=year_range,
            max_videos=max_vids,
            min_views=min_views,
            sort_by=sort_by,
            fast_mode=fast_mode,
            include_related=include_related,
            excluded_langs=self.excluded_countries,
            loop_24h=loop_24h,
            selected_niche=selected_niche,
            selected_subniche=selected_subniche,
            parent=self
        )
        self.crawler_thread.live_video_analyzed.connect(self._on_live_video_analyzed)
        self.crawler_thread.video_found.connect(self._on_video_found)
        self.crawler_thread.domain_found.connect(self._on_domain_found)
        self.crawler_thread.progress_updated.connect(self._on_progress_updated)
        self.crawler_thread.active_keyword_changed.connect(self._on_active_keyword_changed)
        self.crawler_thread.finished_crawl.connect(self._on_finished_crawl)
        self.crawler_thread.error_occurred.connect(self._on_error_occurred)
        self.crawler_thread.start(QThread.Priority.LowPriority)

        # Start glowing visual pulse animation
        self._pulse_state = True
        self.pulse_timer.start(600)
        self._on_mining_pulse()

    def _on_mining_pulse(self):
        """Pulsing visual animation for the active mining HUD banner to show live activity."""
        if self.is_background_mode or not self.crawler_thread or not self.crawler_thread.isRunning() or self.is_paused:
            return
        
        self._pulse_state = not self._pulse_state
        if self._pulse_state:
            # Active glowing pulse state
            self.active_target_card.setStyleSheet("""
                QFrame#active_target_card {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369A1, stop:0.5 #0284C7, stop:1 #0369A1);
                    border: 2px solid #38BDF8;
                    border-radius: 8px;
                    padding: 6px 12px;
                }
            """)
            self.lbl_active_prefix.setStyleSheet("color: #FFFFFF; font-weight: 900; font-size: 11px; letter-spacing: 0.5px;")
            self.lbl_active_prefix.setText("⚡ MINERANDO AGORA:")
        else:
            # Ambient pulse state
            self.active_target_card.setStyleSheet("""
                QFrame#active_target_card {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0F172A, stop:0.5 #1E293B, stop:1 #0F172A);
                    border: 2px solid #0284C7;
                    border-radius: 8px;
                    padding: 6px 12px;
                }
            """)
            self.lbl_active_prefix.setStyleSheet("color: #38BDF8; font-weight: 800; font-size: 11px; letter-spacing: 0.5px;")
            self.lbl_active_prefix.setText("🔍 MINERANDO AGORA:")

    def _on_active_keyword_changed(self, target: str, category: str, current_idx: int, total_count: int):
        """Update the prominent active keyword HUD display in real-time."""
        self.lbl_active_keyword.setText(f"🎯 \"{target}\"  •  {category}")
        self.lbl_active_progress_pill.setText(f"Alvo {current_idx} de {total_count}")

    def _on_live_video_analyzed(self, url: str, title: str):
        if not self.is_background_mode:
            self.live_video_stream.emit(url, title)

    def _on_toggle_pause(self):
        if not self.crawler_thread or not self.crawler_thread.isRunning():
            return

        if not self.is_paused:
            self.is_paused = True
            self.crawler_thread.pause()
            self.pulse_timer.stop()
            self.btn_pause.setText("▶ Retomar")
            self.btn_start.setEnabled(True)
            self.btn_start.setText("▶ Retomar Busca")
            self.status_label.setText("⏸️ Mineração Pausada. Clique em 'Retomar' para prosseguir.")
            self.lbl_active_prefix.setText("⏸️ MINERAÇÃO PAUSADA:")
            self.lbl_active_prefix.setStyleSheet("color: #F59E0B; font-weight: 800; font-size: 11px; letter-spacing: 0.5px;")
            self.active_target_card.setStyleSheet("""
                QFrame#active_target_card {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E293B, stop:0.5 #334155, stop:1 #1E293B);
                    border: 2px solid #F59E0B;
                    border-radius: 8px;
                    padding: 6px 12px;
                }
            """)
            self._append_log("⏸️ Mineração pausada pelo usuário.")
        else:
            self.is_paused = False
            self.crawler_thread.resume()
            self.pulse_timer.start(600)
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
            self.telemetry_timer.stop()
            self.pulse_timer.stop()
            self.is_paused = False
            self.btn_start.setEnabled(True)
            self.btn_start.setText("🚀 Iniciar Busca")
            self.btn_pause.setEnabled(False)
            self.btn_stop.setEnabled(False)
            self.lbl_active_prefix.setText("⏹️ MINERAÇÃO ENCERRADA:")
            self.lbl_active_prefix.setStyleSheet("color: #94A3B8; font-weight: 800; font-size: 11px; letter-spacing: 0.5px;")
            self.active_target_card.setStyleSheet("""
                QFrame#active_target_card {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0F172A, stop:0.5 #1E293B, stop:1 #0F172A);
                    border: 2px solid #475569;
                    border-radius: 8px;
                    padding: 6px 12px;
                }
            """)
            self._flush_pending_ui_batch()
            self._ui_batch_timer.stop()
            self._trigger_autosave(force=True, include_excel=True)

    def _on_video_found(self, video_dict: Dict[str, Any]):
        v_id = video_dict.get("id")
        if not v_id or v_id in self._seen_video_ids:
            return
        self._seen_video_ids.add(v_id)
        self._pending_videos_buffer.append(video_dict)
        self._processed_videos_counter += 1

        # Preventive Auto-Hygiene routine every 250 videos
        if self._processed_videos_counter % 250 == 0:
            self._preventive_memory_health_check()

        if not self._ui_batch_timer.isActive():
            self._ui_batch_timer.start()

        if not self.is_background_mode:
            self.live_video_stream.emit(video_dict.get("url", ""), video_dict.get("title", ""), video_dict)
        self._append_log(f"📹 Vídeo minerado: {video_dict['title'][:45]}... ({video_dict['metrics']['view_count_formatted']} views)")

    def _on_domain_found(self, domain_dict: Dict[str, Any]):
        d_root = (domain_dict.get("root_domain") or domain_dict.get("display_name") or "").strip().lower()
        v_id = domain_dict.get("video_id", "")
        if not d_root:
            return
        key = (d_root, v_id)
        if key in self._seen_domain_keys:
            return
        self._seen_domain_keys.add(key)
        self._pending_domains_buffer.append(domain_dict)

        badge = domain_dict.get("badge_icon", "")
        status = domain_dict.get("status", "")
        name = domain_dict.get("display_name") or domain_dict.get("root_domain", "")
        self._append_log(f"  {badge} {name} -> {status} ({domain_dict.get('source_location')})")

        if not self._ui_batch_timer.isActive():
            self._ui_batch_timer.start()

    def _flush_pending_ui_batch(self):
        """High-performance batch flusher: updates tables and stats in batches to prevent UI freeze."""
        has_new_videos = bool(self._pending_videos_buffer)
        has_new_domains = bool(self._pending_domains_buffer)

        if not has_new_videos and not has_new_domains:
            if not self.crawler_thread or not self.crawler_thread.isRunning():
                self._ui_batch_timer.stop()
            return

        if has_new_videos:
            batch_v = self._pending_videos_buffer[:]
            self._pending_videos_buffer.clear()
            self.all_videos.extend(batch_v)

            if not self.is_background_mode:
                self.all_videos.sort(key=lambda x: x.get("metrics", {}).get("view_count", 0), reverse=True)
                self.video_table.set_videos(self.all_videos)

        if has_new_domains:
            batch_d = self._pending_domains_buffer[:]
            self._pending_domains_buffer.clear()
            self.all_domains.extend(batch_d)

            for d in batch_d:
                if d.get("status") == "Disponível" and not d.get("is_instagram"):
                    self.seo_table.add_domain(d)

            if not self.is_background_mode:
                self.domain_table.set_domains(self.all_domains)

        if not self.is_background_mode:
            self._update_stat_cards()

        self._trigger_autosave(force=False, include_excel=False)
        QApplication.processEvents()

    def _preventive_memory_health_check(self):
        """Preventive health routine to free unused RAM and maintain long-term stability."""
        try:
            collected = gc.collect()
            if self._processed_videos_counter % 1000 == 0:
                self._append_log(f"🧹 [Auto-Higiene Preventiva] Coleta de lixo executada ({self._processed_videos_counter:,} vídeos processados | {collected} objetos liberados).")
        except Exception:
            pass

    def _trigger_autosave(self, force: bool = False, include_excel: bool = False):
        """Perform automatic atomic session save to disk with preventive throttling."""
        if self.all_videos or self.all_domains:
            raw = self.input_target.text() if hasattr(self, 'input_target') else ""
            kws = [k.strip() for k in raw.split(",") if k.strip()]
            self.autosave_manager.save_session(
                self.all_videos,
                self.all_domains,
                kws,
                force=force,
                include_excel=include_excel
            )

    def _restore_previous_session_if_any(self):
        """Automatically restore previously mined data if an autosave session exists."""
        if self.autosave_manager.has_saved_session():
            saved = self.autosave_manager.load_saved_session()
            if saved and (saved.get("videos") or saved.get("domains")):
                vids = saved.get("videos", [])
                doms = saved.get("domains", [])
                time_saved = saved.get("formatted_time", "anteriormente")

                self.all_videos = vids
                self.all_domains = doms
                self._seen_video_ids = {v.get("id") for v in vids if v.get("id")}
                self._seen_domain_keys = {
                    ((d.get("root_domain") or d.get("display_name") or "").strip().lower(), d.get("video_id", ""))
                    for d in doms if d.get("root_domain") or d.get("display_name")
                }
                self.video_table.set_videos(self.all_videos)
                self.domain_table.set_domains(self.all_domains)
                self.seo_table.set_domains(self.all_domains)
                self._update_stat_cards()
                self._append_log(f"📂 Sessão anterior recuperada com sucesso ({len(vids)} vídeos, {len(doms)} domínios salvos em {time_saved}).")

    def _on_progress_updated(self, current: int, total: int, message: str):
        if total > 0:
            percent = min(100, int((current / total) * 100))
            self.progress_bar.setValue(percent)
        self.status_label.setText(message)
        # Only overwrite the active target HUD banner if the crawl is not actively scanning
        if not (self.crawler_thread and self.crawler_thread.isRunning()):
            if any(token in message for token in ["ℹ️", "🏁", "Nenhum vídeo", "concluída", "finalizado"]):
                self.lbl_active_keyword.setText(message)

    def _on_finished_crawl(self, summary: Dict[str, Any]):
        self.btn_start.setEnabled(True)
        self.btn_start.setText("🚀 Iniciar Busca")
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.is_paused = False
        self.telemetry_timer.stop()
        self.pulse_timer.stop()
        self.progress_bar.setValue(100)

        # Flush any remaining buffer items and force final save with Excel
        self._flush_pending_ui_batch()
        self._ui_batch_timer.stop()
        self._trigger_autosave(force=True, include_excel=True)

        elapsed = time.time() - self.start_time if self.start_time > 0 else 0
        mins, secs = divmod(int(elapsed), 60)
        time_str = f"{mins:02d}:{secs:02d}"
        avg_str = f"{(elapsed / max(1, len(self.all_videos))):.1f}s/vídeo" if self.all_videos else "0s"

        total_vids = len(self.all_videos)
        total_doms = len(self.all_domains)
        avail_doms = summary.get("available_domains", 0)

        self.lbl_telemetry.setText(f"✅ Concluído em {time_str}  •  ⚡ Média: {avg_str}")

        if total_vids == 0:
            # Explicit clear message when no videos are found
            self.lbl_active_prefix.setText("ℹ️ SEM RESULTADOS:")
            self.lbl_active_prefix.setStyleSheet("color: #F59E0B; font-weight: 800; font-size: 11px; letter-spacing: 0.5px;")
            self.lbl_active_keyword.setText("O YouTube não encontrou nenhum vídeo adicional para os termos/filtros informados.")
            self.lbl_active_progress_pill.setText("Finalizado")
            self.active_target_card.setStyleSheet("""
                QFrame#active_target_card {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #78350F, stop:0.5 #92400E, stop:1 #78350F);
                    border: 2px solid #F59E0B;
                    border-radius: 8px;
                    padding: 6px 12px;
                }
            """)
            self.status_label.setText("Busca finalizada: O YouTube não possui mais vídeos com os filtros atuais.")
            self._append_log(f"⚠️ Varredura finalizada ({time_str}): Nenhum vídeo retornado pelo YouTube.")
            QMessageBox.information(
                self,
                "Busca Finalizada (Sem Novos Vídeos)",
                f"A varredura foi concluída!\n\n"
                f"O YouTube não encontrou mais vídeos para os termos ou canais pesquisados com os filtros atuais.\n\n"
                f"💡 Sugestões:\n"
                f"• Verifique se a palavra-chave ou @handle do canal está digitada corretamente.\n"
                f"• Reduza ou zere o filtro de 'Mín. Views'.\n"
                f"• Se usou filtro de data específico (ex: este ano), altere para 'Todo o Período'."
            )
        else:
            self.lbl_active_prefix.setText("✅ CONCLUÍDO:")
            self.lbl_active_prefix.setStyleSheet("color: #34D399; font-weight: 800; font-size: 11px; letter-spacing: 0.5px;")
            self.lbl_active_keyword.setText(f"Varredura finalizada: Todos os {total_vids} vídeos disponíveis no YouTube foram minerados!")
            self.lbl_active_progress_pill.setText("Concluído")
            self.active_target_card.setStyleSheet("""
                QFrame#active_target_card {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #064E3B, stop:0.5 #065F46, stop:1 #064E3B);
                    border: 2px solid #10B981;
                    border-radius: 8px;
                    padding: 6px 12px;
                }
            """)
            self.status_label.setText(f"Varredura 100% finalizada: {total_vids} vídeos e {total_doms} oportunidades mineradas até o fim.")
            self._append_log(f"✅ Mineração finalizada com sucesso ({time_str})! {total_vids} vídeos minerados | Disponíveis: {avail_doms} | Total: {total_doms}")
            QMessageBox.information(
                self,
                "Mineração Concluída (Fim dos Vídeos)",
                f"Varredura 100% finalizada com sucesso!\n\n"
                f"Todos os vídeos disponíveis na plataforma para esta pesquisa foram minerados até o final.\n\n"
                f"• Tempo total: {time_str} (Média: {avg_str})\n"
                f"• Vídeos analisados no YouTube: {total_vids:,}\n"
                f"• Domínios / Contas IG identificadas: {total_doms:,}\n"
                f"• Oportunidades DISPONÍVEIS para compra/claim: {avail_doms:,}\n\n"
                f"💾 Cópia de segurança auto-salva na pasta Downloads."
            )

    def _on_error_occurred(self, err_msg: str):
        self.btn_start.setEnabled(True)
        self.btn_start.setText("🚀 Iniciar Busca")
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.is_paused = False
        self.telemetry_timer.stop()
        self.pulse_timer.stop()
        self.status_label.setText(f"Erro: {err_msg}")
        self.lbl_active_keyword.setText("❌ Mineração interrompida por erro.")
        self.lbl_active_prefix.setText("❌ ERRO:")
        self.lbl_active_prefix.setStyleSheet("color: #F87171; font-weight: 800; font-size: 11px; letter-spacing: 0.5px;")
        self.active_target_card.setStyleSheet("""
            QFrame#active_target_card {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #450A0A, stop:0.5 #7F1D1D, stop:1 #450A0A);
                border: 2px solid #EF4444;
                border-radius: 8px;
                padding: 6px 12px;
            }
        """)
        self._append_log(f"❌ Erro na varredura: {err_msg}")
        if self.isVisible() and not self.isMinimized():
            QMessageBox.critical(self, "Erro na Varredura", f"Ocorreu um erro:\n{err_msg}")

    def _update_stat_cards(self):
        total_vids = len(self.all_videos)
        total_views = sum(v.get("metrics", {}).get("view_count", 0) for v in self.all_videos)
        
        # Group domains to get exact unique opportunities counts
        unique_doms_set = set()
        unique_avail_domains_set = set()
        unique_avail_instagram_set = set()
        for d in self.all_domains:
            key = (d.get("root_domain") or d.get("display_name") or "").strip().lower()
            if key:
                unique_doms_set.add(key)
                st = d.get("status", "")
                # Strictly Available/Expired (excludes Inativo, Ativo, and Verificar)
                if st == "Disponível" and st != "Inativo" and st != "Ativo" and st != "Verificar":
                    if d.get("is_instagram"):
                        unique_avail_instagram_set.add(key)
                    else:
                        unique_avail_domains_set.add(key)

        self.val_videos.setText(str(total_vids))
        self.val_views.setText(format_number(total_views))
        self.val_domains.setText(str(len(unique_doms_set)))
        self.val_avail.setText(str(len(unique_avail_domains_set)))
        self.val_instagram.setText(str(len(unique_avail_instagram_set)))

    def _append_log(self, text: str):
        self.log_view.appendPlainText(text)

    def _on_navigate_requested(self, url: str):
        self.navigate_url_requested.emit(url)

    def _on_open_video_requested(self, url: str):
        """Open YouTube video directly in default external browser (Chrome/Edge/Firefox) without leaving results."""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _on_buy_domain_requested(self, url: str):
        """Open domain registration or Instagram claim URL directly in user's default external browser."""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _on_filter_videos_by_domain(self, domain_name: str):
        """Switch to videos tab and filter strictly for all videos containing the specified domain."""
        self.results_tabs.setCurrentIndex(0) # Tab 0: Videos
        self.video_table.filter_by_exact_domain(domain_name)
        self.status_label.setText(f"Exibindo todos os vídeos com o link '{domain_name}'...")
        self._append_log(f"🔍 Filtrando vídeos com o link '{domain_name}' na tabela principal.")

    def _on_domains_excluded(self, excluded_targets: Any):
        """Immediately remove one or more excluded domains from tables, memory and session storage."""
        from core.domain_extractor import parse_multiple_exclusion_targets
        clean_targets = set(parse_multiple_exclusion_targets(excluded_targets))
        if not clean_targets:
            return

        # 1. Filter all_domains
        self.all_domains = [
            d for d in self.all_domains
            if (d.get("display_name") or "").strip().lower().replace("📸 @", "").replace("@", "") not in clean_targets
            and (d.get("root_domain") or "").strip().lower().replace("@", "") not in clean_targets
        ]
        self.domain_table.set_domains(self.all_domains)

        for target in clean_targets:
            if target in self.seo_table.raw_seo_data:
                del self.seo_table.raw_seo_data[target]
        self.seo_table._apply_filter_and_render()

        # 2. Filter video internal domain references
        for v in self.all_videos:
            v_doms = v.get("domains", [])
            v["domains"] = [
                d for d in v_doms
                if (d.get("display_name") or "").strip().lower().replace("📸 @", "").replace("@", "") not in clean_targets
                and (d.get("root_domain") or "").strip().lower().replace("@", "") not in clean_targets
            ]
        self.video_table.set_videos(self.all_videos)

        self._update_stat_cards()
        self._trigger_autosave()
        if len(clean_targets) == 1:
            item = next(iter(clean_targets))
            self._append_log(f"🚫 '{item}' adicionado à Lista de Exclusão e removido dos resultados.")
            self.status_label.setText(f"Domínio '{item}' adicionado à lista de exclusão.")
        else:
            self._append_log(f"🚫 {len(clean_targets)} domínios/perfis adicionados à Lista de Exclusão e removidos dos resultados.")
            self.status_label.setText(f"{len(clean_targets)} itens adicionados à lista de exclusão.")

    def _on_domain_excluded(self, excluded_target: str):
        self._on_domains_excluded([excluded_target])

    def _clear_results(self):
        self.all_videos.clear()
        self.all_domains.clear()
        self.video_table.set_videos([])
        self.domain_table.set_domains([])
        self.seo_table.clear_domains()
        if self.crawler_thread and self.crawler_thread.crawler:
            self.crawler_thread.crawler.clear_seen_videos()
        self.log_view.clear()
        self.progress_bar.setValue(0)
        self.lbl_active_keyword.setText("Aguardando início da mineração...")
        self.lbl_active_progress_pill.setText("Termo -- / --")
        self.lbl_telemetry.setText("⏱️ Tempo: 00:00  •  ⚡ Média: -- s/vídeo  •  ⏳ Restante: --")
        self.val_videos.setText("0")
        self.val_views.setText("0")
        self.val_domains.setText("0")
        self.val_avail.setText("0")
        self.val_instagram.setText("0")
        self._update_stat_cards()
        self.autosave_manager.clear_saved_session()
        self.status_label.setText("Resultados limpos e sessão anterior resetada.")

    def _export_pdf(self):
        avail_cnt = sum(1 for d in self.all_domains if d.get("status") == "Disponível")
        if avail_cnt == 0:
            QMessageBox.warning(self, "Exportar PDF", "Nenhum domínio expirado / disponível foi encontrado para exportação.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Relatório PDF (Disponíveis)", "Relatorio_YouTube_Espiao_Disponiveis.pdf", "PDF Files (*.pdf)")
        if path:
            try:
                DataExporter.export_to_pdf(path, self.all_domains, self.all_videos)
                QMessageBox.information(self, "Sucesso", f"Relatório PDF com {avail_cnt} oportunidades disponíveis salvo em:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro na Exportação", str(e))

    def _export_excel(self):
        avail_cnt = sum(1 for d in self.all_domains if d.get("status") == "Disponível")
        if avail_cnt == 0:
            QMessageBox.warning(self, "Exportar Excel", "Nenhum domínio expirado / disponível foi encontrado para exportação.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Relatório Excel (Disponíveis)", "Relatorio_YouTube_Espiao_Disponiveis.xlsx", "Excel Files (*.xlsx)")
        if path:
            try:
                DataExporter.export_to_excel(path, self.all_domains, self.all_videos)
                QMessageBox.information(self, "Sucesso", f"Planilha Excel com {avail_cnt} oportunidades disponíveis salva em:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro na Exportação", str(e))

    def _export_txt(self):
        avail_cnt = sum(1 for d in self.all_domains if d.get("status") == "Disponível")
        if avail_cnt == 0:
            QMessageBox.warning(self, "Exportar TXT", "Nenhum domínio expirado / disponível foi encontrado para exportação.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Lista TXT (Disponíveis)", "Dominios_Disponiveis.txt", "Text Files (*.txt)")
        if path:
            try:
                DataExporter.export_to_txt(path, self.all_domains, self.all_videos)
                QMessageBox.information(self, "Sucesso", f"Lista TXT com {avail_cnt} oportunidades disponíveis salva em:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro na Exportação", str(e))

    def _export_csv(self):
        avail_cnt = sum(1 for d in self.all_domains if d.get("status") == "Disponível")
        if avail_cnt == 0:
            QMessageBox.warning(self, "Exportar CSV", "Nenhum domínio expirado / disponível foi encontrado para exportação.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Oportunidades CSV (Disponíveis)", "Oportunidades_Disponiveis.csv", "CSV Files (*.csv)")
        if path:
            try:
                DataExporter.export_to_csv(path, self.all_domains)
                QMessageBox.information(self, "Sucesso", f"Arquivo CSV com {avail_cnt} oportunidades disponíveis salvo em:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro na Exportação", str(e))

    def _export_json(self):
        avail_cnt = sum(1 for d in self.all_domains if d.get("status") == "Disponível")
        if avail_cnt == 0:
            QMessageBox.warning(self, "Exportar JSON", "Nenhum domínio expirado / disponível foi encontrado para exportação.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Dados JSON (Disponíveis)", "Dados_Disponiveis.json", "JSON Files (*.json)")
        if path:
            try:
                DataExporter.export_to_json(path, self.all_domains, self.all_videos)
                QMessageBox.information(self, "Sucesso", f"Arquivo JSON com {avail_cnt} oportunidades disponíveis salvo em:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro na Exportação", str(e))
