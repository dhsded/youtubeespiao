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
        """Test calculation of hourly, daily, monthly, and annual view averages."""
        ten_days_ago = datetime.now(timezone.utc) - timedelta(days=10)
        metrics = calculate_video_metrics(view_count=24000, upload_date=ten_days_ago)

        self.assertEqual(metrics["view_count"], 24000)
        self.assertAlmostEqual(metrics["daily_views"], 2400.0, delta=20.0)
        self.assertAlmostEqual(metrics["hourly_views"], 100.0, delta=2.0)
        self.assertGreater(metrics["monthly_views"], 70000)
        self.assertGreater(metrics["yearly_views"], 800000)
        self.assertIn("24K", metrics["view_count_formatted"])

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

if __name__ == "__main__":
    unittest.main()
