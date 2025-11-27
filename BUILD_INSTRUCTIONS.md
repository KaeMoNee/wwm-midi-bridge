# Building for Windows

This project uses PyInstaller to create a standalone Windows executable (.exe).

## Prerequisites

1.  Ensure you have Python installed.
2.  Install the project requirements from the project root directory:
    ```bash
    pip install -r requirements.txt
    ```

## Building the Executable

Run the following command in your terminal from the project root directory. This command tells PyInstaller to include the `locales` folder, requests Admin rights, names the file "WWM-Midi-Bridge", and **fixes the missing MIDI backend error**.

```shell
pyinstaller --noconfirm --onefile --console --uac-admin --icon="assets/icon.ico" --add-data "assets/icon.ico;assets" --name "WWM-Midi-Bridge" --hidden-import="mido.backends.rtmidi" --add-data "locales;locales" main.py
```


### Explanation of flags:

*   `--hidden-import="mido.backends.rtmidi"`: **Crucial Fix.** Explicitly bundles the `rtmidi` backend for `mido`. Without this, the compiled app crashes because it can't find the MIDI driver.
*   `--name "WWM-Midi-Bridge"`: Sets the name of the output file to `WWM-Midi-Bridge.exe`.
*   `--uac-admin`: **Important.** Forces the executable to request Administrator privileges (User Account Control) when launched. This is required for the script to simulate key presses in games that run as Admin.
*   `--noconfirm`: Replace output directory without asking for confirmation.
*   `--onefile`: Bundle everything into a single `.exe` file for easy distribution.
*   `--console`: The application will open with a console window. This is necessary for our text-based UI.
*   `--add-data "locales;locales"`: This is the crucial part for internationalization. It copies the `locales` directory and all its contents into the build, ensuring the .json language files are available to the executable at runtime. The syntax is `source;destination_in_bundle`.
*   `--icon="assets/icon.ico"`: Sets the application icon.

## Output

After the build completes successfully:

1.  A `dist` folder will be created in your project directory.
2.  Inside `dist`, you will find `WWM-Midi-Bridge.exe`.
3.  You can run this .exe file on any Windows machine to use the application. The first time it runs, it will ask for a language preference.