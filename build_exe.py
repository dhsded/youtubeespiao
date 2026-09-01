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
    PyInstaller.__main__.run([
        spec_file,
        "--noconfirm",
        "--clean"
    ])
    print("\n[+] Build completed successfully! Executable is located in dist/YouTubeEspiao/YouTubeEspiao.exe")

if __name__ == "__main__":
    build()
