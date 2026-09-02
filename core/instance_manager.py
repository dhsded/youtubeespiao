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

# 10 Clean, Refined Accent Tones for Instances (YouTube Studio Aesthetic)
INSTANCE_COLORS = [
    {
        "name": "YouTube Red",
        "start": "#CC0000",
        "end": "#E50914",
        "border": "#FF4D4D",
        "text": "#FFFFFF",
        "tray": "#CC0000"
    },  # Instância #1
    {
        "name": "Studio Blue",
        "start": "#065FD4",
        "end": "#1A73E8",
        "border": "#4285F4",
        "text": "#FFFFFF",
        "tray": "#065FD4"
    },  # Instância #2
    {
        "name": "Studio Emerald",
        "start": "#0E8345",
        "end": "#137333",
        "border": "#34A853",
        "text": "#FFFFFF",
        "tray": "#0E8345"
    },  # Instância #3
    {
        "name": "Studio Amber",
        "start": "#B25000",
        "end": "#E37400",
        "border": "#FBBC04",
        "text": "#FFFFFF",
        "tray": "#B25000"
    },  # Instância #4
    {
        "name": "Studio Indigo",
        "start": "#5E35B1",
        "end": "#7E57C2",
        "border": "#9575CD",
        "text": "#FFFFFF",
        "tray": "#5E35B1"
    },  # Instância #5
    {
        "name": "Studio Teal",
        "start": "#00796B",
        "end": "#00897B",
        "border": "#26A69A",
        "text": "#FFFFFF",
        "tray": "#00796B"
    },  # Instância #6
    {
        "name": "Studio Crimson",
        "start": "#AD1457",
        "end": "#C2185B",
        "border": "#EC407A",
        "text": "#FFFFFF",
        "tray": "#AD1457"
    },  # Instância #7
    {
        "name": "Studio Cyan",
        "start": "#00838F",
        "end": "#0097A7",
        "border": "#26C6DA",
        "text": "#FFFFFF",
        "tray": "#00838F"
    },  # Instância #8
    {
        "name": "Studio Slate",
        "start": "#374151",
        "end": "#4B5563",
        "border": "#6B7280",
        "text": "#FFFFFF",
        "tray": "#4B5563"
    },  # Instância #9
    {
        "name": "Studio Bronze",
        "start": "#8D6E63",
        "end": "#A1887F",
        "border": "#BCAAA4",
        "text": "#FFFFFF",
        "tray": "#8D6E63"
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

    @classmethod
    def spawn_new_instance(cls) -> bool:
        """
        Spawns a new independent instance of the application in the background.
        Works seamlessly both when running from Python source (main.py) and from compiled PyInstaller EXE.
        """
        import subprocess
        try:
            flags = 0
            if sys.platform == "win32":
                flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

            if getattr(sys, "frozen", False):
                # Running as compiled PyInstaller executable
                exe_path = sys.executable
                subprocess.Popen([exe_path], creationflags=flags, close_fds=True)
            else:
                # Running from Python source
                script_path = os.path.abspath(sys.argv[0])
                if not script_path.endswith("main.py"):
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    script_path = os.path.join(base_dir, "main.py")
                subprocess.Popen([sys.executable, script_path], creationflags=flags, close_fds=True)

            logger.info("Successfully spawned new application instance process.")
            return True
        except Exception as e:
            logger.error(f"Failed to spawn new application instance: {e}")
            return False
