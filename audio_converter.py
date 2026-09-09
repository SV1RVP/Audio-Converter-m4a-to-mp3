# Copyright (C) 2026 Alexandros - Ermis Tsourapas (SV1RVP)
# SPDX-License-Identifier: AGPL-3.0-only

import json
import os
import queue
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser
from pathlib import Path

try:
    import updater
except ImportError:
    updater = None

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    DND_FILES = None
    TkinterDnD = None


APP_VERSION = "1.3.2"
# Configurable GitHub Repository (Owner/Repo ή URL). Μπορεί να τροποποιηθεί άμεσα.
GITHUB_REPO = "SV1RVP/Audio-Converter-m4a-to-mp3"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

BITRATE_LEVELS = [
    ("320k", "320 kbps — Maximum", "320 kbps — Μέγιστη"),
    ("256k", "256 kbps — Very High", "256 kbps — Πολύ υψηλή"),
    ("192k", "192 kbps — High", "192 kbps — Υψηλή"),
    ("128k", "128 kbps — Standard", "128 kbps — Κανονική"),
]


def get_bitrate_options_for_lang(lang: str) -> list:
    idx = 1 if lang == "en" else 2
    return [b[idx] for b in BITRATE_LEVELS]


def normalize_bitrate_code(value: str) -> str:
    """Takes either a bitrate code ('320k') or display string in any language and returns code ('320k')."""
    if not value:
        return "320k"
    for code, en_label, el_label in BITRATE_LEVELS:
        if value in (code, en_label, el_label):
            return code
    if "320" in value:
        return "320k"
    if "256" in value:
        return "256k"
    if "192" in value:
        return "192k"
    if "128" in value:
        return "128k"
    return "320k"


def get_bitrate_display(code: str, lang: str) -> str:
    code = normalize_bitrate_code(code)
    idx = 1 if lang == "en" else 2
    for item in BITRATE_LEVELS:
        if item[0] == code:
            return item[idx]
    return BITRATE_LEVELS[0][idx]


TRANSLATIONS = {
    "en": {
        "app_name": "Audio Converter m4a to mp3",
        "subtitle": "Batch convert M4A to MP3 or WAV",
        "check_updates": "🔄 Check",
        "checking_updates": "🔄 Checking...",
        "theme_light": "☀ Light",
        "theme_dark": "☾ Dark",
        "lang_name": "English",
        "lang_toggle_btn": "🇺🇸 EN",
        "card_files": "  1  Files to convert  ",
        "drop_text_dnd": "Drag and drop M4A files or folders here",
        "drop_text_nodnd": "Select one or more M4A files",
        "col_name": "File",
        "col_duration": "Duration",
        "col_size": "Size",
        "col_status": "Status",
        "col_progress": "Progress",
        "btn_add_files": "Add files…",
        "btn_remove_selected": "Remove selected",
        "btn_clear_list": "Clear list",
        "file_count_zero": "0 files",
        "file_count_single": "1 file",
        "file_count_multiple": "{count} files",
        "card_settings": "  2  Output settings  ",
        "lbl_format": "Format",
        "lbl_quality": "Quality",
        "lbl_folder": "Folder",
        "btn_browse": "Browse…",
        "output_hint": "Leave blank to save next to each source file.",
        "card_conversion": "  3  Batch conversion  ",
        "status_default": "Add one or more M4A files",
        "btn_convert_all": "Convert All",
        "btn_cancel": "Cancel",
        "btn_open_folder": "Open Folder",
        "footer_text": "v{version}  •  Alexandros - Ermis Tsourapas (SV1RVP)",
        "menu_help": "Help",
        "menu_language": "Language",
        "menu_check_updates": "Check for updates…",
        "menu_about": "About / Licenses",
        "status_reading": "Reading…",
        "status_ready": "Ready",
        "status_no_info": "No info",
        "status_converting_item": "Converting {current}/{total}",
        "status_completed_item": "Completed",
        "status_error_item": "Error",
        "status_canceled_item": "Canceled",
        "status_queued_item": "Queued",
        "status_skipped_item": "Skipped",
        "status_files_added": "Added {count} file(s)",
        "status_skipped": "Skipped: {details}",
        "skipped_invalid": "{count} invalid or non-M4A",
        "skipped_duplicates": "{count} duplicates",
        "status_list_cleared": "List cleared",
        "status_starting_conversion": "Starting conversion of {count} files…",
        "status_canceling": "Canceling queue…",
        "status_canceled_summary": "Queue canceled • {count} completed",
        "status_done_errors": "Completed with {count} error(s)",
        "status_done_success": "Successfully converted {count} files",
        "status_fatal_error": "Batch conversion failed",
        "dlg_browse_files_title": "Select M4A files",
        "dlg_file_type_m4a": "M4A audio",
        "dlg_file_type_all": "All files",
        "dlg_browse_output_title": "Select output folder",
        "dlg_no_files_title": "No files",
        "dlg_no_files_msg": "Please add at least one M4A file.",
        "dlg_ffmpeg_error_title": "FFmpeg Error",
        "dlg_ffmpeg_missing_msg": "Missing from application folder: {tools}",
        "dlg_output_not_found_title": "Error",
        "dlg_output_not_found_msg": "The output folder does not exist.",
        "dlg_overwrite_title": "Overwrite files",
        "dlg_overwrite_msg": "{count} output files already exist.\n\nOverwrite them and start conversion?",
        "dlg_queue_errors_title": "Queue completed with errors",
        "dlg_queue_errors_msg": "Success: {success}\nErrors: {errors}\n\n{details}",
        "dlg_queue_errors_more": "…and {count} more.",
        "dlg_conversion_done_title": "Conversion completed",
        "dlg_conversion_done_msg": "Successfully converted {count} files.",
        "dlg_open_folder_title": "Open Folder",
        "dlg_open_folder_no_files": "No completed files yet.",
        "dlg_open_folder_not_found": "Output files were not found.",
        "dlg_close_title": "Exit",
        "dlg_close_msg": "A conversion is in progress. Do you want to cancel and exit?",
        "dlg_about_title": "About / Licenses",
        "dlg_about_dnd_active": "active",
        "dlg_about_dnd_inactive": "not available",
        "dlg_update_available_title": "Audio Converter m4a to mp3 - Update Available",
        "dlg_update_new_version": "New Version Available!",
        "dlg_update_version_diff": "Current: v{current}  ➔  New: v{latest}",
        "dlg_update_changelog": "Release Notes (Changelog):",
        "dlg_update_no_notes": "No release details available.",
        "dlg_update_confirm_title": "Confirm Update",
        "dlg_update_confirm_msg": "Do you want to download and apply the update?\n\nThe application will download the package and restart automatically.",
        "dlg_update_downloading": "Downloading update package...",
        "dlg_update_error_title": "Update Error",
        "dlg_update_no_download_url": "Download link not found.",
        "dlg_update_up_to_date_title": "Update Check",
        "dlg_update_up_to_date_msg": "The application is up to date!\n\nCurrent version: v{version}\nRepository: {repo}",
        "dlg_update_failed_title": "Update Check",
        "dlg_update_failed_msg": "Could not check for updates.",
        "dlg_update_btn_apply": "⚡ Update Now",
        "dlg_update_btn_close": "Close",
    },
    "el": {
        "app_name": "Audio Converter m4a to mp3",
        "subtitle": "Πολλαπλή μετατροπή M4A σε MP3 ή WAV",
        "check_updates": "🔄 Έλεγχος",
        "checking_updates": "🔄 Έλεγχος...",
        "theme_light": "☀ Φωτεινό",
        "theme_dark": "☾ Σκούρο",
        "lang_name": "Ελληνικά",
        "lang_toggle_btn": "🇬🇷 ΕΛ",
        "card_files": "  1  Αρχεία προς μετατροπή  ",
        "drop_text_dnd": "Σύρε εδώ αρχεία ή φακέλους M4A",
        "drop_text_nodnd": "Επίλεξε ένα ή περισσότερα αρχεία M4A",
        "col_name": "Αρχείο",
        "col_duration": "Διάρκεια",
        "col_size": "Μέγεθος",
        "col_status": "Κατάσταση",
        "col_progress": "Πρόοδος",
        "btn_add_files": "Προσθήκη αρχείων…",
        "btn_remove_selected": "Αφαίρεση επιλεγμένων",
        "btn_clear_list": "Καθαρισμός λίστας",
        "file_count_zero": "0 αρχεία",
        "file_count_single": "1 αρχείο",
        "file_count_multiple": "{count} αρχεία",
        "card_settings": "  2  Ρυθμίσεις εξόδου  ",
        "lbl_format": "Format",
        "lbl_quality": "Ποιότητα",
        "lbl_folder": "Φάκελος",
        "btn_browse": "Επιλογή…",
        "output_hint": "Άφησέ το κενό για αποθήκευση δίπλα σε κάθε αρχικό αρχείο.",
        "card_conversion": "  3  Μαζική μετατροπή  ",
        "status_default": "Πρόσθεσε ένα ή περισσότερα αρχεία M4A",
        "btn_convert_all": "Μετατροπή όλων",
        "btn_cancel": "Ακύρωση",
        "btn_open_folder": "Άνοιγμα φακέλου",
        "footer_text": "v{version}  •  Alexandros - Ermis Tsourapas (SV1RVP)",
        "menu_help": "Βοήθεια",
        "menu_language": "Γλώσσα",
        "menu_check_updates": "Έλεγχος για ενημερώσεις…",
        "menu_about": "Σχετικά / Άδειες",
        "status_reading": "Ανάγνωση…",
        "status_ready": "Έτοιμο",
        "status_no_info": "Χωρίς πληροφορίες",
        "status_converting_item": "Μετατροπή {current}/{total}",
        "status_completed_item": "Ολοκληρώθηκε",
        "status_error_item": "Σφάλμα",
        "status_canceled_item": "Ακυρώθηκε",
        "status_queued_item": "Σε αναμονή",
        "status_skipped_item": "Δεν εκτελέστηκε",
        "status_files_added": "Προστέθηκαν {count} αρχεία",
        "status_skipped": "Παραλείφθηκαν: {details}",
        "skipped_invalid": "{count} μη έγκυρα ή μη-M4A",
        "skipped_duplicates": "{count} διπλότυπα",
        "status_list_cleared": "Η λίστα καθαρίστηκε",
        "status_starting_conversion": "Ξεκινά η μετατροπή {count} αρχείων…",
        "status_canceling": "Γίνεται ακύρωση της ουράς…",
        "status_canceled_summary": "Η ουρά ακυρώθηκε • {count} ολοκληρώθηκαν",
        "status_done_errors": "Ολοκληρώθηκε με {count} σφάλματα",
        "status_done_success": "Ολοκληρώθηκαν επιτυχώς {count} αρχεία",
        "status_fatal_error": "Η μαζική μετατροπή απέτυχε",
        "dlg_browse_files_title": "Επιλογή αρχείων M4A",
        "dlg_file_type_m4a": "Ήχος M4A",
        "dlg_file_type_all": "Όλα τα αρχεία",
        "dlg_browse_output_title": "Επιλογή φακέλου αποθήκευσης",
        "dlg_no_files_title": "Δεν υπάρχουν αρχεία",
        "dlg_no_files_msg": "Πρόσθεσε τουλάχιστον ένα M4A.",
        "dlg_ffmpeg_error_title": "Σφάλμα FFmpeg",
        "dlg_ffmpeg_missing_msg": "Λείπουν από τον φάκελο της εφαρμογής: {tools}",
        "dlg_output_not_found_title": "Σφάλμα",
        "dlg_output_not_found_msg": "Ο φάκελος αποθήκευσης δεν υπάρχει.",
        "dlg_overwrite_title": "Αντικατάσταση αρχείων",
        "dlg_overwrite_msg": "{count} αρχεία εξόδου υπάρχουν ήδη.\n\nΝα αντικατασταθούν και να ξεκινήσει η μετατροπή;",
        "dlg_queue_errors_title": "Η ουρά ολοκληρώθηκε με σφάλματα",
        "dlg_queue_errors_msg": "Επιτυχίες: {success}\nΣφάλματα: {errors}\n\n{details}",
        "dlg_queue_errors_more": "…και {count} ακόμη.",
        "dlg_conversion_done_title": "Η μετατροπή ολοκληρώθηκε",
        "dlg_conversion_done_msg": "Μετατράπηκαν επιτυχώς {count} αρχεία.",
        "dlg_open_folder_title": "Άνοιγμα φακέλου",
        "dlg_open_folder_no_files": "Δεν υπάρχει ακόμη ολοκληρωμένο αρχείο.",
        "dlg_open_folder_not_found": "Τα αρχεία εξόδου δεν βρέθηκαν.",
        "dlg_close_title": "Έξοδος",
        "dlg_close_msg": "Υπάρχει ουρά σε εξέλιξη. Θέλεις να ακυρωθεί και να κλείσει η εφαρμογή;",
        "dlg_about_title": "Σχετικά / Άδειες",
        "dlg_about_dnd_active": "ενεργό",
        "dlg_about_dnd_inactive": "μη διαθέσιμο",
        "dlg_update_available_title": "Audio Converter m4a to mp3 - Διαθέσιμη Ενημέρωση",
        "dlg_update_new_version": "Νέα Έκδοση Διαθέσιμη!",
        "dlg_update_version_diff": "Τρέχουσα: v{current}  ➔  Νέα: v{latest}",
        "dlg_update_changelog": "Σημειώσεις Έκδοσης (Changelog):",
        "dlg_update_no_notes": "Δεν υπάρχουν λεπτομέρειες.",
        "dlg_update_confirm_title": "Επιβεβαίωση Ενημέρωσης",
        "dlg_update_confirm_msg": "Θέλετε να προχωρήσετε σε λήψη και εφαρμογή της ενημέρωσης;\n\nΗ εφαρμογή θα κατεβάσει το πακέτο και θα επανεκκινηθεί αυτόματα.",
        "dlg_update_downloading": "Λήψη πακέτου ενημέρωσης...",
        "dlg_update_error_title": "Σφάλμα Ενημέρωσης",
        "dlg_update_no_download_url": "Δεν βρέθηκε σύνδεσμος λήψης.",
        "dlg_update_up_to_date_title": "Έλεγχος Ενημέρωσης",
        "dlg_update_up_to_date_msg": "Η εφαρμογή είναι ενημερωμένη!\n\nΤρέχουσα έκδοση: v{version}\nΑποθετήριο: {repo}",
        "dlg_update_failed_title": "Έλεγχος Ενημέρωσης",
        "dlg_update_failed_msg": "Δεν ήταν δυνατός ο έλεγχος ενημέρωσης.",
        "dlg_update_btn_apply": "⚡ Ενημέρωση Τώρα",
        "dlg_update_btn_close": "Κλείσιμο",
    },
}

THEMES = {
    "light": {
        "bg": "#f3f5f9",
        "card": "#ffffff",
        "text": "#172033",
        "muted": "#667085",
        "border": "#d8dee9",
        "input": "#ffffff",
        "accent": "#2563eb",
        "accent_hover": "#1d4ed8",
        "success": "#16803a",
        "warning": "#c46a09",
        "danger": "#c93636",
        "disabled": "#aab2c0",
        "progress_bg": "#dbe4f0",
    },
    "dark": {
        "bg": "#111827",
        "card": "#1f2937",
        "text": "#f3f4f6",
        "muted": "#a7b0bf",
        "border": "#374151",
        "input": "#111827",
        "accent": "#60a5fa",
        "accent_hover": "#3b82f6",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "danger": "#fb7185",
        "disabled": "#687386",
        "progress_bg": "#374151",
    },
}


class ConversionCanceled(Exception):
    pass


class AudioConverterApp:
    def __init__(self, root):
        self.root = root
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.ffmpeg_path = os.path.join(self.script_dir, "ffmpeg.exe")
        self.ffprobe_path = os.path.join(self.script_dir, "ffprobe.exe")
        self.settings_path = os.path.join(
            os.environ.get("LOCALAPPDATA", self.script_dir),
            "AudioConverterPro",
            "settings.json",
        )

        settings = self.load_settings()
        # Default language is English ("en") as requested
        self.language = settings.get("language", "en")
        if self.language not in ("en", "el"):
            self.language = "en"
        self.lang_var = tk.StringVar(value=self.language)

        self.root.title(f"{self.t('app_name')} v{APP_VERSION}")
        self.root.geometry("920x730")
        self.root.minsize(800, 650)

        # Set window icon if available
        logo_png_path = os.path.join(self.script_dir, "assets", "logo.png")
        if os.path.exists(logo_png_path):
            try:
                self._app_icon = tk.PhotoImage(file=logo_png_path)
                self.root.iconphoto(True, self._app_icon)
            except Exception:
                pass

        self.output_directory = tk.StringVar(value=settings.get("output_directory", ""))
        self.target_format = tk.StringVar(value=settings.get("target_format", "MP3"))

        raw_bitrate = settings.get("selected_bitrate", "320k")
        self.current_bitrate_code = normalize_bitrate_code(raw_bitrate)
        self.selected_bitrate = tk.StringVar(
            value=get_bitrate_display(self.current_bitrate_code, self.language)
        )

        self.theme_name = settings.get("theme", "light")
        if self.theme_name not in THEMES:
            self.theme_name = "light"

        self.status_text = tk.StringVar(value=self.t("status_default"))
        self.progress_text = tk.StringVar(value="0%")
        self.progress_value = tk.DoubleVar(value=0)

        self.file_records = {}
        self.item_to_key = {}
        self.next_item_id = 1
        self.result_queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.conversion_process = None
        self.completed_outputs = []
        self.is_converting = False
        self.dnd_enabled = DND_FILES is not None and TkinterDnD is not None

        self.style = ttk.Style(self.root)
        self.create_menu()
        self.create_widgets()
        self.apply_theme()
        self.toggle_bitrate_options()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(100, self.poll_worker_messages)
        self.root.after(2500, lambda: self.check_for_updates_ui(silent=True))

    def t(self, key: str, **kwargs) -> str:
        lang_dict = TRANSLATIONS.get(self.language, TRANSLATIONS["en"])
        text = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def load_settings(self):
        try:
            with open(self.settings_path, "r", encoding="utf-8") as settings_file:
                data = json.load(settings_file)
                return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save_settings(self):
        data = {
            "language": self.language,
            "theme": self.theme_name,
            "target_format": self.target_format.get(),
            "selected_bitrate": self.current_bitrate_code,
            "output_directory": self.output_directory.get().strip(),
        }
        try:
            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
            with open(self.settings_path, "w", encoding="utf-8") as settings_file:
                json.dump(data, settings_file, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def create_menu(self):
        self.menu_bar = tk.Menu(self.root, tearoff=False)

        # Language selection menu
        self.lang_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.lang_menu.add_radiobutton(
            label="EN (🇺🇸)",
            value="en",
            variable=self.lang_var,
            command=lambda: self.set_language("en"),
        )
        self.lang_menu.add_radiobutton(
            label="ΕΛ (🇬🇷)",
            value="el",
            variable=self.lang_var,
            command=lambda: self.set_language("el"),
        )
        self.menu_bar.add_cascade(label=self.t("menu_language"), menu=self.lang_menu)

        # Help menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.help_menu.add_command(
            label=self.t("menu_check_updates"),
            command=self.check_for_updates_ui,
        )
        self.help_menu.add_separator()
        self.help_menu.add_command(label=self.t("menu_about"), command=self.show_about)
        self.menu_bar.add_cascade(label=self.t("menu_help"), menu=self.help_menu)

        self.root.config(menu=self.menu_bar)

    def update_menu_texts(self):
        try:
            self.menu_bar.entryconfigure(0, label=self.t("menu_language"))
            self.menu_bar.entryconfigure(1, label=self.t("menu_help"))
            self.help_menu.entryconfigure(0, label=self.t("menu_check_updates"))
            self.help_menu.entryconfigure(2, label=self.t("menu_about"))
        except Exception:
            pass

    def toggle_language(self):
        new_lang = "el" if self.language == "en" else "en"
        self.set_language(new_lang)

    def set_language(self, lang: str):
        if lang not in ("en", "el") or lang == self.language:
            return
        self.language = lang
        self.lang_var.set(lang)
        self.update_ui_texts()
        self.save_settings()

    def update_ui_texts(self):
        self.root.title(f"{self.t('app_name')} v{APP_VERSION}")
        if hasattr(self, "header_title"):
            self.header_title.configure(text=self.t("app_name"))
        self.header_subtitle.configure(text=self.t("subtitle"))
        self.lang_button.configure(text=self.t("lang_toggle_btn"))
        self.theme_button.configure(
            text=self.t("theme_light" if self.theme_name == "dark" else "theme_dark")
        )
        if hasattr(self, "update_button") and not self.update_button.cget("text").startswith("⚡"):
            self.update_button.configure(text=self.t("check_updates"))

        self.file_card.configure(text=self.t("card_files"))
        self.drop_label.configure(
            text=self.t("drop_text_dnd" if self.dnd_enabled else "drop_text_nodnd")
        )
        self.file_tree.heading("name", text=self.t("col_name"))
        self.file_tree.heading("duration", text=self.t("col_duration"))
        self.file_tree.heading("size", text=self.t("col_size"))
        self.file_tree.heading("status", text=self.t("col_status"))
        self.file_tree.heading("progress", text=self.t("col_progress"))

        self.add_button.configure(text=self.t("btn_add_files"))
        self.remove_button.configure(text=self.t("btn_remove_selected"))
        self.clear_button.configure(text=self.t("btn_clear_list"))
        self.update_file_count()

        self.settings_card.configure(text=self.t("card_settings"))
        self.format_label.configure(text=self.t("lbl_format"))
        self.bitrate_label.configure(text=self.t("lbl_quality"))
        self.folder_label.configure(text=self.t("lbl_folder"))
        self.output_hint_label.configure(text=self.t("output_hint"))
        self.output_button.configure(text=self.t("btn_browse"))

        self.bitrate_combo.configure(values=get_bitrate_options_for_lang(self.language))
        self.selected_bitrate.set(
            get_bitrate_display(self.current_bitrate_code, self.language)
        )

        self.action_card.configure(text=self.t("card_conversion"))
        self.convert_button.configure(text=self.t("btn_convert_all"))
        self.cancel_button.configure(text=self.t("btn_cancel"))
        self.open_folder_button.configure(text=self.t("btn_open_folder"))
        self.footer_label.configure(text=self.t("footer_text", version=APP_VERSION))

        for key in list(self.file_records.keys()):
            self.refresh_tree_record(key)

        if not self.file_records and not self.is_converting:
            self.status_text.set(self.t("status_default"))

        self.update_menu_texts()

    def create_widgets(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.main_frame = ttk.Frame(self.root, padding=(26, 18, 26, 16))
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)

        header = ttk.Frame(self.main_frame)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.columnconfigure(1, weight=1)

        logo_path = os.path.join(self.script_dir, "assets", "logo.png")
        if os.path.exists(logo_path):
            try:
                self.logo_image = tk.PhotoImage(file=logo_path).subsample(24, 24)
                self.logo_label = ttk.Label(header, image=self.logo_image)
                self.logo_label.grid(row=0, column=0, rowspan=2, padx=(0, 12))
            except Exception:
                ttk.Label(header, text="♫", style="Logo.TLabel").grid(
                    row=0, column=0, rowspan=2, padx=(0, 12)
                )
        else:
            ttk.Label(header, text="♫", style="Logo.TLabel").grid(
                row=0, column=0, rowspan=2, padx=(0, 12)
            )
        self.header_title = ttk.Label(header, text=self.t("app_name"), style="Title.TLabel")
        self.header_title.grid(
            row=0, column=1, sticky="w"
        )
        self.header_subtitle = ttk.Label(
            header,
            text=self.t("subtitle"),
            style="Muted.TLabel",
        )
        self.header_subtitle.grid(row=1, column=1, sticky="w", pady=(2, 0))

        header_actions = ttk.Frame(header)
        header_actions.grid(row=0, column=2, rowspan=2, sticky="e")

        self.lang_button = ttk.Button(
            header_actions,
            text=self.t("lang_toggle_btn"),
            command=self.toggle_language,
            style="Secondary.TButton",
        )
        self.lang_button.pack(side="left", padx=(0, 8))

        self.update_button = ttk.Button(
            header_actions,
            text=self.t("check_updates"),
            command=self.check_for_updates_ui,
            style="Secondary.TButton",
        )
        self.update_button.pack(side="left", padx=(0, 8))

        self.theme_button = ttk.Button(
            header_actions, command=self.toggle_theme, style="Secondary.TButton"
        )
        self.theme_button.pack(side="left")

        self.file_card = ttk.LabelFrame(
            self.main_frame, text=self.t("card_files"), padding=14
        )
        self.file_card.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        self.file_card.columnconfigure(0, weight=1)
        self.file_card.rowconfigure(1, weight=1)

        drop_text = (
            self.t("drop_text_dnd")
            if self.dnd_enabled
            else self.t("drop_text_nodnd")
        )
        self.drop_label = tk.Label(
            self.file_card,
            text=drop_text,
            font=("Segoe UI Semibold", 10),
            padx=12,
            pady=9,
            cursor="hand2",
        )
        self.drop_label.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.drop_label.bind("<Button-1>", lambda _event: self.browse_files())

        tree_container = ttk.Frame(self.file_card, style="Card.TFrame")
        tree_container.grid(row=1, column=0, sticky="nsew")
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)

        columns = ("name", "duration", "size", "status", "progress")
        self.file_tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="headings",
            selectmode="extended",
            height=8,
        )
        self.file_tree.heading("name", text=self.t("col_name"))
        self.file_tree.heading("duration", text=self.t("col_duration"))
        self.file_tree.heading("size", text=self.t("col_size"))
        self.file_tree.heading("status", text=self.t("col_status"))
        self.file_tree.heading("progress", text=self.t("col_progress"))
        self.file_tree.column("name", width=330, minwidth=180, anchor="w")
        self.file_tree.column("duration", width=80, minwidth=70, anchor="center")
        self.file_tree.column("size", width=90, minwidth=75, anchor="e")
        self.file_tree.column("status", width=150, minwidth=110, anchor="center")
        self.file_tree.column("progress", width=80, minwidth=65, anchor="center")
        self.file_tree.grid(row=0, column=0, sticky="nsew")

        tree_scroll = ttk.Scrollbar(
            tree_container, orient="vertical", command=self.file_tree.yview
        )
        tree_scroll.grid(row=0, column=1, sticky="ns")
        self.file_tree.configure(yscrollcommand=tree_scroll.set)

        if self.dnd_enabled:
            for widget in (self.drop_label, self.file_tree):
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self.handle_drop)

        file_buttons = ttk.Frame(self.file_card, style="Card.TFrame")
        file_buttons.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        file_buttons.columnconfigure(3, weight=1)

        self.add_button = ttk.Button(
            file_buttons, text=self.t("btn_add_files"), command=self.browse_files
        )
        self.add_button.grid(row=0, column=0, padx=(0, 8))
        self.remove_button = ttk.Button(
            file_buttons, text=self.t("btn_remove_selected"), command=self.remove_selected
        )
        self.remove_button.grid(row=0, column=1, padx=(0, 8))
        self.clear_button = ttk.Button(
            file_buttons, text=self.t("btn_clear_list"), command=self.clear_files
        )
        self.clear_button.grid(row=0, column=2)
        self.file_count_label = ttk.Label(
            file_buttons, text=self.t("file_count_zero"), style="CardMuted.TLabel"
        )
        self.file_count_label.grid(row=0, column=4, sticky="e")

        self.settings_card = ttk.LabelFrame(
            self.main_frame, text=self.t("card_settings"), padding=14
        )
        self.settings_card.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.settings_card.columnconfigure(1, weight=1)
        self.settings_card.columnconfigure(3, weight=1)

        self.format_label = ttk.Label(self.settings_card, text=self.t("lbl_format"))
        self.format_label.grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        self.format_combo = ttk.Combobox(
            self.settings_card,
            textvariable=self.target_format,
            values=("MP3", "WAV"),
            state="readonly",
            width=12,
        )
        self.format_combo.grid(row=0, column=1, sticky="ew", padx=(0, 20), ipady=3)
        self.format_combo.bind("<<ComboboxSelected>>", self.on_setting_changed)

        self.bitrate_label = ttk.Label(self.settings_card, text=self.t("lbl_quality"))
        self.bitrate_label.grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.bitrate_combo = ttk.Combobox(
            self.settings_card,
            textvariable=self.selected_bitrate,
            values=get_bitrate_options_for_lang(self.language),
            state="readonly",
            width=23,
        )
        self.bitrate_combo.grid(row=0, column=3, sticky="ew", ipady=3)
        self.bitrate_combo.bind("<<ComboboxSelected>>", self.on_setting_changed)

        self.folder_label = ttk.Label(self.settings_card, text=self.t("lbl_folder"))
        self.folder_label.grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=(12, 0)
        )
        self.output_entry = ttk.Entry(
            self.settings_card, textvariable=self.output_directory, font=("Segoe UI", 10)
        )
        self.output_entry.grid(
            row=1,
            column=1,
            columnspan=2,
            sticky="ew",
            padx=(0, 10),
            pady=(12, 0),
            ipady=5,
        )
        self.output_entry.bind("<FocusOut>", lambda _event: self.save_settings())
        self.output_button = ttk.Button(
            self.settings_card, text=self.t("btn_browse"), command=self.browse_output_directory
        )
        self.output_button.grid(row=1, column=3, sticky="e", pady=(12, 0))
        self.output_hint_label = ttk.Label(
            self.settings_card,
            text=self.t("output_hint"),
            style="CardMuted.TLabel",
        )
        self.output_hint_label.grid(row=2, column=1, columnspan=3, sticky="w", pady=(6, 0))

        self.action_card = ttk.LabelFrame(
            self.main_frame, text=self.t("card_conversion"), padding=14
        )
        self.action_card.grid(row=3, column=0, sticky="ew")
        self.action_card.columnconfigure(0, weight=1)

        status_row = ttk.Frame(self.action_card, style="Card.TFrame")
        status_row.grid(row=0, column=0, columnspan=3, sticky="ew")
        status_row.columnconfigure(0, weight=1)
        self.status_label = ttk.Label(
            status_row, textvariable=self.status_text, style="Status.TLabel"
        )
        self.status_label.grid(row=0, column=0, sticky="w")
        ttk.Label(
            status_row, textvariable=self.progress_text, style="Status.TLabel"
        ).grid(row=0, column=1, sticky="e")

        self.progress_bar = ttk.Progressbar(
            self.action_card,
            variable=self.progress_value,
            maximum=100,
            mode="determinate",
        )
        self.progress_bar.grid(
            row=1, column=0, columnspan=3, sticky="ew", pady=(9, 12), ipady=3
        )

        self.convert_button = ttk.Button(
            self.action_card,
            text=self.t("btn_convert_all"),
            command=self.start_batch_conversion,
            style="Accent.TButton",
        )
        self.convert_button.grid(row=2, column=0, sticky="ew", padx=(0, 8))

        self.cancel_button = ttk.Button(
            self.action_card,
            text=self.t("btn_cancel"),
            command=self.cancel_conversion,
            state="disabled",
            style="Danger.TButton",
        )
        self.cancel_button.grid(row=2, column=1, sticky="ew", padx=4)

        self.open_folder_button = ttk.Button(
            self.action_card,
            text=self.t("btn_open_folder"),
            command=self.open_output_folder,
            state="disabled",
        )
        self.open_folder_button.grid(row=2, column=2, sticky="ew", padx=(8, 0))

        footer = ttk.Frame(self.main_frame)
        footer.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        footer.columnconfigure(0, weight=1)
        self.footer_label = ttk.Label(
            footer,
            text=self.t("footer_text", version=APP_VERSION),
            style="Muted.TLabel",
        )
        self.footer_label.grid(row=0, column=0, sticky="w")
        ttk.Label(footer, text="AGPL-3.0-only", style="Muted.TLabel").grid(
            row=0, column=1, sticky="e"
        )

    def apply_theme(self):
        colors = THEMES[self.theme_name]
        self.colors = colors
        self.style.theme_use("clam")
        self.root.configure(background=colors["bg"])

        self.style.configure(
            ".",
            background=colors["bg"],
            foreground=colors["text"],
            font=("Segoe UI", 10),
        )
        self.style.configure("TFrame", background=colors["bg"])
        self.style.configure("Card.TFrame", background=colors["card"])
        self.style.configure(
            "TLabelframe",
            background=colors["card"],
            bordercolor=colors["border"],
            relief="solid",
            borderwidth=1,
        )
        self.style.configure(
            "TLabelframe.Label",
            background=colors["bg"],
            foreground=colors["text"],
            font=("Segoe UI Semibold", 10),
        )
        self.style.configure("TLabel", background=colors["card"], foreground=colors["text"])
        self.style.configure(
            "Title.TLabel",
            background=colors["bg"],
            foreground=colors["text"],
            font=("Segoe UI Semibold", 19),
        )
        self.style.configure(
            "Logo.TLabel",
            background=colors["accent"],
            foreground="#ffffff",
            font=("Segoe UI", 21, "bold"),
            padding=(12, 6),
        )
        self.style.configure(
            "Muted.TLabel", background=colors["bg"], foreground=colors["muted"]
        )
        self.style.configure(
            "CardMuted.TLabel",
            background=colors["card"],
            foreground=colors["muted"],
        )
        self.style.configure(
            "Status.TLabel",
            background=colors["card"],
            foreground=colors["text"],
            font=("Segoe UI Semibold", 10),
        )
        self.style.configure(
            "TButton",
            background=colors["card"],
            foreground=colors["text"],
            bordercolor=colors["border"],
            padding=(12, 7),
            font=("Segoe UI Semibold", 10),
        )
        self.style.map(
            "TButton",
            background=[("active", colors["border"]), ("disabled", colors["bg"])],
            foreground=[("disabled", colors["disabled"])],
        )
        self.style.configure(
            "Accent.TButton",
            background=colors["accent"],
            foreground="#ffffff",
            bordercolor=colors["accent"],
        )
        self.style.map(
            "Accent.TButton",
            background=[
                ("active", colors["accent_hover"]),
                ("disabled", colors["disabled"]),
            ],
            foreground=[("disabled", "#e5e7eb")],
        )
        self.style.configure(
            "Secondary.TButton",
            background=colors["bg"],
            foreground=colors["text"],
            bordercolor=colors["border"],
        )
        self.style.configure(
            "Danger.TButton",
            background=colors["card"],
            foreground=colors["danger"],
            bordercolor=colors["border"],
        )
        self.style.map(
            "Danger.TButton", foreground=[("disabled", colors["disabled"])]
        )
        self.style.configure(
            "TEntry",
            fieldbackground=colors["input"],
            foreground=colors["text"],
            bordercolor=colors["border"],
            insertcolor=colors["text"],
            padding=5,
        )
        self.style.configure(
            "TCombobox",
            fieldbackground=colors["input"],
            background=colors["input"],
            foreground=colors["text"],
            arrowcolor=colors["text"],
            bordercolor=colors["border"],
            padding=5,
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[
                ("readonly", colors["input"]),
                ("disabled", colors["bg"]),
            ],
            foreground=[
                ("readonly", colors["text"]),
                ("disabled", colors["disabled"]),
            ],
            selectbackground=[("readonly", colors["input"])],
            selectforeground=[("readonly", colors["text"])],
        )
        self.style.configure(
            "Horizontal.TProgressbar",
            troughcolor=colors["progress_bg"],
            background=colors["accent"],
            bordercolor=colors["progress_bg"],
            lightcolor=colors["accent"],
            darkcolor=colors["accent"],
        )
        self.style.configure(
            "Treeview",
            background=colors["card"],
            fieldbackground=colors["card"],
            foreground=colors["text"],
            bordercolor=colors["border"],
            rowheight=29,
        )
        self.style.map(
            "Treeview",
            background=[("selected", colors["accent"])],
            foreground=[("selected", "#ffffff")],
        )
        self.style.configure(
            "Treeview.Heading",
            background=colors["bg"],
            foreground=colors["text"],
            bordercolor=colors["border"],
            font=("Segoe UI Semibold", 9),
            padding=(6, 7),
        )

        self.drop_label.configure(
            background=colors["progress_bg"],
            foreground=colors["accent"],
            highlightbackground=colors["border"],
            highlightthickness=1,
        )
        self.file_tree.tag_configure("completed", foreground=colors["success"])
        self.file_tree.tag_configure("error", foreground=colors["danger"])
        self.file_tree.tag_configure("active", foreground=colors["accent"])
        self.file_tree.tag_configure("canceled", foreground=colors["muted"])

        for menu in (self.menu_bar, self.help_menu):
            menu.configure(
                background=colors["card"],
                foreground=colors["text"],
                activebackground=colors["accent"],
                activeforeground="#ffffff",
            )

        self.theme_button.configure(
            text=self.t("theme_light" if self.theme_name == "dark" else "theme_dark")
        )
        self.lang_button.configure(
            text=self.t("lang_toggle_btn")
        )

    def toggle_theme(self):
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self.apply_theme()
        self.save_settings()

    def check_for_updates_ui(self, silent: bool = False):
        if updater is None:
            if not silent:
                messagebox.showwarning(
                    self.t("dlg_update_check_title"),
                    "Updater module not available." if self.language == "en" else "Το υποσύστημα ενημερώσεων δεν είναι διαθέσιμο.",
                )
            return

        self.update_button.configure(text=self.t("checking_updates"), state="disabled")

        def _worker():
            res = updater.check_for_updates(APP_VERSION, GITHUB_REPO, lang=self.language)
            self.root.after(0, lambda: self._on_update_checked(res, silent))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_update_checked(self, result: dict, silent: bool):
        self.update_button.configure(state="normal")
        if result.get("update_available"):
            latest = result.get("latest_version", "")
            self.update_button.configure(text=f"⚡ v{latest}")
            self.show_update_dialog(result)
        else:
            self.update_button.configure(text=self.t("check_updates"))
            if not silent:
                if result.get("status") == "success":
                    messagebox.showinfo(
                        self.t("dlg_update_up_to_date_title"),
                        self.t(
                            "dlg_update_up_to_date_msg",
                            version=APP_VERSION,
                            repo=result.get("repo", GITHUB_REPO),
                        ),
                    )
                else:
                    messagebox.showwarning(
                        self.t("dlg_update_failed_title"),
                        result.get("message") or self.t("dlg_update_failed_msg"),
                    )

    def show_update_dialog(self, update_info: dict):
        colors = self.colors
        dialog = tk.Toplevel(self.root)
        dialog.title(self.t("dlg_update_available_title"))
        dialog.geometry("520x420")
        dialog.minsize(460, 360)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=colors["bg"])

        try:
            x = self.root.winfo_x() + (self.root.winfo_width() - 520) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - 420) // 2
            dialog.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill="both", expand=True)

        header_frame = ttk.Frame(frame)
        header_frame.pack(fill="x", pady=(0, 12))

        ttk.Label(header_frame, text="⚡", font=("Segoe UI", 24)).pack(side="left", padx=(0, 10))
        titles = ttk.Frame(header_frame)
        titles.pack(side="left", fill="x", expand=True)
        ttk.Label(titles, text=self.t("dlg_update_new_version"), font=("Segoe UI Semibold", 14)).pack(anchor="w")
        ttk.Label(
            titles,
            text=self.t(
                "dlg_update_version_diff",
                current=APP_VERSION,
                latest=update_info.get("latest_version", ""),
            ),
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        notes_label = ttk.Label(frame, text=self.t("dlg_update_changelog"), font=("Segoe UI Semibold", 10))
        notes_label.pack(anchor="w", pady=(6, 4))

        notes_box = tk.Text(
            frame,
            wrap="word",
            height=8,
            font=("Segoe UI", 9),
            bg=colors["card"],
            fg=colors["text"],
            bd=1,
            relief="solid",
            highlightthickness=0,
            padx=8,
            pady=8,
        )
        notes_box.pack(fill="both", expand=True, pady=(0, 16))
        notes_box.insert("1.0", update_info.get("release_notes") or self.t("dlg_update_no_notes"))
        notes_box.configure(state="disabled")

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill="x")

        status_lbl = ttk.Label(btn_row, text="", style="Muted.TLabel")
        status_lbl.pack(side="left")

        def _do_update():
            download_url = update_info.get("download_url")
            if not download_url:
                messagebox.showerror(self.t("dlg_update_error_title"), self.t("dlg_update_no_download_url"))
                return

            if not messagebox.askyesno(
                self.t("dlg_update_confirm_title"),
                self.t("dlg_update_confirm_msg"),
            ):
                return

            status_lbl.configure(text=self.t("dlg_update_downloading"))
            apply_btn.configure(state="disabled")

            def _dl():
                success, msg = updater.download_and_launch_updater(
                    download_url, Path(self.script_dir), lang=self.language
                )
                if success:
                    dialog.after(0, lambda: self.root.destroy())
                else:
                    dialog.after(0, lambda: messagebox.showerror(self.t("dlg_update_error_title"), msg))
                    dialog.after(0, lambda: status_lbl.configure(text=""))
                    dialog.after(0, lambda: apply_btn.configure(state="normal"))

            threading.Thread(target=_dl, daemon=True).start()

        def _open_github():
            url = update_info.get("html_url") or f"https://github.com/{GITHUB_REPO}"
            webbrowser.open(url)

        close_btn = ttk.Button(btn_row, text=self.t("dlg_update_btn_close"), command=dialog.destroy, style="Secondary.TButton")
        close_btn.pack(side="right", padx=(6, 0))

        gh_btn = ttk.Button(btn_row, text="🌐 GitHub", command=_open_github, style="Secondary.TButton")
        gh_btn.pack(side="right", padx=(6, 0))

        apply_btn = ttk.Button(btn_row, text=self.t("dlg_update_btn_apply"), command=_do_update, style="Accent.TButton")
        apply_btn.pack(side="right")

    def show_about(self):
        dnd_status = (
            self.t("dlg_about_dnd_active")
            if self.dnd_enabled
            else self.t("dlg_about_dnd_inactive")
        )
        app_name = self.t("app_name")
        messagebox.showinfo(
            self.t("dlg_about_title"),
            f"{app_name} v{APP_VERSION}\n\n"
            "Creator: Alexandros - Ermis Tsourapas (SV1RVP)\n"
            "Application license: AGPL-3.0-only\n\n"
            "Uses FFmpeg under GPLv3-or-later.\n"
            "Uses tkinterdnd2 under the MIT License.\n\n"
            f"Drag & drop: {dnd_status}\n\n"
            "See LICENSE, FFMPEG_LICENSE.txt and THIRD_PARTY_NOTICES.md.",
        )

    def browse_files(self):
        selected = filedialog.askopenfilenames(
            title=self.t("dlg_browse_files_title"),
            filetypes=[
                (self.t("dlg_file_type_m4a"), "*.m4a"),
                (self.t("dlg_file_type_all"), "*.*"),
            ],
        )
        if selected:
            self.add_files(selected)

    def handle_drop(self, event):
        if self.is_converting:
            return "break"

        dropped = self.root.tk.splitlist(event.data)
        expanded = []
        for dropped_path in dropped:
            path = os.path.abspath(dropped_path)
            if os.path.isdir(path):
                try:
                    expanded.extend(
                        entry.path
                        for entry in sorted(
                            os.scandir(path), key=lambda item: item.name.lower()
                        )
                        if entry.is_file() and entry.name.lower().endswith(".m4a")
                    )
                except OSError:
                    continue
            else:
                expanded.append(path)

        self.add_files(expanded)
        return "break"

    @staticmethod
    def canonical_path(path):
        return os.path.normcase(os.path.abspath(path))

    def add_files(self, paths):
        added_keys = []
        invalid_count = 0
        duplicate_count = 0

        for raw_path in paths:
            path = os.path.abspath(str(raw_path).strip().strip('"'))
            if not os.path.isfile(path) or not path.lower().endswith(".m4a"):
                invalid_count += 1
                continue

            key = self.canonical_path(path)
            if key in self.file_records:
                duplicate_count += 1
                continue

            item_id = f"file_{self.next_item_id}"
            self.next_item_id += 1
            record = {
                "key": key,
                "path": path,
                "item_id": item_id,
                "duration": 0.0,
                "size": os.path.getsize(path),
                "status_key": "status_reading",
                "status_args": {},
                "status": self.t("status_reading"),
                "progress": 0.0,
                "output_path": "",
                "error": "",
            }
            self.file_records[key] = record
            self.item_to_key[item_id] = key
            self.file_tree.insert(
                "",
                "end",
                iid=item_id,
                values=(
                    os.path.basename(path),
                    "…",
                    self.format_size(record["size"]),
                    record["status"],
                    "0%",
                ),
            )
            added_keys.append(key)

        if added_keys:
            self.update_file_count()
            self.set_status(
                self.t("status_files_added", count=len(added_keys)),
                self.colors["text"],
            )
            threading.Thread(
                target=self.probe_files_worker,
                args=(added_keys,),
                daemon=True,
            ).start()

        if invalid_count or duplicate_count:
            details = []
            if invalid_count:
                details.append(self.t("skipped_invalid", count=invalid_count))
            if duplicate_count:
                details.append(self.t("skipped_duplicates", count=duplicate_count))
            self.set_status(
                self.t("status_skipped", details=", ".join(details)),
                self.colors["warning"],
            )

    def probe_files_worker(self, keys):
        for key in keys:
            record = self.file_records.get(key)
            if not record:
                continue
            try:
                info = self.get_media_info(record["path"])
                self.result_queue.put(("file_info", key, info))
            except Exception as error:
                self.result_queue.put(("file_probe_error", key, str(error)))

    def get_media_info(self, input_path):
        if not os.path.isfile(self.ffprobe_path):
            raise FileNotFoundError("ffprobe.exe not found.")

        command = [
            self.ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            input_path,
        ]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=CREATE_NO_WINDOW,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "ffprobe failed.")

        payload = json.loads(result.stdout)
        duration = float(payload.get("format", {}).get("duration") or 0)
        return {"duration": duration}

    def remove_selected(self):
        if self.is_converting:
            return
        for item_id in self.file_tree.selection():
            key = self.item_to_key.pop(item_id, None)
            if key:
                self.file_records.pop(key, None)
            self.file_tree.delete(item_id)
        self.update_file_count()

    def clear_files(self):
        if self.is_converting or not self.file_records:
            return
        self.file_tree.delete(*self.file_tree.get_children())
        self.file_records.clear()
        self.item_to_key.clear()
        self.completed_outputs.clear()
        self.progress_value.set(0)
        self.progress_text.set("0%")
        self.open_folder_button.configure(state="disabled")
        self.update_file_count()
        self.set_status(self.t("status_list_cleared"), self.colors["muted"])

    def update_file_count(self):
        count = len(self.file_records)
        if count == 0:
            label = self.t("file_count_zero")
        elif count == 1:
            label = self.t("file_count_single")
        else:
            label = self.t("file_count_multiple", count=count)
        self.file_count_label.configure(text=label)
        if not count and not self.is_converting:
            self.status_text.set(self.t("status_default"))

    def browse_output_directory(self):
        initial = self.output_directory.get().strip()
        selected = filedialog.askdirectory(
            title=self.t("dlg_browse_output_title"),
            initialdir=initial if os.path.isdir(initial) else None,
        )
        if selected:
            self.output_directory.set(os.path.abspath(selected))
            self.save_settings()

    @staticmethod
    def format_duration(seconds):
        total = max(0, int(round(seconds)))
        hours, remainder = divmod(total, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    @staticmethod
    def format_size(size_bytes):
        value = float(size_bytes)
        for unit in ("B", "KB", "MB", "GB"):
            if value < 1024 or unit == "GB":
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} GB"

    def on_setting_changed(self, _event=None):
        self.current_bitrate_code = normalize_bitrate_code(self.selected_bitrate.get())
        self.toggle_bitrate_options()
        self.save_settings()

    def toggle_bitrate_options(self):
        if self.target_format.get() == "WAV":
            self.bitrate_combo.configure(state="disabled")
            self.bitrate_label.configure(style="CardMuted.TLabel")
        elif not self.is_converting:
            self.bitrate_combo.configure(state="readonly")
            self.bitrate_label.configure(style="TLabel")

    def make_output_tasks(self):
        if not self.file_records:
            messagebox.showerror(
                self.t("dlg_no_files_title"), self.t("dlg_no_files_msg")
            )
            return None

        missing_tools = [
            name
            for name, path in (
                ("ffmpeg.exe", self.ffmpeg_path),
                ("ffprobe.exe", self.ffprobe_path),
            )
            if not os.path.isfile(path)
        ]
        if missing_tools:
            messagebox.showerror(
                self.t("dlg_ffmpeg_error_title"),
                self.t("dlg_ffmpeg_missing_msg", tools=", ".join(missing_tools)),
            )
            return None

        common_output_dir = self.output_directory.get().strip()
        if common_output_dir:
            common_output_dir = os.path.abspath(common_output_dir)
            if not os.path.isdir(common_output_dir):
                messagebox.showerror(
                    self.t("dlg_output_not_found_title"),
                    self.t("dlg_output_not_found_msg"),
                )
                return None

        fmt = self.target_format.get().lower()
        bitrate = self.current_bitrate_code
        used_outputs = set()
        tasks = []

        for record in self.file_records.values():
            output_dir = common_output_dir or os.path.dirname(record["path"])
            base_name = os.path.splitext(os.path.basename(record["path"]))[0]
            candidate = os.path.join(output_dir, f"{base_name}.{fmt}")
            suffix = 2
            while os.path.normcase(candidate) in used_outputs:
                candidate = os.path.join(output_dir, f"{base_name}_{suffix}.{fmt}")
                suffix += 1
            used_outputs.add(os.path.normcase(candidate))
            tasks.append(
                {
                    "key": record["key"],
                    "path": record["path"],
                    "duration": record["duration"],
                    "output_path": candidate,
                    "format": fmt,
                    "bitrate": bitrate,
                }
            )

        existing_count = sum(os.path.exists(task["output_path"]) for task in tasks)
        if existing_count and not messagebox.askyesno(
            self.t("dlg_overwrite_title"),
            self.t("dlg_overwrite_msg", count=existing_count),
        ):
            return None

        return tasks

    def start_batch_conversion(self):
        tasks = self.make_output_tasks()
        if not tasks:
            return

        self.cancel_event.clear()
        self.completed_outputs.clear()
        self.progress_value.set(0)
        self.progress_text.set("0%")
        self.open_folder_button.configure(state="disabled")

        for task in tasks:
            record = self.file_records[task["key"]]
            record["status_key"] = "status_queued_item"
            record["status_args"] = {}
            record["status"] = self.t("status_queued_item")
            record["progress"] = 0.0
            record["output_path"] = task["output_path"]
            record["error"] = ""
            self.refresh_tree_record(task["key"])

        self.set_conversion_state(True)
        self.set_status(
            self.t("status_starting_conversion", count=len(tasks)),
            self.colors["warning"],
        )
        threading.Thread(
            target=self.batch_conversion_worker,
            args=(tasks,),
            daemon=True,
        ).start()

    def batch_conversion_worker(self, tasks):
        outputs = []
        errors = []
        canceled = False
        total = len(tasks)

        try:
            for index, task in enumerate(tasks):
                if self.cancel_event.is_set():
                    canceled = True
                    break

                self.result_queue.put(
                    ("file_status", task["key"], index + 1, total)
                )

                def progress_callback(percent, key=task["key"], position=index):
                    overall = ((position + percent / 100.0) / total) * 100.0
                    self.result_queue.put(("file_progress", key, percent))
                    self.result_queue.put(("overall_progress", overall))

                try:
                    self.convert_one_file(task, progress_callback)
                    outputs.append(task["output_path"])
                    self.result_queue.put(
                        ("file_completed", task["key"], task["output_path"])
                    )
                except ConversionCanceled:
                    canceled = True
                    self.result_queue.put(("file_canceled", task["key"]))
                    break
                except Exception as error:
                    errors.append((task["path"], str(error)))
                    self.result_queue.put(
                        ("file_error", task["key"], str(error))
                    )

                self.result_queue.put(
                    ("overall_progress", ((index + 1) / total) * 100.0)
                )

            if canceled:
                completed_keys = {
                    task["key"]
                    for task in tasks
                    if task["output_path"] in outputs
                }
                for task in tasks:
                    if task["key"] not in completed_keys:
                        self.result_queue.put(("file_not_run", task["key"]))

            self.result_queue.put(("batch_done", outputs, errors, canceled))
        except Exception as error:
            self.result_queue.put(("fatal_error", str(error)))

    def convert_one_file(self, task, progress_callback):
        duration = task["duration"]
        if duration <= 0:
            duration = self.get_media_info(task["path"])["duration"]

        command = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            task["path"],
            "-map_metadata",
            "0",
            "-vn",
        ]
        if task["format"] == "mp3":
            command.extend(
                [
                    "-codec:a",
                    "libmp3lame",
                    "-b:a",
                    task["bitrate"],
                    "-id3v2_version",
                    "3",
                ]
            )
        elif task["format"] == "wav":
            command.extend(["-codec:a", "pcm_s16le"])
        else:
            raise ValueError(f"Unsupported format: {task['format']}")

        command.extend(["-progress", "pipe:1", "-nostats", task["output_path"]])
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=CREATE_NO_WINDOW,
        )
        self.conversion_process = process
        diagnostic_lines = []

        try:
            if process.stdout is None:
                raise RuntimeError("Could not monitor FFmpeg output.")

            for raw_line in process.stdout:
                line = raw_line.strip()
                if self.cancel_event.is_set():
                    process.terminate()
                    break

                if "=" not in line:
                    if line:
                        diagnostic_lines.append(line)
                    continue

                key, value = line.split("=", 1)
                if key in ("out_time_us", "out_time_ms") and duration > 0:
                    try:
                        percent = min(
                            99.0, (float(value) / 1_000_000) / duration * 100
                        )
                        progress_callback(percent)
                    except ValueError:
                        pass
                elif key == "progress" and value == "end":
                    progress_callback(100.0)

            return_code = process.wait()
        finally:
            self.conversion_process = None

        if self.cancel_event.is_set():
            if os.path.isfile(task["output_path"]):
                try:
                    os.remove(task["output_path"])
                except OSError:
                    pass
            raise ConversionCanceled()

        if return_code != 0:
            details = "\n".join(diagnostic_lines[-8:]).strip()
            raise RuntimeError(
                details or f"FFmpeg terminated with exit code {return_code}."
            )

        progress_callback(100.0)

    def cancel_conversion(self):
        if not self.is_converting:
            return
        self.cancel_event.set()
        self.cancel_button.configure(state="disabled")
        process = self.conversion_process
        if process and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass
        self.set_status(self.t("status_canceling"), self.colors["warning"])

    def poll_worker_messages(self):
        try:
            while True:
                message = self.result_queue.get_nowait()
                message_type = message[0]

                if message_type == "file_info":
                    _, key, info = message
                    record = self.file_records.get(key)
                    if record:
                        record["duration"] = info["duration"]
                        record["status_key"] = "status_ready"
                        record["status_args"] = {}
                        record["status"] = self.t("status_ready")
                        self.refresh_tree_record(key)
                elif message_type == "file_probe_error":
                    _, key, error = message
                    record = self.file_records.get(key)
                    if record:
                        record["status_key"] = "status_no_info"
                        record["status_args"] = {}
                        record["status"] = self.t("status_no_info")
                        record["error"] = error
                        self.refresh_tree_record(key)
                elif message_type == "file_status":
                    _, key, current_idx, total_cnt = message
                    record = self.file_records.get(key)
                    if record:
                        record["status_key"] = "status_converting_item"
                        record["status_args"] = {"current": current_idx, "total": total_cnt}
                        record["status"] = self.t("status_converting_item", current=current_idx, total=total_cnt)
                        self.refresh_tree_record(key, "active")
                elif message_type == "file_progress":
                    _, key, percent = message
                    record = self.file_records.get(key)
                    if record:
                        record["progress"] = percent
                        self.refresh_tree_record(key, "active")
                elif message_type == "overall_progress":
                    percent = max(0.0, min(100.0, float(message[1])))
                    self.progress_value.set(percent)
                    self.progress_text.set(f"{percent:.0f}%")
                elif message_type == "file_completed":
                    _, key, output_path = message
                    record = self.file_records.get(key)
                    if record:
                        record["status_key"] = "status_completed_item"
                        record["status_args"] = {}
                        record["status"] = self.t("status_completed_item")
                        record["progress"] = 100.0
                        record["output_path"] = output_path
                        self.refresh_tree_record(key, "completed")
                elif message_type == "file_error":
                    _, key, error = message
                    record = self.file_records.get(key)
                    if record:
                        record["status_key"] = "status_error_item"
                        record["status_args"] = {}
                        record["status"] = self.t("status_error_item")
                        record["error"] = error
                        self.refresh_tree_record(key, "error")
                elif message_type == "file_canceled":
                    _, key = message
                    record = self.file_records.get(key)
                    if record:
                        record["status_key"] = "status_canceled_item"
                        record["status_args"] = {}
                        record["status"] = self.t("status_canceled_item")
                        self.refresh_tree_record(key, "canceled")
                elif message_type == "file_not_run":
                    _, key = message
                    record = self.file_records.get(key)
                    if record and (
                        record.get("status_key") in ("status_queued_item", "status_converting_item")
                        or record.get("status") == "Σε αναμονή"
                    ):
                        record["status_key"] = "status_skipped_item"
                        record["status_args"] = {}
                        record["status"] = self.t("status_skipped_item")
                        self.refresh_tree_record(key, "canceled")
                elif message_type == "batch_done":
                    self.on_batch_done(message[1], message[2], message[3])
                elif message_type == "fatal_error":
                    self.on_fatal_error(message[1])
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.poll_worker_messages)

    def refresh_tree_record(self, key, tag=None):
        record = self.file_records.get(key)
        if not record or not self.file_tree.exists(record["item_id"]):
            return

        duration_text = (
            self.format_duration(record["duration"]) if record["duration"] > 0 else "—"
        )
        tags = (tag,) if tag else ()
        status_key = record.get("status_key")
        if status_key:
            status_text = self.t(status_key, **record.get("status_args", {}))
        else:
            status_text = record.get("status", "")
        record["status"] = status_text

        self.file_tree.item(
            record["item_id"],
            values=(
                os.path.basename(record["path"]),
                duration_text,
                self.format_size(record["size"]),
                status_text,
                f"{record['progress']:.0f}%",
            ),
            tags=tags,
        )

    def set_conversion_state(self, converting):
        self.is_converting = converting
        normal_state = "disabled" if converting else "normal"
        readonly_state = "disabled" if converting else "readonly"

        for button in (
            self.add_button,
            self.remove_button,
            self.clear_button,
            self.output_button,
            self.theme_button,
            self.lang_button,
        ):
            button.configure(state=normal_state)

        self.output_entry.configure(state=normal_state)
        self.format_combo.configure(state=readonly_state)
        self.convert_button.configure(state=normal_state)
        self.cancel_button.configure(state="normal" if converting else "disabled")

        if converting or self.target_format.get() == "WAV":
            self.bitrate_combo.configure(state="disabled")
        else:
            self.bitrate_combo.configure(state="readonly")

    def set_status(self, text, color):
        self.status_text.set(text)
        self.style.configure("Status.TLabel", foreground=color)

    def on_batch_done(self, outputs, errors, canceled):
        self.completed_outputs = outputs
        self.set_conversion_state(False)

        if outputs:
            self.open_folder_button.configure(state="normal")

        if canceled:
            self.set_status(
                self.t("status_canceled_summary", count=len(outputs)),
                self.colors["warning"],
            )
            return

        self.progress_value.set(100)
        self.progress_text.set("100%")
        if errors:
            self.set_status(
                self.t("status_done_errors", count=len(errors)),
                self.colors["warning"],
            )
            details = "\n".join(
                f"• {os.path.basename(path)}: {error}"
                for path, error in errors[:5]
            )
            if len(errors) > 5:
                details += f"\n{self.t('dlg_queue_errors_more', count=len(errors) - 5)}"
            messagebox.showwarning(
                self.t("dlg_queue_errors_title"),
                self.t(
                    "dlg_queue_errors_msg",
                    success=len(outputs),
                    errors=len(errors),
                    details=details,
                ),
            )
        else:
            self.set_status(
                self.t("status_done_success", count=len(outputs)),
                self.colors["success"],
            )
            messagebox.showinfo(
                self.t("dlg_conversion_done_title"),
                self.t("dlg_conversion_done_msg", count=len(outputs)),
            )
        self.save_settings()

    def on_fatal_error(self, error_message):
        self.set_conversion_state(False)
        self.set_status(self.t("status_fatal_error"), self.colors["danger"])
        messagebox.showerror(self.t("dlg_output_not_found_title"), error_message)

    def open_output_folder(self):
        if not self.completed_outputs:
            messagebox.showwarning(
                self.t("dlg_open_folder_title"),
                self.t("dlg_open_folder_no_files"),
            )
            return

        first_existing = next(
            (path for path in self.completed_outputs if os.path.isfile(path)), None
        )
        if first_existing:
            os.startfile(os.path.dirname(first_existing))
        else:
            messagebox.showwarning(
                self.t("dlg_open_folder_title"),
                self.t("dlg_open_folder_not_found"),
            )

    def on_close(self):
        if self.is_converting and not messagebox.askyesno(
            self.t("dlg_close_title"),
            self.t("dlg_close_msg"),
        ):
            return

        self.save_settings()
        self.cancel_event.set()
        process = self.conversion_process
        if process and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass
        self.root.destroy()


if __name__ == "__main__":
    root = TkinterDnD.Tk() if TkinterDnD is not None else tk.Tk()
    app = AudioConverterApp(root)
    root.mainloop()
