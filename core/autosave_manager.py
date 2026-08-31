"""
Auto-Save & Emergency Crash Recovery Manager for YouTube Espião.
Features:
- Continuous background auto-saving (every 30 seconds and on item discovery).
- Crash and reboot resilience: persists complete session data to %APPDATA%/YouTube Espiao/autosave_session.json.
- Automatic emergency backup export in user's Downloads folder (YouTube_Espiao_AutoSave_Recuperacao.xlsx).
- Seamless 1-click or automatic session restoration upon application startup.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

logger = logging.getLogger("AutoSaveManager")

class AutoSaveManager:
    def __init__(self):
        # 1. Determine AppData storage path
        appdata = os.getenv("APPDATA") or os.path.expanduser("~")
        self.save_dir = os.path.join(appdata, "YouTube Espiao")
        os.makedirs(self.save_dir, exist_ok=True)
        self.session_file = os.path.join(self.save_dir, "autosave_session.json")

        # 2. Determine User Downloads path for emergency exported sheets
        user_home = os.path.expanduser("~")
        self.downloads_dir = os.path.join(user_home, "Downloads")
        if not os.path.exists(self.downloads_dir):
            self.downloads_dir = user_home

    def save_session(
        self,
        videos_data: List[Dict[str, Any]],
        domains_data: List[Dict[str, Any]],
        keywords: Optional[List[str]] = None,
        search_params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Atomically save current mined data and parameters to local AppData and emergency Downloads backup.
        """
        if not videos_data and not domains_data:
            return False

        payload = {
            "timestamp": datetime.now().isoformat(),
            "formatted_time": datetime.now().strftime("%d/%m/%Y às %H:%M:%S"),
            "total_videos": len(videos_data),
            "total_domains": len(domains_data),
            "keywords": keywords or [],
            "search_params": search_params or {},
            "videos": videos_data,
            "domains": domains_data
        }

        try:
            # 1. Atomic write to local JSON
            temp_file = self.session_file + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            
            if os.path.exists(self.session_file):
                try:
                    os.remove(self.session_file)
                except Exception:
                    pass
            os.rename(temp_file, self.session_file)

            # 2. Emergency Backup to Downloads folder (Excel & JSON) if there are domains
            if len(domains_data) > 0 or len(videos_data) > 0:
                self._export_downloads_backup(videos_data, domains_data, payload)

            return True

        except Exception as e:
            logger.error(f"Failed to auto-save session: {e}")
            return False

    def _export_downloads_backup(self, videos_data: List[Dict[str, Any]], domains_data: List[Dict[str, Any]], payload: Dict[str, Any]):
        """Export emergency backup copies in the user's Downloads directory."""
        try:
            from core.exporter import DataExporter
            dl_xlsx = os.path.join(self.downloads_dir, "YouTube_Espiao_AutoSave_Recuperacao.xlsx")
            dl_json = os.path.join(self.downloads_dir, "YouTube_Espiao_AutoSave_Recuperacao.json")

            # Write Excel
            DataExporter.export_to_excel(dl_xlsx, domains_data, videos_data)

            # Write JSON
            with open(dl_json, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.debug(f"Downloads backup write ignored: {e}")

    def has_saved_session(self) -> bool:
        """Check if an existing auto-saved session with data exists."""
        if not os.path.exists(self.session_file):
            return False
        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return bool(data.get("videos") or data.get("domains"))
        except Exception:
            return False

    def load_saved_session(self) -> Optional[Dict[str, Any]]:
        """Load and return the saved session payload."""
        if not self.has_saved_session():
            return None
        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load saved session: {e}")
            return None

    def clear_saved_session(self):
        """Clear local session storage when user resets or clears data."""
        if os.path.exists(self.session_file):
            try:
                os.remove(self.session_file)
            except Exception:
                pass
