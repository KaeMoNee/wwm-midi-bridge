import threading
import time

import keyboard
import mido

from core import config, logger, i18n


class MidiPlayerEngine:
    def __init__(self, on_progress=None, on_stop=None, on_info_update=None):
        self.is_playing = False
        self.stop_signal = False
        self.speed = 1.0
        self.current_thread = None
        self.armed_file = None

        self.on_progress = on_progress
        self.on_stop = on_stop
        self.on_info_update = on_info_update

        try:
            keyboard.add_hotkey('f11', self.toggle)
        except ImportError:
            pass

    def set_speed(self, value):
        self.speed = value

    def toggle(self):
        if self.is_playing:
            self.stop()
        else:
            self.play_file(self.armed_file)

    def stop(self):
        self.stop_signal = True
        self.is_playing = False
        if self.on_stop:
            self.on_stop()

    def trigger_start_from_hotkey(self):
        if self.armed_file and not self.is_playing:
            self.play_file(self.armed_file)

    def play_file(self, file_path):
        if self.is_playing:
            self.stop()
            time.sleep(0.1)  # pause a bit to reflect changes

        self.stop_signal = False
        self.is_playing = True

        # Run in a separate thread
        self.armed_file = file_path
        self.current_thread = threading.Thread(target=self._play_thread, args=(file_path,), daemon=True)
        self.current_thread.start()

    def _play_thread(self, file_path):
        try:
            mid = mido.MidiFile(file_path)

            total_duration = mid.length
            bpm = 120

            for track in mid.tracks:
                for msg in track:
                    if msg.type == 'set_tempo':
                        bpm = mido.tempo2bpm(msg.tempo)
                        break
                if bpm != 120: break

            if self.on_info_update:
                self.on_info_update(total_duration, bpm, 0)

            # Calculate transposition
            mapping = config.get_note_mapping()  # {str(note): key}
            valid_notes = {int(k) for k in mapping.keys()}  # Set of available integers

            # Gather all notes
            song_notes = []
            for track in mid.tracks:
                for msg in track:
                    if msg.type == 'note_on':
                        song_notes.append(msg.note)

            if not song_notes:
                logger.log(i18n.t("player.midi.no_notes"))
                self.stop()
                return

            # Find the best offset
            best_offset = 0
            max_matches = -1

            for offset in range(-24, 25):
                matches = sum(1 for note in song_notes if (note + offset) in valid_notes)
                if matches > max_matches:
                    max_matches = matches
                    best_offset = offset

            logger.log(i18n.t("player.midi.transposed", offset=best_offset, matches=max_matches, total=len(song_notes)))

            if self.on_progress:
                for i in range(3, 0, -1):
                    if self.stop_signal: return
                    self.on_progress(f"Starting in {i}...")
                    time.sleep(1)
                self.on_progress(f"Playing...")

            # Play logic
            start_time = time.perf_counter()
            input_time = 0.0

            last_ui_update = 0  # counter against the spam in UI

            for msg in mid:
                if self.stop_signal:
                    break

                input_time += msg.time
                playback_time = time.perf_counter() - start_time
                duration_to_wait = (input_time - playback_time * self.speed) / self.speed

                if duration_to_wait > 0:
                    time.sleep(duration_to_wait)

                if self.on_info_update and (input_time - last_ui_update > 0.5):
                    self.on_info_update(total_duration, bpm, input_time)
                    last_ui_update = input_time

                if msg.type == 'note_on' and msg.velocity > 0:
                    target_note = msg.note + best_offset
                    # Check if the note is in mapping
                    if str(target_note) in mapping:
                        key_char = mapping[str(target_note)]
                        keyboard.press_and_release(key_char)

        except Exception as e:
            print(f"Error playing midi: {e}")
        finally:
            self.is_playing = False
            if self.on_stop:
                self.on_stop()
