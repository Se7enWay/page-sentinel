@echo off
title Page Sentinel - Web Monitor
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo Starting Page Sentinel...
python sentinel.py
if errorlevel 1 (
    echo.
    echo [ERROR] Page Sentinel exited with an error.
    pause
)
