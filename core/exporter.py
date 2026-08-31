"""
Data Exporter for YouTube Miner, Domain and Instagram Results.
Exports comprehensive executive reports in PDF, Excel (.xlsx), CSV, and JSON.
Features:
- High-fidelity Landscape PDF reports with interactive clickable links (YouTube URLs, Domain Registrar & Claim links).
- High-precision 90-Day Traffic Metrics ('Views nos Últimos 90 Dias') and calibrated VPH.
- Complete data columns: Video Count, Cumulative Daily Traffic, 90-Day Views, Total Views, Upload Date, and WHOIS details.
- Clean corporate typography and visual KPI badges.
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
            v_cnt = item.get("video_count", 1)
            tot_daily = item.get("total_daily_views", v_metrics.get("daily_views", 0))
            tot_views = item.get("total_view_count", v_metrics.get("view_count", 0))
            tot_90d = item.get("total_views_90d", v_metrics.get("views_90d", tot_views))
            
            rows.append({
                "Tipo": "Instagram" if item.get("is_instagram") else "Domínio Web",
                "Domínio / Conta": item.get("display_name") or item.get("root_domain"),
                "Status": item.get("status"),
                "Vídeos Presente (Qtd)": v_cnt,
                "Soma Tráfego Diário (Views/Dia)": tot_daily,
                "Soma Views 90 Dias": tot_90d,
                "Soma Visualizações Totais": tot_views,
                "Detalhes": item.get("details"),
                "Título do Vídeo Principal": item.get("video_title"),
                "Canal": item.get("channel_name"),
                "Views por Hora (VPH)": item.get("total_hourly_views", v_metrics.get("hourly_views", 0)),
                "Views por Dia (Média)": tot_daily,
                "Views por Mês (Média)": item.get("total_monthly_views", v_metrics.get("monthly_views", 0)),
                "Views por Ano (Média)": item.get("total_yearly_views", v_metrics.get("yearly_views", 0)),
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
                "Views nos Últimos 90 Dias": metrics.get("views_90d", metrics.get("view_count", 0)),
                "Views/Hora (VPH)": metrics.get("hourly_views", 0),
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
        Generates a comprehensive executive PDF report in Landscape format with clickable hyperlinks,
        90-day traffic metrics, domain purchase links, and video source links.
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
                body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #0F172A; font-size: 8pt; line-height: 1.35; }}
                .header-title {{ font-size: 14pt; font-weight: 800; color: #1E3A8A; margin-bottom: 2px; }}
                .header-sub {{ font-size: 8pt; color: #64748B; margin-bottom: 10px; }}
                .summary-table {{ width: 100%; border-collapse: collapse; margin-bottom: 12px; }}
                .summary-box {{ background-color: #F8FAFC; border: 1px solid #CBD5E1; padding: 6px 10px; text-align: center; border-radius: 4px; }}
                .summary-val {{ font-size: 12pt; font-weight: 800; color: #0F172A; }}
                .summary-val-blue {{ font-size: 12pt; font-weight: 800; color: #0284C7; }}
                .summary-val-purple {{ font-size: 12pt; font-weight: 800; color: #7C3AED; }}
                .summary-val-green {{ font-size: 12pt; font-weight: 800; color: #16A34A; }}
                .summary-lbl {{ font-size: 7.5pt; color: #475569; text-transform: uppercase; font-weight: 700; }}
                
                h2 {{ font-size: 10.5pt; color: #0F172A; border-bottom: 2px solid #2563EB; padding-bottom: 3px; margin-top: 10px; margin-bottom: 6px; }}
                
                table.data-table {{ width: 100%; border-collapse: collapse; font-size: 7.5pt; margin-bottom: 12px; }}
                table.data-table th {{ background-color: #1E293B; color: #FFFFFF; font-weight: 700; padding: 5px 6px; text-align: left; border: 1px solid #334155; }}
                table.data-table td {{ padding: 5px 6px; border: 1px solid #E2E8F0; vertical-align: top; }}
                table.data-table tr:nth-child(even) {{ background-color: #F8FAFC; }}
                
                .badge-available {{ color: #16A34A; font-weight: 800; }}
                .badge-inactive {{ color: #D97706; font-weight: 700; }}
                .badge-active {{ color: #DC2626; }}
                
                a {{ color: #0284C7; text-decoration: none; font-weight: 700; }}
                a.buy-btn {{ color: #16A34A; font-weight: 800; text-decoration: underline; }}
                a.watch-btn {{ color: #2563EB; font-weight: 700; text-decoration: underline; }}
                .small-gray {{ font-size: 6.5pt; color: #64748B; font-weight: normal; }}
            </style>
        </head>
        <body>
            <div class="header-title">🎯 YouTube Espião & Hunter Browser — Relatório Executivo de Mineração</div>
            <div class="header-sub">Gerado em {now_str} • Relatório de Oportunidades & Análise de Tráfego Recente (90 Dias & VPH)</div>
            
            <table class="summary-table">
                <tr>
                    <td class="summary-box" style="width: 25%;">
                        <div class="summary-val">{total_videos}</div>
                        <div class="summary-lbl">Vídeos Minerados</div>
                    </td>
                    <td class="summary-box" style="width: 25%;">
                        <div class="summary-val-blue">{format_number(total_views)}</div>
                        <div class="summary-lbl">Visualizações Totais</div>
                    </td>
                    <td class="summary-box" style="width: 25%;">
                        <div class="summary-val-purple">{total_domains}</div>
                        <div class="summary-lbl">Oportunidades Analisadas</div>
                    </td>
                    <td class="summary-box" style="width: 25%; background-color: #DCFCE7; border-color: #16A34A;">
                        <div class="summary-val-green">{avail_count}</div>
                        <div class="summary-lbl" style="color: #15803D;">Disponíveis p/ Compra/Claim</div>
                    </td>
                </tr>
            </table>

            <h2>💎 Oportunidades: Domínios e Contas de Instagram (Agregados por Tráfego)</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th style="width: 8%;">Status</th>
                        <th style="width: 6%;">Tipo</th>
                        <th style="width: 15%;">Domínio / Conta</th>
                        <th style="width: 7%;">Vídeos</th>
                        <th style="width: 10%;">Soma Tráfego/Dia</th>
                        <th style="width: 10%;">Views 90 Dias</th>
                        <th style="width: 9%;">Views Totais</th>
                        <th style="width: 19%;">Vídeo Principal (Link YouTube)</th>
                        <th style="width: 7%;">Data Envio</th>
                        <th style="width: 9%;">Ação Compra</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Populate domains table with clickable links and formatted data
        if not domains_data:
            html += "<tr><td colspan='10' style='text-align:center; color:#64748B;'>Nenhuma oportunidade encontrada na varredura.</td></tr>"
        else:
            for d in domains_data:
                status = d.get("status", "Desconhecido")
                is_ig = d.get("is_instagram", False)
                type_label = "📸 Instagram" if is_ig else "🌐 Domínio"
                badge_class = "badge-available" if status == "Disponível" else ("badge-inactive" if status == "Inativo" else "badge-active")
                badge_icon = d.get("badge_icon", "⚪")
                name = d.get("display_name") or d.get("root_domain", "")
                
                v_cnt = d.get("video_count", 1)
                v_cnt_str = f"🎯 {v_cnt} vídeos" if v_cnt > 1 else "🎯 1 vídeo"
                
                tot_daily = d.get("total_daily_views", d.get("video_metrics", {}).get("daily_views", 0))
                daily_formatted = f"🔥 {format_number(round(tot_daily, 1))}/dia"
                
                tot_90d = d.get("total_views_90d", d.get("total_view_count", 0))
                views_90d_formatted = f"⚡ {format_number(tot_90d)}"
                
                tot_views = d.get("total_view_count", d.get("video_metrics", {}).get("view_count", 0))
                tot_views_formatted = format_number(tot_views)
                
                v_title = d.get("video_title", "Vídeo")
                v_url = d.get("video_url", "")
                channel = d.get("channel_name", "")
                pub_date = d.get("video_metrics", {}).get("publish_date", "Recente")
                
                buy_link = d.get("buy_link", "")
                reg_name = d.get("registrar_name", "Registrar")

                if v_url:
                    video_link_html = f"<a class='watch-btn' href='{v_url}'>{v_title[:40]}... ↗</a><br><span class='small-gray'>Canal: {channel}</span>"
                else:
                    video_link_html = f"<b>{v_title[:40]}</b><br><span class='small-gray'>Canal: {channel}</span>"

                if buy_link and status == "Disponível":
                    action_html = f"<a class='buy-btn' href='{buy_link}'>🛒 Comprar ({reg_name}) ↗</a>"
                elif is_ig and status == "Disponível":
                    ig_claim_url = f"https://www.instagram.com/{name.replace('@', '')}"
                    action_html = f"<a class='buy-btn' href='{ig_claim_url}'>📸 Reivindicar IG ↗</a>"
                else:
                    action_html = f"<span class='small-gray'>{d.get('details', '')[:30]}</span>"

                html += f"""
                    <tr>
                        <td class="{badge_class}">{badge_icon} {status}</td>
                        <td>{type_label}</td>
                        <td><b>{name}</b><br><span class='small-gray'>{d.get('source_location', '')}</span></td>
                        <td><b>{v_cnt_str}</b></td>
                        <td style="color:#16A34A; font-weight:800;">{daily_formatted}</td>
                        <td style="color:#8B5CF6; font-weight:700;">{views_90d_formatted}</td>
                        <td style="color:#0284C7; font-weight:700;">{tot_views_formatted}</td>
                        <td>{video_link_html}</td>
                        <td>{pub_date}</td>
                        <td>{action_html}</td>
                    </tr>
                """

        html += """
                </tbody>
            </table>

            <h2>🏆 Vídeos Minerados & Desempenho de Tráfego Recente (Links Clicáveis)</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th style="width: 30%;">Título do Vídeo (Clique para Assistir)</th>
                        <th style="width: 14%;">Canal</th>
                        <th style="width: 9%;">Total Views</th>
                        <th style="width: 10%;">Views 90 Dias</th>
                        <th style="width: 9%;">Views / Hora</th>
                        <th style="width: 9%;">Views / Dia</th>
                        <th style="width: 8%;">Data Envio</th>
                        <th style="width: 11%;">Domínios</th>
                    </tr>
                </thead>
                <tbody>
        """

        top_videos = sorted(videos_data, key=lambda x: x.get("metrics", {}).get("daily_views", 0), reverse=True)
        if not top_videos:
            html += "<tr><td colspan='8' style='text-align:center; color:#64748B;'>Nenhum vídeo registrado.</td></tr>"
        else:
            for v in top_videos:
                m = v.get("metrics", {})
                doms = v.get("domains", [])
                avail_d = sum(1 for d in doms if d.get("status") == "Disponível")
                dom_summary = f"🟢 {avail_d} disp. | Total: {len(doms)}"
                v_url = v.get("url", "")
                v_title = v.get("title", "")

                if v_url:
                    title_cell = f"<a class='watch-btn' href='{v_url}'>{v_title[:50]} ↗</a>"
                else:
                    title_cell = f"<b>{v_title[:50]}</b>"

                html += f"""
                    <tr>
                        <td>{title_cell}</td>
                        <td>{v.get('channel_name', '')}</td>
                        <td style="color:#0284C7; font-weight:700;">{m.get('view_count_formatted', '0')}</td>
                        <td style="color:#8B5CF6; font-weight:700;">{m.get('views_90d_formatted', '0')}</td>
                        <td style="color:#D97706; font-weight:700;">{m.get('hourly_views_formatted', '0/h')}</td>
                        <td style="color:#16A34A; font-weight:800;">{m.get('daily_views_formatted', '0/dia')}</td>
                        <td>{m.get('publish_date', 'Recente')}</td>
                        <td><b>{dom_summary}</b></td>
                    </tr>
                """

        html += """
                </tbody>
            </table>
        </body>
        </html>
        """

        # Render HTML to PDF in Landscape A4
        doc = QTextDocument()
        doc.setHtml(html)

        writer = QPdfWriter(file_path)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setPageOrientation(QPageLayout.Orientation.Landscape)
        writer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Unit.Millimeter)

        doc.print(writer)
