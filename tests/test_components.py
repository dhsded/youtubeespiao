"""
Automated unit tests for YouTube Espião core components.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from datetime import datetime, timezone, timedelta
from core.metrics_calculator import calculate_video_metrics, format_number
from core.domain_extractor import DomainExtractor
from core.domain_validator import DomainValidator
from core.instagram_validator import InstagramValidator
from core.translator import expand_queries_for_language, translate_query, AVAILABLE_LANGUAGES

class TestYoutubeEspiaoCore(unittest.TestCase):

    def test_metrics_calculator(self):
        """Test calculation of hourly, daily, monthly, 90-day, and annual view averages."""
        # 1. Recent video (10 days old)
        ten_days_ago = datetime.now(timezone.utc) - timedelta(days=10)
        metrics = calculate_video_metrics(view_count=24000, upload_date=ten_days_ago)

        self.assertEqual(metrics["view_count"], 24000)
        self.assertEqual(metrics["views_90d"], 24000)
        self.assertAlmostEqual(metrics["daily_views"], 2400.0, delta=20.0)
        self.assertAlmostEqual(metrics["hourly_views"], 100.0, delta=2.0)
        self.assertGreater(metrics["monthly_views"], 70000)
        self.assertGreater(metrics["yearly_views"], 800000)
        self.assertIn("24K", metrics["view_count_formatted"])

        # 2. Older video (365 days old with decay & evergreen 90d traffic)
        one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
        metrics_old = calculate_video_metrics(view_count=500000, upload_date=one_year_ago)
        self.assertGreater(metrics_old["views_90d"], 20000)
        self.assertLess(metrics_old["views_90d"], 500000)
        self.assertGreater(metrics_old["hourly_views"], 5.0)

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
        """Test multi-language expansion for global and specific languages."""
        # 1. Global expansion creates tasks for all 12 supported languages
        tasks = expand_queries_for_language("curso de marketing", "global")
        self.assertEqual(len(tasks), 12)
        lang_codes = [t["lang_code"] for t in tasks]
        self.assertIn("ru", lang_codes) # Russian
        self.assertIn("ja", lang_codes) # Japanese
        self.assertIn("zh", lang_codes) # Chinese
        self.assertIn("ar", lang_codes) # Arabic

        # 2. Universal acronym preservation with localized token targeting
        gta_task = expand_queries_for_language("GTA", "pt")
        gta_queries = [t["query"] for t in gta_task]
        self.assertIn("GTA brasil", gta_queries)
        self.assertIn("GTA", gta_queries)

        gta_global = expand_queries_for_language("GTA", "global")
        self.assertTrue(all(t["query"] == "GTA" for t in gta_global))

        # 3. Long-tail mixed keyword in Portuguese
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
        Email para contato: contato@ignorar.com
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
        self.assertNotIn("ignorar.com", extracted)

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

if __name__ == "__main__":
    unittest.main()
