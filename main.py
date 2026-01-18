import sys
import os
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import yt_dlp
import vlc
import threading
import time

# --- FUNGSI RESOURCE PATH ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SpotifyCloneROG:
    def __init__(self, root):
        self.root = root
        self.root.title("Rafi's ROG Player")
        self.root.geometry("1100x750")
        self.root.configure(bg="#121212")

        self.path_assets = resource_path("assets")
        self.path_library = os.path.join("playlists", "Default")
        self.path_ffmpeg = resource_path("ffmpeg.exe") 

        if not os.path.exists(self.path_library):
            os.makedirs(self.path_library)

        # --- VLC STANDARD (RINGAN) ---
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        
        self.current_song_url = ""
        self.search_results = []
        self.is_playing = False
        self.is_looping = False
        
        self.col_bg = "#121212"
        self.col_sidebar = "#000000"
        self.col_player = "#181818"
        self.col_accent = "#FF0000"
        self.col_text = "#FFFFFF"
        self.col_text_sec = "#B3B3B3"

        self.setup_layout()
        self.show_home()
        
        # Timer Loop (Ringan)
        self.update_timer()

    def load_img(self, name, size=(24, 24)):
        try:
            path = os.path.join(self.path_assets, name)
            if os.path.exists(path):
                img = Image.open(path).resize(size, Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
        except: pass
        return None

    def setup_layout(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # 1. SIDEBAR
        self.sidebar = tk.Frame(self.root, bg=self.col_sidebar, width=280)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="ROG MUSIC", fg=self.col_accent, bg=self.col_sidebar, 
                 font=("Calibri", 18, "bold")).pack(pady=20, padx=20, anchor="w")

        self.btn_nav("🏠  Home", self.show_home)
        self.btn_nav("🔍  Cari Lagu", self.show_search)
        self.btn_nav("📚  Library Offline", self.show_library)

        # Lirik Box
        tk.Label(self.sidebar, text="INFO / LYRICS:", fg="gray", bg=self.col_sidebar, 
                 font=("Arial", 9, "bold")).pack(pady=(30, 5), padx=20, anchor="w")
        self.lyrics_box = tk.Text(self.sidebar, bg="#111", fg="#ddd", font=("Consolas", 9), 
                                  bd=0, height=25, padx=10, pady=10, wrap="word")
        self.lyrics_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.lyrics_box.insert(tk.END, "Siap memutar musik.")
        self.lyrics_box.config(state="disabled")

        # 2. MAIN AREA
        self.main_area = tk.Frame(self.root, bg=self.col_bg)
        self.main_area.grid(row=0, column=1, sticky="nsew")

        # 3. PLAYER BAR
        self.player_bar = tk.Frame(self.root, bg=self.col_player, height=100, borderwidth=1, relief="ridge")
        self.player_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.player_bar.pack_propagate(False)

        self.setup_player_controls()

    def btn_nav(self, text, command):
        btn = tk.Button(self.sidebar, text=text, bg=self.col_sidebar, fg=self.col_text_sec, 
                        font=("Arial", 11, "bold"), bd=0, activebackground=self.col_sidebar, 
                        activeforeground="white", cursor="hand2", command=command, anchor="w", padx=20)
        btn.pack(fill="x", pady=5)

    def setup_player_controls(self):
        # Kiri: Info Lagu + TIMER
        left_box = tk.Frame(self.player_bar, bg=self.col_player)
        left_box.pack(side="left", padx=20)

        self.lbl_track = tk.Label(left_box, text="Ready", bg=self.col_player, fg="white", font=("Arial", 11, "bold"))
        self.lbl_track.pack(anchor="w")

        # --- INI DIA TIMERNYA ---
        self.lbl_timer = tk.Label(left_box, text="--:-- / --:--", bg=self.col_player, fg=self.col_accent, font=("Consolas", 10))
        self.lbl_timer.pack(anchor="w")
        
        # Tengah: Tombol Kontrol Manual
        ctrl_frame = tk.Frame(self.player_bar, bg=self.col_player)
        ctrl_frame.pack(side="left", expand=True, fill="x")

        center_box = tk.Frame(ctrl_frame, bg=self.col_player)
        center_box.pack(anchor="center")

        self.icon_play = self.load_img("play.png", (35, 35))
        self.icon_pause = self.load_img("pause.png", (35, 35))
        self.icon_stop = self.load_img("stop.png", (25, 25))

        # Loop
        self.btn_loop = tk.Button(center_box, text="🔁", command=self.toggle_loop, bg=self.col_player, fg="gray", bd=0, font=("Arial", 12))
        self.btn_loop.pack(side="left", padx=10)

        # Mundur 10s
        tk.Button(center_box, text="⏪ 10s", command=lambda: self.skip_time(-10), bg=self.col_player, fg="white", bd=0, font=("Arial", 10, "bold")).pack(side="left", padx=5)

        # Stop
        tk.Button(center_box, image=self.icon_stop, command=self.stop_music, bg=self.col_player, bd=0).pack(side="left", padx=10)
        
        # Play/Pause
        self.btn_play = tk.Button(center_box, image=self.icon_play, command=self.play_pause_music, bg=self.col_player, bd=0)
        self.btn_play.pack(side="left", padx=10)

        # Maju 10s
        tk.Button(center_box, text="10s ⏩", command=lambda: self.skip_time(10), bg=self.col_player, fg="white", bd=0, font=("Arial", 10, "bold")).pack(side="left", padx=5)

        # Kanan: Volume & DL
        right_box = tk.Frame(self.player_bar, bg=self.col_player)
        right_box.pack(side="right", padx=20)

        tk.Label(right_box, text="Vol", bg=self.col_player, fg="gray").pack(side="left", padx=(0,5))
        self.vol_slider = ttk.Scale(right_box, from_=0, to=100, orient="horizontal", command=self.set_volume)
        self.vol_slider.set(80) 
        self.vol_slider.pack(side="left", padx=5)

        self.btn_dl = tk.Button(right_box, text="⬇ MP3", command=self.start_download, 
                                bg=self.col_player, fg=self.col_text_sec, font=("Arial", 8, "bold"), bd=0, state="disabled")
        self.btn_dl.pack(side="left", padx=15)

    # --- TIMER SYSTEM (RINGAN) ---
    def update_timer(self):
        # 1. Cek jika lagu selesai (untuk fitur Loop)
        if self.is_playing and self.is_looping:
             if self.player.get_state() == vlc.State.Ended:
                self.player.stop()
                self.player.play()

        # 2. Update Teks Waktu (Hanya Teks, Tidak Berat)
        if self.is_playing:
            try:
                curr = self.player.get_time()
                total = self.player.get_length()
                
                if curr > 0:
                    def fmt(ms):
                        s = int(ms / 1000)
                        m, s = divmod(s, 60)
                        return f"{m:02d}:{s:02d}"
                    
                    self.lbl_timer.config(text=f"{fmt(curr)} / {fmt(total)}")
            except: pass
        
        # Update setiap 1 detik (1000ms)
        self.root.after(1000, self.update_timer)

    # --- UI PAGES ---
    def clear_main_area(self):
        for widget in self.main_area.winfo_children(): widget.destroy()

    def show_home(self):
        self.clear_main_area()
        tk.Label(self.main_area, text="Selamat Datang di ROG Music Player", bg=self.col_bg, fg="white", font=("Arial", 32, "bold")).pack(padx=40, pady=40, anchor="w")
        tk.Label(self.main_area, text="Selamat nikmati lagu favorit kamu", bg=self.col_bg, fg=self.col_accent, font=("Arial", 16)).pack(padx=40, anchor="w")
        tk.Label(self.main_area, text="Fitur:", bg=self.col_bg, fg="white", font=("Arial", 12, "bold")).pack(anchor="w", padx=40, pady=(20, 5))
        tk.Label(self.main_area, text="- Timer Digital (00:00 / 03:00)", bg=self.col_bg, fg=self.col_text_sec).pack(anchor="w", padx=40)
        tk.Label(self.main_area, text="- Tombol ⏪ ⏩ untuk skip manual (Anti-Lag).", bg=self.col_bg, fg=self.col_text_sec).pack(anchor="w", padx=40)

    def show_search(self):
        self.clear_main_area()
        tk.Label(self.main_area, text="Cari Lagu (YouTube)", bg=self.col_bg, fg="white", font=("Arial", 20, "bold")).pack(padx=30, pady=(20, 10), anchor="w")

        search_frame = tk.Frame(self.main_area, bg="#2a2a2a", padx=10, pady=5)
        search_frame.pack(fill="x", padx=30)
        self.entry_search = tk.Entry(search_frame, bg="#2a2a2a", fg="white", font=("Arial", 14), bd=0, insertbackground="red")
        self.entry_search.pack(side="left", fill="x", expand=True)
        self.entry_search.bind("<Return>", lambda e: self.search_online())
        tk.Button(search_frame, text="🔍", command=self.search_online, bg="#2a2a2a", fg="white", bd=0, font=("Arial", 12)).pack(side="right")
        
        self.lbl_status = tk.Label(self.main_area, text="", bg=self.col_bg, fg=self.col_text_sec)
        self.lbl_status.pack(pady=5)

        list_frame = tk.Frame(self.main_area, bg=self.col_bg)
        list_frame.pack(fill="both", expand=True, padx=30, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        self.search_list = tk.Listbox(list_frame, bg=self.col_bg, fg="white", font=("Arial", 11),
                                      selectbackground="#FF0000", selectforeground="white", bd=0, 
                                      highlightthickness=0, yscrollcommand=scrollbar.set)
        self.search_list.pack(fill="both", expand=True)
        scrollbar.config(command=self.search_list.yview)
        self.search_list.bind("<Double-Button-1>", self.play_from_search_result)

    def show_library(self):
        self.clear_main_area()
        tk.Label(self.main_area, text="Library Offline", bg=self.col_bg, fg="white", font=("Arial", 20, "bold")).pack(padx=30, pady=(20, 10), anchor="w")
        list_frame = tk.Frame(self.main_area, bg=self.col_bg)
        list_frame.pack(fill="both", expand=True, padx=30, pady=10)
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        self.lib_list = tk.Listbox(list_frame, bg=self.col_bg, fg=self.col_text_sec, font=("Arial", 11),
                                   selectbackground="#2a2a2a", selectforeground="white", bd=0, 
                                   highlightthickness=0, yscrollcommand=scrollbar.set)
        self.lib_list.pack(fill="both", expand=True)
        scrollbar.config(command=self.lib_list.yview)
        self.lib_list.bind("<Double-Button-1>", self.play_from_library)
        self.load_offline_files()

    # --- LOGIC UTAMA ---
    def load_offline_files(self):
        self.lib_list.delete(0, tk.END)
        if os.path.exists(self.path_library):
            for f in os.listdir(self.path_library):
                if f.endswith(".mp3"): self.lib_list.insert(tk.END, f"  🎵  {f}")

    def search_online(self):
        query = self.entry_search.get()
        if not query: return
        self.lbl_status.config(text="Sedang mencari...", fg=self.col_accent)
        self.search_list.delete(0, tk.END)
        threading.Thread(target=self.worker_search_list, args=(query,), daemon=True).start()

    def worker_search_list(self, query):
        ydl_opts = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True, 'extract_flat': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(f"ytsearch10:{query}", download=False)
                if 'entries' in result:
                    self.search_results = result['entries']
                    self.root.after(0, self.update_search_ui_list)
        except: self.root.after(0, lambda: self.lbl_status.config(text="Gagal mencari.", fg="red"))

    def update_search_ui_list(self):
        self.lbl_status.config(text=f"Ditemukan {len(self.search_results)} lagu.", fg="#00FF00")
        for item in self.search_results:
            self.search_list.insert(tk.END, f" ▶  {item.get('title')}")

    def play_from_search_result(self, event):
        try:
            if not self.search_list.curselection(): return 
            index = self.search_list.curselection()[0]
            selected_data = self.search_results[index]
            self.player.stop()
            self.lbl_status.config(text="Menyiapkan audio...", fg="yellow")
            threading.Thread(target=self.worker_resolve_and_play, args=(selected_data['url'],), daemon=True).start()
        except: pass

    def worker_resolve_and_play(self, video_url):
        ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'force_ipv4': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                self.current_song_url = info.get('webpage_url', video_url)
                self.root.after(0, lambda: self.play_stream(info['url'], info['title']))
                desc = info.get('description', 'Tidak ada deskripsi.')
                self.root.after(0, lambda: self.update_lyrics_box(f"JUDUL: {info['title']}\n\nINFO:\n{desc}"))
        except Exception as e: print(e)

    def update_lyrics_box(self, text):
        self.lyrics_box.config(state="normal")
        self.lyrics_box.delete("1.0", tk.END)
        self.lyrics_box.insert(tk.END, text)
        self.lyrics_box.config(state="disabled")

    def play_stream(self, stream_url, title):
        try:
            media = self.instance.media_new(stream_url)
            self.player.set_media(media)
            self.player.play()
            self.is_playing = True
            self.lbl_track.config(text=f"{title[:40]}...")
            self.btn_play.config(image=self.icon_pause)
            self.btn_dl.config(state="normal", bg=self.col_accent)
            self.lbl_status.config(text=f"Playing: {title}", fg="#00FF00")
        except: pass

    def play_from_library(self, event):
        try:
            if not self.lib_list.curselection(): return
            selection = self.lib_list.get(self.lib_list.curselection())
            filename = selection.replace("  🎵  ", "")
            path = os.path.join(self.path_library, filename)
            self.player.stop()
            media = self.instance.media_new(path)
            self.player.set_media(media)
            self.player.play()
            self.is_playing = True
            self.lbl_track.config(text=filename)
            self.btn_play.config(image=self.icon_pause)
            self.update_lyrics_box(f"File Offline: {filename}")
        except: pass

    # --- KONTROL FITUR ---
    def toggle_loop(self):
        self.is_looping = not self.is_looping
        if self.is_looping: self.btn_loop.config(fg="#00FF00")
        else: self.btn_loop.config(fg="gray")

    def play_pause_music(self):
        if self.is_playing:
            self.player.pause()
            self.btn_play.config(image=self.icon_play)
            self.is_playing = False
        else:
            self.player.play()
            self.btn_play.config(image=self.icon_pause)
            self.is_playing = True

    def stop_music(self):
        self.player.stop()
        self.btn_play.config(image=self.icon_play)
        self.is_playing = False
        self.lbl_track.config(text="Stopped")
        self.lbl_timer.config(text="--:-- / --:--")

    def set_volume(self, val):
        self.player.audio_set_volume(int(float(val)))

    # FUNGSI SKIP MANUAL (RINGAN)
    def skip_time(self, seconds):
        if self.player.is_playing():
            current = self.player.get_time() 
            new_time = current + (seconds * 1000)
            if new_time < 0: new_time = 0
            self.player.set_time(new_time)

    def start_download(self):
        if not self.current_song_url: return
        self.btn_dl.config(text="DOWNLOADING...", state="disabled", bg="#333")
        threading.Thread(target=self.worker_download, daemon=True).start()

    def worker_download(self):
        ydl_opts = {'format': 'bestaudio/best', 'ffmpeg_location': self.path_ffmpeg, 'outtmpl': os.path.join(self.path_library, '%(title)s.%(ext)s'), 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}], 'quiet': True, 'force_ipv4': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.current_song_url])
            self.root.after(0, lambda: messagebox.showinfo("Sukses", "Lagu berhasil didownload!"))
            self.root.after(0, lambda: self.btn_dl.config(text="⬇ DOWNLOAD", state="normal", bg=self.col_accent))
        except:
            self.root.after(0, lambda: messagebox.showerror("Error", "Gagal Download."))

if __name__ == "__main__":
    root = tk.Tk()
    if os.path.exists("assets/icon_rog.ico"):
        root.iconbitmap("assets/icon_rog.ico")
    app = SpotifyCloneROG(root)
    root.mainloop()