@echo off
title YouTube Espiao & Hunter Browser
cd /d "%~dp0"

if exist "dist\YouTube Espiao\YouTube Espiao.exe" (
    echo Iniciando o executavel YouTube Espiao.exe...
    start "" "dist\YouTube Espiao\YouTube Espiao.exe"
) else (
    echo Executavel nao encontrado. Iniciando via Python...
    python main.py
)
