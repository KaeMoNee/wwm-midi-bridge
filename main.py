import json
import mido
import keyboard
from colorama import init, Fore, Style
import os
import i18n
import traceback
from datetime import datetime


init(autoreset=True)

CONFIG_FILE = 'config.json'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "device_name_filter": "",
            "verbose": True,
            "note_mapping": {
                "48": "z", "49": "shift+z", "50": "x", "51": "ctrl+c", "52": "c",
                "53": "v", "54": "shift+v", "55": "b", "56": "shift+b", "57": "n",
                "58": "ctrl+m", "59": "m", "60": "a", "61": "shift+a", "62": "s",
                "63": "ctrl+d", "64": "d", "65": "f", "66": "shift+f", "67": "g",
                "68": "shift+g", "69": "h", "70": "ctrl+j", "71": "j", "72": "q",
                "73": "shift+q", "74": "w", "75": "ctrl+e", "76": "e", "77": "r",
                "78": "shift+r", "79": "t", "80": "shift+t", "81": "y", "82": "ctrl+u",
                "83": "u"
            }
        }
        save_config(default_config)
        return default_config
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def select_midi_port(device_name_filter=''):
    # Use mido to get INPUT ports
    ports = mido.get_input_names()

    if device_name_filter:
        filtered_ports = [p for p in ports if device_name_filter.lower() in p.lower()]
        if filtered_ports:
            print(Fore.CYAN + i18n.t("filtered_selection", filter=device_name_filter, port=filtered_ports[0]))
            return filtered_ports[0]

    if not ports:
        print(Fore.RED + i18n.t("no_ports_found"))
        return None

    print(Fore.CYAN + i18n.t("available_ports"))
    for i, port_name in enumerate(ports):
        print(f"  {i}: {port_name}")

    while True:
        try:
            choice = input(Fore.YELLOW + i18n.t("enter_port_number"))
            if not choice: continue
            port_index = int(choice)
            if 0 <= port_index < len(ports):
                return ports[port_index]
            else:
                print(Fore.RED + i18n.t("invalid_port_number", max_val=len(ports) - 1))
        except ValueError:
            print(Fore.RED + i18n.t("error_enter_number"))

def main():
    config = load_config()

    # --- Language Selection Logic ---
    lang = config.get('language')
    if not lang:
        available_languages = i18n.get_available_languages()
        if not available_languages:
            # Fallback if locales are missing
            print(Fore.RED + "No language files found ('locales' directory missing or empty). Exiting.")
            input("Press Enter to exit...")
            return

        print(Fore.CYAN + i18n.t("select_language_prompt"))
        lang_map = {"en": "English", "ru": "Русский"}
        for i, l_code in enumerate(available_languages):
            print(f"  {i + 1}: {lang_map.get(l_code, l_code)}")

        while True:
            choice = input(i18n.t("select_language_choice", count=len(available_languages)))
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(available_languages):
                    lang = available_languages[choice_idx]
                    config['language'] = lang
                    save_config(config)
                    break
                else:
                    print(Fore.RED + i18n.t("invalid_selection"))
            except ValueError:
                print(Fore.RED + i18n.t("invalid_input_number"))

    if not i18n.init_translation(lang):
        input(i18n.t("press_enter_to_exit"))
        return
    # -------------------------------

    print(Fore.MAGENTA + Style.BRIGHT + i18n.t("app_title"))
    print(Fore.WHITE + i18n.t("separator"))

    mapping = {int(k): v for k, v in config.get('note_mapping', {}).items()}
    verbose = config.get('verbose', True)

    port_name = select_midi_port(config.get('device_name_filter', ''))

    if not port_name:
        input(i18n.t("press_enter_to_exit"))
        return

    print(Fore.GREEN + f"\n" + i18n.t("connected_to", port_name=port_name))
    print(Fore.WHITE + i18n.t("press_ctrl_c_to_stop"))
    print(Fore.WHITE + i18n.t("separator"))
    print(Fore.GREEN + i18n.t("ready_to_receive"))

    try:
        # Open the MIDI port for INPUT
        with mido.open_input(port_name) as inport:
            for msg in inport:
                # Check for Note On messages with velocity > 0
                if msg.type == 'note_on' and msg.velocity > 0:
                    if msg.note in mapping:
                        key = mapping[msg.note]
                        try:
                            # Simulate key press
                            keyboard.press_and_release(key)
                            if verbose:
                                print(Fore.GREEN + i18n.t("received_note", note=msg.note, key=key.upper()))
                        except ValueError as e:
                            print(Fore.RED + i18n.t("error_pressing_key", key=key.upper(), error=e))
                    else:
                        if verbose:
                            print(Fore.RED + i18n.t("unmapped_note", note=msg.note))

    except (EOFError, KeyboardInterrupt):
        print(Fore.YELLOW + "\n" + i18n.t("program_stopped"))
    except Exception as e:
        print(Fore.RED + i18n.t("error_occurred", error=e))
        input(i18n.t("press_enter_to_exit"))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Global crash handler
        with open("WWM-Midi-Bridge-logs.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now()}] CRITICAL CRASH: {e}\n")
            f.write(traceback.format_exc())

        print(Fore.RED + "\n!!! CRITICAL ERROR !!!")
        print(Fore.RED + f"Error: {e}")
        print(Fore.RED + "Details saved to 'WWM-Midi-Bridge-logs.txt'")
        input("Press Enter to exit...")
