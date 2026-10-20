"""
Hot reload module for development - watches for file changes and triggers app restart.
"""
import os
import sys
import threading
import time
from pathlib import Path
from typing import Optional, Callable

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    # Define a dummy class to prevent NameError if watchdog is not installed
    class FileSystemEventHandler:
        pass


class FileChangeHandler(FileSystemEventHandler):
    """Detects file changes and triggers a callback."""
    
    def __init__(self, callback: Callable, ignore_patterns: Optional[list] = None):
        """
        Initialize the file change handler.
        
        Args:
            callback: Function to call when a Python file changes
            ignore_patterns: List of patterns to ignore (e.g., ['__pycache__', '.pyc'])
        """
        self.callback = callback
        self.ignore_patterns = ignore_patterns or [
            '__pycache__', '.pyc', '.pyo', '.db', '.log',
            'node_modules', '.git', '.venv', 'venv', '.pytest_cache'
        ]
        self.debounce_time = 0.5
        self.last_modified = 0
    
    def should_ignore(self, path: str) -> bool:
        """Check if path should be ignored."""
        for pattern in self.ignore_patterns:
            if pattern in path:
                return True
        return False
    
    def on_modified(self, event):
        """Handle file modification."""
        if event.is_directory:
            return
        
        if self.should_ignore(event.src_path):
            return
        
        if not event.src_path.endswith('.py'):
            return
            
        # Ignore hidden files (e.g. IDE temporary files like .#config.py)
        import os
        if os.path.basename(event.src_path).startswith('.'):
            return
        
        # Debounce rapid changes
        now = time.time()
        if now - self.last_modified < self.debounce_time:
            return
        
        self.last_modified = now
        print(f"\n🔄 Detected change in: {event.src_path}")
        print("🔄 Reloading application...")
        self.callback()


class HotReloadWatcher:
    """Monitors a directory for changes and triggers hot reload."""
    
    def __init__(self, watch_dir: str, enable: bool = True):
        """
        Initialize the hot reload watcher.
        
        Args:
            watch_dir: Directory to watch for changes
            enable: Whether hot reload is enabled
        """
        self.watch_dir = watch_dir
        self.enable = enable and WATCHDOG_AVAILABLE
        self.observer: Optional[Observer] = None
        self.thread: Optional[threading.Thread] = None
    
    def start(self, callback: Callable):
        """
        Start watching for file changes.
        
        Args:
            callback: Function to call when files change
        """
        if not self.enable:
            return
        
        try:
            handler = FileChangeHandler(callback)
            self.observer = Observer()
            self.observer.schedule(handler, self.watch_dir, recursive=True)
            self.observer.start()
            print(f"✅ Hot reload enabled - watching: {self.watch_dir}")
        except Exception as e:
            print(f"⚠️  Hot reload setup failed: {e}")
            self.enable = False
    
    def stop(self):
        """Stop watching for changes."""
        if self.observer:
            self.observer.stop()
            self.observer.join()


def trigger_hot_reload():
    """Exit the application with code 1000 to trigger a restart."""
    print("🔄 Exiting for hot reload...")
    app = QApplication.instance()
    if app is not None:
        QTimer.singleShot(0, app, lambda: app.exit(1000))
    else:
        sys.exit(1000)
