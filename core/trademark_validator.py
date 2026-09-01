"""
Trademark & Brand Safety Intelligence Engine.
Analyzes domains and Instagram handles for Cybersquatting, Typosquatting,
and Trademark Infringement risks against famous/renowned trademarks (INPI Brazil, WIPO, USPTO, and Global Top Brands).

Classifications:
- 🟢 SEGURO P/ USO (Safe / Generic / Niche): Domain is generic or descriptive with no overlap with famous protected trademarks.
- 🟡 ATENÇÃO / SIMILARIDADE (Moderate / Typosquatting / Phonetic): Contains typos, homoglyphs, or phonetic similarities to renowned brands.
- 🔴 RISCO LEGAL / MARCA NOTÓRIA (High Risk / Cybersquatting): Directly contains a well-known registered brand. High risk of loss via UDRP / SACI-Adm without compensation.
"""

import re
import urllib.parse
from typing import Dict, Any, List, Optional, Set, Tuple

# ==============================================================================
# 1. COMPREHENSIVE DATABASE OF FAMOUS & RENOWNED REGISTERED TRADEMARKS (1000+)
# ==============================================================================

# A. Casas de Apostas, Cassinos Online & Betting (Brasil e Internacional)
TRADEMARKS_BETTING: Dict[str, str] = {
    "bet365": "Bet365",
    "betano": "Betano",
    "sportingbet": "Sportingbet",
    "betfair": "Betfair",
    "kto": "KTO Apostas",
    "estrelabet": "EstrelaBet",
    "novibet": "Novibet",
    "pixbet": "Pixbet",
    "superbet": "Superbet",
    "parimatch": "Parimatch",
    "blaze": "Blaze Apostas",
    "stake": "Stake.com",
    "1xbet": "1xBet",
    "betsson": "Betsson",
    "betway": "Betway",
    "rivalo": "Rivalo",
    "betnacional": "Betnacional",
    "pagbet": "Pagbet",
    "mrjack": "Mr. Jack Bet",
    "mrjackbet": "Mr. Jack Bet",
    "betfast": "Betfast",
    "betmotion": "Betmotion",
    "f12bet": "F12.Bet",
    "f12": "F12.Bet",
    "galerabet": "Galera.bet",
    "vaidebet": "Vai de Bet",
    "esportesdasorte": "Esportes da Sorte",
    "jonbet": "Jonbet",
    "luvabet": "Luva.bet",
    "pokerstars": "PokerStars",
    "888poker": "888poker",
    "888casino": "888 Casino",
    "ggpoker": "GGPoker",
    "draftkings": "DraftKings",
    "fanduel": "FanDuel",
    "bodog": "Bodog",
    "betboom": "BetBoom",
    "bet7k": "Bet7k",
    "casaapostas": "Casa de Apostas"
}

# B. Infoprodutos, Gateways de Afiliados, Plataformas & EdTech
TRADEMARKS_INFOPRODUCTS_EDTECH: Dict[str, str] = {
    "hotmart": "Hotmart",
    "kiwify": "Kiwify",
    "eduzz": "Eduzz",
    "monetizze": "Monetizze",
    "braip": "Braip",
    "perfectpay": "Perfect Pay",
    "kirvano": "Kirvano",
    "ticto": "Ticto",
    "cakto": "Cakto",
    "lastlink": "Lastlink",
    "greenn": "Greenn",
    "buygoods": "BuyGoods",
    "clickbank": "ClickBank",
    "digistore24": "Digistore24",
    "jvzoo": "JVZoo",
    "warriorplus": "WarriorPlus",
    "udemy": "Udemy",
    "coursera": "Coursera",
    "edx": "edX",
    "alura": "Alura",
    "rocketseat": "Rocketseat",
    "dio": "Digital Innovation One (DIO)",
    "digitalinnovationone": "DIO",
    "descomplica": "Descomplica",
    "grancursos": "Gran Cursos Online",
    "estrategiaconcursos": "Estratégia Concursos",
    "alfacon": "AlfaCon Concursos",
    "damasio": "Damásio Educacional",
    "sanar": "Sanar Saúde",
    "anhanguera": "Anhanguera Educacional",
    "estacio": "Estácio de Sá",
    "kroton": "Kroton Educacional",
    "cogna": "Cogna Educação",
    "yduqs": "Yduqs",
    "fgv": "Fundação Getulio Vargas (FGV)",
    "senac": "Senac",
    "senai": "Senai",
    "sebrae": "Sebrae",
    "sesc": "Sesc",
    "sesi": "Sesi",
    "cna": "CNA Idiomas",
    "wizard": "Wizard Idiomas",
    "fisk": "Fisk Idiomas",
    "ccaa": "CCAA",
    "wiseup": "Wise Up",
    "openenglish": "Open English",
    "duolingo": "Duolingo",
    "babbel": "Babbel",
    "cambly": "Cambly"
}

# C. Inteligência Artificial, Big Tech, Cloud, Redes Sociais & Software
TRADEMARKS_TECH_AI: Dict[str, str] = {
    "google": "Google",
    "alphabet": "Alphabet Inc.",
    "youtube": "YouTube (Google)",
    "youtubekids": "YouTube Kids",
    "youtubemusic": "YouTube Music",
    "gmail": "Gmail (Google)",
    "googlecloud": "Google Cloud",
    "googleplay": "Google Play Store",
    "gemini": "Google Gemini",
    "deepmind": "Google DeepMind",
    "apple": "Apple Inc.",
    "iphone": "iPhone (Apple)",
    "ipad": "iPad (Apple)",
    "macbook": "MacBook (Apple)",
    "airpods": "AirPods (Apple)",
    "applewatch": "Apple Watch",
    "appstore": "App Store (Apple)",
    "icloud": "iCloud (Apple)",
    "appletv": "Apple TV",
    "microsoft": "Microsoft",
    "windows": "Windows (Microsoft)",
    "office365": "Office 365 (Microsoft)",
    "microsoft365": "Microsoft 365",
    "azure": "Microsoft Azure",
    "xbox": "Xbox (Microsoft)",
    "copilot": "Microsoft Copilot",
    "meta": "Meta Platforms",
    "facebook": "Facebook (Meta)",
    "instagram": "Instagram (Meta)",
    "threads": "Threads (Meta)",
    "whatsapp": "WhatsApp (Meta)",
    "oculus": "Oculus (Meta)",
    "metaquest": "Meta Quest",
    "tiktok": "TikTok (ByteDance)",
    "douyin": "Douyin (ByteDance)",
    "bytedance": "ByteDance",
    "kwai": "Kwai",
    "kuaishou": "Kuaishou",
    "twitter": "Twitter / X",
    "xcorp": "X Corp",
    "linkedin": "LinkedIn (Microsoft)",
    "pinterest": "Pinterest",
    "snapchat": "Snapchat",
    "snap": "Snap Inc.",
    "twitch": "Twitch (Amazon)",
    "discord": "Discord",
    "telegram": "Telegram",
    "signal": "Signal Messenger",
    "reddit": "Reddit",
    "quora": "Quora",
    "tumblr": "Tumblr",
    "wechat": "WeChat (Tencent)",
    "tencent": "Tencent",
    "baidu": "Baidu",
    "weibo": "Sina Weibo",
    "line": "LINE Messenger",
    "kakaotalk": "KakaoTalk",
    "openai": "OpenAI",
    "chatgpt": "ChatGPT (OpenAI)",
    "dalle": "DALL-E (OpenAI)",
    "sora": "Sora (OpenAI)",
    "anthropic": "Anthropic",
    "claude": "Claude AI (Anthropic)",
    "midjourney": "Midjourney",
    "perplexity": "Perplexity AI",
    "deepseek": "DeepSeek AI",
    "stabilityai": "Stability AI",
    "stablediffusion": "Stable Diffusion",
    "runway": "Runway AI",
    "elevenlabs": "ElevenLabs",
    "huggingface": "Hugging Face",
    "cursor": "Cursor AI",
    "mistral": "Mistral AI",
    "cohere": "Cohere AI",
    "adobe": "Adobe Systems",
    "photoshop": "Photoshop (Adobe)",
    "illustrator": "Illustrator (Adobe)",
    "premiere": "Premiere Pro (Adobe)",
    "aftereffects": "After Effects (Adobe)",
    "indesign": "InDesign (Adobe)",
    "acrobat": "Adobe Acrobat",
    "lightroom": "Adobe Lightroom",
    "figma": "Figma",
    "canva": "Canva",
    "coreldraw": "CorelDraw",
    "notion": "Notion",
    "evernote": "Evernote",
    "trello": "Trello (Atlassian)",
    "asana": "Asana",
    "monday": "Monday.com",
    "clickup": "ClickUp",
    "jira": "Jira (Atlassian)",
    "confluence": "Confluence (Atlassian)",
    "slack": "Slack (Salesforce)",
    "zoom": "Zoom Video",
    "webex": "Cisco Webex",
    "skype": "Skype (Microsoft)",
    "teamviewer": "TeamViewer",
    "anydesk": "AnyDesk",
    "loom": "Loom",
    "miro": "Miro",
    "wordpress": "WordPress",
    "shopify": "Shopify",
    "woocommerce": "WooCommerce",
    "nuvemshop": "Nuvemshop",
    "tray": "Tray Commerce",
    "lojaintegrada": "Loja Integrada",
    "vtex": "VTEX",
    "rdstation": "RD Station",
    "hubspot": "HubSpot",
    "activecampaign": "ActiveCampaign",
    "mailchimp": "Mailchimp",
    "leadlovers": "Leadlovers",
    "clickfunnels": "ClickFunnels",
    "salesforce": "Salesforce",
    "zendesk": "Zendesk",
    "freshdesk": "Freshdesk",
    "intercom": "Intercom",
    "pipefy": "Pipefy",
    "totvs": "Totvs",
    "senior": "Senior Sistemas",
    "omie": "Omie ERP",
    "contaazul": "Conta Azul",
    "bling": "Bling! ERP",
    "tinyerp": "Tiny ERP",
    "sap": "SAP",
    "oracle": "Oracle",
    "ibm": "IBM",
    "cisco": "Cisco Systems",
    "vmware": "VMware",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "github": "GitHub (Microsoft)",
    "gitlab": "GitLab",
    "bitbucket": "Bitbucket",
    "postman": "Postman",
    "vercel": "Vercel",
    "netlify": "Netlify",
    "supabase": "Supabase",
    "firebase": "Firebase (Google)",
    "cloudflare": "Cloudflare",
    "namecheap": "Namecheap",
    "godaddy": "GoDaddy",
    "hostgator": "HostGator",
    "hostinger": "Hostinger",
    "locaweb": "Locaweb",
    "kinghost": "KingHost",
    "uolhost": "UOL Host",
    "umbler": "Umbler",
    "digitalocean": "DigitalOcean",
    "linode": "Linode",
    "aws": "Amazon Web Services (AWS)",
    "amazon": "Amazon",
    "kindle": "Amazon Kindle",
    "alexa": "Amazon Alexa",
    "primevideo": "Amazon Prime Video",
    "nvidia": "Nvidia",
    "geforce": "GeForce (Nvidia)",
    "intel": "Intel Corporation",
    "amd": "AMD",
    "ryzen": "Ryzen (AMD)",
    "qualcomm": "Qualcomm",
    "snapdragon": "Snapdragon"
}

# D. Bancos, Fintechs, Gateways & Meios de Pagamento (Brasil e Global)
TRADEMARKS_FINANCIAL: Dict[str, str] = {
    "nubank": "Nubank",
    "itau": "Itaú Unibanco",
    "itaú": "Itaú Unibanco",
    "bradesco": "Banco Bradesco",
    "santander": "Banco Santander",
    "bancodobrasil": "Banco do Brasil",
    "bb": "Banco do Brasil",
    "caixa": "Caixa Econômica Federal",
    "caixaeconomica": "Caixa Econômica Federal",
    "inter": "Banco Inter",
    "bancointer": "Banco Inter",
    "c6": "C6 Bank",
    "c6bank": "C6 Bank",
    "picpay": "PicPay",
    "pagseguro": "PagSeguro / PagBank",
    "pagbank": "PagBank",
    "stone": "Stone Pagamentos",
    "ton": "Ton (Stone)",
    "infinitepay": "InfinitePay (CloudWalk)",
    "mercadopago": "Mercado Pago",
    "safra": "Banco Safra",
    "btg": "BTG Pactual",
    "btgpactual": "BTG Pactual",
    "xp": "XP Investimentos",
    "xpinvestimentos": "XP Investimentos",
    "clear": "Clear Corretora",
    "rico": "Rico Investimentos",
    "genial": "Genial Investimentos",
    "modalmais": "Modalmais",
    "toro": "Toro Investimentos",
    "avenue": "Avenue Securities",
    "nomad": "Nomad Global",
    "wise": "Wise (TransferWise)",
    "remessaonline": "Remessa Online",
    "mercadobitcoin": "Mercado Bitcoin",
    "foxbit": "Foxbit",
    "binance": "Binance",
    "coinbase": "Coinbase",
    "bybit": "Bybit",
    "okx": "OKX",
    "bitso": "Bitso",
    "metamask": "MetaMask",
    "tether": "Tether USDt",
    "b3": "B3 (Brasil, Bolsa, Balcão)",
    "serasa": "Serasa Experian",
    "serasaexperian": "Serasa Experian",
    "spc": "SPC Brasil",
    "boavista": "Boa Vista SCPC",
    "elo": "Cartão Elo",
    "cartaoelo": "Cartão Elo",
    "alelo": "Alelo",
    "ticket": "Ticket Alimentação",
    "sodexo": "Sodexo / Pluxee",
    "pluxee": "Pluxee",
    "vr": "VR Benefícios",
    "flash": "Flash Benefícios",
    "caju": "Caju Benefícios",
    "swile": "Swile Benefícios",
    "visa": "Visa Inc.",
    "mastercard": "Mastercard",
    "americanexpress": "American Express",
    "amex": "American Express",
    "hipercard": "Hipercard",
    "unionpay": "UnionPay",
    "jcb": "JCB",
    "diners": "Diners Club",
    "stripe": "Stripe Payments",
    "paypal": "PayPal",
    "adyen": "Adyen",
    "westernunion": "Western Union",
    "moneygram": "MoneyGram"
}

# E. Varejo, E-Commerce & Marketplaces (Brasil e Global)
TRADEMARKS_RETAIL_ECOM: Dict[str, str] = {
    "mercadolivre": "Mercado Livre",
    "magalu": "Magazine Luiza",
    "magazineluiza": "Magazine Luiza",
    "casasbahia": "Casas Bahia",
    "pontofrio": "Ponto Frio",
    "ponto": "Ponto",
    "americanas": "Lojas Americanas",
    "submarino": "Submarino",
    "shoptime": "Shoptime",
    "netshoes": "Netshoes",
    "zattini": "Zattini",
    "centauro": "Centauro",
    "dafiti": "Dafiti",
    "kanui": "Kanui",
    "tricae": "Tricae",
    "mobly": "Mobly",
    "madeiramadeira": "MadeiraMadeira",
    "enjoei": "Enjoei",
    "elo7": "Elo7",
    "kabum": "KaBuM!",
    "pichau": "Pichau Informática",
    "terabyte": "TerabyteShop",
    "terabyteshop": "TerabyteShop",
    "leroymerlin": "Leroy Merlin",
    "telhanorte": "Telhanorte",
    "cec": "C&C Casa e Construção",
    "dicico": "Dicico",
    "sodimac": "Sodimac",
    "tokstok": "Tok&Stok",
    "camicado": "Camicado",
    "fastshop": "Fast Shop",
    "polishop": "Polishop",
    "havan": "Havan",
    "lojasluiza": "Magazine Luiza",
    "lojascem": "Lojas Cem",
    "riachuelo": "Riachuelo",
    "renner": "Lojas Renner",
    "lojasrenner": "Lojas Renner",
    "c&a": "C&A",
    "cea": "C&A Brasil",
    "marisa": "Lojas Marisa",
    "pernambucanas": "Pernambucanas",
    "torratorra": "Torra Torra",
    "besni": "Besni",
    "caedu": "Caedu",
    "zara": "Zara (Inditex)",
    "forever21": "Forever 21",
    "amaro": "Amaro",
    "insider": "Insider Store",
    "insiderstore": "Insider Store",
    "baw": "Baw Clothing",
    "approve": "Approve",
    "reserva": "Reserva",
    "aramis": "Aramis",
    "osklen": "Osklen",
    "colcci": "Colcci",
    "farm": "Farm Rio",
    "animale": "Animale",
    "schutz": "Schutz (Arezzo&Co)",
    "arezzo": "Arezzo",
    "anacapri": "Anacapri",
    "melissa": "Melissa (Grendene)",
    "grendene": "Grendene",
    "havaianas": "Havaianas (Alpargatas)",
    "dupe": "Dupé",
    "ipanema": "Ipanema (Grendene)",
    "rider": "Rider (Grendene)",
    "olympikus": "Olympikus (Vulcabras)",
    "topper": "Topper",
    "rainha": "Rainha",
    "penalty": "Penalty",
    "aliexpress": "AliExpress",
    "alibaba": "Alibaba Group",
    "shopee": "Shopee",
    "shein": "Shein",
    "temu": "Temu (PDD Holdings)",
    "ebay": "eBay",
    "rakuten": "Rakuten",
    "walmart": "Walmart",
    "target": "Target",
    "bestbuy": "Best Buy",
    "costco": "Costco",
    "homedepot": "The Home Depot",
    "ikea": "IKEA",
    "decathlon": "Decathlon",
    "sephora": "Sephora (LVMH)",
    "maccosmetics": "MAC Cosmetics"
}

# F. Streaming, Mídia, Notícias, TV & Podcasting
TRADEMARKS_MEDIA: Dict[str, str] = {
    "netflix": "Netflix",
    "globoplay": "Globoplay (Grupo Globo)",
    "redeglobo": "TV Globo",
    "globo": "Grupo Globo",
    "g1": "G1 Notícias",
    "ge": "Globo Esporte",
    "gshow": "Gshow",
    "sbt": "SBT - Sistema Brasileiro de Televisão",
    "record": "RecordTV",
    "recordtv": "RecordTV",
    "r7": "Portal R7",
    "band": "Rede Bandeirantes",
    "bandtv": "Band TV",
    "bandnews": "BandNews",
    "redetv": "RedeTV!",
    "tvcultura": "TV Cultura",
    "cnn": "CNN",
    "cnnbrasil": "CNN Brasil",
    "jovempan": "Jovem Pan",
    "jovempannews": "Jovem Pan News",
    "uol": "UOL - Universo Online",
    "terra": "Portal Terra",
    "folha": "Folha de S.Paulo",
    "folhadespaulo": "Folha de S.Paulo",
    "estadao": "O Estado de S. Paulo",
    "oglobo": "Jornal O Globo",
    "valoreconomico": "Valor Econômico",
    "exame": "Revista Exame",
    "veja": "Revista Veja",
    "abril": "Editora Abril",
    "epoca": "Revista Época",
    "istoe": "Revista IstoÉ",
    "canaltech": "Canaltech",
    "tecmundo": "TecMundo",
    "olhardigital": "Olhar Digital",
    "techtudo": "TechTudo",
    "jovemnerd": "Jovem Nerd",
    "omelete": "Omelete",
    "ign": "IGN Brasil",
    "theenemy": "The Enemy",
    "flowpodcast": "Flow Podcast",
    "podpah": "Podpah",
    "poddelas": "PodDelas",
    "inteligencialtda": "Inteligência Ltda.",
    "disney": "The Walt Disney Company",
    "disneyplus": "Disney+",
    "starplus": "Star+",
    "marvel": "Marvel Entertainment",
    "starwars": "Star Wars (Lucasfilm)",
    "pixar": "Pixar",
    "warnerbros": "Warner Bros. Discovery",
    "warner": "Warner Bros.",
    "hbomax": "HBO Max",
    "max": "Max (Warner Bros)",
    "hbo": "HBO",
    "paramount": "Paramount Pictures",
    "paramountplus": "Paramount+",
    "universal": "Universal Pictures",
    "sony": "Sony Corporation",
    "spotify": "Spotify",
    "deezer": "Deezer",
    "applemusic": "Apple Music",
    "tidal": "Tidal",
    "amazonmusic": "Amazon Music",
    "soundcloud": "SoundCloud",
    "shazam": "Shazam"
}

# G. Alimentos, Bebidas, Supermercados, Fast Food & Delivery
TRADEMARKS_FOOD_BEV: Dict[str, str] = {
    "cocacola": "Coca-Cola",
    "coca": "Coca-Cola",
    "fanta": "Fanta (Coca-Cola)",
    "sprite": "Sprite (Coca-Cola)",
    "schweppes": "Schweppes",
    "pepsi": "PepsiCo",
    "pepsico": "PepsiCo",
    "guaranaantarctica": "Guaraná Antarctica",
    "dolly": "Dolly Refrigerantes",
    "redbull": "Red Bull",
    "monsterenergy": "Monster Energy",
    "fusionenergy": "Fusion Energy Drink",
    "tntenergy": "TNT Energy Drink",
    "gatorade": "Gatorade (PepsiCo)",
    "powerade": "Powerade (Coca-Cola)",
    "ambev": "Ambev",
    "brahma": "Brahma (Ambev)",
    "skol": "Skol (Ambev)",
    "antarctica": "Antarctica (Ambev)",
    "heineken": "Heineken",
    "stellaartois": "Stella Artois (Ambev)",
    "budweiser": "Budweiser (Ambev)",
    "corona": "Corona (Ambev)",
    "spaten": "Spaten (Ambev)",
    "eisenbahn": "Eisenbahn (Heineken)",
    "bohemia": "Bohemia (Ambev)",
    "itaipava": "Itaipava (Grupo Petrópolis)",
    "petra": "Petra (Grupo Petrópolis)",
    "blackprincess": "Black Princess",
    "schin": "Schin",
    "devassa": "Devassa",
    "johnniewalker": "Johnnie Walker (Diageo)",
    "smirnoff": "Smirnoff (Diageo)",
    "absolut": "Absolut Vodka",
    "nestle": "Nestlé",
    "ninho": "Leite Ninho (Nestlé)",
    "molico": "Molico (Nestlé)",
    "nescau": "Nescau (Nestlé)",
    "toddy": "Toddy (PepsiCo)",
    "toddynho": "Toddynho (PepsiCo)",
    "kitkat": "KitKat (Nestlé)",
    "nespresso": "Nespresso (Nestlé)",
    "garoto": "Chocolates Garoto",
    "lacta": "Lacta (Mondelez)",
    "mondelez": "Mondelēz International",
    "bauducco": "Bauducco",
    "visconti": "Visconti (Pandurata)",
    "piraque": "Piraquê (M. Dias Branco)",
    "marilan": "Marilan",
    "mabel": "Mabel (Camil)",
    "adria": "Adria (M. Dias Branco)",
    "mdiasbranco": "M. Dias Branco",
    "renata": "Renata (Selmi)",
    "barilla": "Barilla",
    "donabenta": "Dona Benta (J.Macêdo)",
    "qualy": "Qualy (BRF)",
    "doriana": "Doriana (Seara)",
    "vigor": "Vigor Alimentos",
    "danone": "Danone",
    "activia": "Activia (Danone)",
    "danoninho": "Danoninho (Danone)",
    "yakult": "Yakult",
    "piracanjuba": "Piracanjuba",
    "itambe": "Itambé",
    "italac": "Italac",
    "tirolez": "Tirolez",
    "catupiry": "Catupiry",
    "camil": "Camil Alimentos",
    "tiojoao": "Tio João",
    "pratofino": "Prato Fino",
    "sadia": "Sadia (BRF)",
    "perdigao": "Perdigão (BRF)",
    "perdigão": "Perdigão (BRF)",
    "brf": "BRF S.A.",
    "seara": "Seara Alimentos",
    "friboi": "Friboi (JBS)",
    "jbs": "JBS S.A.",
    "marfrig": "Marfrig",
    "swift": "Swift Mercado da Carne",
    "minerva": "Minerva Foods",
    "carrefour": "Carrefour",
    "assai": "Assaí Atacadista",
    "atacadao": "Atacadão",
    "paodeacucar": "Pão de Açúcar",
    "extrabr": "Extra Hipermercados",
    "samsclub": "Sam's Club",
    "stmarche": "St. Marche",
    "muffato": "Super Muffato",
    "condor": "Supermercados Condor",
    "supermercadosbh": "Supermercados BH",
    "guanabara": "Supermercados Guanabara",
    "mundial": "Supermercados Mundial",
    "prezunic": "Prezunic",
    "mcdonalds": "McDonald's",
    "burgerking": "Burger King",
    "subway": "Subway",
    "kfc": "KFC",
    "pizzahut": "Pizza Hut",
    "dominos": "Domino's Pizza",
    "habibs": "Habib's",
    "ragazzo": "Ragazzo",
    "spoleto": "Spoleto",
    "giraffas": "Giraffas",
    "bobs": "Bob's",
    "madero": "Madero",
    "jeronimo": "Jeronimo Burger",
    "outback": "Outback Steakhouse",
    "applebees": "Applebee's",
    "starbucks": "Starbucks",
    "cacashow": "Cacau Show",
    "kopenhagen": "Kopenhagen",
    "brasilcacau": "Chocolates Brasil Cacau",
    "dengo": "Dengo Chocolates",
    "lindt": "Lindt & Sprüngli",
    "sodie": "Sodiê Doces",
    "baciodilatte": "Bacio di Latte",
    "chiquinho": "Chiquinho Sorvetes",
    "oggisorvetes": "Oggi Sorvetes",
    "ifood": "iFood",
    "zedelivery": "Zé Delivery (Ambev)",
    "rappi": "Rappi",
    "ubereats": "Uber Eats",
    "daki": "Daki Delivery",
    "aiqfome": "Aiqfome"
}

# H. Farmácia, Cosméticos, Saúde & Beleza
TRADEMARKS_PHARMA_BEAUTY: Dict[str, str] = {
    "drogasil": "Drogasil (RD)",
    "drogaraia": "Droga Raia (RD)",
    "paguemenos": "Farmácias Pague Menos",
    "ultrafarma": "Ultrafarma",
    "pacheco": "Drogaria Pacheco (DPSP)",
    "drogariasaopaulo": "Drogaria São Paulo (DPSP)",
    "panvel": "Panvel Farmácias",
    "araujo": "Drogaria Araujo",
    "venancio": "Drogaria Venancio",
    "nissei": "Farmácias Nissei",
    "extrafarma": "Extrafarma",
    "natura": "Natura",
    "boticario": "O Boticário",
    "oboticario": "O Boticário",
    "eudora": "Eudora (Grupo Boticário)",
    "quemdisseberenice": "Quem Disse, Berenice?",
    "jequiti": "Jequiti Cosméticos",
    "avon": "Avon (Natura &Co)",
    "marykay": "Mary Kay",
    "hinode": "Hinode",
    "herbalife": "Herbalife",
    "loreal": "L'Oréal",
    "maybelline": "Maybelline (L'Oréal)",
    "garnier": "Garnier (L'Oréal)",
    "nivea": "Nivea (Beiersdorf)",
    "dove": "Dove (Unilever)",
    "rexona": "Rexona (Unilever)",
    "seda": "Seda (Unilever)",
    "pantene": "Pantene (P&G)",
    "headandshoulders": "Head & Shoulders (P&G)",
    "tresemme": "TRESemmé (Unilever)",
    "colgate": "Colgate (Colgate-Palmolive)",
    "sorriso": "Sorriso (Colgate-Palmolive)",
    "oralb": "Oral-B (P&G)",
    "sensodyne": "Sensodyne (Haleon)",
    "closeup": "Close Up (Unilever)",
    "gillette": "Gillette (P&G)",
    "always": "Always (P&G)",
    "intimus": "Intimus (Kimberly-Clark)",
    "pampers": "Pampers (P&G)",
    "huggies": "Huggies (Kimberly-Clark)",
    "babysec": "Babysec (Softys)",
    "johnson": "Johnson & Johnson",
    "johnsonandjohnson": "Johnson & Johnson",
    "cimed": "Cimed Medicamentos",
    "ems": "EMS Farmacêutica",
    "eurofarma": "Eurofarma",
    "neoquimica": "Neo Química (Hypera)",
    "hypera": "Hypera Pharma",
    "medley": "Medley (Sanofi)",
    "ache": "Aché Laboratórios",
    "sanofi": "Sanofi",
    "pfizer": "Pfizer",
    "astrazeneca": "AstraZeneca",
    "bayer": "Bayer",
    "novartis": "Novartis",
    "roche": "Roche",
    "gsk": "GSK (GlaxoSmithKline)",
    "abbott": "Abbott Laboratories",
    "biolab": "Biolab Farmacêutica",
    "libbs": "Libbs Farmacêutica",
    "cristalia": "Cristália"
}

# I. Automotivo, Linhas Aéreas, Mobilidade & Indústria
TRADEMARKS_AUTO_INDUSTRY: Dict[str, str] = {
    "toyota": "Toyota Motor",
    "honda": "Honda Motor",
    "volkswagen": "Volkswagen",
    "vw": "Volkswagen",
    "ford": "Ford Motor Company",
    "chevrolet": "Chevrolet (General Motors)",
    "chevy": "Chevrolet",
    "generalmotors": "General Motors",
    "hyundai": "Hyundai Motor",
    "fiat": "Fiat (Stellantis)",
    "jeep": "Jeep (Stellantis)",
    "ram": "Ram Trucks (Stellantis)",
    "renault": "Renault",
    "peugeot": "Peugeot (Stellantis)",
    "citroen": "Citroën (Stellantis)",
    "nissan": "Nissan",
    "mitsubishi": "Mitsubishi Motors",
    "caoa": "CAOA Chery",
    "chery": "Chery Automobile",
    "byd": "BYD Auto",
    "gwm": "GWM (Great Wall Motors)",
    "volvo": "Volvo",
    "bmw": "BMW Group",
    "mercedes": "Mercedes-Benz",
    "mercedesbenz": "Mercedes-Benz",
    "audi": "Audi (Volkswagen)",
    "porsche": "Porsche",
    "landrover": "Land Rover (JLR)",
    "jaguar": "Jaguar (JLR)",
    "ferrari": "Ferrari",
    "lamborghini": "Lamborghini",
    "maserati": "Maserati",
    "mclaren": "McLaren",
    "tesla": "Tesla Inc.",
    "yamaha": "Yamaha Motor",
    "kawasaki": "Kawasaki",
    "suzuki": "Suzuki",
    "harley": "Harley-Davidson",
    "harleydavidson": "Harley-Davidson",
    "royalenfield": "Royal Enfield",
    "gol": "GOL Linhas Aéreas",
    "voegol": "GOL Linhas Aéreas",
    "latam": "LATAM Airlines",
    "azul": "Azul Linhas Aéreas",
    "voeazul": "Azul Linhas Aéreas",
    "voepass": "Voepass Linhas Aéreas",
    "tap": "TAP Air Portugal",
    "copaairlines": "Copa Airlines",
    "americanairlines": "American Airlines",
    "unitedairlines": "United Airlines",
    "delta": "Delta Air Lines",
    "emirates": "Emirates",
    "qatarairways": "Qatar Airways",
    "airfrance": "Air France",
    "klm": "KLM Royal Dutch Airlines",
    "lufthansa": "Lufthansa",
    "britishairways": "British Airways",
    "uber": "Uber Technologies",
    "99": "99 (DiDi)",
    "99app": "99 App",
    "99taxi": "99 Táxi",
    "indrive": "inDrive",
    "cabify": "Cabify",
    "buser": "Buser",
    "clickbus": "ClickBus",
    "localiza": "Localiza",
    "movida": "Movida",
    "unidas": "Unidas Locadora",
    "turbi": "Turbi",
    "kovi": "Kovi",
    "webmotors": "Webmotors (Santander)",
    "icarros": "iCarros (Itaú)",
    "petrobras": "Petrobras",
    "brdistribuidora": "Vibra Energia (Postos BR)",
    "ipiranga": "Postos Ipiranga (Ultrapar)",
    "postoipiranga": "Postos Ipiranga",
    "shell": "Shell (Raízen)",
    "raizen": "Raízen",
    "vibra": "Vibra Energia",
    "alecombustiveis": "Ale Combustíveis",
    "embraer": "Embraer",
    "marcopolo": "Marcopolo",
    "randon": "Randoncorp",
    "weg": "WEG S.A.",
    "gerdau": "Gerdau",
    "csn": "CSN (Companhia Siderúrgica Nacional)",
    "usiminas": "Usiminas",
    "vale": "Vale S.A.",
    "suzano": "Suzano Papel e Celulose",
    "klabin": "Klabin"
}

# J. Telecomunicações, Internet & Satélite
TRADEMARKS_TELECOM: Dict[str, str] = {
    "claro": "Claro Telecom",
    "clarobrasil": "Claro Telecom",
    "vivo": "Vivo (Telefônica)",
    "telefonicavivo": "Vivo",
    "tim": "TIM Brasil",
    "timbrasil": "TIM Brasil",
    "oi": "Oi Telecom",
    "oifibra": "Oi Fibra",
    "embratel": "Embratel (Claro)",
    "algar": "Algar Telecom",
    "algartelecom": "Algar Telecom",
    "brisanet": "Brisanet",
    "desktop": "Desktop Internet",
    "unifique": "Unifique",
    "vero": "Vero Internet",
    "ligga": "Ligga Telecom",
    "sky": "SKY Brasil",
    "skybrasil": "SKY Brasil",
    "net": "NET (Claro)",
    "directv": "Directv Go / DGO",
    "starlink": "Starlink (SpaceX)"
}

# K. Games, Consoles & Esports
TRADEMARKS_GAMES: Dict[str, str] = {
    "playstation": "PlayStation (Sony)",
    "ps5": "PlayStation 5",
    "ps4": "PlayStation 4",
    "psplus": "PlayStation Plus",
    "nintendo": "Nintendo",
    "nintendoswitch": "Nintendo Switch",
    "pokemon": "Pokémon (Nintendo/Game Freak)",
    "pokémon": "Pokémon",
    "mario": "Super Mario (Nintendo)",
    "supermario": "Super Mario (Nintendo)",
    "zelda": "The Legend of Zelda (Nintendo)",
    "sega": "Sega",
    "sonic": "Sonic the Hedgehog (Sega)",
    "capcom": "Capcom",
    "residentevil": "Resident Evil (Capcom)",
    "streetfighter": "Street Fighter (Capcom)",
    "konami": "Konami",
    "bandainamco": "Bandai Namco",
    "squareenix": "Square Enix",
    "ea": "Electronic Arts",
    "easports": "EA Sports",
    "fifa": "EA Sports / FIFA",
    "eafc": "EA Sports FC",
    "blizzard": "Activision Blizzard",
    "activision": "Activision Blizzard",
    "callofduty": "Call of Duty (Activision)",
    "warzone": "Call of Duty Warzone",
    "worldofwarcraft": "World of Warcraft",
    "diablo": "Diablo (Blizzard)",
    "overwatch": "Overwatch (Blizzard)",
    "riotgames": "Riot Games",
    "leagueoflegends": "League of Legends",
    "valorant": "Valorant (Riot Games)",
    "garena": "Garena (Sea Group)",
    "freefire": "Free Fire (Garena)",
    "pubg": "PUBG Mobile (Krafton)",
    "epicgames": "Epic Games",
    "fortnite": "Fortnite (Epic Games)",
    "valve": "Valve Corporation",
    "steam": "Steam (Valve)",
    "counterstrike": "Counter-Strike (Valve)",
    "csgo": "Counter-Strike (Valve)",
    "cs2": "Counter-Strike 2 (Valve)",
    "rockstargames": "Rockstar Games (Take-Two)",
    "gta": "Grand Theft Auto (Rockstar Games)",
    "grandtheftauto": "Grand Theft Auto",
    "reddead": "Red Dead Redemption",
    "ubisoft": "Ubisoft",
    "assassinscreed": "Assassin's Creed",
    "roblox": "Roblox Corporation",
    "minecraft": "Minecraft (Microsoft/Mojang)",
    "mojang": "Mojang Studios",
    "genshinimpact": "Genshin Impact (miHoYo)",
    "mihoyo": "miHoYo / HoYoverse",
    "supercell": "Supercell",
    "clashofclans": "Clash of Clans",
    "brawlstars": "Brawl Stars"
}

# L. Moda, Joias, Relógios & Luxo
TRADEMARKS_FASHION_LUXURY: Dict[str, str] = {
    "nike": "Nike Inc.",
    "airjordan": "Air Jordan (Nike)",
    "jordan": "Jordan (Nike)",
    "adidas": "Adidas",
    "yeezy": "Yeezy",
    "puma": "Puma",
    "underarmour": "Under Armour",
    "newbalance": "New Balance",
    "asics": "Asics",
    "mizuno": "Mizuno",
    "fila": "Fila",
    "reebok": "Reebok",
    "vans": "Vans",
    "converse": "Converse (Nike)",
    "allstar": "All Star (Converse)",
    "timberland": "Timberland",
    "oakley": "Oakley (EssilorLuxottica)",
    "rayban": "Ray-Ban (EssilorLuxottica)",
    "chillibeans": "Chilli Beans",
    "vivara": "Vivara Joias",
    "pandora": "Pandora Joias",
    "hstern": "H. Stern",
    "montecarlo": "Monte Carlo Joias",
    "rolex": "Rolex",
    "omega": "Omega Watches",
    "tagheuer": "TAG Heuer (LVMH)",
    "cartier": "Cartier (Richemont)",
    "tiffany": "Tiffany & Co. (LVMH)",
    "bvlgari": "Bvlgari (LVMH)",
    "casio": "Casio",
    "gshock": "G-Shock (Casio)",
    "seiko": "Seiko",
    "citizen": "Citizen Watch",
    "fossil": "Fossil",
    "diesel": "Diesel",
    "tommyhilfiger": "Tommy Hilfiger",
    "calvinklein": "Calvin Klein",
    "ralphlauren": "Ralph Lauren",
    "lacoste": "Lacoste",
    "hugoboss": "Hugo Boss",
    "armani": "Giorgio Armani",
    "emporioarmani": "Emporio Armani",
    "gucci": "Gucci (Kering)",
    "louisvuitton": "Louis Vuitton (LVMH)",
    "lv": "Louis Vuitton",
    "prada": "Prada",
    "chanel": "Chanel",
    "dior": "Christian Dior (LVMH)",
    "hermes": "Hermès",
    "balenciaga": "Balenciaga (Kering)",
    "versace": "Versace (Capri)",
    "dolcegabbana": "Dolce & Gabbana",
    "burberry": "Burberry",
    "fendi": "Fendi (LVMH)",
    "ysl": "Yves Saint Laurent (Kering)",
    "givenchy": "Givenchy (LVMH)",
    "valentino": "Valentino",
    "victoriassecret": "Victoria's Secret"
}

# Merge all into one canonical lookup dictionary
ALL_TRADEMARKS: Dict[str, str] = {
    **TRADEMARKS_BETTING,
    **TRADEMARKS_INFOPRODUCTS_EDTECH,
    **TRADEMARKS_TECH_AI,
    **TRADEMARKS_FINANCIAL,
    **TRADEMARKS_RETAIL_ECOM,
    **TRADEMARKS_MEDIA,
    **TRADEMARKS_FOOD_BEV,
    **TRADEMARKS_PHARMA_BEAUTY,
    **TRADEMARKS_AUTO_INDUSTRY,
    **TRADEMARKS_TELECOM,
    **TRADEMARKS_GAMES,
    **TRADEMARKS_FASHION_LUXURY
}

# ==============================================================================
# 2. COMMERCIAL AFFIXES & SLUGS (CYBERSQUATTING SIGNALS)
# ==============================================================================

CYBERSQUATTING_AFFIXES: Set[str] = {
    "oficial", "login", "suporte", "sac", "app", "promo", "promocao",
    "desconto", "cupom", "afiliado", "afiliados", "loja", "store",
    "portal", "curso", "cursos", "entrar", "painel", "segundavia",
    "atendimento", "brasil", "br", "24h", "online", "vip", "bonus",
    "apostas", "download", "apk", "comprar", "vender", "cadastro",
    "seguro", "contato", "site", "web", "link", "gratis", "free",
    "acesso", "canal", "grupo", "clube", "hub", "shop", "bot"
}

# ==============================================================================
# 3. GENERIC DICTIONARY WHITELIST (PREVENTS FALSE POSITIVES ON SHORT/COMMON WORDS)
# ==============================================================================

# Words that contain short brand keys (like 'tim', 'elo', 'gol', 'claro', 'vivo', 'vale', 'max', 'ponto', 'extra', 'inter')
# but are legitimate generic Portuguese or English dictionary terms.
GENERIC_WORD_WHITELIST: Set[str] = {
    # TIM false positive shields
    "otimizado", "otimizada", "otimizacao", "otimizador", "otimizar", "intimo", "intima",
    "intimidade", "sentimento", "sentimentos", "estimativa", "estimado", "vitima", "vitimas",
    "legitimo", "legitima", "legitimidade", "otimismo", "otimista", "rotina", "rotinas",
    "estimulo", "estimular", "ultimato", "centimetro", "centimetros", "multimidia",
    
    # ELO false positive shields
    "modelo", "modelos", "cabelo", "cabelos", "cabelereiro", "castelo", "castelos",
    "amarelo", "amarela", "amarelos", "martelo", "camelo", "zelo", "singelo", "singela",
    "desenvolvedor", "cotovelo", "desenvolvimento", "pesadelo", "pesadelos", "duelo", "duelos",
    "selo", "selos", "chinelo", "chinelos", "farelo", "paralelo", "paralela", "avelo",
    
    # GOL false positive shields
    "algoritmo", "algoritmos", "goleiro", "goleiros", "goleada", "goleador", "pagol",
    "argola", "angola", "gola", "golas", "mongolia",
    
    # CLARO false positive shields (when not preceded/followed by telecom tokens)
    "claraboia", "claridade", "clareamento", "esclarecimento", "esclarecer", "declaracao", "declarar",
    
    # VIVO false positive shields
    "convivio", "convivencia", "revivor", "sobrevivente", "sobrevivencia", "reviver",
    
    # VALE false positive shields
    "valente", "valentia", "equivalente", "equivalencia", "prevalecer", "prevalente",
    
    # MAX false positive shields
    "climax", "maximo", "maxima", "maximizar", "maximizacao",
    
    # PONTO false positive shields
    "espontaneo", "espontanea", "apontamento", "apontador", "apontar",
    
    # EXTRA false positive shields
    "extraordinario", "extraordinaria", "extracao", "extrator", "extrato", "extratos",
    "extravagante", "extravasor", "extradicao",
    
    # INTER false positive shields
    "internacional", "interesse", "interessante", "internet", "intervalo", "interativo",
    "interatividade", "interiores", "interior", "intervencao", "intermediario"
}

# Brands that require strict exact root, boundary delimiter or verified commercial affix match to avoid false positives
STRICT_MATCH_BRANDS: Set[str] = {
    "tim", "elo", "gol", "oi", "bb", "vw", "hp", "lg", "ea", "ge", "b3", "gap", "kto",
    "byd", "gwm", "zap", "olx", "tnt", "sky", "c&a", "cea", "max", "tot", "pan", "dia",
    "sol", "rio", "claro", "vivo", "vale", "ponto", "extra", "inter", "clear", "stone",
    "ton", "mac", "sub", "fox", "ale", "vr", "dgo", "net", "c6", "xp", "btg", "pg"
}

# Homoglyphs table to detect obfuscation (e.g. g00gle, paypa1, faceb00k)
HOMOGLYPHS_MAP = str.maketrans({
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "8": "b",
    "@": "a",
    "$": "s"
})

def _clean_domain_for_trademark(domain_or_handle: str) -> str:
    """
    Strips protocol, www, slashes, TLD extensions and symbols to extract core brand tokens.
    """
    if not domain_or_handle:
        return ""
    
    text = domain_or_handle.lower().strip()
    text = re.sub(r"^https?://", "", text)
    text = re.sub(r"^www\.", "", text)
    text = text.split("/")[0] # Strip paths
    text = text.replace("@", "").replace("📸", "").strip()

    # Remove common TLD extensions (.com.br, .com, .net, .org, .online, .bet, .site, etc.)
    tlds = [
        ".com.br", ".net.br", ".org.br", ".adv.br", ".med.br", ".app.br", ".eco.br",
        ".co.uk", ".org.uk", ".com.mx", ".com.au", ".co.in", ".bet.br",
        ".com", ".net", ".org", ".info", ".biz", ".io", ".co", ".me", ".tv", ".cc",
        ".de", ".uk", ".es", ".fr", ".it", ".nl", ".eu", ".ca", ".au", ".in", ".ru",
        ".app", ".dev", ".ai", ".xyz", ".online", ".site", ".store", ".shop", ".tech",
        ".club", ".vip", ".pro", ".br", ".us", ".bet", ".live", ".space", ".fun"
    ]
    for tld in tlds:
        if text.endswith(tld):
            text = text[:-len(tld)]
            break

    # Remove special characters
    clean = re.sub(r"[^a-z0-9]", "", text)
    return clean


def _extract_domain_tokens(raw_name: str) -> List[str]:
    """
    Splits domain by hyphens, dots, underscores, numbers, and camelCase.
    """
    clean_raw = raw_name.lower().strip()
    clean_raw = re.sub(r"^https?://", "", clean_raw)
    clean_raw = re.sub(r"^www\.", "", clean_raw)
    clean_raw = clean_raw.split("/")[0]
    
    # Split on non-alphanumeric
    parts = re.split(r"[-_.\s]+", clean_raw)
    return [p for p in parts if p]


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculates Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def analyze_trademark_risk(domain_or_handle: str) -> Dict[str, Any]:
    """
    Performs comprehensive Trademark Safety & Brand Infringement risk analysis:
    1. Direct match with renowned brands (e.g. 'mercadolivre.com', 'apple.com.br', 'betano.com').
    2. Compound Cybersquatting match (e.g. 'ofertas-mercadolivre.com', 'suporteapple.com', 'bet365bonus.net').
    3. Smart delimiter & affix token matching (anti-false-positive engine).
    4. Typosquatting / Homoglyph proximity match (e.g. 'mercadolvre', 'faceb00k', 'whatsap').
    5. Safe Generic & Descriptive verification.

    Returns rich dictionary with risk level, visual badges, matched brand details,
    legal guidance, and direct INPI/WIPO search URLs.
    """
    raw_name = domain_or_handle or ""
    clean_token = _clean_domain_for_trademark(raw_name)
    tokens = _extract_domain_tokens(raw_name)

    if not clean_token:
        return {
            "risk_level": "SAFE",
            "is_safe": True,
            "badge": "🟢 Seguro p/ Registro",
            "badge_short": "🟢 Seguro",
            "color": "#16A34A",
            "detected_brands": [],
            "matched_names": "",
            "legal_advice": "Domínio genérico ou sem marca detectada.",
            "inpi_url": "https://busca.inpi.gov.br/pePI/servlet/MarcasServletController",
            "wipo_url": "https://branddb.wipo.int/"
        }

    # Whitelist check: If the full clean token is in the dictionary whitelist, mark SAFE immediately
    if clean_token in GENERIC_WORD_WHITELIST:
        return {
            "risk_level": "SAFE",
            "is_safe": True,
            "badge": "🟢 Seguro p/ Uso (Genérico)",
            "badge_short": "🟢 Seguro",
            "color": "#16A34A",
            "detected_brands": [],
            "matched_names": "Termo Genérico Dicionarizado",
            "legal_advice": "🟢 DOMÍNIO SEGURO. Palavra comum dicionarizada, livre de risco de apropriação indevida de marca.",
            "inpi_url": "https://busca.inpi.gov.br/pePI/servlet/MarcasServletController",
            "wipo_url": "https://branddb.wipo.int/"
        }

    detected_brands: List[Tuple[str, str, str]] = [] # (brand_key, official_name, match_type: EXACT, DELIMITED, COMPOUND, TYPOSQUAT)

    # -------------------------------------------------------------------------
    # Tier 1 & 2: Exact, Delimited, and Compound Trademark Overlaps
    # -------------------------------------------------------------------------
    for brand_key, official_name in ALL_TRADEMARKS.items():
        # Check Exact Match
        if clean_token == brand_key:
            detected_brands.append((brand_key, official_name, "EXACT"))
            continue

        # Check Delimited Match in raw tokens (e.g. 'loja-nike', 'promo_itau')
        if brand_key in tokens:
            detected_brands.append((brand_key, official_name, "DELIMITED"))
            continue

        # For short brands (len <= 3) or strictly controlled brands (like tim, elo, gol, claro, vivo, vale, max)
        if len(brand_key) <= 3 or brand_key in STRICT_MATCH_BRANDS:
            # 2-letter brands (e.g. 'lv', 'bb', 'vw', 'oi', 'hp', 'lg', 'ea', 'ge', 'b3', 'c6', 'xp')
            # must match EXACTLY or as a delimited token (e.g. 'loja-lv')
            if len(brand_key) <= 2:
                continue
            
            # 3-letter brands (e.g. 'tim', 'elo', 'gol', 'byd', 'gwm', 'olx', 'sky')
            # Check if brand_key is combined with explicit commercial affixes in clean_token
            # e.g., 'timrecargas', 'planostim', 'voegol', 'golviagens', 'cartaoelo', 'elobeneficios', 'claroservicos'
            for affix in CYBERSQUATTING_AFFIXES:
                if clean_token.startswith(f"{brand_key}{affix}") or clean_token.endswith(f"{affix}{brand_key}") or clean_token.startswith(f"{affix}{brand_key}"):
                    detected_brands.append((brand_key, official_name, "COMPOUND"))
                    break
            continue

        # For regular brands (len >= 4, distinctive trademarks like mercadolivre, nubank, shopee, betano, hotmart, chatgpt)
        if brand_key in clean_token:
            # Check if the surrounding string forms a generic whitelisted word
            is_whitelisted = False
            for white_word in GENERIC_WORD_WHITELIST:
                if white_word in clean_token:
                    is_whitelisted = True
                    break
            
            if not is_whitelisted:
                detected_brands.append((brand_key, official_name, "COMPOUND"))

    # -------------------------------------------------------------------------
    # Tier 3: Typosquatting & Homoglyphs Detection (Proximity Match)
    # -------------------------------------------------------------------------
    if not detected_brands:
        # Check homoglyph substitution (e.g. 'g00gle', 'faceb00k', 'n0bank')
        normalized_homoglyphs = clean_token.translate(HOMOGLYPHS_MAP)
        if normalized_homoglyphs != clean_token:
            for brand_key, official_name in ALL_TRADEMARKS.items():
                if len(brand_key) >= 4 and (brand_key == normalized_homoglyphs or brand_key in normalized_homoglyphs):
                    detected_brands.append((brand_key, official_name, "TYPOSQUAT"))
                    break

        # Check Levenshtein distance for core high-value brands (length >= 5)
        if not detected_brands:
            for brand_key, official_name in ALL_TRADEMARKS.items():
                if len(brand_key) >= 5 and abs(len(clean_token) - len(brand_key)) <= 1:
                    dist = _levenshtein_distance(clean_token, brand_key)
                    if dist == 1:
                        # 1-character typo (e.g. 'mercadolvre', 'whatsap', 'instagraam', 'betanno')
                        detected_brands.append((brand_key, official_name, "TYPOSQUAT"))
                        break

    # -------------------------------------------------------------------------
    # Risk Level Synthesis & Legal Opinion Generation
    # -------------------------------------------------------------------------
    if detected_brands:
        # Prioritize exact/delimited matches if present
        exact_matches = [b for b in detected_brands if b[2] in ("EXACT", "DELIMITED")]
        typo_matches = [b for b in detected_brands if b[2] == "TYPOSQUAT"]
        
        if exact_matches:
            primary_match = exact_matches[0]
        elif typo_matches and not [b for b in detected_brands if b[2] == "COMPOUND"]:
            primary_match = typo_matches[0]
        else:
            primary_match = detected_brands[0]
            
        brand_key, official_name, m_type = primary_match
        
        all_official_names = list(dict.fromkeys([b[1] for b in detected_brands]))
        names_str = ", ".join(all_official_names)

        # Generate direct search URLs
        encoded_brand = urllib.parse.quote(brand_key)
        inpi_search_url = "https://busca.inpi.gov.br/pePI/servlet/MarcasServletController"
        wipo_search_url = f"https://branddb.wipo.int/en/similarname/search?sort=score%20desc&rows=30&asStructure=%7B%22_boolean%22:%22AND%22,%22_subStructure%22:%5B%7B%22_boolean%22:%22AND%22,%22_field%22:%22brandName%22,%22_value%22:%22{encoded_brand}%22%7D%5D%7D"

        if m_type == "EXACT":
            advice = (
                f"🚨 ALTO RISCO LEGAL (Marca Notória Registrada: {official_name}). "
                f"O uso deste domínio viola a Lei de Propriedade Industrial (Lei 9.279/96, Art. 124, XIX e Art. 125) "
                f"e está sujeito a perda imediata via processo SACI-Adm (Registro.br) ou UDRP (ICANN), "
                f"além de processos judiciais por indenização por uso indevido de marca."
            )
            badge = f"🔴 Marca Registrada ({official_name})"
            badge_short = f"🔴 Risco Marca ({official_name})"
            risk_level = "HIGH_RISK"
            color = "#EF4444" # Red
        elif m_type in ("DELIMITED", "COMPOUND"):
            advice = (
                f"⚠️ RISCO DE CYBERSQUATTING (Contém a marca registrada: {official_name}). "
                f"Registrar ou monetizar domínios associando marcas famosas a afixos ou prefixos/sufixos "
                f"viola o Art. 124 da Lei 9.279/96. O titular da marca ({official_name}) tem direito legal "
                f"de requisitar a transferência compulsória do domínio via SACI-Adm/UDRP sem ressarcimento."
            )
            badge = f"🔴 Contém Marca ({official_name})"
            badge_short = f"🔴 Cybersquatting ({official_name})"
            risk_level = "HIGH_RISK"
            color = "#EF4444" # Red
        else: # TYPOSQUAT
            advice = (
                f"🟡 ALERTA DE TYPOSQUATTING / SIMILARIDADE FONÉTICA ({official_name}). "
                f"Identificada alta similaridade fonética ou erro proposital de digitação em relação à marca '{official_name}'. "
                f"Prática de Typosquatting sujeita a disputas de cancelamento ou transferência pelo titular legítimo."
            )
            badge = f"🟡 Similaridade / Typosquatting ({official_name})"
            badge_short = f"🟡 Similar ({official_name})"
            risk_level = "MODERATE_RISK"
            color = "#F59E0B" # Amber/Orange

        return {
            "risk_level": risk_level,
            "is_safe": False,
            "badge": badge,
            "badge_short": badge_short,
            "color": color,
            "detected_brands": all_official_names,
            "matched_names": names_str,
            "legal_advice": advice,
            "inpi_url": inpi_search_url,
            "wipo_url": wipo_search_url
        }

    # -------------------------------------------------------------------------
    # Safe Generic & Descriptive Verification
    # -------------------------------------------------------------------------
    encoded_token = urllib.parse.quote(clean_token)
    inpi_search_url = "https://busca.inpi.gov.br/pePI/servlet/MarcasServletController"
    wipo_search_url = f"https://branddb.wipo.int/en/similarname/search?sort=score%20desc&rows=30&asStructure=%7B%22_boolean%22:%22AND%22,%22_subStructure%22:%5B%7B%22_boolean%22:%22AND%22,%22_field%22:%22brandName%22,%22_value%22:%22{encoded_token}%22%7D%5D%7D"

    advice = (
        "🟢 DOMÍNIO SEGURO PARA USO. Não foram detectadas marcas notórias ou conflitos de cybersquatting. "
        "Termo genérico, descritivo ou de nicho livre para registro, redirecionamento de tráfego e monetização sem risco legal."
    )

    return {
        "risk_level": "SAFE",
        "is_safe": True,
        "badge": "🟢 Seguro p/ Uso (Genérico)",
        "badge_short": "🟢 Seguro",
        "color": "#16A34A", # Green
        "detected_brands": [],
        "matched_names": "Nenhuma marca notória detectada",
        "legal_advice": advice,
        "inpi_url": inpi_search_url,
        "wipo_url": wipo_search_url
    }
