# 🎯 YouTube Espião & Hunter Browser

Um aplicativo desktop completo com visual de navegador web moderno (Chromium) e painel inteligente de mineração de vídeos no YouTube, cálculo de métricas de visualizações (médias diárias, mensais e anuais) e rastreamento de domínios expirados ou disponíveis para registro.

---

## ✨ Principais Funcionalidades

### 1. 🌐 Navegador Web Integrado (Chromium)
- Se comporta exatamente como um navegador padrão (Chrome/Edge).
- Barra de endereços completa com histórico, navegação de páginas e atalhos rápidos para YouTube, Registro.br, Namecheap, etc.
- Ao clicar em qualquer vídeo ou domínio encontrado no painel de mineração, a página abre automaticamente no navegador embutido.

### 2. 🎯 Painel Espião de Mineração
- **Busca Multilíngue**: Suporte a termos em Português, Inglês, Espanhol, Francês, Alemão e Italiano.
- **Varredura Completa**: Extração do título, canal, visualizações, data de publicação, miniatura, texto completo da **Descrição** e do **Comentário Fixado**.
- **Filtros e Ordenação**:
  - Ordenar por **Mais Visualizados (Top Views)**, **Relevância** ou **Mais Recentes**.
  - Definir quantidade de vídeos para minerar.

### 3. 📊 Métricas de Desempenho e Velocidade de Vídeos
- **Média Diária**: Total de visualizações / Dias desde a publicação.
- **Média Mensal**: Média diária × 30.4.
- **Média Anual**: Média diária × 365.25.
- **Badges de Desempenho**: Identificação visual de vídeos de alto tráfego e virais.

### 4. 💎 Validador de Domínios Expirados & WHOIS/RDAP
- **Desencurtador Automático**: Expande links encurtados (`bit.ly`, `tinyurl`, `linktr.ee`, etc.) para encontrar o domínio real de destino.
- **Filtro de Whitelist**: Ignora redes sociais e plataformas gigantes (YouTube, Instagram, Facebook, TikTok, Twitter, Google, etc.).
- **Classificação Visual de Status**:
  - 🟢 **Disponível / Expirado**: Domínio não registrado ou livre para registro imediato.
  - 🟡 **Inativo / DNS Caído**: Domínio registrado no WHOIS, mas com servidores DNS ou site abandonados.
  - 🔴 **Ativo**: Domínio registrado e funcionando.
- **Botão de 1 Clique**: Acesso direto para registrar/comprar o domínio (Registro.br ou Namecheap).

### 5. 📥 Exportação de Relatórios
- Exportação em **Excel (.xlsx)** com múltiplas abas formatadas.
- Exportação em **CSV** (compatível com acentuação no Excel).
- Exportação em **JSON**.

---

## 🚀 Como Executar

### Opção 1: Executável Rápido
Dê um duplo clique no arquivo:
```
iniciar.bat
```

### Opção 2: Linha de Comando (Terminal)
```bash
python main.py
```

---

## 🛠️ Tecnologias Utilizadas
- **PyQt6 & PyQt6-WebEngine** (Interface desktop moderna e motor Chromium)
- **yt-dlp & scrapetube** (Mineração de dados e comentários do YouTube)
- **dnspython** (Verificação ultra-rápida de registros DNS)
- **python-whois & RDAP** (Validação de disponibilidade de domínios)
- **tldextract & pandas** (Extração de domínios raiz e exportação de dados)
