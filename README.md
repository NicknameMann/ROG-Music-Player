# 🎵 ROG Music Player

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![GUI](https://img.shields.io/badge/GUI-Tkinter-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Stable-success?style=for-the-badge)

**ROG Music Player** adalah aplikasi pemutar musik desktop berbasis Python yang ringan dan bertenaga. Aplikasi ini memungkinkan pengguna untuk mencari dan memutar lagu langsung dari **YouTube** (streaming audio) serta mengelola file musik lokal (offline) dengan antarmuka bertema *Dark Mode* ala ROG.

Aplikasi ini dibangun dengan fokus pada **efisiensi performa**, menggunakan teknik *Low-Frequency UI Update* untuk mencegah lag pada perangkat dengan spesifikasi rendah.

## ✨ Fitur Utama

* **🎧 Instant Streaming:** Memutar audio dari YouTube tanpa menunggu download selesai.
* **📂 Offline Library:** Mendukung pemutaran file MP3 lokal dari folder library.
* **⬇️ MP3 Downloader:** Fitur download lagu dari YouTube menjadi MP3 berkualitas tinggi (menggunakan FFmpeg).
* **⚡ Lightweight Engine:** Menggunakan VLC core tanpa beban UI yang berat (Anti-Lag).
* **🎛️ Manual Controls:**
    * Skip Mundur/Maju 10 detik.
    * Pengaturan Volume slider.
    * Fitur Loop (Pengulangan Lagu).
* **⏱️ Digital Timer:** Penunjuk waktu durasi lagu yang akurat.
* **📝 Auto Lyrics Info:** Menampilkan deskripsi/lirik dari metadata video YouTube secara otomatis.

## 🛠️ Teknologi yang Digunakan

Project ini dibuat menggunakan teknologi berikut:
* **Python 3.11+**: Bahasa pemrograman utama.
* **Tkinter**: Untuk antarmuka grafis (GUI) yang ringan dan native.
* **VLC Python Binding (`python-vlc`)**: Engine pemutar media yang stabil.
* **yt-dlp**: Library powerful untuk ekstraksi audio dari YouTube.
* **FFmpeg**: Backend untuk konversi audio.
* **Threading**: Manajemen proses agar UI tidak macet saat loading lagu.

## 📥 Cara Instalasi (Pengguna Biasa)

Anda tidak perlu menginstal Python. Cukup unduh installer yang sudah jadi:

1.  Buka menu **[Releases](../../releases)** di sebelah kanan halaman ini.
2.  Download file **`ROG_Music_Player_Setup_v1.exe`**.
3.  Jalankan file exe tersebut.
    * *Note:* Installer akan otomatis mendeteksi apakah Anda memiliki **VLC Media Player**. Jika belum, installer akan menawari untuk menginstalnya secara otomatis.
4.  Jalankan aplikasi dari Desktop!

## 💻 Cara Menjalankan dari Source Code (Developer)

Jika Anda ingin memodifikasi kode, ikuti langkah ini:

### 1. Clone Repository
```bash
git clone [https://github.com/NicknameMann/ROG-Music-Player.git](https://github.com/NicknameMann/ROG-Music-Player.git)
cd ROG-Music-Player