import sys
import os
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.youtube_crawler import YouTubeCrawler

def test_live_search():
    crawler = YouTubeCrawler()
    print("Iniciando teste de busca ao vivo no YouTube...")
    
    results = crawler.process_keyword(
        keyword="curso dropshipping",
        max_videos=3,
        sort_by="view_count",
        on_video_processed=lambda v: print(f"-> Vídeo: {v['title'][:40]} | Views: {v['metrics']['view_count_formatted']} | Média: {v['metrics']['daily_views_formatted']}"),
        on_domain_found=lambda d: print(f"   -> Domínio: {d['root_domain']} [{d['status']}] (Fonte: {d['source_location']})"),
        on_progress=lambda cur, tot, msg: print(f"[{cur}/{tot}] {msg}")
    )
    
    print("\n--- Resumo do Teste ---")
    print(f"Total de Vídeos: {results['total_videos']}")
    print(f"Total de Domínios: {results['total_domains']}")
    print(f"Domínios Disponíveis: {results['available_domains']}")
    assert results["total_videos"] > 0, "Deveria encontrar ao menos 1 vídeo"
    print("✅ Teste de integração ao vivo concluído com sucesso!")

if __name__ == "__main__":
    test_live_search()
