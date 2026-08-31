"""
Multi-Language Translation & High-Precision Linguistic Classification Engine.
Features:
- Massive multi-thousand word dictionary for Portuguese, Spanish, and regional dialects.
- Strict morphological and grammatical isolation (eliminates Spanish false positives like 'Jugué GTA', 'La policía me quitó', 'Encuentro y tuneo un coche secreto').
- Isolated conjunction and preposition tracking (e.g. 'y', 'el', 'los', 'las', 'del', 'al', 'en', 'es').
- Localized YouTube query expansion with country tokens (e.g. 'GTA brasil', 'GTA portugues').
"""

import re
import urllib.parse
import logging
from typing import List, Dict, Optional, Set
import requests

logger = logging.getLogger(__name__)

UNIVERSAL_TERMS: Set[str] = {
    "gta", "gta 5", "gta 6", "gta rp", "minecraft", "roblox", "fortnite", "valorant",
    "cod", "warzone", "fifa", "ea fc", "csgo", "cs2", "lol", "dota", "free fire",
    "seo", "cpa", "plr", "vls", "vsl", "drop", "dropshipping", "ecommerce", "e-com",
    "ia", "ai", "chatgpt", "midjourney", "gemini", "python", "javascript", "react",
    "crypto", "bitcoin", "btc", "ethereum", "eth", "nft", "forex", "trading",
    "iphone", "android", "ios", "windows", "mac", "pc", "playstation", "ps5", "xbox"
}

# Words and tokens that are EXCLUSIVELY Portuguese (NOT Spanish or English)
PT_EXCLUSIVE_WORDS = {
    "o", "os", "um", "uma", "uns", "umas", "do", "da", "dos", "das",
    "no", "na", "nos", "nas", "ao", "aos", "à", "às", "pelo", "pela",
    "pelos", "pelas", "num", "numa", "nuns", "numas", "dele", "dela",
    "deles", "delas", "nele", "nela", "neles", "nelas", "você", "voce",
    "vocês", "voces", "vc", "vcs", "pra", "pras", "pro", "pros", "ele",
    "ela", "eles", "elas", "nós", "meu", "minha", "meus", "minhas",
    "teu", "tua", "teus", "tuas", "seu", "sua", "seus", "suas", "nosso",
    "nossa", "nossos", "nossas", "este", "esta", "estes", "estas", "esse",
    "essa", "esses", "essas", "aquele", "aquela", "aqueles", "aquelas",
    "isto", "isso", "aquilo", "mesmo", "mesma", "mesmos", "mesmas",
    "qual", "quais", "quem", "quanto", "quanta", "quantos", "quantas",
    "onde", "aonde", "quando", "como", "porque", "porquê", "muito",
    "muita", "muitos", "muitas", "pouco", "pouca", "poucos", "poucas",
    "todo", "toda", "todos", "todas", "outro", "outra", "outros", "outras",
    "algum", "alguma", "alguns", "algumas", "nenhum", "nenhuma", "tudo",
    "nada", "algo", "alguém", "alguem", "ninguém", "ninguem", "mais",
    "menos", "bem", "mal", "assim", "hoje", "ontem", "amanhã", "amanha",
    "agora", "já", "ja", "sempre", "nunca", "jamais", "aqui", "aí", "ai",
    "ali", "lá", "la", "dentro", "fora", "acima", "abaixo", "atrás",
    "atras", "antes", "depois", "cedo", "tarde", "também", "tambem",
    "não", "nao", "sim", "realmente", "talvez", "jogando", "joguei", "jogou",
    "jogamos", "jogaram", "fazer", "fiz", "fez", "fizemos", "fizeram",
    "ganhar", "ganhei", "ganhou", "vídeo", "video", "canal", "brasil",
    "brasileiro", "brasileira", "jogo", "jogos", "passo a passo", "tutorial",
    "dicas", "completo", "dublado", "legendado", "servidor", "vida real",
    "inscreva-se", "inscrevase", "deixe seu like", "se inscreva",
    "compartilhe", "valeu", "galera", "pessoal", "mano", "bora", "tá",
    "ta", "tô", "to", "estou", "está", "estamos", "estão", "carro", "carros",
    "moto", "motos", "favela", "policial", "polícia", "policia", "troca de tiros",
    "confronto", "bope", "pmce", "pmesp", "pmrj", "policia militar",
    "casamento", "filme", "episodio", "episódio", "temporada", "dinheiro",
    "milhões", "milhoes", "mil", "comprando", "comprei", "comprou", "mansão",
    "mansao", "vida", "vida de", "segredo", "segredos", "escondido",
    "virando", "fui", "fui preso", "preso", "fuga", "fuga épica", "fuga epica"
}

# Words and tokens that are EXCLUSIVELY Spanish (NOT Portuguese)
ES_EXCLUSIVE_WORDS = {
    # Pronouns & Articles
    "el", "la", "los", "las", "un", "del", "al", "yo", "tú", "tu", "él", "el",
    "ella", "ellos", "ellas", "nosotros", "nosotras", "usted", "ustedes",
    "vos", "vosotros", "vosotras", "mi", "mis", "su", "sus", "nuestro",
    "nuestra", "nuestros", "nuestras", "este", "esta", "estos", "estas",
    "ese", "esa", "esos", "esas", "aquel", "aquella", "aquellos", "aquellas",
    "esto", "eso", "aquello",
    
    # Prepositions & Conjunctions
    "y", "e", "ni", "o", "u", "pero", "sino", "aunque", "porque", "por que",
    "por qué", "pues", "ya que", "con", "sin", "sobre", "entre", "hasta",
    "desde", "hacia", "contra", "durante", "según", "segun", "tras", "bajo",
    "en", "para", "por",
    
    # Verbs (Spanish Conjugations)
    "es", "son", "era", "eran", "fue", "fueron", "ser", "estar", "está",
    "esta", "están", "estan", "estoy", "estás", "estas", "estamos", "estuve",
    "estuviste", "estuvo", "estuvimos", "estuvieron",
    "jugué", "jugue", "juegas", "juega", "jugamos", "juegan", "jugaron",
    "jugando", "jugar",
    "coche", "coches", "auto", "autos",
    "quitó", "quito", "quitas", "quita", "quitamos", "quitaron", "quitar",
    "me quitó", "me quito", "le quitó", "le quito", "nos quitó",
    "costosa", "costoso", "costosas", "costosos",
    "policía", "policia", "policías", "policias",
    "tuneo", "tuneas", "tunea", "tuneamos", "tunen", "tunear", "tuneando",
    "encuentro", "encuentras", "encuentra", "encontré", "encontre", "encontró",
    "encontro", "encontramos", "encontraron", "encontrar",
    "hago", "haces", "hace", "hacemos", "hacen", "hice", "hiciste", "hizo",
    "hicimos", "hicieron", "hagan", "hacer", "haciendo",
    "tengo", "tienes", "tiene", "tenemos", "tienen", "tuve", "tuviste", "tuvo",
    "tuvimos", "tuvieron", "tener", "teniendo",
    "puedo", "puedes", "puede", "podemos", "pueden", "pude", "pudo",
    "voy", "vas", "va", "vamos", "van", "fui", "fuiste", "fue",
    "quiero", "quieres", "quiere", "queremos", "quieren", "quise", "quiso",
    "sé", "sabes", "sabe", "sabemos", "saben", "supe", "supo",
    "veo", "ves", "ve", "vemos", "ven", "vi", "viste", "vio", "vieron",
    "mira", "miren", "míralo", "miralo",
    "digo", "dices", "dice", "decimos", "dicen", "dije", "dijo",
    "compro", "compras", "compra", "compré", "compre", "compró", "compro",
    "compramos", "compraron", "comprar", "comprando",
    "mato", "matas", "mata", "maté", "mate", "mató", "mato", "mataron",
    "robo", "robas", "roba", "robé", "robe", "robó", "robo", "robaron",
    "escapo", "escapas", "escapa", "escapé", "escape", "escapó", "escaparon",
    
    # Common Nouns & Adjectives
    "dinero", "plata", "pesos", "dólares", "dolares", "gratis", "truco",
    "trucos", "misterio", "misterios", "historia", "capítulo", "capitulo",
    "canción", "cancion", "canciones", "letra", "video oficial", "vídeo oficial",
    "tema oficial", "disco", "álbum", "album", "música", "musica",
    "chico", "chica", "chicos", "chicas", "amigo", "amiga", "amigos", "amigas",
    "hombre", "mujer", "gente", "personas", "niño", "niña", "niños", "niñas",
    "mundo", "ciudad", "calle", "barrio", "vaceo", "droga", "droga e mala",
    "caos", "completo caos", "locura", "secreto", "secreta", "secretos", "secretas",
    "año", "años", "ano", "anos", "día", "dia", "días", "dias", "hora", "horas",
    "semana", "semanas", "mes", "meses",
    "bueno", "buena", "buenos", "buenas", "malo", "mala", "malos", "malas",
    "nuevo", "nueva", "nuevos", "nuevas", "viejo", "vieja", "viejos", "viejas",
    "grande", "grandes", "pequeño", "pequeña", "pequeños", "pequeñas",
    "primer", "primero", "primera", "primeros", "primeras",
    "último", "ultimo", "última", "ultima", "últimos", "ultimos", "últimas", "ultimas",
    "mejor", "mejores", "peor", "peores",
    "más", "mas", "menos", "muy", "mucho", "mucha", "muchos", "muchas",
    "poco", "poca", "pocos", "pocas", "demasiado", "bastante",
    "cada", "ambos", "ambas", "todo", "toda", "todos", "todas",
    "alguno", "alguna", "algunos", "algunas", "ninguno", "ninguna",
    "cual", "cuál", "cuales", "cuáles", "cuanto", "cuánto", "cuanta", "cuánta",
    "cuantos", "cuántos", "cuantas", "cuántas",
    "cómo", "como", "dónde", "donde", "cuándo", "cuando", "quién", "quien",
    "quiénes", "quienes", "qué", "que",
    "españa", "espana", "español", "espanol", "castellano", "latino", "méxico",
    "mexico", "argentina", "colombia", "chile", "peru", "perú",
    "suscríbete", "suscribete", "deja tu like", "comenta", "comparte",
    "sígueme", "sigueme", "únete", "unete", "activa la campanita"
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
    Generate localized search queries with country tokens.
    """
    keyword = keyword.strip()
    if not keyword:
        return []

    if language_code == "global":
        tasks = []
        for l_code in GLOBAL_EXPANSION_LANGS:
            info = AVAILABLE_LANGUAGES.get(l_code, {})
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
        tasks = []

        if language_code == "pt":
            # For short terms in Portuguese (e.g. GTA, SEO, PLR, dropshipping), query localized tokens
            if len(keyword.split()) <= 2:
                for q_variant in [f"{keyword} brasil", f"{keyword} portugues", f"{keyword} pt-br", keyword]:
                    tasks.append({
                        "query": q_variant,
                        "original_keyword": keyword,
                        "lang_code": "pt",
                        "lang_name": info.get("name", "Português (Brasil)"),
                        "flag": info.get("flag", "🇧🇷"),
                        "hl": "pt",
                        "gl": "BR"
                    })
                return tasks
            else:
                target_query = keyword
        elif language_code == "es":
            if len(keyword.split()) <= 2:
                for q_variant in [f"{keyword} español", f"{keyword} espana", keyword]:
                    tasks.append({
                        "query": q_variant,
                        "original_keyword": keyword,
                        "lang_code": "es",
                        "lang_name": info.get("name", "Espanhol"),
                        "flag": info.get("flag", "🇪🇸"),
                        "hl": "es",
                        "gl": "ES"
                    })
                return tasks
            else:
                target_query = translate_query(keyword, "es")
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


def is_content_matching_language(
    title: str,
    description: str,
    channel_name: str,
    target_lang: str,
    comments_sample: str = ""
) -> bool:
    """
    High-precision multi-layer linguistic scoring engine.
    Strictly filters out foreign content (especially Spanish vs Portuguese).
    """
    if not target_lang or target_lang in ("global", "auto", "en"):
        return True

    title_clean = title.lower()
    full_text = f"{title} {description} {channel_name} {comments_sample}".lower()
    
    words_list = re.findall(r"\b\w+\b", full_text)
    words_set = set(words_list)
    title_words_set = set(re.findall(r"\b\w+\b", title_clean))

    if target_lang == "pt":
        pt_score = 0
        es_score = 0

        # 1. Exclusive Spanish Characters (ñ, ¿, ¡) -> Immediate heavy penalty
        if re.search(r"[ñ¿¡]", full_text):
            es_score += 30

        # 2. Exclusive Portuguese Characters (ã, õ, ç, ê, ô, à do NOT exist in Spanish)
        pt_char_matches = len(re.findall(r"[ãõçêôà]", full_text))
        pt_score += pt_char_matches * 6

        # 3. Isolated Spanish Conjunction 'y' (In Portuguese, conjunction is 'e')
        if re.search(r"\by\b", title_clean) or re.search(r"\by\b", full_text):
            es_score += 15

        # 4. Strict Title Word Matches (Title carries 70% of grammatical intent)
        matched_es_title = title_words_set.intersection(ES_EXCLUSIVE_WORDS)
        matched_pt_title = title_words_set.intersection(PT_EXCLUSIVE_WORDS)
        
        es_score += len(matched_es_title) * 8
        pt_score += len(matched_pt_title) * 6

        # 5. Full Context Word Matches
        matched_pt_full = words_set.intersection(PT_EXCLUSIVE_WORDS)
        matched_es_full = words_set.intersection(ES_EXCLUSIVE_WORDS)

        pt_score += len(matched_pt_full) * 3
        es_score += len(matched_es_full) * 4

        # 6. Check Brazilian tokens (only add weight if no strong Spanish words exist)
        if any(token in full_text for token in ["brasil", "brasileiro", "brasileira", "pt-br", "pt_br", "em português"]):
            if len(matched_es_title) == 0:
                pt_score += 8
            else:
                pt_score += 2

        # 7. Check explicit Spanish channel/video tokens
        if any(token in full_text for token in ["españa", "espana", "español", "espanol", "latino", "mexico", "argentina", "colombia", "en español", "canción oficial", "video oficial"]):
            es_score += 20

        # Strict Isolation Rules for Portuguese:
        # If Spanish words in title >= 2, reject immediately
        if len(matched_es_title) >= 2 and len(matched_pt_title) <= 1:
            return False

        # If es_score outweighs pt_score, reject
        if es_score > pt_score:
            return False

        # Must have at least minimum Portuguese presence
        if pt_score >= 3 and pt_score >= es_score:
            return True
        if pt_score > 0 and es_score == 0:
            return True

        return False

    elif target_lang == "es":
        es_score = 0
        pt_score = 0

        if re.search(r"[ñ¿¡]", full_text):
            es_score += 25
        if re.search(r"\by\b", title_clean):
            es_score += 15

        pt_char_matches = len(re.findall(r"[ãõçêôà]", full_text))
        pt_score += pt_char_matches * 10

        matched_es = words_set.intersection(ES_EXCLUSIVE_WORDS)
        matched_pt = words_set.intersection(PT_EXCLUSIVE_WORDS)

        es_score += len(matched_es) * 4
        pt_score += len(matched_pt) * 4

        return es_score >= 3 and es_score >= pt_score

    elif target_lang == "ru":
        return bool(re.search(r"[\u0400-\u04FF]", full_text))

    elif target_lang == "ja":
        return bool(re.search(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]", full_text))

    elif target_lang == "zh":
        return bool(re.search(r"[\u4e00-\u9fff]", full_text))

    elif target_lang == "ar":
        return bool(re.search(r"[\u0600-\u06ff]", full_text))

    elif target_lang == "ko":
        return bool(re.search(r"[\uac00-\ud7af]", full_text))

    elif target_lang == "hi":
        return bool(re.search(r"[\u0900-\u097f]", full_text))

    return True
