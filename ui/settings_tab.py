"""
Settings Tab for Custom Preferences, Anti-Block Settings, Proxies, and Domain Whitelists.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QGroupBox, QMessageBox, QCheckBox, QLineEdit, QDoubleSpinBox, QSpinBox
)
from core.domain_extractor import IGNORE_DOMAINS

# Shared config store
APP_SETTINGS = {
    "min_delay": 1.0,
    "max_delay": 2.5,
    "proxy_url": "",
    "auto_unshorten": True,
    "rdap_deep_check": True
}

class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 1. 24/7 Anti-Block & Performance Settings
        group_safety = QGroupBox("🛡️ Proteção Anti-Bloqueio & Operação 24 Horas")
        s_layout = QVBoxLayout(group_safety)
        s_layout.setSpacing(10)

        # Delay settings
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Intervalo de Espera Humana (Jitter entre vídeos):"))
        self.spin_min_delay = QDoubleSpinBox()
        self.spin_min_delay.setRange(0.5, 10.0)
        self.spin_min_delay.setValue(APP_SETTINGS["min_delay"])
        self.spin_min_delay.setSuffix(" s (Mín)")
        
        self.spin_max_delay = QDoubleSpinBox()
        self.spin_max_delay.setRange(1.0, 20.0)
        self.spin_max_delay.setValue(APP_SETTINGS["max_delay"])
        self.spin_max_delay.setSuffix(" s (Máx)")

        delay_layout.addWidget(self.spin_min_delay)
        delay_layout.addWidget(QLabel("até"))
        delay_layout.addWidget(self.spin_max_delay)
        delay_layout.addStretch()
        s_layout.addLayout(delay_layout)

        # Proxy Setting
        proxy_layout = QHBoxLayout()
        proxy_layout.addWidget(QLabel("Servidor Proxy (Opcional p/ 24h contínuo):"))
        self.txt_proxy = QLineEdit()
        self.txt_proxy.setPlaceholderText("ex: http://ip:porta ou http://user:pass@ip:porta")
        self.txt_proxy.setText(APP_SETTINGS["proxy_url"])
        proxy_layout.addWidget(self.txt_proxy)
        s_layout.addLayout(proxy_layout)

        layout.addWidget(group_safety)

        # 2. API Keys for SEO Analysis
        group_api = QGroupBox("🔑 Chaves de API para Análise SEO de Domínios")
        api_layout = QVBoxLayout(group_api)
        api_layout.setSpacing(10)

        lbl_api_info = QLabel(
            "Insira suas chaves de API <b>gratuitas</b> para habilitar a análise completa de domínios disponíveis.<br>"
            "<span style='color: #64748B;'>As demais análises (RDAP, Wayback Machine, DNS) funcionam sem chave.</span>"
        )
        lbl_api_info.setWordWrap(True)
        api_layout.addWidget(lbl_api_info)

        # Open PageRank API Key
        opr_layout = QHBoxLayout()
        opr_layout.addWidget(QLabel("📊 Open PageRank API Key:"))
        self.txt_opr_key = QLineEdit()
        self.txt_opr_key.setPlaceholderText("opr_live_xxxxxxxxxxxxxxxx (Grátis: 30.000/mês)")
        self.txt_opr_key.setEchoMode(QLineEdit.EchoMode.Password)
        opr_layout.addWidget(self.txt_opr_key)
        btn_opr_show = QPushButton("👁")
        btn_opr_show.setFixedWidth(35)
        btn_opr_show.setToolTip("Mostrar/ocultar chave")
        btn_opr_show.clicked.connect(lambda: self.txt_opr_key.setEchoMode(
            QLineEdit.EchoMode.Normal if self.txt_opr_key.echoMode() == QLineEdit.EchoMode.Password else QLineEdit.EchoMode.Password
        ))
        opr_layout.addWidget(btn_opr_show)
        api_layout.addLayout(opr_layout)

        lbl_opr_signup = QLabel(
            "🔗 <a href='https://www.domcop.com/openpagerank/' style='color: #38BDF8;'>Criar chave gratuita no Open PageRank</a> "
            "(30.000 consultas/mês, sem cartão de crédito)"
        )
        lbl_opr_signup.setOpenExternalLinks(True)
        lbl_opr_signup.setWordWrap(True)
        api_layout.addWidget(lbl_opr_signup)

        layout.addWidget(group_api)

        # Load saved API keys
        try:
            from core.domain_seo_service import load_api_key
            saved_opr = load_api_key("open_pagerank_key")
            if saved_opr:
                self.txt_opr_key.setText(saved_opr)
        except Exception:
            pass

        # 3. Domain Whitelist
        group_ignore = QGroupBox("🛡️ Lista de Domínios Ignorados (Whitelist de Grandes Plataformas)")
        g_layout = QVBoxLayout(group_ignore)
        g_layout.setSpacing(8)

        lbl_desc = QLabel("Domínios abaixo são ignorados automaticamente para focar apenas em domínios comerciais e próprios (um por linha):")
        lbl_desc.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        g_layout.addWidget(lbl_desc)

        self.txt_ignored = QPlainTextEdit()
        self.txt_ignored.setPlainText("\n".join(sorted(IGNORE_DOMAINS)))
        self.txt_ignored.setStyleSheet("background-color: #121212; color: #F1F1F1; font-family: 'Consolas', monospace;")
        g_layout.addWidget(self.txt_ignored)

        btn_save_all = QPushButton("💾 Salvar Todas as Configurações")
        btn_save_all.setObjectName("btn_start_action")
        btn_save_all.clicked.connect(self._save_settings)
        g_layout.addWidget(btn_save_all)

        layout.addWidget(group_ignore, 1)

    def showEvent(self, event):
        super().showEvent(event)
        self.txt_ignored.setPlainText("\n".join(sorted(IGNORE_DOMAINS)))

    def _save_settings(self):
        # Update ignore list
        lines = [l.strip().lower().replace("@", "") for l in self.txt_ignored.toPlainText().splitlines() if l.strip()]
        IGNORE_DOMAINS.clear()
        IGNORE_DOMAINS.update(lines)

        from core.domain_extractor import ALL_EXCLUDED_DOMAINS, _get_exclusion_file_path
        ALL_EXCLUDED_DOMAINS.clear()
        ALL_EXCLUDED_DOMAINS.update(lines)

        # Save to disk
        path = _get_exclusion_file_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                for item in sorted(lines):
                    f.write(f"{item}\n")
        except Exception:
            pass

        # Update safety settings
        APP_SETTINGS["min_delay"] = self.spin_min_delay.value()
        APP_SETTINGS["max_delay"] = self.spin_max_delay.value()
        APP_SETTINGS["proxy_url"] = self.txt_proxy.text().strip()

        # Save API keys
        try:
            from core.domain_seo_service import save_api_key
            opr_key = self.txt_opr_key.text().strip()
            if opr_key:
                save_api_key("open_pagerank_key", opr_key)
        except Exception:
            pass

        QMessageBox.information(
            self,
            "Configurações Salvas",
            f"Configurações atualizadas com sucesso!\n\n"
            f"• Delays: {APP_SETTINGS['min_delay']}s - {APP_SETTINGS['max_delay']}s\n"
            f"• Proxy: {'Ativo' if APP_SETTINGS['proxy_url'] else 'Desativado (IP Local)'}\n"
            f"• Domínios ignorados / lista de exclusão: {len(IGNORE_DOMAINS)}"
        )
