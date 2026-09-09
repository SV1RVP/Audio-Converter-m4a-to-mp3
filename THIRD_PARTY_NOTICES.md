# Third-party notices

Το κύριο project είναι διαθέσιμο υπό την AGPL-3.0-only. Τα παρακάτω components τρίτων **δεν επαναδειοδοτούνται** ως AGPL και εξακολουθούν να καλύπτονται από τις δικές τους άδειες.

## FFmpeg

- Project: https://ffmpeg.org/
- Windows builds: https://www.gyan.dev/ffmpeg/builds/
- Source code: https://ffmpeg.org/download.html
- License information: https://ffmpeg.org/legal.html
- License of the Gyan Windows builds used by the installer: GNU GPL version 3 or later.
- Included license text: `FFMPEG_LICENSE.txt`.

Ο installer κατεβάζει το τρέχον 64-bit `ffmpeg-release-essentials.zip` απευθείας από το gyan.dev και επαληθεύει το δημοσιευμένο SHA-256 πριν αντιγράψει τα `ffmpeg.exe` και `ffprobe.exe`.

Το FFmpeg δεν ανήκει στον δημιουργό αυτού του project. Το “FFmpeg” είναι εμπορικό σήμα του Fabrice Bellard, δημιουργού του FFmpeg project.

Αν δημιουργήσεις release που περιλαμβάνει FFmpeg binaries αντί να τα κατεβάζει κατά την εγκατάσταση, πρέπει να συμπεριλάβεις την κατάλληλη άδεια, τα notices, τα build details και να προσφέρεις το ακριβές corresponding source σύμφωνα με τους όρους της GPL.

## tkinterdnd2

- Project: https://pypi.org/project/tkinterdnd2/
- Source: https://github.com/Eliav2/tkinterdnd2
- License: MIT License

Το `tkinterdnd2` εγκαθίσταται μέσα στο τοπικό `.venv` και παρέχει native drag & drop στο Tkinter.
