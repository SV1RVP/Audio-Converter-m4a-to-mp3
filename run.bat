<# : run.bat - Audio Converter m4a to mp3 Launcher
@echo off
chcp 65001 >nul
REM Copyright (C) 2026 Alexandros - Ermis Tsourapas (SV1RVP)
REM SPDX-License-Identifier: AGPL-3.0-only

setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $code=[System.IO.File]::ReadAllText('%~f0', [System.Text.Encoding]::UTF8); & ([scriptblock]::Create($code)) '%~dp0'"
set "RUN_EXIT=%ERRORLEVEL%"
if not "%RUN_EXIT%"=="0" pause
exit /b %RUN_EXIT%
: end batch / begin powershell #>

param([string]$ProjectDir = $PSScriptRoot)
if (-not $ProjectDir) { $ProjectDir = (Get-Location).Path }
$ProjectDir = $ProjectDir.TrimEnd('\')

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding

$Installer = Join-Path $ProjectDir "install.bat"
$VenvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$Application = Join-Path $ProjectDir "audio_converter.py"
$Ffmpeg = Join-Path $ProjectDir "ffmpeg.exe"
$Ffprobe = Join-Path $ProjectDir "ffprobe.exe"

try {
    $dragAndDropReady = $false
    if (Test-Path -LiteralPath $VenvPython) {
        & $VenvPython -c "import tkinterdnd2" 2>$null
        $dragAndDropReady = $LASTEXITCODE -eq 0
    }

    $needsInstallation =
        -not (Test-Path -LiteralPath $VenvPython) -or
        -not (Test-Path -LiteralPath $Ffmpeg) -or
        -not (Test-Path -LiteralPath $Ffprobe) -or
        -not $dragAndDropReady

    if ($needsInstallation) {
        Write-Host "Missing .venv or FFmpeg. Starting automated installation..." -ForegroundColor Yellow
        & cmd.exe /c (Join-Path $ProjectDir "install.bat")
        if ($LASTEXITCODE -ne 0) {
            throw "Installation could not be completed."
        }
    }

    foreach ($requiredFile in @($VenvPython, $Application, $Ffmpeg, $Ffprobe)) {
        if (-not (Test-Path -LiteralPath $requiredFile)) {
            throw "Missing required file: $requiredFile"
        }
    }

    Write-Host "Starting Audio Converter m4a to mp3..." -ForegroundColor Cyan
    & $VenvPython $Application
    if ($LASTEXITCODE -ne 0) {
        throw "Application exited with code $LASTEXITCODE."
    }
}
catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
