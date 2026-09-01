"""
YouTube Espião & Hunter Browser.
Ponto de entrada principal da aplicação desktop com suporte a múltiplas instâncias concorrentes.
"""

import sys
import os
import tempfile
import logging
import ctypes

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# Global Exception Catcher to guarantee zero silent crashes
def _handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    import traceback
    err = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.error(f"FATAL UNCAUGHT EXCEPTION: {err}")

sys.excepthook = _handle_unhandled_exception

try:
    import threading
    threading.excepthook = lambda args: logging.error(f"THREAD EXCEPTION: {args.exc_type}: {args.exc_value}")
except Exception:
    pass

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Multi-Instance Registration & Chromium Profile Isolation
from core.instance_manager import InstanceManager
instance_num = InstanceManager.claim_instance_number()

# Set isolated Chromium user data directory before QtWebEngine initializes
profile_dir = os.path.join(tempfile.gettempdir(), f"yt_espiao_profile_{instance_num}_{os.getpid()}")
os.makedirs(profile_dir, exist_ok=True)

# Optimized Chromium arguments for low-resource background multi-instance execution
sys.argv.extend([
    f"--user-data-dir={profile_dir}",
    f"--disk-cache-dir={profile_dir}",
    "--disable-background-timer-throttling=false",
    "--disable-renderer-backgrounding=false",
    "--disable-features=TranslateUI,AutofillServerCommunication",
    "--disable-hang-monitor",
    "--disable-sync",
    "--disable-default-apps",
    "--renderer-process-limit=2",
    "--js-flags=--max-old-space-size=128",
    "--mute-audio"
])
os.environ["QTWEBENGINE_STORAGE_PATH"] = profile_dir

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow

def main():
    # Set Windows App ID for taskbar icon
    if sys.platform == "win32":
        try:
            myappid = f"youtube.espiao.hunter.browser.{instance_num}"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    # Configure high-DPI settings
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Espião & Hunter Browser")
    app.setApplicationDisplayName(f"YouTube Espião #{instance_num}")
    app.setQuitOnLastWindowClosed(False)

    # Parse CLI launch arguments for batch multi-instance automation
    target_arg = None
    autostart_arg = False
    args_list = list(sys.argv)
    if "--target" in args_list:
        try:
            t_idx = args_list.index("--target")
            if t_idx + 1 < len(args_list):
                target_arg = args_list[t_idx + 1]
        except Exception:
            pass
    if "--autostart" in args_list:
        autostart_arg = True

    window = MainWindow(initial_target=target_arg, autostart=autostart_arg)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
