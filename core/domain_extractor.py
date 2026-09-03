"""
Ultra-Robust Domain Extractor and Multi-Layer Recursive URL Unshortener.
Strictly identifies genuine CLICKABLE HYPERLINKS (http://, https://, www., or YouTube redirect links)
and Instagram accounts (@handles and profile links).
Discards plain text domain mentions and email addresses that are not clickable on YouTube.
Expands all layers of redirects/shortlinks/bridges hop-by-hop without losing offline target domains,
extracts destination links from bio hubs (Linktree, Beacons, etc.),
and rigorously filters out known infrastructure and social platforms.
"""

import re
import urllib.parse
import os
import logging
from typing import List, Dict, Set, Optional, Any
import requests
import tldextract
from bs4 import BeautifulSoup

from core.instagram_validator import InstagramValidator

logger = logging.getLogger(__name__)

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
    "bio.link", "allmylinks.com", "lnk.bio", "heylink.me", "taplink.cc",
    "instabio.cc", "link.bio"
}

# Bio Link Hubs that contain lists of creator destination links
BIO_HUB_DOMAINS = {
    "linktr.ee", "solo.to", "beacons.ai", "direct.me", "campsite.bio",
    "bio.link", "allmylinks.com", "lnk.bio", "heylink.me", "taplink.cc",
    "instabio.cc", "link.bio"
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

# Discard non-web extensions (e.g. filename mentions in text)
NON_WEB_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "svg", "webp", "mp4", "mp3", "mov", "avi",
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "zip", "rar", "7z",
    "exe", "dmg", "apk", "iso", "tar", "gz", "txt", "csv", "json", "xml",
    "css", "js", "ts", "py", "sh", "bat", "cmd", "env"
}

# Combine all infrastructure to exclude from candidate domains
ALL_EXCLUDED_DOMAINS = IGNORE_DOMAINS.union(SHORTENER_DOMAINS)

# Matches clickable URLs: must start with http://, https://, or www.
URL_CLICKABLE_PATTERN = re.compile(
    r'(?:https?:\/\/|www\.)[^\s<>\"\'`()\[\]{}]+',
    re.IGNORECASE
)

def _get_exclusion_file_path() -> str:
    appdata = os.getenv("APPDATA") or os.path.expanduser("~")
    save_dir = os.path.join(appdata, "YouTube Espiao")
    os.makedirs(save_dir, exist_ok=True)
    return os.path.join(save_dir, "custom_exclusions.txt")

def _clean_exclusion_target(target: str) -> str:
    """Clean domain or Instagram handle string for exclusion."""
    if not target:
        return ""
    clean = target.strip().lower()
    clean = re.sub(r'^https?:\/\/', '', clean)
    clean = re.sub(r'^www\.', '', clean)
    clean = clean.replace("@", "").strip("/ \t\r\n.,;:'\"")
    # If it was an Instagram URL like instagram.com/handle/
    if clean.startswith("instagram.com/") or clean.startswith("instagr.am/"):
        parts = clean.split("/")
        clean = parts[1] if len(parts) > 1 else clean
    elif "/" in clean:
        # Strip URL path from web domain (e.g. site.com/pagina -> site.com)
        clean = clean.split("/", 1)[0].strip()
    clean = clean.strip("/ \t\r\n.,;:'\"")
    return clean

def parse_multiple_exclusion_targets(text_or_items: Any) -> List[str]:
    """Parse string (with commas, semicolons, newlines) or iterable into clean domain/handle targets."""
    results: List[str] = []
    if isinstance(text_or_items, str):
        parts = re.split(r'[\r\n,;]+', text_or_items)
        for p in parts:
            p_clean = _clean_exclusion_target(p)
            if p_clean and p_clean not in results:
                results.append(p_clean)
    elif hasattr(text_or_items, '__iter__'):
        for item in text_or_items:
            if isinstance(item, str):
                p_clean = _clean_exclusion_target(item)
                if p_clean and p_clean not in results:
                    results.append(p_clean)
    return results

def load_custom_exclusions():
    """Load persistent custom user exclusions into IGNORE_DOMAINS and ALL_EXCLUDED_DOMAINS."""
    path = _get_exclusion_file_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    dom = _clean_exclusion_target(line)
                    if dom:
                        IGNORE_DOMAINS.add(dom)
                        ALL_EXCLUDED_DOMAINS.add(dom)
        except Exception as e:
            logger.debug(f"Failed to read custom exclusions: {e}")

def add_to_exclusion_list(domain_or_domains: Any) -> bool:
    """Add one or more domains/Instagram handles to persistent exclusion list."""
    targets = parse_multiple_exclusion_targets(domain_or_domains)
    if not targets:
        return False
    
    for t in targets:
        IGNORE_DOMAINS.add(t)
        ALL_EXCLUDED_DOMAINS.add(t)
    
    path = _get_exclusion_file_path()
    try:
        current_custom = set()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                current_custom = {_clean_exclusion_target(l) for l in f if l.strip()}
        current_custom.update(targets)
        with open(path, "w", encoding="utf-8") as f:
            for item in sorted(current_custom):
                if item:
                    f.write(f"{item}\n")
        return True
    except Exception as e:
        logger.error(f"Failed to persist exclusion: {e}")
        return False

def remove_from_exclusion_list(domain_or_domains: Any) -> bool:
    """Remove one or more domains/Instagram handles from persistent custom exclusion list."""
    targets = parse_multiple_exclusion_targets(domain_or_domains)
    if not targets:
        return False
        
    for t in targets:
        IGNORE_DOMAINS.discard(t)
        ALL_EXCLUDED_DOMAINS.discard(t)
        
    path = _get_exclusion_file_path()
    try:
        current_custom = set()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                current_custom = {_clean_exclusion_target(l) for l in f if l.strip()}
        current_custom.difference_update(targets)
        with open(path, "w", encoding="utf-8") as f:
            for item in sorted(current_custom):
                if item:
                    f.write(f"{item}\n")
        return True
    except Exception as e:
        logger.error(f"Failed to persist exclusion removal: {e}")
        return False

def get_custom_exclusions() -> List[str]:
    """Return sorted list of custom user exclusions from disk."""
    path = _get_exclusion_file_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return sorted(list({_clean_exclusion_target(l) for l in f if _clean_exclusion_target(l)}))
        except Exception:
            return []
    return []

# Initialize custom exclusions on module load
load_custom_exclusions()


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

    @staticmethod
    def _clean_trailing(s: str) -> str:
        """Strip trailing punctuation, brackets, and quotes from candidate URL strings."""
        return re.sub(r'[\s\"\'\`\(\)\[\]\{\}\<\>\,\;\!\?\:\*\|\#\\]+$', '', s).strip(' \t\n\r"\'`()[]{}<>,;')

    @staticmethod
    def _unwrap_redirect_query(raw_url: str) -> List[str]:
        """
        Extract destination URLs embedded inside redirect wrappers like:
        - https://www.youtube.com/redirect?q=https%3A%2F%2Fexemplo.com%2F...
        - https://www.google.com/url?q=http://exemplo.com&...
        - https://l.instagram.com/?u=https%3A%2F%2Fexemplo.com
        - https://l.facebook.com/l.php?u=https%3A%2F%2Fexemplo.com
        """
        results = [raw_url]
        try:
            parsed = urllib.parse.urlparse(raw_url)
            if parsed.query:
                params = urllib.parse.parse_qs(parsed.query)
                for param_key in ('q', 'url', 'u', 'target', 'dest', 'link', 'r', 'redirect_to'):
                    if param_key in params:
                        for val in params[param_key]:
                            decoded = urllib.parse.unquote(val).strip()
                            if decoded.startswith(('http://', 'https://', 'www.')):
                                results.append(decoded)
                                # Recursively unwrap if nested
                                results.extend(DomainExtractor._unwrap_redirect_query(decoded))
        except Exception:
            pass
        return results

    def extract_urls(self, text: str) -> List[str]:
        """
        Extracts ONLY genuine clickable URLs (starting with http://, https://, or www.).
        Discards plain text mentions, non-clickable domains, and non-web file extensions.
        """
        if not text:
            return []

        matches = URL_CLICKABLE_PATTERN.findall(text)
        candidates: List[str] = []

        for m in matches:
            u = self._clean_trailing(m)
            if not u:
                continue

            # Reject if it's an email address (e.g. name@www.example.com)
            if "@" in u and not u.startswith(("http://", "https://")):
                continue

            # Reject non-web file mentions (e.g. www.arquivo.pdf)
            parts = u.split('?')[0].split('/')
            first_part = parts[0]
            token_ext = first_part.split('.')[-1].lower() if '.' in first_part else ''
            if len(parts) == 1 and token_ext in NON_WEB_EXTENSIONS:
                continue

            full_u = u if u.startswith(('http://', 'https://')) else f"https://{u}"
            candidates.extend(self._unwrap_redirect_query(full_u))

        # Validate each candidate using PSL (tldextract) & deduplicate
        valid_urls = []
        for cand in candidates:
            ext = tldextract.extract(cand)
            if ext.domain and ext.suffix:
                if ext.suffix.lower() not in NON_WEB_EXTENSIONS:
                    valid_urls.append(cand)

        return list(dict.fromkeys(valid_urls))

    def get_registered_domain(self, url: str) -> Optional[str]:
        """Extract root domain (e.g. 'sub.example.com.br' -> 'example.com.br')."""
        try:
            ext = tldextract.extract(url)
            if ext.domain and ext.suffix:
                return f"{ext.domain}.{ext.suffix}".lower()
        except Exception:
            pass
        return None

    def unshorten_url(self, url: str, max_hops: int = 6) -> str:
        """
        Step-by-step redirect resolver.
        Reads HTTP 'Location' headers with allow_redirects=False.
        Guarantees that if the target domain server is dead/offline or NXDOMAIN,
        we STILL return the target domain instead of crashing or discarding it!
        """
        if url in self._unshortened_cache:
            return self._unshortened_cache[url]

        current_url = url
        hops = 0

        while hops < max_hops:
            hops += 1
            root = self.get_registered_domain(current_url)
            if not root:
                break

            # If not a known shortener or redirect bridge, attempt lightweight HEAD probe
            if root not in SHORTENER_DOMAINS:
                try:
                    resp = self.session.head(current_url, allow_redirects=False, timeout=self.timeout)
                    if resp.status_code in (301, 302, 303, 307, 308) and "Location" in resp.headers:
                        loc = resp.headers["Location"].strip()
                        new_url = urllib.parse.urljoin(current_url, loc)
                        if new_url != current_url:
                            current_url = new_url
                            continue
                except Exception:
                    pass
                break

            # If it IS a known shortener, step-by-step resolve with allow_redirects=False
            try:
                resp = self.session.get(current_url, allow_redirects=False, timeout=self.timeout, stream=True)
                if resp.status_code in (301, 302, 303, 307, 308) and "Location" in resp.headers:
                    loc = resp.headers["Location"].strip()
                    new_url = urllib.parse.urljoin(current_url, loc)
                    if new_url != current_url:
                        current_url = new_url
                        continue

                # If status 200, check HTML body for Meta refresh or JS redirect
                content_type = resp.headers.get("Content-Type", "")
                if "text/html" in content_type:
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

            except Exception as e:
                # If network error occurs during a shortener hop, break and keep the best current_url
                logger.debug(f"Redirect step error for {current_url}: {e}")
                break

        if len(self._unshortened_cache) >= 20000:
            for old_k in list(self._unshortened_cache.keys())[:2000]:
                self._unshortened_cache.pop(old_k, None)

        self._unshortened_cache[url] = current_url
        return current_url

    def extract_links_from_bio_hub(self, hub_url: str) -> List[str]:
        """
        Scrapes external target links from bio link hubs like linktr.ee, solo.to, beacons.ai, etc.
        """
        extracted_links = []
        try:
            resp = self.session.get(hub_url, timeout=3.0)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href'].strip()
                    if href.startswith(('http://', 'https://')):
                        root = self.get_registered_domain(href)
                        if root and root not in ALL_EXCLUDED_DOMAINS and root not in BIO_HUB_DOMAINS:
                            extracted_links.append(href)
        except Exception as e:
            logger.debug(f"Bio hub scrape error for {hub_url}: {e}")
        return extracted_links

    def process_text_for_domains(self, text: str, source_location: str = "Descrição") -> List[Dict[str, Any]]:
        """
        Extract valid target domains and Instagram accounts from text.
        Web domains: ONLY genuine clickable hyperlinks (http://, https://, www., or redirect links).
        Instagram: Handles (@handle and profile URLs) allowed.
        """
        results = []
        seen_domains: Set[str] = set()

        # 1. Process Instagram Accounts & Handles (Clickable links and explicit IG mentions)
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

        # 2. Process Clickable Web Domains (Hyperlinks only: http://, https://, www.)
        urls = self.extract_urls(text)

        # Strictly report links directly contained in the video.
        # Do not scrape third-party bio hubs (linktree, solo.to, etc.) to prevent injecting external phantom links.
        expanded_urls = list(urls)

        for raw_url in expanded_urls:
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
