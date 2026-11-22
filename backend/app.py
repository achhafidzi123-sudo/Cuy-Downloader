"""
CUY DOWNLOADER - backend server
---------------------------------
Flask API yang membungkus yt-dlp untuk mengambil info video dan
mendownload-nya pada resolusi tertentu (144/240/480/720/1080).

Mendukung semua situs yang didukung yt-dlp (YouTube, TikTok, Instagram,
Facebook, Twitter/X, dll) karena extractor-nya otomatis dipilih
berdasarkan URL yang dikirim - tidak perlu kode berbeda per platform.

Jalankan:
    pip install -r requirements.txt
    python app.py
"""

import os
import re
import uuid
import tempfile
from flask import Flask, request, jsonify, send_file, after_this_request, abort
from flask_cors import CORS
import yt_dlp

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)

# Resolusi yang ditawarkan ke user
TARGET_HEIGHTS = [144, 240, 480, 720, 1080]

# Folder sementara untuk file hasil download (dibersihkan otomatis per-request)
DOWNLOAD_DIR = tempfile.mkdtemp(prefix="cuydl_")


def is_safe_url(url: str) -> bool:
    """Validasi sederhana: hanya terima URL http/https."""
    return bool(re.match(r"^https?://", (url or "").strip(), re.IGNORECASE))


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/info", methods=["POST"])
def info():
    """
    Terima { "url": "<link video>" } dan kembalikan judul, thumbnail,
    durasi, serta daftar resolusi yang tersedia/ditawarkan.
    """
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not url or not is_safe_url(url):
        return jsonify({"error": "Link tidak valid. Pastikan link dimulai dengan http:// atau https://"}), 400

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "socket_timeout": 20,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(url, download=False)
    except Exception as exc:  # yt-dlp melempar banyak jenis exception tergantung situs
        return jsonify({"error": f"Gagal mengambil info video: {exc}"}), 400

    formats = meta.get("formats") or []

    # Cek resolusi mana yang benar-benar tersedia dari daftar format asli video
    available_heights = {
        f.get("height")
        for f in formats
        if f.get("height") and f.get("vcodec") not in (None, "none")
    }

    resolutions = []
    for h in TARGET_HEIGHTS:
        resolutions.append({
            "height": h,
            "label": f"{h}p",
            # Jika tidak ada format dengan tinggi persis h (umum di TikTok/IG
            # yang cuma punya 1-2 kualitas), tetap ditawarkan - saat
            # download, yt-dlp otomatis ambil kualitas terdekat <= h.
            "exact_match": h in available_heights,
        })

    return jsonify({
        "title": meta.get("title") or "Video",
        "thumbnail": meta.get("thumbnail"),
        "duration": meta.get("duration"),
        "uploader": meta.get("uploader") or meta.get("channel"),
        "extractor": meta.get("extractor_key"),
        "resolutions": resolutions,
    })


@app.route("/api/download", methods=["GET"])
def download():
    """
    Download video pada resolusi tertentu dan stream filenya ke browser.
    Query params: ?url=...&height=720
    """
    url = (request.args.get("url") or "").strip()
    height = (request.args.get("height") or "").strip()

    if not url or not is_safe_url(url):
        abort(400, "Link tidak valid.")
    if height not in [str(h) for h in TARGET_HEIGHTS]:
        abort(400, "Resolusi tidak valid.")

    job_id = uuid.uuid4().hex
    outtmpl = os.path.join(DOWNLOAD_DIR, f"{job_id}.%(ext)s")

    # Ambil video terbaik <= resolusi pilihan, gabung dengan audio terbaik.
    # Fallback ke "best" kalau situs sumber tidak expose stream terpisah
    # (umum terjadi di TikTok/Instagram).
    format_selector = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": format_selector,
        "outtmpl": outtmpl,
        "merge_output_format": "mp4",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as exc:
        abort(500, f"Gagal mengunduh video: {exc}")

    produced_path = None
    for fname in os.listdir(DOWNLOAD_DIR):
        if fname.startswith(job_id):
            produced_path = os.path.join(DOWNLOAD_DIR, fname)
            break

    if not produced_path or not os.path.exists(produced_path):
        abort(500, "File hasil unduhan tidak ditemukan.")

    @after_this_request
    def cleanup(response):
        try:
            os.remove(produced_path)
        except OSError:
            pass
        return response

    ext = os.path.splitext(produced_path)[1] or ".mp4"
    download_name = f"cuydownloader_{height}p{ext}"
    return send_file(produced_path, as_attachment=True, download_name=download_name)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
