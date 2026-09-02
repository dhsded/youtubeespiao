"""
High-Resilience On-Demand VPH (Views Per Hour) Service & Multi-Source Ingestion Engine.
Operates without YouTube Data API keys using a cascade fallback architecture:
1. InnerTube API (Direct, fast, mobile/web client emulation)
2. Invidious Public Proxy Pool (Rotating external IP shield)
3. Minimalist HTML / Embed Fallback (Regex-based exact integer extraction)

Features:
- Local Throttling Cache (15-minute anti-ban / performance protection)
- Lazy Anchoring VPH Engine (Cold start, >=1h delta, 15-60m proportional delta, negative audit detection)
- Automated Traffic Classification ('viral_spike' | 'active' | 'evergreen' | 'dormant')
- Strictly conforms to the VideoVPHResponse typed contract
"""

import os
import re
import json
import time
import logging
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple, List, Literal, TypedDict
import requests

logger = logging.getLogger(__name__)

# Type definition conforming strictly to the requested return contract
class VideoVPHResponse(TypedDict):
    videoId: str
    exactViews: int
    publishedAt: str
    vph: float
    trafficStatus: Literal['viral_spike', 'active', 'evergreen', 'dormant']
    confidence: Literal['high', 'medium', 'lifetime_fallback']
    providerUsed: Literal['innertube', 'invidious_proxy', 'embed_fallback', 'local_cache']
    auditDetected: bool
    deltaHours: float
    calculatedAt: str

# Rotating pool of public Invidious instances for Level 2 IP shielding
INVIDIOUS_INSTANCES_POOL: List[str] = [
    "https://invidious.nerdvpn.de",
    "https://invidious.privacyredirect.com",
    "https://inv.tux.pizza",
    "https://yewtu.be",
    "https://invidious.no-logs.com",
    "https://iv.nboeck.de",
    "https://invidious.perennialte.ch",
    "https://invidious.einfachzocken.eu",
    "https://invidious.mutahar.rocks",
    "https://inv.zzls.xyz"
]

def _get_vph_cache_filepath() -> str:
    appdata = os.getenv("APPDATA") or os.path.expanduser("~")
    save_dir = os.path.join(appdata, "YouTube Espiao")
    os.makedirs(save_dir, exist_ok=True)
    return os.path.join(save_dir, "vph_anchors_cache.json")


class MultiSourceVideoFetcher:
    """
    Resilient Multi-Source Fetcher for exact YouTube video view counts and publication dates.
    Operates without API keys using a 3-tier cascade fallback.
    """

    def __init__(self, request_timeout: float = 3.5):
        self.timeout = request_timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
        })
        self._invidious_idx = 0

    def fetch_from_innertube(self, video_id: str) -> Optional[Tuple[int, str]]:
        """
        Level 1: YouTube InnerTube API (Direct, Fast, No API Key).
        Emulates YouTube Client to retrieve exact unrounded viewCount.
        """
        url = "https://www.youtube.com/youtubei/v1/player?prettyPrint=false"
        
        # Primary attempt: Web client (high reliability for exact integer viewCount)
        payload_web = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": "2.20240410.01.00",
                    "hl": "pt",
                    "gl": "BR"
                }
            },
            "videoId": video_id
        }
        headers = {
            "Content-Type": "application/json",
            "Origin": "https://www.youtube.com",
            "X-YouTube-Client-Name": "1",
            "X-YouTube-Client-Version": "2.20240410.01.00"
        }

        try:
            resp = self.session.post(url, json=payload_web, headers=headers, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                vd = data.get("videoDetails", {})
                vc_raw = vd.get("viewCount")
                if vc_raw is not None:
                    exact_views = int(vc_raw)
                    mf = data.get("microformat", {}).get("playerMicroformatRenderer", {})
                    pub_date = mf.get("publishDate") or mf.get("uploadDate") or vd.get("publishDate") or ""
                    return exact_views, str(pub_date)
        except Exception as e:
            logger.debug(f"InnerTube Level 1 (WEB) exception for {video_id}: {e}")

        # Secondary attempt: Android client context
        payload_android = {
            "context": {
                "client": {
                    "clientName": "ANDROID",
                    "clientVersion": "19.09.37",
                    "androidSdkVersion": 30,
                    "osName": "Android",
                    "osVersion": "11",
                    "hl": "pt",
                    "gl": "BR"
                }
            },
            "videoId": video_id
        }
        headers_android = {
            "Content-Type": "application/json",
            "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11; pt_BR) gzip"
        }

        try:
            resp_and = self.session.post(url, json=payload_android, headers=headers_android, timeout=self.timeout)
            if resp_and.status_code == 200:
                data = resp_and.json()
                vd = data.get("videoDetails", {})
                vc_raw = vd.get("viewCount")
                if vc_raw is not None:
                    exact_views = int(vc_raw)
                    mf = data.get("microformat", {}).get("playerMicroformatRenderer", {})
                    pub_date = mf.get("publishDate") or mf.get("uploadDate") or vd.get("publishDate") or ""
                    return exact_views, str(pub_date)
        except Exception as e:
            logger.debug(f"InnerTube Level 1 (ANDROID) exception for {video_id}: {e}")

        return None

    def fetch_from_invidious_proxy(self, video_id: str) -> Optional[Tuple[int, str]]:
        """
        Level 2: Rotating Invidious Public Proxy Pool (External IP Shield).
        Requests to YouTube are executed by third-party instances, shielding our IP.
        """
        pool_len = len(INVIDIOUS_INSTANCES_POOL)
        for attempt in range(pool_len):
            idx = (self._invidious_idx + attempt) % pool_len
            instance_url = INVIDIOUS_INSTANCES_POOL[idx]
            try:
                endpoint = f"{instance_url}/api/v1/videos/{video_id}"
                resp = self.session.get(endpoint, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    vc_raw = data.get("viewCount") or data.get("views")
                    if vc_raw is not None:
                        self._invidious_idx = (idx + 1) % pool_len
                        exact_views = int(vc_raw)
                        pub_date = data.get("publishedText") or data.get("uploadDate") or str(data.get("published", ""))
                        return exact_views, str(pub_date)
            except Exception as e:
                logger.debug(f"Invidious Level 2 instance {instance_url} failed: {e}")
                continue

        return None

    def fetch_from_embed_fallback(self, video_id: str) -> Optional[Tuple[int, str]]:
        """
        Level 3: Minimalist Embed / Watch HTML Fallback.
        Fetches HTML directly and extracts exact viewCount via Regex.
        """
        # 1. Watch page initial data
        try:
            watch_url = f"https://www.youtube.com/watch?v={video_id}"
            resp = self.session.get(watch_url, timeout=self.timeout)
            if resp.status_code == 200:
                html = resp.text
                vc_matches = re.findall(r'"viewCount"\s*:\s*"(\d+)"', html)
                if vc_matches:
                    exact_views = int(vc_matches[0])
                    pub_matches = re.findall(r'"publishDate"\s*:\s*"([^"]+)"', html) or re.findall(r'"uploadDate"\s*:\s*"([^"]+)"', html)
                    pub_date = pub_matches[0] if pub_matches else ""
                    return exact_views, str(pub_date)
        except Exception as e:
            logger.debug(f"Level 3 Watch fallback exception for {video_id}: {e}")

        # 2. Embed page fallback
        try:
            embed_url = f"https://www.youtube.com/embed/{video_id}"
            resp_e = self.session.get(embed_url, timeout=self.timeout)
            if resp_e.status_code == 200:
                html_e = resp_e.text
                vc_matches = re.findall(r'"viewCount"\s*:\s*"(\d+)"', html_e) or re.findall(r'\\\"viewCount\\\"\s*:\s*\\\"(\d+)\\\"', html_e)
                if vc_matches:
                    exact_views = int(vc_matches[0])
                    return exact_views, ""
        except Exception as e:
            logger.debug(f"Level 3 Embed fallback exception for {video_id}: {e}")

        return None

    def fetch_exact_video_details(self, video_id: str) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        """
        Cascading multi-source fetch:
        Returns: (exact_views, published_at, provider_used)
        """
        if not video_id:
            return None, None, None

        # Level 1: InnerTube
        res_l1 = self.fetch_from_innertube(video_id)
        if res_l1 is not None:
            return res_l1[0], res_l1[1], "innertube"

        # Level 2: Invidious Proxy Pool
        res_l2 = self.fetch_from_invidious_proxy(video_id)
        if res_l2 is not None:
            return res_l2[0], res_l2[1], "invidious_proxy"

        # Level 3: Embed Fallback
        res_l3 = self.fetch_from_embed_fallback(video_id)
        if res_l3 is not None:
            return res_l3[0], res_l3[1], "embed_fallback"

        return None, None, None


class VPHService:
    """
    On-Demand VPH Service with 15-Minute Local Throttling and Lazy Anchoring Engine.
    """

    def __init__(self, cache_ttl_seconds: int = 900):
        self.cache_ttl = cache_ttl_seconds # 15 minutes local cache protection
        self.fetcher = MultiSourceVideoFetcher()
        self.cache_file = _get_vph_cache_filepath()
        # Memory storage: video_id -> { "anchor_ts": float, "anchor_views": int, "last_vph": float, "published_at": str, "last_fetch_ts": float, "last_response": dict }
        self._anchors_db: Dict[str, Dict[str, Any]] = {}
        self._load_cache()

    def _load_cache(self):
        """Load persistent anchor database from disk."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self._anchors_db = json.load(f)
            except Exception as e:
                logger.debug(f"Failed to load VPH cache: {e}")
                self._anchors_db = {}

    def _save_cache(self):
        """Atomically persist anchor database to disk."""
        try:
            temp_path = f"{self.cache_file}.tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self._anchors_db, f, indent=2, ensure_ascii=False)
            if os.path.exists(temp_path):
                os.replace(temp_path, self.cache_file)
        except Exception as e:
            logger.debug(f"Failed to save VPH cache: {e}")

    @staticmethod
    def parse_published_datetime(pub_str: str) -> Optional[datetime]:
        """Parse various ISO and date representations into UTC datetime."""
        if not pub_str:
            return None
        clean = pub_str.strip().replace("Z", "+00:00")
        for fmt in (
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y"
        ):
            try:
                dt = datetime.strptime(clean[:19], fmt[:len(clean[:19])])
                if not dt.tzinfo:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                continue
        return None

    @staticmethod
    def classify_traffic(vph: float, published_dt: Optional[datetime], now_dt: Optional[datetime] = None) -> Literal['viral_spike', 'active', 'evergreen', 'dormant']:
        """
        Traffic Status Rules:
        - 'viral_spike': VPH >= 500
        - 'active': 20 <= VPH < 500
        - 'evergreen': 2 <= VPH < 20 for videos published > 6 months (180 days) ago
        - 'dormant': VPH < 2 (or < 20 on videos <= 180 days old)
        """
        if vph >= 500.0:
            return "viral_spike"
        elif vph >= 20.0:
            return "active"
        
        now = now_dt or datetime.now(timezone.utc)
        if published_dt:
            age_days = (now - published_dt).total_seconds() / 86400.0
            if age_days >= 180.0 and vph >= 2.0:
                return "evergreen"
        
        return "dormant"

    def get_on_demand_vph(
        self,
        video_id: str,
        force_refresh: bool = False,
        fallback_views: Optional[int] = None,
        fallback_published: Optional[str] = None
    ) -> VideoVPHResponse:
        """
        Calculate and return on-demand VPH for a requested video.
        
        Steps:
        1. Check local 15-min throttle cache.
        2. Ingest exact data via MultiSourceVideoFetcher cascade.
        3. Apply Lazy Anchoring algorithm (Cold start, >=1h delta, 15-60m proportional delta, negative audit clamp).
        4. Classify traffic vitality.
        5. Return VideoVPHResponse contract object.
        """
        now = datetime.now(timezone.utc)
        now_ts = now.timestamp()
        now_iso = now.isoformat()

        # Step 1: Local Throttling Check (15-Minute Cache Protection)
        record = self._anchors_db.get(video_id)
        if not force_refresh and record and "last_response" in record:
            last_fetch_ts = record.get("last_fetch_ts", 0.0)
            if (now_ts - last_fetch_ts) < self.cache_ttl:
                cached_resp: VideoVPHResponse = dict(record["last_response"])
                cached_resp["providerUsed"] = "local_cache"
                return cached_resp

        # Step 2: Multi-Source Ingestion
        exact_views, pub_date, provider_used = self.fetcher.fetch_exact_video_details(video_id)

        # Fallback to provided metadata if live network fetch fails
        if exact_views is None:
            if fallback_views is not None:
                exact_views = int(fallback_views)
                pub_date = fallback_published or (record.get("published_at") if record else "")
                provider_used = "embed_fallback"
            elif record and record.get("anchor_views") is not None:
                exact_views = int(record["anchor_views"])
                pub_date = record.get("published_at", "")
                provider_used = "local_cache"
            else:
                exact_views = 0
                pub_date = fallback_published or ""
                provider_used = "embed_fallback"

        pub_dt = self.parse_published_datetime(pub_date)
        pub_iso = pub_dt.isoformat() if pub_dt else (pub_date or now_iso)

        # Step 3: Lazy Anchoring Engine
        audit_detected = False

        if not record or "anchor_ts" not in record:
            # Scenario A: Cold Start (First query for this video)
            hours_since_pub = 1.0
            if pub_dt:
                diff_seconds = (now - pub_dt).total_seconds()
                hours_since_pub = max(1.0, diff_seconds / 3600.0)
            
            vph_lifetime = float(exact_views) / hours_since_pub
            vph_val = round(vph_lifetime, 2)
            confidence: Literal['high', 'medium', 'lifetime_fallback'] = "lifetime_fallback"
            delta_hours = round(hours_since_pub, 2)

            # Store anchor
            self._anchors_db[video_id] = {
                "anchor_ts": now_ts,
                "anchor_views": exact_views,
                "last_vph": vph_val,
                "published_at": pub_iso,
                "last_fetch_ts": now_ts
            }
        else:
            # Re-access scenarios
            old_ts = record.get("anchor_ts", now_ts)
            old_views = record.get("anchor_views", exact_views)
            prev_vph = record.get("last_vph", 0.0)
            delta_hours = max(0.001, (now_ts - old_ts) / 3600.0)

            if delta_hours >= (1.0 - 1e-3):
                # Scenario B: Re-access with delta >= 1 hour
                if exact_views < old_views:
                    # YouTube Audit (Negative delta)
                    vph_val = 0.0
                    audit_detected = True
                    confidence = "high"
                    self._anchors_db[video_id]["anchor_ts"] = now_ts
                    self._anchors_db[video_id]["anchor_views"] = exact_views
                    self._anchors_db[video_id]["last_vph"] = 0.0
                else:
                    vph_val = round((exact_views - old_views) / delta_hours, 2)
                    if vph_val < 0.1:
                        vph_val = 0.0
                    confidence = "high"
                    self._anchors_db[video_id]["anchor_ts"] = now_ts
                    self._anchors_db[video_id]["anchor_views"] = exact_views
                    self._anchors_db[video_id]["last_vph"] = vph_val

            elif delta_hours >= 0.25: # Between 15 and 60 minutes
                # Scenario C: Re-access between 15 and 60 minutes
                if exact_views > old_views:
                    vph_val = round((exact_views - old_views) / delta_hours, 2)
                    confidence = "medium"
                    self._anchors_db[video_id]["anchor_ts"] = now_ts
                    self._anchors_db[video_id]["anchor_views"] = exact_views
                    self._anchors_db[video_id]["last_vph"] = vph_val
                elif exact_views == old_views:
                    # Maintain last calculated VPH (handles YouTube CDN batch synchronization delays)
                    vph_val = prev_vph
                    confidence = "medium"
                else:
                    # Negative delta in short interval
                    vph_val = 0.0
                    audit_detected = True
                    confidence = "medium"
                    self._anchors_db[video_id]["anchor_ts"] = now_ts
                    self._anchors_db[video_id]["anchor_views"] = exact_views
                    self._anchors_db[video_id]["last_vph"] = 0.0
            else:
                # Very recent access (< 15 mins) fallback
                vph_val = prev_vph
                confidence = "medium"

            self._anchors_db[video_id]["last_fetch_ts"] = now_ts

        # Step 4: Traffic Classification
        traffic_status = self.classify_traffic(vph_val, pub_dt, now)

        # Step 5: Construct Typed Response Object
        response_obj: VideoVPHResponse = {
            "videoId": video_id,
            "exactViews": int(exact_views),
            "publishedAt": pub_iso,
            "vph": vph_val,
            "trafficStatus": traffic_status,
            "confidence": confidence,
            "providerUsed": provider_used or "innertube",
            "auditDetected": audit_detected,
            "deltaHours": round(delta_hours, 2),
            "calculatedAt": now_iso
        }

        # Cache response object in memory & persist
        self._anchors_db[video_id]["last_response"] = response_obj
        self._save_cache()

        return response_obj


# Global Singleton Instance
_DEFAULT_VPH_SERVICE: Optional[VPHService] = None

def get_vph_service() -> VPHService:
    """Get or initialize global VPHService singleton."""
    global _DEFAULT_VPH_SERVICE
    if _DEFAULT_VPH_SERVICE is None:
        _DEFAULT_VPH_SERVICE = VPHService()
    return _DEFAULT_VPH_SERVICE

def get_on_demand_vph(
    video_id: str,
    force_refresh: bool = False,
    fallback_views: Optional[int] = None,
    fallback_published: Optional[str] = None
) -> VideoVPHResponse:
    """Convenience helper to retrieve on-demand VPH with full multi-source fallback."""
    service = get_vph_service()
    return service.get_on_demand_vph(
        video_id=video_id,
        force_refresh=force_refresh,
        fallback_views=fallback_views,
        fallback_published=fallback_published
    )
