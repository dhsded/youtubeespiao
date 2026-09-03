"""
Instagram Profile and Handle Validator.
Detects expired/deleted or available Instagram accounts from video descriptions and comments.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set
import requests

logger = logging.getLogger(__name__)

# Reserved Instagram paths and generic handles to ignore
RESERVED_INSTAGRAM_HANDLES = {
    "explore", "reels", "stories", "accounts", "direct", "legal",
    "about", "developer", "help", "p", "tv", "reel", "channel",
    "instagram", "privacy", "terms", "terms_of_service", "emails",
    "download", "press", "about_us", "settings", "support", "creators",
    "business", "guidelines", "safety", "shopping", "home"
}

# Regex to capture genuine CLICKABLE Instagram URLs on YouTube (must start with https://, http://, or www.)
IG_CLICKABLE_URL_REGEX = re.compile(
    r'(?:https?:\/\/|www\.)(?:instagram\.com|instagr\.am)\/([a-zA-Z0-9_\.]{2,30})',
    re.IGNORECASE
)

# Regex to capture explicit Instagram handle mentions (e.g. "instagram: @handle", "insta: @handle", "ig @handle")
# Strictly prevents false positive mentions from Twitter, Telegram, Discord, editors, or credits.
IG_EXPLICIT_MENTION_REGEX = re.compile(
    r'(?:^|[\s\(\[\{\,\;:])(?:instagram|insta|ig)(?:\s+oficial|\s+ofc)?\s*[:\-]?\s*@([a-zA-Z0-9_\.]{2,30})',
    re.IGNORECASE
)

# Backward-compatibility alias
IG_URL_REGEX = IG_CLICKABLE_URL_REGEX

class InstagramValidator:
    def __init__(self, timeout: float = 4.0):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        })
        self._cache: Dict[str, Dict[str, Any]] = {}

    def extract_handles_from_text(self, text: str) -> List[str]:
        """
        Extract valid Instagram handles from text.
        Captures genuine clickable Instagram URLs (https://instagram.com/...) and explicit Instagram mentions (instagram: @handle).
        Strictly prevents false positive non-clickable plain-text mentions from Twitter, Telegram, editors, or credits.
        """
        if not text:
            return []
        
        matches = IG_CLICKABLE_URL_REGEX.findall(text)
        matches.extend(IG_EXPLICIT_MENTION_REGEX.findall(text))
            
        cleaned_handles = []
        for handle in matches:
            h = handle.strip().strip("/").rstrip(".,;:!?)\"'").lower()
            if not h or len(h) < 2 or h in RESERVED_INSTAGRAM_HANDLES:
                continue
            if h not in cleaned_handles:
                cleaned_handles.append(h)
                
        return cleaned_handles

    def validate_handle(self, username: str) -> Dict[str, Any]:
        """
        Check if an Instagram handle is:
        - 🟢 Disponível / Deletado (Account deleted, 404, or free to claim)
        - 🔴 Ativo (Active profile)
        """
        username = username.strip().lower()
        if username in self._cache:
            return self._cache[username]

        profile_url = f"https://www.instagram.com/{username}/"
        claim_url = f"https://www.instagram.com/{username}/"

        try:
            resp = self.session.get(
                profile_url,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # Instagram returns 404 for nonexistent/deleted profiles
            if resp.status_code == 404:
                result = {
                    "username": username,
                    "profile_url": profile_url,
                    "claim_url": claim_url,
                    "is_available": True,
                    "status": "Disponível",
                    "badge_icon": "🟢",
                    "status_color": "#10B981",
                    "details": "Conta de Instagram Deletada / Disponível para Criar!",
                    "type": "instagram"
                }
                self._cache[username] = result
                return result

            page_text = resp.text.lower()

            # Known Instagram "Page Not Found" strings in multiple languages
            not_found_indicators = [
                "esta página não está disponível",
                "sorry, this page isn't available",
                "the link you followed may be broken",
                "o link que você acessou pode não estar funcionando",
                "esta página não está disponível",
                "página no disponible"
            ]

            is_deleted = any(ind in page_text for ind in not_found_indicators)

            if is_deleted or resp.status_code == 404:
                result = {
                    "username": username,
                    "profile_url": profile_url,
                    "claim_url": claim_url,
                    "is_available": True,
                    "status": "Disponível",
                    "badge_icon": "🟢",
                    "status_color": "#10B981",
                    "details": "Conta de Instagram Deletada / Disponível para Criar!",
                    "type": "instagram"
                }
            else:
                result = {
                    "username": username,
                    "profile_url": profile_url,
                    "claim_url": claim_url,
                    "is_available": False,
                    "status": "Ativo",
                    "badge_icon": "🔴",
                    "status_color": "#EF4444",
                    "details": "Perfil do Instagram Ativo",
                    "type": "instagram"
                }

        except Exception as e:
            logger.debug(f"Instagram check error for @{username}: {e}")
            result = {
                "username": username,
                "profile_url": profile_url,
                "claim_url": claim_url,
                "is_available": False,
                "status": "Inativo",
                "badge_icon": "🟡",
                "status_color": "#F59E0B",
                "details": f"Instabilidade ao verificar conta IG: {e}",
                "type": "instagram"
            }

        # Trademark risk
        from core.trademark_validator import analyze_trademark_risk
        result["trademark_risk"] = analyze_trademark_risk(username)

        if len(self._cache) >= 20000:
            for old_k in list(self._cache.keys())[:2000]:
                self._cache.pop(old_k, None)

        self._cache[username] = result
        return result
