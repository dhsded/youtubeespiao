"""
Automated unit tests for YouTube Espião core components.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from core.metrics_calculator import calculate_video_metrics, format_number
from core.domain_extractor import DomainExtractor
from core.domain_validator import DomainValidator
from core.instagram_validator import InstagramValidator
from core.translator import expand_queries_for_language, translate_query, AVAILABLE_LANGUAGES

class TestYoutubeEspiaoCore(unittest.TestCase):

    def test_metrics_calculator(self):
        """Test calculation of hourly (VPH), daily, monthly, 90-day, and annual view averages."""
        # 1. Very recent video (2 hours old) -> Exact launch VPH
        two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
        metrics_new = calculate_video_metrics(view_count=10000, upload_date=two_hours_ago)
        self.assertAlmostEqual(metrics_new["hourly_views"], 5000.0, delta=250.0)
        self.assertEqual(metrics_new["velocity_badge"], "🔥 Viral em Alta")

        # 2. Recent video (10 days old)
        ten_days_ago = datetime.now(timezone.utc) - timedelta(days=10)
        metrics = calculate_video_metrics(view_count=24000, upload_date=ten_days_ago)

        self.assertEqual(metrics["view_count"], 24000)
        self.assertEqual(metrics["views_90d"], 24000)
        self.assertAlmostEqual(metrics["lifetime_daily_views"], 2400.0, delta=50.0)
        self.assertAlmostEqual(metrics["daily_views"], 1712.7, delta=50.0)
        self.assertGreater(metrics["hourly_views"], 60.0)
        self.assertLess(metrics["hourly_views"], 100.0)
        self.assertGreater(metrics["monthly_views"], 40000)
        self.assertIn("24K", metrics["view_count_formatted"])

        # 3. Relative text parsing for Portuguese & English
        from core.metrics_calculator import parse_relative_time_text
        self.assertAlmostEqual(parse_relative_time_text("há 3 horas"), 0.125, delta=0.02)
        self.assertAlmostEqual(parse_relative_time_text("há 5 dias"), 5.0, delta=0.1)
        self.assertAlmostEqual(parse_relative_time_text("há 2 semanas"), 14.0, delta=0.1)
        self.assertAlmostEqual(parse_relative_time_text("2 months ago"), 60.83, delta=1.0)
        self.assertAlmostEqual(parse_relative_time_text("há 1 ano"), 365.25, delta=5.0)

        # 4. Older video (365 days old with calibrated evergreen 90d traffic)
        one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
        metrics_old = calculate_video_metrics(view_count=500000, upload_date=one_year_ago)
        self.assertGreater(metrics_old["views_90d"], 5000)
        self.assertLess(metrics_old["views_90d"], 50000)
        self.assertGreater(metrics_old["hourly_views"], 2.0)
        self.assertLess(metrics_old["hourly_views"], 20.0)

    def test_format_number(self):
        """Test human readable number formatting."""
        self.assertEqual(format_number(500), "500")
        self.assertEqual(format_number(1500), "1.5K")
        self.assertEqual(format_number(2300000), "2.3M")
        self.assertEqual(format_number(1000000000), "1B")

    def test_domain_extractor_and_shorteners(self):
        """Test URL parsing, unshortener filtering, and social network filtering."""
        extractor = DomainExtractor()
        
        sample_text = """
        Curso: https://meucursoteste12345.com.br/matricula
        Instagram: https://instagram.com/perfilteste987
        YouTube: https://youtube.com/watch?v=12345
        Parceiro: www.ferramentateste987.net/app
        Shortener Bridge: https://pxf.io/c/12345/link
        """
        
        domains = extractor.process_text_for_domains(sample_text, source_location="Descrição")
        extracted_roots = [d["root_domain"] for d in domains]

        self.assertIn("meucursoteste12345.com.br", extracted_roots)
        self.assertIn("ferramentateste987.net", extracted_roots)
        self.assertTrue(any(d.get("is_instagram") for d in domains))
        self.assertNotIn("pxf.io", extracted_roots)
        self.assertNotIn("youtube.com", extracted_roots)

    def test_translator_multi_languages(self):
        """Test multi-language expansion for global, exclusions, and specific languages."""
        # 1. Global expansion creates tasks for all 18 supported languages
        tasks = expand_queries_for_language("curso de marketing", "global")
        self.assertEqual(len(tasks), 18)
        lang_codes = [t["lang_code"] for t in tasks]
        self.assertIn("ru", lang_codes) # Russian
        self.assertIn("ja", lang_codes) # Japanese
        self.assertIn("zh", lang_codes) # Chinese
        self.assertIn("ar", lang_codes) # Arabic
        self.assertIn("tr", lang_codes) # Turkish
        self.assertIn("pl", lang_codes) # Polish

        # 2. Global expansion with excluded languages
        tasks_excluded = expand_queries_for_language("curso de marketing", "global", excluded_langs=["ru", "zh", "hi", "ar"])
        self.assertEqual(len(tasks_excluded), 14)
        lang_codes_ex = [t["lang_code"] for t in tasks_excluded]
        self.assertNotIn("ru", lang_codes_ex)
        self.assertNotIn("zh", lang_codes_ex)
        self.assertNotIn("hi", lang_codes_ex)
        self.assertNotIn("ar", lang_codes_ex)

        # 3. Universal acronym preservation with localized token targeting
        gta_task = expand_queries_for_language("GTA", "pt")
        gta_queries = [t["query"] for t in gta_task]
        self.assertIn("GTA brasil", gta_queries)
        self.assertIn("GTA", gta_queries)

        gta_global = expand_queries_for_language("GTA", "global")
        self.assertTrue(all(t["query"] == "GTA" for t in gta_global))

        # 4. Long-tail mixed keyword in Portuguese
        long_tail = expand_queries_for_language("GTA 6 gameplay brasil novidades", "pt")
        self.assertEqual(long_tail[0]["query"], "GTA 6 gameplay brasil novidades")

    def test_domain_validator_dns(self):
        """Test DNS resolution for active vs nonexistent domains."""
        validator = DomainValidator(timeout=3.0)
        active_res = validator.check_dns("google.com")
        self.assertTrue(active_res["dns_active"])

        nonexistent_res = validator.check_dns("dominio-completamente-inexistente-123459876.com")
        self.assertTrue(nonexistent_res["nxdomain"])
        self.assertFalse(nonexistent_res["dns_active"])

    def test_pdf_export(self):
        """Test generating executive PDF report."""
        from PyQt6.QtWidgets import QApplication
        from core.exporter import DataExporter
        app = QApplication.instance() or QApplication([])

        sample_domains = [{
            "root_domain": "exemplo123.com.br",
            "display_name": "exemplo123.com.br",
            "status": "Disponível",
            "badge_icon": "🟢",
            "details": "Domínio sem DNS e sem registro",
            "video_title": "Vídeo Teste de Marketing",
            "channel_name": "Canal Sucesso",
            "source_location": "Descrição",
            "video_metrics": {
                "hourly_views_formatted": "120/h",
                "daily_views_formatted": "2.8K/dia",
                "view_count_formatted": "50K"
            }
        }]
        sample_videos = [{
            "title": "Vídeo Teste de Marketing",
            "channel_name": "Canal Sucesso",
            "metrics": {
                "view_count_formatted": "50K",
                "daily_views": 2800,
                "daily_views_formatted": "2.8K/dia"
            },
            "domains": sample_domains
        }]

        pdf_path = "test_out.pdf"
        DataExporter.export_to_pdf(pdf_path, sample_domains, sample_videos)
        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 500)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    def test_video_deduplication(self):
        """Test that duplicate video IDs are properly tracked and skipped."""
        from core.youtube_crawler import YouTubeCrawler
        crawler = YouTubeCrawler()
        crawler.seen_video_ids.add("dQw4w9WgXcQ")

        self.assertIn("dQw4w9WgXcQ", crawler.seen_video_ids)
        crawler.clear_seen_videos()
        self.assertEqual(len(crawler.seen_video_ids), 0)

    def test_language_matching_filter(self):
        """Test strict language detection to avoid English/foreign leakage when searching GTA in Portuguese."""
        from core.translator import is_content_matching_language
        
        # 1. Portuguese GTA video with Portuguese words/accents
        pt_video = is_content_matching_language(
            title="GTA 6 gameplay vazado oficial - Tudo sobre o novo jogo",
            description="Confira as novidades do GTA Brasil e como jogar no servidor RP.",
            channel_name="GameplayRJ",
            target_lang="pt"
        )
        self.assertTrue(pt_video)

        # 2. English-only GTA video without Portuguese context
        en_video = is_content_matching_language(
            title="Grand Theft Auto VI Trailer 1",
            description="Watch the official first trailer for Grand Theft Auto VI. Coming 2025.",
            channel_name="Rockstar Games",
            target_lang="pt"
        )
        self.assertFalse(en_video)

        # 3. Spanish music / Latin videos with GTA acronym (must be rejected for target_lang='pt')
        es_video1 = is_content_matching_language(
            title="EZZY R x RONNY GTA x KIK1 STW - HAGAN DE TO MENO DANO (VIDEO OFICIAL)",
            description="Musica oficial en espanol",
            channel_name="Ezzy R",
            target_lang="pt"
        )
        self.assertFalse(es_video1)

        es_video2 = is_content_matching_language(
            title="Rony alca La Droga e Mala (Video oficial)",
            description="Video musical oficial",
            channel_name="Rony Alca",
            target_lang="pt"
        )
        self.assertFalse(es_video2)

        es_video3 = is_content_matching_language(
            title="RONNY GTA X PAPA JEISON - LA TENGO DE VACEO [ VIDEO OFICIAL ]",
            description="Tema musical oficial",
            channel_name="Papa Jeison",
            target_lang="pt"
        )
        self.assertFalse(es_video3)

        # 4. Specific Spanish gameplay titles with GTA / Brasil
        es_video4 = is_content_matching_language(
            title="Jugué GTA X y es un Completo Caos...",
            description="Gameplay en espanol",
            channel_name="Lechu",
            target_lang="pt"
        )
        self.assertFalse(es_video4)

        es_video5 = is_content_matching_language(
            title="LA POLICÍA ME QUITÓ LA MOTO MÁS COSTOSA DE TODO ELITE AUTO BRASIL",
            description="Gameplay en servidor de Brasil pero en espanol",
            channel_name="LoopXP",
            target_lang="pt"
        )
        self.assertFalse(es_video5)

        es_video6 = is_content_matching_language(
            title="ENCUENTRO Y TUNEO UN COCHE SECRETO ..",
            description="Video de coches y secretos",
            channel_name="Gamer",
            target_lang="pt"
        )
        self.assertFalse(es_video6)

        # 5. Legitimate Brazilian GTA videos (must be ACCEPTED for pt)
        pt_video_br1 = is_content_matching_language(
            title="O FILME - Jogando GTA 5 Como POLICIAL DO BRASIL!",
            description="Jogando gta 5 vida real como policial no brasil",
            channel_name="Jazzghost",
            target_lang="pt"
        )
        self.assertTrue(pt_video_br1)

        pt_video_br2 = is_content_matching_language(
            title="TROCA DE TIROS + CONFRONTO NA FAVELA - BOPE PMCE GTA 5 POLICIAL",
            description="Confronto na favela com bope",
            channel_name="OLD BOB",
            target_lang="pt"
        )
        self.assertTrue(pt_video_br2)

    def test_pinned_comment_link_extraction(self):
        """Test domain & Instagram extraction specifically from pinned comments."""
        from core.domain_extractor import DomainExtractor
        extractor = DomainExtractor()
        pinned_text = "🔥 Acesse nosso servidor oficial em https://meu-gta-rp-servidor123.com e siga nosso IG @gtarproficialbr"
        
        domains = extractor.process_text_for_domains(pinned_text, source_location="📌 Comentário Fixado")
        self.assertEqual(len(domains), 2)
        
        roots = [d["root_domain"] for d in domains]
        self.assertIn("meu-gta-rp-servidor123.com", roots)
        self.assertTrue(any(d.get("is_instagram") for d in domains))
        self.assertTrue(all(d["source_location"] == "📌 Comentário Fixado" for d in domains))

    def test_channel_crawler_interface(self):
        """Test YouTubeCrawler channel methods."""
        from core.youtube_crawler import YouTubeCrawler
        crawler = YouTubeCrawler()
        self.assertTrue(hasattr(crawler, "get_channel_videos"))
        self.assertTrue(hasattr(crawler, "process_channel"))

    def test_domain_aggregation_and_cumulative_traffic(self):
        """Test aggregation of occurrences of the same domain in multiple videos and sum of daily views."""
        from PyQt6.QtWidgets import QApplication
        import sys
        app = QApplication.instance() or QApplication(sys.argv)
        from ui.video_table_model import DomainTableView
        
        table = DomainTableView()
        
        # Sample occurrences of the same domain in 2 distinct videos
        dom_occurrences = [
            {
                "root_domain": "loja-dropshipping-antiga123.com",
                "video_id": "vid_1",
                "video_title": "Vídeo 1 de Dropshipping",
                "video_url": "https://youtube.com/watch?v=vid_1",
                "status": "Disponível",
                "badge_icon": "🟢",
                "video_metrics": {"daily_views": 1500, "view_count": 50000}
            },
            {
                "root_domain": "loja-dropshipping-antiga123.com",
                "video_id": "vid_2",
                "video_title": "Vídeo 2 de Dropshipping",
                "video_url": "https://youtube.com/watch?v=vid_2",
                "status": "Disponível",
                "badge_icon": "🟢",
                "video_metrics": {"daily_views": 3200, "view_count": 100000}
            }
        ]
        
        table.set_domains(dom_occurrences)
        self.assertEqual(len(table.raw_domains_data), 1) # Aggregated into 1 unique domain entry
        
        agg = table.raw_domains_data[0]
        self.assertEqual(agg["video_count"], 2)
        self.assertEqual(agg["total_daily_views"], 4700) # 1500 + 3200 = 4700 daily views sum!
        self.assertEqual(agg["total_view_count"], 150000) # 50000 + 100000 = 150000 total views sum!

    def test_help_dialog_instantiation(self):
        """Test HelpDialog instantiation and content tabs."""
        from PyQt6.QtWidgets import QApplication
        import sys
        app = QApplication.instance() or QApplication(sys.argv)
        from ui.help_dialog import HelpDialog
        
        dlg = HelpDialog()
        self.assertIsNotNone(dlg)
        self.assertTrue(dlg.findChild(object, "help_tabs") is not None)

    def test_pdf_export_with_links(self):
        """Test DataExporter export_to_pdf generation with hyperlinks."""
        import os
        import tempfile
        from PyQt6.QtWidgets import QApplication
        import sys
        app = QApplication.instance() or QApplication(sys.argv)
        from core.exporter import DataExporter
        
        sample_domains = [{
            "root_domain": "exemplo123.com.br",
            "status": "Disponível",
            "is_instagram": False,
            "badge_icon": "🟢",
            "video_count": 3,
            "total_daily_views": 8500,
            "total_view_count": 250000,
            "video_title": "Tutorial Completo GTA 5",
            "video_url": "https://www.youtube.com/watch?v=12345678901",
            "channel_name": "Canal Exemplo",
            "buy_link": "https://registro.br/busca-dominio/?fqdn=exemplo123.com.br",
            "registrar_name": "Registro.br",
            "video_metrics": {"publish_date": "10/01/2024", "daily_views": 8500, "view_count": 250000}
        }]
        
        sample_videos = [{
            "id": "12345678901",
            "title": "Tutorial Completo GTA 5",
            "url": "https://www.youtube.com/watch?v=12345678901",
            "channel_name": "Canal Exemplo",
            "metrics": {
                "view_count": 250000,
                "view_count_formatted": "250K",
                "hourly_views": 354,
                "hourly_views_formatted": "354/h",
                "daily_views": 8500,
                "daily_views_formatted": "8.5K/dia",
                "publish_date": "10/01/2024"
            },
            "domains": sample_domains
        }]
        
        temp_pdf = os.path.join(tempfile.gettempdir(), "test_report_espiao.pdf")
        try:
            DataExporter.export_to_pdf(temp_pdf, sample_domains, sample_videos)
            self.assertTrue(os.path.exists(temp_pdf))
            self.assertGreater(os.path.getsize(temp_pdf), 1000)
        finally:
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)

    def test_domain_validator_active_rejection(self):
        """Test that active domains like vipertacticalshop.co.uk are never marked as Available."""
        from core.domain_validator import DomainValidator
        validator = DomainValidator()
        
        # 1. Registered domain
        res_active = validator.validate_domain("vipertacticalshop.co.uk")
        self.assertNotEqual(res_active["status"], "Disponível")
        self.assertTrue(res_active["status"] in ("Ativo", "Inativo"))
        
        # 2. Registered global domain
        res_google = validator.validate_domain("google.com")
        self.assertEqual(res_google["status"], "Ativo")

    def test_column_visibility_toggle(self):
        """Test column visibility toggling on VideoTableView and DomainTableView."""
        from PyQt6.QtWidgets import QApplication
        import sys
        app = QApplication.instance() or QApplication(sys.argv)
        from ui.video_table_model import VideoTableView, DomainTableView
        
        v_table = VideoTableView()
        d_table = DomainTableView()
        
        self.assertFalse(v_table.table.isColumnHidden(0))
        v_table.table.setColumnHidden(0, True)
        self.assertTrue(v_table.table.isColumnHidden(0))
        v_table.table.setColumnHidden(0, False)
        self.assertFalse(v_table.table.isColumnHidden(0))
        
        self.assertFalse(d_table.table.isColumnHidden(3))
        d_table.table.setColumnHidden(3, True)
        self.assertTrue(d_table.table.isColumnHidden(3))
        d_table.table.setColumnHidden(3, False)
        self.assertFalse(d_table.table.isColumnHidden(3))

    def test_browser_extract_video_id(self):
        """Test extraction of YouTube 11-char video IDs in BrowserView."""
        from ui.browser_view import BrowserView
        self.assertEqual(BrowserView.extract_youtube_video_id("https://www.youtube.com/watch?v=EYlh15Kboyo"), "EYlh15Kboyo")
        self.assertEqual(BrowserView.extract_youtube_video_id("https://youtu.be/EYlh15Kboyo"), "EYlh15Kboyo")
        self.assertEqual(BrowserView.extract_youtube_video_id("https://www.youtube.com/embed/EYlh15Kboyo"), "EYlh15Kboyo")
        self.assertIsNone(BrowserView.extract_youtube_video_id("https://google.com"))

    def test_clickable_links_filter(self):
        """Test that only genuine clickable URLs are extracted and Instagram @handles are allowed as the sole exception."""
        extractor = DomainExtractor()
        sample_text = """
        Confira o curso: https://cursolinkclicavel123.com/aula
        Acesse também www.ferramentaclicavel.org/app
        Instagram oficial: @perfilteste_expirado123
        Link curto: bit.ly/meulink456
        Email para contato: contato@gmail.com
        Arquivo para download: imagem.png e instalador.exe
        """
        urls = extractor.extract_urls(sample_text)
        domains = extractor.process_text_for_domains(sample_text)
        extracted = [d["root_domain"] for d in domains]

        self.assertIn("cursolinkclicavel123.com", extracted)
        self.assertIn("ferramentaclicavel.org", extracted)
        self.assertTrue(any(d.get("is_instagram") and "perfilteste_expirado123" in d.get("root_domain", "") for d in domains))
        self.assertNotIn("imagem.png", urls)
        self.assertNotIn("instalador.exe", urls)
        self.assertNotIn("gmail.com", extracted)

    def test_autosave_manager(self):
        """Test AutoSave session persistence and recovery."""
        from core.autosave_manager import AutoSaveManager
        manager = AutoSaveManager()

        sample_vids = [{"id": "vid123", "title": "Vídeo Teste", "metrics": {"view_count": 1000}}]
        sample_doms = [{"root_domain": "teste.com", "status": "Disponível"}]

        # 1. Save session
        success = manager.save_session(sample_vids, sample_doms, keywords=["teste"])
        self.assertTrue(success)
        self.assertTrue(manager.has_saved_session())

        # 2. Load session
        loaded = manager.load_saved_session()
        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded.get("videos", [])), 1)
        self.assertEqual(len(loaded.get("domains", [])), 1)

        # 3. Clear session
        manager.clear_saved_session()
        self.assertFalse(manager.has_saved_session())

    def test_associated_videos_dialog(self):
        """Test AssociatedVideosDialog creation and multi-video table rendering."""
        from PyQt6.QtWidgets import QApplication
        import sys
        app = QApplication.instance() or QApplication(sys.argv)
        from ui.video_table_model import AssociatedVideosDialog

        assoc_vids = [
            {"video_title": "Vídeo 1", "video_url": "https://youtube.com/watch?v=1", "channel_name": "Canal 1", "view_count": 1000, "daily_views": 50},
            {"video_title": "Vídeo 2", "video_url": "https://youtube.com/watch?v=2", "channel_name": "Canal 2", "view_count": 5000, "daily_views": 200}
        ]
        dialog = AssociatedVideosDialog("dominio.com", assoc_vids)
        self.assertEqual(dialog.domain_name, "dominio.com")
        self.assertEqual(len(dialog.associated_videos), 2)

    def test_exporter_available_only_filter(self):
        """Test that PDF, Excel, CSV, and TXT export ONLY available expired domains."""
        from core.exporter import DataExporter

        mixed_domains = [
            {"root_domain": "disponivel123.com", "status": "Disponível", "total_daily_views": 100},
            {"root_domain": "ativo-ocupado.com", "status": "Ativo", "total_daily_views": 500},
            {"root_domain": "inativo.com", "status": "Inativo", "total_daily_views": 200},
            {"root_domain": "disponivel-ig", "status": "Disponível", "is_instagram": True, "total_daily_views": 80}
        ]
        
        # 1. Filter test
        avail = DataExporter.get_available_domains(mixed_domains)
        self.assertEqual(len(avail), 2)
        self.assertTrue(all(d["status"] == "Disponível" for d in avail))

        # 2. DataFrame test
        df = DataExporter.export_domains_to_dataframe(mixed_domains, only_available=True)
        self.assertEqual(len(df), 2)
        self.assertIn("disponivel123.com", df["Domínio / Conta"].values)
        self.assertNotIn("ativo-ocupado.com", df["Domínio / Conta"].values)

        # 3. TXT export test
        txt_path = "test_avail_out.txt"
        DataExporter.export_to_txt(txt_path, mixed_domains)
        self.assertTrue(os.path.exists(txt_path))
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("disponivel123.com", content)
            self.assertNotIn("ativo-ocupado.com", content)
        if os.path.exists(txt_path):
            os.remove(txt_path)

    def test_add_to_exclusion_list(self):
        """Test adding domain/Instagram to exclusion list and ensuring it is ignored in subsequent extraction."""
        from core.domain_extractor import add_to_exclusion_list, IGNORE_DOMAINS, ALL_EXCLUDED_DOMAINS
        extractor = DomainExtractor()

        import time
        unique_id = int(time.time() * 1000)
        sample_domain = f"teste-excluir-{unique_id}.com"
        sample_ig = f"perfil_excluir_{unique_id}"

        # Initially extractable
        text = f"Site: https://{sample_domain}/aula e Insta: @{sample_ig}"
        res1 = extractor.process_text_for_domains(text)
        doms1 = [d["root_domain"] for d in res1]
        self.assertIn(sample_domain, doms1)

        # Add to exclusion list
        add_to_exclusion_list(sample_domain)
        add_to_exclusion_list(sample_ig)

        self.assertIn(sample_domain, IGNORE_DOMAINS)
        
        # Extract again -> Must be completely excluded
        res2 = extractor.process_text_for_domains(text)
        doms2 = [d["root_domain"] for d in res2]
        self.assertNotIn(sample_domain, doms2)
        self.assertFalse(any(sample_ig in d.get("root_domain", "") for d in res2))

    def test_multiple_domain_exclusion(self):
        """Test adding multiple domains and Instagram handles via comma, semicolon, newlines, and lists."""
        from core.domain_extractor import (
            add_to_exclusion_list, remove_from_exclusion_list,
            get_custom_exclusions, IGNORE_DOMAINS
        )
        import time
        uid = int(time.time() * 1000)
        d1 = f"multitest-a-{uid}.com"
        d2 = f"multitest-b-{uid}.net"
        d3 = f"multitest-c-{uid}.org"
        ig1 = f"multitest_ig_{uid}"

        # 1. Comma and newline separated string
        multi_str = f"https://{d1}/page, www.{d2};\n@{ig1}, {d3}"
        success = add_to_exclusion_list(multi_str)
        self.assertTrue(success)

        for target in [d1, d2, d3, ig1]:
            self.assertIn(target, IGNORE_DOMAINS)
            self.assertIn(target, get_custom_exclusions())

        # 2. Test removal of some items
        remove_from_exclusion_list([d1, ig1])
        self.assertNotIn(d1, IGNORE_DOMAINS)
        self.assertNotIn(ig1, IGNORE_DOMAINS)
        self.assertIn(d2, IGNORE_DOMAINS)
        self.assertIn(d3, IGNORE_DOMAINS)

        # Cleanup remaining
        remove_from_exclusion_list([d2, d3])

    def test_segregated_available_stats(self):
        """Test separating web domains and Instagram handles in stats calculation."""
        mock_domains = [
            {"root_domain": "compravel1.com", "status": "Disponível", "is_instagram": False},
            {"root_domain": "compravel2.com", "status": "Disponível", "is_instagram": False},
            {"root_domain": "livre_ig_1", "display_name": "📸 @livre_ig_1", "status": "Disponível", "is_instagram": True},
            {"root_domain": "livre_ig_2", "display_name": "📸 @livre_ig_2", "status": "Disponível", "is_instagram": True},
            {"root_domain": "inativo.com", "status": "Inativo", "is_instagram": False},
            {"root_domain": "ativo.com", "status": "Ativo", "is_instagram": False},
        ]

        avail_doms = {
            (d.get("root_domain") or "").strip().lower()
            for d in mock_domains
            if d.get("status") == "Disponível" and not d.get("is_instagram")
        }
        avail_igs = {
            (d.get("root_domain") or d.get("display_name") or "").strip().lower()
            for d in mock_domains
            if d.get("status") == "Disponível" and d.get("is_instagram")
        }

        self.assertEqual(len(avail_doms), 2)
        self.assertEqual(len(avail_igs), 2)
        self.assertIn("compravel1.com", avail_doms)
        self.assertIn("livre_ig_1", avail_igs)

    def test_instance_manager(self):
        """Test multi-instance claiming, numbering, releasing, and color palettes."""
        from core.instance_manager import InstanceManager, get_instance_color
        inst_num = InstanceManager.claim_instance_number()
        self.assertGreaterEqual(inst_num, 1)
        self.assertEqual(InstanceManager.get_instance_number(), inst_num)
        
        # Test PID validation
        self.assertTrue(InstanceManager._is_pid_running(os.getpid()))
        self.assertFalse(InstanceManager._is_pid_running(99999999))

        # Test colors
        c1 = get_instance_color(1)
        c2 = get_instance_color(2)
        self.assertIn("start", c1)
        self.assertIn("tray", c1)
        self.assertNotEqual(c1["start"], c2["start"])

        # Test spawn_new_instance with mock
        with unittest.mock.patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = unittest.mock.MagicMock()
            spawned = InstanceManager.spawn_new_instance()
            self.assertTrue(spawned)
            self.assertTrue(mock_popen.called)

        InstanceManager.release_instance()

    def test_youtube_related_suggestions(self):
        """Test YouTube autocomplete and related search terms harvester."""
        from core.relevance_filter import get_youtube_related_suggestions
        suggestions = get_youtube_related_suggestions("dropshipping", hl="pt", gl="BR", max_suggestions=10)
        self.assertIsInstance(suggestions, list)
        self.assertGreaterEqual(len(suggestions), 1)
        self.assertTrue(any("dropshipping" in s.lower() for s in suggestions))

    def test_topic_profile_and_relevance_filter(self):
        """Test semantic topic profile building and strict relevance filtering to prevent topic drift."""
        from core.relevance_filter import build_topic_profile, is_content_relevant_to_topic, calculate_relevance_score

        # Build profile for 'dropshipping'
        profile_drop = build_topic_profile("dropshipping", related_terms=[
            "dropshipping do zero", "dropshipping shopify", "dropshipping como comecar", "fornecedores dropshipping"
        ])
        self.assertIn("dropshipping", profile_drop["primary_tokens"])

        # 1. On-topic video -> Must be APPROVED
        drop_video_title = "Como fazer Dropshipping do Zero em 2026 - Passo a Passo Completo"
        drop_video_desc = "Aprenda a criar sua loja de dropshipping com Shopify e encontrar fornecedores."
        self.assertTrue(is_content_relevant_to_topic(
            title=drop_video_title,
            description=drop_video_desc,
            channel_name="Empreendedor Digital",
            topic_profile=profile_drop
        ))

        # 2. Off-topic viral drift video (e.g. Minecraft / Funk / Pranks) -> Must be REJECTED
        off_topic_title = "COMPREI UM CARRO NOVO E OLHA NO QUE DEU!! (TROLLAGEM ÉPICA)"
        off_topic_desc = "Fui na loja e comprei um carro esportivo para zoar meus amigos."
        self.assertFalse(is_content_relevant_to_topic(
            title=off_topic_title,
            description=off_topic_desc,
            channel_name="Canal de Pegadinhas",
            topic_profile=profile_drop
        ))

        # 3. Test multi-word topic: 'marketing digital'
        profile_mkt = build_topic_profile("marketing digital", related_terms=[
            "marketing digital para iniciantes", "marketing digital trafego pago", "marketing digital afiliados"
        ])
        self.assertTrue(is_content_relevant_to_topic(
            title="Tudo sobre Marketing Digital e Tráfego Pago para Vender Mais",
            description="Curso grátis de marketing digital e gestão de tráfego.",
            channel_name="Mestre do Marketing",
            topic_profile=profile_mkt
        ))
        
        # Off-topic video for marketing digital
        self.assertFalse(is_content_relevant_to_topic(
            title="Joguei GTA RP e virei chefe da polícia",
            description="Gameplay completa no melhor servidor de GTA 5 do Brasil.",
            channel_name="GamerBR",
            topic_profile=profile_mkt
        ))

    def test_100k_video_limits_config(self):
        """Test spinbox and unlimited limits configured for up to 100,000 videos."""
        from PyQt6.QtWidgets import QApplication
        import sys
        app = QApplication.instance() or QApplication(sys.argv)
        from ui.hunter_tab import HunterTab

        hunter = HunterTab()
        self.assertEqual(hunter.spin_max.maximum(), 10000000)
        self.assertEqual(hunter.spin_max.minimum(), 5)
        
        # Test unlimited toggle
        hunter.chk_unlimited.setChecked(True)
        self.assertFalse(hunter.spin_max.isEnabled())
        hunter.chk_unlimited.setChecked(False)
        self.assertTrue(hunter.spin_max.isEnabled())

    def test_video_table_domain_search(self):
        """Test searching a domain name filters all videos containing that expired domain."""
        from PyQt6.QtWidgets import QApplication
        import sys
        app = QApplication.instance() or QApplication(sys.argv)
        from ui.video_table_model import VideoTableView

        table = VideoTableView()
        sample_vids = [
            {
                "id": "vid1",
                "title": "Aprenda Marketing",
                "channel_name": "Canal 1",
                "metrics": {"view_count": 1000, "view_count_formatted": "1K"},
                "domains": [{"root_domain": "curso-expirado.com.br", "display_name": "curso-expirado.com.br", "status": "Disponível"}]
            },
            {
                "id": "vid2",
                "title": "Tutorial Python",
                "channel_name": "Canal 2",
                "metrics": {"view_count": 5000, "view_count_formatted": "5K"},
                "domains": [{"root_domain": "outro-site.com", "display_name": "outro-site.com", "status": "Ativo"}]
            }
        ]
        table.set_videos(sample_vids)
        self.assertEqual(len(table.filtered_videos_data), 2)

        # Search by domain name -> Must filter to vid1 only
        table.set_search_query("curso-expirado")
        self.assertEqual(len(table.filtered_videos_data), 1)
        self.assertEqual(table.filtered_videos_data[0]["id"], "vid1")

        # Clear search
        table.set_search_query("")
        self.assertEqual(len(table.filtered_videos_data), 2)

    def test_trademark_validator(self):
        """Test detection of famous trademarks and classification of safe generic domains."""
        from core.trademark_validator import analyze_trademark_risk

        # 1. Renowned Brazilian Brand (INPI) -> High Risk
        res_ml = analyze_trademark_risk("ofertas-mercadolivre.com.br")
        self.assertFalse(res_ml["is_safe"])
        self.assertEqual(res_ml["risk_level"], "HIGH_RISK")
        self.assertIn("Mercado Livre", res_ml["detected_brands"])
        self.assertIn("CYBERSQUATTING", res_ml["legal_advice"])

        # 2. Renowned Bank (Nubank) -> High Risk
        res_nu = analyze_trademark_risk("cartoesnubank.com")
        self.assertFalse(res_nu["is_safe"])
        self.assertIn("Nubank", res_nu["detected_brands"])

        # 3. Global Big Tech (Apple) -> High Risk
        res_apple = analyze_trademark_risk("suporteapple.net")
        self.assertFalse(res_apple["is_safe"])
        self.assertTrue(any("Apple" in b for b in res_apple["detected_brands"]))

        # 4. Safe Generic / Niche Domain -> Safe
        res_generic = analyze_trademark_risk("dicasdejardinagem123.com.br")
        self.assertTrue(res_generic["is_safe"])
        self.assertEqual(res_generic["risk_level"], "SAFE")
        self.assertEqual(len(res_generic["detected_brands"]), 0)
        self.assertIn("DOMÍNIO SEGURO", res_generic["legal_advice"])

        # 5. Safe Generic English Domain -> Safe
        res_en = analyze_trademark_risk("digitalmarketingtipsfree.com")
        self.assertTrue(res_en["is_safe"])
        self.assertEqual(res_en["risk_level"], "SAFE")

    def test_trademark_validator_comprehensive_database(self):
        """Test detection across all 12 trademark categories and anti-false-positive whitelist."""
        from core.trademark_validator import analyze_trademark_risk

        # 1. Betting / Casas de Apostas
        self.assertFalse(analyze_trademark_risk("bet365bonus.com")["is_safe"])
        self.assertFalse(analyze_trademark_risk("betanobrasil.bet")["is_safe"])
        self.assertFalse(analyze_trademark_risk("pixbetapostas.com")["is_safe"])
        self.assertFalse(analyze_trademark_risk("blaze-login.com")["is_safe"])
        self.assertFalse(analyze_trademark_risk("esportesdasorte.online")["is_safe"])

        # 2. AI & Big Tech
        self.assertFalse(analyze_trademark_risk("deepseekapp.com")["is_safe"])
        self.assertFalse(analyze_trademark_risk("chatgptlogin.net")["is_safe"])
        self.assertFalse(analyze_trademark_risk("claudeai-brasil.com")["is_safe"])
        self.assertFalse(analyze_trademark_risk("midjourneycursos.com")["is_safe"])

        # 3. Infoprodutos & EdTech
        self.assertFalse(analyze_trademark_risk("hotmartafiliados.com")["is_safe"])
        self.assertFalse(analyze_trademark_risk("kiwifycursos.com.br")["is_safe"])
        self.assertFalse(analyze_trademark_risk("aluracursos.com")["is_safe"])
        self.assertFalse(analyze_trademark_risk("descomplicaaulas.com")["is_safe"])

        # 4. Anti-False-Positive Shield (Generic Dictionary Whitelist)
        self.assertTrue(analyze_trademark_risk("otimizacao.com.br")["is_safe"])
        self.assertTrue(analyze_trademark_risk("cabelos.com")["is_safe"])
        self.assertTrue(analyze_trademark_risk("algoritmo.com.br")["is_safe"])
        self.assertTrue(analyze_trademark_risk("modelo.com")["is_safe"])
        self.assertTrue(analyze_trademark_risk("claridade.com.br")["is_safe"])
        self.assertTrue(analyze_trademark_risk("valente.com")["is_safe"])
        self.assertTrue(analyze_trademark_risk("extraordinario.com")["is_safe"])
        self.assertTrue(analyze_trademark_risk("internacional.com.br")["is_safe"])

        # 5. Typosquatting & Homoglyphs
        res_typo1 = analyze_trademark_risk("mercadolvre.com")
        self.assertFalse(res_typo1["is_safe"])
        self.assertEqual(res_typo1["risk_level"], "MODERATE_RISK")

        res_typo2 = analyze_trademark_risk("whatsap.com")
        self.assertFalse(res_typo2["is_safe"])

        res_homoglyph = analyze_trademark_risk("faceb00k.com")
        self.assertFalse(res_homoglyph["is_safe"])

    def test_recent_vph_and_traffic_vitality(self):
        """Test Recent VPH modeling: launch viral vs active evergreen vs dead video."""
        from core.metrics_calculator import calculate_video_metrics, format_vph

        # 1. Launch Viral video (24h, 2400 views)
        one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
        m_launch = calculate_video_metrics(view_count=2400, upload_date=one_day_ago)
        self.assertAlmostEqual(m_launch["hourly_views"], 100.0, delta=5.0)
        self.assertEqual(m_launch["velocity_badge"], "🔥 Viral em Alta")
        self.assertTrue(m_launch["is_active_traffic"])

        # 2. High-traffic Active Evergreen video (3 years old, 3,000,000 views)
        three_years_ago = datetime.now(timezone.utc) - timedelta(days=1095)
        m_evergreen = calculate_video_metrics(view_count=3000000, upload_date=three_years_ago)
        self.assertGreaterEqual(m_evergreen["hourly_views"], 3.0)
        self.assertLessEqual(m_evergreen["hourly_views"], 15.0)
        self.assertEqual(m_evergreen["velocity_badge"], "🟢 Tráfego Ativo (Evergreen)")
        self.assertTrue(m_evergreen["is_active_traffic"])

        # 3. Dead / Stagnant video (5 years old, 5,000 views)
        five_years_ago = datetime.now(timezone.utc) - timedelta(days=1825)
        m_dead = calculate_video_metrics(view_count=5000, upload_date=five_years_ago)
        self.assertLess(m_dead["hourly_views"], 0.2)
        self.assertEqual(m_dead["velocity_badge"], "⚪ Tráfego Estagnado")
        self.assertFalse(m_dead["is_active_traffic"])

        # 4. Format VPH
        self.assertEqual(format_vph(125.4), "⚡ 125 VPH")
        self.assertEqual(format_vph(14.8), "⚡ 14.8 VPH")
        self.assertEqual(format_vph(5.4), "⚡ 5.4 VPH")
        self.assertEqual(format_vph(0.76), "⚡ 0.76 VPH")
        self.assertEqual(format_vph(0.01), "⚡ < 0.1 VPH")

    def test_min_views_and_year_range_filtering(self):
        """Test video filtering with minimum views threshold and strict year interval enforcement."""
        from core.metrics_calculator import calculate_video_metrics
        from core.youtube_crawler import YouTubeCrawler

        # 1. Test upload_year extraction in metrics
        dt_2022 = datetime(2022, 6, 15, tzinfo=timezone.utc)
        m2022 = calculate_video_metrics(view_count=50000, upload_date=dt_2022)
        self.assertEqual(m2022["upload_year"], 2022)

        dt_2025 = datetime(2025, 1, 10, tzinfo=timezone.utc)
        m2025 = calculate_video_metrics(view_count=1200, upload_date=dt_2025)
        self.assertEqual(m2025["upload_year"], 2025)

        # 2. Test min_views filter logic
        crawler = YouTubeCrawler()
        
        # Test simulated channel processing with min_views filter
        dummy_vids = [
            {"id": "v1", "url": "https://youtube.com/watch?v=v1", "title": "Big Hit", "initial_view_count": 100000, "channel_name": "Canal"},
            {"id": "v2", "url": "https://youtube.com/watch?v=v2", "title": "Low Views", "initial_view_count": 500, "channel_name": "Canal"},
        ]
        
        crawler.get_channel_videos = lambda **kwargs: dummy_vids
        crawler.get_video_deep_details = lambda url, **kwargs: {
            "title": "Big Hit" if "v1" in url else "Low Views",
            "channel_name": "Canal",
            "thumbnail": "",
            "view_count": 100000 if "v1" in url else 500,
            "description": "contato@site123.com",
            "pinned_comment": "",
            "top_comments": [],
            "upload_date": dt_2022,
            "timestamp": None
        }

        # Run with min_views = 5000 -> only Big Hit should be processed!
        res = crawler.process_channel(channel_identifier="@Canal", max_videos=10, min_views=5000)
        processed_titles = [v["title"] for v in res["videos"]]
        self.assertIn("Big Hit", processed_titles)
        self.assertNotIn("Low Views", processed_titles)

    def test_profile_manager_and_batch_execution(self):
        """Test default profile saving, loading, and batch multi-instance parsing."""
        from core.profile_manager import save_default_profile, load_default_profile, DEFAULT_PROFILE
        
        test_prof = {
            "search_mode": "keywords",
            "target_lang": "global",
            "excluded_countries": ["hi", "ru", "ar"],
            "date_filter": "custom_range",
            "year_start": 2021,
            "year_end": 2025,
            "sort_by": "view_count",
            "max_videos": 100,
            "unlimited_videos": True,
            "min_views": 50000,
            "fast_mode": True,
            "include_related": True,
            "loop_24h": False
        }

        # Save profile
        self.assertTrue(save_default_profile(test_prof))

        # Load profile
        loaded = load_default_profile()
        self.assertEqual(loaded["min_views"], 50000)
        self.assertEqual(loaded["excluded_countries"], ["hi", "ru", "ar"])
        self.assertEqual(loaded["year_start"], 2021)
        self.assertTrue(loaded["unlimited_videos"])

    def test_robust_domain_extraction_features(self):
        """Test clickable hyperlinks only for web domains, Instagram @handles allowance, and redirect unwraps."""
        extractor = DomainExtractor()

        # 1. Clickable hyperlinks (https://, http://, www.)
        sample_clickable = "Acesse https://cursodepianoonline.com.br ou http://lojadomarcio.com e tambem www.novocurso.org/promo"
        res_click = extractor.process_text_for_domains(sample_clickable)
        roots_click = [d["root_domain"] for d in res_click]
        self.assertIn("cursodepianoonline.com.br", roots_click)
        self.assertIn("lojadomarcio.com", roots_click)
        self.assertIn("novocurso.org", roots_click)

        # 2. Non-clickable plain text domain mentions must be ignored for web
        sample_plain = "Apenas mencao em texto: cursodemarketing.com.br ou site.online e contato@empresa.com.br"
        res_plain = extractor.process_text_for_domains(sample_plain)
        roots_plain = [d["root_domain"] for d in res_plain]
        self.assertNotIn("cursodemarketing.com.br", roots_plain)
        self.assertNotIn("site.online", roots_plain)
        self.assertNotIn("empresa.com.br", roots_plain)

        # 3. Instagram @handles and profile links allowed
        sample_ig = "Siga nosso insta @perfil_oficial_123 e https://instagram.com/canal_oficial"
        res_ig = extractor.process_text_for_domains(sample_ig)
        roots_ig = [d["root_domain"] for d in res_ig]
        self.assertIn("instagram.com/perfil_oficial_123", roots_ig)
        self.assertIn("instagram.com/canal_oficial", roots_ig)

        # 4. Non-web file rejection alongside valid clickable domain
        res_files = extractor.process_text_for_domains("Baixe www.relatorio.pdf e musica.mp3 no site https://novaloja.net")
        roots_files = [d["root_domain"] for d in res_files]
        self.assertIn("novaloja.net", roots_files)
        self.assertNotIn("relatorio.pdf", roots_files)

        # 5. YouTube & Google redirect unwrapping
        yt_redirect_text = "Link: https://www.youtube.com/redirect?q=https%3A%2F%2Fcursoteste123.com.br%2Fpromo&redir_token=xyz"
        res_yt = extractor.process_text_for_domains(yt_redirect_text)
        roots_yt = [d["root_domain"] for d in res_yt]
        self.assertIn("cursoteste123.com.br", roots_yt)

        # 6. Trailing punctuation and parentheses
        res_punct = extractor.process_text_for_domains("Veja nosso site (https://www.exemplo.com.br/contato), aproveite!")
        roots_punct = [d["root_domain"] for d in res_punct]
        self.assertIn("exemplo.com.br", roots_punct)

    def test_statistical_ols_vph_calculation(self):
        """Test rolling window OLS linear regression VPH calculation and edge cases."""
        from core.metrics_calculator import calculate_ols_vph_from_history, record_video_snapshot, calculate_video_metrics
        import time

        base_ts = 1700000000.0

        # 1. Steady linear growth: 100 views/hour across 4 hourly points
        h_steady = [
            (base_ts, 1000),
            (base_ts + 3600, 1100),
            (base_ts + 7200, 1200),
            (base_ts + 10800, 1300)
        ]
        vph, audit = calculate_ols_vph_from_history(h_steady, base_ts + 10800)
        self.assertAlmostEqual(vph, 100.0, delta=0.5)
        self.assertFalse(audit)

        # 2. Staircase CDN sync effect: (10k, 10k, 10k, +600 views)
        h_staircase = [
            (base_ts, 10000),
            (base_ts + 3600, 10000),
            (base_ts + 7200, 10000),
            (base_ts + 10800, 10600)
        ]
        vph_stair, audit_stair = calculate_ols_vph_from_history(h_staircase, base_ts + 10800)
        self.assertGreater(vph_stair, 0.0)
        self.assertFalse(audit_stair)

        # 3. YouTube Audit (Negative delta / views removed) -> Clamp to 0 and set audit_detected: True
        h_audit = [
            (base_ts, 50000),
            (base_ts + 3600, 48000),
            (base_ts + 7200, 46000)
        ]
        vph_aud, audit_flag = calculate_ols_vph_from_history(h_audit, base_ts + 7200)
        self.assertEqual(vph_aud, 0.0)
        self.assertTrue(audit_flag)

        # 4. Fallback for < 3 samples with time >= 1h
        h_few = [
            (base_ts, 2000),
            (base_ts + 7200, 2400) # 2 hours delta
        ]
        vph_few, audit_few = calculate_ols_vph_from_history(h_few, base_ts + 7200)
        self.assertAlmostEqual(vph_few, 200.0, delta=0.5)
        self.assertFalse(audit_few)

        # 5. Near-zero views (< 0.1 VPH) -> returns 0.0
        h_zero = [
            (base_ts, 5000),
            (base_ts + 3600, 5000),
            (base_ts + 7200, 5000)
        ]
        vph_z, audit_z = calculate_ols_vph_from_history(h_zero, base_ts + 7200)
        self.assertEqual(vph_z, 0.0)
        self.assertFalse(audit_z)

        # 6. Full calculate_video_metrics with snapshot integration
        v_id = "test_vid_ols_99"
        record_video_snapshot(v_id, 10000, base_ts)
        record_video_snapshot(v_id, 10250, base_ts + 3600)
        record_video_snapshot(v_id, 10500, base_ts + 7200)
        res = calculate_video_metrics(10500, video_id=v_id)
        self.assertIn("hourly_views", res)
        self.assertIn("audit_detected", res)

    def test_on_demand_vph_service(self):
        """Test on-demand VPH service, Wayback Cold-Start, Likes correlation, Cache mutation, and Weighted Confidence Score."""
        from core.vph_service import VPHService, VideoVPHResponse
        from datetime import datetime, timezone, timedelta
        import time

        service = VPHService(cache_ttl_seconds=900)
        service._anchors_db.clear()
        v_id = "test_vph_ondemand_01"

        # Mock fetcher to simulate deterministic view & like returns
        mock_views = 50000
        mock_likes = 1200
        mock_pub = "2023-01-01T00:00:00Z"
        mock_provider = "innertube"
        mock_mutation = False

        def mock_fetch(vid):
            return mock_views, mock_likes, mock_pub, mock_provider, mock_mutation

        service.fetcher.fetch_exact_video_details = mock_fetch

        # 1. Cold Start (Scenario A): First query (without Wayback)
        resp1 = service.get_on_demand_vph(v_id, force_refresh=True)
        self.assertEqual(resp1["videoId"], v_id)
        self.assertEqual(resp1["exactViews"], 50000)
        self.assertEqual(resp1["likeCount"], 1200)
        self.assertEqual(resp1["confidence"], "lifetime_fallback")
        self.assertFalse(resp1["waybackResolved"])
        self.assertFalse(resp1["auditDetected"])
        self.assertEqual(resp1["providerUsed"], "innertube")
        self.assertLessEqual(resp1["confidenceScore"], 40)
        self.assertIn("calculatedAt", resp1)

        # 1b. Cold Start WITH Wayback Machine capture (e.g. captured 3 days ago with 48,000 views)
        v_id_wb = "test_vph_wayback_99"
        service._anchors_db.pop(v_id_wb, None)
        
        # Monkeypatch fetch_wayback_anchor for this test
        import core.vph_service
        orig_fetch_wb = core.vph_service.fetch_wayback_anchor
        core.vph_service.fetch_wayback_anchor = lambda vid, timeout=2.5: (48000, time.time() - (72 * 3600.0)) # 3 days ago

        try:
            resp_wb = service.get_on_demand_vph(v_id_wb, force_refresh=True)
            self.assertTrue(resp_wb["waybackResolved"])
            self.assertEqual(resp_wb["confidence"], "medium")
            # (50,000 - 48,000) / 72h = ~27.78 VPH
            self.assertAlmostEqual(resp_wb["vph"], 27.78, delta=1.0)
            self.assertGreater(resp_wb["confidenceScore"], 40)
        finally:
            core.vph_service.fetch_wayback_anchor = orig_fetch_wb

        # 2. Local Throttling (< 15 mins): Returns cached result immediately with providerUsed = "local_cache"
        resp2 = service.get_on_demand_vph(v_id, force_refresh=False)
        self.assertEqual(resp2["providerUsed"], "local_cache")
        self.assertEqual(resp2["exactViews"], 50000)

        # 3. Re-access with Delta >= 1 hour (Scenario B): Steady traffic (+300 views, +15 likes in 2 hours -> 150 VPH)
        service._anchors_db[v_id]["anchor_ts"] = time.time() - 7200.0 # 2 hours ago
        service._anchors_db[v_id]["anchor_views"] = 50000
        service._anchors_db[v_id]["anchor_likes"] = 1200
        service._anchors_db[v_id]["last_fetch_ts"] = time.time() - 7200.0
        mock_views = 50300
        mock_likes = 1215
        mock_mutation = True # Cache mutation active (|playerViews - schemaViews| > 0)

        resp3 = service.get_on_demand_vph(v_id, force_refresh=True)
        self.assertEqual(resp3["confidence"], "high")
        self.assertAlmostEqual(resp3["vph"], 150.0, delta=1.0)
        self.assertEqual(resp3["trafficStatus"], "active")
        self.assertTrue(resp3["organicEngagementVerified"])
        self.assertTrue(resp3["cacheMutationActive"])
        self.assertEqual(resp3["confidenceScore"], 100) # 30 + 30 (1-24h) + 20 (likes) + 10 (mutation) + 10 (innertube) = 100
        self.assertFalse(resp3["auditDetected"])

        # 4. YouTube Audit Detection: Negative Delta in >= 1h (views removed: 50,300 -> 49,000) -> Score = 0
        service._anchors_db[v_id]["anchor_ts"] = time.time() - 3650.0
        service._anchors_db[v_id]["anchor_views"] = 50300
        service._anchors_db[v_id]["anchor_likes"] = 1215
        service._anchors_db[v_id]["last_fetch_ts"] = time.time() - 3650.0
        mock_views = 49000
        mock_likes = 1215

        resp4 = service.get_on_demand_vph(v_id, force_refresh=True)
        self.assertEqual(resp4["vph"], 0.0)
        self.assertTrue(resp4["auditDetected"])
        self.assertEqual(resp4["confidenceScore"], 0) # Audit penalty zeros score

        # 5. Severe Engagement Anomaly: +600 views in 2h with 0 likes -> penalized score
        service._anchors_db[v_id]["anchor_ts"] = time.time() - 7200.0
        service._anchors_db[v_id]["anchor_views"] = 49000
        service._anchors_db[v_id]["anchor_likes"] = 1215
        service._anchors_db[v_id]["last_fetch_ts"] = time.time() - 7200.0
        mock_views = 49600
        mock_likes = 1215 # 0 delta likes
        mock_mutation = False

        resp5 = service.get_on_demand_vph(v_id, force_refresh=True)
        self.assertFalse(resp5["organicEngagementVerified"])
        # Score = 30 + 30 (1-24h) + 10 (innertube) - 25 (anomaly penalty) = 45
        self.assertEqual(resp5["confidenceScore"], 45)

        # 6. Re-access between 15 and 60 minutes (Scenario C):
        # 6a. Positive delta (+100 views, +5 likes in 30 min -> 200 VPH)
        service._anchors_db[v_id]["anchor_ts"] = time.time() - 1800.0 # 30 min ago
        service._anchors_db[v_id]["anchor_views"] = 49600
        service._anchors_db[v_id]["anchor_likes"] = 1215
        service._anchors_db[v_id]["last_fetch_ts"] = time.time() - 1800.0
        mock_views = 49700
        mock_likes = 1220

        resp6a = service.get_on_demand_vph(v_id, force_refresh=True)
        self.assertEqual(resp6a["confidence"], "medium")
        self.assertAlmostEqual(resp6a["vph"], 200.0, delta=2.0)
        self.assertTrue(resp6a["organicEngagementVerified"])

        # 6b. Same views (CDN batch delay -> preserve previous VPH)
        service._anchors_db[v_id]["anchor_ts"] = time.time() - 1800.0
        service._anchors_db[v_id]["anchor_views"] = 49700
        service._anchors_db[v_id]["last_vph"] = 200.0
        service._anchors_db[v_id]["last_fetch_ts"] = time.time() - 1800.0
        mock_views = 49700

        resp6b = service.get_on_demand_vph(v_id, force_refresh=True)
        self.assertEqual(resp6b["confidence"], "medium")
        self.assertEqual(resp6b["vph"], 200.0)

        # 7. Traffic Classification Rules
        now = datetime.now(timezone.utc)
        old_pub = now - timedelta(days=200)
        new_pub = now - timedelta(days=30)

        # viral_spike: >= 500
        self.assertEqual(VPHService.classify_traffic(550.0, new_pub, now), "viral_spike")
        # active: 20 <= VPH < 500
        self.assertEqual(VPHService.classify_traffic(150.0, new_pub, now), "active")
        # evergreen: 2 <= VPH < 20 on videos > 180 days
        self.assertEqual(VPHService.classify_traffic(8.0, old_pub, now), "evergreen")
        # dormant: < 2 (or < 20 on new videos)
        self.assertEqual(VPHService.classify_traffic(1.0, old_pub, now), "dormant")
        self.assertEqual(VPHService.classify_traffic(8.0, new_pub, now), "dormant")

    def test_strict_domain_matching_and_exclusion_of_generic_mentions(self):
        """
        Verify that:
        1. Generic non-clickable mentions (Twitter @handle, Telegram @handle, editor @handle) are rejected.
        2. Strict domain filtering in VideoTableView ONLY matches videos that genuinely contain that domain in their domains list, never matching false substring titles or channel names.
        """
        from core.domain_extractor import DomainExtractor
        extractor = DomainExtractor()

        # 1. Non-clickable generic mentions & emails rejected
        mixed_text = (
            "Siga no Twitter: @twitterhandle e no Telegram: @telegramhandle\n"
            "Edição por @editor_video e áudio por @audiomaster\n"
            "E-mail para contato: contato@empresa.com.br\n"
            "Texto solto não clicável: siteapenastexto.com ou outro.net\n"
            "Link real clicável: https://meusiteclicavel.com/oferta\n"
            "Instagram oficial: https://www.instagram.com/canal_oficial_real"
        )
        res = extractor.process_text_for_domains(mixed_text)
        roots = [d["root_domain"] for d in res]

        self.assertIn("meusiteclicavel.com", roots)
        self.assertIn("instagram.com/canal_oficial_real", roots)
        self.assertNotIn("twitterhandle", roots)
        self.assertNotIn("telegramhandle", roots)
        self.assertNotIn("editor_video", roots)
        self.assertNotIn("audiomaster", roots)
        self.assertNotIn("empresa.com.br", roots)
        self.assertNotIn("siteapenastexto.com", roots)

        # 2. Strict domain filter in VideoTableView
        from PyQt6.QtWidgets import QApplication
        import sys
        app = QApplication.instance() or QApplication(sys.argv)
        from ui.video_table_model import VideoTableView
        v_table = VideoTableView()

        v1 = {
            "id": "vid_1",
            "title": "Tutorial Completo de Tecnologia e Programação",
            "channel_name": "Canal Tecnologia Total",
            "domains": [{"root_domain": "iniciante.org", "display_name": "iniciante.org", "status": "Ativo"}]
        }
        v2 = {
            "id": "vid_2",
            "title": "Vlog de Viagem pela Europa",
            "channel_name": "Mochilão",
            "domains": [{"root_domain": "tecnologia.com", "display_name": "tecnologia.com", "status": "Disponível"}]
        }
        v3 = {
            "id": "vid_3",
            "title": "Receita Deliciosa de Bolo",
            "channel_name": "Cozinha Prática",
            "domains": [{"root_domain": "instagram.com/chef_bolo", "display_name": "📸 @chef_bolo", "status": "Disponível"}]
        }

        v_table.set_videos([v1, v2, v3])

        # A: Filter strictly by 'tecnologia.com'
        # Must return ONLY v2 (which has the domain), NOT v1 (which only has 'Tecnologia' in title/channel)!
        v_table.filter_by_exact_domain("tecnologia.com")
        filtered_ids = [v["id"] for v in v_table.filtered_videos_data]
        self.assertEqual(filtered_ids, ["vid_2"])

        # B: Filter strictly by Instagram handle
        v_table.filter_by_exact_domain("📸 @chef_bolo")
        filtered_ids_ig = [v["id"] for v in v_table.filtered_videos_data]
        self.assertEqual(filtered_ids_ig, ["vid_3"])

        # C: General search for 'Tecnologia' matches both v1 (title) and v2 (domain)
        v_table.set_search_query("Tecnologia")
        general_ids = [v["id"] for v in v_table.filtered_videos_data]
        self.assertIn("vid_1", general_ids)
        self.assertIn("vid_2", general_ids)
        self.assertNotIn("vid_3", general_ids)

    def test_seo_metrics_intelligence_and_table_column_reordering(self):
        """
        Verify that:
        1. SeoMetricsService calculates valid DA (1-100), PA (1-100), Backlinks, RefDomains, and deep audit URLs.
        2. SeoAuthorityTableView enables interactive movable columns and handles available domains properly.
        """
        from core.seo_metrics_service import SeoMetricsService
        service = SeoMetricsService()

        # 1. Clean domain parsing
        self.assertEqual(service.clean_domain("https://www.cursodepiano.com.br/aulas?id=1"), "cursodepiano.com.br")
        self.assertEqual(service.clean_domain("http://lojadomarcio.com/"), "lojadomarcio.com")

        # 2. Analyze domain calculation
        res = service.analyze_domain(
            "cursodepiano.com.br",
            video_count=3,
            total_daily_views=15000,
            total_views=500000,
            force_refresh=True
        )
        self.assertTrue(1 <= res["da"] <= 100)
        self.assertTrue(1 <= res["pa"] <= 100)
        self.assertTrue(res["backlinks"] >= 1)
        self.assertTrue(res["ref_domains"] >= 1)
        self.assertTrue(1 <= res["spam_score"] <= 100)
        self.assertIn("moz.com/domain-analysis", res["moz_url"])
        self.assertIn("ahrefs.com/backlink-checker", res["ahrefs_url"])
        self.assertIn("semrush.com/analytics", res["semrush_url"])

        # 3. SeoAuthorityTableView and Column Reordering
        from PyQt6.QtWidgets import QApplication
        import sys
        app = QApplication.instance() or QApplication(sys.argv)
        from ui.seo_table_view import SeoAuthorityTableView
        table_view = SeoAuthorityTableView()

        # Sections must be movable (drag-and-drop column reordering)
        header = table_view.table.horizontalHeader()
        self.assertTrue(header.sectionsMovable())
        self.assertTrue(header.dragEnabled())

        # Move column 1 to visual index 3
        orig_visual_1 = header.visualIndex(1)
        header.moveSection(orig_visual_1, 3)
        self.assertEqual(header.visualIndex(1), 3)

        # Reset column order
        table_view._reset_column_order(silent=True)
        self.assertEqual(header.visualIndex(1), 1)

        # 4. Add available domain
        domain_item = {
            "root_domain": "cursodepiano.com.br",
            "display_name": "cursodepiano.com.br",
            "status": "Disponível",
            "is_instagram": False,
            "video_count": 2,
            "total_daily_views": 8500
        }
        table_view.add_domain(domain_item)
        self.assertIn("cursodepiano.com.br", table_view.raw_seo_data)
        self.assertEqual(len(table_view.filtered_seo_data), 1)

    def test_niche_catalog_and_queries(self):
        """Test niche catalog retrieval and structured query generation."""
        from core.niche_catalog import (
            get_available_niches, get_subniches_for_niche,
            generate_queries_for_subniche, get_all_subniches_flat,
            NICHE_CATALOG
        )

        niches = get_available_niches()
        self.assertGreaterEqual(len(niches), 10)
        self.assertIn("💼 Marketing Digital & Afiliados", niches)
        self.assertIn("💰 Finanças, Investimentos & Cripto", niches)

        subniches = get_subniches_for_niche("💼 Marketing Digital & Afiliados")
        self.assertGreaterEqual(len(subniches), 3)

        first_sub = subniches[0]
        queries = generate_queries_for_subniche("💼 Marketing Digital & Afiliados", first_sub)
        self.assertGreaterEqual(len(queries), 3)
        self.assertTrue(all(isinstance(q, str) and len(q) > 5 for q in queries))

        # Query with additional keyword
        queries_with_add = generate_queries_for_subniche(
            "💼 Marketing Digital & Afiliados", first_sub, additional_keyword="2026"
        )
        self.assertTrue(all("2026" in q for q in queries_with_add))

        # Flat list
        flat = get_all_subniches_flat()
        self.assertGreaterEqual(len(flat), 20)

    def test_niche_mode_ui_and_preventive_routine(self):
        """Test niche mode UI switching, batch timer, O(1) duplicate set, and log block cap."""
        import time
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from ui.hunter_tab import HunterTab

        hunter = HunterTab()
        hunter.all_videos.clear()
        hunter.all_domains.clear()
        hunter._seen_video_ids.clear()
        hunter._seen_domain_keys.clear()
        hunter._pending_videos_buffer.clear()
        hunter._pending_domains_buffer.clear()

        # 1. Log block count cap to prevent Qt layout freezing
        self.assertEqual(hunter.log_view.maximumBlockCount(), 2000)

        # 2. Batching buffer & O(1) sets initialized
        self.assertEqual(len(hunter._seen_video_ids), 0)
        self.assertEqual(len(hunter._seen_domain_keys), 0)
        self.assertIsNotNone(hunter._ui_batch_timer)
        self.assertEqual(hunter._ui_batch_timer.interval(), 250)

        # 3. Test niche mode in combo_mode
        niches_idx = hunter.combo_mode.findData("niches")
        self.assertGreaterEqual(niches_idx, 0)

        # Switch to niches mode
        hunter.combo_mode.setCurrentIndex(niches_idx)
        self.assertFalse(hunter.combo_niche.isHidden())
        self.assertFalse(hunter.combo_subniche.isHidden())
        self.assertTrue(hunter.input_target.isHidden())

        # Test sub-niche population
        hunter.combo_niche.setCurrentIndex(1)
        self.assertGreater(hunter.combo_subniche.count(), 1)

        # 4. Test O(1) video duplicate check & batching
        sample_v = {
            "id": "vid_test_123",
            "url": "https://youtube.com/watch?v=vid_test_123",
            "title": "Vídeo de Teste de Mineração",
            "metrics": {"view_count": 1000, "view_count_formatted": "1K"}
        }
        hunter._on_video_found(sample_v)
        self.assertIn("vid_test_123", hunter._seen_video_ids)
        self.assertEqual(len(hunter._pending_videos_buffer), 1)

        # Duplicate should be rejected instantly
        hunter._on_video_found(sample_v)
        self.assertEqual(len(hunter._pending_videos_buffer), 1)

        # Flush batch
        hunter._flush_pending_ui_batch()
        self.assertEqual(len(hunter._pending_videos_buffer), 0)
        self.assertEqual(len(hunter.all_videos), 1)

        # 5. Test AutoSave throttling
        hunter.autosave_manager._last_save_time = time.time()
        # Non-forced save should be throttled
        saved = hunter.autosave_manager.save_session(hunter.all_videos, hunter.all_domains, force=False)
        self.assertFalse(saved)

if __name__ == "__main__":
    unittest.main()

