# Copyright (C) 2026 Alexandros - Ermis Tsourapas (SV1RVP)
# SPDX-License-Identifier: AGPL-3.0-only

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding

$ProjectDir = $PSScriptRoot
if (-not $ProjectDir) {
    if ($MyInvocation.MyCommand.Path) {
        $ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    } else {
        $ProjectDir = (Get-Location).Path
    }
}

$Installer = Join-Path $ProjectDir "install.ps1"
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
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Installer
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
