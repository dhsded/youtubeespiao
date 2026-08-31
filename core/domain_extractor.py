"""
Domain Extractor and Recursive URL Unshortener.
Identifies URLs and Instagram handles in descriptions and pinned comments,
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

# Combine all infrastructure to exclude from candidate domains
ALL_EXCLUDED_DOMAINS = IGNORE_DOMAINS.union(SHORTENER_DOMAINS)

URL_REGEX = re.compile(
    r'(?:https?:\/\/)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:\/[^\s\)\"\'<>,;]*)*',
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
        """Find all URL patterns in a block of text."""
        if not text:
            return []
        
        matches = URL_REGEX.findall(text)
        cleaned_urls = []
        
        for match in matches:
            url = match.strip().rstrip(".,:;!?'\")]}")
            if not url:
                continue
            if not url.startswith("http://") and not url.startswith("https://"):
                if "@" in url:
                    continue
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
            domain = self.get_registered_domain(current_url)
            
            # If not a shortener or bridge, we might still check 1 hop
            try:
                resp = self.session.get(
                    current_url,
                    allow_redirects=True,
                    timeout=self.timeout,
                    headers={"Accept": "text/html,application/xhtml+xml"}
                )
                
                final_url = resp.url
                
                # Check for HTML Meta Refresh (e.g., <meta http-equiv="refresh" content="0;url=...">)
                if resp.status_code == 200 and "html" in resp.headers.get("Content-Type", ""):
                    soup = BeautifulSoup(resp.text[:4096], "html.parser")
                    meta_refresh = soup.find("meta", attrs={"http-equiv": re.compile(r"^refresh$", re.I)})
                    if meta_refresh and meta_refresh.get("content"):
                        content = meta_refresh["content"]
                        match = re.search(r'url=([^;]+)', content, re.I)
                        if match:
                            target = match.group(1).strip().strip("'\"")
                            if not target.startswith("http"):
                                target = urllib.parse.urljoin(final_url, target)
                            current_url = target
                            continue

                self._unshortened_cache[url] = final_url
                return final_url

            except Exception:
                break

        self._unshortened_cache[url] = current_url
        return current_url

    def process_text_for_domains(self, text: str, source_location: str = "Descrição") -> List[Dict[str, Any]]:
        """
        Extract valid target domains and Instagram accounts from text.
        """
        results = []
        seen_domains: Set[str] = set()

        # 1. Process Instagram Accounts
        ig_handles = self.instagram_validator.extract_handles_from_text(text)
        for handle in ig_handles:
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

        # 2. Process Web Domains
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
