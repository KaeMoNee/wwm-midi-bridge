import sys
import threading


class Logger:
    def __init__(self):
        self.target = None
        self.lock = threading.Lock()
        self._buffer = []
        self._max_buffer_size = 100  # Keep the last 100 messages if UI isn't ready

    def set_target(self, target):
        """Sets the UI target (Text widget) and flushes buffered logs."""
        with self.lock:
            self.target = target
            if self.target and self._buffer:
                for msg in self._buffer:
                    self._write_to_target(msg)
                self._buffer.clear()

    def log(self, msg):
        """Logs a message to the console and the UI target if available."""
        # Always mirror to console for debugging
        print(msg)

        with self.lock:
            if self.target is None:
                # Buffer early messages (e.g. startup logs)
                if len(self._buffer) < self._max_buffer_size:
                    self._buffer.append(msg)
                return

            self._write_to_target(msg)

    def _write_to_target(self, msg):
        """Helper to safely write to the UI widget."""
        try:
            self.target.configure(state="normal")
            self.target.insert("end", str(msg) + "\n")
            self.target.see("end")
            self.target.configure(state="disabled")
        except Exception as e:
            # Don't crash if the UI widget is gone or invalid
            print(f"Error updating UI logger: {e}", file=sys.stderr)


_logger = Logger()


def log(msg):
    _logger.log(msg)


def set_target(target):
    _logger.set_target(target)