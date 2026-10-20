from typing import List, Optional

# Lazy-load keyboard to avoid Windows import hang
_keyboard = None

def _get_keyboard():
    """Lazy-load keyboard module."""
    global _keyboard
    if _keyboard is None:
        import keyboard
        _keyboard = keyboard
    return _keyboard

class InputBlocker:
    """
    Blocks keyboard input during Strict and Focused mode breaks.
    Allows the emergency escape hatch combination to pass through.
    """
    def __init__(self, escape_combo: str = "ctrl+alt+shift+e"):
        self.escape_combo = escape_combo.lower()
        self._is_blocking = False
        self._hooked = False

    def start_blocking(self):
        """
        Starts blocking all keys globally, except for the keys 
        required for the escape hatch.
        """
        if self._is_blocking:
            return
            
        # We use a global hook to suppress all keys.
        # Note: This is a powerful feature and requires appropriate permissions.
        keyboard = _get_keyboard()
        keyboard.hook(self._handle_key_event, suppress=True)
        self._is_blocking = True
        self._hooked = True

    def stop_blocking(self):
        """Stops blocking keys."""
        if self._hooked:
            keyboard = _get_keyboard()
            keyboard.unhook(self._handle_key_event)
            self._hooked = False
        self._is_blocking = False

    def _handle_key_event(self, event):
        """
        Callback for every key event. Returns True to suppress, False to allow.
        """
        # We need to allow keys that are part of the escape combo.
        # This is a simplification; a more robust version would check 
        # if the keys being pressed are strictly part of the combo.
        parts = self.escape_combo.split('+')
        if event.name.lower() in parts:
            return False # Allow these keys
        
        return True # Suppress everything else