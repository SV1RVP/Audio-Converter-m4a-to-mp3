<# : install.bat - Audio Converter m4a to mp3 Automated Installer
@echo off
chcp 65001 >nul
REM Copyright (C) 2026 Alexandros - Ermis Tsourapas (SV1RVP)
REM SPDX-License-Identifier: AGPL-3.0-only

setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $code=[System.IO.File]::ReadAllText('%~f0', [System.Text.Encoding]::UTF8); & ([scriptblock]::Create($code)) '%~dp0'"
set "INSTALL_EXIT=%ERRORLEVEL%"
echo.
pause
exit /b %INSTALL_EXIT%
: end batch / begin powershell #>

param([string]$ProjectDir = $PSScriptRoot)
if (-not $ProjectDir) { $ProjectDir = (Get-Location).Path }
$ProjectDir = $ProjectDir.TrimEnd('\')

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$VenvDir = Join-Path $ProjectDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$Requirements = Join-Path $ProjectDir "requirements.txt"
$FfmpegZipUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$FfmpegHashUrl = "$FfmpegZipUrl.sha256"
$GitHubLatestReleaseApi = "https://api.github.com/repos/GyanD/codexffmpeg/releases/latest"
$WebHeaders = @{ "User-Agent" = "AudioConverter-Installer/$((Get-Date).Year)" }

function Invoke-DownloadWithRetry {
    param(
        [Parameter(Mandatory = $true)][string]$Uri,
        [Parameter(Mandatory = $true)][string]$OutFile,
        [hashtable]$Headers = @{},
        [int]$Attempts = 3
    )

    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        try {
            $parameters = @{
                Uri = $Uri
                OutFile = $OutFile
                UseBasicParsing = $true
            }
            if ($Headers.Count -gt 0) {
                $parameters["Headers"] = $Headers
            }
            Invoke-WebRequest @parameters
            return
        }
        catch {
            if ($attempt -eq $Attempts) {
                throw
            }
            Write-Host "  Download failed. Retrying ($($attempt + 1)/$Attempts)..." -ForegroundColor Yellow
            Start-Sleep -Seconds (2 * $attempt)
        }
    }
}

function Invoke-GitHubApiWithRetry {
    param([int]$Attempts = 3)

    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        try {
            return Invoke-RestMethod -Uri $GitHubLatestReleaseApi -Headers $WebHeaders -UseBasicParsing
        }
        catch {
            if ($attempt -eq $Attempts) {
                throw
            }
            Write-Host "  GitHub API did not respond. Retrying ($($attempt + 1)/$Attempts)..." -ForegroundColor Yellow
            Start-Sleep -Seconds (2 * $attempt)
        }
    }
}

function Get-FfmpegPackage {
    param(
        [Parameter(Mandatory = $true)][string]$ArchivePath,
        [Parameter(Mandatory = $true)][string]$HashPath
    )

    try {
        Write-Host "Downloading FFmpeg from gyan.dev..."
        Invoke-DownloadWithRetry -Uri $FfmpegZipUrl -OutFile $ArchivePath
        Invoke-DownloadWithRetry -Uri $FfmpegHashUrl -OutFile $HashPath
        return "gyan.dev"
    }
    catch {
        Write-Host "gyan.dev is unavailable. Trying official GitHub mirror..." -ForegroundColor Yellow
        Write-Host "  Reason: $($_.Exception.Message)" -ForegroundColor DarkYellow
        Remove-Item -LiteralPath $ArchivePath, $HashPath -Force -ErrorAction SilentlyContinue
    }

    $release = Invoke-GitHubApiWithRetry
    $zipAssets = @(
        $release.assets | Where-Object {
            $_.name -match '^ffmpeg-[0-9]+(\.[0-9]+)+-essentials_build\.zip$'
        }
    )
    if ($zipAssets.Count -lt 1) {
        throw "Could not find FFmpeg essentials ZIP in the latest GitHub release."
    }

    $zipAsset = $zipAssets | Select-Object -First 1
    $hashAsset = @(
        $release.assets | Where-Object {
            $_.name -eq "$($zipAsset.name).sha256"
        }
    ) | Select-Object -First 1

    Write-Host "Downloading FFmpeg $($release.tag_name) from GitHub..."
    Invoke-DownloadWithRetry -Uri $zipAsset.browser_download_url -OutFile $ArchivePath -Headers $WebHeaders

    if ($hashAsset) {
        Invoke-DownloadWithRetry -Uri $hashAsset.browser_download_url -OutFile $HashPath -Headers $WebHeaders
    }
    elseif (
        ($zipAsset.PSObject.Properties.Name -contains "digest") -and
        $zipAsset.digest -match '^sha256:([A-Fa-f0-9]{64})$'
    ) {
        Set-Content -LiteralPath $HashPath -Value $Matches[1] -Encoding ASCII
    }
    else {
        throw "GitHub release does not contain SHA-256 for the FFmpeg ZIP."
    }

    return "GitHub mirror"
}

function Install-PortableFfmpeg {
    $requiredTools = @("ffmpeg.exe", "ffprobe.exe")
    $missingTools = @(
        $requiredTools | Where-Object {
            -not (Test-Path -LiteralPath (Join-Path $ProjectDir $_))
        }
    )

    if (-not $missingTools) {
        Write-Host "Checking portable FFmpeg: OK"
        return
    }

    Write-Host "Portable FFmpeg is missing and will be installed automatically." -ForegroundColor Yellow
    $tempBase = [System.IO.Path]::GetTempPath()
    $tempRoot = Join-Path $tempBase ("audio-converter-ffmpeg-" + [guid]::NewGuid().ToString("N"))
    $archivePath = Join-Path $tempRoot "ffmpeg.zip"
    $hashPath = Join-Path $tempRoot "ffmpeg.zip.sha256"

    New-Item -ItemType Directory -Path $tempRoot | Out-Null
    try {
        $downloadSource = Get-FfmpegPackage -ArchivePath $archivePath -HashPath $hashPath

        $hashText = Get-Content -LiteralPath $hashPath -Raw
        $hashMatch = [regex]::Match($hashText, "[A-Fa-f0-9]{64}")
        if (-not $hashMatch.Success) {
            throw "Could not read SHA-256 hash for FFmpeg."
        }

        $expectedHash = $hashMatch.Value.ToUpperInvariant()
        $actualHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToUpperInvariant()
        if ($actualHash -ne $expectedHash) {
            throw "FFmpeg SHA-256 checksum verification failed. Download rejected."
        }

        Write-Host "SHA-256 Verification: OK"
        $extractDir = Join-Path $tempRoot "extracted"
        Expand-Archive -LiteralPath $archivePath -DestinationPath $extractDir

        foreach ($tool in $requiredTools) {
            $matches = @(Get-ChildItem -LiteralPath $extractDir -Filter $tool -File -Recurse)
            if ($matches.Count -ne 1) {
                throw "Could not find exactly one $tool in the FFmpeg package."
            }
            Copy-Item -LiteralPath $matches[0].FullName -Destination (Join-Path $ProjectDir $tool) -Force
        }

        Write-Host "FFmpeg installation from $($downloadSource): OK"
    }
    finally {
        $resolvedTempBase = [System.IO.Path]::GetFullPath($tempBase)
        $resolvedTempRoot = [System.IO.Path]::GetFullPath($tempRoot)
        $safePrefix = "audio-converter-ffmpeg-"
        if (
            $resolvedTempRoot.StartsWith($resolvedTempBase, [System.StringComparison]::OrdinalIgnoreCase) -and
            (Split-Path -Leaf $resolvedTempRoot).StartsWith($safePrefix, [System.StringComparison]::OrdinalIgnoreCase) -and
            (Test-Path -LiteralPath $resolvedTempRoot)
        ) {
            Remove-Item -LiteralPath $resolvedTempRoot -Recurse -Force
        }
    }
}

function Find-Python312 {
    $pyLauncher = Get-Command "py.exe" -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        try {
            & $pyLauncher.Source -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"
            if ($LASTEXITCODE -eq 0) {
                return @($pyLauncher.Source, "-3.12")
            }
        }
        catch {}
    }

    $python = Get-Command "python.exe" -ErrorAction SilentlyContinue
    if ($python) {
        try {
            & $python.Source -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"
            if ($LASTEXITCODE -eq 0) {
                return @($python.Source)
            }
        }
        catch {}
    }

    $knownPython = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"
    if (Test-Path -LiteralPath $knownPython) {
        return @($knownPython)
    }

    return $null
}

try {
    Write-Host ""
    Write-Host "=== Audio Converter m4a to mp3 - Installation ===" -ForegroundColor Cyan

    Install-PortableFfmpeg

    $pythonCommand = @(Find-Python312)
    if (-not $pythonCommand) {
        $winget = Get-Command "winget.exe" -ErrorAction SilentlyContinue
        if (-not $winget) {
            throw "Python 3.12 and winget were not found. Please install Python 3.12 from python.org and run install.bat again."
        }

        Write-Host "Python 3.12 was not found. Installing automatically via winget..." -ForegroundColor Yellow
        & $winget.Source install --id Python.Python.3.12 --exact --scope user --silent --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            throw "Python 3.12 installation via winget failed with exit code $LASTEXITCODE."
        }

        $pythonCommand = @(Find-Python312)
        if (-not $pythonCommand) {
            throw "Python was installed but could not be detected. Please close this window and run install.bat again."
        }
    }
    else {
        Write-Host "Checking Python 3.12: OK"
    }

    if (-not (Test-Path -LiteralPath $VenvPython)) {
        Write-Host "Creating virtual environment (.venv)..."
        $pythonExe = $pythonCommand[0]
        $pythonArgs = @()
        if ($pythonCommand.Count -gt 1) {
            $pythonArgs = $pythonCommand[1..($pythonCommand.Count - 1)]
        }
        & $pythonExe @pythonArgs -m venv $VenvDir
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create .venv virtual environment."
        }
    }
    else {
        Write-Host "Checking virtual environment (.venv): OK"
    }

    Write-Host "Installing Python dependencies into .venv..."
    & $VenvPython -m pip install --disable-pip-version-check -r $Requirements
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install Python dependencies."
    }

    & $VenvPython -c "import json, subprocess, tkinter; from tkinterdnd2 import DND_FILES, TkinterDnD; tkinter.Tcl()"
    if ($LASTEXITCODE -ne 0) {
        throw "Verification of Python, Tkinter, and Drag & Drop failed."
    }
    Write-Host "Verification (Python/Tkinter/Drag and Drop): OK"

    Write-Host ""
    Write-Host "Installation completed successfully." -ForegroundColor Green
    Write-Host "Double-click run.bat to launch Audio Converter m4a to mp3."
}
catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please check your Internet connection and run install.bat again." -ForegroundColor Yellow
    exit 1
}
