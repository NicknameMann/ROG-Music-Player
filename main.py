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

# --- FUNGSI RESOURCE PATH ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- FUNGSI PATH DATA USER (PERSISTENT) ---
def get_data_path(filename):
    app_data = os.getenv('APPDATA') 
    data_dir = os.path.join(app_data, "ROGMusicPlayer")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return os.path.join(data_dir, filename)

class SpotifyCloneROG:
    def __init__(self, root):
        self.root = root
        self.root.title("Rafi's ROG Player v1.1")
        self.root.geometry("1100x750")
        self.root.configure(bg="#121212")

        # --- PATHS ---
        self.path_assets = resource_path("assets")
        self.path_ffmpeg = resource_path("ffmpeg.exe") 
        self.path_playlist_json = get_data_path("user_playlists.json")
        self.path_settings_json = get_data_path("settings.json")

        # --- LOAD SETTINGS ---
        self.settings = self.load_settings()
        
        # Set Library Path dari Settings
        self.path_library = self.settings.get("download_path", os.path.join(os.path.expanduser("~/Music"), "ROG_Library"))
        if not os.path.exists(self.path_library):
            os.makedirs(self.path_library)

        # --- DATABASE & VLC ---
        self.playlists = self.load_playlists()
        self.current_view_playlist = None
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        
        # --- VARIABLES ---
        self.current_song_data = {} 
        self.search_results = []
        self.is_playing = False
        self.is_looping = False
        self.context_song_data = None 
        
        # --- COLORS ---
        self.col_bg = "#121212"
        self.col_sidebar = "#000000"
        self.col_player = "#181818"
        self.col_accent = "#FF0000"
        self.col_text = "#FFFFFF"
        self.col_text_sec = "#B3B3B3"

        # --- UI INIT ---
        self.setup_layout()
        self.show_home()
        self.update_timer()
        
        # Set Volume Awal
        start_vol = self.settings.get("default_volume", 80)
        self.player.audio_set_volume(start_vol)
        self.vol_slider.set(start_vol)

        # --- KEYBOARD ---
        self.root.bind("<space>", self.on_key_space)
        self.root.bind("<Right>", self.on_key_right)
        self.root.bind("<Left>", self.on_key_left)

    # --- SETTINGS SYSTEM ---
    def load_settings(self):
        default_settings = {
            "download_path": os.path.join(os.path.expanduser("~/Music"), "ROG_Library"),
            "default_volume": 80
        }
        if os.path.exists(self.path_settings_json):
            try:
                with open(self.path_settings_json, 'r') as f:
                    data = json.load(f)
                    default_settings.update(data)
                    return default_settings
            except: pass
        return default_settings

    def save_settings(self):
        with open(self.path_settings_json, 'w') as f:
            json.dump(self.settings, f)

    def change_download_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.settings["download_path"] = folder_selected
            self.path_library = folder_selected
            self.save_settings()
            self.show_settings()
            messagebox.showinfo("Berhasil", f"Lokasi penyimpanan diubah ke:\n{folder_selected}")

    # --- LOGIKA KEYBOARD ---
    def on_key_space(self, event):
        if isinstance(event.widget, tk.Entry): return
        self.play_pause_music()

    def on_key_right(self, event):
        if isinstance(event.widget, tk.Entry): return
        self.skip_time(10)

    def on_key_left(self, event):
        if isinstance(event.widget, tk.Entry): return
        self.skip_time(-10)

    def load_img(self, name, size=(24, 24)):
        try:
            path = os.path.join(self.path_assets, name)
            if os.path.exists(path):
                img = Image.open(path).resize(size, Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
        except: pass
        return None

    # --- DATABASE PLAYLIST ---
    def load_playlists(self):
        if os.path.exists(self.path_playlist_json):
            try:
                with open(self.path_playlist_json, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict): return data
            except: pass
        return {"Favorites": []}

    def save_playlists(self):
        with open(self.path_playlist_json, 'w') as f:
            json.dump(self.playlists, f)

    def open_save_dialog(self, target_song=None):
        song_to_save = target_song if target_song else self.current_song_data
        if not song_to_save or not song_to_save.get('url'): 
            messagebox.showwarning("Info", "Tidak ada lagu yang dipilih!")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Simpan Lagu")
        dialog.geometry("400x450")
        dialog.configure(bg="#222")
        dialog.transient(self.root)
        
        tk.Label(dialog, text=f"Simpan: {song_to_save['title'][:30]}...", fg="white", bg="#222", font=("Arial", 10)).pack(pady=(10, 5))
        tk.Label(dialog, text="Pilih Playlist:", fg=self.col_accent, bg="#222", font=("Arial", 12, "bold")).pack(pady=5)

        frame_list = tk.Frame(dialog, bg="#222")
        frame_list.pack(fill="both", expand=True, padx=20)
        
        lb = tk.Listbox(frame_list, bg="#333", fg="white", font=("Arial", 11), bd=0, highlightthickness=0)
        lb.pack(side="left", fill="both", expand=True)
        scroll = tk.Scrollbar(frame_list, command=lb.yview)
        scroll.pack(side="right", fill="y")
        lb.config(yscrollcommand=scroll.set)

        for pl_name in self.playlists.keys():
            lb.insert(tk.END, f"📂 {pl_name}")

        tk.Label(dialog, text="Atau Playlist Baru:", fg="gray", bg="#222", font=("Arial", 10)).pack(pady=(15, 5))
        entry_new = tk.Entry(dialog, font=("Arial", 11))
        entry_new.pack(fill="x", padx=20)

        def confirm_save():
            selected_indices = lb.curselection()
            new_name = entry_new.get().strip()
            target_playlist = ""
            
            if new_name:
                target_playlist = new_name
                if target_playlist not in self.playlists:
                    self.playlists[target_playlist] = []
            elif selected_indices:
                selection = lb.get(selected_indices[0])
                target_playlist = selection.replace("📂 ", "")
            else:
                messagebox.showerror("Error", "Pilih playlist dulu!")
                return

            exists = any(s['url'] == song_to_save['url'] for s in self.playlists[target_playlist])
            if exists:
                messagebox.showinfo("Info", f"Lagu sudah ada di '{target_playlist}'")
            else:
                self.playlists[target_playlist].append(song_to_save)
                self.save_playlists()
                messagebox.showinfo("Sukses", f"Disimpan ke: {target_playlist}")
            dialog.destroy()

        tk.Button(dialog, text="💾 SIMPAN", command=confirm_save, bg=self.col_accent, fg="white", font=("Arial", 11, "bold"), bd=0, pady=10).pack(fill="x", padx=20, pady=20)

    # --- UI LAYOUT ---
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
        self.btn_nav("📂  My Playlists", self.show_library)
        self.btn_nav("⚙️  Settings", self.show_settings) 

        tk.Label(self.sidebar, text="INFO / LYRICS:", fg="gray", bg=self.col_sidebar, 
                 font=("Arial", 9, "bold")).pack(pady=(30, 5), padx=20, anchor="w")
        self.lyrics_box = tk.Text(self.sidebar, bg="#111", fg="#ddd", font=("Consolas", 9), 
                                  bd=0, height=25, padx=10, pady=10, wrap="word")
        self.lyrics_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.lyrics_box.insert(tk.END, "Tekan SPASI untuk Play/Pause.\nPanah Kanan/Kiri untuk Skip.")
        self.lyrics_box.config(state="disabled")

        # 2. MAIN AREA
        self.main_area = tk.Frame(self.root, bg=self.col_bg)
        self.main_area.grid(row=0, column=1, sticky="nsew")

        # 3. PLAYER BAR
        self.player_bar = tk.Frame(self.root, bg=self.col_player, height=100, borderwidth=1, relief="ridge")
        self.player_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.player_bar.pack_propagate(False)

        self.setup_player_controls()

        # 4. CONTEXT MENU
        self.context_menu = tk.Menu(self.root, tearoff=0, bg="#333", fg="white")
        self.context_menu.add_command(label="▶ Putar Sekarang", command=self.play_context_song)
        self.context_menu.add_command(label="➕ Simpan ke Playlist", command=self.save_context_song)

    def btn_nav(self, text, command):
        btn = tk.Button(self.sidebar, text=text, bg=self.col_sidebar, fg=self.col_text_sec, 
                        font=("Arial", 11, "bold"), bd=0, activebackground=self.col_sidebar, 
                        activeforeground="white", cursor="hand2", command=command, anchor="w", padx=20)
        btn.pack(fill="x", pady=5)

    def setup_player_controls(self):
        # Kiri
        left_box = tk.Frame(self.player_bar, bg=self.col_player)
        left_box.pack(side="left", padx=20)
        self.lbl_track = tk.Label(left_box, text="Ready", bg=self.col_player, fg="white", font=("Arial", 11, "bold"))
        self.lbl_track.pack(anchor="w")
        self.lbl_timer = tk.Label(left_box, text="--:-- / --:--", bg=self.col_player, fg=self.col_accent, font=("Consolas", 10))
        self.lbl_timer.pack(anchor="w")
        
        # Tengah
        ctrl_frame = tk.Frame(self.player_bar, bg=self.col_player)
        ctrl_frame.pack(side="left", expand=True, fill="x")
        center_box = tk.Frame(ctrl_frame, bg=self.col_player)
        center_box.pack(anchor="center")

        self.icon_play = self.load_img("play.png", (35, 35))
        self.icon_pause = self.load_img("pause.png", (35, 35))
        self.icon_stop = self.load_img("stop.png", (25, 25))

        tk.Button(center_box, text="💾", command=lambda: self.open_save_dialog(None), bg=self.col_player, fg="white", bd=0, font=("Arial", 14)).pack(side="left", padx=15)
        self.btn_loop = tk.Button(center_box, text="🔁", command=self.toggle_loop, bg=self.col_player, fg="gray", bd=0, font=("Arial", 12))
        self.btn_loop.pack(side="left", padx=10)

        tk.Button(center_box, text="⏪", command=lambda: self.skip_time(-10), bg=self.col_player, fg="white", bd=0, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        self.btn_play = tk.Button(center_box, image=self.icon_play, command=self.play_pause_music, bg=self.col_player, bd=0)
        self.btn_play.pack(side="left", padx=10)
        tk.Button(center_box, text="⏩", command=lambda: self.skip_time(10), bg=self.col_player, fg="white", bd=0, font=("Arial", 12, "bold")).pack(side="left", padx=5)

        # Kanan (FIXED VOLUME SLIDER)
        right_box = tk.Frame(self.player_bar, bg=self.col_player)
        right_box.pack(side="right", padx=20)
        tk.Label(right_box, text="Vol", bg=self.col_player, fg="gray").pack(side="left", padx=(0,5))
        
        # SLIDER VOLUME (DIPERBAIKI)
        self.vol_slider = ttk.Scale(right_box, from_=0, to=100, orient="horizontal", command=self.set_volume)
        self.vol_slider.set(80) 
        self.vol_slider.pack(side="left", padx=5) # <--- INI YG TADI KETINGGALAN

        self.btn_dl = tk.Button(right_box, text="⬇ MP3", command=self.start_download, 
                                bg=self.col_player, fg=self.col_text_sec, font=("Arial", 8, "bold"), bd=0, state="disabled")
        self.btn_dl.pack(side="left", padx=15)

    def clear_main_area(self):
        for widget in self.main_area.winfo_children(): widget.destroy()

    # --- HALAMAN SETTINGS ---
    def show_settings(self):
        self.clear_main_area()
        tk.Label(self.main_area, text="Pengaturan / Settings", bg=self.col_bg, fg="white", font=("Arial", 32, "bold")).pack(padx=40, pady=40, anchor="w")
        
        setting_frame = tk.Frame(self.main_area, bg=self.col_bg)
        setting_frame.pack(padx=40, anchor="w", fill="x")

        tk.Label(setting_frame, text="📂 Folder Penyimpanan (Download):", bg=self.col_bg, fg=self.col_accent, font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 5))
        
        path_box = tk.Frame(setting_frame, bg="#222", padx=10, pady=10)
        path_box.pack(fill="x", anchor="w", pady=(0, 20))
        
        tk.Label(path_box, text=self.path_library, bg="#222", fg="white", font=("Consolas", 11)).pack(side="left", padx=10)
        tk.Button(path_box, text="Ubah Folder", command=self.change_download_folder, bg=self.col_accent, fg="white", bd=0, font=("Arial", 10, "bold"), padx=15).pack(side="right")
        
        tk.Label(setting_frame, text="* Lagu yang didownload akan otomatis masuk ke folder di atas.", bg=self.col_bg, fg="gray").pack(anchor="w")

        tk.Label(setting_frame, text="🔊 Default Volume:", bg=self.col_bg, fg=self.col_accent, font=("Arial", 14, "bold")).pack(anchor="w", pady=(20, 5))
        tk.Label(setting_frame, text="Atur volume lewat slider di kanan bawah (Otomatis tersimpan di memori saat aplikasi berjalan).", bg=self.col_bg, fg="gray").pack(anchor="w")

    def show_home(self):
        self.clear_main_area()
        tk.Label(self.main_area, text="Selamat Datang di ROG Music Player", bg=self.col_bg, fg="white", font=("Arial", 32, "bold")).pack(padx=40, pady=(40, 10), anchor="w")
        tk.Label(self.main_area, text="ROG Music Player (Settings Edition)", bg=self.col_bg, fg=self.col_accent, font=("Arial", 16, "bold")).pack(padx=40, anchor="w")
        
        info_frame = tk.Frame(self.main_area, bg=self.col_bg)
        info_frame.pack(padx=40, pady=20, anchor="w")
        
        features = [
            ("⚙️ SETTINGS", "Atur lokasi penyimpanan download sesuka hati!"),
            ("⌨️ SPASI", "Play / Pause musik"),
            ("⌨️ ARAH KANAN", "Skip Maju 10 Detik"),
            ("🖱️ KLIK KANAN", "Menu Opsi Lagu (Play / Simpan)"),
            ("⬇️ DOWNLOAD", "Simpan Lagu MP3 (Offline)")
        ]
        
        for icon, desc in features:
            row = tk.Frame(info_frame, bg=self.col_bg)
            row.pack(fill="x", pady=8)
            tk.Label(row, text=icon, bg=self.col_bg, fg="white", font=("Arial", 12, "bold"), width=15, anchor="w").pack(side="left")
            tk.Label(row, text=desc, bg=self.col_bg, fg=self.col_text_sec, font=("Arial", 12)).pack(side="left")

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

        container = tk.Frame(self.main_area, bg=self.col_bg)
        container.pack(fill="both", expand=True, padx=30, pady=5)

        self.canvas_search = tk.Canvas(container, bg=self.col_bg, bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas_search.yview)
        self.scrollable_frame = tk.Frame(self.canvas_search, bg=self.col_bg)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas_search.configure(scrollregion=self.canvas_search.bbox("all")))
        self.canvas_search.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas_search.configure(yscrollcommand=scrollbar.set)
        self.canvas_search.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def show_library(self):
        self.clear_main_area()
        self.current_view_playlist = None 
        self.lbl_lib_header = tk.Label(self.main_area, text="My Playlists & Files", bg=self.col_bg, fg="white", font=("Arial", 20, "bold"))
        self.lbl_lib_header.pack(padx=30, pady=(20, 10), anchor="w")
        
        tk.Label(self.main_area, text=f"📂 Sumber File Offline: {self.path_library}", bg=self.col_bg, fg="gray", font=("Arial", 9)).pack(padx=30, anchor="w", pady=(0, 10))

        list_frame = tk.Frame(self.main_area, bg=self.col_bg)
        list_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        self.lib_list = tk.Listbox(list_frame, bg=self.col_bg, fg=self.col_text_sec, font=("Arial", 11),
                                   selectbackground="#2a2a2a", selectforeground="white", bd=0, 
                                   highlightthickness=0, yscrollcommand=scrollbar.set)
        self.lib_list.pack(fill="both", expand=True)
        scrollbar.config(command=self.lib_list.yview)
        
        self.lib_list.bind("<Double-Button-1>", self.on_library_click)
        self.load_root_library()

    def search_online(self):
        query = self.entry_search.get()
        if not query: return
        self.lbl_status.config(text="Sedang mencari...", fg=self.col_accent)
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
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
        
        for i, item in enumerate(self.search_results):
            row_frame = tk.Frame(self.scrollable_frame, bg=self.col_bg, pady=5)
            row_frame.pack(fill="x", expand=True)

            lbl_title = tk.Label(row_frame, text=f"▶ {item.get('title')}", bg=self.col_bg, fg="white", font=("Arial", 11), cursor="hand2", anchor="w")
            lbl_title.pack(side="left", fill="x", expand=True, padx=5)
            
            lbl_title.bind("<Button-1>", lambda e, idx=i: self.play_specific_index(idx))
            lbl_title.bind("<Button-3>", lambda e, d=item: self.open_context_menu(e, d))
            lbl_title.bind("<Enter>", lambda e, l=lbl_title: l.config(fg=self.col_accent))
            lbl_title.bind("<Leave>", lambda e, l=lbl_title: l.config(fg="white"))

            btn_menu = tk.Button(row_frame, text="⋮", bg="#333", fg="white", bd=0, font=("Arial", 12, "bold"), cursor="hand2", width=3)
            btn_menu.config(command=lambda d=item: self.open_save_dialog_direct(d))
            btn_menu.pack(side="right", padx=5)

            tk.Frame(self.scrollable_frame, bg="#333", height=1).pack(fill="x")

    def play_specific_index(self, index):
        selected_data = self.search_results[index]
        self.start_play_process(selected_data)

    def open_save_dialog_direct(self, song_data):
        formatted_data = {"title": song_data['title'], "url": song_data['url']}
        self.open_save_dialog(formatted_data)

    def open_context_menu(self, event, data):
        self.context_song_data = {"title": data['title'], "url": data['url']}
        self.context_menu.post(event.x_root, event.y_root)

    def play_context_song(self):
        if self.context_song_data:
            self.start_play_process(self.context_song_data)

    def save_context_song(self):
        if self.context_song_data:
            self.open_save_dialog(self.context_song_data)

    def start_play_process(self, data):
        self.player.stop()
        self.lbl_status.config(text="Menyiapkan audio...", fg="yellow")
        self.current_song_data = {"title": data['title'], "url": data['url']}
        threading.Thread(target=self.worker_resolve_and_play, args=(data['url'],), daemon=True).start()

    def load_root_library(self):
        self.lib_list.delete(0, tk.END)
        self.current_view_playlist = None
        self.lbl_lib_header.config(text="My Playlists")
        self.lib_list.insert(tk.END, "--- DAFTAR PLAYLIST ---")
        self.lib_list.itemconfig(tk.END, {'fg': self.col_accent})
        for pl_name in self.playlists.keys():
            self.lib_list.insert(tk.END, f"📂 {pl_name}")
        self.lib_list.insert(tk.END, "")
        self.lib_list.insert(tk.END, "--- FILE OFFLINE ---")
        self.lib_list.itemconfig(tk.END, {'fg': '#00FF00'})
        
        if os.path.exists(self.path_library):
            for f in os.listdir(self.path_library):
                if f.endswith(".mp3"): self.lib_list.insert(tk.END, f"🎵 {f}")
        else:
             self.lib_list.insert(tk.END, "(Folder tidak ditemukan)")

    def load_playlist_content(self, playlist_name):
        self.lib_list.delete(0, tk.END)
        self.current_view_playlist = playlist_name
        self.lbl_lib_header.config(text=f"Playlist: {playlist_name}")
        self.lib_list.insert(tk.END, "🔙 ... KEMBALI KE MENU UTAMA")
        self.lib_list.itemconfig(tk.END, {'fg': 'yellow'})
        self.lib_list.insert(tk.END, "")
        songs = self.playlists.get(playlist_name, [])
        if not songs: self.lib_list.insert(tk.END, "(Playlist Kosong)")
        else:
            for song in songs: self.lib_list.insert(tk.END, f"☁️ {song['title']}")

    def on_library_click(self, event):
        if not self.lib_list.curselection(): return
        selection = self.lib_list.get(self.lib_list.curselection())
        if selection == "" or selection.startswith("---") or selection == "(Playlist Kosong)": return

        if "🔙" in selection:
            self.load_root_library()
            return
        if "📂" in selection:
            pl_name = selection.replace("📂 ", "")
            self.load_playlist_content(pl_name)
            return
        if "🎵" in selection:
            filename = selection.replace("🎵 ", "")
            self.play_offline_file(filename)
            return
        if "☁️" in selection:
            title = selection.replace("☁️ ", "")
            self.play_cloud_song(title)
            return

    def play_offline_file(self, filename):
        path = os.path.join(self.path_library, filename)
        self.player.stop()
        self.current_song_data = {"title": filename, "url": ""}
        media = self.instance.media_new(path)
        self.player.set_media(media)
        self.player.play()
        self.is_playing = True
        self.lbl_track.config(text=filename)
        self.btn_play.config(image=self.icon_pause)
        self.update_lyrics_box(f"Playing Offline:\n{filename}\n\nLokasi:\n{path}")

    def play_cloud_song(self, title):
        if not self.current_view_playlist: return
        songs = self.playlists[self.current_view_playlist]
        song_data = next((s for s in songs if s['title'] == title), None)
        if song_data:
            self.start_play_process(song_data)

    def worker_resolve_and_play(self, video_url):
        ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'force_ipv4': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                self.current_song_data['url'] = info.get('webpage_url', video_url)
                self.current_song_data['title'] = info.get('title', 'Unknown')
                self.root.after(0, lambda: self.play_stream(info['url'], info['title']))
                desc = info.get('description', 'Tidak ada deskripsi.')
                self.root.after(0, lambda: self.update_lyrics_box(f"JUDUL: {info['title']}\n\nINFO:\n{desc}"))
        except Exception as e: print(e)

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

    def update_lyrics_box(self, text):
        self.lyrics_box.config(state="normal")
        self.lyrics_box.delete("1.0", tk.END)
        self.lyrics_box.insert(tk.END, text)
        self.lyrics_box.config(state="disabled")

    def toggle_loop(self):
        self.is_looping = not self.is_looping
        self.btn_loop.config(fg="#00FF00" if self.is_looping else "gray")

    def play_pause_music(self):
        if self.is_playing:
            self.player.pause()
            self.btn_play.config(image=self.icon_play)
            self.is_playing = False
        else:
            self.player.play()
            self.btn_play.config(image=self.icon_pause)
            self.is_playing = True

    def skip_time(self, seconds):
        if self.player.is_playing():
            current = self.player.get_time() 
            new_time = max(0, current + (seconds * 1000))
            self.player.set_time(new_time)

    def set_volume(self, val):
        vol = int(float(val))
        self.player.audio_set_volume(vol)
        # Update setting di memori
        self.settings["default_volume"] = vol

    def update_timer(self):
        if self.is_playing and self.is_looping:
             if self.player.get_state() == vlc.State.Ended:
                self.player.stop()
                self.player.play()
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
        self.root.after(1000, self.update_timer)

    def start_download(self):
        if not self.current_song_data.get('url'): return
        self.btn_dl.config(text="DOWNLOADING...", state="disabled", bg="#333")
        threading.Thread(target=self.worker_download, daemon=True).start()

    def worker_download(self):
        target_path = self.path_library 
        if not os.path.exists(target_path): os.makedirs(target_path)

        ydl_opts = {
            'format': 'bestaudio/best', 
            'ffmpeg_location': self.path_ffmpeg, 
            'outtmpl': os.path.join(target_path, '%(title)s.%(ext)s'), 
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}], 
            'quiet': True, 
            'force_ipv4': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.current_song_data['url']])
            self.root.after(0, lambda: messagebox.showinfo("Sukses", f"Lagu berhasil didownload ke:\n{target_path}"))
            self.root.after(0, lambda: self.btn_dl.config(text="⬇ DOWNLOAD", state="normal", bg=self.col_accent))
        except:
            self.root.after(0, lambda: messagebox.showerror("Error", "Gagal Download."))

if __name__ == "__main__":
    root = tk.Tk()
    if os.path.exists("assets/icon_rog.ico"):
        root.iconbitmap("assets/icon_rog.ico")
    app = SpotifyCloneROG(root)
    root.mainloop()