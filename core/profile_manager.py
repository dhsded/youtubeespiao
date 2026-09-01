"""
Profile & Multi-Instance Batch Manager for YouTube Espião.
Handles:
- Persistent default user profile (language, filters, min views, limits, exclusions).
- Saving and loading user presets.
- Spawning multiple isolated application instances from a .txt list of search terms.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ProfileManager")

DEFAULT_PROFILE: Dict[str, Any] = {
    "search_mode": "keywords",
    "target_lang": "global",
    "excluded_countries": [],
    "date_filter": "all_time",
    "year_start": 2020,
    "year_end": 2026,
    "sort_by": "view_count",
    "max_videos": 50,
    "unlimited_videos": False,
    "min_views": 0,
    "fast_mode": True,
    "include_related": True,
    "loop_24h": False,
    "min_delay": 1.0,
    "max_delay": 2.5,
    "proxy_url": ""
}

def get_profile_path() -> str:
    """Returns the persistent location for the default user profile JSON file."""
    app_data = os.environ.get("APPDATA")
    if app_data and os.path.exists(app_data):
        folder = os.path.join(app_data, "YouTubeEspiao")
    else:
        folder = os.path.join(os.path.expanduser("~"), ".youtube_espiao")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "default_profile.json")

def load_default_profile() -> Dict[str, Any]:
    """Loads the saved default profile from disk or returns factory defaults."""
    path = get_profile_path()
    profile = dict(DEFAULT_PROFILE)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    profile.update(data)
        except Exception as e:
            logger.warning(f"Failed to load default profile from {path}: {e}")
    return profile

def save_default_profile(profile_data: Dict[str, Any]) -> bool:
    """Saves the given profile configuration as the application default."""
    path = get_profile_path()
    try:
        merged = dict(DEFAULT_PROFILE)
        merged.update(profile_data)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save default profile to {path}: {e}")
        return False

def get_named_profiles_path() -> str:
    """Returns the persistent location for custom named profiles JSON file."""
    app_data = os.environ.get("APPDATA")
    if app_data and os.path.exists(app_data):
        folder = os.path.join(app_data, "YouTubeEspiao")
    else:
        folder = os.path.join(os.path.expanduser("~"), ".youtube_espiao")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "named_profiles.json")

def get_named_profiles() -> Dict[str, Dict[str, Any]]:
    """Returns all saved named profiles, including default built-in presets."""
    path = get_named_profiles_path()
    profiles: Dict[str, Dict[str, Any]] = {
        "⭐ Modo Padrão": dict(DEFAULT_PROFILE),
        "🔥 Alto Impacto (50k+ Views BR)": {
            **DEFAULT_PROFILE,
            "target_lang": "pt",
            "min_views": 50000,
            "max_videos": 100,
            "fast_mode": True
        },
        "🌐 Varredura Global Exaustiva": {
            **DEFAULT_PROFILE,
            "target_lang": "global",
            "unlimited_videos": True,
            "max_videos": 100000,
            "min_views": 10000,
            "fast_mode": True
        }
    }
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    profiles.update(saved)
        except Exception as e:
            logger.warning(f"Failed to load named profiles: {e}")
    return profiles

def save_named_profile(name: str, profile_data: Dict[str, Any]) -> bool:
    """Saves or updates a named configuration preset."""
    path = get_named_profiles_path()
    try:
        profiles = get_named_profiles()
        clean_name = name.strip()
        if not clean_name:
            return False
        merged = dict(DEFAULT_PROFILE)
        merged.update(profile_data)
        profiles[clean_name] = merged
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save named profile '{name}': {e}")
        return False

def delete_named_profile(name: str) -> bool:
    """Deletes a custom named profile if it exists."""
    path = get_named_profiles_path()
    try:
        profiles = get_named_profiles()
        if name in profiles:
            del profiles[name]
            with open(path, "w", encoding="utf-8") as f:
                json.dump(profiles, f, indent=4, ensure_ascii=False)
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to delete profile '{name}': {e}")
        return False

def launch_instance_with_target(target: str, autostart: bool = True) -> bool:
    """
    Spawns a new independent instance of YouTube Espião for the specified search term/channel,
    automatically claiming a new instance number and slot.
    """
    import subprocess
    try:
        target_clean = target.strip()
        if not target_clean:
            return False

        if getattr(sys, "frozen", False):
            exe_path = sys.executable
            args = [exe_path, "--target", target_clean]
            if autostart:
                args.append("--autostart")
            subprocess.Popen(args)
        else:
            main_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
            args = [sys.executable, main_script, "--target", target_clean]
            if autostart:
                args.append("--autostart")
            subprocess.Popen(args)
        return True
    except Exception as e:
        logger.error(f"Error launching instance for target '{target}': {e}")
        return False
