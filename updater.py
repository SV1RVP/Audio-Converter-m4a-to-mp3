# Copyright (C) 2026 Alexandros - Ermis Tsourapas (SV1RVP)
# SPDX-License-Identifier: AGPL-3.0-only

"""
Audio Converter m4a to mp3 - GitHub Auto-Updater Module
Provides zero-dependency version checking and seamless self-update from GitHub.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("AudioConverterPro.Updater")

# Configurable GitHub Repository (Owner/Repo)
# Set this to the repository path provided on GitHub
DEFAULT_GITHUB_REPO = "SV1RVP/Audio-Converter-m4a-to-mp3"

APP_DIR = Path(__file__).resolve().parent
VERSION_FILE = APP_DIR / "VERSION"


def get_local_version() -> str:
    """Reads the current version from the VERSION file."""
    try:
        if VERSION_FILE.exists():
            return VERSION_FILE.read_text(encoding="utf-8").strip()
    except Exception as e:
        logger.error("Error reading VERSION file: %s", e)
    return "1.3.1"


def parse_semver(version_str: str) -> Tuple[int, ...]:
    """Parses semantic version string like '1.2.0' or 'v1.2.0' into a tuple of ints."""
    try:
        clean = str(version_str).strip().lstrip("v")
        parts = []
        for part in clean.split("."):
            num = ""
            for ch in part:
                if ch.isdigit():
                    num += ch
                else:
                    break
            parts.append(int(num) if num else 0)
        return tuple(parts)
    except Exception:
        return (0, 0, 0)


def check_for_updates(
    current_version: Optional[str] = None,
    github_repo: Optional[str] = None,
    timeout: int = 8,
    lang: str = "en",
) -> Dict[str, Any]:
    """
    Checks GitHub for newer releases.
    Uses standard library urllib (zero external dependencies).
    """
    if not current_version:
        current_version = get_local_version()

    repo = (github_repo or DEFAULT_GITHUB_REPO).strip()
    if not repo:
        msg = (
            "No GitHub repository URL configured."
            if lang == "en"
            else "Δεν έχει οριστεί GitHub repository URL."
        )
        return {
            "status": "error",
            "update_available": False,
            "message": msg,
            "current_version": current_version,
            "latest_version": current_version,
        }

    # Normalize repo format (handle full URL or owner/repo)
    if "github.com/" in repo:
        repo = repo.split("github.com/")[-1].strip("/").rstrip(".git")

    headers = {
        "User-Agent": "AudioConverterPro-Updater/1.2 (Windows)",
        "Accept": "application/vnd.github.v3+json",
    }

    # 1. Attempt checking latest release via GitHub API
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    default_no_notes = (
        "No release notes provided."
        if lang == "en"
        else "Δεν υπάρχουν σημειώσεις έκδοσης."
    )
    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                tag_name = data.get("tag_name", "").lstrip("v").strip()
                release_notes = data.get("body") or default_no_notes
                html_url = data.get("html_url", f"https://github.com/{repo}/releases")
                zip_url = data.get("zipball_url") or f"https://github.com/{repo}/archive/refs/heads/main.zip"

                if tag_name:
                    is_newer = parse_semver(tag_name) > parse_semver(current_version)
                    return {
                        "status": "success",
                        "update_available": is_newer,
                        "current_version": current_version,
                        "latest_version": tag_name,
                        "release_notes": release_notes,
                        "html_url": html_url,
                        "download_url": zip_url,
                        "repo": repo,
                    }
    except Exception as e:
        logger.debug("GitHub Releases API unavailable (%s), trying raw VERSION file...", e)

    # 2. Fallback: Check raw VERSION file from main branch
    raw_version_url = f"https://raw.githubusercontent.com/{repo}/main/VERSION"
    try:
        req = urllib.request.Request(raw_version_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                raw_ver = response.read().decode("utf-8").strip().lstrip("v")
                is_newer = parse_semver(raw_ver) > parse_semver(current_version)
                fb_notes = (
                    f"New version {raw_ver} available on GitHub."
                    if lang == "en"
                    else f"Νέα έκδοση {raw_ver} διαθέσιμη στο GitHub."
                )
                return {
                    "status": "success",
                    "update_available": is_newer,
                    "current_version": current_version,
                    "latest_version": raw_ver,
                    "release_notes": fb_notes,
                    "html_url": f"https://github.com/{repo}",
                    "download_url": f"https://github.com/{repo}/archive/refs/heads/main.zip",
                    "repo": repo,
                }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            msg_404 = (
                f"Repository '{repo}' was not found on GitHub (404)."
                if lang == "en"
                else f"Το αποθετήριο '{repo}' δεν βρέθηκε στο GitHub (404)."
            )
            return {
                "status": "error",
                "update_available": False,
                "message": msg_404,
                "current_version": current_version,
                "latest_version": current_version,
            }
        logger.debug("Raw VERSION fetch failed: %s", e)
    except Exception as e:
        logger.debug("Raw VERSION fetch failed: %s", e)

    err_msg = (
        "Could not connect to GitHub to check for updates."
        if lang == "en"
        else "Δεν ήταν δυνατή η σύνδεση με το GitHub για έλεγχο ενημερώσεων."
    )
    return {
        "status": "error",
        "update_available": False,
        "message": err_msg,
        "current_version": current_version,
        "latest_version": current_version,
    }


def download_and_launch_updater(
    download_url: str,
    target_dir: Optional[Path] = None,
    progress_callback=None,
    lang: str = "en",
) -> Tuple[bool, str]:
    """
    Downloads update archive and launches an external batch helper to replace files.
    Preserves settings.json, .venv, and downloaded ffmpeg binaries.
    """
    if target_dir is None:
        target_dir = APP_DIR

    zip_file = target_dir / "update_package.zip"
    helper_bat = target_dir / "update_helper.bat"

    try:
        headers = {"User-Agent": "AudioConverterPro-Updater/1.2 (Windows)"}
        req = urllib.request.Request(download_url, headers=headers)

        with urllib.request.urlopen(req, timeout=30) as response:
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 32768

            with open(zip_file, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        progress_callback(int((downloaded / total_size) * 100))

        # Create Windows update runner batch script
        script_content = f"""@echo off
chcp 65001 >nul
title Audio Converter m4a to mp3 - Ενημέρωση Εφαρμογής
cd /d "{target_dir}"

echo ============================================================
echo      Audio Converter m4a to mp3 - Εφαρμογή Ενημέρωσης
echo ============================================================
echo.
echo Αναμονή για τερματισμό της εφαρμογής...
timeout /t 2 /nobreak > nul

echo Εξαγωγή αρχείων ενημέρωσης...
if exist "_update_extract" rmdir /s /q "_update_extract"
powershell.exe -NoProfile -Command "Expand-Archive -Path '{zip_file.name}' -DestinationPath '_update_extract' -Force"

set "SRC_DIR="
for /d %%d in ("_update_extract\\*") do (
    set "SRC_DIR=%%d"
)

if defined SRC_DIR (
    echo Αντιγραφή νέων αρχείων κώδικα...
    REM Copy code and document files, excluding binaries and user environment
    xcopy /y /e /q "!SRC_DIR!\\*.py" "." >nul 2>&1
    xcopy /y /e /q "!SRC_DIR!\\*.md" "." >nul 2>&1
    xcopy /y /e /q "!SRC_DIR!\\*.bat" "." >nul 2>&1
    xcopy /y /q "!SRC_DIR!\\VERSION" "." >nul 2>&1
    xcopy /y /q "!SRC_DIR!\\pyproject.toml" "." >nul 2>&1
    xcopy /y /q "!SRC_DIR!\\requirements.txt" "." >nul 2>&1
    xcopy /y /q "!SRC_DIR!\\.gitignore" "." >nul 2>&1
    xcopy /y /q "!SRC_DIR!\\.gitattributes" "." >nul 2>&1
    if exist "install.ps1" del /f /q "install.ps1" >nul 2>&1
    if exist "run.ps1" del /f /q "run.ps1" >nul 2>&1
    echo [OK] Η ενημέρωση εφαρμόστηκε επιτυχώς!
) else (
    echo [ERROR] Αποτυχία εύρεσης αποσυμπιεσμένων αρχείων.
    pause
    exit /b 1
)

echo Καθαρισμός προσωρινών αρχείων...
if exist "{zip_file.name}" del /f /q "{zip_file.name}" >nul 2>&1
if exist "_update_extract" rmdir /s /q "_update_extract" >nul 2>&1

echo Επανεκκίνηση εφαρμογής...
timeout /t 1 /nobreak > nul
start "" run.bat
(goto) 2>nul & del "update_helper.bat" & exit
"""
        helper_bat.write_text(script_content, encoding="utf-8")

        # Launch the batch helper in a new command window and signal success
        subprocess.Popen(["cmd.exe", "/c", str(helper_bat)], shell=True)
        success_msg = (
            "Update launched successfully."
            if lang == "en"
            else "Η ενημέρωση ξεκίνησε επιτυχώς."
        )
        return True, success_msg

    except Exception as e:
        logger.error("Update download/launch failed: %s", e)
        if zip_file.exists():
            try:
                zip_file.unlink()
            except Exception:
                pass
        err_msg = (
            f"Error during update download: {e}"
            if lang == "en"
            else f"Σφάλμα κατά τη λήψη της ενημέρωσης: {e}"
        )
        return False, err_msg
