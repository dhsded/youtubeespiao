"""
Multi-Instance Manager for YouTube Espião & Hunter Browser.
Features:
- Dynamic instance numbering (#1, #2, #3, ...) starting strictly from 1.
- Robust PID verification and cleanup of stale locks.
- Dynamic color themes per instance number (#1 Red, #2 Blue, #3 Green, #4 Amber, #5 Purple, etc.).
- Chromium profile data isolation per instance to avoid file locks.
- Clean release of instance slot on exit.
"""

import os
import sys
import tempfile
import atexit
import logging
from typing import Optional, Dict

logger = logging.getLogger("InstanceManager")

# 10 Distinct, High-Contrast Color Themes for Instances
INSTANCE_COLORS = [
    {
        "name": "Vermelho Carmim",
        "start": "#DC2626",
        "end": "#EF4444",
        "border": "#F87171",
        "text": "#FFFFFF",
        "tray": "#EF4444"
    },  # Instância #1
    {
        "name": "Azul Royal",
        "start": "#1D4ED8",
        "end": "#3B82F6",
        "border": "#60A5FA",
        "text": "#FFFFFF",
        "tray": "#3B82F6"
    },  # Instância #2
    {
        "name": "Verde Esmeralda",
        "start": "#047857",
        "end": "#10B981",
        "border": "#34D399",
        "text": "#FFFFFF",
        "tray": "#10B981"
    },  # Instância #3
    {
        "name": "Âmbar / Laranja",
        "start": "#D97706",
        "end": "#F59E0B",
        "border": "#FBBF24",
        "text": "#FFFFFF",
        "tray": "#F59E0B"
    },  # Instância #4
    {
        "name": "Roxo Violeta",
        "start": "#7C3AED",
        "end": "#8B5CF6",
        "border": "#A78BFA",
        "text": "#FFFFFF",
        "tray": "#8B5CF6"
    },  # Instância #5
    {
        "name": "Ciano Oceano",
        "start": "#0E7490",
        "end": "#06B6D4",
        "border": "#22D3EE",
        "text": "#FFFFFF",
        "tray": "#06B6D4"
    },  # Instância #6
    {
        "name": "Rosa Magenta",
        "start": "#BE185D",
        "end": "#EC4899",
        "border": "#F472B6",
        "text": "#FFFFFF",
        "tray": "#EC4899"
    },  # Instância #7
    {
        "name": "Lima Neon",
        "start": "#4D7C0F",
        "end": "#84CC16",
        "border": "#A3E635",
        "text": "#FFFFFF",
        "tray": "#84CC16"
    },  # Instância #8
    {
        "name": "Índigo Profundo",
        "start": "#4338CA",
        "end": "#6366F1",
        "border": "#818CF8",
        "text": "#FFFFFF",
        "tray": "#6366F1"
    },  # Instância #9
    {
        "name": "Ouro Dourado",
        "start": "#B45309",
        "end": "#EAB308",
        "border": "#FDE047",
        "text": "#FFFFFF",
        "tray": "#EAB308"
    },  # Instância #10
]

def get_instance_color(instance_num: int) -> Dict[str, str]:
    """Return distinct color palette for the given instance number."""
    idx = max(0, instance_num - 1) % len(INSTANCE_COLORS)
    return INSTANCE_COLORS[idx]

class InstanceManager:
    _instance_number: int = 1
    _lock_file: str = ""

    @classmethod
    def get_instances_dir(cls) -> str:
        base = os.getenv("TEMP") or tempfile.gettempdir()
        d = os.path.join(base, "yt_espiao_instances")
        os.makedirs(d, exist_ok=True)
        return d

    @classmethod
    def _is_pid_running(cls, pid: int) -> bool:
        """Check if a process with the given PID is currently active."""
        if pid <= 0:
            return False
        if sys.platform == "win32":
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            SYNCHRONIZE = 0x00100000
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid)
            if not handle:
                return False
            try:
                exit_code = ctypes.c_ulong()
                if ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    STILL_ACTIVE = 259
                    if exit_code.value != STILL_ACTIVE:
                        return False
                return True
            except Exception:
                return False
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        else:
            try:
                os.kill(pid, 0)
                return True
            except Exception:
                return False

    @classmethod
    def claim_instance_number(cls) -> int:
        """
        Find the lowest available instance slot (#1, #2, #3, ...),
        register current PID, and return the instance number.
        """
        inst_dir = cls.get_instances_dir()
        current_pid = os.getpid()

        # Find the first available or stale slot starting strictly from 1
        for i in range(1, 100):
            lock_path = os.path.join(inst_dir, f"instance_{i}.pid")
            
            if os.path.exists(lock_path):
                is_stale = True
                try:
                    with open(lock_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            pid = int(content)
                            if pid == current_pid:
                                cls._instance_number = i
                                cls._lock_file = lock_path
                                return i
                            if cls._is_pid_running(pid):
                                is_stale = False
                except Exception:
                    is_stale = True

                if not is_stale:
                    # Slot i is actively used by a running process, proceed to next slot
                    continue

                # Stale file: try to remove
                try:
                    os.remove(lock_path)
                except Exception:
                    pass

            # Try to claim slot i
            try:
                with open(lock_path, "w", encoding="utf-8") as f:
                    f.write(str(current_pid))
                cls._instance_number = i
                cls._lock_file = lock_path
                atexit.register(cls.release_instance)
                return i
            except Exception:
                continue

        cls._instance_number = 1
        return 1

    @classmethod
    def release_instance(cls):
        """Release the claimed instance lock file upon exit."""
        if cls._lock_file and os.path.exists(cls._lock_file):
            try:
                os.remove(cls._lock_file)
            except Exception:
                pass

    @classmethod
    def get_instance_number(cls) -> int:
        return cls._instance_number
