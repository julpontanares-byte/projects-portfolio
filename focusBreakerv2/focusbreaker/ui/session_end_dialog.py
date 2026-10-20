from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QFrame, QWidget, QSpinBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from focusbreaker.config import Colors, UIConfig, Palette
from focusbreaker.core.timer import fmt_time


class SessionEndDialog(QDialog):
    """
    Session Summary / Completion dialog (B1)
    Shown when normal-mode session completes.
    User can choose to extend or end session.
    """
    action_taken = Signal(str, int)  # ("end" or "extend", additional_minutes if extend)
    
    def __init__(self, session, elapsed_time: int = 0, breaks_taken: int = 0, 
                 breaks_skipped: int = 0, streak_count: int = 0, can_extend=True, parent=None):
        super().__init__(parent)
        self.session = session
        self.elapsed_time = elapsed_time  # in seconds
        self.breaks_taken = breaks_taken
        self.breaks_skipped = breaks_skipped
        self.streak_count = streak_count
        self.can_extend = can_extend
        self.action = 'end'
        self.extend_mins = 0
        
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setModal(True)
        self.setFixedSize(500, 450)
        self._center()
        self._setup_ui()
    
    def _center(self):
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def _setup_ui(self):
        """Build dialog UI (B1)"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Palette.SURFACE_DEFAULT};
            }}
            QFrame#summary {{
                background-color: {Palette.SURFACE_WHITE};
                border-radius: 12px;
                padding: 20px;
            }}
            QPushButton {{
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
                border: none;
            }}
            QPushButton#extend {{
                background-color: {Palette.BRAND_PRIMARY};
                color: white;
            }}
            QPushButton#extend:hover {{
                background-color: {Palette.BRAND_SECONDARY};
            }}
            QPushButton#end {{
                background-color: {Palette.SURFACE_DARK};
                color: {Palette.TEXT_PRIMARY};
            }}
            QPushButton#end:hover {{
                background-color: #FF5F57;
                color: white;
            }}
        """)
        
        # Title (B1)
        title = QLabel("Session Complete! 🎉")
        title.setFont(QFont("Syne", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Summary card (B1)
        summary_frame = QFrame()
        summary_frame.setObjectName("summary")
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setSpacing(12)
        
        task_lbl = QLabel(f"📌 <b>{self.session.task_name}</b>")
        task_lbl.setFont(QFont("Syne", 12, QFont.Weight.Bold))
        summary_layout.addWidget(task_lbl)
        
        if self.elapsed_time > 0:
            elapsed_lbl = QLabel(f"⏱ Worked: {fmt_time(self.elapsed_time)}")
            summary_layout.addWidget(elapsed_lbl)
        
        breaks_lbl = QLabel(f"☕ Breaks: {self.breaks_taken} taken, {self.breaks_skipped} skipped")
        summary_layout.addWidget(breaks_lbl)
        
        streak_lbl = QLabel(f"🔥 Streak: {self.streak_count} day(s)")
        streak_lbl.setStyleSheet(f"color: {Palette.BRAND_SECONDARY};")
        summary_layout.addWidget(streak_lbl)
        
        layout.addWidget(summary_frame)
        
        # Extend option (B1)
        if self.can_extend:
            extend_frame = QFrame()
            extend_frame.setObjectName("summary")
            extend_layout = QHBoxLayout(extend_frame)
            extend_layout.setContentsMargins(0, 0, 0, 0)
            extend_layout.setSpacing(12)
            
            extend_label = QLabel("Extend session by (minutes):")
            extend_layout.addWidget(extend_label)
            
            self.extend_spinbox = QSpinBox()
            self.extend_spinbox.setMinimum(1)
            self.extend_spinbox.setMaximum(120)
            self.extend_spinbox.setValue(15)
            self.extend_spinbox.setMinimumWidth(80)
            self.extend_spinbox.setStyleSheet("""
                QSpinBox {
                    padding: 6px;
                    border: 1px solid #ccc;
                    border-radius: 6px;
                }
            """)
            extend_layout.addWidget(self.extend_spinbox)
            extend_layout.addStretch()
            
            layout.addWidget(extend_frame)
        
        layout.addStretch()
        
        # Buttons (B1)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        end_btn = QPushButton("Done" if not self.can_extend else "End Session")
        end_btn.setObjectName("end")
        end_btn.clicked.connect(self._on_end)
        button_layout.addWidget(end_btn)
        
        if self.can_extend:
            extend_btn = QPushButton("Extend Session")
            extend_btn.setObjectName("extend")
            extend_btn.clicked.connect(self._on_extend)
            button_layout.addWidget(extend_btn)
        
        layout.addLayout(button_layout)
    
    def _on_end(self):
        """User chose to end session (B1)"""
        self.action = 'end'
        self.extend_mins = 0
        self.action_taken.emit("end", 0)
        self.accept()
    
    def _on_extend(self):
        """User chose to extend session (B1)"""
        self.action = 'extend'
        self.extend_mins = self.extend_spinbox.value()
        self.action_taken.emit("extend", self.extend_mins)
        self.accept()
