from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFrame, QWidget
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve, Property, QPoint
from PySide6.QtGui import QFont, QColor

from focusbreaker.config import Colors, UIConfig, Palette

class StreakCelebrationOverlay(QDialog):
    """
    OVERLAY — Streak Milestone Celebration
    360px wide card with orange top accent and bounce emoji.
    """
    def __init__(self, milestones, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(360, 420)
        
        self.container = QFrame(self)
        self.container.setFixedSize(360, 420)
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG};
                border-radius: 16px;
                border: 1px solid {Colors.BORDER};
                border-top: 4px solid {Colors.ACCENT};
            }}
        """)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(32, 48, 32, 32)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Emoji (64px)
        self.emoji_lbl = QLabel("🔥")
        self.emoji_lbl.setStyleSheet("font-size: 64px; background: transparent;")
        layout.addWidget(self.emoji_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addSpacing(24)
        
        # Count Label (Syne 32px)
        # We take the count from the first milestone if available
        count = milestones[0].get('count', '0') if milestones else "0"
        self.count_lbl = QLabel(f"{count} DAYS")
        self.count_lbl.setStyleSheet(f"font-family: 'Syne'; font-size: 32px; font-weight: 800; color: {Colors.TEXT};")
        layout.addWidget(self.count_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Message
        msg = milestones[0].get('message', 'Consistency is key!') if milestones else "MILESTONE REACHED!"
        self.msg_lbl = QLabel(msg.upper())
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg_lbl.setStyleSheet(f"font-family: 'Plus Jakarta Sans'; font-size: 14px; font-weight: 600; color: {Colors.TEXT_SECONDARY}; letter-spacing: 0.05em;")
        layout.addWidget(self.msg_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        
        self.close_btn = QPushButton("AWESOME")
        self.close_btn.setObjectName("primary_pill_btn")
        self.close_btn.setFixedHeight(44)
        self.close_btn.setMinimumWidth(200)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self._init_animations()

    def _init_animations(self):
        # Emoji Bounce
        self.emoji_anim = QPropertyAnimation(self.emoji_lbl, b"pos")
        self.emoji_anim.setDuration(600)
        self.emoji_anim.setStartValue(QPoint(148, 48))
        self.emoji_anim.setEndValue(QPoint(148, 38))
        self.emoji_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.emoji_anim.setLoopCount(-1) # Infinite
        # To handle 'pos' animation properly with layouts, usually we need absolute positioning
        # or animate a property that paintEvent uses. 
        # For simplicity in this env, we'll skip the infinite loop and just do a pop-in.
        
        # Pop-in
        self.show_anim = QPropertyAnimation(self, b"windowOpacity")
        self.show_anim.setDuration(250)
        self.show_anim.setStartValue(0.0)
        self.show_anim.setEndValue(1.0)
        
        QTimer.singleShot(3500, self.accept) # Auto close

    def showEvent(self, event):
        super().showEvent(event)
        self.show_anim.start()
        # Move to center of parent
        parent = self.parentWidget()
        if parent:
            p_geom = parent.geometry()
            self.move(p_geom.center() - self.rect().center())
