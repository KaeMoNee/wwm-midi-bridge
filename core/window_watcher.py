from core import logger

try:
    import win32gui
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    logger.log("Warning: win32gui not found. Game focus detection disabled.")


# TODO not used yet, implement it once it works
def is_game_active(target_names):
    """
    Checks if the foreground window title contains any of the target_names.
    Returns True if match found or if win32gui is missing (fail open).
    """
    if not HAS_WIN32:
        return True

    if not target_names:
        return True

    try:
        hwnd = win32gui.GetForegroundWindow()
        window_title = win32gui.GetWindowText(hwnd)

        for name in target_names:
            if name.lower() in window_title.lower():
                return True
        return False
    except Exception as e:
        # If we got an error, then we should just propagate all inputs to be safe
        logger.log(f"Error checking game activity: {e}")
        return True