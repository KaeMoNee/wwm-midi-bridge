import traceback
from datetime import datetime

import customtkinter as ctk

from core import config, i18n
from ui.app import MidiApp

if __name__ == "__main__":
    try:
        config.load_config()
        i18n.init_translation(config.get_language())
        ctk.set_appearance_mode('dark')
        ctk.set_default_color_theme('dark-blue')
        app = MidiApp()
        app.mainloop()
    except Exception as e:
        # Global crash handler
        with open("WWM-Midi-Bridge-logs.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now()}] CRITICAL CRASH: {e}\n")
            f.write(traceback.format_exc())
