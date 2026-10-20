from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QApplication, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QPropertyAnimation
from focusbreaker.config import Palette

class ThemedConfirmDialog(QDialog):
    """Modern themed confirmation dialog."""
    def __init__(self, title: str, message: str, parent=None, danger: bool = False):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.result_value = False
        
        self.setFixedSize(400, 240)
        # Center on parent
        if parent:
            self.move(parent.geometry().center() - self.rect().center())
            
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        # Modal Shell
        self.container = QFrame()
        self.container.setObjectName("confirm_shell")
        self.container.setStyleSheet(f"QFrame#confirm_shell {{ background-color: {Palette.SURFACE_WHITE}; border-radius: 20px; border: 1.5px solid {Palette.SURFACE_DARK}; }}")
        root.addWidget(self.container)
        
        l = QVBoxLayout(self.container)
        l.setContentsMargins(32, 32, 32, 32)
        l.setSpacing(20)
        
        # Title
        t_lbl = QLabel(title.upper())
        t_lbl.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {Palette.TEXT_MUTED}; letter-spacing: 1.5px; border: none;")
        l.addWidget(t_lbl)
        
        # Message
        m_lbl = QLabel(message)
        m_lbl.setWordWrap(True)
        m_lbl.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {Palette.TEXT_PRIMARY}; line-height: 140%; border: none; background: transparent;")
        l.addWidget(m_lbl)
        
        l.addSpacing(10)
        
        # Buttons
        btn_l = QHBoxLayout()
        btn_l.setSpacing(12)
        
        no_btn = QPushButton("Cancel")
        no_btn.setFixedHeight(44)
        no_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        no_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1.5px solid {Palette.SURFACE_DARK};
                border-radius: 22px;
                color: {Palette.TEXT_SECONDARY};
                font-weight: 700;
                font-size: 13px;
                padding: 0 24px;
            }}
            QPushButton:hover {{ background: {Palette.SURFACE_DARK}; }}
        """)
        no_btn.clicked.connect(self.reject)
        btn_l.addWidget(no_btn)
        
        yes_btn = QPushButton("Confirm")
        yes_btn.setFixedHeight(44)
        yes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_color = "#FF5F57" if danger else Palette.BRAND_PRIMARY
        hover_color = "#E53935" if danger else Palette.BRAND_SECONDARY
        
        yes_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {confirm_color};
                border: none;
                border-radius: 22px;
                color: white;
                font-weight: 800;
                font-size: 13px;
                padding: 0 32px;
            }}
            QPushButton:hover {{ background-color: {hover_color}; }}
        """)
        yes_btn.clicked.connect(self.accept)
        btn_l.addWidget(yes_btn)
        
        l.addLayout(btn_l)

    def accept(self):
        self.result_value = True
        super().accept()

    def reject(self):
        self.result_value = False
        super().reject()

class ThemedMessageDialog(QDialog):
    """Simple themed message/alert dialog."""
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        
        # Geometry logic: Cover the active visible context
        from PySide6.QtWidgets import QApplication
        target = parent
        if not target or not target.isVisible():
            target = QApplication.activeWindow()
            
        if target and target.isVisible():
            self.resize(target.size())
            self.move(target.mapToGlobal(target.rect().topLeft()))
        else:
            screen = QApplication.primaryScreen().geometry()
            self.resize(screen.size())
            self.move(screen.topLeft())
        
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.backdrop = QFrame()
        self.backdrop.setObjectName("msg_backdrop")
        self.backdrop.setStyleSheet(f"QFrame#msg_backdrop {{ background-color: rgba(0, 0, 0, 0.4); border-radius: 24px; border: none; }}")
        root.addWidget(self.backdrop)
        
        container_l = QVBoxLayout(self.backdrop)
        container_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_l.setContentsMargins(0, 0, 0, 0)
        
        self.container = QFrame()
        self.container.setObjectName("msg_shell")
        self.container.setFixedWidth(360)
        self.container.setStyleSheet(f"QFrame#msg_shell {{ background-color: {Palette.SURFACE_WHITE}; border-radius: 20px; border: 1px solid {Palette.SURFACE_DARK}; }}")
        container_l.addWidget(self.container)
        
        l = QVBoxLayout(self.container)
        l.setContentsMargins(32, 32, 32, 32)
        l.setSpacing(16)
        
        header = QHBoxLayout()
        # Polished CSS-drawn italicized info icon
        info = QLabel("i")
        info.setObjectName("info_icon_btn")
        info.setFixedSize(18, 18)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(info)
        
        t_lbl = QLabel(title.upper())
        t_lbl.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {Palette.BRAND_PRIMARY}; letter-spacing: 2px; border: none;")
        header.addWidget(t_lbl)
        header.addStretch()
        l.addLayout(header)
        
        m_lbl = QLabel(message)
        m_lbl.setWordWrap(True)
        m_lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {Palette.TEXT_PRIMARY}; border: none; background: transparent;")
        l.addWidget(m_lbl)
        
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        
        btn = QPushButton("Got it")
        btn.setFixedHeight(44)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Palette.BRAND_PRIMARY};
                border: none;
                border-radius: 22px;
                color: white;
                font-weight: 800;
                font-size: 13px;
                padding: 0 32px;
            }}
            QPushButton:hover {{ background-color: {Palette.BRAND_SECONDARY}; }}
        """)
        btn.clicked.connect(self.accept)
        btn_box.addWidget(btn)
        btn_box.addStretch()
        l.addLayout(btn_box)
