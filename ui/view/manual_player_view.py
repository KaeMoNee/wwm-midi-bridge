import tkinter as tk

import customtkinter as ctk
import mido

from ui.style import Theme


class ManualPlayerView(ctk.CTkFrame):
    def __init__(self, master, midi_handler, **kwargs):
        super().__init__(master, **kwargs)

        self.midi_handler = midi_handler

        self.is_running = False
        self.notes_data = []
        self.current_time = 0.0
        self.total_duration = 0.0
        self.bpm = 120
        self.transposition = 0

        self.scroll_speed = 150
        self.lookahead_time = 4.0

        self.waiting_for_notes = []
        self.pressed_keys = set()

        # C3 -> B5
        self.start_note = 48
        self.end_note = 83

        # Size with recalculation with resize event
        self.white_key_width = 30
        self.black_key_width = 20

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, height=50, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="left")

        ctk.CTkButton(btn_frame, text="📂 Load", width=80,
                      command=self.load_midi_file).pack(side="left", padx=2)

        self.btn_start = ctk.CTkButton(btn_frame, text="Start", width=70,
                                       command=self.toggle_game, state="disabled",
                                       fg_color=Theme.SUCCESS)
        self.btn_start.pack(side="left", padx=2)

        self.btn_restart = ctk.CTkButton(btn_frame, text="↺", width=40,
                                         command=self.restart_game, state="disabled",
                                         fg_color=Theme.ACCENT)
        self.btn_restart.pack(side="left", padx=2)

        info_frame = ctk.CTkFrame(header, fg_color="transparent")
        info_frame.pack(side="right", padx=10)

        self.lbl_trans = ctk.CTkLabel(info_frame, text="Trans: 0", font=("Consolas", 14), text_color="gray")
        self.lbl_trans.pack(side="left", padx=10)

        self.lbl_bpm = ctk.CTkLabel(info_frame, text="BPM: --", font=("Consolas", 14, "bold"))
        self.lbl_bpm.pack(side="left", padx=10)

        self.lbl_time = ctk.CTkLabel(info_frame, text="00:00 / 00:00", font=("Consolas", 14))
        self.lbl_time.pack(side="left", padx=10)

        self.lbl_status = ctk.CTkLabel(self, text="Load a MIDI file to start practice", text_color="gray", height=20)
        self.lbl_status.grid(row=2, column=0, sticky="ew", pady=(0, 5))

        self.canvas_bg = "#222222"
        self.canvas = tk.Canvas(self, bg=self.canvas_bg, highlightthickness=0, bd=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 5))

        self.canvas.bind("<Configure>", self.on_resize)

        self.midi_handler.add_listener(self)

    def restart_game(self):
        if not self.notes_data: return
        self.is_running = False
        self.current_time = 0.0
        self.waiting_for_notes = []
        for n in self.notes_data:
            n['done'] = False

        self.btn_start.configure(text="Start")
        self.update_time_label()
        self.canvas.delete("note")

    def load_midi_file(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("MIDI files", "*.mid *.midi")])
        if not file_path: return

        try:
            mid = mido.MidiFile(file_path)
            self.notes_data = []

            self.total_duration = mid.length
            self.bpm = 120
            for track in mid.tracks:
                for msg in track:
                    if msg.type == 'set_tempo':
                        self.bpm = int(mido.tempo2bpm(msg.tempo))
                        break

            # Smart Transpose
            all_file_notes = []
            for track in mid.tracks:
                for msg in track:
                    if msg.type == 'note_on':
                        all_file_notes.append(msg.note)

            best_offset = 0
            if all_file_notes:
                max_matches = -1
                for offset in range(-24, 25):
                    matches = sum(1 for n in all_file_notes if self.start_note <= (n + offset) <= self.end_note)
                    if matches > max_matches:
                        max_matches = matches
                        best_offset = offset

            self.transposition = best_offset

            current_time = 0
            for msg in mid:
                current_time += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    final_note = msg.note + best_offset

                    if self.start_note <= final_note <= self.end_note:
                        self.notes_data.append({
                            'note': final_note,
                            'start': current_time,
                            'length': 0.5,
                            'done': False
                        })

            self.notes_data.sort(key=lambda x: x['start'])

            trans_sign = "+" if self.transposition >= 0 else ""
            self.lbl_trans.configure(text=f"Trans: {trans_sign}{self.transposition}")
            self.lbl_bpm.configure(text=f"BPM: {self.bpm}")
            self.lbl_status.configure(text=f"Loaded {len(self.notes_data)} notes (Optimized for range).")

            self.btn_start.configure(state="normal")
            self.btn_restart.configure(state="normal")
            self.restart_game()

        except Exception as e:
            self.lbl_status.configure(text=f"Error: {e}")
            print(e)

    def toggle_game(self):
        if self.is_running:
            self.is_running = False
            self.btn_start.configure(text="Continue")
        else:
            self.is_running = True
            self.btn_start.configure(text="Pause")
            self.game_loop()

    def game_loop(self):
        if not self.is_running: return

        blockers = [n for n in self.notes_data
                    if self.current_time >= n['start'] > self.current_time - 0.5 and not n['done']]

        self.waiting_for_notes = blockers

        if not blockers:
            self.current_time += 0.02
        else:
            self.lbl_status.configure(text=f"WAITING INPUT...")

        self.update_time_label()
        self.update_falling_notes()

        if self.notes_data and all(n['done'] for n in self.notes_data):
            self.is_running = False
            self.lbl_status.configure(text="Song Finished!")
            self.btn_start.configure(text="Finished")
        else:
            self.after(20, self.game_loop)

    def update_time_label(self):
        def fmt(s):
            m = int(s // 60)
            sec = int(s % 60)
            return f"{m:02}:{sec:02}"

        self.lbl_time.configure(text=f"{fmt(self.current_time)} / {fmt(self.total_duration)}")

    def on_midi_input(self, msg):
        self.after(0, lambda: self._on_midi_input(msg))

    def _on_midi_input(self, msg):
        if msg.type == 'note_on' and msg.velocity > 0:
            self.pressed_keys.add(msg.note)
            self.check_hit(msg.note)
            self.set_key_color(msg.note, True)
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            if msg.note in self.pressed_keys:
                self.pressed_keys.remove(msg.note)
            self.set_key_color(msg.note, False)

    def set_key_color(self, note, is_pressed):
        if note < self.start_note or note > self.end_note: return

        if self.is_black_key(note):
            color = "#00cc00" if is_pressed else "black"
        else:
            color = "#66ff66" if is_pressed else "#dddddd"

        self.canvas.itemconfig(f"key_{note}", fill=color)

    def check_hit(self, note):
        for n in self.waiting_for_notes:
            if n['note'] == note:
                n['done'] = True

    def on_resize(self, event):
        self.init_static_scene()
        self.update_falling_notes()

    def calculate_dimensions(self):
        w = self.canvas.winfo_width()
        if w < 10: return

        num_white = 0
        for n in range(self.start_note, self.end_note + 1):
            if not self.is_black_key(n):
                num_white += 1

        if num_white == 0: num_white = 1
        self.white_key_width = w / num_white
        self.black_key_width = self.white_key_width * 0.65

    def get_x_for_note(self, note):
        if note < self.start_note or note > self.end_note: return None

        white_index = 0
        for n in range(self.start_note, note):
            if not self.is_black_key(n):
                white_index += 1

        base_x = white_index * self.white_key_width

        if self.is_black_key(note):
            return base_x - (self.black_key_width / 2)
        else:
            return base_x

    def init_static_scene(self):
        self.canvas.delete("static")
        self.calculate_dimensions()

        h = self.canvas.winfo_height()
        key_h = 120
        hit_y = h - key_h
        self.hit_line_y = hit_y

        wk_idx = 0
        for note in range(self.start_note, self.end_note + 1):
            if not self.is_black_key(note):
                x = wk_idx * self.white_key_width

                self.canvas.create_line(x, 0, x, h, fill="#333333", width=1, tags="static")

                is_pressed = note in self.pressed_keys
                color = "#66ff66" if is_pressed else "#dddddd"

                self.canvas.create_rectangle(
                    x, hit_y, x + self.white_key_width, h,
                    fill=color, outline="black",
                    tags=("static", f"key_{note}")
                )

                if note % 12 == 0:
                    octave = (note // 12) - 1
                    self.canvas.create_text(
                        x + self.white_key_width / 2, h - 20,
                        text=f"C{octave}", font=("Arial", 10, "bold"), fill="#555",
                        tags="static"
                    )

                self.canvas.create_line(x + self.white_key_width, 0, x + self.white_key_width, h, fill="#333333",
                                        width=1,
                                        tags="static")
                wk_idx += 1

        for note in range(self.start_note, self.end_note + 1):
            if self.is_black_key(note):
                x = self.get_x_for_note(note)
                is_pressed = note in self.pressed_keys
                color = "#00cc00" if is_pressed else "black"

                self.canvas.create_rectangle(
                    x, hit_y, x + self.black_key_width, hit_y + (key_h * 0.6),
                    fill=color, outline="gray",
                    tags=("static", f"key_{note}")
                )

        self.canvas.create_line(0, hit_y, 3000, hit_y, fill="#00bfff", width=2, dash=(4, 2), tags="static")

        self.canvas.tag_raise("note")

    def update_falling_notes(self):
        self.canvas.delete("note")

        visible_notes = [n for n in self.notes_data
                         if self.current_time - 1 < n['start'] < self.current_time + self.lookahead_time
                         and not n['done']]

        hit_y = getattr(self, 'hit_line_y', self.canvas.winfo_height() - 120)

        for n in visible_notes:
            dt = n['start'] - self.current_time
            y = hit_y - (dt * self.scroll_speed)
            x = self.get_x_for_note(n['note'])

            if x is None: continue

            is_black = self.is_black_key(n['note'])
            w = self.black_key_width if is_black else self.white_key_width

            color = "#4a90e2"
            if n in self.waiting_for_notes:
                color = "#ff4757"
                y = hit_y

            self.canvas.create_rectangle(
                x, y - 25, x + w, y,
                fill=color, outline="white" if is_black else "black",
                tags="note"
            )

    def is_black_key(self, note):
        return (note % 12) in [1, 3, 6, 8, 10]
