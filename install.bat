@echo off
chcp 65001 >nul
REM Copyright (C) 2026 Alexandros - Ermis Tsourapas (SV1RVP)
REM SPDX-License-Identifier: AGPL-3.0-only

setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
set "INSTALL_EXIT=%ERRORLEVEL%"
echo.
pause
exit /b %INSTALL_EXIT%
