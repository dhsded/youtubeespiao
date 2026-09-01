@echo off
title Compilando YouTube Espiao Executavel
cd /d "%~dp0"
echo ============================================================
echo      CONSTRUINDO EXECUTAVEL YOUTUBE ESPIAO & HUNTER
echo ============================================================
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" build_exe.py
) else (
    python build_exe.py
)
echo.
if %ERRORLEVEL% equ 0 (
    echo ============================================================
    echo  [SUCESSO] O executavel foi gerado em:
    echo  dist\YouTubeEspiao\YouTubeEspiao.exe
    echo ============================================================
) else (
    echo [ERRO] Ocorreu uma falha durante a compilacao.
)
echo.
pause
