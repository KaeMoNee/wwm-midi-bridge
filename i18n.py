import json
import os
import sys


class Translator:
    def __init__(self, locales_dir="locales", default_lang="en"):
        if hasattr(sys, '_MEIPASS'):
            self.locales_dir = os.path.join(sys._MEIPASS, locales_dir)
        else:
            self.locales_dir = locales_dir

        self.translations = {}
        self.language = default_lang
        self.load_language(self.language)

    def load_language(self, lang_code):
        file_path = os.path.join(self.locales_dir, f"{lang_code}.json")
        if not os.path.exists(file_path):
            print(f"Language file not found for '{lang_code}', falling back to default.")
            file_path = os.path.join(self.locales_dir, f"{self.language}.json")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            self.language = lang_code
            return True
        except Exception as e:
            print(f"Error loading language {lang_code}: {e}")
            return False

    def t(self, _msg_id, **kwargs):
        """Get translated string by key, with optional format arguments"""
        text = self.translations.get(_msg_id, _msg_id)
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError) as e:
            print(f"Warning: Could not format translation for key '{_msg_id}': {e}")
            return text


# Singleton instance
_translator = Translator()


def init_translation(lang_code):
    return _translator.load_language(lang_code)


def t(_msg_id, **kwargs):
    return _translator.t(_msg_id, **kwargs)


def get_available_languages(locales_dir="locales"):
    if hasattr(sys, '_MEIPASS'):
        locales_dir = os.path.join(sys._MEIPASS, locales_dir)

    if not os.path.isdir(locales_dir):
        return []

    languages = []
    for filename in os.listdir(locales_dir):
        if filename.endswith(".json"):
            languages.append(os.path.splitext(filename)[0])
    return languages
