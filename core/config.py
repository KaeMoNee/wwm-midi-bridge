import json
import os
import threading

from core import logger, i18n

CONFIG_FILE = 'config.json'
REPO_URL = "https://github.com/KaeMoNee/wwm-midi-bridge"
REPO_RELEASE_CHECK_URL = "https://api.github.com/repos/KaeMoNee/wwm-midi-bridge/releases/latest"
VERSION = "1.0.0"

class Config:
    def __init__(self):
        self.lock = threading.Lock()
        # Initialize with defaults
        self._data = {
            'device_name_filter': None,
            'verbose': False,
            'language': 'en',
            'note_mapping': {}
        }

    def load_config(self) -> None:
        if not os.path.exists(CONFIG_FILE):
            default_config = {
                "device_name_filter": None,
                "verbose": False,
                "language": "en",
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
            self._data.update(default_config)
            self.save_config()
            return

        with self.lock:
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    if isinstance(loaded_data, dict):
                        # Merge loaded data into defaults, preserving existing keys
                        self._data.update(loaded_data)
            except (json.JSONDecodeError, OSError) as e:
                logger.log(i18n.t("config.error.loading", error=e))

        logger.log(i18n.t("config.loaded"))

    def save_config(self):
        with self.lock:
            try:
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self._data, f, indent=4, ensure_ascii=False)
                logger.log(i18n.t("config.saved"))
            except Exception as e:
                logger.log(i18n.t("config.error.saving", error=e))

    def _get(self, key, default=None):
        with self.lock:
            return self._data.get(key, default)

    def _set(self, key, value):
        with self.lock:
            self._data[key] = value
        self.save_config()

    @property
    def device_name_filter(self) -> str | None:
        return self._get('device_name_filter')

    @device_name_filter.setter
    def device_name_filter(self, value):
        self._set('device_name_filter', value)

    @property
    def verbose(self) -> bool:
        return self._get('verbose', False)

    @verbose.setter
    def verbose(self, value):
        self._set('verbose', value)

    @property
    def language(self) -> str:
        return self._get('language', 'en')

    @language.setter
    def language(self, value):
        self._set('language', value)

    @property
    def note_mapping(self) -> dict:
        return self._get('note_mapping', {})


# Singleton instance
_config = Config()


def load_config() -> None:
    _config.load_config()


def save_config() -> None:
    _config.save_config()


def get_language() -> str:
    return _config.language


def set_language(language) -> None:
    _config.language = language


def get_verbose() -> bool:
    return _config.verbose


def set_verbose(verbose) -> None:
    _config.verbose = verbose


def get_device_name_filter() -> str | None:
    return _config.device_name_filter


def set_device_name_filter(device_name_filter) -> None:
    _config.device_name_filter = device_name_filter


def get_note_mapping() -> dict:
    return _config.note_mapping
