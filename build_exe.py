import sys
import os

python_exe = sys.executable
default_py = r"C:\Users\Diego Dutra\AppData\Local\Programs\Python\Python312\python.exe"
if os.path.exists(default_py):
    python_exe = default_py

sys.executable = python_exe
if hasattr(sys, '_base_executable'):
    sys._base_executable = python_exe
sys._pyi_isolated_subprocess = True

print(f"[*] Building YouTube Espião Executable...")
print(f"[*] Python Executable: {sys.executable}")

import PyInstaller.__main__

def build():
    spec_file = "YoutubeEspiao.spec"
    if os.path.exists(spec_file):
        args = [spec_file, "--noconfirm", "--clean"]
    else:
        args = [
            "main.py",
            "--noconfirm",
            "--onedir",
            "--windowed",
            "--name=YouTube Espiao",
            "--icon=assets/icon.ico",
            "--add-data=assets;assets",
            "--collect-all=PyQt6",
            "--collect-all=PyQt6_WebEngine",
            "--collect-all=scrapetube",
            "--collect-all=yt_dlp",
            "--collect-all=tldextract",
            "--collect-all=dns",
            "--collect-all=whois"
        ]
    PyInstaller.__main__.run(args)
    print("\n[+] Build completed successfully! Executable is located in dist/YouTube Espiao/YouTube Espiao.exe")

if __name__ == "__main__":
    build()
