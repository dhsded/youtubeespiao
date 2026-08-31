"""
Help & Documentation Dialog (Centro de Ajuda & Metodologia Didática).
Explains all formulas, traffic calculations, domain validation mechanics, DNS/WHOIS logic,
Instagram checking, and harvesting strategies with clear didactic breakdowns.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QTextBrowser, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📖 Manual & Metodologia — YouTube Espião")
        self.resize(880, 640)
        self.setMinimumSize(700, 500)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        # Header Title
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #1E293B; border-radius: 8px; padding: 10px 16px;")
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_title = QLabel("📖 Central de Ajuda, Metodologia e Fórmulas de Cálculo")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #38BDF8;")
        h_layout.addWidget(lbl_title)
        h_layout.addStretch()

        btn_close = QPushButton("✕ Fechar")
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.clicked.connect(self.accept)
        h_layout.addWidget(btn_close)

        layout.addWidget(header_frame)

        # Tabs Container
        tabs = QTabWidget()
        tabs.setObjectName("help_tabs")

        # Tab 1: Fórmulas de Tráfego
        tab_traffic = QTextBrowser()
        tab_traffic.setOpenExternalLinks(True)
        tab_traffic.setHtml(self._get_traffic_html())
        tabs.addTab(tab_traffic, "📊 Fórmulas de Tráfego")

        # Tab 2: Validação de Domínios
        tab_domain = QTextBrowser()
        tab_domain.setOpenExternalLinks(True)
        tab_domain.setHtml(self._get_domain_html())
        tabs.addTab(tab_domain, "🟢 Validação de Domínios")

        # Tab 3: Instagram & Redes
        tab_instagram = QTextBrowser()
        tab_instagram.setOpenExternalLinks(True)
        tab_instagram.setHtml(self._get_instagram_html())
        tabs.addTab(tab_instagram, "📸 Validação do Instagram")

        # Tab 4: Modos de Busca & Canais
        tab_search = QTextBrowser()
        tab_search.setOpenExternalLinks(True)
        tab_search.setHtml(self._get_search_html())
        tabs.addTab(tab_search, "🎯 Busca & Canais")

        layout.addWidget(tabs, 1)

    def _get_traffic_html(self) -> str:
        return """
        <style>
            body { font-family: 'Segoe UI', sans-serif; font-size: 13px; line-height: 1.6; color: #E2E8F0; }
            h2 { color: #38BDF8; margin-top: 10px; margin-bottom: 6px; font-size: 16px; }
            h3 { color: #818CF8; margin-top: 12px; margin-bottom: 4px; font-size: 14px; }
            .card { background-color: #1E293B; border: 1px solid #334155; border-radius: 6px; padding: 12px; margin-bottom: 12px; }
            .formula { background-color: #0F172A; border-left: 4px solid #38BDF8; padding: 8px 12px; font-family: monospace; font-size: 13px; color: #F8FAFC; margin: 6px 0; }
            .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; }
            .highlight { color: #F59E0B; font-weight: bold; }
        </style>
        <body>
            <h2>Como os Cálculos de Tráfego são Realizados</h2>
            <p>O YouTube Espião calcula o <b>volume real e projetado de visualizações passivas</b> de cada vídeo desde a data de postagem até o dia de hoje, permitindo avaliar com precisão o tráfego gerado por links presentes na descrição ou no comentário fixado.</p>

            <div class="card">
                <h3>1. Tempo Ativo do Vídeo</h3>
                <div class="formula">Dias Ativos = Data Atual (Hoje) - Data de Postagem do Vídeo</div>
                <p>Calculado com base no carimbo de data/hora (timestamp) oficial do YouTube. Vídeos postados hoje têm um valor mínimo de 1 hora ativa para evitar divisão por zero.</p>
            </div>

            <div class="card">
                <h3>2. Visualizações por Dia (Views / Dia)</h3>
                <div class="formula">Views / Dia = Total de Visualizações ÷ Dias Ativos</div>
                <p>Representa o <b>fluxo médio diário contínuo</b> de visitantes que assistem àquele vídeo. Exemplo: um vídeo com 365.000 visualizações postado há 1 ano (365 dias) gera em média <b>1.000 views/dia</b>.</p>
            </div>

            <div class="card">
                <h3>3. Visualizações por Hora (Views / Hora)</h3>
                <div class="formula">Views / Hora = Total de Visualizações ÷ Horas Ativas</div>
                <p>Mede a velocidade instantânea do vídeo. Útil para identificar vídeos com alta taxa de viralização recente.</p>
            </div>

            <div class="card">
                <h3>4. Projeções Mensal e Anual</h3>
                <div class="formula">Views / Mês = Views / Dia × 30.416</div>
                <div class="formula">Views / Ano = Views / Dia × 365.25</div>
                <p>Permite estimar o potencial acumulado de tráfego passivo ao longo dos meses.</p>
            </div>

            <div class="card">
                <h3>5. 🔥 Soma do Tráfego Diário Acumulado (Múltiplos Vídeos)</h3>
                <div class="formula">Soma Tráfego Diário = (Views/Dia do Vídeo 1) + (Views/Dia do Vídeo 2) + ... + (Views/Dia do Vídeo N)</div>
                <p>Quando o mesmo domínio aparece em <b>vários vídeos de um canal ou pesquisa</b> (ex: em 5 vídeos que juntos somam 15.000 views/dia), o sistema agrega todos esses vídeos em uma única linha e calcula a <b>soma total do tráfego diário</b> gerado para aquele domínio.</p>
            </div>
        </body>
        """

    def _get_domain_html(self) -> str:
        return """
        <style>
            body { font-family: 'Segoe UI', sans-serif; font-size: 13px; line-height: 1.6; color: #E2E8F0; }
            h2 { color: #10B981; margin-top: 10px; margin-bottom: 6px; font-size: 16px; }
            h3 { color: #38BDF8; margin-top: 12px; margin-bottom: 4px; font-size: 14px; }
            .card { background-color: #1E293B; border: 1px solid #334155; border-radius: 6px; padding: 12px; margin-bottom: 12px; }
            .status-box { padding: 8px 12px; border-radius: 6px; margin: 6px 0; }
            .avail { background-color: rgba(16, 185, 129, 0.15); border-left: 4px solid #10B981; }
            .inact { background-color: rgba(245, 158, 11, 0.15); border-left: 4px solid #F59E0B; }
            .act { background-color: rgba(239, 68, 68, 0.15); border-left: 4px solid #EF4444; }
        </style>
        <body>
            <h2>Como um Domínio é Validado como Livre / Disponível</h2>
            <p>O YouTube Espião executa um pipeline de <b>3 camadas de validação técnica em tempo real</b> para garantir que um domínio marcado como disponível realmente esteja livre para compra imediata.</p>

            <div class="card">
                <h3>1ª Camada: Desencurtamento de Links & Redirecionamentos</h3>
                <p>O robô resolve automaticamente links encurtados (bit.ly, tinyurl, linktr.ee, abre.ai), códigos HTTP 301/302 e meta-tags HTML de redirecionamento para extrair o <b>domínio raiz final</b> (ex: <i>siteantigo.com.br</i>).</p>
            </div>

            <div class="card">
                <h3>2ª Camada: Resolução DNS Multi-Servidor</h3>
                <p>O validador consulta servidores DNS raiz em busca de registros <code>A</code>, <code>AAAA</code>, <code>NS</code> (Nameservers), <code>CNAME</code> e <code>SOA</code>. Se o domínio responder com <b>NXDOMAIN</b> (Domínio Inexistente) ou não possuir servidores DNS autoritativos, ele avança para o teste conclusivo.</p>
            </div>

            <div class="card">
                <h3>3ª Camada: Consulta de Registro Oficial (WHOIS & RDAP)</h3>
                <p>O sistema faz uma consulta direta na autoridade de registro (Registro.br para extensões <code>.br</code>, e ICANN RDAP / WHOIS para <code>.com</code>, <code>.net</code>, <code>.org</code>, etc.).</p>

                <div class="status-box avail">
                    <b>🟢 Disponível para Registro:</b> O domínio não possui titular ativo e não possui DNS. Está 100% livre para ser registrado em registradores oficiais (Registro.br, Namecheap, GoDaddy).
                </div>

                <div class="status-box inact">
                    <b>🟡 Inativo:</b> O domínio possui um titular no WHOIS, porém não possui DNS ativo configurado ou a hospedagem foi desativada (site fora do ar).
                </div>

                <div class="status-box act">
                    <b>🔴 Ativo:</b> O domínio está registrado e possui servidores DNS em operação (site funcionando).
                </div>
            </div>
        </body>
        """

    def _get_instagram_html(self) -> str:
        return """
        <style>
            body { font-family: 'Segoe UI', sans-serif; font-size: 13px; line-height: 1.6; color: #E2E8F0; }
            h2 { color: #EC4899; margin-top: 10px; margin-bottom: 6px; font-size: 16px; }
            h3 { color: #818CF8; margin-top: 12px; margin-bottom: 4px; font-size: 14px; }
            .card { background-color: #1E293B; border: 1px solid #334155; border-radius: 6px; padding: 12px; margin-bottom: 12px; }
        </style>
        <body>
            <h2>Validação de Contas e @Handles do Instagram</h2>
            <p>O programa detecta links diretos (<code>instagram.com/usuario</code>) e menções de texto (ex: <code>siga no insta @nomedaloja</code>) presentes na descrição ou nos comentários dos vídeos.</p>

            <div class="card">
                <h3>1. Extração Inteligente de Handles</h3>
                <p>Ignora caminhos reservados do sistema (ex: <i>/explore</i>, <i>/reels</i>, <i>/developer</i>, <i>/terms</i>) e evita falsos positivos em endereços de e-mail (ex: <i>contato@gmail.com</i> não é capturado como perfil).</p>
            </div>

            <div class="card">
                <h3>2. Verificação de Status da Conta</h3>
                <p>O sistema faz uma checagem HTTP em tempo real:</p>
                <ul>
                    <li><b>🟢 Disponível / Deletado:</b> O perfil retornou erro HTTP 404 (Página não encontrada) ou a conta foi excluída/abandonada pelo criador original. O nome de usuário pode ser reivindicado (claim) no Instagram.</li>
                    <li><b>🔴 Ativo:</b> O perfil existe e está funcionando normalmente no Instagram.</li>
                </ul>
            </div>
        </body>
        """

    def _get_search_html(self) -> str:
        return """
        <style>
            body { font-family: 'Segoe UI', sans-serif; font-size: 13px; line-height: 1.6; color: #E2E8F0; }
            h2 { color: #F59E0B; margin-top: 10px; margin-bottom: 6px; font-size: 16px; }
            h3 { color: #38BDF8; margin-top: 12px; margin-bottom: 4px; font-size: 14px; }
            .card { background-color: #1E293B; border: 1px solid #334155; border-radius: 6px; padding: 12px; margin-bottom: 12px; }
        </style>
        <body>
            <h2>Modos de Busca, Idiomas e Estratégias de Mineração</h2>

            <div class="card">
                <h3>🎯 Modo 1: Busca por Palavras-chave</h3>
                <p>Permite minerar termos em escala global ou por idioma específico:</p>
                <ul>
                    <li><b>Priorização por Mais Vistos:</b> Inicia sempre pelos vídeos de maior alcance.</li>
                    <li><b>Filtros de Anos & Intervalos:</b> Permite minerar anos específicos (ex: 2020 a 2025) para encontrar vídeos consolidados cujos projetos de domínio foram esquecidos.</li>
                    <li><b>Blindagem de Idiomas:</b> Termos curtos ou siglas universais (ex: <code>GTA</code>) usam tokens regionais e validação morfológica para evitar vídeos em espanhol/inglês quando Português for selecionado.</li>
                    <li><b>Busca em Vídeos Relacionados:</b> Descobre automaticamente vídeos conectados no mesmo nicho.</li>
                </ul>
            </div>

            <div class="card">
                <h3>📺 Modo 2: Busca por Canal e Listas de Canais</h3>
                <p>Permite escanear canais inteiros ou listas em lote:</p>
                <ul>
                    <li><b>Formatos Aceitos:</b> Links completos (<code>https://youtube.com/@canal</code>), handles (<code>@canal</code>) ou nomes de usuário.</li>
                    <li><b>Listas em Lote:</b> Cole vários canais separados por vírgula para processar em sequência.</li>
                    <li><b>Ordenação por Mais Populares / Mais Antigos:</b> Excelente para canais antigos de tutoriais, jogos e negócios que possuem links quebrados em vídeos clássicos.</li>
                </ul>
            </div>
        </body>
        """
