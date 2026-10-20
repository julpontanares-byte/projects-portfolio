from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPixmap

from focusbreaker.config import Colors, UIConfig, APP_VERSION

class SplashScreen(QWidget):
    """
    Step 3.1: Application Splash Screen.
    Displays branding with logo wrapped in a rounded container.
    """
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(450, 420)
        self._setup_ui()
        self._center()

    def _center(self):
        screen = self.screen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 24px;
            }}
            QFrame#logo_container {{
                background-color: transparent;
                border: none;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(48, 48, 48, 48)

        # Logo Container
        self.logo_container = QFrame()
        self.logo_container.setObjectName("logo_container")
        self.logo_container.setFixedSize(300, 200)
        container_layout = QVBoxLayout(self.logo_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        self.logo_lbl = QLabel()
        self.logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        pixmap = QPixmap(UIConfig.LOGO_PATH)
        if not pixmap.isNull():
            self.logo_lbl.setPixmap(pixmap.scaled(280, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            # Fallback text in case logo is missing
            # self.logo_lbl.setText("focusBreaker")
            self.logo_lbl.setStyleSheet(f"font-size: 32px; font-weight: 900; color: {Colors.PRIMARY};")
            
        container_layout.addWidget(self.logo_lbl)
        layout.addWidget(self.logo_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Version
        ver = QLabel(f"Version {APP_VERSION}")
        ver.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {Colors.TEXT_MUTED}; margin-top: 4px;")
        layout.addWidget(ver, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(40)

        # Progress indicator
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setFixedWidth(260)
        self.progress.setStyleSheet(f"""
            QProgressBar {{ background: {Colors.BORDER}; border: none; border-radius: 3px; }}
            QProgressBar::chunk {{ background: {Colors.PRIMARY}; border-radius: 3px; }}
        """)
        layout.addWidget(self.progress, alignment=Qt.AlignmentFlag.AlignCenter)

        self.loading_lbl = QLabel("Initializing components...")
        self.loading_lbl.setStyleSheet(f"font-size: 13px; font-weight: 500; color: {Colors.TEXT_MUTED}; margin-top: 16px;")
        layout.addWidget(self.loading_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

    def start_loading(self):
        steps = ["Initializing Database...", "Checking Assets...", "Loading Work Modes...", "Ready!"]
        self._current_step = 0
        
        def next_step():
            if self._current_step < len(steps):
                self.loading_lbl.setText(steps[self._current_step])
                self._current_step += 1
                QTimer.singleShot(600, next_step)
            else:
                self.finished.emit()

        QTimer.singleShot(500, next_step)
