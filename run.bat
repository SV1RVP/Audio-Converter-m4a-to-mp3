@echo off
chcp 65001 >nul
REM Copyright (C) 2026 Alexandros - Ermis Tsourapas (SV1RVP)
REM SPDX-License-Identifier: AGPL-3.0-only

setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1"
set "RUN_EXIT=%ERRORLEVEL%"
if not "%RUN_EXIT%"=="0" pause
exit /b %RUN_EXIT%
