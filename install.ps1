# Copyright (C) 2026 Alexandros - Ermis Tsourapas (SV1RVP)
# SPDX-License-Identifier: AGPL-3.0-only

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ProjectDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$Requirements = Join-Path $ProjectDir "requirements.txt"
$FfmpegZipUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$FfmpegHashUrl = "$FfmpegZipUrl.sha256"
$GitHubLatestReleaseApi = "https://api.github.com/repos/GyanD/codexffmpeg/releases/latest"
$WebHeaders = @{ "User-Agent" = "AudioConverterPro-Installer/$((Get-Date).Year)" }

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
            Write-Host "  Η λήψη απέτυχε. Νέα προσπάθεια $($attempt + 1)/$Attempts..." -ForegroundColor Yellow
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
            Write-Host "  Το GitHub API δεν απάντησε. Νέα προσπάθεια $($attempt + 1)/$Attempts..." -ForegroundColor Yellow
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
        Write-Host "Λήψη FFmpeg από gyan.dev..."
        Invoke-DownloadWithRetry -Uri $FfmpegZipUrl -OutFile $ArchivePath
        Invoke-DownloadWithRetry -Uri $FfmpegHashUrl -OutFile $HashPath
        return "gyan.dev"
    }
    catch {
        Write-Host "Το gyan.dev δεν είναι διαθέσιμο. Δοκιμή του επίσημου GitHub mirror..." -ForegroundColor Yellow
        Write-Host "  Αιτία: $($_.Exception.Message)" -ForegroundColor DarkYellow
        Remove-Item -LiteralPath $ArchivePath, $HashPath -Force -ErrorAction SilentlyContinue
    }

    $release = Invoke-GitHubApiWithRetry
    $zipAssets = @(
        $release.assets | Where-Object {
            $_.name -match '^ffmpeg-[0-9]+(\.[0-9]+)+-essentials_build\.zip$'
        }
    )
    if ($zipAssets.Count -lt 1) {
        throw "Δεν βρέθηκε FFmpeg essentials ZIP στο τελευταίο GitHub release."
    }

    $zipAsset = $zipAssets | Select-Object -First 1
    $hashAsset = @(
        $release.assets | Where-Object {
            $_.name -eq "$($zipAsset.name).sha256"
        }
    ) | Select-Object -First 1

    Write-Host "Λήψη FFmpeg $($release.tag_name) από GitHub..."
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
        throw "Το GitHub release δεν περιέχει SHA-256 για το FFmpeg ZIP."
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
        Write-Host "Έλεγχος portable FFmpeg: OK"
        return
    }

    Write-Host "Το portable FFmpeg λείπει και θα εγκατασταθεί αυτόματα." -ForegroundColor Yellow
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
            throw "Δεν ήταν δυνατή η ανάγνωση του SHA-256 του FFmpeg."
        }

        $expectedHash = $hashMatch.Value.ToUpperInvariant()
        $actualHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToUpperInvariant()
        if ($actualHash -ne $expectedHash) {
            throw "Ο έλεγχος SHA-256 του FFmpeg απέτυχε. Η λήψη απορρίφθηκε."
        }

        Write-Host "Έλεγχος SHA-256: OK"
        $extractDir = Join-Path $tempRoot "extracted"
        Expand-Archive -LiteralPath $archivePath -DestinationPath $extractDir

        foreach ($tool in $requiredTools) {
            $matches = @(Get-ChildItem -LiteralPath $extractDir -Filter $tool -File -Recurse)
            if ($matches.Count -ne 1) {
                throw "Δεν βρέθηκε ακριβώς ένα $tool μέσα στο πακέτο FFmpeg."
            }
            Copy-Item -LiteralPath $matches[0].FullName -Destination (Join-Path $ProjectDir $tool) -Force
        }

        Write-Host "Εγκατάσταση FFmpeg από $($downloadSource): OK"
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
    Write-Host "=== Audio Converter m4a to mp3 - Εγκατάσταση ===" -ForegroundColor Cyan

    Install-PortableFfmpeg

    $pythonCommand = @(Find-Python312)
    if (-not $pythonCommand) {
        $winget = Get-Command "winget.exe" -ErrorAction SilentlyContinue
        if (-not $winget) {
            throw "Δεν βρέθηκε Python 3.12 ούτε winget. Εγκατάστησε την Python 3.12 από το python.org και εκτέλεσε ξανά το install.bat."
        }

        Write-Host "Η Python 3.12 δεν βρέθηκε. Αυτόματη εγκατάσταση μέσω winget..." -ForegroundColor Yellow
        & $winget.Source install --id Python.Python.3.12 --exact --scope user --silent --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            throw "Η εγκατάσταση της Python 3.12 απέτυχε με κωδικό $LASTEXITCODE."
        }

        $pythonCommand = @(Find-Python312)
        if (-not $pythonCommand) {
            throw "Η Python εγκαταστάθηκε αλλά δεν εντοπίστηκε. Κλείσε το παράθυρο και εκτέλεσε ξανά το install.bat."
        }
    }
    else {
        Write-Host "Έλεγχος Python 3.12: OK"
    }

    if (-not (Test-Path -LiteralPath $VenvPython)) {
        Write-Host "Δημιουργία του virtual environment .venv..."
        $pythonExe = $pythonCommand[0]
        $pythonArgs = @()
        if ($pythonCommand.Count -gt 1) {
            $pythonArgs = $pythonCommand[1..($pythonCommand.Count - 1)]
        }
        & $pythonExe @pythonArgs -m venv $VenvDir
        if ($LASTEXITCODE -ne 0) {
            throw "Η δημιουργία του .venv απέτυχε."
        }
    }
    else {
        Write-Host "Έλεγχος virtual environment .venv: OK"
    }

    Write-Host "Έλεγχος Python dependencies μέσα στο .venv..."
    & $VenvPython -m pip install --disable-pip-version-check -r $Requirements
    if ($LASTEXITCODE -ne 0) {
        throw "Η εγκατάσταση των Python dependencies απέτυχε."
    }

    & $VenvPython -c "import json, subprocess, tkinter; from tkinterdnd2 import DND_FILES, TkinterDnD; tkinter.Tcl()"
    if ($LASTEXITCODE -ne 0) {
        throw "Ο τελικός έλεγχος Python και Tkinter απέτυχε."
    }
    Write-Host "Έλεγχος Python/Tkinter/Drag and Drop: OK"

    Write-Host ""
    Write-Host "Η εγκατάσταση ολοκληρώθηκε επιτυχώς." -ForegroundColor Green
    Write-Host "Άνοιξε το run.bat για να ξεκινήσεις την εφαρμογή."
}
catch {
    Write-Host ""
    Write-Host "ΣΦΑΛΜΑ: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Έλεγξε τη σύνδεση Internet και εκτέλεσε ξανά το install.bat." -ForegroundColor Yellow
    exit 1
}
