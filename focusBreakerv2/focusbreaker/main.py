import sys
import os
import logging
from logging import INFO, FileHandler, StreamHandler

print("[DEBUG] Starting imports...", flush=True)

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("[DEBUG] Importing PySide6...", flush=True)
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QPalette, QColor, QIcon, QFontDatabase
from PySide6.QtCore import Qt, QTimer

print("[DEBUG] Importing focusbreaker modules...", flush=True)
print("[DEBUG] - Importing DBManager...", flush=True)
from focusbreaker.data.db import DBManager
print("[DEBUG] - Importing MainWindow...", flush=True)
from focusbreaker.ui.main_window import MainWindow
print("[DEBUG] - Importing SplashScreen...", flush=True)
from focusbreaker.ui.splash_screen import SplashScreen
print("[DEBUG] - Importing FirstTimeSetupDialog...", flush=True)
from focusbreaker.ui.setup_dialog import FirstTimeSetupDialog
print("[DEBUG] - Importing config...", flush=True)
from focusbreaker.config import Colors, AppPaths
print("[DEBUG] - Importing hot_reload...", flush=True)
from focusbreaker.core.hot_reload import HotReloadWatcher, trigger_hot_reload
print("[DEBUG] All imports complete!", flush=True)


def ensure_directories():
    """Ensure all required asset and log directories exist."""
    dirs = [
        "logs",
        "focusbreaker/assets/media/normal/defaults",
        "focusbreaker/assets/media/normal/user",
        "focusbreaker/assets/media/strict/defaults",
        "focusbreaker/assets/media/strict/user",
        "focusbreaker/assets/media/focused/defaults",
        "focusbreaker/assets/media/focused/user",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    # Check for critical sound asset, warn if missing
    alarm_path = "focusbreaker/assets/media/alarm.wav"
    if not os.path.exists(alarm_path):
        import logging
        logging.getLogger("FocusBreaker").warning(f"Default alarm sound missing: {alarm_path}. The app will remain silent during break endings.")


def init_logging():
    """
    Step 1.2: Logging Initialization.
    All events will be logged to logs/app.log and console.
    """
    logging.basicConfig(
        level=INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            FileHandler('logs/app.log'),
            StreamHandler(sys.stdout)
        ]
    )
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    # Suppress EDID parsing warnings from screen_brightness_control (harmless)
    logging.getLogger('screen_brightness_control.windows').setLevel(logging.ERROR)
    return logging.getLogger("FocusBreaker")


def load_fonts():
    """Load custom fonts from assets/fonts."""
    font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
    if os.path.exists(font_dir):
        for font_file in os.listdir(font_dir):
            if font_file.endswith(".ttf"):
                QFontDatabase.addApplicationFont(os.path.join(font_dir, font_file))


def main():
    print("[DEBUG] main() starting...", flush=True)
    ensure_directories()
    print("[DEBUG] Directories ensured...", flush=True)
    logger = init_logging()
    print("[DEBUG] Logging initialized...", flush=True)
    logger.info("Application starting...")

    print("[DEBUG] Creating QApplication...", flush=True)
    app = QApplication(sys.argv)
    print("[DEBUG] QApplication created!", flush=True)
    hot_reload_watcher: HotReloadWatcher | None = None
    app.setStyle("Fusion") # Fixes many rendering bugs with tooltips on Windows
    app.setApplicationName("focusBreaker")
    app.setApplicationVersion("1.0.0")
    app.setQuitOnLastWindowClosed(False)  # Keep app running in background with tray icon
    
    print("[DEBUG] Loading fonts...", flush=True)
    load_fonts()
    
    print("[DEBUG] Setting up UI styling...", flush=True)
    # Taskbar Logo handling for Windows
    from focusbreaker.config import UIConfig
    if os.path.exists(UIConfig.LOGO_PATH):
        app.setWindowIcon(QIcon(UIConfig.LOGO_PATH))

    # Global Styling
    font = QFont("Plus Jakarta Sans", 10)
    app.setFont(font)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(Colors.BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(Colors.TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor(Colors.SURFACE))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(Colors.SURFACE))
    palette.setColor(QPalette.ColorRole.Text, QColor(Colors.TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor(Colors.SURFACE))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(Colors.TEXT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(Colors.PRIMARY))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    
    # Force Tooltip Colors (Prevents dark system themes from making them unreadable)
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#1E2D2C"))

    app.setPalette(palette)

    # Global Tooltip & UI Styling (Must be on app instance to affect top-level tooltips)
    from focusbreaker.ui.styles import get_stylesheet
    app.setStyleSheet(get_stylesheet())

    print("[DEBUG] Connecting to database...", flush=True)
    db = DBManager()
    db.connect()
    print("[DEBUG] Database connected!", flush=True)

    print("[DEBUG] Creating splash screen...", flush=True)
    # Step 3: Splash Screen
    splash = SplashScreen()
    print("[DEBUG] Showing splash screen...", flush=True)
    splash.show()
    print("[DEBUG] Splash screen shown!", flush=True)
    
    def on_loading_finished():
        nonlocal hot_reload_watcher
        try:
            print("[DEBUG] on_loading_finished() called", flush=True)
            logger.info("Loading finished, preparing main interface...")
            splash.close()
            print("[DEBUG] Splash closed", flush=True)
            
            # Step 6: First Time Setup Check
            if db.is_first_run():
                print("[DEBUG] First run detected, showing setup dialog", flush=True)
                logger.info("First run detected, showing setup dialog.")
                setup = FirstTimeSetupDialog()
                if setup.exec():
                    settings = db.get_settings()
                    settings.username = setup.get_username()
                    db.save_settings(settings)
                    db.complete_first_run()
                    logger.info(f"Setup complete. Username: {settings.username}")
                print("[DEBUG] Setup dialog complete", flush=True)
            
            # Step 7: Show Main Window
            print("[DEBUG] Creating MainWindow...", flush=True)
            window = MainWindow(db)
            
            # Keep a reference to the main window
            global _main_window
            _main_window = window
            
            # Ensure window starts in a normal state and show it
            window.setWindowState(Qt.WindowState.WindowNoState)
            window.show()
            print("[DEBUG] window.show() called", flush=True)
            
            # Force focus and "pop out" behavior
            window.raise_()
            window.activateWindow()
            
            # Extra insurance: ensure it's normal state after showing
            QTimer.singleShot(200, lambda: (
                window.showNormal(),
                window.raise_(),
                window.activateWindow()
            ))
            
            logger.info("Main window displayed.")
            print("[DEBUG] Main window ready", flush=True)
            
            # Step 8: Setup Hot Reload for Development
            # Set DEV_MODE=1 environment variable to enable hot reload
            dev_mode = os.environ.get('DEV_MODE', '').lower() in ('1', 'true', 'yes')
            if dev_mode:
                print("[DEBUG] Hot reload enabled, starting watcher...", flush=True)
                focusbreaker_dir = os.path.dirname(os.path.abspath(__file__))
                hot_reload_watcher = HotReloadWatcher(focusbreaker_dir, enable=True)
                hot_reload_watcher.start(trigger_hot_reload)
                logger.info("Hot reload enabled - changes to .py files will trigger restart")
                print("[DEBUG] Hot reload watcher started", flush=True)
        except Exception as e:
            print(f"[ERROR] Exception in on_loading_finished(): {e}", flush=True)
            import traceback
            traceback.print_exc()
            logger.error(f"Exception in on_loading_finished(): {e}", exc_info=True)
            splash.close()
            app.quit()

    splash.finished.connect(on_loading_finished)
    print("[DEBUG] Connecting splash.finished signal...", flush=True)
    print("[DEBUG] Starting splash loading animation...", flush=True)
    splash.start_loading()

    print("[DEBUG] Starting Qt event loop (app.exec())...", flush=True)
    result = app.exec()
    print("[DEBUG] Event loop finished!", flush=True)
    db.close()
    
    # Exit cleanly. The root launcher will handle code 1000 as a restart.
    logger.info(f"Application exiting with code {result}.")
    sys.exit(result)


if __name__ == "__main__":
    main()