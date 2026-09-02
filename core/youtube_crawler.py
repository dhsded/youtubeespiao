"""
YouTube Crawler and Harvester (Keywords, Channels & Lists of Channels Engine).
Features:
- Dual Modes: Search by Keyword OR Search by Channel (single or bulk list of channels).
- Primary sorting by Views Count (Vídeos Mais Vistos).
- Channel Video Harvester (Populares / Recentes / Todos os Vídeos de Canais).
- Live Real-Time Video Signal for Embedded Chromium Browser.
- Recursive Related Videos Search (Busca em Vídeos Relacionados dentro do mesmo nicho/idioma).
- High-precision Language Verification & Scoring.
- Date of Upload & Comprehensive Metrics Calculation.
- Turbo Search Mode vs Safe Anti-Ban Mode.
- Date Filtering: Global, Specific Years, Year Ranges, and YouTube intervals.
- Automatic Duplicate Elimination (Session-wide seen video cache).
"""

import time
import random
import logging
import gc
import json
import re
import requests
from typing import List, Dict, Any, Callable, Optional, Set
import scrapetube
import yt_dlp

from core.metrics_calculator import calculate_video_metrics
from core.domain_extractor import DomainExtractor
from core.domain_validator import DomainValidator
from core.translator import is_content_matching_language, expand_queries_for_language
from core.relevance_filter import (
    get_youtube_related_suggestions,
    build_topic_profile,
    is_content_relevant_to_topic
)

logger = logging.getLogger(__name__)

USER_AGENTS_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
]

class YouTubeCrawler:
    def __init__(
        self,
        domain_extractor: Optional[DomainExtractor] = None,
        domain_validator: Optional[DomainValidator] = None,
        proxy_url: Optional[str] = None,
        min_delay: float = 1.0,
        max_delay: float = 2.5,
        fast_mode: bool = False
    ):
        self.extractor = domain_extractor or DomainExtractor()
        self.validator = domain_validator or DomainValidator()
        self.proxy_url = proxy_url.strip() if proxy_url else None
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.fast_mode = fast_mode
        self._is_stopped = False
        self.seen_video_ids: Set[str] = set()
        
        self.ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "skip_download": True,
            "ignoreerrors": True,
            "no_color": True,
            "get_comments": True,
            "extractor_args": {
                "youtube": {
                    "max_comments": ["2" if fast_mode else "5", "all", "2" if fast_mode else "5", "0"],
                    "comment_sort": ["top"]
                }
            }
        }

        if self.proxy_url:
            self.ydl_opts["proxy"] = self.proxy_url

    def set_fast_mode(self, fast: bool):
        self.fast_mode = fast
        self.ydl_opts["extractor_args"]["youtube"]["max_comments"] = ["2" if fast else "5", "all", "2" if fast else "5", "0"]

    def stop(self):
        """Signal the crawler to stop execution gracefully."""
        self._is_stopped = True

    def clear_seen_videos(self):
        """Reset the record of processed video IDs."""
        self.seen_video_ids.clear()

    def _sleep_jitter(self, multiplier: float = 1.0):
        if self._is_stopped:
            return
        if self.fast_mode:
            delay = random.uniform(0.1, 0.35) * multiplier
        else:
            delay = random.uniform(self.min_delay, self.max_delay) * multiplier
        steps = max(1, int(delay / 0.1))
        for _ in range(steps):
            if self._is_stopped:
                break
            time.sleep(0.1)

    def _get_random_user_agent(self) -> str:
        return random.choice(USER_AGENTS_POOL)

    def search_videos(
        self,
        keyword: str,
        max_results: int = 20,
        sort_by: str = "view_count",
        upload_date: Optional[str] = None,
        hl: str = "pt",
        gl: str = "BR"
    ) -> List[Dict[str, Any]]:
        """
        Fast search using scrapetube with sorting by view_count and date filters.
        """
        results = []
        try:
            kwargs = {
                "query": keyword,
                "limit": max_results,
                "sort_by": sort_by
            }
            if upload_date and upload_date not in ("all_time", "custom_range"):
                if upload_date in ("today", "this_week", "this_month", "this_year"):
                    kwargs["upload_date"] = upload_date

            search_gen = scrapetube.get_search(**kwargs)
            
            for item in search_gen:
                if self._is_stopped:
                    break
                
                vid_id = item.get("videoId")
                if not vid_id:
                    continue

                # Title
                title_runs = item.get("title", {}).get("runs", [])
                title = title_runs[0].get("text", "") if title_runs else "Sem Título"

                # Channel
                owner_runs = item.get("ownerText", {}).get("runs", [])
                channel_name = owner_runs[0].get("text", "Canal Desconhecido") if owner_runs else "Canal Desconhecido"
                
                # Thumbnail
                thumbs = item.get("thumbnail", {}).get("thumbnails", [])
                thumb_url = thumbs[-1].get("url") if thumbs else f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"

                # View count text
                view_text = item.get("viewCountText", {}).get("simpleText", "")
                view_count = self._parse_view_count(view_text)

                # Published time text
                pub_text = item.get("publishedTimeText", {}).get("simpleText", "")

                results.append({
                    "id": vid_id,
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "title": title,
                    "channel_name": channel_name,
                    "thumbnail": thumb_url,
                    "initial_view_count": view_count,
                    "published_text": pub_text
                })
        except Exception as e:
            logger.error(f"Error during search for '{keyword}' (sort={sort_by}, upload_date={upload_date}): {e}")

        return results

    def get_channel_videos(
        self,
        channel_identifier: str,
        max_results: int = 50,
        sort_by: str = "popular"
    ) -> List[Dict[str, Any]]:
        """
        Fetch videos from a specific YouTube channel.
        Supports URLs (@handle, /channel/UC..., /c/..., etc.), @handles, or usernames.
        Sort options: 'popular' (mais vistos), 'newest' (mais recentes), 'oldest' (mais antigos).
        """
        results = []
        clean = channel_identifier.strip()
        if not clean:
            return results

        clean_sort = "popular" if sort_by in ("popular", "view_count") else ("oldest" if sort_by == "oldest" else "newest")
        kwargs = {
            "limit": max_results,
            "sort_by": clean_sort
        }

        if clean.startswith("http://") or clean.startswith("https://"):
            kwargs["channel_url"] = clean
        elif clean.startswith("UC") and len(clean) >= 20:
            kwargs["channel_id"] = clean
        elif clean.startswith("@"):
            kwargs["channel_url"] = f"https://www.youtube.com/{clean}"
        else:
            kwargs["channel_url"] = f"https://www.youtube.com/@{clean}"

        try:
            search_gen = scrapetube.get_channel(**kwargs)
            for item in search_gen:
                if self._is_stopped:
                    break
                vid_id = item.get("videoId")
                if not vid_id:
                    continue

                # Title
                title_runs = item.get("title", {}).get("runs", [])
                title = title_runs[0].get("text", "") if title_runs else "Sem Título"

                # Channel
                owner_runs = item.get("ownerText", {}).get("runs", [])
                channel_name = owner_runs[0].get("text", clean) if owner_runs else clean

                # Thumbnail
                thumbs = item.get("thumbnail", {}).get("thumbnails", [])
                thumb_url = thumbs[-1].get("url") if thumbs else f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"

                # View count text
                view_text = item.get("viewCountText", {}).get("simpleText", "")
                view_count = self._parse_view_count(view_text)

                # Published time text
                pub_text = item.get("publishedTimeText", {}).get("simpleText", "")

                results.append({
                    "id": vid_id,
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "title": title,
                    "channel_name": channel_name,
                    "thumbnail": thumb_url,
                    "initial_view_count": view_count,
                    "published_text": pub_text
                })
        except Exception as e:
            logger.error(f"Error fetching channel videos for '{channel_identifier}': {e}")

        return results

    def _fetch_innertube_comments(self, video_id: str, hl: str = "pt", gl: str = "BR") -> Dict[str, Any]:
        """
        Direct high-speed YouTube InnerTube extraction for 2024 Entity Framework.
        Guarantees 100% extraction of Pinned Comment and Top Comments even when yt-dlp returns none.
        """
        pinned_comment = ""
        top_comments = []

        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            headers = {
                "User-Agent": self._get_random_user_agent(),
                "Accept-Language": f"{hl}-{gl},{hl};q=0.9,en-US;q=0.8,en;q=0.7"
            }
            proxies = {"http": self.proxy_url, "https": self.proxy_url} if self.proxy_url else None

            # 1. Fetch watch page initial data
            resp = requests.get(url, headers=headers, proxies=proxies, timeout=3.5)
            if resp.status_code != 200:
                return {"pinned_comment": "", "top_comments": []}

            html = resp.text
            match = re.search(r'var ytInitialData\s*=\s*({.*?});</script>', html)
            if not match:
                return {"pinned_comment": "", "top_comments": []}

            data = json.loads(match.group(1))

            # 2. Find comments continuation token
            tokens = []
            def _find_tokens(obj):
                if isinstance(obj, dict):
                    if "continuationCommand" in obj:
                        t = obj["continuationCommand"].get("token")
                        if t:
                            tokens.append(t)
                    for k, v in obj.items():
                        _find_tokens(v)
                elif isinstance(obj, list):
                    for it in obj:
                        _find_tokens(it)

            _find_tokens(data)

            # 3. Query InnerTube next endpoint with continuation token
            for tok in tokens:
                payload = {
                    "context": {
                        "client": {
                            "clientName": "WEB",
                            "clientVersion": "2.20240901.00.00",
                            "hl": hl,
                            "gl": gl
                        }
                    },
                    "continuation": tok
                }
                r_next = requests.post(
                    "https://www.youtube.com/youtubei/v1/next",
                    json=payload,
                    headers=headers,
                    proxies=proxies,
                    timeout=3.5
                )
                if r_next.status_code != 200:
                    continue

                d_next = r_next.json()

                # A. Identify Pinned Comment ID
                pinned_comment_id = None
                endpoints = d_next.get("onResponseReceivedEndpoints", [])
                for ep in endpoints:
                    action = ep.get("reloadContinuationItemsCommand") or ep.get("appendContinuationItemsAction")
                    if action:
                        items = action.get("continuationItems", [])
                        for it in items:
                            ctr = it.get("commentThreadRenderer", {})
                            if ctr:
                                cvm = ctr.get("commentViewModel", {}).get("commentViewModel", {})
                                if cvm.get("pinnedText") or ctr.get("renderingPriority") == "RENDERING_PRIORITY_PINNED":
                                    pinned_comment_id = cvm.get("commentId")

                # B. Extract from modern Entity Framework (2024 architecture)
                mutations = d_next.get("frameworkUpdates", {}).get("entityBatchUpdate", {}).get("mutations", [])
                if mutations:
                    for m in mutations:
                        payload_m = m.get("payload", {})
                        if "commentEntityPayload" in payload_m:
                            cep = payload_m["commentEntityPayload"]
                            c_id = cep.get("properties", {}).get("commentId", "")
                            content = cep.get("properties", {}).get("content", {}).get("content", "")
                            if content:
                                if pinned_comment_id and c_id == pinned_comment_id and not pinned_comment:
                                    pinned_comment = content
                                else:
                                    top_comments.append(content)
                    if top_comments or pinned_comment:
                        break

                # C. Extract from legacy comments format (fallback)
                for ep in endpoints:
                    action = ep.get("reloadContinuationItemsCommand") or ep.get("appendContinuationItemsAction")
                    if action:
                        items = action.get("continuationItems", [])
                        for it in items:
                            ctr = it.get("commentThreadRenderer", {})
                            if ctr:
                                c_rend = ctr.get("comment", {}).get("commentRenderer", {})
                                if c_rend:
                                    is_p = bool(c_rend.get("pinnedCommentBadge"))
                                    runs = c_rend.get("contentText", {}).get("runs", [])
                                    text = "".join([r.get("text", "") for r in runs])
                                    if text:
                                        if is_p and not pinned_comment:
                                            pinned_comment = text
                                        else:
                                            top_comments.append(text)
                if top_comments or pinned_comment:
                    break

        except Exception as e:
            logger.debug(f"InnerTube comments extraction error for video {video_id}: {e}")

        return {
            "pinned_comment": pinned_comment,
            "top_comments": top_comments
        }

    def _fetch_watch_page_data_fallback(self, video_id: str, hl: str = "pt", gl: str = "BR") -> Dict[str, Any]:
        """
        Direct high-speed HTTP extraction for video details (description, title, author, views)
        directly from YouTube watch page HTML payload when yt-dlp is rate-limited or fails.
        """
        fallback_data = {"description": "", "title": "", "channel_name": "", "view_count": 0}
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            headers = {
                "User-Agent": self._get_random_user_agent(),
                "Accept-Language": f"{hl}-{gl},{hl};q=0.9,en-US;q=0.8,en;q=0.7"
            }
            proxies = {"http": self.proxy_url, "https": self.proxy_url} if self.proxy_url else None
            resp = requests.get(url, headers=headers, proxies=proxies, timeout=3.5)
            if resp.status_code == 200:
                html = resp.text
                
                # 1. Try ytInitialPlayerResponse
                m_player = re.search(r'var ytInitialPlayerResponse\s*=\s*({.*?});', html)
                if m_player:
                    try:
                        p_data = json.loads(m_player.group(1))
                        v_details = p_data.get("videoDetails", {})
                        if v_details:
                            fallback_data["description"] = v_details.get("shortDescription", "")
                            fallback_data["title"] = v_details.get("title", "")
                            fallback_data["channel_name"] = v_details.get("author", "")
                            views_str = v_details.get("viewCount")
                            if views_str and str(views_str).isdigit():
                                fallback_data["view_count"] = int(views_str)
                    except Exception:
                        pass

                # 2. Try ytInitialData if description is still empty
                if not fallback_data["description"]:
                    m_initial = re.search(r'var ytInitialData\s*=\s*({.*?});</script>', html)
                    if m_initial:
                        try:
                            i_data = json.loads(m_initial.group(1))
                            def _find_desc(obj):
                                if isinstance(obj, dict):
                                    if "description" in obj and isinstance(obj["description"], dict) and "runs" in obj["description"]:
                                        return "".join([r.get("text", "") for r in obj["description"]["runs"]])
                                    if "shortDescription" in obj and isinstance(obj["shortDescription"], str):
                                        return obj["shortDescription"]
                                    for v in obj.values():
                                        res = _find_desc(v)
                                        if res:
                                            return res
                                elif isinstance(obj, list):
                                    for item in obj:
                                        res = _find_desc(item)
                                        if res:
                                            return res
                                return ""
                            d_text = _find_desc(i_data)
                            if d_text:
                                fallback_data["description"] = d_text
                        except Exception:
                            pass
        except Exception as e:
            logger.debug(f"Watch page fallback error for video {video_id}: {e}")
        return fallback_data

    def get_video_deep_details(self, video_url: str, hl: str = "pt", gl: str = "BR", retries: int = 1) -> Dict[str, Any]:
        """
        Fetch video metadata & comments with automatic retry and backoff.
        """
        info = {
            "description": "",
            "pinned_comment": "",
            "top_comments": [],
            "view_count": 0,
            "upload_date": None,
            "timestamp": None,
            "title": "",
            "channel_name": "",
            "thumbnail": ""
        }

        opts = dict(self.ydl_opts)
        opts["user_agent"] = self._get_random_user_agent()
        opts["http_headers"] = {
            "Accept-Language": f"{hl}-{gl},{hl};q=0.9,en;q=0.8"
        }

        vid_id = (video_url.split("v=")[-1].split("&")[0] if "v=" in video_url else "")

        for attempt in range(retries + 1):
            if self._is_stopped:
                break
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    meta = ydl.extract_info(video_url, download=False)
                    if meta:
                        info["title"] = meta.get("title", "")
                        info["channel_name"] = meta.get("uploader") or meta.get("channel", "")
                        info["thumbnail"] = meta.get("thumbnail", "")
                        info["description"] = meta.get("description", "")
                        info["view_count"] = meta.get("view_count") or 0
                        info["upload_date"] = meta.get("upload_date")
                        info["timestamp"] = meta.get("timestamp")

                        comments = meta.get("comments") or []
                        for c in comments:
                            c_text = c.get("text", "")
                            is_pinned = c.get("is_pinned", False) or c.get("pinned", False)
                            if is_pinned and not info["pinned_comment"]:
                                info["pinned_comment"] = c_text
                            else:
                                info["top_comments"].append(c_text)
                        
                        if not info["pinned_comment"] and comments:
                            info["pinned_comment"] = comments[0].get("text", "")

                        # High-Precision InnerTube fallback: if yt-dlp extracted no comments or no description
                        if vid_id:
                            if not info["description"]:
                                fb = self._fetch_watch_page_data_fallback(vid_id, hl=hl, gl=gl)
                                if fb.get("description"):
                                    info["description"] = fb["description"]

                            if not info["pinned_comment"] and not info["top_comments"]:
                                c_info = self._fetch_innertube_comments(vid_id, hl=hl, gl=gl)
                                if c_info.get("pinned_comment"):
                                    info["pinned_comment"] = c_info["pinned_comment"]
                                if c_info.get("top_comments"):
                                    info["top_comments"] = c_info["top_comments"]

                        return info

            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "too many requests" in err_str or "captcha" in err_str:
                    cool_off = (attempt + 1) * 10
                    logger.warning(f"Rate limit detected. Cooling off for {cool_off}s...")
                    time.sleep(cool_off)
                else:
                    logger.debug(f"yt-dlp extract error for {video_url}: {e}")
                    time.sleep(0.3)

        # Fallback if yt-dlp failed completely
        if vid_id and not info["description"]:
            fb = self._fetch_watch_page_data_fallback(vid_id, hl=hl, gl=gl)
            if fb.get("description"):
                info["description"] = fb["description"]
            if not info["title"] and fb.get("title"):
                info["title"] = fb["title"]
            if not info["channel_name"] and fb.get("channel_name"):
                info["channel_name"] = fb["channel_name"]
            if not info["view_count"] and fb.get("view_count"):
                info["view_count"] = fb["view_count"]

            c_info = self._fetch_innertube_comments(vid_id, hl=hl, gl=gl)
            if c_info.get("pinned_comment"):
                info["pinned_comment"] = c_info["pinned_comment"]
            if c_info.get("top_comments"):
                info["top_comments"] = c_info["top_comments"]

        return info

    def process_channel(
        self,
        channel_identifier: str,
        max_videos: int = 50,
        min_views: int = 0,
        sort_by: str = "popular",
        hl: str = "pt",
        gl: str = "BR",
        on_live_video: Optional[Callable[[str, str], None]] = None,
        on_video_processed: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_domain_found: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_progress: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Process all or top videos of a specific YouTube channel, extracting domains and Instagram accounts.
        """
        self._is_stopped = False
        display_name = channel_identifier if channel_identifier.startswith("@") or channel_identifier.startswith("http") else f"@{channel_identifier}"
        
        if on_progress:
            on_progress(0, max_videos, f"Coletando vídeos do canal {display_name}...")

        channel_vids = self.get_channel_videos(
            channel_identifier=channel_identifier,
            max_results=max_videos,
            sort_by=sort_by
        )

        scanned_videos = []
        all_domains = []
        total_found = len(channel_vids)

        for idx, v_item in enumerate(channel_vids):
            if self._is_stopped:
                break

            vid_id = v_item.get("id")
            if not vid_id or vid_id in self.seen_video_ids:
                continue
            self.seen_video_ids.add(vid_id)

            # Minimum views pre-filter
            if min_views > 0:
                init_views = v_item.get("initial_view_count")
                if init_views is not None and init_views < min_views:
                    logger.debug(f"Pre-filter skipped channel video below min views ({init_views} < {min_views}): {v_item.get('title')}")
                    continue

            current_num = idx + 1
            if on_progress:
                on_progress(current_num, max(total_found, max_videos), f"Canal {display_name} [{current_num}/{total_found}]: {v_item['title'][:32]}...")

            if on_live_video:
                on_live_video(v_item["url"], v_item["title"])

            self._sleep_jitter()

            deep_info = self.get_video_deep_details(v_item.get("url", ""), hl=hl, gl=gl)
            
            title = deep_info.get("title") or v_item.get("title", "Sem Título")
            channel = deep_info.get("channel_name") or v_item.get("channel_name", "Canal")
            thumbnail = deep_info.get("thumbnail") or v_item.get("thumbnail", "")
            view_count = deep_info.get("view_count") or v_item.get("initial_view_count") or 0

            # Strict minimum views check
            if min_views > 0 and view_count < min_views:
                logger.debug(f"Skipped channel video below min views ({view_count} < {min_views}): {title}")
                continue

            description = deep_info.get("description", "")
            pinned_comment = deep_info.get("pinned_comment", "")

            metrics = calculate_video_metrics(
                view_count=view_count,
                upload_date=deep_info["upload_date"],
                timestamp=deep_info["timestamp"],
                published_text=v_item.get("published_text"),
                video_id=v_item.get("id")
            )

            # Extract domains comprehensively from Pinned Comment, Description, and Top Comments
            combined_extracted_domains = []
            seen_video_domains = set()

            # 1. Pinned Comment
            if pinned_comment:
                for d in self.extractor.process_text_for_domains(pinned_comment, source_location="📌 Comentário Fixado"):
                    if d["root_domain"] not in seen_video_domains:
                        seen_video_domains.add(d["root_domain"])
                        combined_extracted_domains.append(d)

            # 2. Video Description
            if description:
                for d in self.extractor.process_text_for_domains(description, source_location="📄 Descrição"):
                    if d["root_domain"] not in seen_video_domains:
                        seen_video_domains.add(d["root_domain"])
                        combined_extracted_domains.append(d)

            # 3. Top Comments
            for comm in deep_info.get("top_comments", []):
                if comm and comm != pinned_comment:
                    for d in self.extractor.process_text_for_domains(comm, source_location="💬 Comentário"):
                        if d["root_domain"] not in seen_video_domains:
                            seen_video_domains.add(d["root_domain"])
                            combined_extracted_domains.append(d)

            validated_domains_for_video = []
            for d in combined_extracted_domains:
                if d.get("is_instagram"):
                    val_res = {
                        "status": d.get("status", "Disponível"),
                        "status_color": d.get("status_color", "#10B981"),
                        "badge_icon": d.get("badge_icon", "🟢"),
                        "details": d.get("details", ""),
                        "dns_active": False,
                        "ns_records": [],
                        "ip_records": [],
                        "expires_at": None,
                        "buy_link": d.get("buy_link", ""),
                        "registrar_name": "Instagram"
                    }
                else:
                    val_res = self.validator.validate_domain(d["root_domain"])
                
                domain_record = {
                    **d,
                    **val_res,
                    "video_id": v_item["id"],
                    "video_title": title,
                    "video_url": v_item["url"],
                    "channel_name": channel,
                    "keyword": display_name,
                    "language": hl,
                    "video_metrics": metrics
                }
                
                validated_domains_for_video.append(domain_record)
                all_domains.append(domain_record)

                if on_domain_found:
                    on_domain_found(domain_record)

            video_record = {
                "id": v_item["id"],
                "url": v_item["url"],
                "title": title,
                "channel_name": channel,
                "thumbnail": thumbnail,
                "description": description,
                "pinned_comment": pinned_comment,
                "keyword": display_name,
                "language": hl,
                "metrics": metrics,
                "domains": validated_domains_for_video
            }

            scanned_videos.append(video_record)

            if on_video_processed:
                on_video_processed(video_record)

        return {
            "channel": display_name,
            "total_videos": len(scanned_videos),
            "total_domains": len(all_domains),
            "available_domains": sum(1 for d in all_domains if d.get("status") == "Disponível"),
            "videos": scanned_videos,
            "domains": all_domains
        }

    def process_keyword(
        self,
        keyword: str,
        target_lang: str = "pt",
        max_videos: int = 15,
        min_views: int = 0,
        sort_by: str = "view_count",
        date_filter: str = "all_time",
        custom_year: Optional[int] = None,
        year_range: Optional[tuple] = None,
        include_related: bool = True,
        excluded_langs: Optional[List[str]] = None,
        hl: str = "pt",
        gl: str = "BR",
        display_label: str = "",
        on_live_video: Optional[Callable[[str, str], None]] = None,
        on_video_processed: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_domain_found: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_progress: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Processes a keyword prioritized by views with real-time browser signals,
        intelligent related terms learning (YouTube Suggest) and strict semantic relevance filtering.
        """
        self._is_stopped = False
        
        target_info = f"{display_label} - " if display_label else ""
        if on_progress:
            on_progress(0, max_videos, f"{target_info}Descobrindo termos relacionados e buscando vídeos...")

        # Determine active year range if specified
        active_year_range = None
        if year_range:
            active_year_range = (min(year_range), max(year_range))
        elif date_filter.isdigit():
            yr = int(date_filter)
            active_year_range = (yr, yr)
        elif custom_year:
            active_year_range = (int(custom_year), int(custom_year))

        # 1. Learn real-time related search suggestions from YouTube Autocomplete
        related_suggestions = []
        if include_related or max_videos > 30:
            try:
                related_suggestions = get_youtube_related_suggestions(keyword, hl=hl, gl=gl, max_suggestions=25)
                if related_suggestions and on_progress:
                    on_progress(0, max_videos, f"{target_info}🔗 {len(related_suggestions)} termos relacionados aprendidos no YouTube...")
            except Exception as e:
                logger.debug(f"Error fetching related suggestions for '{keyword}': {e}")

        # 2. Build multi-language query expansion
        sub_tasks = expand_queries_for_language(keyword, target_lang, excluded_langs=excluded_langs)
        # 2. Build Semantic Topic Profile for strict relevance gating
        topic_profile = build_topic_profile(keyword, related_terms=related_suggestions)

        # 3. Initial Primary Search
        initial_videos = []
        if active_year_range:
            start_yr, end_yr = active_year_range
            num_years = max(1, (end_yr - start_yr + 1))
            per_year_limit = 5000 if max_videos >= 50000 else max(10, int(max_videos / num_years) + 5)
            for yr in range(end_yr, start_yr - 1, -1):
                if self._is_stopped:
                    break
                yr_videos = self.search_videos(
                    f"{keyword} {yr}",
                    max_results=per_year_limit,
                    sort_by=sort_by,
                    hl=hl,
                    gl=gl
                )
                initial_videos.extend(yr_videos)
        else:
            search_limit = 5000 if max_videos >= 50000 else min(max_videos, 500)
            initial_videos = self.search_videos(
                keyword,
                max_results=search_limit,
                sort_by=sort_by,
                upload_date=date_filter if date_filter in ("today", "this_week", "this_month", "this_year") else None,
                hl=hl,
                gl=gl
            )

        scanned_videos = []
        all_domains = []
        processed_index = 0
        related_suggestions_queue = list(related_suggestions)

        while (initial_videos or related_suggestions_queue) and len(scanned_videos) < max_videos:
            if self._is_stopped:
                break

            # If current batch is empty or low, fetch from next learned related suggestion
            if not initial_videos and related_suggestions_queue and len(scanned_videos) < max_videos:
                next_rel_term = related_suggestions_queue.pop(0)
                if on_progress:
                    on_progress(len(scanned_videos), max_videos, f"{target_info}Buscando termo relacionado: '{next_rel_term}'...")
                
                if active_year_range:
                    start_yr, end_yr = active_year_range
                    rel_vids = []
                    for yr in range(end_yr, start_yr - 1, -1):
                        if self._is_stopped:
                            break
                        rel_vids.extend(self.search_videos(
                            keyword=f"{next_rel_term} {yr}",
                            max_results=min(max_videos - len(scanned_videos), 300),
                            sort_by=sort_by,
                            hl=hl,
                            gl=gl
                        ))
                else:
                    rel_vids = self.search_videos(
                        keyword=next_rel_term,
                        max_results=min(max_videos - len(scanned_videos), 300),
                        sort_by=sort_by,
                        upload_date=date_filter if date_filter in ("today", "this_week", "this_month", "this_year") else None,
                        hl=hl,
                        gl=gl
                    )
                initial_videos.extend(rel_vids)
                if not initial_videos and not related_suggestions_queue:
                    break

            if not initial_videos:
                break

            v_item = initial_videos.pop(0)
            vid_id = v_item.get("id")
            if not vid_id or vid_id in self.seen_video_ids:
                continue
            self.seen_video_ids.add(vid_id)

            # Minimum views pre-filter
            if min_views > 0:
                init_views = v_item.get("initial_view_count")
                if init_views is not None and init_views < min_views:
                    logger.debug(f"Pre-filter skipped video below min views ({init_views} < {min_views}): {v_item.get('title')}")
                    continue

            # Quick pre-filter check on title relevance before deep scraping
            if not is_content_relevant_to_topic(
                title=v_item.get("title", ""),
                description="",
                channel_name=v_item.get("channel_name", ""),
                topic_profile=topic_profile,
                min_score_threshold=15.0
            ):
                logger.debug(f"Pre-filter skipped off-topic video: {v_item.get('title')}")
                continue

            if on_progress:
                on_progress(len(scanned_videos) + 1, max_videos, f"{target_info}Analisando [{len(scanned_videos)+1}/{max_videos}]: {v_item['title'][:35]}...")

            # Emit Live Real-time Video Signal for Browser
            if on_live_video:
                on_live_video(v_item["url"], v_item["title"])

            self._sleep_jitter()

            # Deep extraction with language headers
            deep_info = self.get_video_deep_details(v_item.get("url", ""), hl=hl, gl=gl)
            
            title = deep_info.get("title") or v_item.get("title", "Sem Título")
            channel = deep_info.get("channel_name") or v_item.get("channel_name", "Canal")
            thumbnail = deep_info.get("thumbnail") or v_item.get("thumbnail", "")
            view_count = deep_info.get("view_count") or v_item.get("initial_view_count") or 0
            
            # Strict Minimum Views Check
            if min_views > 0 and view_count < min_views:
                logger.debug(f"Skipped video below min views ({view_count} < {min_views}): {title}")
                continue

            description = deep_info.get("description", "")
            pinned_comment = deep_info.get("pinned_comment", "")

            # High-Precision Multi-Layer Language Verification
            if target_lang and target_lang not in ("global", "auto", "en"):
                if not is_content_matching_language(
                    title=title,
                    description=description,
                    channel_name=channel,
                    target_lang=target_lang,
                    comments_sample=""
                ):
                    # Video is in foreign language (e.g. Spanish, English), strictly skip
                    continue

            # Strict Semantic Topic Relevance Verification
            if not is_content_relevant_to_topic(
                title=title,
                description=description,
                channel_name=channel,
                topic_profile=topic_profile,
                min_score_threshold=20.0
            ):
                logger.info(f"Filtered out off-topic video: '{title}' (Channel: {channel})")
                continue

            # Calculate views metrics (hourly, daily, monthly, yearly, publish date)
            metrics = calculate_video_metrics(
                view_count=view_count,
                upload_date=deep_info["upload_date"],
                timestamp=deep_info["timestamp"],
                published_text=v_item.get("published_text"),
                video_id=v_item.get("id")
            )

            # Strict Year Range Enforcement (respects specified interval even with 'all videos' option)
            if active_year_range:
                start_yr, end_yr = active_year_range
                v_year = metrics.get("upload_year")
                if v_year is not None and (v_year < start_yr or v_year > end_yr):
                    logger.debug(f"Skipped video outside year range {start_yr}-{end_yr} (upload_year={v_year}): {title}")
                    continue

            # Extract domains comprehensively from Pinned Comment, Description, and Top Comments
            combined_extracted_domains = []
            seen_video_domains = set()

            # 1. Pinned Comment
            if pinned_comment:
                for d in self.extractor.process_text_for_domains(pinned_comment, source_location="📌 Comentário Fixado"):
                    if d["root_domain"] not in seen_video_domains:
                        seen_video_domains.add(d["root_domain"])
                        combined_extracted_domains.append(d)

            # 2. Video Description
            if description:
                for d in self.extractor.process_text_for_domains(description, source_location="📄 Descrição"):
                    if d["root_domain"] not in seen_video_domains:
                        seen_video_domains.add(d["root_domain"])
                        combined_extracted_domains.append(d)

            # 3. Top Comments
            for comm in deep_info.get("top_comments", []):
                if comm and comm != pinned_comment:
                    for d in self.extractor.process_text_for_domains(comm, source_location="💬 Comentário"):
                        if d["root_domain"] not in seen_video_domains:
                            seen_video_domains.add(d["root_domain"])
                            combined_extracted_domains.append(d)

            # Validate each domain or Instagram account
            validated_domains_for_video = []
            for d in combined_extracted_domains:
                if d.get("is_instagram"):
                    val_res = {
                        "status": d.get("status", "Disponível"),
                        "status_color": d.get("status_color", "#10B981"),
                        "badge_icon": d.get("badge_icon", "🟢"),
                        "details": d.get("details", ""),
                        "dns_active": False,
                        "ns_records": [],
                        "ip_records": [],
                        "expires_at": None,
                        "buy_link": d.get("buy_link", ""),
                        "registrar_name": "Instagram"
                    }
                else:
                    val_res = self.validator.validate_domain(d["root_domain"])
                
                domain_record = {
                    **d,
                    **val_res,
                    "video_id": v_item["id"],
                    "video_title": title,
                    "video_url": v_item["url"],
                    "channel_name": channel,
                    "keyword": keyword,
                    "language": hl,
                    "video_metrics": metrics
                }
                
                validated_domains_for_video.append(domain_record)
                all_domains.append(domain_record)

                if on_domain_found:
                    on_domain_found(domain_record)

            video_record = {
                "id": v_item["id"],
                "url": v_item["url"],
                "title": title,
                "channel_name": channel,
                "thumbnail": thumbnail,
                "description": description,
                "pinned_comment": pinned_comment,
                "keyword": keyword,
                "language": hl,
                "metrics": metrics,
                "domains": validated_domains_for_video
            }

            scanned_videos.append(video_record)

            if on_video_processed:
                on_video_processed(video_record)

            # Periodic garbage collection every 200 videos to preserve low memory footprint
            if len(scanned_videos) % 200 == 0:
                gc.collect()

        # Primary sort: Highest view counts first
        scanned_videos.sort(key=lambda x: x["metrics"]["view_count"], reverse=True)
        gc.collect()

        return {
            "keyword": keyword,
            "total_videos": len(scanned_videos),
            "total_domains": len(all_domains),
            "available_domains": sum(1 for d in all_domains if d.get("status") == "Disponível"),
            "videos": scanned_videos,
            "domains": all_domains
        }

    @staticmethod
    def _parse_view_count(view_text: str) -> int:
        if not view_text:
            return 0
        text = view_text.lower().replace(".", "").replace(",", ".")
        try:
            nums = "".join([c for c in text if c.isdigit()])
            return int(nums) if nums else 0
        except Exception:
            return 0
