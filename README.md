# CUY DOWNLOADER

Website sederhana untuk mendownload video dari YouTube, TikTok, Instagram, dan ratusan situs lain (lewat [yt-dlp](https://github.com/yt-dlp/yt-dlp)), dengan pilihan resolusi 144p / 240p / 480p / 720p / 1080p.

## Struktur Proyek

```
cuy-downloader/
├── backend/
│   ├── app.py            # Server Flask + logika yt-dlp
│   └── requirements.txt  # Dependensi Python
├── frontend/
│   ├── index.html        # UI dengan tab per platform
│   ├── style.css
│   └── script.js
└── README.md
```

## Cara Menjalankan

Proyek ini **butuh akses internet** saat dijalankan (untuk mengambil video dari YouTube/TikTok/dll), jadi jalankan di komputer/server yang punya koneksi internet normal — bukan di sandbox tanpa internet.

1. Pastikan **Python 3.9+** dan **ffmpeg** sudah terpasang di server/komputer kamu.
   - ffmpeg dibutuhkan untuk menggabungkan stream video+audio pada resolusi tinggi.
   - Cek dengan: `ffmpeg -version`

2. Masuk ke folder backend dan install dependensi:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Jalankan server:
   ```bash
   python app.py
   ```

4. Buka browser ke `http://localhost:5000` — frontend dan backend disajikan dari server yang sama.

## Cara Kerja

1. User menempel link video di kolom sesuai platform (tab YouTube / TikTok / Instagram / Lainnya).
2. Tombol **"Cek Video"** memanggil endpoint `POST /api/info`, yang memakai `yt-dlp` untuk membaca metadata video (judul, thumbnail, durasi) dan daftar resolusi yang ditawarkan.
3. User memilih resolusi (144–1080p). Tombol resolusi mengarahkan browser ke `GET /api/download?url=...&height=...`.
4. Backend menjalankan `yt-dlp` untuk mengunduh video pada resolusi target (menggabungkan stream video+audio terbaik yang ≤ resolusi pilihan), lalu mengirim file tersebut sebagai download ke browser, dan menghapus file sementara setelah terkirim.

Catatan: karena satu backend memakai `yt-dlp`, kode tidak perlu dibedakan per platform — extractor dipilih otomatis berdasarkan domain di URL. Tab di frontend hanya untuk kenyamanan tampilan/UX.

## Deployment Produksi

Proyek ini sudah dilengkapi `Dockerfile` (sudah termasuk ffmpeg + gunicorn), jadi cara paling gampang & konsisten adalah deploy sebagai container Docker, di VPS mana pun atau di platform PaaS yang mendukung Dockerfile.

### Opsi A — VPS (DigitalOcean/Contabo/dll) + Docker

```bash
# di server, setelah clone/upload folder proyek ini
docker build -t cuy-downloader .
docker run -d --name cuy-downloader -p 80:8080 --restart unless-stopped cuy-downloader
```
Lalu arahkan domain kamu (A record) ke IP server tersebut.

Untuk HTTPS gratis otomatis, paling simpel pakai **Caddy** sebagai reverse proxy (cukup 1 baris Caddyfile: `domainmu.com { reverse_proxy localhost:8080 }`), atau Nginx + Certbot kalau sudah familiar dengan itu.

### Opsi B — PaaS yang mendukung Dockerfile (Railway, Render, Fly.io)

1. Push proyek ini ke repo GitHub.
2. Di Railway/Render/Fly.io, buat "New Project" → hubungkan repo tersebut → platform akan otomatis mendeteksi `Dockerfile` dan build sendiri.
3. Set environment variable `PORT` kalau platform mengharuskan port tertentu (kode sudah membaca `PORT` dari environment).
4. Setelah build sukses, platform akan memberi URL publik (dan biasanya HTTPS otomatis) — tinggal hubungkan domain custom kalau mau.

### Opsi C — Tanpa Docker (manual di VPS)

```bash
sudo apt install ffmpeg python3-pip -y
cd backend && pip install -r requirements.txt
gunicorn -w 4 --timeout 120 -b 0.0.0.0:8000 app:app
```
Jalankan sebagai service (`systemd`) agar otomatis restart, lalu pasang Nginx/Caddy di depannya untuk HTTPS + domain.

### Hal lain yang perlu diperhatikan di produksi

- Pertimbangkan rate limiting (misalnya dengan `flask-limiter`) agar server tidak kebanjiran request download dari satu orang/bot.
- Update `yt-dlp` secara rutin (`pip install -U yt-dlp`, atau rebuild image Docker secara berkala) karena platform seperti YouTube/Instagram kadang mengubah struktur situsnya, yang bisa membuat versi lama yt-dlp berhenti berfungsi.
- Monitor disk server: file hasil download memang dihapus otomatis setelah terkirim, tapi kalau ada request yang gagal di tengah jalan, sesekali cek folder temp tidak menumpuk.
- Video berdurasi panjang/resolusi tinggi bisa memakan waktu & bandwidth besar — pertimbangkan batas durasi/ukuran kalau trafiknya ramai.

## Peringatan Hukum & Etika

- Gunakan situs ini hanya untuk mengunduh konten yang kamu miliki sendiri, berlisensi terbuka, atau memang diizinkan pemiliknya untuk diunduh.
- Mengunduh dan mendistribusikan ulang video berhak cipta tanpa izin dapat melanggar Ketentuan Layanan platform terkait maupun undang-undang hak cipta di negaramu.
- Pertimbangkan menambahkan halaman kebijakan penggunaan (Terms of Use) di website agar tanggung jawab penggunaan jelas ada di tangan pengguna.
