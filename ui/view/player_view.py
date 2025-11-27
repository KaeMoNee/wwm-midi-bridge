import os
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk

from core.midi_player_engine import MidiPlayerEngine
from ui.components import create_header_label
from ui.style import Theme


# TODO make midi files list as global with transpose being calculated and saved for them
class PlayerView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.player = MidiPlayerEngine(
            on_progress=self.update_status_label,
            on_stop=self.on_playback_finished,
            on_info_update=self.update_time_info,
        )

        self.current_folder = ""
        self.midi_files_map = []

        self.grid_columnconfigure(0, weight=0)  # File List (Left/Top)
        self.grid_columnconfigure(1, weight=1)  # Controls (Right/Bottom)
        self.grid_rowconfigure(1, weight=1)  # Content expands

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        create_header_label(header, "player.header").pack(side="left")

        self.btn_folder = ctk.CTkButton(header, text="Select Folder", width=120,
                                        fg_color=Theme.ACCENT, command=self.select_folder)
        self.btn_folder.pack(side="right")

        # --- Left Side: File List ---
        list_container = ctk.CTkFrame(self, width=360, fg_color="transparent")
        list_container.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(0, 10))
        list_container.grid_propagate(False)
        list_container.grid_rowconfigure(0, weight=1)
        list_container.grid_columnconfigure(0, weight=1)

        self.scrollbar = ctk.CTkScrollbar(list_container)
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.file_listbox = tk.Listbox(
            list_container,
            bg=Theme.BG_PANEL,
            fg=Theme.TEXT_MAIN,
            selectbackground=Theme.ACCENT,
            selectforeground="white",
            borderwidth=0,
            highlightthickness=0,
            font=Theme.FONT_MONO,
            activestyle="none",
            yscrollcommand=self.scrollbar.set
        )
        self.file_listbox.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.configure(command=self.file_listbox.yview)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)

        # --- Right Side: Controls ---
        controls_frame = ctk.CTkFrame(self, fg_color=Theme.BG_PANEL)
        controls_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=(0, 10))

        ctk.CTkLabel(controls_frame, text="Now Playing:", font=Theme.FONT_NORMAL, text_color="gray").pack(pady=(20, 5))

        self.lbl_song_name = ctk.CTkLabel(controls_frame, text="Select a file...",
                                          font=Theme.FONT_HEADER, text_color=Theme.ACCENT,
                                          wraplength=300)
        self.lbl_song_name.pack(pady=5, padx=10)

        info_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        info_frame.pack(pady=10)

        self.lbl_bpm = ctk.CTkLabel(info_frame, text="BPM: --", font=("Consolas", 14, "bold"))
        self.lbl_bpm.pack(side="left", padx=15)

        ctk.CTkLabel(info_frame, text="|", text_color="gray").pack(side="left")

        self.lbl_time = ctk.CTkLabel(info_frame, text="00:00 / 00:00", font=("Consolas", 14))
        self.lbl_time.pack(side="left", padx=15)

        self.lbl_status = ctk.CTkLabel(controls_frame, text="Ready", text_color="gray")
        self.lbl_status.pack(pady=5)

        # Speed Control
        # ctk.CTkLabel(controls_frame, text="Playback Speed").pack(pady=(20, 5))
        # self.slider_speed = ctk.CTkSlider(controls_frame, from_=0.1, to=2.0, number_of_steps=19,
        #                                   command=self.update_speed)
        # self.slider_speed.set(1.0)
        # self.slider_speed.pack(pady=5, padx=20, fill="x")
        #
        # self.lbl_speed_val = ctk.CTkLabel(controls_frame, text="1.0x")
        # self.lbl_speed_val.pack(pady=0)

        # Buttons
        btn_box = ctk.CTkFrame(controls_frame, fg_color="transparent")
        btn_box.pack(pady=30, fill="x")

        self.btn_play = ctk.CTkButton(btn_box, text="▶ PLAY (F11)", fg_color=Theme.SUCCESS,
                                      height=50, state="disabled", command=self.toggle_play)
        self.btn_play.pack(side="left", padx=10, expand=True, fill="x")

        self.btn_stop = ctk.CTkButton(btn_box, text="⏹ STOP (F11)", fg_color=Theme.DANGER,
                                      height=50, state="disabled", command=self.stop_playback)
        self.btn_stop.pack(side="right", padx=10, expand=True, fill="x")

        # Info Note
        ctk.CTkLabel(controls_frame, text="* Auto-transposed to fit keys.\n* Press F11 to emergency stop.",
                     font=("Arial", 12), text_color="gray").pack(side="bottom", pady=20)

        # Selected file tracking
        self.selected_file_path = None

    def destroy(self):
        """Clean up player resources when the view is closed."""
        if self.player:
            self.player.stop()
            # Break references to callbacks to prevent them from being called on dead object
            self.player.on_progress = None
            self.player.on_stop = None
            self.player.on_info_update = None
        super().destroy()

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.current_folder = folder
            self.load_files_from_folder()

    def load_files_from_folder(self):
        self.file_listbox.delete(0, tk.END)
        self.midi_files_map = []

        try:
            files = [f for f in os.listdir(self.current_folder) if f.lower().endswith(('.mid', '.midi'))]
            files.sort()

            if not files:
                self.file_listbox.insert(tk.END, "No MIDI files found")
                return

            for f in files:
                self.file_listbox.insert(tk.END, f"♪ {f}")
                full_path = os.path.join(self.current_folder, f)
                self.midi_files_map.append(full_path)

        except Exception as e:
            print(f"Error: {e}")

    def on_file_select(self, event):
        selection = self.file_listbox.curselection()
        if not selection:
            return

        index = selection[0]

        if index >= len(self.midi_files_map):
            return

        full_path = self.midi_files_map[index]
        file_name = os.path.basename(full_path)

        self.selected_file_path = full_path
        self.lbl_song_name.configure(text=file_name)
        self.btn_play.configure(state="normal")
        self.lbl_time.configure(text="00:00 / --:--")
        self.lbl_bpm.configure(text="BPM: --")
        self.player.armed_file = full_path

    def select_file(self, path, name):
        self.selected_file_path = path
        self.lbl_song_name.configure(text=name)
        self.btn_play.configure(state="normal")
        self.lbl_status.configure(text="Selected")

    # def update_speed(self, value):
    #     self.player.set_speed(value)
    #     self.lbl_speed_val.configure(text=f"{value:.1f}x")

    def toggle_play(self):
        if not self.selected_file_path:
            return

        if self.player.is_playing:
            # Can be paused? Should implement this?
            pass
        else:
            self.player.play_file(self.selected_file_path)
            self.update_ui_state(playing=True)

    def stop_playback(self):
        self.player.stop()

    def on_playback_finished(self):
        self.after(0, lambda: self.update_ui_state(playing=False))

    def update_ui_state(self, playing):
        if not self.winfo_exists():
            return

        if playing:
            self.btn_play.configure(state="disabled", text="Playing...")
            self.btn_stop.configure(state="normal")
            self.lbl_status.configure(text="Playing...", text_color=Theme.SUCCESS)
        else:
            self.btn_play.configure(state="normal", text="▶ PLAY (F11)")
            self.btn_stop.configure(state="disabled")
            self.lbl_status.configure(text="Stopped", text_color="gray")

    def update_status_label(self, text):
        self.after(0, lambda: self.lbl_status.configure(text=text, text_color=Theme.ACCENT))

    def update_time_info(self, total_sec, bpm, current_sec):
        def fmt(s):
            mins = int(s // 60)
            secs = int(s % 60)
            return f"{mins:02}:{secs:02}"

        t_str = f"{fmt(current_sec)} / {fmt(total_sec)}"
        bpm_str = f"BPM: {int(bpm)}"

        self.after(0, lambda: self.lbl_time.configure(text=t_str))
        self.after(0, lambda: self.lbl_bpm.configure(text=bpm_str))
