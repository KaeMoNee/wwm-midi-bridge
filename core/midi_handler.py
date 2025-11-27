import threading
import weakref

import keyboard
import mido

from core import logger, config, i18n


def get_ports():
    return mido.get_input_names()


def _handle_note(note, mapping, verbose):
    if note in mapping:
        key = mapping[note]
        try:
            keyboard.press_and_release(key)
            if verbose:
                # For UI log, we can just send the string
                logger.log(i18n.t("bridge.received_note", note=note, key=key.upper()))
        except ValueError as e:
            logger.log(i18n.t("bridge.error_pressing_key", key=key.upper(), error=e))
    else:
        if verbose:
            logger.log(i18n.t("bridge.unmapped_note", note=note))


class MidiHandler:
    def __init__(self):
        self.is_running = False
        self.midi_thread = None
        self._stop_event = threading.Event()
        self._listeners = weakref.WeakSet()

    def stop(self):
        if self.is_running:
            self._stop_event.set()
            self.is_running = False
            logger.log(i18n.t("bridge.stopped"))

    def start(self, device_name: str) -> bool:
        if self.is_running:
            return False

        self._stop_event.clear()
        self.is_running = True
        self.midi_thread = threading.Thread(target=self.listen, args=(device_name,), daemon=True)
        self.midi_thread.start()
        return True

    def listen(self, port_name: str):
        mapping = {int(k): v for k, v in config.get_note_mapping().items()}
        verbose = config.get_verbose()

        logger.log(i18n.t("bridge.connecting"))

        try:
            with mido.open_input(port_name) as inport:
                logger.log(i18n.t("bridge.connected", device=port_name))

                while not self._stop_event.is_set():
                    # Poll for messages instead of blocking iteration to allow clean exit
                    for msg in inport.iter_pending():
                        if self._stop_event.is_set():
                            break
                        if msg.type == 'note_on' and msg.velocity > 0:
                            _handle_note(msg.note, mapping, verbose)
                        self._notify_listeners(msg)
                    # Small sleep to prevent high CPU usage in polling loop
                    if self._stop_event.wait(0.001):
                        break
        except OSError as e:
            logger.log(i18n.t("error_occurred", error=f"Device error: {e}"))
            self.stop()
        except Exception as e:
            logger.log(i18n.t("error_occurred", error=e))
            self.stop()
        finally:
            # Ensure flag is reset if thread crashes
            self.is_running = False

    def add_listener(self, listener):
        self._listeners.add(listener)

    def _notify_listeners(self, msg):
        # WeakSet automatically cleans up dead references
        for listener in self._listeners:
            try:
                if hasattr(listener, 'on_midi_input'):
                    listener.on_midi_input(msg)
            except Exception as e:
                print(f"Error in listener: {e}")