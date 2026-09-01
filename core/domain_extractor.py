"""
Domain Extractor and Recursive URL Unshortener.
Identifies URLs and Instagram handles in descriptions and pinned comments,
strictly enforces clickable links (discards non-clickable plain text),
expands all layers of redirects/shortlinks/bridges, and filters out known infrastructure and social platforms.
"""

import re
import urllib.parse
from typing import List, Dict, Set, Optional, Any
import requests
import tldextract
from bs4 import BeautifulSoup

from core.instagram_validator import InstagramValidator

# Known Shorteners, Affiliate Tracking Bridges, and Link Aggregators that MUST be expanded and NEVER reported as expired domains
SHORTENER_DOMAINS = {
    # Classic Shorteners
    "bit.ly", "tinyurl.com", "cutt.ly", "is.gd", "t.co", "rebrand.ly",
    "buff.ly", "ow.ly", "shorturl.at", "bl.ink", "tiny.cc", "goo.gl",
    "clck.ru", "trib.al", "snip.ly", "bitly.com", "ift.tt", "cutt.us",
    "v.gd", "rb.gy", "s.id", "qrs.ly", "hyperurl.co", "smarturl.it",
    "geni.us", "lnk.to", "fanlink.to", "hypeddit.com", "toneden.io",
    
    # Affiliate Bridges & Tracking Networks
    "pxf.io", "partnerlinks.io", "shareasale.com", "impact.com", "cj.com",
    "awin1.com", "clickbank.net", "rakuten.com", "amzn.to", "amzn.eu",
    "hotm.art", "hotmart.com", "monetizze.com.br", "eduzz.com", "kiwify.com.br",
    "perfectpay.com.br", "braip.com", "pepper.com.br", "doppus.com",
    
    # Bio Link Hubs
    "linktr.ee", "solo.to", "beacons.ai", "direct.me", "campsite.bio",
    "bio.link", "allmylinks.com", "lnk.bio", "heylink.me"
}

# Whitelist / Known Mega Platforms to ignore from domain registration list
IGNORE_DOMAINS = {
    # Search & Tech Giants
    "google.com", "google.com.br", "youtube.com", "youtu.be", "gmail.com",
    "microsoft.com", "apple.com", "github.com", "gitlab.com", "wikipedia.org",
    "yahoo.com", "bing.com", "cloudflare.com", "wordpress.org", "w3.org",
    
    # Social & Messaging (Instagram handled separately)
    "facebook.com", "fb.me", "instagram.com", "instagr.am", "twitter.com",
    "x.com", "tiktok.com", "whatsapp.com", "wa.me", "telegram.org", "t.me",
    "telegram.me", "discord.gg", "discord.com", "linkedin.com", "pinterest.com",
    "reddit.com", "threads.net", "snapchat.com", "vk.com", "twitch.tv",
    "medium.com", "tumblr.com", "patreon.com",
    
    # Media & Stores
    "spotify.com", "open.spotify.com", "soundcloud.com", "deezer.com",
    "amazon.com", "amazon.com.br", "aliexpress.com", "shopee.com.br",
    "mercadolivre.com.br", "magazineluiza.com.br", "play.google.com", "apps.apple.com",
    
    # Forms & Docs
    "forms.gle", "docs.google.com", "drive.google.com", "notion.so", "canva.com"
}

import os
import logging

logger = logging.getLogger(__name__)

# Combine all infrastructure to exclude from candidate domains
ALL_EXCLUDED_DOMAINS = IGNORE_DOMAINS.union(SHORTENER_DOMAINS)

def _get_exclusion_file_path() -> str:
    appdata = os.getenv("APPDATA") or os.path.expanduser("~")
    save_dir = os.path.join(appdata, "YouTube Espiao")
    os.makedirs(save_dir, exist_ok=True)
    return os.path.join(save_dir, "custom_exclusions.txt")

def load_custom_exclusions():
    """Load persistent custom user exclusions into IGNORE_DOMAINS."""
    path = _get_exclusion_file_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    dom = line.strip().lower().replace("@", "")
                    if dom:
                        IGNORE_DOMAINS.add(dom)
                        ALL_EXCLUDED_DOMAINS.add(dom)
        except Exception as e:
            logger.debug(f"Failed to read custom exclusions: {e}")

def add_to_exclusion_list(domain: str) -> bool:
    """Add a domain or Instagram handle to persistent exclusion list."""
    clean = domain.strip().lower().replace("@", "").replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
    if not clean:
        return False
    
    IGNORE_DOMAINS.add(clean)
    ALL_EXCLUDED_DOMAINS.add(clean)
    
    path = _get_exclusion_file_path()
    try:
        current_custom = set()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                current_custom = {l.strip().lower().replace("@", "") for l in f if l.strip()}
        current_custom.add(clean)
        with open(path, "w", encoding="utf-8") as f:
            for item in sorted(current_custom):
                f.write(f"{item}\n")
        return True
    except Exception as e:
        logger.error(f"Failed to persist exclusion: {e}")
        return False

# Initialize custom exclusions on module load
load_custom_exclusions()

# Discard non-web extensions (e.g. filename mentions in text)
NON_WEB_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "svg", "webp", "mp4", "mp3", "mov", "avi",
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "zip", "rar", "7z",
    "exe", "dmg", "apk", "iso", "tar", "gz", "txt", "csv", "json", "xml"
}

# Match explicit clickable links in text (http://, https://, www., or structured domain links with subpaths)
URL_CLICKABLE_REGEX = re.compile(
    r'(?:https?:\/\/|www\.)[a-zA-Z0-9][-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{2,12}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
    r'|'
    r'\b[a-zA-Z0-9][-a-zA-Z0-9]{1,62}\.[a-zA-Z]{2,12}\/(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]+)',
    re.IGNORECASE
)

class DomainExtractor:
    def __init__(self, request_timeout: int = 4):
        self.timeout = request_timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
        })
        self._unshortened_cache: Dict[str, str] = {}
        self.instagram_validator = InstagramValidator(timeout=request_timeout)

    def extract_urls(self, text: str) -> List[str]:
        """
        Find all genuine CLICKABLE URL patterns in a block of text.
        Discards plain text mentions, email addresses, and non-clickable strings.
        """
        if not text:
            return []
        
        matches = URL_CLICKABLE_REGEX.findall(text)
        cleaned_urls = []
        
        for match in matches:
            url = match.strip().rstrip(".,:;!?'\")]}")
            if not url:
                continue
            
            # Reject email addresses
            if "@" in url and not url.startswith("http"):
                continue
            
            # Reject non-web file mentions (e.g. 'arquivo.pdf')
            parts = url.split("?")[0].split("/")
            last_token = parts[0].split(".")[-1].lower() if parts else ""
            if len(parts) == 1 and last_token in NON_WEB_EXTENSIONS:
                continue

            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
                
            cleaned_urls.append(url)
            
        return list(dict.fromkeys(cleaned_urls))

    def get_registered_domain(self, url: str) -> Optional[str]:
        """Extract root domain (e.g. 'sub.example.com.br' -> 'example.com.br')."""
        try:
            ext = tldextract.extract(url)
            if ext.domain and ext.suffix:
                return f"{ext.domain}.{ext.suffix}".lower()
        except Exception:
            pass
        return None

    def unshorten_url(self, url: str, max_hops: int = 5) -> str:
        """
        Recursively resolve redirects, meta refresh, and JS redirects to reach final landing domain.
        """
        if url in self._unshortened_cache:
            return self._unshortened_cache[url]

        current_url = url
        hops = 0

        while hops < max_hops:
            hops += 1
            try:
                # First check TLD of current URL - if already a non-shortener destination, we can return or probe lightly
                root = self.get_registered_domain(current_url)
                if not root:
                    break

                # If current root is NOT a known shortener, perform single HEAD request
                if root not in SHORTENER_DOMAINS:
                    try:
                        resp = self.session.head(current_url, allow_redirects=True, timeout=self.timeout)
                        if resp.url and resp.url != current_url:
                            current_url = resp.url
                    except Exception:
                        pass
                    break

                # For known shorteners, perform full GET to follow HTML meta refresh / JS redirects
                resp = self.session.get(current_url, allow_redirects=True, timeout=self.timeout, stream=True)
                if resp.url and resp.url != current_url:
                    current_url = resp.url

                # Check HTML body for client-side redirects (Meta refresh / window.location)
                content_type = resp.headers.get("Content-Type", "")
                if "text/html" in content_type:
                    # Read only first 4KB to save bandwidth
                    chunk = resp.raw.read(4096).decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(chunk, 'html.parser')
                    
                    # 1. Meta refresh
                    meta_refresh = soup.find('meta', attrs={'http-equiv': re.compile(r'refresh', re.I)})
                    if meta_refresh and meta_refresh.get('content'):
                        content = meta_refresh['content']
                        if 'url=' in content.lower():
                            next_url = content.split('url=')[-1].split(';')[0].strip(' "\'')
                            if next_url.startswith("http"):
                                current_url = next_url
                                continue

                    # 2. JavaScript location.href or location.replace
                    js_match = re.search(r'(?:window\.location(?:\.href|\.replace)?\s*=\s*[\'"]|location\.replace\([\'"])(https?://[^\'"]+)', chunk)
                    if js_match:
                        current_url = js_match.group(1)
                        continue

                break

            except Exception:
                break

        self._unshortened_cache[url] = current_url
        return current_url

    def process_text_for_domains(self, text: str, source_location: str = "Descrição") -> List[Dict[str, Any]]:
        """
        Extract valid target domains and Instagram accounts from text.
        Guarantees that only clickable web links and active handles are retained.
        """
        results = []
        seen_domains: Set[str] = set()

        # 1. Process Instagram Accounts
        ig_handles = self.instagram_validator.extract_handles_from_text(text)
        for handle in ig_handles:
            h_clean = handle.lower().strip().replace("@", "")
            if h_clean in IGNORE_DOMAINS or f"instagram.com/{h_clean}" in IGNORE_DOMAINS or f"@{h_clean}" in IGNORE_DOMAINS:
                continue

            ig_res = self.instagram_validator.validate_handle(handle)
            results.append({
                "raw_url": f"https://instagram.com/{handle}",
                "final_url": ig_res["profile_url"],
                "root_domain": f"instagram.com/{handle}",
                "display_name": f"📸 @{handle}",
                "source_location": source_location,
                "is_instagram": True,
                "status": ig_res["status"],
                "badge_icon": ig_res["badge_icon"],
                "status_color": ig_res["status_color"],
                "details": ig_res["details"],
                "buy_link": ig_res["claim_url"],
                "registrar_name": "Instagram"
            })

        # 2. Process Clickable Web Domains
        urls = self.extract_urls(text)

        for raw_url in urls:
            final_url = self.unshorten_url(raw_url)
            root_domain = self.get_registered_domain(final_url)

            if not root_domain:
                continue

            # Must NOT be in the excluded/shortener/platform set
            if root_domain in ALL_EXCLUDED_DOMAINS or root_domain in IGNORE_DOMAINS:
                continue

            # Must NOT be a known shortener domain
            if root_domain in SHORTENER_DOMAINS:
                continue

            if root_domain in seen_domains:
                continue

            seen_domains.add(root_domain)
            results.append({
                "raw_url": raw_url,
                "final_url": final_url,
                "root_domain": root_domain,
                "display_name": root_domain,
                "source_location": source_location,
                "is_instagram": False
            })

        return results
