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
        self.root.title("Rafi's ROG Player (Ultimate Version)")
        self.root.geometry("1100x750")
        self.root.configure(bg="#121212")

        # --- SETUP PATH ---
        self.path_assets = resource_path("assets")
        self.path_library = os.path.join("playlists", "Default")
        self.path_ffmpeg = resource_path("ffmpeg.exe") 

        if not os.path.exists(self.path_library):
            os.makedirs(self.path_library)

        # --- SETUP VLC ---
        self.instance = vlc.Instance('--network-caching=1000')
        self.player = self.instance.media_player_new()
        
        # Event Manager untuk update slider
        self.event_manager = self.player.event_manager()
        
        # Variables
        self.current_song_url = ""
        self.search_results = []
        self.is_playing = False
        self.is_dragging = False # Agar slider tidak loncat saat ditarik user
        
        # --- UI COLORS ---
        self.col_bg = "#121212"
        self.col_sidebar = "#000000"
        self.col_player = "#181818"
        self.col_accent = "#FF0000"
        self.col_text = "#FFFFFF"
        self.col_text_sec = "#B3B3B3"

        self.setup_layout()
        self.show_search() 
        
        # Mulai Timer Loop untuk update durasi
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
        self.sidebar = tk.Frame(self.root, bg=self.col_sidebar, width=250)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="ROG MUSIC", fg=self.col_accent, bg=self.col_sidebar, 
                 font=("Calibri", 18, "bold")).pack(pady=20, padx=20, anchor="w")

        self.btn_nav("🔍  Search Music", self.show_search)
        self.btn_nav("📚  My Library", self.show_library)

        tk.Label(self.sidebar, text="NOW PLAYING INFO:", fg=self.col_text_sec, bg=self.col_sidebar, 
                 font=("Arial", 9, "bold")).pack(pady=(30, 5), padx=20, anchor="w")
        
        self.lyrics_box = tk.Text(self.sidebar, bg="#1a1a1a", fg="#cccccc", font=("Consolas", 8), 
                                  bd=0, height=20, padx=10, pady=10, wrap="word")
        self.lyrics_box.pack(fill="x", padx=10, pady=5)
        self.lyrics_box.insert(tk.END, "Info lagu akan muncul di sini.")
        self.lyrics_box.config(state="disabled")

        # 2. MAIN AREA
        self.main_area = tk.Frame(self.root, bg=self.col_bg)
        self.main_area.grid(row=0, column=1, sticky="nsew")

        # 3. PLAYER BAR (Bagian Bawah)
        self.player_bar = tk.Frame(self.root, bg=self.col_player, height=120, borderwidth=1, relief="ridge")
        self.player_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.player_bar.pack_propagate(False)

        self.setup_player_controls()

    def btn_nav(self, text, command):
        btn = tk.Button(self.sidebar, text=text, bg=self.col_sidebar, fg=self.col_text_sec, 
                        font=("Arial", 11, "bold"), bd=0, activebackground=self.col_sidebar, 
                        activeforeground="white", cursor="hand2", command=command, anchor="w", padx=20)
        btn.pack(fill="x", pady=5)

    def setup_player_controls(self):
        # --- BARIS 1: SEEKBAR (Slider Durasi) ---
        seek_frame = tk.Frame(self.player_bar, bg=self.col_player)
        seek_frame.pack(fill="x", padx=20, pady=(10, 0))

        # Label Waktu Berjalan (00:00)
        self.lbl_current_time = tk.Label(seek_frame, text="00:00", bg=self.col_player, fg="white", font=("Arial", 9))
        self.lbl_current_time.pack(side="left")

        # Slider Durasi
        self.seek_var = tk.DoubleVar()
        self.seek_slider = ttk.Scale(seek_frame, from_=0, to=100, orient="horizontal", variable=self.seek_var, command=self.on_seek)
        self.seek_slider.pack(side="left", fill="x", expand=True, padx=10)
        
        # Event Binding untuk mencegah konflik saat user menarik slider
        self.seek_slider.bind("<ButtonPress-1>", self.start_drag)
        self.seek_slider.bind("<ButtonRelease-1>", self.stop_drag)

        # Label Total Durasi (04:30)
        self.lbl_total_time = tk.Label(seek_frame, text="00:00", bg=self.col_player, fg="white", font=("Arial", 9))
        self.lbl_total_time.pack(side="right")

        # --- BARIS 2: TOMBOL KONTROL & VOLUME ---
        ctrl_frame = tk.Frame(self.player_bar, bg=self.col_player)
        ctrl_frame.pack(fill="x", padx=20, pady=5)

        # Judul Lagu (Kiri)
        self.lbl_track = tk.Label(ctrl_frame, text="Ready to Play", bg=self.col_player, fg="white", font=("Arial", 11, "bold"), width=30, anchor="w")
        self.lbl_track.pack(side="left")

        # Tombol Tengah (Play/Pause)
        center_box = tk.Frame(ctrl_frame, bg=self.col_player)
        center_box.pack(side="left", expand=True)

        self.icon_play = self.load_img("play.png", (35, 35))
        self.icon_pause = self.load_img("pause.png", (35, 35))
        self.icon_stop = self.load_img("stop.png", (25, 25))

        tk.Button(center_box, image=self.icon_stop, command=self.stop_music, bg=self.col_player, bd=0).pack(side="left", padx=15)
        self.btn_play = tk.Button(center_box, image=self.icon_play, command=self.play_pause_music, bg=self.col_player, bd=0)
        self.btn_play.pack(side="left", padx=15)

        # Kanan: Volume & Download
        right_box = tk.Frame(ctrl_frame, bg=self.col_player)
        right_box.pack(side="right")

        tk.Label(right_box, text="Vol", bg=self.col_player, fg="gray").pack(side="left", padx=(0,5))
        
        # Volume Slider
        self.vol_slider = ttk.Scale(right_box, from_=0, to=100, orient="horizontal", command=self.set_volume)
        self.vol_slider.set(80) # Default volume 80%
        self.vol_slider.pack(side="left", padx=5)

        self.btn_dl = tk.Button(right_box, text="⬇ MP3", command=self.start_download, 
                                bg=self.col_player, fg=self.col_text_sec, font=("Arial", 8, "bold"), bd=0, state="disabled")
        self.btn_dl.pack(side="left", padx=15)

    # --- UI PAGES ---
    def clear_main_area(self):
        for widget in self.main_area.winfo_children():
            widget.destroy()

    def show_search(self):
        self.clear_main_area()
        tk.Label(self.main_area, text="Cari Lagu (YouTube)", bg=self.col_bg, fg="white", font=("Arial", 20, "bold")).pack(padx=30, pady=(30, 10), anchor="w")

        search_frame = tk.Frame(self.main_area, bg="#2a2a2a", padx=10, pady=5)
        search_frame.pack(fill="x", padx=30)
        
        self.entry_search = tk.Entry(search_frame, bg="#2a2a2a", fg="white", font=("Arial", 14), bd=0, insertbackground="red")
        self.entry_search.pack(side="left", fill="x", expand=True)
        self.entry_search.bind("<Return>", lambda e: self.search_online())

        tk.Button(search_frame, text="🔍 SEARCH", command=self.search_online, bg="#2a2a2a", fg="white", bd=0, font=("Arial", 12, "bold")).pack(side="right")
        self.lbl_status = tk.Label(self.main_area, text="", bg=self.col_bg, fg=self.col_text_sec)
        self.lbl_status.pack(pady=10)

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
        tk.Label(self.main_area, text="Library Offline", bg=self.col_bg, fg="white", font=("Arial", 20, "bold")).pack(padx=30, pady=(30, 10), anchor="w")
        
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
                if f.endswith(".mp3"):
                    self.lib_list.insert(tk.END, f"  🎵  {f}")

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
        except Exception as e:
            print(f"Error Search: {e}")

    def update_search_ui_list(self):
        self.lbl_status.config(text=f"Ditemukan {len(self.search_results)} lagu.", fg="#00FF00")
        for item in self.search_results:
            self.search_list.insert(tk.END, f" ▶  {item.get('title')} [{item.get('duration_string')}]")

    def play_from_search_result(self, event):
        try:
            if not self.search_list.curselection(): return 
            index = self.search_list.curselection()[0]
            selected_data = self.search_results[index]
            
            self.lbl_status.config(text=f"Sedang memuat: {selected_data.get('title')}...", fg="yellow")
            self.update_lyrics_box("Mengambil data lagu & deskripsi...")
            threading.Thread(target=self.worker_resolve_and_play, args=(selected_data['url'],), daemon=True).start()
        except: pass

    def worker_resolve_and_play(self, video_url):
        ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'ignoreerrors': True, 'force_ipv4': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                if not info: return

                self.current_song_url = info.get('webpage_url', video_url)
                self.root.after(0, lambda: self.play_stream(info['url'], info['title']))
                
                desc = info.get('description', 'Tidak ada deskripsi.')
                self.root.after(0, lambda: self.update_lyrics_box(f"JUDUL: {info['title']}\n\nLIRIK/DESKRIPSI:\n{desc}"))
        except Exception as e:
            print(f"Error Worker: {e}")

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
            self.lbl_track.config(text=f"{title[:35]}...")
            self.btn_play.config(image=self.icon_pause)
            self.btn_dl.config(state="normal", bg=self.col_accent)
            self.lbl_status.config(text=f"Sedang memutar: {title}", fg="#00FF00")
        except: pass

    def play_from_library(self, event):
        try:
            if not self.lib_list.curselection(): return
            selection = self.lib_list.get(self.lib_list.curselection())
            filename = selection.replace("  🎵  ", "")
            path = os.path.join(self.path_library, filename)
            
            media = self.instance.media_new(path)
            self.player.set_media(media)
            self.player.play()
            
            self.is_playing = True
            self.lbl_track.config(text=filename)
            self.btn_play.config(image=self.icon_pause)
            self.update_lyrics_box(f"Memutar: {filename}\n(Offline Mode)")
        except: pass

    # --- KONTROL MUSIK BARU (VOLUME & SEEK) ---
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
        self.seek_slider.set(0)
        self.lbl_current_time.config(text="00:00")

    def set_volume(self, val):
        """Mengatur Volume VLC (0-100)"""
        volume = int(float(val))
        self.player.audio_set_volume(volume)

    # --- LOGIKA SEEKBAR (WAKTU BERJALAN) ---
    def update_timer(self):
        """Fungsi Loop untuk update slider setiap detik"""
        if self.is_playing and not self.is_dragging:
            # Ambil durasi total dan waktu sekarang (ms)
            length = self.player.get_length()
            current = self.player.get_time()
            
            if length > 0:
                # Update Slider
                self.seek_slider.config(to=length/1000) # Convert ms to seconds
                self.seek_slider.set(current/1000)
                
                # Update Label Waktu (00:00 / 05:30)
                cur_str = time.strftime('%M:%S', time.gmtime(current/1000))
                tot_str = time.strftime('%M:%S', time.gmtime(length/1000))
                self.lbl_current_time.config(text=cur_str)
                self.lbl_total_time.config(text=tot_str)

        # Ulangi fungsi ini setiap 1 detik (1000 ms)
        self.root.after(1000, self.update_timer)

    def start_drag(self, event):
        self.is_dragging = True # Stop auto-update saat user menggeser

    def stop_drag(self, event):
        self.is_dragging = False # Lanjut auto-update

    def on_seek(self, val):
        """Dipanggil saat slider digeser user"""
        if self.player:
            # Set waktu VLC (convert seconds ke ms)
            seek_time = int(float(val) * 1000)
            self.player.set_time(seek_time)

    def start_download(self):
        if not self.current_song_url: return
        self.btn_dl.config(text="DOWNLOADING...", state="disabled", bg="#333")
        threading.Thread(target=self.worker_download, daemon=True).start()

    def worker_download(self):
        ydl_opts = {
            'format': 'bestaudio/best',
            'ffmpeg_location': self.path_ffmpeg,
            'outtmpl': os.path.join(self.path_library, '%(title)s.%(ext)s'),
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
            'quiet': True, 'ignoreerrors': True, 'force_ipv4': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.current_song_url])
            self.root.after(0, lambda: messagebox.showinfo("Sukses", "Lagu berhasil didownload!"))
            self.root.after(0, lambda: self.btn_dl.config(text="⬇ MP3", state="normal", bg=self.col_accent))
        except:
            self.root.after(0, lambda: messagebox.showerror("Error", "Gagal Download."))

if __name__ == "__main__":
    root = tk.Tk()
    if os.path.exists("assets/icon_rog.ico"):
        root.iconbitmap("assets/icon_rog.ico")
    app = SpotifyCloneROG(root)
    root.mainloop()