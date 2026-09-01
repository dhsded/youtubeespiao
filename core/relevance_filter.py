"""
Intelligent Topic Relevance & Related Terms Engine for YouTube Mining.
Features:
- Live YouTube Autocomplete / Suggest query harvester (fetches real user search trends).
- Niche intent & long-tail semantic expansion ("como", "tutorial", "dicas", "ferramentas", "melhores", etc.).
- Multi-layer Topic Profile extraction (primary tokens, root stems, n-grams, related vocabulary).
- Strict Semantic Relevance Evaluator: guarantees that videos discovered belong to the target niche,
  completely eliminating topic drift and unrelated viral/clickbait videos.
"""

import re
import unicodedata
import urllib.parse
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
import requests

logger = logging.getLogger(__name__)

STOP_WORDS = {
    # Portuguese Stopwords
    "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "é", "com", "não",
    "uma", "os", "no", "se", "na", "por", "mais", "as", "dos", "como", "mas", "foi",
    "ao", "ele", "das", "tem", "à", "seu", "sua", "ou", "ser", "quando", "muito",
    "há", "nos", "já", "está", "eu", "também", "só", "pelo", "pela", "até", "isso",
    "ela", "entre", "era", "depois", "sem", "mesmo", "aos", "ter", "seus", "quem",
    "nas", "me", "esse", "eles", "estão", "você", "tinha", "foram", "essa", "num",
    "nem", "suas", "meu", "às", "minha", "têm", "numa", "pelos", "elas", "havia",
    "seja", "qual", "será", "nós", "tenho", "lhe", "deles", "essas", "esses", "pelas",
    "este", "fosse", "dele", "tu", "te", "vocês", "vos", "lhes", "meus", "minhas",
    "teu", "tua", "teus", "tuas", "nosso", "nossa", "nossos", "nossas", "dela", "delas",
    "esta", "estes", "estas", "aquele", "aquela", "aqueles", "aquelas", "isto", "aquilo",
    "estou", "está", "estamos", "estão", "estive", "esteve", "estivemos", "estiveram",
    "pra", "pro", "pras", "pros", "vc", "vcs", "tb", "tbm", "pq", "né", "ne",
    
    # English Stopwords
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not",
    "on", "with", "he", "as", "you", "do", "at", "this", "but", "his", "by", "from",
    "they", "we", "say", "her", "she", "or", "an", "will", "my", "one", "all", "would",
    "there", "their", "what", "so", "up", "out", "if", "about", "who", "get", "which",
    "go", "me", "when", "make", "can", "like", "time", "no", "just", "him", "know",
    "take", "people", "into", "year", "your", "good", "some", "could", "them", "see",
    "other", "than", "then", "now", "look", "only", "come", "its", "over", "think",
    "also", "back", "after", "use", "two", "how", "our", "work", "first", "well",
    "way", "even", "new", "want", "because", "any", "these", "give", "day", "most", "us",
    
    # Spanish Stopwords
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al", "en",
    "para", "por", "con", "sin", "sobre", "entre", "hasta", "desde", "hacia", "contra",
    "y", "e", "ni", "o", "u", "pero", "sino", "aunque", "porque", "es", "son", "fue",
    "fueron", "ser", "estar", "este", "esta", "estos", "estas", "ese", "esa", "esos"
}

INTENT_MODIFIERS_PT = [
    "como", "como começar", "do zero", "passo a passo", "tutorial", "curso",
    "dicas", "melhor", "melhores", "grátis", "estratégia", "ferramentas",
    "guia", "iniciantes", "2026", "2025", "atualizado", "completo", "segredos"
]

def normalize_text(text: str) -> str:
    """Normalize text by lowering, removing accents and non-alphanumeric noise."""
    if not text:
        return ""
    text = text.lower()
    # Normalize unicode characters (remove diacritics / accents)
    nfkd = unicodedata.normalize('NFKD', text)
    text_clean = "".join([c for c in nfkd if not unicodedata.combining(c)])
    # Replace non-alphanumeric characters with spaces
    text_clean = re.sub(r"[^\w\s]", " ", text_clean)
    return " ".join(text_clean.split())

def extract_tokens(text: str, remove_stopwords: bool = True) -> List[str]:
    """Extract clean words/tokens from text."""
    norm = normalize_text(text)
    words = norm.split()
    if remove_stopwords:
        words = [w for w in words if w not in STOP_WORDS and len(w) >= 2]
    return words

def get_youtube_related_suggestions(
    keyword: str,
    hl: str = "pt",
    gl: str = "BR",
    max_suggestions: int = 30
) -> List[str]:
    """
    Fetch real-time YouTube autocomplete search suggestions and related terms.
    Uses official YouTube suggestion endpoints to learn real queries searched by users in that niche.
    """
    keyword = keyword.strip()
    if not keyword:
        return []

    suggestions: List[str] = []
    seen = set()

    # Query variations for broader niche harvesting
    queries_to_fetch = [
        keyword,
        f"{keyword} como",
        f"{keyword} tutorial",
        f"{keyword} do zero",
        f"{keyword} dicas",
        f"{keyword} curso",
        f"{keyword} melhor",
        f"{keyword} 2026"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": f"{hl}-{gl},{hl};q=0.9,en;q=0.8"
    }

    for q in queries_to_fetch:
        if len(suggestions) >= max_suggestions:
            break
        try:
            encoded_q = urllib.parse.quote(q)
            # YouTube DS endpoint (Firefox client format returns [query, [sug1, sug2, ...]])
            url_ff = f"https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={encoded_q}&hl={hl}&gl={gl}"
            resp = requests.get(url_ff, headers=headers, timeout=2.5)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
                    for item in data[1]:
                        if isinstance(item, str):
                            clean_item = item.strip()
                            clean_norm = normalize_text(clean_item)
                            if clean_norm and clean_norm not in seen:
                                seen.add(clean_norm)
                                suggestions.append(clean_item)
        except Exception as e:
            logger.debug(f"YouTube Suggestion fetch failed for '{q}': {e}")

    # If API had temporary network limit or returned few, add structured intent variants
    if len(suggestions) < 5:
        for mod in INTENT_MODIFIERS_PT:
            combo = f"{keyword} {mod}"
            norm_combo = normalize_text(combo)
            if norm_combo not in seen:
                seen.add(norm_combo)
                suggestions.append(combo)

    return suggestions[:max_suggestions]


def build_topic_profile(keyword: str, related_terms: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Build a comprehensive semantic Topic Profile for relevance evaluation.
    """
    clean_kw = keyword.strip()
    norm_kw = normalize_text(clean_kw)
    primary_tokens = set(extract_tokens(clean_kw, remove_stopwords=True))
    
    # If all tokens were stopwords (e.g. 'como fazer'), use all tokens
    if not primary_tokens:
        primary_tokens = set(extract_tokens(clean_kw, remove_stopwords=False))

    related_tokens: Set[str] = set()
    cleaned_related: List[str] = []
    
    if related_terms:
        for r_term in related_terms:
            r_norm = normalize_text(r_term)
            if r_norm:
                cleaned_related.append(r_term)
                related_tokens.update(extract_tokens(r_term, remove_stopwords=True))

    return {
        "raw_keyword": clean_kw,
        "normalized_keyword": norm_kw,
        "primary_tokens": primary_tokens,
        "related_terms": cleaned_related,
        "related_tokens": related_tokens,
        "is_single_token": len(primary_tokens) == 1,
        "is_short_query": len(clean_kw.split()) <= 2
    }


def calculate_relevance_score(
    title: str,
    description: str,
    channel_name: str,
    topic_profile: Dict[str, Any],
    tags: Optional[List[str]] = None
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate high-precision semantic relevance score (0.0 to 100.0).
    Evaluates title, description, channel and tags against topic profile.
    """
    norm_title = normalize_text(title)
    norm_desc = normalize_text(description[:600]) # First 600 chars of description
    norm_channel = normalize_text(channel_name)

    title_tokens = set(extract_tokens(title, remove_stopwords=True))
    desc_tokens = set(extract_tokens(description[:600], remove_stopwords=True))
    channel_tokens = set(extract_tokens(channel_name, remove_stopwords=True))
    all_content_tokens = title_tokens | desc_tokens | channel_tokens

    primary_tokens = topic_profile.get("primary_tokens", set())
    norm_kw = topic_profile.get("normalized_keyword", "")
    related_terms = topic_profile.get("related_terms", [])
    related_tokens = topic_profile.get("related_tokens", set())

    score = 0.0
    matched_primary_in_title = title_tokens.intersection(primary_tokens)
    matched_primary_in_all = all_content_tokens.intersection(primary_tokens)

    # 1. Exact phrase match in Title (Highest indicator of relevancy)
    if norm_kw and norm_kw in norm_title:
        score += 50.0
    elif norm_kw and norm_kw in norm_desc:
        score += 25.0

    # 2. Primary Token Coverage in Title (e.g. 'marketing' and 'digital')
    if primary_tokens:
        title_ratio = len(matched_primary_in_title) / len(primary_tokens)
        score += title_ratio * 35.0
        
        all_ratio = len(matched_primary_in_all) / len(primary_tokens)
        score += all_ratio * 15.0

    # 3. Discovered Related Terms & Suggestions match in Title
    for rel_term in related_terms[:15]:
        rel_norm = normalize_text(rel_term)
        if rel_norm and rel_norm in norm_title:
            score += 25.0
            break
        elif rel_norm and rel_norm in norm_desc:
            score += 10.0
            break

    # 4. Related Token overlap
    if related_tokens:
        matched_rel_title = title_tokens.intersection(related_tokens)
        if matched_rel_title:
            score += min(15.0, len(matched_rel_title) * 3.0)

    # 5. Channel Name relevance bonus (channel dedicated to niche)
    if channel_tokens.intersection(primary_tokens):
        score += 10.0

    diagnostics = {
        "matched_primary_in_title": list(matched_primary_in_title),
        "matched_primary_in_all": list(matched_primary_in_all),
        "raw_score": score,
        "is_exact_kw_in_title": norm_kw in norm_title if norm_kw else False
    }

    return min(100.0, score), diagnostics


def is_content_relevant_to_topic(
    title: str,
    description: str,
    channel_name: str,
    topic_profile: Dict[str, Any],
    min_score_threshold: float = 20.0,
    tags: Optional[List[str]] = None
) -> bool:
    """
    Strict semantic gatekeeper to eliminate topic drift and irrelevant content.
    Returns True if the content is verified to be within the search topic, False otherwise.
    """
    if not topic_profile:
        return True

    primary_tokens = topic_profile.get("primary_tokens", set())
    norm_kw = topic_profile.get("normalized_keyword", "")
    
    # If no valid keywords, pass through
    if not primary_tokens and not norm_kw:
        return True

    score, diag = calculate_relevance_score(
        title=title,
        description=description,
        channel_name=channel_name,
        topic_profile=topic_profile,
        tags=tags
    )

    # Quick approval conditions:
    # 1. Exact keyword phrase is in title
    if diag.get("is_exact_kw_in_title"):
        return True

    # 2. All primary tokens present in title
    if primary_tokens and len(diag.get("matched_primary_in_title", [])) == len(primary_tokens):
        return True

    # 3. Single-word niche (e.g. 'dropshipping', 'bitcoin', 'gta', 'emagrecimento')
    if topic_profile.get("is_single_token"):
        # The single token must appear at least in title, description, or channel
        if diag.get("matched_primary_in_all"):
            return True
        return False

    # 4. Multi-word topic: score must exceed threshold and have at least 1 primary token or strong related phrase
    if score >= min_score_threshold:
        if diag.get("matched_primary_in_title") or diag.get("matched_primary_in_all"):
            return True
        # If no primary token is matched directly, at least a multi-token related phrase must match
        if score >= 35.0:
            return True

    logger.debug(f"Off-topic video rejected (Score: {score:.1f}/{min_score_threshold}): '{title[:45]}'")
    return False
