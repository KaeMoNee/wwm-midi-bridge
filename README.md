# Midi-Bridge

**Midi-Bridge** allows you to play musical instruments in the game *Where Winds Meet* (and other games) using your
real MIDI Keyboard.

The script intercepts MIDI signals and simulates PC keyboard presses mapped to specific notes.

## ⚠️ Disclaimer

Use at your own risk. While this script only maps keys for musical purposes, using automated scripts in online games can
sometimes be flagged by anti-cheat software. Recommended for use only in "Guqin" mode.

It is a grey area, so use it at your own risk. The chance of banning your account is very slim, almost 0. It is against
ToS to use a third party program, but our keyboard, mouse and other peripherals are using them all the time. They can't
ban everyone, so only once the program exceeds the "allowed" part, they will start the ban wave. We will try to keep
this script as clean and simple as possible to avoid this situation and be only a bridge between your MIDI keyboard and
your game.

## License & Usage

This project is open-source software licensed under the GPL-3.0 license.

**You can:** Use this app, modify it, fork it, study the code, share it with friends.

**You can:** Use it in your own projects, IF your project is also open-source (GPLv3).

**You cannot:** Copy this code into closed-source or proprietary software without permission.

## Features

- **Low Latency:** Uses `mido` and `python-rtmidi` for fast response.
- **Configurable:** Map any MIDI note to any keyboard key via `config.json`.
- **Graphic User Interface**
- **MIDI Player**
- **Manual MIDI Player**

## Installation

1. **Install Python** (3.8 or higher).
2. **Clone this repository** or download the ZIP.
   ```bash
   git clone https://github.com/KaeMoNee/wwm-midi-bridge.git
   cd wwm-midi-bridge
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## How to Use

1. Connect your MIDI Keyboard to your PC.
2. Edit `config.json` to match your game keybinds (see Configuration below). Or use a default file which is generated on
   the first run.
3. **Run the script as Administrator** (Important! Games often block non-admin input).
   ```bash
   python main.py
   ```
4. Select your MIDI device from the list (or set it in config for auto-connect).
5. Focus the game window and play!

## Configuration (`config.json`)

- **device_name_filter**: Part of your MIDI device name (e.g., "Yamaha"). If empty, the script asks you to choose on
  startup.
- **note_mapping**: Dictionary where `Key` is the MIDI Note Number and `Value` is the PC Keyboard key.
    - *Tip:* Middle C is usually note 60.

Example:

```json
{
  "note_mapping": {
    "60": "q",
    "62": "w",
    "64": "e"
  }
}
```
