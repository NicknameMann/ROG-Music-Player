import sys
import os
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from PIL import Image, ImageTk
import yt_dlp
import vlc
import threading
import time
import json
import random # Penting untuk membuat nama file unik (Anti-Error 416)

# --- FUNGSI RESOURCE PATH (Agar aset terbaca saat jadi EXE) ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- FUNGSI PATH DATA USER (Menyimpan playlist & cache di AppData) ---
def get_data_path(filename):
    app_data = os.getenv('APPDATA') 
    data_dir = os.path.join(app_data, "ROGMusicPlayer")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return os.path.join(data_dir, filename)

class SpotifyCloneROG:
    def __init__(self, root):
        self.root = root
        self.root.title("Rafi's ROG Player v1.3.1")
        self.root.geometry("1100x750")
        self.root.configure(bg="#121212")

        # --- PATHS (Lokasi File) ---
        self.path_assets = resource_path("assets")
        self.path_ffmpeg = resource_path("ffmpeg.exe") 
        
        # [PENTING] Tambahkan ffmpeg ke sistem PATH agar yt-dlp lancar
        project_dir = os.path.dirname(os.path.abspath(__file__))
        os.environ["PATH"] += os.pathsep + project_dir

        self.path_playlist_json = get_data_path("user_playlists.json")
        self.path_settings_json = get_data_path("settings.json")
        self.path_cache = get_data_path("cache")
        
        # Buat folder cache jika belum ada
        if not os.path.exists(self.path_cache): os.makedirs(self.path_cache)

        # --- LOAD SETTINGS (Pengaturan User) ---
        self.settings = self.load_settings()
        self.current_lang = self.settings.get("language", "en") 
        self.path_library = self.settings.get("download_path", os.path.join(os.path.expanduser("~/Music"), "ROG_Library"))
        if not os.path.exists(self.path_library): os.makedirs(self.path_library)

        # --- DATABASE & VLC PLAYER ---
        self.playlists = self.load_playlists()
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        
        # --- VARIABLES (Status Aplikasi) ---
        self.current_song_data = {} 
        self.search_results = [] 
        self.is_playing = False
        self.is_looping = False
        self.context_song_data = None 
        self.lbl_status = None 
        self.page_history = [] 
        self.current_page_func = None
        self.active_list = []      
        self.active_index = -1     
        self.active_source = None  

        # --- COLORS (Tema ROG) ---
        self.col_bg = "#121212"
        self.col_sidebar = "#000000"
        self.col_player = "#181818"
        self.col_accent = "#FF0000" # Merah ROG
        self.col_text = "#FFFFFF"
        self.col_text_sec = "#B3B3B3"

        # --- KAMUS BAHASA ---
        self.LANG = {
            "en": {
                "welcome": "Welcome to ROG Music", "nav_home": "🏠  Home", "nav_search": "🔍  Search Song",
                "nav_lib": "📂  My Playlists", "nav_set": "⚙️  Settings", "back": "⬅ BACK",
                "lyrics": "INFO / LYRICS:", "ready": "Ready", "stopped": "Stopped",
                "home_title": "ROG Music Player (v1.3.1)", "search_title": "Search Song (YouTube)",
                "lib_title": "Playlists & Files", "set_title": "Settings", "searching": "Searching...",
                "found": "Found {} songs.", "loading": "🚀 Buffering...", "downloading": "DOWNLOADING...",
                "dl_success": "Success", "dl_msg": "Song downloaded to:", "save_title": "Save Song",
                "save_btn": "SAVE", "new_pl": "Or New Playlist:", "choose_pl": "Choose Playlist:",
                "pl_success": "Saved to {}", "folder_title": "📂 Download Folder:", "change_btn": "Change Folder",
                "vol_title": "🔊 Default Volume:", "vol_desc": "Automatically saved.", "lang_title": "🌐 Language:",
                "lang_desc": "Select language.", "source_file": "📂 Source:", "menu_play": "▶ Play Now",
                "menu_save": "➕ Save to Playlist", "menu_dl": "⬇ Download MP3", "search_lib_hint": "🔍 Filter...",
                "tut_autoplay": "Auto-Play Active", "tut_settings": "Settings", "tut_space": "Space: Play/Pause",
                "tut_right": "Right: Skip 10s", "tut_left": "Left: Rewind 10s", "tut_rclick": "Right Click Menu",
                "tut_3dots": "Options", "tut_dl": "Download MP3", "err_stream": "❌ Buffer Error (Skip)"
            },
            "id": {
                "welcome": "Selamat Datang di ROG Musik", "nav_home": "🏠  Beranda", "nav_search": "🔍  Cari Lagu",
                "nav_lib": "📂  Koleksi Saya", "nav_set": "⚙️  Pengaturan", "back": "⬅ KEMBALI",
                "lyrics": "INFO / LIRIK:", "ready": "Siap", "stopped": "Berhenti",
                "home_title": "ROG Music Player (v1.3.1)", "search_title": "Cari Lagu (YouTube)",
                "lib_title": "Playlist & File Offline", "set_title": "Pengaturan", "searching": "Sedang mencari...",
                "found": "Ditemukan {} lagu.", "loading": "🚀 Menyiapkan...", "downloading": "MENGUNDUH...",
                "dl_success": "Berhasil", "dl_msg": "Lagu berhasil diunduh ke:", "save_title": "Simpan Lagu",
                "save_btn": "SIMPAN", "new_pl": "Atau Playlist Baru:", "choose_pl": "Pilih Playlist:",
                "pl_success": "Disimpan ke {}", "folder_title": "📂 Folder Unduhan:", "change_btn": "Ubah Folder",
                "vol_title": "🔊 Volume Awal:", "vol_desc": "Otomatis tersimpan saat slider digeser.",
                "lang_title": "🌐 Bahasa / Language:",
                "lang_desc": "Pilih bahasa aplikasi.",
                "source_file": "📂 Sumber Folder:",
                "menu_play": "▶ Putar Sekarang",
                "menu_save": "➕ Simpan ke Playlist",
                "menu_dl": "⬇ Download MP3",
                "search_lib_hint": "🔍 Cari...",
                "tut_autoplay": "Search: Auto Acak. Playlist: Auto Lanjut.",
                "tut_settings": "Atur lokasi simpan & bahasa.",
                "tut_space": "Spasi: Putar/Jeda",
                "tut_right": "Kanan: Maju 10dtk", "tut_left": "Kiri: Mundur 10dtk", "tut_rclick": "Klik Kanan: Menu",
                "tut_3dots": "Opsi", "tut_dl": "Download MP3", "err_stream": "❌ Gagal Buffer (Lewati)"
            }
        }

        # --- UI INITIALIZATION ---
        self.setup_layout()
        self.current_page_func = self.show_home
        self.show_home()
        self.update_timer() 
        
        # Set Volume Awal
        start_vol = self.settings.get("default_volume", 80)
        self.player.audio_set_volume(start_vol)
        self.vol_slider.set(start_vol)

        # [SHORTCUT KEYBOARD]
        self.root.bind("<space>", self.on_key_space)
        self.root.bind("<Right>", self.on_key_right)
        self.root.bind("<Left>", self.on_key_left)
        self.root.focus_set()

    # --- FUNGSI SHORTCUT ---
    def on_key_space(self, event):
        if isinstance(event.widget, tk.Entry): return
        self.play_pause_music()

    def on_key_right(self, event):
        if isinstance(event.widget, tk.Entry): return
        self.skip_time(10)

    def on_key_left(self, event):
        if isinstance(event.widget, tk.Entry): return
        self.skip_time(-10)

    # --- HELPER LAINNYA ---
    def tr(self, key):
        return self.LANG[self.current_lang].get(key, key)

    def set_language(self, lang_code):
        self.current_lang = lang_code
        self.settings["language"] = lang_code
        self.save_settings()
        self.sidebar.destroy()
        self.setup_sidebar()
        if self.current_page_func: self.current_page_func()

    def navigate_to(self, target_func):
        if self.current_page_func == target_func: return
        if self.current_page_func: self.page_history.append(self.current_page_func)
        self.current_page_func = target_func
        target_func()
        if self.page_history: self.btn_back_ui.config(state="normal", fg="white")
        else: self.btn_back_ui.config(state="disabled", fg="#333")
        self.root.focus_set()

    def go_back(self):
        if not self.page_history: return
        prev_page = self.page_history.pop()
        self.current_page_func = prev_page
        prev_page()
        if not self.page_history: self.btn_back_ui.config(state="disabled", fg="#333")
        self.root.focus_set()

    # --- LOGIKA PLAYER: FINISH & ERROR ---
    def handle_song_finish(self):
        if self.is_looping:
            self.player.stop(); self.player.play()
            return
        if not self.active_list: return 
        next_index = self.active_index + 1

        if self.active_source == "search":
            if next_index < len(self.active_list): self.play_specific_index(next_index)
            else: self.play_specific_index(random.randint(0, len(self.active_list) - 1))
        elif self.active_source == "playlist":
            if next_index < len(self.active_list):
                item = self.active_list[next_index]
                if isinstance(item, str): self.play_offline_file(item, auto_next=True)
                else: self.play_cloud_song(item['title'], auto_next=True)
            else: self.stop_music()

    def handle_play_error(self):
        print("Play Error. Skipping...")
        if self.lbl_status and self.lbl_status.winfo_exists():
            self.lbl_status.config(text=self.tr("err_stream"), fg="red")
        self.root.after(2000, self.handle_song_finish)

    # --- PENGATURAN (JSON) ---
    def load_settings(self):
        default = {"download_path": os.path.join(os.path.expanduser("~/Music"), "ROG_Library"), "default_volume": 80, "language": "en"}
        if os.path.exists(self.path_settings_json):
            try:
                with open(self.path_settings_json, 'r') as f: default.update(json.load(f))
            except: pass
        return default

    def save_settings(self):
        with open(self.path_settings_json, 'w') as f: json.dump(self.settings, f)

    def change_download_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.settings["download_path"] = folder
            self.path_library = folder
            self.save_settings()
            self.show_settings()
            messagebox.showinfo(self.tr("dl_success"), f"Folder: {folder}")

    def load_playlists(self):
        if os.path.exists(self.path_playlist_json):
            try:
                with open(self.path_playlist_json, 'r') as f: return json.load(f)
            except: pass
        return {"Favorites": []}

    def save_playlists(self):
        with open(self.path_playlist_json, 'w') as f: json.dump(self.playlists, f)

    # --- TAMPILAN UTAMA (LAYOUT) ---
    def setup_layout(self):
        self.root.columnconfigure(1, weight=1); self.root.rowconfigure(0, weight=1)
        self.setup_sidebar()
        self.main_area = tk.Frame(self.root, bg=self.col_bg); self.main_area.grid(row=0, column=1, sticky="nsew")
        self.player_bar = tk.Frame(self.root, bg=self.col_player, height=100, borderwidth=1, relief="ridge")
        self.player_bar.grid(row=1, column=0, columnspan=2, sticky="ew"); self.player_bar.pack_propagate(False)
        self.setup_player_controls()
        
        # --- MENU KONTEKS (Klik Kanan & Titik 3) ---
        self.context_menu = tk.Menu(self.root, tearoff=0, bg="#333", fg="white", font=("Arial", 10))
        
    def setup_sidebar(self):
        self.sidebar = tk.Frame(self.root, bg=self.col_sidebar, width=280)
        self.sidebar.grid(row=0, column=0, sticky="ns"); self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text="ROG MUSIC", fg=self.col_accent, bg=self.col_sidebar, font=("Calibri", 18, "bold")).pack(pady=(20, 10), padx=20, anchor="w")
        self.btn_back_ui = tk.Button(self.sidebar, text=self.tr("back"), bg="#222", fg="#333", font=("Arial", 10, "bold"), bd=0, cursor="hand2", state="disabled", command=self.go_back)
        self.btn_back_ui.pack(fill="x", padx=20, pady=(0, 20))
        if self.page_history: self.btn_back_ui.config(state="normal", fg="white")
        self.btn_nav(self.tr("nav_home"), lambda: self.navigate_to(self.show_home))
        self.btn_nav(self.tr("nav_search"), lambda: self.navigate_to(self.show_search))
        self.btn_nav(self.tr("nav_lib"), lambda: self.navigate_to(self.show_library))
        self.btn_nav(self.tr("nav_set"), lambda: self.navigate_to(self.show_settings))
        tk.Label(self.sidebar, text=self.tr("lyrics"), fg="gray", bg=self.col_sidebar, font=("Arial", 9, "bold")).pack(pady=(30, 5), padx=20, anchor="w")
        self.lyrics_box = tk.Text(self.sidebar, bg="#111", fg="#ddd", font=("Consolas", 9), bd=0, height=25, padx=10, pady=10, wrap="word"); self.lyrics_box.pack(fill="both", expand=True, padx=10, pady=(0, 10)); self.lyrics_box.config(state="disabled")

    def btn_nav(self, text, command):
        tk.Button(self.sidebar, text=text, bg=self.col_sidebar, fg=self.col_text_sec, font=("Arial", 11, "bold"), bd=0, activebackground=self.col_sidebar, activeforeground="white", cursor="hand2", command=command, anchor="w", padx=20).pack(fill="x", pady=5)

    def setup_player_controls(self):
        left = tk.Frame(self.player_bar, bg=self.col_player); left.pack(side="left", padx=20)
        self.lbl_track = tk.Label(left, text=self.tr("ready"), bg=self.col_player, fg="white", font=("Arial", 11, "bold")); self.lbl_track.pack(anchor="w")
        self.lbl_timer = tk.Label(left, text="--:-- / --:--", bg=self.col_player, fg=self.col_accent, font=("Consolas", 10)); self.lbl_timer.pack(anchor="w")
        center = tk.Frame(self.player_bar, bg=self.col_player); center.pack(side="left", expand=True)
        self.icon_play = self.load_img("play.png", (35, 35)); self.icon_pause = self.load_img("pause.png", (35, 35))
        
        # Tombol Save di player bar
        tk.Button(center, text="💾", command=lambda: self.open_save_dialog(None), bg=self.col_player, fg="white", bd=0, font=("Arial", 14)).pack(side="left", padx=15)
        
        self.btn_loop = tk.Button(center, text="🔁", command=self.toggle_loop, bg=self.col_player, fg="gray", bd=0, font=("Arial", 12)); self.btn_loop.pack(side="left", padx=10)
        tk.Button(center, text="⏪", command=lambda: self.skip_time(-10), bg=self.col_player, fg="white", bd=0, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        self.btn_play = tk.Button(center, image=self.icon_play, command=self.play_pause_music, bg=self.col_player, bd=0); self.btn_play.pack(side="left", padx=10)
        tk.Button(center, text="⏩", command=lambda: self.skip_time(10), bg=self.col_player, fg="white", bd=0, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        right = tk.Frame(self.player_bar, bg=self.col_player); right.pack(side="right", padx=20)
        tk.Label(right, text="Vol", bg=self.col_player, fg="gray").pack(side="left")
        self.vol_slider = ttk.Scale(right, from_=0, to=100, orient="horizontal", command=self.set_volume); self.vol_slider.set(80); self.vol_slider.pack(side="left", padx=5)
        self.btn_dl = tk.Button(right, text="⬇ MP3", command=self.start_download, bg=self.col_player, fg=self.col_text_sec, font=("Arial", 8, "bold"), bd=0, state="disabled"); self.btn_dl.pack(side="left", padx=15)

    def clear_main_area(self):
        for w in self.main_area.winfo_children(): w.destroy()

    def load_img(self, name, size=(24, 24)):
        try:
            path = os.path.join(self.path_assets, name)
            if os.path.exists(path): return ImageTk.PhotoImage(Image.open(path).resize(size, Image.Resampling.LANCZOS))
        except: pass
        return None

    # --- HALAMAN: HOME ---
    def show_home(self):
        self.clear_main_area()
        tk.Label(self.main_area, text=self.tr("welcome"), bg=self.col_bg, fg="white", font=("Arial", 32, "bold")).pack(padx=40, pady=(40, 10), anchor="w")
        tk.Label(self.main_area, text=self.tr("home_title"), bg=self.col_bg, fg=self.col_accent, font=("Arial", 16, "bold")).pack(padx=40, anchor="w")
        info_frame = tk.Frame(self.main_area, bg=self.col_bg); info_frame.pack(padx=40, pady=20, anchor="w")
        features = [("⬅ KEMBALI", self.tr("back")),("🧠 AUTO-PLAY", self.tr("tut_autoplay")),("⚙️ SETTINGS", self.tr("tut_settings")),("⌨️ SPASI", self.tr("tut_space")),("⌨️ ARAH KANAN", self.tr("tut_right")),("🖱️ KLIK KANAN", self.tr("tut_rclick")),("⬇️ DOWNLOAD", self.tr("tut_dl"))]
        for icon, desc in features:
            row = tk.Frame(info_frame, bg=self.col_bg); row.pack(fill="x", pady=8)
            tk.Label(row, text=icon, bg=self.col_bg, fg="white", font=("Arial", 12, "bold"), width=15, anchor="w").pack(side="left")
            tk.Label(row, text=desc, bg=self.col_bg, fg=self.col_text_sec, font=("Arial", 12)).pack(side="left")
        self.root.focus_set()

    # --- HALAMAN: SETTINGS ---
    def show_settings(self):
        self.clear_main_area()
        tk.Label(self.main_area, text=self.tr("set_title"), bg=self.col_bg, fg="white", font=("Arial", 32, "bold")).pack(padx=40, pady=40, anchor="w")
        f = tk.Frame(self.main_area, bg=self.col_bg); f.pack(padx=40, anchor="w", fill="x")
        tk.Label(f, text=self.tr("lang_title"), bg=self.col_bg, fg=self.col_accent, font=("Arial", 14, "bold")).pack(anchor="w")
        tk.Label(f, text=self.tr("lang_desc"), bg=self.col_bg, fg="gray").pack(anchor="w", pady=(0, 5))
        lang_box = tk.Frame(f, bg=self.col_bg); lang_box.pack(anchor="w", pady=(0, 20))
        tk.Button(lang_box, text="🇬🇧 English", command=lambda: self.set_language("en"), bg="#333" if self.current_lang == "en" else "#222", fg=self.col_accent if self.current_lang == "en" else "white", font=("Arial", 11, "bold"), bd=0, padx=15, pady=5).pack(side="left", padx=(0, 10))
        tk.Button(lang_box, text="🇮🇩 Indonesia", command=lambda: self.set_language("id"), bg="#333" if self.current_lang == "id" else "#222", fg=self.col_accent if self.current_lang == "id" else "white", font=("Arial", 11, "bold"), bd=0, padx=15, pady=5).pack(side="left")
        tk.Label(f, text=self.tr("folder_title"), bg=self.col_bg, fg=self.col_accent, font=("Arial", 14, "bold")).pack(anchor="w")
        pb = tk.Frame(f, bg="#222", padx=10, pady=10); pb.pack(fill="x", pady=(5, 20))
        tk.Label(pb, text=self.path_library, bg="#222", fg="white").pack(side="left")
        tk.Button(pb, text=self.tr("change_btn"), command=self.change_download_folder, bg=self.col_accent, fg="white", bd=0).pack(side="right")
        tk.Label(f, text=self.tr("vol_title"), bg=self.col_bg, fg=self.col_accent, font=("Arial", 14, "bold")).pack(anchor="w")
        tk.Label(f, text=self.tr("vol_desc"), bg=self.col_bg, fg="gray").pack(anchor="w")
        self.root.focus_set()

    # --- HALAMAN: SEARCH ---
    def show_search(self):
        self.clear_main_area()
        self.lbl_status = tk.Label(self.main_area, text="", bg=self.col_bg, fg=self.col_text_sec)
        tk.Label(self.main_area, text=self.tr("search_title"), bg=self.col_bg, fg="white", font=("Arial", 20, "bold")).pack(padx=30, pady=(20, 10), anchor="w")
        sf = tk.Frame(self.main_area, bg="#2a2a2a", padx=10, pady=5); sf.pack(fill="x", padx=30)
        self.entry_search = tk.Entry(sf, bg="#2a2a2a", fg="white", font=("Arial", 14), bd=0, insertbackground="red"); self.entry_search.pack(side="left", fill="x", expand=True)
        self.entry_search.bind("<Return>", lambda e: self.search_online())
        tk.Button(sf, text="🔍", command=self.search_online, bg="#2a2a2a", fg="white", bd=0, font=("Arial", 12)).pack(side="right")
        self.lbl_status.pack(pady=5)
        c = tk.Frame(self.main_area, bg=self.col_bg); c.pack(fill="both", expand=True, padx=30, pady=5)
        self.cv = tk.Canvas(c, bg=self.col_bg, bd=0, highlightthickness=0)
        sb = tk.Scrollbar(c, command=self.cv.yview); self.sf = tk.Frame(self.cv, bg=self.col_bg)
        self.sf.bind("<Configure>", lambda e: self.cv.configure(scrollregion=self.cv.bbox("all")))
        self.cv.create_window((0,0), window=self.sf, anchor="nw"); self.cv.configure(yscrollcommand=sb.set)
        self.cv.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
        
        # Reset Menu agar bersih
        self.context_menu.delete(0, tk.END)
        self.context_menu.add_command(label=self.tr("menu_play"), command=self.play_context_song)
        self.context_menu.add_command(label=self.tr("menu_save"), command=self.save_context_song)
        self.context_menu.add_command(label=self.tr("menu_dl"), command=self.download_context_song)
        
        if self.search_results: self.update_search_ui()

    # --- HALAMAN: LIBRARY ---
    def show_library(self):
        self.clear_main_area()
        self.current_view_playlist = None 
        tk.Label(self.main_area, text=self.tr("lib_title"), bg=self.col_bg, fg="white", font=("Arial", 20, "bold")).pack(padx=30, pady=(20, 10), anchor="w")
        tk.Label(self.main_area, text=f"{self.tr('source_file')} {self.path_library}", bg=self.col_bg, fg="gray").pack(padx=30, anchor="w", pady=(0, 5))
        search_frame = tk.Frame(self.main_area, bg=self.col_bg, padx=30, pady=5); search_frame.pack(fill="x")
        self.entry_lib_search = tk.Entry(search_frame, bg="#2a2a2a", fg="white", font=("Arial", 12), bd=0); self.entry_lib_search.pack(fill="x", ipady=3)
        self.entry_lib_search.insert(0, self.tr("search_lib_hint")); self.entry_lib_search.bind("<FocusIn>", lambda e: self.entry_lib_search.delete(0, tk.END) if "..." in self.entry_lib_search.get() else None); self.entry_lib_search.bind("<KeyRelease>", self.filter_library)
        lf = tk.Frame(self.main_area, bg=self.col_bg); lf.pack(fill="both", expand=True, padx=30, pady=10)
        sb = tk.Scrollbar(lf); sb.pack(side="right", fill="y")
        self.lib_list = tk.Listbox(lf, bg=self.col_bg, fg=self.col_text_sec, font=("Arial", 11), selectbackground="#2a2a2a", selectforeground="white", bd=0, highlightthickness=0, yscrollcommand=sb.set)
        self.lib_list.pack(fill="both", expand=True); sb.config(command=self.lib_list.yview)
        self.lib_list.bind("<Double-Button-1>", self.on_library_click); self.lib_list.bind("<Button-3>", self.on_library_rclick)
        self.load_root_library()
        self.root.focus_set()

    def filter_library(self, event):
        query = self.entry_lib_search.get().lower(); 
        if "..." in query: return
        if self.current_view_playlist is None: self.load_root_library(search_query=query)
        else: self.load_playlist_content(self.current_view_playlist, search_query=query)

    def on_library_rclick(self, event):
        try:
            index = self.lib_list.nearest(event.y); self.lib_list.selection_clear(0, tk.END); self.lib_list.selection_set(index); self.lib_list.activate(index)
            selection = self.lib_list.get(index)
            if "☁️" in selection:
                title = selection.replace("☁️ ", "")
                songs = self.playlists.get(self.current_view_playlist, [])
                song_data = next((s for s in songs if s['title'] == title), None)
                if song_data: 
                    self.context_song_data = song_data
                    self.context_menu.post(event.x_root, event.y_root)
        except: pass

    # --- LOGIKA SEARCH ENGINE ---
    def search_online(self):
        q = self.entry_search.get()
        if not q: return
        if self.lbl_status and self.lbl_status.winfo_exists(): self.lbl_status.config(text=self.tr("searching"), fg=self.col_accent)
        for w in self.sf.winfo_children(): w.destroy()
        threading.Thread(target=self.worker_search, args=(q,), daemon=True).start()

    def worker_search(self, q):
        # [ANTI-ERROR] Konfigurasi Search
        ydl_opts = {
            'format': 'bestaudio/best', 'quiet': True, 'force_ipv4': True, 'extract_flat': True, 
            'no_warnings': True, 'ignoreerrors': True, 'nocheckcertificate': True,
            'source_address': '0.0.0.0' # Fix IP
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                r = ydl.extract_info(f"ytsearch15:{q}", download=False)
                if 'entries' in r: self.search_results = r['entries']; self.root.after(0, self.update_search_ui)
                else: 
                    if self.lbl_status and self.lbl_status.winfo_exists(): self.root.after(0, lambda: self.lbl_status.config(text="No results.", fg="red"))
        except Exception as e: 
             print(f"Search Error: {e}")
             if self.lbl_status and self.lbl_status.winfo_exists(): self.root.after(0, lambda: self.lbl_status.config(text="Network Error", fg="red"))

    def update_search_ui(self):
        if self.lbl_status and self.lbl_status.winfo_exists(): self.lbl_status.config(text=self.tr("found").format(len(self.search_results)), fg="#00FF00")
        for w in self.sf.winfo_children(): w.destroy()
        for i, item in enumerate(self.search_results):
            r = tk.Frame(self.sf, bg=self.col_bg, pady=5); r.pack(fill="x")
            l = tk.Label(r, text=f"▶ {item.get('title')}", bg=self.col_bg, fg="white", font=("Arial", 11), cursor="hand2", anchor="w")
            l.pack(side="left", fill="x", expand=True, padx=5)
            l.bind("<Button-1>", lambda e, x=i: self.play_specific_index(x))
            l.bind("<Button-3>", lambda e, d=item: self.open_context_menu(e, d))
            l.bind("<Enter>", lambda e, w=l: w.config(fg=self.col_accent)); l.bind("<Leave>", lambda e, w=l: w.config(fg="white"))
            
            # TOMBOL TITIK 3
            btn_opt = tk.Button(r, text="⋮", bg="#333", fg="white", bd=0, font=("Arial", 10, "bold"))
            btn_opt.pack(side="right", padx=5)
            btn_opt.bind("<Button-1>", lambda e, d=item: self.open_context_menu(e, d))
            
            tk.Frame(self.sf, bg="#333", height=1).pack(fill="x")

    def play_specific_index(self, index):
        self.active_list = self.search_results; self.active_index = index; self.active_source = "search"; data = self.search_results[index]
        self.start_play_process(data)

    def play_cloud_song(self, title, auto_next=False):
        if not self.current_view_playlist and not auto_next: return
        if not auto_next: self.active_list = self.playlists[self.current_view_playlist]; self.active_source = "playlist"
        for i, s in enumerate(self.active_list):
            if s['title'] == title: self.active_index = i; self.lbl_track.config(text=f"{self.tr('loading')} {title[:20]}..."); self.start_play_process(s); break

    def play_offline_file(self, filename, auto_next=False):
        if not auto_next:
            self.active_source = "playlist"
            if os.path.exists(self.path_library):
                self.active_list = [f for f in os.listdir(self.path_library) if f.endswith(".mp3")]
                try: self.active_index = self.active_list.index(filename)
                except: self.active_index = 0
            else: self.active_list = []
        path = os.path.join(self.path_library, filename); self.play_local_file(path, filename)

    def start_play_process(self, data):
        self.player.stop()
        self.lbl_track.config(text=f"{self.tr('loading')}...")
        if self.lbl_status and self.lbl_status.winfo_exists(): self.lbl_status.config(text=self.tr("loading"), fg="yellow")
        self.current_song_data = {"title": data['title'], "url": data['url']}
        self.root.focus_set()
        threading.Thread(target=self.worker_buffer_and_play, args=(data['url'], data['title']), daemon=True).start()

    # --- [PENTING] LOGIKA BUFFERING FIX (ANTI 416) ---
    def worker_buffer_and_play(self, url, title):
        # 1. Buat nama file acak agar tidak bentrok dengan file rusak (cache)
        unique_id = random.randint(10000, 99999)
        temp_filename = f"temp_play_{unique_id}.mp3"
        temp_path = os.path.join(self.path_cache, temp_filename)

        # 2. Bersihkan file temp lama yang menumpuk di folder cache agar hemat storage
        try:
            for f in os.listdir(self.path_cache):
                if f.startswith("temp_play_") and f.endswith(".mp3"):
                    try: os.remove(os.path.join(self.path_cache, f))
                    except: pass
        except: pass

        # 3. Konfigurasi DOWNLOAD BARU (Memaksa download fresh)
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.path_cache, f'temp_play_{unique_id}.%(ext)s'),
            'ffmpeg_location': self.path_ffmpeg,
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}],
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            
            # --- FIX UTAMA ERROR 416 ---
            'source_address': '0.0.0.0',   # Paksa IPv4
            'no_continue': True,           # Jangan Resume, selalu download baru
            'force_generic_extractor': False,
            'http_chunk_size': 10485760    # Stabilizer
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if os.path.exists(temp_path):
                self.root.after(0, lambda: self.play_local_file(temp_path, title))
                self.root.after(0, lambda: self.update_lyrics_box(f"JUDUL: {title}\n\n[Playing Stream]"))
            else:
                self.root.after(0, self.handle_play_error)

        except Exception as e:
            print(f"Buffer Error: {e}")
            self.root.after(0, self.handle_play_error)

    def play_local_file(self, path, title):
        self.player.stop()
        media = self.instance.media_new(path)
        self.player.set_media(media)
        self.player.play()
        self.is_playing = True
        self.lbl_track.config(text=f"{title[:40]}...")
        self.btn_play.config(image=self.icon_pause)
        self.btn_dl.config(state="normal", bg=self.col_accent)
        if self.lbl_status and self.lbl_status.winfo_exists(): self.lbl_status.config(text=f"Playing: {title}", fg="#00FF00")
        self.root.focus_set() 

    def open_save_dialog_direct(self, d): self.open_save_dialog({"title": d['title'], "url": d['url']})
    
    # --- LOGIKA MENU KONTEKS ---
    def open_context_menu(self, e, d): 
        self.context_song_data={"title":d['title'],"url":d['url']}
        self.context_menu.post(e.x_root, e.y_root)

    def play_context_song(self): 
        if self.context_song_data: self.start_play_process(self.context_song_data)
    def save_context_song(self):
        if self.context_song_data: self.open_save_dialog(self.context_song_data)
    def download_context_song(self):
        if self.context_song_data: 
            self.current_song_data = self.context_song_data
            self.start_download()

    def open_save_dialog(self, target=None):
        song = target if target else self.current_song_data
        if not song or not song.get('url'): return
        d = tk.Toplevel(self.root); d.title(self.tr("save_title")); d.geometry("400x450"); d.configure(bg="#222")
        tk.Label(d, text=f"{self.tr('save_title')}: {song['title'][:30]}...", fg="white", bg="#222").pack(pady=10)
        tk.Label(d, text=self.tr("choose_pl"), fg=self.col_accent, bg="#222", font=("Arial", 12, "bold")).pack(pady=5)
        lb = tk.Listbox(d, bg="#333", fg="white"); lb.pack(fill="both", expand=True, padx=20)
        for p in self.playlists: lb.insert(tk.END, f"📂 {p}")
        tk.Label(d, text=self.tr("new_pl"), fg="gray", bg="#222").pack(pady=(15, 5))
        en = tk.Entry(d); en.pack(fill="x", padx=20, pady=5)
        def save():
            pl = en.get().strip()
            if not pl and lb.curselection(): pl = lb.get(lb.curselection()[0]).replace("📂 ", "")
            if pl:
                if pl not in self.playlists: self.playlists[pl] = []
                if not any(s['url'] == song['url'] for s in self.playlists[pl]):
                    self.playlists[pl].append(song); self.save_playlists()
                    messagebox.showinfo("Sukses", self.tr("pl_success").format(pl))
                d.destroy()
        tk.Button(d, text=self.tr("save_btn"), command=save, bg=self.col_accent, fg="white").pack(fill="x", padx=20, pady=20)

    def load_root_library(self, search_query=""):
        self.lib_list.delete(0, tk.END); self.current_view_playlist = None
        self.lib_list.insert(tk.END, "--- PLAYLISTS ---"); self.lib_list.itemconfig(tk.END, {'fg': self.col_accent})
        for p in self.playlists.keys():
            if search_query == "" or search_query in p.lower(): self.lib_list.insert(tk.END, f"📂 {p}")
        self.lib_list.insert(tk.END, ""); self.lib_list.insert(tk.END, "--- OFFLINE FILES ---"); self.lib_list.itemconfig(tk.END, {'fg': '#00FF00'})
        if os.path.exists(self.path_library):
            for f in os.listdir(self.path_library): 
                if f.endswith(".mp3"):
                    if search_query == "" or search_query in f.lower(): self.lib_list.insert(tk.END, f"🎵 {f}")
        else: self.lib_list.insert(tk.END, "(Folder not found)")

    def load_playlist_content(self, pl, search_query=""):
        self.lib_list.delete(0, tk.END); self.current_view_playlist = pl
        self.lib_list.insert(tk.END, f"🔙 ... {self.tr('back')}"); self.lib_list.itemconfig(tk.END, {'fg': 'yellow'})
        for s in self.playlists.get(pl, []): 
            if search_query == "" or search_query in s['title'].lower(): self.lib_list.insert(tk.END, f"☁️ {s['title']}")

    def on_library_click(self, e):
        if not self.lib_list.curselection(): return
        s = self.lib_list.get(self.lib_list.curselection())
        if "🔙" in s: self.entry_lib_search.delete(0, tk.END); self.load_root_library()
        elif "📂" in s: self.entry_lib_search.delete(0, tk.END); self.load_playlist_content(s.replace("📂 ", ""))
        elif "🎵" in s: self.play_offline_file(s.replace("🎵 ", ""))
        elif "☁️" in s: self.play_cloud_song(s.replace("☁️ ", ""))

    def update_lyrics_box(self, t):
        self.lyrics_box.config(state="normal"); self.lyrics_box.delete("1.0", tk.END); self.lyrics_box.insert(tk.END, t); self.lyrics_box.config(state="disabled")

    def toggle_loop(self):
        self.is_looping = not self.is_looping; self.btn_loop.config(fg="#00FF00" if self.is_looping else "gray")

    def stop_music(self):
        self.player.stop(); self.is_playing = False; self.lbl_track.config(text=self.tr("stopped"))

    def play_pause_music(self):
        if self.is_playing: self.player.pause(); self.btn_play.config(image=self.icon_play); self.is_playing = False
        else: self.player.play(); self.btn_play.config(image=self.icon_pause); self.is_playing = True

    def skip_time(self, s):
        if self.player.is_playing(): self.player.set_time(max(0, self.player.get_time() + (s*1000)))

    def set_volume(self, v): 
        val = int(float(v)); self.player.audio_set_volume(val); self.settings["default_volume"] = val

    def update_timer(self):
        if self.is_playing and self.player.get_state() == vlc.State.Ended: self.handle_song_finish() 
        if self.is_playing:
            try:
                curr = self.player.get_time(); tot = self.player.get_length()
                if curr > 0: fmt = lambda ms: f"{int(ms/1000)//60:02d}:{int(ms/1000)%60:02d}"; self.lbl_timer.config(text=f"{fmt(curr)} / {fmt(tot)}")
            except: pass
        self.root.after(1000, self.update_timer)

    def start_download(self):
        if self.current_song_data.get('url'): 
            self.btn_dl.config(text=self.tr("downloading"), state="disabled", bg="#333")
            threading.Thread(target=self.worker_download, daemon=True).start()
    
    def worker_download(self):
        p = self.path_library
        # [ANTI-ERROR] Konfigurasi Download
        ydl_opts = {
            'format': 'bestaudio/best', 
            'ffmpeg_location': self.path_ffmpeg, 
            'outtmpl': os.path.join(p,'%(title)s.%(ext)s'), 
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}], 
            'quiet': True, 'no_warnings': True, 'ignoreerrors': True,
            # --- FIX ERROR 416 ---
            'source_address': '0.0.0.0',
            'no_continue': True,
            'http_chunk_size': 10485760
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([self.current_song_data['url']])
            self.root.after(0, lambda: messagebox.showinfo(self.tr("dl_success"), f"{self.tr('dl_msg')}\n{p}"))
            self.root.after(0, lambda: self.btn_dl.config(text="⬇ MP3", state="normal", bg=self.col_accent))
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    # Pastikan icon ada atau lewati
    if os.path.exists("assets/icon_rog.ico"): 
        try: root.iconbitmap("assets/icon_rog.ico")
        except: pass
    app = SpotifyCloneROG(root)
    root.mainloop()