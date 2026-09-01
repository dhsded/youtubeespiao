@echo off
title YouTube Espiao & Hunter Browser
cd /d "%~dp0"

if exist "dist\YouTubeEspiao\YouTubeEspiao.exe" (
    echo Iniciando o executavel YouTubeEspiao.exe...
    start "" "dist\YouTubeEspiao\YouTubeEspiao.exe"
) else if exist "dist\YouTube Espiao\YouTube Espiao.exe" (
    echo Iniciando o executavel YouTube Espiao.exe...
    start "" "dist\YouTube Espiao\YouTube Espiao.exe"
) else (
    echo Iniciando via Python...
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" main.py
    ) else (
        python main.py
    )
)
