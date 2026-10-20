from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QStyle
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QObject, Signal
import os
from focusbreaker.config import Colors, UIConfig, APP_NAME

class SystemTrayManager(QObject):
    """
    Handles the system tray icon, context menu, and desktop notifications.
    """
    show_window_requested = Signal()
    new_task_requested = Signal()
    settings_requested = Signal()
    quit_requested = Signal()
    end_session_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tray_icon = QSystemTrayIcon(parent)
        self._session_active = False
        
        # Consistent branding: Use UIConfig.LOGO_PATH for tray
        if os.path.exists(UIConfig.LOGO_PATH):
            self.tray_icon.setIcon(QIcon(UIConfig.LOGO_PATH))
        elif parent and parent.style():
            # Fallback to a standard system icon
            self.tray_icon.setIcon(parent.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))

        self.tray_icon.setToolTip(APP_NAME)
        self._setup_menu()
        self.tray_icon.activated.connect(self._on_activated)

    def _setup_menu(self):
        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Colors.SURFACE};
                color: {Colors.TEXT};
                border: 1px solid {Colors.BORDER};
                padding: 4px;
                border-radius: 8px;
            }}
            QMenu::item {{
                padding: 10px 32px;
                border-radius: 4px;
                font-weight: 500;
            }}
            QMenu::item:selected {{
                background-color: {Colors.NORMAL_DIM};
                color: {Colors.PRIMARY};
            }}
            QMenu::item:disabled {{
                color: rgba(255, 255, 255, 0.3);
            }}
        """)

        if self._session_active:
            # Active session menu
            view_session_action = QAction("👀 View Active Session", self)
            view_session_action.triggered.connect(self.show_window_requested.emit)
            menu.addAction(view_session_action)

            end_session_action = QAction("⏹ End Session", self)
            end_session_action.triggered.connect(self.end_session_requested.emit)
            menu.addAction(end_session_action)
        else:
            # No session menu
            dashboard_action = QAction("📋 Dashboard", self)
            dashboard_action.triggered.connect(self.show_window_requested.emit)
            menu.addAction(dashboard_action)

            new_task_action = QAction("➕ New Session", self)
            new_task_action.setToolTip("Start a new work session")
            new_task_action.triggered.connect(self.new_task_requested.emit)
            menu.addAction(new_task_action)

        settings_action = QAction("⚙️ Settings", self)
        settings_action.triggered.connect(self.settings_requested.emit)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction(f"❌ Exit {APP_NAME}", self)
        if self._session_active:
            quit_action.setEnabled(False)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)

    def update_session_state(self, is_active: bool):
        """Update tray menu based on session state."""
        if self._session_active != is_active:
            self._session_active = is_active
            self._setup_menu()

    def show(self):
        self.tray_icon.show()

    def notify(self, title, message, duration_ms=5000):
        """Displays a system tray notification."""
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, duration_ms)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window_requested.emit()
