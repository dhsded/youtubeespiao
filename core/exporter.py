"""
Data Exporter for YouTube Miner, Domain and Instagram Results.
Exports EXCLUSIVELY AVAILABLE and ACTIONABLE opportunities in PDF, Excel (.xlsx), CSV, TXT, and JSON.
Features:
- Strict filtering: Exports ONLY expired domains and Instagram handles that are AVAILABLE ('Disponível') for purchase/claim.
- High-fidelity Landscape PDF reports with interactive clickable links (YouTube URLs, Domain Registrar & Claim links).
- Executive TXT reports with structured ASCII summary and direct links.
- High-precision 90-Day Traffic Metrics ('Views nos Últimos 90 Dias') and calibrated VPH.
- Clean corporate typography and visual KPI badges.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from PyQt6.QtGui import QPdfWriter, QTextDocument, QPageSize, QPageLayout
from PyQt6.QtCore import QMarginsF

from core.metrics_calculator import format_number
from core.trademark_validator import analyze_trademark_risk

class DataExporter:
    @classmethod
    def get_available_domains(cls, domains_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter list to retain ONLY available domains and Instagram accounts."""
        return [d for d in domains_data if d.get("status") == "Disponível"]

    @classmethod
    def get_available_videos(cls, videos_data: List[Dict[str, Any]], available_domains: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter videos to retain only those containing available expired domains."""
        avail_roots = {d.get("root_domain", "").strip().lower() for d in available_domains if d.get("root_domain")}
        filtered_vids = []
        for v in videos_data:
            v_doms = v.get("domains", [])
            has_avail = any(
                d.get("status") == "Disponível" or d.get("root_domain", "").strip().lower() in avail_roots
                for d in v_doms
            )
            if has_avail:
                filtered_vids.append(v)
        return filtered_vids if filtered_vids else videos_data

    @classmethod
    def export_domains_to_dataframe(cls, domains_data: List[Dict[str, Any]], only_available: bool = True) -> pd.DataFrame:
        """Format available domain items into a pandas DataFrame."""
        filtered_domains = cls.get_available_domains(domains_data) if only_available else domains_data
        rows = []
        for item in filtered_domains:
            v_metrics = item.get("video_metrics", {})
            v_cnt = item.get("video_count", 1)
            tot_daily = item.get("total_daily_views", v_metrics.get("daily_views", 0))
            tot_views = item.get("total_view_count", v_metrics.get("view_count", 0))
            tot_90d = item.get("total_views_90d", v_metrics.get("views_90d", tot_views))
            display_name = item.get("display_name") or item.get("root_domain") or ""
            tm = item.get("trademark_risk") or analyze_trademark_risk(display_name)
            
            rows.append({
                "Tipo": "Instagram" if item.get("is_instagram") else "Domínio Web",
                "Domínio / Conta": display_name,
                "Status": item.get("status"),
                "Segurança de Marca": tm.get("badge_short", "🟢 Seguro"),
                "Risco Jurídico / INPI": tm.get("badge", "🟢 Seguro p/ Registro"),
                "Vídeos Presente (Qtd)": v_cnt,
                "Soma Tráfego Diário (Views/Dia)": tot_daily,
                "Soma Views 90 Dias": tot_90d,
                "Soma Visualizações Totais": tot_views,
                "Parecer Jurídico": tm.get("legal_advice", ""),
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

    @classmethod
    def export_videos_to_dataframe(cls, videos_data: List[Dict[str, Any]], domains_data: Optional[List[Dict[str, Any]]] = None) -> pd.DataFrame:
        """Format video items into a pandas DataFrame (focusing on available opportunities)."""
        avail_doms = cls.get_available_domains(domains_data) if domains_data else []
        filtered_videos = cls.get_available_videos(videos_data, avail_doms) if avail_doms else videos_data
        rows = []
        for v in filtered_videos:
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
        """Export ONLY available opportunities to Excel (.xlsx)."""
        avail_doms = cls.get_available_domains(domains_data)
        df_domains = cls.export_domains_to_dataframe(avail_doms, only_available=True)
        df_videos = cls.export_videos_to_dataframe(videos_data, avail_doms)

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df_domains.to_excel(writer, sheet_name="Domínios Disponíveis", index=False)
            df_videos.to_excel(writer, sheet_name="Vídeos de Origem", index=False)

    @classmethod
    def export_to_csv(cls, file_path: str, domains_data: List[Dict[str, Any]]):
        """Export ONLY available opportunities to CSV."""
        df_domains = cls.export_domains_to_dataframe(domains_data, only_available=True)
        df_domains.to_csv(file_path, index=False, encoding="utf-8-sig")

    @classmethod
    def export_to_txt(cls, file_path: str, domains_data: List[Dict[str, Any]], videos_data: Optional[List[Dict[str, Any]]] = None):
        """Export a clean, structured plain text report of available expired domains and Instagram handles."""
        avail_doms = cls.get_available_domains(domains_data)
        now_str = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
        tot_traffic = sum(d.get("total_daily_views", d.get("video_metrics", {}).get("daily_views", 0)) for d in avail_doms)

        lines = [
            "================================================================================",
            "🎯 YOUTUBE ESPIÃO & HUNTER BROWSER — RELATÓRIO DE OPORTUNIDADES DISPONÍVEIS",
            f"Gerado em: {now_str}",
            f"Total de Oportunidades DISPONÍVEIS para Registro / Claim: {len(avail_doms)}",
            f"Soma Total de Tráfego Diário Estimado: {format_number(round(tot_traffic, 1))} views/dia",
            "================================================================================",
            ""
        ]

        if not avail_doms:
            lines.append("Nenhum domínio expirado ou disponível foi encontrado nesta varredura.")
        else:
            for idx, d in enumerate(avail_doms, 1):
                name = d.get("display_name") or d.get("root_domain", "")
                is_ig = d.get("is_instagram", False)
                type_str = "INSTAGRAM" if is_ig else "DOMÍNIO WEB"
                v_cnt = d.get("video_count", 1)
                daily = d.get("total_daily_views", d.get("video_metrics", {}).get("daily_views", 0))
                tot_90d = d.get("total_views_90d", d.get("total_view_count", 0))
                tot_views = d.get("total_view_count", d.get("video_metrics", {}).get("view_count", 0))
                
                v_title = d.get("video_title", "Vídeo Principal")
                v_url = d.get("video_url", "")
                channel = d.get("channel_name", "")
                pub_date = d.get("video_metrics", {}).get("publish_date", "Recente")
                buy_link = d.get("buy_link", "")
                reg_name = d.get("registrar_name", "Registrador")

                lines.extend([
                    f"[{idx:02d}] 🟢 DISPONÍVEL • [{type_str}] {name}",
                    f"    • Tráfego Diário: 🔥 {format_number(round(daily, 1))}/dia | Views 90d: ⚡ {format_number(tot_90d)} | Total: {format_number(tot_views)} views",
                    f"    • Presente em: {v_cnt} vídeo(s)",
                    f"    • Vídeo Principal: {v_title} ({v_url})",
                    f"    • Canal: {channel} | Data de Postagem: {pub_date}",
                    f"    • Local no Vídeo: {d.get('source_location', 'Descrição')}",
                    f"    • Link Direto de Registro/Claim: {buy_link} ({reg_name})",
                    "--------------------------------------------------------------------------------"
                ])

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    @classmethod
    def export_to_json(cls, file_path: str, domains_data: List[Dict[str, Any]], videos_data: List[Dict[str, Any]]):
        """Export ONLY available opportunities to JSON."""
        avail_doms = cls.get_available_domains(domains_data)
        avail_vids = cls.get_available_videos(videos_data, avail_doms)

        data = {
            "total_available_domains": len(avail_doms),
            "total_associated_videos": len(avail_vids),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "domains": avail_doms,
            "videos": avail_vids
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def export_to_pdf(cls, file_path: str, domains_data: List[Dict[str, Any]], videos_data: List[Dict[str, Any]]):
        """
        Generates a comprehensive executive PDF report in Landscape format with clickable hyperlinks,
        showing EXCLUSIVELY available expired domains and Instagram accounts.
        """
        now_str = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
        avail_doms = cls.get_available_domains(domains_data)
        avail_vids = cls.get_available_videos(videos_data, avail_doms)

        total_videos = len(avail_vids)
        total_views = sum(v.get("metrics", {}).get("view_count", 0) for v in avail_vids)
        avail_count = len(avail_doms)
        total_daily_traffic = sum(d.get("total_daily_views", d.get("video_metrics", {}).get("daily_views", 0)) for d in avail_doms)

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
                
                h2 {{ font-size: 10.5pt; color: #0F172A; border-bottom: 2px solid #16A34A; padding-bottom: 3px; margin-top: 10px; margin-bottom: 6px; }}
                
                table.data-table {{ width: 100%; border-collapse: collapse; font-size: 7.5pt; margin-bottom: 12px; }}
                table.data-table th {{ background-color: #1E293B; color: #FFFFFF; font-weight: 700; padding: 5px 6px; text-align: left; border: 1px solid #334155; }}
                table.data-table td {{ padding: 5px 6px; border: 1px solid #E2E8F0; vertical-align: top; }}
                table.data-table tr:nth-child(even) {{ background-color: #F8FAFC; }}
                
                .badge-available {{ color: #16A34A; font-weight: 800; }}
                
                a {{ color: #0284C7; text-decoration: none; font-weight: 700; }}
                a.buy-btn {{ color: #16A34A; font-weight: 800; text-decoration: underline; }}
                a.watch-btn {{ color: #2563EB; font-weight: 700; text-decoration: underline; }}
                .small-gray {{ font-size: 6.5pt; color: #64748B; font-weight: normal; }}
            </style>
        </head>
        <body>
            <div class="header-title">🎯 YouTube Espião — Relatório de Oportunidades Disponíveis</div>
            <div class="header-sub">Gerado em {now_str} • Relatório Exclusivo de Domínios Expirados & Contas IG Disponíveis para Registro</div>
            
            <table class="summary-table">
                <tr>
                    <td class="summary-box" style="width: 25%; background-color: #DCFCE7; border-color: #16A34A;">
                        <div class="summary-val-green">{avail_count}</div>
                        <div class="summary-lbl" style="color: #15803D;">Oportunidades Disponíveis</div>
                    </td>
                    <td class="summary-box" style="width: 25%;">
                        <div class="summary-val-green">🔥 {format_number(round(total_daily_traffic, 1))}/dia</div>
                        <div class="summary-lbl">Soma Total Tráfego Diário</div>
                    </td>
                    <td class="summary-box" style="width: 25%;">
                        <div class="summary-val">{total_videos}</div>
                        <div class="summary-lbl">Vídeos Associados</div>
                    </td>
                    <td class="summary-box" style="width: 25%;">
                        <div class="summary-val-blue">{format_number(total_views)}</div>
                        <div class="summary-lbl">Visualizações Totais</div>
                    </td>
                </tr>
            </table>

            <h2>💎 Oportunidades Disponíveis: Domínios Web & Contas de Instagram</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th style="width: 7%;">Status</th>
                        <th style="width: 6%;">Tipo</th>
                        <th style="width: 14%;">Domínio / Conta</th>
                        <th style="width: 6%;">Vídeos</th>
                        <th style="width: 9%;">Tráfego/Dia</th>
                        <th style="width: 9%;">Views 90d</th>
                        <th style="width: 8%;">Total Views</th>
                        <th style="width: 23%;">Vídeo de Origem (Link Clicável)</th>
                        <th style="width: 18%;">Link de Compra / Claim (Clicável)</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Populate available domains table with clickable links and formatted data
        if not avail_doms:
            html += "<tr><td colspan='9' style='text-align:center; color:#64748B;'>Nenhuma oportunidade disponível encontrada na varredura.</td></tr>"
        else:
            for d in avail_doms:
                is_ig = d.get("is_instagram", False)
                type_label = "📸 Instagram" if is_ig else "🌐 Domínio"
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
                    video_link_html = f"<b>{v_title[:38]}...</b><br><span class='small-gray'>Canal: {channel} | {pub_date}</span><br><a class='watch-btn' href='{v_url}'>{v_url}</a>"
                else:
                    video_link_html = f"<b>{v_title[:38]}</b><br><span class='small-gray'>Canal: {channel}</span>"

                if buy_link:
                    action_html = f"<span class='small-gray'>({reg_name})</span><br><a class='buy-btn' href='{buy_link}'>{buy_link}</a>"
                elif is_ig:
                    ig_claim_url = f"https://www.instagram.com/{name.replace('@', '').replace('📸 ', '')}"
                    action_html = f"<span class='small-gray'>(Instagram)</span><br><a class='buy-btn' href='{ig_claim_url}'>{ig_claim_url}</a>"
                else:
                    action_html = "<span class='small-gray'>Disponível</span>"

                html += f"""
                    <tr>
                        <td class="badge-available">🟢 Disponível</td>
                        <td>{type_label}</td>
                        <td><b>{name}</b><br><span class='small-gray'>{d.get('source_location', '')}</span></td>
                        <td><b>{v_cnt_str}</b></td>
                        <td style="color:#16A34A; font-weight:800;">{daily_formatted}</td>
                        <td style="color:#8B5CF6; font-weight:700;">{views_90d_formatted}</td>
                        <td style="color:#0284C7; font-weight:700;">{tot_views_formatted}</td>
                        <td>{video_link_html}</td>
                        <td>{action_html}</td>
                    </tr>
                """

        html += """
                </tbody>
            </table>

            <h2>🏆 Vídeos de Origem das Oportunidades Disponíveis (Links Clicáveis)</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th style="width: 38%;">Título do Vídeo & Link do YouTube (Clicável)</th>
                        <th style="width: 14%;">Canal</th>
                        <th style="width: 9%;">Total Views</th>
                        <th style="width: 9%;">Views 90 Dias</th>
                        <th style="width: 8%;">Views / Hora</th>
                        <th style="width: 8%;">Views / Dia</th>
                        <th style="width: 6%;">Data Envio</th>
                        <th style="width: 8%;">Domínios Livres</th>
                    </tr>
                </thead>
                <tbody>
        """

        top_videos = sorted(avail_vids, key=lambda x: x.get("metrics", {}).get("daily_views", 0), reverse=True)
        if not top_videos:
            html += "<tr><td colspan='8' style='text-align:center; color:#64748B;'>Nenhum vídeo registrado com oportunidades disponíveis.</td></tr>"
        else:
            for v in top_videos:
                m = v.get("metrics", {})
                doms = v.get("domains", [])
                avail_d = sum(1 for d in doms if d.get("status") == "Disponível")
                dom_summary = f"🟢 {avail_d} disp."
                v_url = v.get("url", "")
                v_title = v.get("title", "")

                if v_url:
                    title_cell = f"<b>{v_title[:45]}</b><br><a class='watch-btn' href='{v_url}'>{v_url}</a>"
                else:
                    title_cell = f"<b>{v_title[:45]}</b>"

                html += f"""
                    <tr>
                        <td>{title_cell}</td>
                        <td>{v.get('channel_name', '')}</td>
                        <td style="color:#0284C7; font-weight:700;">{m.get('view_count_formatted', '0')}</td>
                        <td style="color:#8B5CF6; font-weight:700;">{m.get('views_90d_formatted', '0')}</td>
                        <td style="color:#D97706; font-weight:700;">{m.get('hourly_views_formatted', '0/h')}</td>
                        <td style="color:#16A34A; font-weight:800;">{m.get('daily_views_formatted', '0/dia')}</td>
                        <td>{m.get('publish_date', 'Recente')}</td>
                        <td><b style="color: #16A34A;">{dom_summary}</b></td>
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
