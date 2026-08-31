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

        # 2. Domain Whitelist
        group_ignore = QGroupBox("🛡️ Lista de Domínios Ignorados (Whitelist de Grandes Plataformas)")
        g_layout = QVBoxLayout(group_ignore)
        g_layout.setSpacing(8)

        lbl_desc = QLabel("Domínios abaixo são ignorados automaticamente para focar apenas em domínios comerciais e próprios (um por linha):")
        lbl_desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        g_layout.addWidget(lbl_desc)

        self.txt_ignored = QPlainTextEdit()
        self.txt_ignored.setPlainText("\n".join(sorted(IGNORE_DOMAINS)))
        self.txt_ignored.setStyleSheet("background-color: #0F172A; color: #E2E8F0; font-family: 'Consolas', monospace;")
        g_layout.addWidget(self.txt_ignored)

        btn_save_all = QPushButton("💾 Salvar Todas as Configurações")
        btn_save_all.setObjectName("btn_primary")
        btn_save_all.clicked.connect(self._save_settings)
        g_layout.addWidget(btn_save_all)

        layout.addWidget(group_ignore, 1)

    def _save_settings(self):
        # Update ignore list
        lines = [l.strip().lower() for l in self.txt_ignored.toPlainText().splitlines() if l.strip()]
        IGNORE_DOMAINS.clear()
        IGNORE_DOMAINS.update(lines)

        # Update safety settings
        APP_SETTINGS["min_delay"] = self.spin_min_delay.value()
        APP_SETTINGS["max_delay"] = self.spin_max_delay.value()
        APP_SETTINGS["proxy_url"] = self.txt_proxy.text().strip()

        QMessageBox.information(
            self,
            "Configurações Salvas",
            f"Configurações atualizadas com sucesso!\n\n"
            f"• Delays: {APP_SETTINGS['min_delay']}s - {APP_SETTINGS['max_delay']}s\n"
            f"• Proxy: {'Ativo' if APP_SETTINGS['proxy_url'] else 'Desativado (IP Local)'}\n"
            f"• Domínios ignorados: {len(IGNORE_DOMAINS)}"
        )
