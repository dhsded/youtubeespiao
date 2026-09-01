"""
Multi-Instance Manager for YouTube Espião & Hunter Browser.
Features:
- Dynamic instance numbering (#1, #2, #3, ...) based on active running processes.
- Automatic cleanup of stale lock files.
- Chromium profile data isolation per instance to avoid file locks.
- Clean release of instance slot on exit.
"""

import os
import sys
import tempfile
import atexit
import logging
from typing import Optional

logger = logging.getLogger("InstanceManager")

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
        """Check if a process with the given PID is currently active on the OS."""
        if pid <= 0:
            return False
        if sys.platform == "win32":
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if handle:
                exit_code = ctypes.c_ulong()
                ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
                ctypes.windll.kernel32.CloseHandle(handle)
                return exit_code.value == STILL_ACTIVE
            return False
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

        # 1. Clean up stale lock files from terminated processes
        for i in range(1, 100):
            lock_path = os.path.join(inst_dir, f"instance_{i}.pid")
            if os.path.exists(lock_path):
                try:
                    with open(lock_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            pid = int(content)
                            if not cls._is_pid_running(pid):
                                try:
                                    os.remove(lock_path)
                                except Exception:
                                    pass
                except Exception:
                    pass

        # 2. Claim lowest available slot
        for i in range(1, 100):
            lock_path = os.path.join(inst_dir, f"instance_{i}.pid")
            if not os.path.exists(lock_path):
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
