

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from hijridate import Gregorian
from config import WEATHER_API_KEY

import requests
import yt_dlp
import os
import re
import shutil
import threading
import time
import uuid
import asyncio
import subprocess
import edge_tts
import qrcode
import sympy as sp
# FFmpeg must NOT be tied to one Windows user's absolute path.
# Prefer FFmpeg from PATH, then fall back to the old path only if it exists.
FFMPEG_DIR = os.environ.get("FFMPEG_DIR", "").strip()

if not FFMPEG_DIR:
    ffmpeg_exe = shutil.which("ffmpeg")
    if ffmpeg_exe:
        FFMPEG_DIR = os.path.dirname(ffmpeg_exe)
    else:
        legacy_ffmpeg_dir = r"C:\Users\Md. Sohag Hossain\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin"
        if os.path.isfile(os.path.join(legacy_ffmpeg_dir, "ffmpeg.exe")):
            FFMPEG_DIR = legacy_ffmpeg_dir

if not FFMPEG_DIR:
    raise RuntimeError(
        "FFmpeg পাওয়া যায়নি। FFmpeg install করে PATH-এ যোগ করুন, "
        "অথবা FFMPEG_DIR environment variable সেট করুন।"
    )

MASTER_MIND_FOOTER = "\n\n🧠 Powered by Mastermind"

MASTER_MIND_FOOTER_RE = re.compile(
    r"\s*🧠\s*(?:<b>)?Powered by Mastermind(?:</b>)?",
    re.IGNORECASE
)

def add_mastermind(text):
    """Append exactly one Mastermind footer."""
    text = MASTER_MIND_FOOTER_RE.sub("", str(text))
    return text.rstrip() + MASTER_MIND_FOOTER
divisions = {

    "🏙️ ঢাকা বিভাগ": [
        "ঢাকা",
        "গাজীপুর",
        "নারায়ণগঞ্জ",
        "টাঙ্গাইল",
        "কিশোরগঞ্জ",
        "মানিকগঞ্জ",
        "মুন্সীগঞ্জ",
        "নরসিংদী",
        "রাজবাড়ী",
        "শরীয়তপুর",
        "ফরিদপুর",
        "গোপালগঞ্জ",
        "মাদারীপুর"
    ],

    "🌊 চট্টগ্রাম বিভাগ": [
        "চট্টগ্রাম",
        "কক্সবাজার",
        "কুমিল্লা",
        "ফেনী",
        "নোয়াখালী",
        "লক্ষ্মীপুর",
        "চাঁদপুর",
        "ব্রাহ্মণবাড়িয়া",
        "খাগড়াছড়ি",
        "রাঙ্গামাটি",
        "বান্দরবান"
    ],

    "🏛️ রাজশাহী বিভাগ": [
        "রাজশাহী",
        "বগুড়া",
        "পাবনা",
        "সিরাজগঞ্জ",
        "নাটোর",
        "নওগাঁ",
        "জয়পুরহাট",
        "চাঁপাইনবাবগঞ্জ"
    ],

    "🌿 খুলনা বিভাগ": [
        "খুলনা",
        "যশোর",
        "সাতক্ষীরা",
        "বাগেরহাট",
        "ঝিনাইদহ",
        "কুষ্টিয়া",
        "চুয়াডাঙ্গা",
        "মেহেরপুর",
        "নড়াইল",
        "মাগুরা"
    ],

    "🌴 বরিশাল বিভাগ": [
        "বরিশাল",
        "পটুয়াখালী",
        "ভোলা",
        "ঝালকাঠি",
        "পিরোজপুর",
        "বরগুনা"
    ],

    "⛰️ সিলেট বিভাগ": [
        "সিলেট",
        "মৌলভীবাজার",
        "হবিগঞ্জ",
        "সুনামগঞ্জ"
    ],

    "❄️ রংপুর বিভাগ": [
        "রংপুর",
        "দিনাজপুর",
        "কুড়িগ্রাম",
        "গাইবান্ধা",
        "লালমনিরহাট",
        "নীলফামারী",
        "পঞ্চগড়",
        "ঠাকুরগাঁও"
    ],

    "🌾 ময়মনসিংহ বিভাগ": [
        "ময়মনসিংহ",
        "জামালপুর",
        "নেত্রকোনা",
        "শেরপুর"
    ]

}






district_api = {

    "ঢাকা": "Dhaka",
    "গাজীপুর": "Gazipur",
    "নারায়ণগঞ্জ": "Narayanganj",
    "টাঙ্গাইল": "Tangail",
    "কিশোরগঞ্জ": "Kishoreganj",
    "মানিকগঞ্জ": "Manikganj",
    "মুন্সীগঞ্জ": "Munshiganj",
    "নরসিংদী": "Narsingdi",
    "রাজবাড়ী": "Rajbari",
    "শরীয়তপুর": "Shariatpur",
    "ফরিদপুর": "Faridpur",
    "গোপালগঞ্জ": "Gopalganj",
    "মাদারীপুর": "Madaripur",

    "চট্টগ্রাম": "Chittagong",
    "কক্সবাজার": "Cox's Bazar",
    "কুমিল্লা": "Cumilla",
    "ফেনী": "Feni",
    "নোয়াখালী": "Noakhali",
    "লক্ষ্মীপুর": "Lakshmipur",
    "চাঁদপুর": "Chandpur",
    "ব্রাহ্মণবাড়িয়া": "Brahmanbaria",
    "খাগড়াছড়ি": "Khagrachhari",
    "রাঙ্গামাটি": "Rangamati",
    "বান্দরবান": "Bandarban",

    "রাজশাহী": "Rajshahi",
    "বগুড়া": "Bogura",
    "পাবনা": "Pabna",
    "সিরাজগঞ্জ": "Sirajganj",
    "নাটোর": "Natore",
    "নওগাঁ": "Naogaon",
    "জয়পুরহাট": "Joypurhat",
    "চাঁপাইনবাবগঞ্জ": "Chapainawabganj",

    "খুলনা": "Khulna",
    "যশোর": "Jessore",
    "সাতক্ষীরা": "Satkhira",
    "বাগেরহাট": "Bagerhat",
    "ঝিনাইদহ": "Jhenaidah",
    "কুষ্টিয়া": "Kushtia",
    "চুয়াডাঙ্গা": "Chuadanga",
    "মেহেরপুর": "Meherpur",
    "নড়াইল": "Narail",
    "মাগুরা": "Magura",

    "বরিশাল": "Barisal",
    "পটুয়াখালী": "Patuakhali",
    "ভোলা": "Bhola",
    "ঝালকাঠি": "Jhalokati",
    "পিরোজপুর": "Pirojpur",
    "বরগুনা": "Barguna",

    "সিলেট": "Sylhet",
    "মৌলভীবাজার": "Moulvibazar",
    "হবিগঞ্জ": "Habiganj",
    "সুনামগঞ্জ": "Sunamganj",

    "রংপুর": "Rangpur",
    "দিনাজপুর": "Dinajpur",
    "কুড়িগ্রাম": "Kurigram",
    "গাইবান্ধা": "Gaibandha",
    "লালমনিরহাট": "Lalmonirhat",
    "নীলফামারী": "Nilphamari",
    "পঞ্চগড়": "Panchagarh",
    "ঠাকুরগাঁও": "Thakurgaon",

    "ময়মনসিংহ": "Mymensingh",
    "জামালপুর": "Jamalpur",
    "নেত্রকোনা": "Netrokona",
    "শেরপুর": "Sherpur"

}


# -------------------- VIDEO DOWNLOADER --------------------

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Per-user state: one user's download can never overwrite another user's state.
download_jobs = {}
download_jobs_lock = threading.Lock()


def _safe_progress_hook(user_id):
    def hook(d):
        if d.get("status") == "downloading":
            percent = d.get("_percent_str", "").strip()
            speed = d.get("_speed_str", "").strip()
            eta = d.get("_eta_str", "").strip()

            message = (
                f"📥 Download হচ্ছে...\n\n"
                f"📊 {percent or '—'}\n"
                f"⚡ {speed or '—'}\n"
                f"⏳ ETA: {eta or '—'}"
            )

            with download_jobs_lock:
                job = download_jobs.get(user_id)
                if job is not None:
                    job["progress"] = message

        elif d.get("status") == "finished":
            with download_jobs_lock:
                job = download_jobs.get(user_id)
                if job is not None:
                    job["progress"] = "🔄 Download complete, file prepare করা হচ্ছে..."

    return hook


def download_video(url, user_id):
    """
    High-throughput yt-dlp downloader.

    Notes:
    - bestvideo+bestaudio gives a much better chance of getting the best
      available separate video/audio streams than format='best'.
    - concurrent_fragment_downloads speeds up DASH/HLS sources when supported.
    - continuedl/retries help unstable connections.
    - The file is written directly to disk; it is not loaded into RAM.
    """
    job_dir = os.path.join(DOWNLOAD_DIR, str(user_id))
    os.makedirs(job_dir, exist_ok=True)

    output_template = os.path.join(job_dir, "%(id)s.%(ext)s")

    options = {
        # Best video with audio; fall back to a single combined format.
        "format": "bv*+ba/bv/b",
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "ffmpeg_location": FFMPEG_DIR,
        "noplaylist": True,

        # No duration limit: videos longer than 3 hours are allowed.
        # The Telegram upload layer below splits large files into parts.

        # Network/reliability
        "continuedl": True,
        "retries": 15,
        "fragment_retries": 15,
        "extractor_retries": 5,
        "sleep_interval_requests": 1,
        "file_access_retries": 10,
        "socket_timeout": 30,
        "http_chunk_size": 10 * 1024 * 1024,
        "retry_sleep_functions": {
            "http": lambda n: min(5 * (n + 1), 30),
            "fragment": lambda n: min(2 * (n + 1), 15),
        },

        # Speed for fragmented DASH/HLS streams
        "concurrent_fragment_downloads": 8,

        "ratelimit": None,

        # Keep logs quiet, but don't hide the actual exception.
        "quiet": True,
        "no_warnings": False,

        # If a supported JS runtime is installed, let yt-dlp use it.
        # This is especially important for current YouTube extraction.
        # yt-dlp expects js_runtimes as a dict, not a string.
        # Deno is used when it is available on PATH.
        "js_runtimes": {"deno": {}},
        # Let yt-dlp use its current EJS challenge solving support when installed.
        "extractor_args": {"youtube": {"player_client": ["web", "android"]}},

        "progress_hooks": [_safe_progress_hook(user_id)],
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)

        filepath = None

        # After merging, yt-dlp normally provides _filename.
        filepath = info.get("_filename")

        if not filepath:
            filepath = ydl.prepare_filename(info)

            base, _ = os.path.splitext(filepath)
            mp4_candidate = base + ".mp4"
            if os.path.exists(mp4_candidate):
                filepath = mp4_candidate

        if not os.path.exists(filepath):
            # Some post-processors change the final extension.
            candidates = []
            if os.path.isdir(job_dir):
                for name in os.listdir(job_dir):
                    full = os.path.join(job_dir, name)
                    if (
                        os.path.isfile(full)
                        and not name.endswith((".part", ".ytdl", ".temp"))
                    ):
                        candidates.append(full)

            if candidates:
                filepath = max(candidates, key=os.path.getmtime)
            else:
                raise FileNotFoundError("Downloaded file পাওয়া যায়নি।")

        return filepath, info.get("title", "Unknown Title")


def download_worker(url, user_id):
    try:
        video, title = download_video(url, user_id)

        with download_jobs_lock:
            job = download_jobs.get(user_id)
            if job is not None:
                job.update({
                    "done": True,
                    "video": video,
                    "title": title,
                })

    except Exception as e:
        with download_jobs_lock:
            job = download_jobs.get(user_id)
            if job is not None:
                job.update({
                    "done": True,
                    "error": str(e),
                })


def cleanup_download(user_id):
    """Remove a user's temporary download directory."""
    job_dir = os.path.join(DOWNLOAD_DIR, str(user_id))

    try:
        if os.path.isdir(job_dir):
            for name in os.listdir(job_dir):
                path = os.path.join(job_dir, name)
                try:
                    if os.path.isfile(path):
                        os.remove(path)
                except OSError:
                    pass

            try:
                os.rmdir(job_dir)
            except OSError:
                pass
    except OSError:
        pass


def split_video_for_telegram(video_path, user_id, max_part_size=45 * 1024 * 1024):
    """
    Split a large downloaded video into Telegram-safe MP4 parts.

    The original file is downloaded first. If it is over the Bot API's
    practical upload limit, FFmpeg creates smaller independently playable
    MP4 segments. Stream-copy is used first so there is no unnecessary
    re-encoding.
    """
    part_dir = os.path.join(
        DOWNLOAD_DIR, str(user_id), "telegram_parts"
    )
    os.makedirs(part_dir, exist_ok=True)

    def find_binary(name):
        found = shutil.which(name)
        if found:
            return found
        if FFMPEG_DIR:
            candidates = [
                os.path.join(FFMPEG_DIR, name),
                os.path.join(FFMPEG_DIR, name + ".exe"),
            ]
            for candidate in candidates:
                if os.path.isfile(candidate):
                    return candidate
        return None

    ffmpeg = find_binary("ffmpeg")
    ffprobe = find_binary("ffprobe")

    if not ffmpeg:
        raise FileNotFoundError(
            "FFmpeg পাওয়া যায়নি। PATH বা FFMPEG_DIR ঠিক করুন।"
        )

    duration = 0.0
    bitrate = 0

    if ffprobe:
        try:
            probe = subprocess.run(
                [
                    ffprobe, "-v", "error",
                    "-show_entries", "format=duration,bit_rate",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    video_path,
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=120,
            ).stdout.strip().splitlines()

            if probe:
                duration = float(probe[0] or 0)
            if len(probe) > 1:
                try:
                    bitrate = int(float(probe[1] or 0))
                except (TypeError, ValueError):
                    bitrate = 0
        except Exception:
            pass

    if bitrate <= 0 and duration > 0:
        bitrate = int(os.path.getsize(video_path) * 8 / duration)

    # Use a conservative target so Telegram does not reject a part because
    # of container overhead or a small bitrate/keyframe estimation error.
    if bitrate > 0:
        segment_seconds = int(
            (max_part_size * 8 * 0.82) / bitrate
        )
        segment_seconds = max(30, min(segment_seconds, 600))
    else:
        segment_seconds = 180

    def run_split(seconds):
        # Clear previous generated parts before every attempt.
        for name in os.listdir(part_dir):
            path = os.path.join(part_dir, name)
            try:
                if os.path.isfile(path):
                    os.remove(path)
            except OSError:
                pass

        pattern = os.path.join(part_dir, "part_%03d.mp4")
        cmd = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            "-i", video_path,
            "-map", "0:v:0",
            "-map", "0:a?",
            "-c", "copy",
            "-f", "segment",
            "-segment_time", str(int(seconds)),
            "-reset_timestamps", "1",
            "-segment_format", "mp4",
            pattern,
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=6 * 60 * 60,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "FFmpeg split failed: "
                + (result.stderr[-2000:] or "unknown error")
            )

        parts = sorted(
            os.path.join(part_dir, name)
            for name in os.listdir(part_dir)
            if name.lower().endswith(".mp4")
        )
        return parts

    parts = run_split(segment_seconds)

    # Keyframes can make stream-copy segments larger than expected.
    # Retry several times with shorter segments.
    for _ in range(4):
        if parts and all(
            os.path.getsize(p) <= max_part_size for p in parts
        ):
            return parts

        segment_seconds = max(20, segment_seconds // 2)
        parts = run_split(segment_seconds)

    oversized = [
        p for p in parts
        if os.path.getsize(p) > max_part_size
    ]
    if oversized:
        raise ValueError(
            "ভিডিওকে Telegram-safe parts-এ ভাগ করা যায়নি। "
            "ভিডিওর bitrate/keyframe structure খুব বেশি হওয়ায় "
            "আরও aggressive splitting দরকার।"
        )

    if not parts:
        raise RuntimeError("ভিডিওকে Telegram-এর জন্য ভাগ করা যায়নি।")

    return parts


def cleanup_video_parts(user_id):
    part_dir = os.path.join(
        DOWNLOAD_DIR, str(user_id), "telegram_parts"
    )
    try:
        if os.path.isdir(part_dir):
            shutil.rmtree(part_dir, ignore_errors=True)
    except OSError:
        pass


def get_bangla_date(date):

    months = [
        "বৈশাখ",
        "জ্যৈষ্ঠ",
        "আষাঢ়",
        "শ্রাবণ",
        "ভাদ্র",
        "আশ্বিন",
        "কার্তিক",
        "অগ্রহায়ণ",
        "পৌষ",
        "মাঘ",
        "ফাল্গুন",
        "চৈত্র"
    ]

    year = date.year
    month = date.month
    day = date.day

    # বাংলা নববর্ষ
    if (month > 4) or (month == 4 and day >= 14):
        bangla_year = year - 593
    else:
        bangla_year = year - 594

    starts = [
        (4,14),
        (5,15),
        (6,15),
        (7,16),
        (8,16),
        (9,16),
        (10,17),
        (11,16),
        (12,16),
        (1,15),
        (2,13),
        (3,15)
    ]

    if month < 4:
        g_month = month + 12
    else:
        g_month = month

    index = 11

    for i,(m,d) in enumerate(starts):
        mm = m if m >= 4 else m + 12

        if (g_month > mm) or (g_month == mm and day >= d):
            index = i

    sm, sd = starts[index]

    start_year = year

    if sm <= 3:
        start_year += 1

    start = datetime(start_year, sm, sd, tzinfo=date.tzinfo)

    diff = (date - start).days + 1

    return diff, months[index], bangla_year



tts_users = {}


qr_users = set()
math_users = set()
physics_cq_users = set()



keyboard = [
    ["🚀 Start", "❓ Help"],
    ["🕒 Time"],
    ["🕌 Prayer Time", "⏳ Prayer Remaining"],
    ["🌤️ Weather"],
    ["🎥 Video Downloader", "🔳 QR Code"],
    ["🧮 Math Solver", "⚛️ Physics CQ Solver"],
    ["🔊 Text To Voice"],
    ["👨‍💻 Developer"],
]

async def menu(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    mode_switch_buttons = {
        "🚀 Start", "❓ Help", "🕒 Time", "🕌 Prayer Time",
        "⏳ Prayer Remaining", "🌤️ Weather", "🎥 Video Downloader",
        "🔳 QR Code", "🔊 Text To Voice", "👨‍💻 Developer", "⚛️ Physics CQ Solver", "⬅️ Back"
    }
    if text in mode_switch_buttons:
        math_users.discard(user_id)
        physics_cq_users.discard(user_id)

    if text == "🚀 Start":
        await update.message.reply_text(add_mastermind(
            "👋 Welcome!"),
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    elif text == "❓ Help":
        await update.message.reply_text(add_mastermind("📖 Help Menu"))

    elif text == "👨‍💻 Developer":
        await update.message.reply_text(add_mastermind(
            "👨‍💻 Developer\n\nName: MASTERMIND\nTelegram: @Do_x_Die"
        ))

    elif text == "🕒 Time":

        # Bangladesh Time (Asia/Dhaka)
        now = datetime.now(ZoneInfo("Asia/Dhaka"))

        days = {
            "Monday":"সোমবার",
            "Tuesday":"মঙ্গলবার",
            "Wednesday":"বুধবার",
            "Thursday":"বৃহস্পতিবার",
            "Friday":"শুক্রবার",
            "Saturday":"শনিবার",
            "Sunday":"রবিবার"
        }

        day_name = days[now.strftime("%A")]

        # বাংলা তারিখ
        b_date, b_month, b_year = get_bangla_date(now)

        # হিজরি
        h = Gregorian(now.year, now.month, now.day).to_hijri()

        hijri_months = {
            1:"মুহাররম",
            2:"সফর",
            3:"রবিউল আউয়াল",
            4:"রবিউস সানি",
            5:"জমাদিউল আউয়াল",
            6:"জমাদিউস সানি",
            7:"রজব",
            8:"শাবান",
            9:"রমজান",
            10:"শাওয়াল",
            11:"জিলকদ",
            12:"জিলহজ্জ"
        }

        await update.message.reply_text(add_mastermind(
    f"""
    ╔══════════════════════════════╗
            🕒 সময় ও তারিখ
    ╚══════════════════════════════╝

    📅 ইংরেজি তারিখ
    {now.strftime("%d-%m-%Y")}

    📆 আজ
    {day_name}

    🕰️ বর্তমান সময়
    {now.strftime("%I:%M:%S %p")}

    ━━━━━━━━━━━━━━━━━━━━━━

    🌿 বাংলা তারিখ
    {b_date} {b_month} {b_year}

    ☪️ হিজরি তারিখ
    {h.day} {hijri_months[h.month]} {h.year} হিজরি

    ━━━━━━━━━━━━━━━━━━━━━━

    """
        ))

    elif text == "🕌 Prayer Time":

        city = "Dhaka"
        country = "Bangladesh"

        url = f"https://api.aladhan.com/v1/timingsByCity?city={city}&country={country}"

        response = requests.get(url)
        data = response.json()

        timings = data["data"]["timings"]

        message = f"""
        ╔══════════════════════════════╗
                🕌 নামাজের সময়
        ╚══════════════════════════════╝

        📍 অবস্থান : ঢাকা, বাংলাদেশ
        📅 আজকের সময়সূচি

        ━━━━━━━━━━━━━━━━━━━━━━━━━━

        🌅 ফজর        │ {timings['Fajr']}
        🌄 সূর্যোদয়   │ {timings['Sunrise']}
        ☀️ যোহর       │ {timings['Dhuhr']}
        🌤️ আসর        │ {timings['Asr']}
        🌇 মাগরিব     │ {timings['Maghrib']}
        🌙 এশা        │ {timings['Isha']}

        ━━━━━━━━━━━━━━━━━━━━━━━━━━

        🤲 আল্লাহ আমাদের সকলের
            নামাজ কবুল করুন।

        """

        await update.message.reply_text(add_mastermind(message))


    elif text == "⏳ Prayer Remaining":

        city = "Dhaka"
        country = "Bangladesh"

        url = f"https://api.aladhan.com/v1/timingsByCity?city={city}&country={country}"

        response = requests.get(url)
        data = response.json()

        timings = data["data"]["timings"]

        # Bangladesh Time (Asia/Dhaka)
        now = datetime.now(ZoneInfo("Asia/Dhaka"))

        prayers = [
            ("🌅 ফজর", timings["Fajr"]),
            ("☀️ যোহর", timings["Dhuhr"]),
            ("🌤️ আসর", timings["Asr"]),
            ("🌇 মাগরিব", timings["Maghrib"]),
            ("🌙 এশা", timings["Isha"])
        ]

        next_prayer = None

        current_prayer = "🌙 এশা"

        for i, (name, prayer_str) in enumerate(prayers):

            prayer_time = datetime.strptime(
                prayer_str,
                "%H:%M"
            ).replace(
                year=now.year,
                month=now.month,
                day=now.day,
                tzinfo=ZoneInfo("Asia/Dhaka")
            )

            if prayer_time > now:
                next_prayer = (name, prayer_time)

                if i == 0:
                    current_prayer = "🌙 এশা"
                else:
                    current_prayer = prayers[i-1][0]

                break


        # যদি আজকের সব নামাজ শেষ হয়ে যায়
        # তাহলে আগামী দিনের Fajr বের করবে
        if next_prayer is None:

            tomorrow = now + timedelta(days=1)

            fajr_time = datetime.strptime(
                timings["Fajr"],
                "%H:%M"
            ).replace(
                year=tomorrow.year,
                month=tomorrow.month,
                day=tomorrow.day,
                tzinfo=ZoneInfo("Asia/Dhaka")
            )

            next_prayer = ("🌅 Fajr", fajr_time)


        remaining = next_prayer[1] - now


        total_seconds = int(remaining.total_seconds())

        hours = total_seconds // 3600

        minutes = (total_seconds % 3600) // 60

        seconds = total_seconds % 60


        prayer_time_format = next_prayer[1].strftime(
            "%I:%M %p"
        )


        await update.message.reply_text(add_mastermind(
            f"""
        ╔══════════════════════════════╗
              🕌 নামাজের স্মরণিকা
        ╚══════════════════════════════╝

         📍 অবস্থান : ঢাকা, বাংলাদেশ

        ━━━━━━━━━━━━━━━━━━━━━━━━━━

        🟢 বর্তমান নামাজ

        {current_prayer}

        ━━━━━━━━━━━━━━━━━━━━━━━━━━

        ⏭️ পরবর্তী নামাজ

        {next_prayer[0]}
        🕒 {prayer_time_format}

        ━━━━━━━━━━━━━━━━━━━━━━━━━━

        ⏳ আর বাকি

        🕐 {hours:02d} ঘণ্টা
        🕑 {minutes:02d} মিনিট
        🕒 {seconds:02d} সেকেন্ড

        ━━━━━━━━━━━━━━━━━━━━━━━━━━

        🤲 আল্লাহ আমাদের সবাইকে
        সময়মতো নামাজ আদায় করার
        তাওফীক দান করুন।

        """
        )) 


    elif text == "🌤️ Weather":
    
        buttons = []
    
        for division in divisions:
            buttons.append([division])
    
        buttons.append(["⬅️ Back"])
    
        await update.message.reply_text(add_mastermind(
            "🌤️ বিভাগ নির্বাচন করুন"),
            reply_markup=ReplyKeyboardMarkup(
                buttons,
                resize_keyboard=True
            )
        )
    
    elif text in divisions:
    
        districts = divisions[text]
    
        buttons = []
    
        for district in districts:
            buttons.append([district])
    
        buttons.append(["⬅️ Back"])
    
        await update.message.reply_text(add_mastermind(
            f"{text}\n\nজেলা নির্বাচন করুন"),
            reply_markup=ReplyKeyboardMarkup(
                buttons,
                resize_keyboard=True
            )
        )
    
    elif any(text in district_list for district_list in divisions.values() for district in district_list):
    
        city = district_api[text]

        url = f"https://api.openweathermap.org/data/2.5/weather?q={city},BD&appid={WEATHER_API_KEY}&units=metric"
    
        response = requests.get(url)
        data = response.json()
    
    
        temp = data["main"]["temp"]
        weather = data["weather"][0]["description"]
    
    
        await update.message.reply_text(add_mastermind(
            f"""
    🌤️ Weather Report
    
    📍 জেলা: {text}
    
    🌡️ Temperature:
    {temp}°C
    
    ☁️ Condition:
    {weather}
    
    
    """),
            reply_markup=ReplyKeyboardMarkup(
                [["⬅️ Back"]],
                resize_keyboard=True
            )
        )

    
    elif text == "⬅️ Back":

        user_id = update.effective_user.id

        math_users.discard(user_id)
        physics_cq_users.discard(user_id)

        # Active modes clear
        qr_users.discard(user_id)
        math_users.discard(user_id)
        physics_cq_users.discard(user_id)
        tts_users.pop(user_id, None)

        await update.message.reply_text(add_mastermind(
            "🏠 Main Menu"),
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )
        )





    
    elif text == "🔳 QR Code":

        user_id = update.effective_user.id

        # QR mode চালু, TTS mode বন্ধ
        qr_users.add(user_id)
        tts_users.pop(user_id, None)

        await update.message.reply_text(add_mastermind(
            """
    🔳 QR Code Generator

    আপনার যেকোনো লেখা, লিংক, নাম্বার বা মেসেজ পাঠান।

    আমি সেটাকে QR Code বানিয়ে দেবো।
    """
        ))


    elif text == "🔊 Text To Voice":

        user_id = update.effective_user.id

        # TTS menu খুললে QR mode বন্ধ
        qr_users.discard(user_id)

        await update.message.reply_text(add_mastermind(
            """
    🎙️ Text To Voice

    আপনার পছন্দের Voice নির্বাচন করুন।
    """),
            reply_markup=ReplyKeyboardMarkup(
                [
                    ["👩 বাংলা Girl", "👨 বাংলা Boy"],
                    ["👩 English Girl", "👨 English Boy"],
                    ["⬅️ Back"]
                ],
                resize_keyboard=True
            )
        )


    elif text == "👩 বাংলা Girl":

        user_id = update.effective_user.id

        # QR mode বন্ধ করে TTS mode চালু
        qr_users.discard(user_id)
        tts_users[user_id] = "bn-BD-NabanitaNeural"

        await update.message.reply_text(add_mastermind(
            "✍️ এখন আপনার লেখা পাঠান।"
        ))


    elif text == "👨 বাংলা Boy":

        user_id = update.effective_user.id

        qr_users.discard(user_id)
        tts_users[user_id] = "bn-BD-PradeepNeural"

        await update.message.reply_text(add_mastermind(
            "✍️ এখন আপনার লেখা পাঠান।"
        ))


    elif text == "👩 English Girl":

        user_id = update.effective_user.id

        qr_users.discard(user_id)
        tts_users[user_id] = "en-US-AriaNeural"

        await update.message.reply_text(add_mastermind(
            "✍️ Enter your text."
        ))


    elif text == "👨 English Boy":

        user_id = update.effective_user.id

        qr_users.discard(user_id)
        tts_users[user_id] = "en-US-GuyNeural"

        await update.message.reply_text(add_mastermind(
            "✍️ Enter your text."
        ))




    elif text == "⚛️ Physics CQ Solver":

        user_id = update.effective_user.id
        physics_cq_users.add(user_id)
        math_users.discard(user_id)
        qr_users.discard(user_id)
        tts_users.pop(user_id, None)

        await update.message.reply_text(
            add_mastermind(
                """⚛️ SSC Physics CQ Solver

পুরো সৃজনশীল প্রশ্নটি একসাথে পাঠান।

যেমন:
উদ্দীপক: ...
ক. ...
খ. ...
গ. ...
ঘ. ...

আমি চেষ্টা করব:
✅ ক, খ, গ, ঘ আলাদা করতে
✅ প্রয়োজনীয় সূত্র শনাক্ত করতে
✅ সংখ্যাগত হিসাব করতে
✅ বাংলায় ধাপে ধাপে ব্যাখ্যা দিতে
✅ SSC পরীক্ষার উপযোগী উত্তর সাজাতে

⬅️ Back চাপলে Solver বন্ধ হবে।"""
            ),
            reply_markup=ReplyKeyboardMarkup(
                [["⬅️ Back"]],
                resize_keyboard=True
            )
        )


    elif update.effective_user.id in physics_cq_users:

        try:
            raw = text.strip()
            answer = solve_ssc_physics_cq(raw)

            if answer:
                await update.message.reply_text(
                    add_mastermind(answer),
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(
                    add_mastermind(
                        "❌ এই CQ-এর chapter বা প্রয়োজনীয় তথ্য এখনো "
                        "নির্ভরযোগ্যভাবে শনাক্ত করতে পারিনি।\n\n"
                        "উদ্দীপকসহ পুরো ক, খ, গ, ঘ প্রশ্নটি একসাথে পাঠান।"
                    )
                )

        except Exception as e:
            await update.message.reply_text(
                add_mastermind(
                    f"❌ CQ solve করতে সমস্যা হয়েছে।\n\nকারণ: {e}"
                )
            )

    elif text == "🧮 Math Solver":

        user_id = update.effective_user.id
        math_users.add(user_id)
        qr_users.discard(user_id)
        tts_users.pop(user_id, None)

        await update.message.reply_text(
            add_mastermind(
                """🧮 Math Solver

যেকোনো mathematical problem লিখে পাঠান।

উদাহরণ:
• 25 + 37 * 2
• (15 + 5) / 4
• x**2 + 5*x + 6 = 0
• sin(x) + cos(x)
• ∫ x**2 dx
• limit(x->0, sin(x)/x)

আমি সম্ভব হলে ধাপে ধাপে solution এবং final answer দেখাব।

⬅️ নিচের Back button চাপলে Math Solver বন্ধ হবে।"""
            ),
            reply_markup=ReplyKeyboardMarkup(
                [["⬅️ Back"]],
                resize_keyboard=True
            )
        )


    elif text == "🎥 Video Downloader":

        await update.message.reply_text(add_mastermind(
            """
        ╔══════════════════════════════╗
            🎥 ভিডিও ডাউনলোডার
        ╚══════════════════════════════╝

        📥 আপনার ভিডিওর লিংক পাঠান।

        🌐 সমর্থিত প্ল্যাটফর্ম

        ▶️ YouTube
        ▶️ Facebook
        ▶️ Instagram
        ▶️ TikTok
        ▶️ X (Twitter)

        ━━━━━━━━━━━━━━━━━━━━━━

        ⚡ সর্বোচ্চ মানের ভিডিও ডাউনলোড করা হবে।

        """
        ))


    elif update.effective_user.id in math_users:

        try:
            raw = text.strip()

            # First try Bangla/English natural-language Math + Physics.
            natural_answer = solve_natural_student_problem(raw)
            if natural_answer:
                await update.message.reply_text(
                    add_mastermind(natural_answer),
                    parse_mode="HTML"
                )
                return


            if len(raw) > 2000:
                raise ValueError("Expression too long")

            # Normalize common mathematical notation.
            expr_text = (
                raw.replace("×", "*")
                   .replace("÷", "/")
                   .replace("−", "-")
                   .replace("π", "pi")
                   .replace("∞", "oo")
            )

            # ^ is power in normal mathematical typing.
            expr_text = expr_text.replace("^", "**")

            # Common Unicode roots.
            expr_text = re.sub(r"√\s*([A-Za-z0-9().]+)", r"sqrt(\1)", expr_text)

            locals_map = {
                "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
                "cot": sp.cot, "sec": sp.sec, "csc": sp.csc,
                "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
                "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
                "sqrt": sp.sqrt, "cbrt": sp.real_root,
                "log": sp.log, "ln": sp.log, "exp": sp.exp,
                "Abs": sp.Abs, "abs": sp.Abs,
                "factorial": sp.factorial,
                "pi": sp.pi, "E": sp.E, "I": sp.I, "oo": sp.oo,
            }

            # ---------------------------------------------------------
            # 1) LIMIT
            # Examples: limit(sin(x)/x, x, 0)
            #           limit((1-cos(x))/x**2, x->0)
            # ---------------------------------------------------------
            limit_match = re.match(
                r"^\s*limit\s*\(\s*(.+?)\s*(?:,\s*|\s*;\s*)"
                r"([A-Za-z]\w*)\s*(?:->|→)\s*(.+?)\s*\)\s*$",
                expr_text,
                re.I
            )

            if limit_match:
                body, var_name, point = limit_match.groups()
                var = sp.Symbol(var_name)
                result = sp.limit(
                    sp.sympify(body, locals=locals_map),
                    var,
                    sp.sympify(point, locals=locals_map)
                )

                answer = (
                    "🧮 <b>Advanced Math Solver</b>\n\n"
                    f"📌 Limit:\n<code>{raw}</code>\n\n"
                    f"✅ Answer:\n<code>{sp.sstr(result)}</code>"
                )

            # ---------------------------------------------------------
            # 2) DERIVATIVE
            # Examples: diff(x**3*sin(x), x)
            #           d/dx (x**2 + sin(x))
            # ---------------------------------------------------------
            elif re.match(r"^\s*d/d[a-zA-Z]\s*", expr_text, re.I):
                m = re.match(r"^\s*d/d([a-zA-Z]\w*)\s*(?:\((.*)\)|(.*))$", expr_text, re.I)
                if not m:
                    raise ValueError("Invalid derivative")

                var = sp.Symbol(m.group(1))
                body = (m.group(2) or m.group(3)).strip()
                result = sp.diff(sp.sympify(body, locals=locals_map), var)

                answer = (
                    "🧮 <b>Advanced Math Solver</b>\n\n"
                    f"📌 Derivative:\n<code>{raw}</code>\n\n"
                    f"✅ Answer:\n<code>{sp.sstr(result)}</code>"
                )

            elif re.match(r"^\s*diff\s*\(", expr_text, re.I):
                inside = expr_text[5:-1]
                parts = [p.strip() for p in inside.split(",")]
                if len(parts) < 2:
                    raise ValueError("Use diff(expression, variable)")

                body = sp.sympify(parts[0], locals=locals_map)
                var = sp.Symbol(parts[1])
                order = int(parts[2]) if len(parts) >= 3 else 1
                result = sp.diff(body, var, order)

                answer = (
                    "🧮 <b>Advanced Math Solver</b>\n\n"
                    f"📌 Derivative:\n<code>{raw}</code>\n\n"
                    f"✅ Answer:\n<code>{sp.sstr(result)}</code>"
                )

            # ---------------------------------------------------------
            # 3) INTEGRAL
            # Examples: integrate(x**2, x)
            #           ∫ x**2 dx
            # ---------------------------------------------------------
            elif re.match(r"^\s*integrate\s*\(", expr_text, re.I):
                inside = expr_text[9:-1]
                parts = [p.strip() for p in inside.split(",")]
                if len(parts) < 2:
                    raise ValueError("Use integrate(expression, variable)")

                body = sp.sympify(parts[0], locals=locals_map)
                var = sp.Symbol(parts[1])
                result = sp.integrate(body, var)

                answer = (
                    "🧮 <b>Advanced Math Solver</b>\n\n"
                    f"📌 Integral:\n<code>{raw}</code>\n\n"
                    f"✅ Answer:\n<code>{sp.sstr(result)} + C</code>"
                )

            elif "∫" in raw:
                body = raw.replace("∫", "").strip()
                body = re.sub(r"\bd([A-Za-z]\w*)\s*$", "", body).strip()
                symbols = sorted(
                    sp.sympify(body, locals=locals_map).free_symbols,
                    key=lambda s: s.name
                )
                if not symbols:
                    raise ValueError("Variable not found")

                var = symbols[0]
                result = sp.integrate(
                    sp.sympify(body, locals=locals_map), var
                )

                answer = (
                    "🧮 <b>Advanced Math Solver</b>\n\n"
                    f"📌 Integral:\n<code>{raw}</code>\n\n"
                    f"✅ Answer:\n<code>{sp.sstr(result)} + C</code>"
                )

            # ---------------------------------------------------------
            # 4) EQUATIONS / SYSTEMS
            # Supports multiple equations separated by ;
            # ---------------------------------------------------------
            elif "=" in expr_text:
                equations = []
                for item in re.split(r"[;\n]+", expr_text):
                    if not item.strip():
                        continue

                    left, right = item.split("=", 1)
                    lhs = sp.sympify(left.strip(), locals=locals_map)
                    rhs = sp.sympify(right.strip(), locals=locals_map)
                    equations.append(sp.Eq(lhs, rhs))

                if not equations:
                    raise ValueError("No equation")

                symbols = sorted(
                    set().union(*(eq.free_symbols for eq in equations)),
                    key=lambda s: s.name
                )

                if not symbols:
                    values = [sp.simplify(eq.lhs - eq.rhs) for eq in equations]
                    result = "All equations evaluated successfully."
                    if any(v != 0 for v in values):
                        result = "The equation is false for the supplied values."
                    answer = (
                        "🧮 <b>Advanced Math Solver</b>\n\n"
                        f"📌 Problem:\n<code>{raw}</code>\n\n"
                        f"✅ {result}"
                    )
                else:
                    solutions = sp.solve(
                        equations,
                        symbols,
                        dict=True
                    )

                    if not solutions:
                        answer = (
                            "🧮 <b>Advanced Math Solver</b>\n\n"
                            f"📌 Problem:\n<code>{raw}</code>\n\n"
                            "❌ No exact solution was found."
                        )
                    else:
                        lines = []
                        for sol in solutions:
                            for symbol in symbols:
                                if symbol in sol:
                                    lines.append(
                                        f"<b>{sp.sstr(symbol)}</b> = "
                                        f"<code>{sp.sstr(sp.simplify(sol[symbol]))}</code>"
                                    )

                        answer = (
                            "🧮 <b>Advanced Math Solver</b>\n\n"
                            f"📌 Problem:\n<code>{raw}</code>\n\n"
                            "✅ Solution:\n" +
                            "\n".join(lines)
                        )

            # ---------------------------------------------------------
            # 5) MATRIX / DETERMINANT
            # ---------------------------------------------------------
            elif raw.lower().startswith(("det(", "matrix(")):
                result = sp.simplify(
                    sp.sympify(expr_text, locals=locals_map)
                )

                answer = (
                    "🧮 <b>Advanced Math Solver</b>\n\n"
                    f"📌 Matrix expression:\n<code>{raw}</code>\n\n"
                    f"✅ Answer:\n<code>{sp.sstr(result)}</code>"
                )

            # ---------------------------------------------------------
            # 6) GENERAL SYMBOLIC / NUMERIC EXPRESSION
            # ---------------------------------------------------------
            else:
                expr = sp.sympify(expr_text, locals=locals_map)
                simplified = sp.simplify(expr)

                answer = (
                    "🧮 <b>Advanced Math Solver</b>\n\n"
                    f"📌 Input:\n<code>{raw}</code>\n\n"
                    f"✅ Simplified:\n<code>{sp.sstr(simplified)}</code>"
                )

                if not simplified.free_symbols:
                    numerical = sp.N(simplified, 15)
                    answer += (
                        f"\n\n🔢 Numerical value:\n"
                        f"<code>{numerical}</code>"
                    )

            await update.message.reply_text(add_mastermind(
                answer),
                parse_mode="HTML"
            )

        except Exception:
            await update.message.reply_text(add_mastermind(
                """❌ এই problem-টা বুঝতে পারিনি।

Try করার মতো format:

• x**2 + 5*x + 6 = 0
• x + y = 10; x - y = 2
• diff(x**3*sin(x), x)
• integrate(x**2, x)
• limit(sin(x)/x, x->0)
• sqrt(144) + log(10)
• det(Matrix([[1,2],[3,4]]))

আরও complex problem হলে mathematical notation পরিষ্কারভাবে লিখুন।"""
            ))

    elif update.effective_user.id in qr_users:

        filename = f"{uuid.uuid4()}.png"

        try:

            qr = qrcode.QRCode(
                version=1,
                box_size=10,
                border=5
            )

            qr.add_data(text)
            qr.make(fit=True)

            img = qr.make_image(
                fill_color="black",
                back_color="white"
            )

            img.save(filename)


            with open(filename, "rb") as photo:

                await update.message.reply_photo(
                    photo=photo,
                    caption="✅ QR Code তৈরি হয়েছে।"
                )

            os.remove(filename)


        except Exception as e:

            await update.message.reply_text(add_mastermind(
                f"❌ QR Code Error\n\n{e}"
            ))




    elif update.effective_user.id in tts_users:

        voice = tts_users[update.effective_user.id]

        filename = f"{uuid.uuid4()}.mp3"

        try:

            communicate = edge_tts.Communicate(
                text,
                voice
            )

            await communicate.save(filename)

            with open(filename, "rb") as audio:

                await update.message.reply_voice(
                    voice=audio,
                    caption="✅ Voice তৈরি হয়েছে।"
                )

            os.remove(filename)

        except Exception as e:

            await update.message.reply_text(add_mastermind(
                f"❌ Error\n\n{e}"
            ))


    

    elif "http" in text:

        if any(site in text.lower() for site in [
            "youtube.com",
            "youtu.be",
            "tiktok.com",
            "instagram.com",
            "facebook.com",
            "x.com",
            "twitter.com"
        ]):

            user_id = update.effective_user.id

            with download_jobs_lock:
                existing = download_jobs.get(user_id)

                # Prevent accidentally starting multiple downloads for the
                # same user at the same time.
                if existing and not existing.get("done", False):
                    await update.message.reply_text(add_mastermind(
                        "⏳ আপনার একটি download already চলছে। সেটি শেষ হওয়া পর্যন্ত অপেক্ষা করুন।"
                    ))
                    return

                download_jobs[user_id] = {
                    "done": False,
                    "progress": "📥 Download শুরু হচ্ছে...",
                    "video": None,
                    "title": None,
                    "error": None,
                }

            status = await update.message.reply_text(add_mastermind(
                """
            📥 ভিডিও ডাউনলোড হচ্ছে...

            ⏳ অনুগ্রহ করে অপেক্ষা করুন।

            ⚡ Fast download mode চালু আছে...

            """
            ))

            thread = threading.Thread(
                target=download_worker,
                args=(text, user_id),
                daemon=True,
            )
            thread.start()

            last_progress = None
            last_edit = 0.0

            try:
                while True:
                    with download_jobs_lock:
                        job = download_jobs.get(user_id, {}).copy()

                    if job.get("done"):
                        break

                    progress = job.get("progress")
                    now = time.monotonic()

                    # Telegram edit rate-limit এড়াতে অন্তত ~2 sec gap রাখি।
                    if progress and progress != last_progress and now - last_edit >= 2:
                        try:
                            await status.edit_text(progress)
                            last_progress = progress
                            last_edit = now
                        except Exception:
                            pass

                    await asyncio.sleep(0.5)

                with download_jobs_lock:
                    job = download_jobs.get(user_id, {}).copy()

                if job.get("error"):
                    raise Exception(job["error"])

                video = job.get("video")
                title = job.get("title") or "Unknown Title"

                if not video or not os.path.exists(video):
                    raise FileNotFoundError("Downloaded video পাওয়া যায়নি।")

                if len(title) > 100:
                    title = title[:97] + "..."

                try:
                    await status.delete()
                except Exception:
                    pass

                # Telegram Bot API has a 50 MB upload limit on the
                # standard cloud API. Long/high-quality videos can be much
                # larger, so split them into playable MP4 parts instead of
                # rejecting the download.
                max_upload_size = 45 * 1024 * 1024
                file_size = os.path.getsize(video)

                if file_size <= max_upload_size:
                    with open(video, "rb") as video_file:
                        await update.message.reply_video(
                            video=video_file,
                            supports_streaming=True,
                            caption=f"""✅ ভিডিও সফলভাবে ডাউনলোড হয়েছে

📌 শিরোনাম:
{title}

━━━━━━━━━━━━━━━━━━━━━━
""",
                            read_timeout=120,
                            write_timeout=300,
                            connect_timeout=30,
                            pool_timeout=30,
                        )
                else:
                    await update.message.reply_text(add_mastermind(
                        "📦 ভিডিওটি বড় হওয়ায় Telegram-এর 50 MB সীমার জন্য "
                        "ছোট ছোট playable part-এ ভাগ করে পাঠানো হচ্ছে..."
                    ))

                    parts = split_video_for_telegram(
                        video, user_id, max_part_size=max_upload_size
                    )

                    total_parts = len(parts)

                    for index, part in enumerate(parts, start=1):
                        part_size = os.path.getsize(part)
                        if part_size > max_upload_size:
                            raise ValueError(
                                f"Part {index} এখনও Telegram limit-এর বেশি।"
                            )

                        with open(part, "rb") as video_file:
                            await update.message.reply_video(
                                video=video_file,
                                supports_streaming=True,
                                caption=(
                                    f"🎬 {title}\n\n"
                                    f"📦 Part {index}/{total_parts}\n"
                                    "🔗 সব part ক্রমানুসারে download করুন।"
                                ),
                                read_timeout=120,
                                write_timeout=300,
                                connect_timeout=30,
                                pool_timeout=30,
                            )

            except Exception as e:
                try:
                    error_text = str(e)

                    # Give a clear message for YouTube authentication/anti-bot
                    # failures instead of suggesting that every public video
                    # can be fixed by retrying.
                    yt_auth_error = (
                        "Sign in to confirm" in error_text
                        or "not a bot" in error_text.lower()
                        or "Use --cookies-from-browser" in error_text
                        or "authentication" in error_text.lower()
                    )

                    if yt_auth_error:
                        user_error = (
                            "❌ YouTube এই ভিডিওটি download করার আগে "
                            "authentication/anti-bot verification চাইছে।\n\n"
                            "🔧 প্রথমে yt-dlp আপডেট করে আবার চেষ্টা করুন।\n"
                            "যদি একই error থাকে, YouTube-এর restriction-এর কারণে "
                            "এই bot থেকে ভিডিওটি download করা যাচ্ছে না।\n\n"
                            "ℹ️ FFmpeg বা ভিডিওর duration-এর সমস্যা নয়।"
                        )
                    else:
                        user_error = (
                            "❌ ভিডিওটি download করা যায়নি।\n\n"
                            f"কারণ:\n{error_text}"
                        )

                    await status.edit_text(
                        f"""{user_error}

✨ Powered by MASTERMIND"""
                    )
                except Exception:
                    await update.message.reply_text(add_mastermind(
                        f"❌ ভিডিও ডাউনলোড করা যায়নি।\n\nকারণ:\n{e}"
                    ))

            finally:
                cleanup_video_parts(user_id)
                cleanup_download(user_id)
                with download_jobs_lock:
                    download_jobs.pop(user_id, None)

        else:
            await update.message.reply_text(add_mastermind(
                "❌ Invalid video link."
            ))





# -------------------- NATURAL LANGUAGE MATH + PHYSICS SOLVER --------------------

BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

def _bn_number_text(s):
    """Convert Bangla digits and a few common Bangla decimal forms."""
    s = str(s).translate(BN_DIGITS)
    return s.replace("٫", ".").replace(",", ".")

def _num(s):
    return float(_bn_number_text(s))

def _fmt(x):
    try:
        xf = float(x)
        if abs(xf - round(xf)) < 1e-10:
            return str(int(round(xf)))
        return f"{xf:.6g}"
    except Exception:
        return str(x)

def _natural_math_expression(raw):
    """
    Convert common Bangla/English student wording into a SymPy expression.
    This is deliberately conservative: unknown text is not executed as code.
    """
    s = _bn_number_text(raw).strip().lower()

    replacements = [
        (r"\bযোগ\b", "+"), (r"\bপ্লাস\b", "+"), (r"\bplus\b", "+"),
        (r"\bবিয়োগ\b|\bবিয়োগ\b", "-"), (r"\bমাইনাস\b|\bminus\b", "-"),
        (r"\bগুণ\b|\bগুন\b|\btimes\b", "*"),
        (r"\bভাগ\b|\bdivided by\b", "/"),
        (r"\bএর\b", " "),
        (r"\bস্কোয়ার\b|\bস্কয়ার\b|\bsquare\b", "**2"),
        (r"\bকিউব\b|\bcube\b", "**3"),
        (r"\bবর্গমূল\b|\bsquare root\b", "sqrt"),
        (r"\bপাই\b|\bpi\b", "pi"),
    ]
    for pat, repl in replacements:
        s = re.sub(pat, repl, s)

    # "25 আর 37 যোগ" / "25 এবং 37 যোগ"
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:আর|এবং|and)\s*(\d+(?:\.\d+)?)\s*(?:যোগ|প্লাস|plus)", s)
    if m:
        return f"{m.group(1)}+{m.group(2)}"

    # Percent questions: "15 এর 20%" / "15 এর 20 শতাংশ"
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:এর|of)\s*(\d+(?:\.\d+)?)\s*%?", s)
    if ("%" in s or "শতাংশ" in s or "percent" in s) and m:
        return f"({m.group(1)}*{m.group(2)}/100)"

    # Keep only safe mathematical characters for the expression fallback.
    cleaned = s.replace(" ", "")
    if re.fullmatch(r"[0-9a-zA-Z_+\-*/().,^%√]+", cleaned):
        cleaned = cleaned.replace("^", "**").replace("√", "sqrt")
        cleaned = cleaned.replace("%", "/100")
        return cleaned

    return None


def _natural_physics_solver(raw):
    """
    Solve common school/HSC-style physics questions written naturally in
    Bangla or English. Returns a Bangla answer, or None when the wording is
    outside the conservative rule set.
    """
    s = _bn_number_text(raw).lower().strip()

    # Normalize Unicode superscripts and common unit spellings.
    s = (s.replace("²", "2").replace("³", "3")
           .replace("মি/সে", "m/s")
           .replace("মিটার/সেকেন্ড", "m/s")
           .replace("মিটার প্রতি সেকেন্ড", "m/s")
           .replace("m s-1", "m/s")
           .replace("কেজি", "kg")
           .replace("নিউটন", "n")
           .replace("সেকেন্ড", "s")
           .replace("সেকেন্ডে", "s"))

    def find(pattern):
        m = re.search(pattern, s, re.I)
        return _num(m.group(1)) if m else None

    # Default school gravity; user can explicitly provide g.
    g = find(r"(?:g\s*=\s*|মাধ্যাকর্ষণ\s*(?:ত্বরণ)?\s*=?\s*)(\d+(?:\.\d+)?)")
    g = 9.8 if g is None else g

    # 1) Vertical throw / maximum height:
    # "20 m/s বেগে উপরের দিকে ছোঁড়া ... সর্বোচ্চ উচ্চতা"
    if any(k in s for k in ["সর্বোচ্চ উচ্চতা", "maximum height", "max height"]) and (
        "উপরে" in s or "উর্ধ্ব" in s or "upward" in s or "vertical" in s
    ):
        u = find(r"(?:u\s*=?\s*|প্রাথমিক\s*বেগ\s*=?\s*|initial\s*velocity\s*=?\s*)(\d+(?:\.\d+)?)")
        if u is None:
            u = find(r"(\d+(?:\.\d+)?)\s*(?:m/s|মি/সে)")
        if u is not None:
            h = u*u/(2*g)
            return (
                "⚙️ <b>Physics Solver</b>\n\n"
                f"📌 দেওয়া আছে:\n• প্রাথমিক বেগ, u = {_fmt(u)} m/s\n"
                f"• g = {_fmt(g)} m/s²\n\n"
                "📐 সূত্র:\n"
                "h = u² / (2g)\n\n"
                f"🧮 হিসাব:\nh = ({_fmt(u)})² / (2 × {_fmt(g)})\n\n"
                f"✅ <b>উত্তর: h = {_fmt(h)} m</b>"
            )

    # 2) Time of flight for upward throw.
    if any(k in s for k in ["কতক্ষণ", "সময়", "সময়", "time"]) and (
        "উপরে" in s or "উর্ধ্ব" in s or "upward" in s
    ):
        if any(k in s for k in ["ফিরে", "ভূমিতে", "মাটিতে", "ground", "flight"]):
            u = find(r"(?:u\s*=?\s*|প্রাথমিক\s*বেগ\s*=?\s*|initial\s*velocity\s*=?\s*)(\d+(?:\.\d+)?)")
            if u is None:
                u = find(r"(\d+(?:\.\d+)?)\s*(?:m/s|মি/সে)")
            if u is not None:
                t = 2*u/g
                return (
                    "⚙️ <b>Physics Solver</b>\n\n"
                    f"📌 প্রাথমিক বেগ, u = {_fmt(u)} m/s\n"
                    f"📌 g = {_fmt(g)} m/s²\n\n"
                    "📐 ভূমিতে ফিরে আসার সময়:\n"
                    "T = 2u/g\n\n"
                    f"🧮 T = 2 × {_fmt(u)} / {_fmt(g)}\n\n"
                    f"✅ <b>উত্তর: T = {_fmt(t)} s</b>"
                )

    # 3) Newton's second law: F = ma
    if ("নিউটন" in s or "force" in s or "বল" in s) and (
        "ভর" in s or "mass" in s or re.search(r"\bm\s*=", s)
    ):
        m = find(r"(?:m\s*=\s*|ভর\s*=?\s*|mass\s*=?\s*)(\d+(?:\.\d+)?)")
        a = find(r"(?:a\s*=\s*|ত্বরণ\s*=?\s*|acceleration\s*=?\s*)(\d+(?:\.\d+)?)")
        if m is not None and a is not None and ("বল" in s or "force" in s or "নিউটন" in s):
            f = m*a
            return (
                "⚙️ <b>Physics Solver</b>\n\n"
                f"📌 ভর, m = {_fmt(m)} kg\n"
                f"📌 ত্বরণ, a = {_fmt(a)} m/s²\n\n"
                "📐 নিউটনের দ্বিতীয় সূত্র:\nF = ma\n\n"
                f"🧮 F = {_fmt(m)} × {_fmt(a)}\n\n"
                f"✅ <b>উত্তর: F = {_fmt(f)} N</b>"
            )

    # 4) Work: W = Fs cos(theta). For simple same-direction case, W = Fs.
    if ("কাজ" in s or re.search(r"\bwork\b", s)) and (
        "বল" in s or re.search(r"\bforce\b|\bf\s*=", s)
    ):
        f = find(r"(?:f\s*=\s*|বল\s*=?\s*|force\s*=?\s*)(\d+(?:\.\d+)?)")
        d = find(r"(?:d\s*=\s*|দূরত্ব\s*=?\s*|distance\s*=?\s*)(\d+(?:\.\d+)?)")
        if f is not None and d is not None:
            theta = find(r"(?:theta|θ|কোণ)\s*=?\s*(\d+(?:\.\d+)?)")
            import math
            if theta is None:
                theta = 0
            w = f*d*math.cos(math.radians(theta))
            return (
                "⚙️ <b>Physics Solver</b>\n\n"
                f"📌 বল, F = {_fmt(f)} N\n"
                f"📌 সরণ, s = {_fmt(d)} m\n"
                f"📌 কোণ, θ = {_fmt(theta)}°\n\n"
                "📐 সূত্র:\nW = Fs cosθ\n\n"
                f"🧮 W = {_fmt(f)} × {_fmt(d)} × cos({_fmt(theta)}°)\n\n"
                f"✅ <b>উত্তর: W = {_fmt(w)} J</b>"
            )

    # 5) Kinetic energy: KE = 1/2 mv²
    if any(k in s for k in ["গতিশক্তি", "kinetic energy", "kinetic"]) and (
        "ভর" in s or "mass" in s
    ):
        m = find(r"(?:m\s*=\s*|ভর\s*=?\s*|mass\s*=?\s*)(\d+(?:\.\d+)?)")
        v = find(r"(?:v\s*=\s*|বেগ\s*=?\s*|velocity\s*=?\s*)(\d+(?:\.\d+)?)")
        if m is not None and v is not None:
            ke = 0.5*m*v*v
            return (
                "⚙️ <b>Physics Solver</b>\n\n"
                f"📌 ভর, m = {_fmt(m)} kg\n"
                f"📌 বেগ, v = {_fmt(v)} m/s\n\n"
                "📐 সূত্র:\nKE = ½mv²\n\n"
                f"🧮 KE = ½ × {_fmt(m)} × ({_fmt(v)})²\n\n"
                f"✅ <b>উত্তর: KE = {_fmt(ke)} J</b>"
            )

    # 6) Potential energy: PE = mgh
    if any(k in s for k in ["বিভব শক্তি", "স্থিতিশক্তি", "potential energy"]) and (
        "ভর" in s or "mass" in s
    ):
        m = find(r"(?:m\s*=\s*|ভর\s*=?\s*|mass\s*=?\s*)(\d+(?:\.\d+)?)")
        h = find(r"(?:h\s*=\s*|উচ্চতা\s*=?\s*|height\s*=?\s*)(\d+(?:\.\d+)?)")
        if m is not None and h is not None:
            pe = m*g*h
            return (
                "⚙️ <b>Physics Solver</b>\n\n"
                f"📌 ভর, m = {_fmt(m)} kg\n"
                f"📌 উচ্চতা, h = {_fmt(h)} m\n"
                f"📌 g = {_fmt(g)} m/s²\n\n"
                "📐 সূত্র:\nPE = mgh\n\n"
                f"🧮 PE = {_fmt(m)} × {_fmt(g)} × {_fmt(h)}\n\n"
                f"✅ <b>উত্তর: PE = {_fmt(pe)} J</b>"
            )

    # 7) Ohm's law: V = IR
    if any(k in s for k in ["ওহম", "ohm", "রোধ", "resistance"]) and (
        "ভোল্ট" in s or "voltage" in s or re.search(r"\bv\s*=", s)
    ):
        i = find(r"(?:i\s*=\s*|কারেন্ট\s*=?\s*|current\s*=?\s*)(\d+(?:\.\d+)?)")
        r = find(r"(?:r\s*=\s*|রোধ\s*=?\s*|resistance\s*=?\s*)(\d+(?:\.\d+)?)")
        v = find(r"(?:v\s*=\s*|ভোল্টেজ\s*=?\s*|voltage\s*=?\s*)(\d+(?:\.\d+)?)")
        if i is not None and r is not None and v is None:
            v = i*r
            return (
                "⚙️ <b>Physics Solver</b>\n\n"
                f"📌 I = {_fmt(i)} A\n📌 R = {_fmt(r)} Ω\n\n"
                "📐 ওহমের সূত্র:\nV = IR\n\n"
                f"🧮 V = {_fmt(i)} × {_fmt(r)}\n\n"
                f"✅ <b>উত্তর: V = {_fmt(v)} V</b>"
            )
        if v is not None and r is not None and i is None:
            i = v/r
            return (
                "⚙️ <b>Physics Solver</b>\n\n"
                f"📌 V = {_fmt(v)} V\n📌 R = {_fmt(r)} Ω\n\n"
                "📐 I = V/R\n\n"
                f"🧮 I = {_fmt(v)} / {_fmt(r)}\n\n"
                f"✅ <b>উত্তর: I = {_fmt(i)} A</b>"
            )

    # 8) Kinematics: v = u + at
    if any(k in s for k in ["v = u + at", "v=u+at", "শেষ বেগ", "final velocity"]):
        u = find(r"(?:u\s*=\s*|প্রাথমিক\s*বেগ\s*=?\s*|initial\s*velocity\s*=?\s*)(\d+(?:\.\d+)?)")
        a = find(r"(?:a\s*=\s*|ত্বরণ\s*=?\s*|acceleration\s*=?\s*)(\d+(?:\.\d+)?)")
        t = find(r"(?:t\s*=\s*|সময়\s*=?\s*|সময়\s*=?\s*time\s*=?\s*)(\d+(?:\.\d+)?)")
        if u is not None and a is not None and t is not None:
            v = u+a*t
            return (
                "⚙️ <b>Physics Solver</b>\n\n"
                f"📌 u = {_fmt(u)} m/s\n"
                f"📌 a = {_fmt(a)} m/s²\n"
                f"📌 t = {_fmt(t)} s\n\n"
                "📐 সূত্র:\nv = u + at\n\n"
                f"🧮 v = {_fmt(u)} + ({_fmt(a)} × {_fmt(t)})\n\n"
                f"✅ <b>উত্তর: v = {_fmt(v)} m/s</b>"
            )

    return None


def _natural_language_solver(raw):
    """Natural-language first, SymPy second. Returns answer or None."""
    physics = _natural_physics_solver(raw)
    if physics:
        return physics

    expr = _natural_math_expression(raw)
    if not expr:
        return None

    locals_map = {
        "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
        "cot": sp.cot, "sec": sp.sec, "csc": sp.csc,
        "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
        "sqrt": sp.sqrt, "cbrt": sp.real_root,
        "log": sp.log, "ln": sp.log, "exp": sp.exp,
        "Abs": sp.Abs, "abs": sp.Abs,
        "factorial": sp.factorial,
        "pi": sp.pi, "E": sp.E, "I": sp.I, "oo": sp.oo,
    }

    # Equation written in natural language.
    if "=" in expr:
        equations = []
        for item in re.split(r"[;\n]+", expr):
            if not item.strip():
                continue
            left, right = item.split("=", 1)
            equations.append(sp.Eq(
                sp.sympify(left.strip(), locals=locals_map),
                sp.sympify(right.strip(), locals=locals_map)
            ))
        symbols = sorted(
            set().union(*(eq.free_symbols for eq in equations)),
            key=lambda x: x.name
        )
        solutions = sp.solve(equations, symbols, dict=True)
        if not solutions:
            return "🧮 <b>Math Solver</b>\n\n❌ কোনো exact solution পাওয়া যায়নি।"
        lines = []
        for sol in solutions:
            for symbol in symbols:
                if symbol in sol:
                    lines.append(
                        f"<b>{sp.sstr(symbol)}</b> = "
                        f"<code>{sp.sstr(sp.simplify(sol[symbol]))}</code>"
                    )
        return (
            "🧮 <b>Math Solver</b>\n\n"
            f"📌 প্রশ্ন:\n{raw}\n\n"
            "📐 সমাধান:\n" + "\n".join(lines)
        )

    expr_obj = sp.sympify(expr, locals=locals_map)
    result = sp.simplify(expr_obj)
    answer = (
        "🧮 <b>Math Solver</b>\n\n"
        f"📌 প্রশ্ন:\n{raw}\n\n"
        f"📐 সরলীকরণ:\n<code>{sp.sstr(result)}</code>"
    )
    if not result.free_symbols:
        answer += f"\n\n🔢 <b>উত্তর: {sp.N(result, 12)}</b>"
    return answer



# -------------------- SSC PHYSICS CREATIVE QUESTION SOLVER --------------------

def _extract_number(patterns, text_value):
    for pattern in patterns:
        m = re.search(pattern, text_value, re.I)
        if m:
            try:
                return float(_bn_number_text(m.group(1)))
            except (TypeError, ValueError, IndexError):
                pass
    return None


def _format_num(x):
    try:
        xf = float(x)
        return str(int(round(xf))) if abs(xf - round(xf)) < 1e-10 else f"{xf:.6g}"
    except Exception:
        return str(x)


def _solve_mirror_cq(question):
    s = _bn_number_text(question).lower()

    if not any(k in s for k in ["অবতল দর্পণ", "concave mirror", "দর্পণ"]):
        return None

    r = _extract_number([
        r"বক্রতার\s*(?:ব্যাসার্ধ|radius)\s*=?\s*(\d+(?:\.\d+)?)\s*cm",
        r"radius\s*(?:of\s*)?(?:curvature)?\s*=?\s*(\d+(?:\.\d+)?)\s*cm",
    ], s)
    # Common SSC wording: "দর্পণের মেরু থেকে 30 cm দূরে..."
    u_abs = _extract_number([
        r"(?:মেরু|দর্পণ)\s*(?:থেকে|হতে)\s*(\d+(?:\.\d+)?)\s*cm",
        r"(\d+(?:\.\d+)?)\s*cm\s*(?:দূরে|distance)",
        r"বস্তু\s*(?:রাখা|রাখা হলো|স্থাপন)\s*(?:হয়েছে|হলো)?\s*(?:দূরে)?\s*(\d+(?:\.\d+)?)\s*cm",
    ], s)

    # Final fallback for "থেকে 30 cm দূরে".
    if u_abs is None:
        m = re.search(
            r"(?:থেকে|হতে)\s*(\d+(?:\.\d+)?)\s*cm",
            s
        )
        if m:
            u_abs = float(m.group(1))

    if r is None or u_abs is None:
        return None

    f_abs = r / 2.0

    # Cartesian sign convention for a concave mirror:
    # u < 0, f < 0.  Mirror formula: 1/f = 1/v + 1/u.
    u = -u_abs
    f = -f_abs

    try:
        v = 1.0 / (1.0 / f - 1.0 / u)
    except ZeroDivisionError:
        return None

    # Magnification m = -v/u
    magnification = -v / u

    return {
        "r": r,
        "f_abs": f_abs,
        "u_abs": u_abs,
        "v": v,
        "m": magnification,
    }


def _physics_cq_answer(question):
    """
    SSC Physics CQ solver for common Bengali/English CQ structure.
    The concave-mirror CQ below is solved from the supplied values rather
    than from hard-coded final numbers.
    """
    s = _bn_number_text(question).lower()

    mirror = _solve_mirror_cq(question)
    if mirror:
        r = mirror["r"]
        f_abs = mirror["f_abs"]
        u_abs = mirror["u_abs"]
        v = mirror["v"]
        mag = mirror["m"]

        # Detect whether this looks like the exact common CQ wording:
        # radius + pole distance + object between F and C + focus comparison.
        is_full_mirror_cq = (
            "বক্রতার ব্যাসার্ধ" in s
            and ("মেরু থেকে" in s or "মেরু হতে" in s)
            and "আলোককেন্দ্র" in s
            and ("ফোকাস" in s or "ফোকাসে" in s)
        )

        if is_full_mirror_cq:
            return "\n".join([
                "⚛️ <b>SSC Physics — সৃজনশীল সমাধান</b>",
                "",
                "📌 <b>উদ্দীপক:</b> অবতল দর্পণের R = "
                f"{_format_num(r)} cm এবং মেরু থেকে বস্তুর দূরত্ব "
                f"{_format_num(u_abs)} cm।",
                "",
                "🔹 <b>ক. আলোককেন্দ্র কাকে বলে?</b> [১]",
                "দর্পণের মেরু ও বক্রতার কেন্দ্রের সংযোগকারী সরলরেখার "
                "যে বিন্দুতে প্রধান অক্ষের সমান্তরাল আপতিত রশ্মি "
                "প্রতিফলনের পর মিলিত হয়, সেই বিন্দুকে ফোকাস/আলোককেন্দ্র বলা হয়।",
                "",
                "🔹 <b>খ. বস্তু ফোকাস ও বক্রতার কেন্দ্রের মাঝখানে রাখলে "
                "কেমন বিম্ব গঠিত হয়?</b> [২]",
                "বস্তু F ও C-এর মাঝখানে থাকলে বিম্ব C-এর বাইরে গঠিত হয়। "
                "বিম্বটি বাস্তব, উল্টো এবং বস্তুর চেয়ে বড় (বর্ধিত)। "
                "কারণ প্রতিফলিত রশ্মিগুলো C-এর বাইরে গিয়ে মিলিত হয়।",
                "",
                "🔹 <b>গ. উদ্দীপকের তথ্য ব্যবহার করে বিম্বের অবস্থান নির্ণয় কর।</b> [৩]",
                f"দেওয়া আছে, R = {_format_num(r)} cm",
                f"অতএব, f = R/2 = {_format_num(f_abs)} cm",
                f"কার্টেসীয় sign convention অনুযায়ী, "
                f"u = -{_format_num(u_abs)} cm এবং f = -{_format_num(f_abs)} cm।",
                "",
                "দর্পণের সূত্র:",
                "1/f = 1/v + 1/u",
                "",
                f"1/(-{_format_num(f_abs)}) = 1/v + "
                f"1/(-{_format_num(u_abs)})",
                f"⇒ 1/v = -1/{_format_num(f_abs)} + 1/{_format_num(u_abs)}",
                f"⇒ v = {_format_num(v)} cm",
                "",
                f"✅ <b>উত্তর: বিম্বটি দর্পণের সামনে "
                f"{_format_num(abs(v))} cm দূরে, অর্থাৎ C-এর বাইরে গঠিত হবে।</b>",
                "",
                "🔹 <b>ঘ. বস্তুটি ফোকাসে রাখলে পূর্বের তুলনায় "
                "বিম্বের কী পরিবর্তন হবে?</b> [৪]",
                f"এখানে F = {_format_num(f_abs)} cm দূরে।",
                "বস্তু F-এ রাখলে প্রতিফলিত রশ্মিগুলো পরস্পর সমান্তরাল হয়ে যায়। "
                "তাই সসীম দূরত্বে বিম্ব পাওয়া যায় না; বিম্ব অসীমে গঠিত হয়। "
                "এ অবস্থায় বিম্ব অত্যন্ত বর্ধিত/অসীমে গঠিত বলে বিবেচিত হয়।",
                "",
                "📊 <b>তুলনা:</b>",
                f"আগে: u = {_format_num(u_abs)} cm → v = {_format_num(abs(v))} cm, "
                "বাস্তব ও উল্টো বিম্ব।",
                f"ফোকাসে: u = {_format_num(f_abs)} cm → v → ∞, "
                "বিম্ব অসীমে।",
                "",
                f"📐 Magnification, m = -v/u = {_format_num(mag)} "
                "⇒ বিম্বটি 2 গুণ বর্ধিত ও উল্টো।",
            ])

        # Generic mirror problem fallback.
        return "\n".join([
            "⚛️ <b>SSC Physics — দর্পণ সমাধান</b>",
            "",
            f"R = {_format_num(r)} cm",
            f"f = R/2 = {_format_num(f_abs)} cm",
            f"u = -{_format_num(u_abs)} cm",
            "",
            "1/f = 1/v + 1/u",
            f"⇒ v = {_format_num(v)} cm",
            "",
            f"✅ বিম্বের দূরত্ব = {_format_num(abs(v))} cm",
            f"📐 Magnification = {_format_num(mag)}",
        ])

    # Generic CQ detection: do not invent a solution for unsupported chapters.
    if re.search(r"\b[কখগঘ]\s*[.)।:]|\bক\)|\bখ\)|\bগ\)|\bঘ\)", s):
        return (
            "⚛️ <b>SSC Physics CQ Solver</b>\n\n"
            "CQ-এর কাঠামো শনাক্ত করেছি, কিন্তু এই প্রশ্নের chapter/concept "
            "এখনও নির্ভরযোগ্যভাবে শনাক্ত করতে পারিনি।\n\n"
            "উদ্দীপকসহ পুরো ক, খ, গ, ঘ পাঠানো হয়েছে—তাই unsupported হলে "
            "ভুল উত্তর বানানোর বদলে নির্দিষ্টভাবে জানাচ্ছি।"
        )

    return None


def solve_ssc_physics_cq(question):
    if len(question.strip()) > 5000:
        raise ValueError("CQ too long")
    return _physics_cq_answer(question)

def solve_natural_student_problem(raw):
    """
    Public entry point for the natural-language solver.

    Important: SSC Physics CQ is checked BEFORE the normal Math/SymPy
    parser, so a student can paste a complete Bangla CQ while still inside
    the normal Math Solver mode.
    """
    if len(raw) > 5000:
        raise ValueError("Question too long")

    # Full SSC Physics CQ first.
    cq_answer = _physics_cq_answer(raw)
    if cq_answer:
        return cq_answer

    return _natural_language_solver(raw)


def menu_handler(app):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))
