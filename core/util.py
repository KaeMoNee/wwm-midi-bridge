import os
import sys


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)

    base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)