from PySide6.QtCore import QObject, Signal, QTimer, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QColor, QPalette

# Lazy-load screen_brightness_control to avoid Windows import hang
_sbc = None

def _get_sbc():
    """Lazy-load screen_brightness_control module."""
    global _sbc
    if _sbc is None:
        import screen_brightness_control as sbc
        _sbc = sbc
    return _sbc

class DisplayController(QObject):
    """
    Handles screen brightness and full-screen overlays.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            sbc = _get_sbc()
            brightness = sbc.get_brightness()
            # sbc.get_brightness() returns a list, e.g., [74]
            if isinstance(brightness, list) and len(brightness) > 0:
                self.original_brightness = brightness[0]
            else:
                self.original_brightness = brightness if brightness is not None else 100
        except Exception:
            self.original_brightness = 100
            
        self.brightness_boost = 100

    def boost_brightness(self, level: int = 100):
        """Boosts screen brightness during surprise effects."""
        try:
            sbc = _get_sbc()
            sbc.set_brightness(level)
        except Exception:
            pass

    def restore_brightness(self):
        """Restores original screen brightness."""
        try:
            sbc = _get_sbc()
            # Ensure we pass an int/float, not a list
            val = self.original_brightness
            if isinstance(val, list):
                val = val[0] if len(val) > 0 else 100
            sbc.set_brightness(val)
        except Exception:
            pass

    def show_full_screen_overlay(self, title: str = "FocusBreaker Break", 
                                message: str = "Time to rest.", 
                                mode_color: str = "#2F81F7"):
        """Displays a system-wide full-screen overlay."""
        overlay = OverlayWindow(title, message, mode_color)
        overlay.showFullScreen()
        return overlay

class OverlayWindow(QWidget):
    """
    A full-screen window that blocks interaction with other windows.
    Used for Strict and Focused mode breaks.
    """
    def __init__(self, title: str, message: str, color: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 240)) # Semi-transparent black
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 48px; font-weight: 700; color: {color};")
        layout.addWidget(title_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet("font-size: 24px; color: #E6EDF3;")
        layout.addWidget(msg_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

    def keyPressEvent(self, event):
        # Prevent closing via Escape or other keys
        event.ignore()

    def closeEvent(self, event):
        # Override to ensure it doesn't close accidentally
        event.accept()
