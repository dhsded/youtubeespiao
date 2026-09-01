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
sys.argv.append(f"--user-data-dir={profile_dir}")
sys.argv.append(f"--disk-cache-dir={profile_dir}")
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

    # Set App Icon
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "assets", "icon.png")
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
