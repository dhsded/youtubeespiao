"""
Multi-Language Translation & Region Harvester Helper.
Supports 12+ major languages, regional parameters (hl/gl),
preserves acronyms, brands, proper nouns, and handles mixed long-tail keyword queries.
"""

import re
import urllib.parse
import logging
from typing import List, Dict, Optional, Set
import requests

logger = logging.getLogger(__name__)

# Common acronyms, tech terms, games, and universal brands that should NEVER be translated
UNIVERSAL_TERMS: Set[str] = {
    "gta", "gta 5", "gta 6", "gta rp", "minecraft", "roblox", "fortnite", "valorant",
    "cod", "warzone", "fifa", "ea fc", "csgo", "cs2", "lol", "dota",
    "seo", "cpa", "plr", "vls", "vsl", "drop", "dropshipping", "ecommerce", "e-com",
    "ia", "ai", "chatgpt", "midjourney", "gemini", "python", "javascript", "react",
    "crypto", "bitcoin", "btc", "ethereum", "eth", "nft", "forex", "trading",
    "iphone", "android", "ios", "windows", "mac", "pc", "playstation", "ps5", "xbox"
}

AVAILABLE_LANGUAGES: Dict[str, Dict[str, str]] = {
    "global": {
        "name": "Global (Todos os Idiomas)",
        "code": "global",
        "country": "US",
        "hl": "en",
        "gl": "US",
        "flag": "🌍"
    },
    "pt": {
        "name": "Português (Brasil)",
        "code": "pt",
        "country": "BR",
        "hl": "pt",
        "gl": "BR",
        "flag": "🇧🇷"
    },
    "en": {
        "name": "Inglês (Global / EUA)",
        "code": "en",
        "country": "US",
        "hl": "en",
        "gl": "US",
        "flag": "🇺🇸"
    },
    "es": {
        "name": "Espanhol (Espanha / LatAm)",
        "code": "es",
        "country": "ES",
        "hl": "es",
        "gl": "ES",
        "flag": "🇪🇸"
    },
    "ru": {
        "name": "Russo (Rússia)",
        "code": "ru",
        "country": "RU",
        "hl": "ru",
        "gl": "RU",
        "flag": "🇷🇺"
    },
    "ja": {
        "name": "Japonês (Japão)",
        "code": "ja",
        "country": "JP",
        "hl": "ja",
        "gl": "JP",
        "flag": "🇯🇵"
    },
    "de": {
        "name": "Alemão (Alemanha)",
        "code": "de",
        "country": "DE",
        "hl": "de",
        "gl": "DE",
        "flag": "🇩🇪"
    },
    "fr": {
        "name": "Francês (França)",
        "code": "fr",
        "country": "FR",
        "hl": "fr",
        "gl": "FR",
        "flag": "🇫🇷"
    },
    "it": {
        "name": "Italiano (Itália)",
        "code": "it",
        "country": "IT",
        "hl": "it",
        "gl": "IT",
        "flag": "🇮🇹"
    },
    "zh": {
        "name": "Chinês (Mandarim)",
        "code": "zh",
        "country": "CN",
        "hl": "zh-CN",
        "gl": "CN",
        "flag": "🇨🇳"
    },
    "ko": {
        "name": "Coreano (Coreia do Sul)",
        "code": "ko",
        "country": "KR",
        "hl": "ko",
        "gl": "KR",
        "flag": "🇰🇷"
    },
    "ar": {
        "name": "Árabe (Oriente Médio)",
        "code": "ar",
        "country": "SA",
        "hl": "ar",
        "gl": "SA",
        "flag": "🇸🇦"
    },
    "hi": {
        "name": "Hindi (Índia)",
        "code": "hi",
        "country": "IN",
        "hl": "hi",
        "gl": "IN",
        "flag": "🇮🇳"
    }
}

GLOBAL_EXPANSION_LANGS = ["pt", "en", "es", "ru", "ja", "de", "fr", "it", "zh", "ko", "ar", "hi"]

def is_universal_acronym(text: str) -> bool:
    """Check if the text is a universal acronym, game title, or proper noun."""
    clean = text.strip().lower()
    if clean in UNIVERSAL_TERMS:
        return True
    # Acronyms in all-caps (e.g. GTA, SEO, VSL, UFC, WWE)
    if text.isupper() and len(text) <= 5:
        return True
    return False

def get_language_list() -> List[Dict[str, str]]:
    """Return formatted languages for UI dropdown."""
    return [
        {
            "key": k,
            "label": f"{v['flag']} {v['name']}",
            "code": v["code"],
            "country": v["country"],
            "hl": v["hl"],
            "gl": v["gl"]
        }
        for k, v in AVAILABLE_LANGUAGES.items()
    ]

def translate_query(text: str, target_lang: str) -> str:
    """
    Translate query while preserving acronyms, brand names, and long-tail terms.
    If target_lang is 'pt' (or identical), returns original text.
    """
    text = text.strip()
    if not text or target_lang in ("global", "auto", "pt"):
        return text

    # If it's a known universal term or short uppercase acronym (e.g., 'GTA', 'SEO'), don't translate
    if is_universal_acronym(text):
        return text

    lang_code = target_lang
    if target_lang == "zh":
        lang_code = "zh-CN"

    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={lang_code}&dt=t&q={urllib.parse.quote(text)}"

    try:
        resp = requests.get(url, timeout=3.5, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        if resp.status_code == 200:
            data = resp.json()
            if data and isinstance(data, list) and len(data) > 0 and data[0]:
                translated_parts = [item[0] for item in data[0] if item and item[0]]
                translated = "".join(translated_parts).strip()
                if translated:
                    return translated
    except Exception as e:
        logger.debug(f"Translation failed for '{text}' to '{target_lang}': {e}")

    return text

def expand_queries_for_language(keyword: str, language_code: str) -> List[Dict[str, str]]:
    """
    Generate non-restrictive search tasks.
    - If 'global': Expands into all 12 major languages.
    - If specific language (e.g., 'pt', 'es', 'en'):
      Maintains user's exact long-tail keywords, preserves acronyms (e.g., 'GTA', 'GTA RP'),
      and avoids destructive translations.
    """
    keyword = keyword.strip()
    if not keyword:
        return []

    if language_code == "global":
        tasks = []
        for l_code in GLOBAL_EXPANSION_LANGS:
            info = AVAILABLE_LANGUAGES.get(l_code, {})
            # If keyword is universal acronym (like GTA), keep it as GTA in all regions
            translated = keyword if is_universal_acronym(keyword) else translate_query(keyword, l_code)
            tasks.append({
                "query": translated,
                "original_keyword": keyword,
                "lang_code": l_code,
                "lang_name": info.get("name", l_code),
                "flag": info.get("flag", "🌐"),
                "hl": info.get("hl", "en"),
                "gl": info.get("gl", "US")
            })
        return tasks
    else:
        info = AVAILABLE_LANGUAGES.get(language_code, AVAILABLE_LANGUAGES["pt"])
        
        # In specific language mode:
        # If language is Portuguese or the keyword is long-tail or acronym, keep exact user query
        if language_code == "pt" or is_universal_acronym(keyword):
            target_query = keyword
        else:
            target_query = translate_query(keyword, language_code)

        return [{
            "query": target_query,
            "original_keyword": keyword,
            "lang_code": language_code,
            "lang_name": info.get("name", language_code),
            "flag": info.get("flag", "🌐"),
            "hl": info.get("hl", "pt"),
            "gl": info.get("gl", "BR")
        }]
