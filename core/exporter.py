"""
Data Exporter for YouTube Miner, Domain and Instagram Results.
Exports comprehensive executive reports in PDF, Excel (.xlsx), CSV, and JSON.
"""

import json
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
from PyQt6.QtGui import QPdfWriter, QTextDocument, QPageSize, QPageLayout
from PyQt6.QtCore import QMarginsF

from core.metrics_calculator import format_number

class DataExporter:
    @staticmethod
    def export_domains_to_dataframe(domains_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Format domain items into a pandas DataFrame."""
        rows = []
        for item in domains_data:
            v_metrics = item.get("video_metrics", {})
            rows.append({
                "Tipo": "Instagram" if item.get("is_instagram") else "Domínio Web",
                "Domínio / Conta": item.get("display_name") or item.get("root_domain"),
                "Status": item.get("status"),
                "Detalhes": item.get("details"),
                "Título do Vídeo": item.get("video_title"),
                "Canal": item.get("channel_name"),
                "Views por Hora (Média)": v_metrics.get("hourly_views", 0),
                "Views por Dia (Média)": v_metrics.get("daily_views", 0),
                "Views por Mês (Média)": v_metrics.get("monthly_views", 0),
                "Views por Ano (Média)": v_metrics.get("yearly_views", 0),
                "Visualizações Totais": v_metrics.get("view_count", 0),
                "Data de Publicação": v_metrics.get("publish_date", ""),
                "Origem no Vídeo": item.get("source_location"),
                "Link p/ Compra / Claim": item.get("buy_link"),
                "URL do Vídeo": item.get("video_url")
            })
        return pd.DataFrame(rows)

    @staticmethod
    def export_videos_to_dataframe(videos_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Format video items into a pandas DataFrame."""
        rows = []
        for v in videos_data:
            metrics = v.get("metrics", {})
            rows.append({
                "Título": v.get("title"),
                "Canal": v.get("channel_name"),
                "Visualizações Totais": metrics.get("view_count", 0),
                "Views/Hora": metrics.get("hourly_views", 0),
                "Views/Dia": metrics.get("daily_views", 0),
                "Views/Mês": metrics.get("monthly_views", 0),
                "Views/Ano": metrics.get("yearly_views", 0),
                "Data de Publicação": metrics.get("publish_date", ""),
                "Desempenho": metrics.get("velocity_badge", ""),
                "Qtd Domínios": len(v.get("domains", [])),
                "Domínios Disponíveis": sum(1 for d in v.get("domains", []) if d.get("status") == "Disponível"),
                "URL do Vídeo": v.get("url")
            })
        return pd.DataFrame(rows)

    @classmethod
    def export_to_excel(cls, file_path: str, domains_data: List[Dict[str, Any]], videos_data: List[Dict[str, Any]]):
        df_domains = cls.export_domains_to_dataframe(domains_data)
        df_videos = cls.export_videos_to_dataframe(videos_data)

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df_domains.to_excel(writer, sheet_name="Oportunidades Expiradas", index=False)
            df_videos.to_excel(writer, sheet_name="Vídeos Minerados", index=False)

    @classmethod
    def export_to_csv(cls, file_path: str, domains_data: List[Dict[str, Any]]):
        df_domains = cls.export_domains_to_dataframe(domains_data)
        df_domains.to_csv(file_path, index=False, encoding="utf-8-sig")

    @classmethod
    def export_to_json(cls, file_path: str, domains_data: List[Dict[str, Any]], videos_data: List[Dict[str, Any]]):
        data = {
            "total_domains": len(domains_data),
            "total_videos": len(videos_data),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "domains": domains_data,
            "videos": videos_data
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def export_to_pdf(cls, file_path: str, domains_data: List[Dict[str, Any]], videos_data: List[Dict[str, Any]]):
        """
        Generates a clean executive PDF report using QTextDocument and QPdfWriter.
        """
        now_str = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
        total_videos = len(videos_data)
        total_views = sum(v.get("metrics", {}).get("view_count", 0) for v in videos_data)
        total_domains = len(domains_data)
        avail_count = sum(1 for d in domains_data if d.get("status") == "Disponível")

        # HTML document structure
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #1E293B; font-size: 10pt; line-height: 1.3; }}
                .header-title {{ font-size: 16pt; font-weight: bold; color: #1E3A8A; margin-bottom: 2px; }}
                .header-sub {{ font-size: 9pt; color: #64748B; margin-bottom: 12px; }}
                .summary-table {{ width: 100%; border-collapse: collapse; margin-bottom: 16px; }}
                .summary-box {{ background-color: #F1F5F9; border: 1px solid #CBD5E1; padding: 8px; text-align: center; border-radius: 4px; }}
                .summary-val {{ font-size: 13pt; font-weight: bold; color: #0F172A; }}
                .summary-val-green {{ font-size: 13pt; font-weight: bold; color: #16A34A; }}
                .summary-lbl {{ font-size: 8pt; color: #64748B; text-transform: uppercase; font-weight: bold; }}
                
                h2 {{ font-size: 12pt; color: #0F172A; border-bottom: 2px solid #2563EB; padding-bottom: 4px; margin-top: 14px; margin-bottom: 8px; }}
                
                table.data-table {{ width: 100%; border-collapse: collapse; font-size: 8.5pt; margin-bottom: 14px; }}
                table.data-table th {{ background-color: #1E293B; color: #FFFFFF; font-weight: bold; padding: 6px; text-align: left; border: 1px solid #334155; }}
                table.data-table td {{ padding: 5px; border: 1px solid #E2E8F0; vertical-align: middle; }}
                table.data-table tr:nth-child(even) {{ background-color: #F8FAFC; }}
                
                .badge-available {{ color: #16A34A; font-weight: bold; }}
                .badge-inactive {{ color: #CA8A04; font-weight: bold; }}
                .badge-active {{ color: #DC2626; }}
            </style>
        </head>
        <body>
            <div class="header-title">🎯 YouTube Espião — Relatório de Mineração & Oportunidades</div>
            <div class="header-sub">Gerado em {now_str} • Relatório Executivo</div>
            
            <table class="summary-table">
                <tr>
                    <td class="summary-box" style="width: 25%;">
                        <div class="summary-val">{total_videos}</div>
                        <div class="summary-lbl">Vídeos Minerados</div>
                    </td>
                    <td class="summary-box" style="width: 25%;">
                        <div class="summary-val">{format_number(total_views)}</div>
                        <div class="summary-lbl">Visualizações Totais</div>
                    </td>
                    <td class="summary-box" style="width: 25%;">
                        <div class="summary-val">{total_domains}</div>
                        <div class="summary-lbl">Oportunidades Analisadas</div>
                    </td>
                    <td class="summary-box" style="width: 25%; background-color: #F0FDF4; border-color: #16A34A;">
                        <div class="summary-val-green">{avail_count}</div>
                        <div class="summary-lbl" style="color: #16A34A;">Disponíveis p/ Compra</div>
                    </td>
                </tr>
            </table>

            <h2>💎 Domínios e Contas de Instagram Expirados / Disponíveis</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th style="width: 12%;">Status</th>
                        <th style="width: 25%;">Domínio / Conta</th>
                        <th style="width: 33%;">Vídeo Associado & Canal</th>
                        <th style="width: 10%;">Views / Hora</th>
                        <th style="width: 10%;">Views / Dia</th>
                        <th style="width: 10%;">Total Views</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Populate domains
        if not domains_data:
            html += "<tr><td colspan='6' style='text-align:center; color:#64748B;'>Nenhuma oportunidade encontrada.</td></tr>"
        else:
            for d in domains_data:
                status = d.get("status", "")
                badge_class = "badge-available" if status == "Disponível" else ("badge-inactive" if status == "Inativo" else "badge-active")
                badge_icon = d.get("badge_icon", "⚪")
                name = d.get("display_name") or d.get("root_domain", "")
                v_title = d.get("video_title", "")[:45]
                channel = d.get("channel_name", "")
                m = d.get("video_metrics", {})

                html += f"""
                    <tr>
                        <td class="{badge_class}">{badge_icon} {status}</td>
                        <td><b>{name}</b><br><span style="font-size:7.5pt; color:#64748B;">{d.get('source_location', '')}</span></td>
                        <td>{v_title}<br><span style="font-size:7.5pt; color:#64748B;">Canal: {channel}</span></td>
                        <td><b>{m.get('hourly_views_formatted', '0/h')}</b></td>
                        <td><b>{m.get('daily_views_formatted', '0/dia')}</b></td>
                        <td>{m.get('view_count_formatted', '0')}</td>
                    </tr>
                """

        html += """
                </tbody>
            </table>

            <h2>🏆 Top Vídeos com Maior Velocidade de Tráfego</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th style="width: 40%;">Título do Vídeo</th>
                        <th style="width: 20%;">Canal</th>
                        <th style="width: 13%;">Total Views</th>
                        <th style="width: 13%;">Média / Dia</th>
                        <th style="width: 14%;">Domínios</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Populate top videos (up to 30)
        top_videos = sorted(videos_data, key=lambda x: x.get("metrics", {}).get("daily_views", 0), reverse=True)[:30]
        if not top_videos:
            html += "<tr><td colspan='5' style='text-align:center; color:#64748B;'>Nenhum vídeo registrado.</td></tr>"
        else:
            for v in top_videos:
                m = v.get("metrics", {})
                doms = v.get("domains", [])
                avail_d = sum(1 for d in doms if d.get("status") == "Disponível")
                dom_summary = f"🟢 {avail_d} disp. (Total {len(doms)})"

                html += f"""
                    <tr>
                        <td><b>{v.get('title', '')[:50]}</b></td>
                        <td>{v.get('channel_name', '')}</td>
                        <td>{m.get('view_count_formatted', '0')}</td>
                        <td><b>{m.get('daily_views_formatted', '0/dia')}</b></td>
                        <td>{dom_summary}</td>
                    </tr>
                """

        html += """
                </tbody>
            </table>
        </body>
        </html>
        """

        # Render HTML to PDF
        doc = QTextDocument()
        doc.setHtml(html)

        writer = QPdfWriter(file_path)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setPageOrientation(QPageLayout.Orientation.Portrait)
        writer.setPageMargins(QMarginsF(12, 12, 12, 12), QPageLayout.Unit.Millimeter)

        doc.print(writer)
