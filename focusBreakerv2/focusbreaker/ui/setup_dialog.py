from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QWidget, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from focusbreaker.config import Colors, UIConfig

class FirstTimeSetupDialog(QDialog):
    """
    Onboarding - Simplified version.
    Only asks for the user's name before proceeding to main window.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(600, 480)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.container = QFrame(self)
        self.container.setFixedSize(600, 480)
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG};
                border-radius: {UIConfig.RADIUS_LG}px;
            }}
        """)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(60, 80, 60, 60)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.logo_lbl = QLabel()
        logo_pix = QPixmap(UIConfig.LOGO_PATH)
        if not logo_pix.isNull():
            self.logo_lbl.setPixmap(logo_pix.scaledToWidth(140, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(self.logo_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(32)
        
        self.tagline = QLabel("Find your focus rhythm. What should we call you?")
        self.tagline.setWordWrap(True)
        self.tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tagline.setStyleSheet(f"font-family: 'Plus Jakarta Sans'; font-size: 14px; font-weight: 500; color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(self.tagline)

        layout.addSpacing(24)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name")
        self.name_input.setFixedSize(280, 44)
        self.name_input.setStyleSheet(f"""
            QLineEdit {{ 
                background: {Colors.SURFACE}; 
                border: 1px solid {Colors.BORDER}; 
                border-radius: 6px; 
                padding: 0 16px;
                font-family: 'Plus Jakarta Sans';
                font-size: 14px;
                color: {Colors.TEXT};
            }}
            QLineEdit:focus {{ border-color: {Colors.PRIMARY}; }}
        """)
        self.name_input.textChanged.connect(self._validate)
        layout.addWidget(self.name_input, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(32)

        self.start_btn = QPushButton("GET STARTED")
        self.start_btn.setFixedSize(280, 44)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: white;
                border-radius: 22px;
                font-weight: 700;
                font-size: 13px;
            }}
            QPushButton:disabled {{
                background-color: {Colors.TEXT_MUTED};
            }}
        """)
        self.start_btn.clicked.connect(self.accept)
        layout.addWidget(self.start_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def _validate(self):
        self.start_btn.setEnabled(len(self.name_input.text().strip()) > 0)

    def get_username(self) -> str:
        return self.name_input.text().strip() or "User"
