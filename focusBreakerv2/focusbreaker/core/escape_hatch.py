import time
import logging
from PySide6.QtCore import QObject, Signal, QTimer

logger = logging.getLogger(__name__)

# Lazy-load keyboard to avoid hanging on import
_keyboard = None

def _get_keyboard():
    """Lazy-load keyboard module on first use."""
    global _keyboard
    if _keyboard is None:
        try:
            import keyboard
            _keyboard = keyboard
        except ImportError:
            logger.error("keyboard module not installed")
            return None
    return _keyboard

class EscapeHatch(QObject):
    """
    Handles the emergency escape hatch logic.
    Detects a global hotkey (default: Ctrl+Alt+Shift+E) held for a specified duration.
    """
    progress = Signal(float)  # 0.0 to 1.0
    triggered = Signal()
    cancelled = Signal()

    def __init__(self, combo: str = "ctrl+alt+shift+e", hold_duration: float = 3.0, parent=None):
        super().__init__(parent)
        self.combo = combo
        self.hold_duration = hold_duration
        self._is_pressed = False
        self._start_time = 0.0
        
        self._check_timer = QTimer(self)
        self._check_timer.setInterval(100)  # Check every 100ms
        self._check_timer.timeout.connect(self._check_state)

    def start_listening(self):
        """Starts monitoring the keyboard for the escape combo."""
        # Note: We use polling via QTimer instead of keyboard.on_press to 
        # accurately track 'held' duration across systems.
        self._check_timer.start()

    def stop_listening(self):
        """Stops monitoring."""
        self._check_timer.stop()
        self._reset_state()

    def _check_state(self):
        try:
            keyboard = _get_keyboard()
            if keyboard is None:
                logger.warning("keyboard module not available, escape hatch disabled")
                self.stop_listening()
                return
            
            now = time.time()
            if keyboard.is_pressed(self.combo):
                if not self._is_pressed:
                    self._is_pressed = True
                    self._start_time = now

                elapsed = now - self._start_time
                progress_val = min(1.0, elapsed / self.hold_duration)
                self.progress.emit(progress_val)

                if elapsed >= self.hold_duration:
                    self.triggered.emit()
                    self._reset_state()
            else:
                if self._is_pressed:
                    self._reset_state()
                    self.cancelled.emit()
        except OSError as e:
            logger.warning(f"Keyboard hook failed or requires elevated permissions: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in escape hatch key detection: {e}")

    def _reset_state(self):
        self._is_pressed = False
        self._start_time = 0.0
        self.progress.emit(0.0)