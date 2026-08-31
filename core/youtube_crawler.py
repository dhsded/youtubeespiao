"""
YouTube Crawler and Harvester (24/7 Multi-Language, Live Telemetry & Recursive Related Videos Engine).
Features:
- Primary sorting by Views Count (Vídeos Mais Vistos).
- Live Real-Time Video Signal for Embedded Chromium Browser.
- Recursive Related Videos Search (Busca em Vídeos Relacionados dentro do mesmo nicho/idioma).
- Robust Language Verification: Filters out foreign videos when a specific language (e.g. Portuguese) is chosen.
- Turbo Search Mode (Ultra-Fast 0.3s processing) vs Safe Anti-Ban Mode.
- Date Filtering: Global/All-Time, Specific Years, Year Ranges, and YouTube intervals.
- Automatic Duplicate Elimination (Session-wide seen video cache).
"""

import time
import random
import logging
import gc
from typing import List, Dict, Any, Callable, Optional, Set
import scrapetube
import yt_dlp

from core.metrics_calculator import calculate_video_metrics
from core.domain_extractor import DomainExtractor
from core.domain_validator import DomainValidator
from core.translator import is_content_matching_language

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

        return info

    def process_keyword(
        self,
        keyword: str,
        target_lang: str = "pt",
        max_videos: int = 15,
        sort_by: str = "view_count",
        date_filter: str = "all_time",
        custom_year: Optional[int] = None,
        year_range: Optional[tuple] = None,
        include_related: bool = True,
        hl: str = "pt",
        gl: str = "BR",
        display_label: str = "",
        on_live_video: Optional[Callable[[str, str], None]] = None,
        on_video_processed: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_domain_found: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_progress: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Processes a keyword prioritized by views with real-time browser signals and related video expansion.
        """
        self._is_stopped = False
        
        target_info = f"{display_label} - " if display_label else ""
        if on_progress:
            on_progress(0, max_videos, f"{target_info}Buscando vídeos mais vistos para: '{keyword}'...")

        initial_videos = []

        # 1. Check if user specified a specific year (e.g. 2024) or year range (e.g. 2020..2026)
        if date_filter.isdigit():
            year_val = date_filter
            search_term = f"{keyword} {year_val}"
            initial_videos = self.search_videos(
                search_term,
                max_results=max_videos,
                sort_by=sort_by,
                hl=hl,
                gl=gl
            )
        elif date_filter == "custom_range" and year_range:
            start_yr, end_yr = year_range
            per_year_limit = max(5, int(max_videos / max(1, (end_yr - start_yr + 1))))
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
            initial_videos = self.search_videos(
                keyword,
                max_results=max_videos,
                sort_by=sort_by,
                upload_date=date_filter if date_filter in ("today", "this_week", "this_month", "this_year") else None,
                hl=hl,
                gl=gl
            )

        scanned_videos = []
        all_domains = []
        processed_index = 0

        while initial_videos and len(scanned_videos) < max_videos:
            if self._is_stopped:
                break

            v_item = initial_videos.pop(0)
            vid_id = v_item.get("id")
            if not vid_id or vid_id in self.seen_video_ids:
                continue
            self.seen_video_ids.add(vid_id)

            processed_index += 1

            if on_progress:
                on_progress(len(scanned_videos) + 1, max_videos, f"{target_info}Analisando [{len(scanned_videos)+1}/{max_videos}]: {v_item['title'][:35]}...")

            # Emit Live Real-time Video Signal for Browser
            if on_live_video:
                on_live_video(v_item["url"], v_item["title"])

            self._sleep_jitter()

            # Deep extraction with language headers
            deep_info = self.get_video_deep_details(v_item["url"], hl=hl, gl=gl)
            
            title = deep_info["title"] or v_item["title"]
            channel = deep_info["channel_name"] or v_item["channel_name"]
            thumbnail = deep_info["thumbnail"] or v_item["thumbnail"]
            view_count = deep_info["view_count"] or v_item["initial_view_count"]
            description = deep_info["description"]
            pinned_comment = deep_info["pinned_comment"]
            top_comments = deep_info.get("top_comments", [])

            # High-Precision Multi-Layer Language Verification
            if target_lang and target_lang not in ("global", "auto", "en"):
                comments_text_sample = " ".join(top_comments[:3])
                if not is_content_matching_language(
                    title=title,
                    description=description,
                    channel_name=channel,
                    target_lang=target_lang,
                    comments_sample=comments_text_sample
                ):
                    # Video is in foreign language (e.g. Spanish, English), strictly skip
                    continue

            # Recursive Related Videos Harvest: Discover related videos in the exact niche cluster
            if include_related and len(scanned_videos) + len(initial_videos) < max_videos * 2:
                try:
                    rel_query = f"{title[:45]}"
                    rel_vids = self.search_videos(
                        keyword=rel_query,
                        max_results=3,
                        sort_by="view_count",
                        hl=hl,
                        gl=gl
                    )
                    for r_vid in rel_vids:
                        r_id = r_vid.get("id")
                        if r_id and r_id not in self.seen_video_ids:
                            # Quick check on related video title
                            if target_lang and target_lang not in ("global", "auto", "en"):
                                if is_content_matching_language(r_vid.get("title", ""), "", r_vid.get("channel_name", ""), target_lang):
                                    initial_videos.append(r_vid)
                            else:
                                initial_videos.append(r_vid)
                except Exception as e:
                    logger.debug(f"Related videos fetch error: {e}")

            # Calculate views metrics (hourly, daily, monthly, yearly)
            metrics = calculate_video_metrics(
                view_count=view_count,
                upload_date=deep_info["upload_date"],
                timestamp=deep_info["timestamp"]
            )

            # Extract domains and Instagrams from Pinned Comment, Description, and other Comments
            pinned_domains = self.extractor.process_text_for_domains(pinned_comment, source_location="📌 Comentário Fixado") if pinned_comment else []
            desc_domains = self.extractor.process_text_for_domains(description, source_location="📄 Descrição")
            comments_text = " ".join(top_comments)
            other_comment_domains = self.extractor.process_text_for_domains(comments_text, source_location="💬 Comentários")

            combined_extracted_domains = pinned_domains + desc_domains + other_comment_domains

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
