import customtkinter as ctk

from core import config, i18n
from ui.components import create_header_label, I18nCheckBox, create_normal_label
from ui.style import Theme


def _update_mapping(note, new_key):
    mapping = config.get_note_mapping()
    if mapping.get(str(note)) != new_key:
        mapping[str(note)] = new_key
        config.save_config()


def _create_mapping_row(parent, midi_note, current_key):
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", pady=2)

    # MIDI Note Label
    ctk.CTkLabel(row, text=f"MIDI {midi_note}", width=80, anchor="w", font=Theme.FONT_MONO).pack(side="left",
                                                                                                 padx=5)
    ctk.CTkLabel(row, text="->", width=30).pack(side="left")

    # Key Entry
    entry = ctk.CTkEntry(row, placeholder_text=current_key)
    entry.insert(0, current_key)
    entry.pack(side="left", fill="x", expand=True, padx=5)

    # Bind focus out to save the specific mapping
    entry.bind("<FocusOut>", lambda event, n=midi_note, e=entry: _update_mapping(n, e.get()))
    entry.bind("<Return>", lambda event, n=midi_note, e=entry: _update_mapping(n, e.get()))


def _change_language(lang):
    config.set_language(lang)
    i18n.init_translation(lang)


class SettingsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        create_header_label(self, "settings.header").pack(anchor="nw", pady=8, padx=8)
        lbl_language = create_normal_label(self, "settings.language")
        lbl_language.pack(anchor="nw", padx=8, pady=8)
        self.lang_select = ctk.CTkOptionMenu(
            self, values=i18n.get_available_languages(), command=_change_language)
        self.lang_select.pack(padx=8, pady=8, anchor="nw")

        self.check_verbose = I18nCheckBox(
            self, "settings.verbose",
            fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_HOVER,
            command=self.toggle_verbose)
        self.check_verbose.pack(padx=8, pady=8, anchor="nw")

        # Mapping
        lbl_mapping = create_header_label(self, "settings.mapping")
        lbl_mapping.pack(anchor="nw", padx=8, pady=8)
        self.config_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.config_scroll.pack(fill="both", expand=True)

        self.load_mapping_ui()

        self.load_initial_settings()

    def load_initial_settings(self):
        # Set UI state based on config
        current_lang = config.get_language()
        self.lang_select.set(current_lang)

        is_verbose = config.get_verbose()
        if is_verbose:
            self.check_verbose.select()
        else:
            self.check_verbose.deselect()
        pass

    def toggle_verbose(self):
        state = self.check_verbose.get()
        config.set_verbose(bool(state))

    def load_mapping_ui(self):
        # Clear existing widgets in scroll frame
        for widget in self.config_scroll.winfo_children():
            widget.destroy()

        mapping = config.get_note_mapping()
        # Sort by MIDI note number
        sorted_notes = sorted(mapping.keys(), key=lambda x: int(x) if x.isdigit() else 0)

        for note in sorted_notes:
            key = mapping[note]
            _create_mapping_row(self.config_scroll, note, key)
