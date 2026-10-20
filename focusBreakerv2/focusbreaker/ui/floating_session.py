from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, QFrame
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QMouseEvent

from focusbreaker.config import Colors, UIConfig
from focusbreaker.core.timer import fmt_time

class FloatingSessionWindow(QWidget):
    """
    Step 12.4: Floating Session View Window.
    An always-on-top, borderless mini-window to track active sessions.
    Refined with JetBrains Mono and brand styles.
    """
    close_requested = Signal()
    stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(280, 160)
        self._drag_pos = QPoint()
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.container = QFrame()
        self.container.setObjectName("floating_container")
        self.container.setStyleSheet(f"""
            QFrame#floating_container {{
                background-color: {Colors.BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(0)

        # Header
        header = QHBoxLayout()
        self.task_lbl = QLabel("FOCUSING")
        self.task_lbl.setStyleSheet(f"font-family: 'Plus Jakarta Sans'; font-size: 10px; font-weight: 800; color: {Colors.TEXT_MUTED}; letter-spacing: 0.1em;")
        header.addWidget(self.task_lbl)
        header.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {Colors.TEXT_MUTED}; border: none; font-size: 14px; }} QPushButton:hover {{ color: {Colors.PRIMARY}; }}")
        close_btn.clicked.connect(self.close_requested.emit)
        header.addWidget(close_btn)
        layout.addLayout(header)

        layout.addStretch()

        # Timer
        self.timer_lbl = QLabel("00:00")
        self.timer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 36px; font-weight: 700; color: {Colors.TEXT};")
        layout.addWidget(self.timer_lbl)

        # Next Break info
        self.next_break_lbl = QLabel("NEXT BREAK IN: --:--")
        self.next_break_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_break_lbl.setStyleSheet(f"font-family: 'Plus Jakarta Sans'; font-size: 10px; font-weight: 700; color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(self.next_break_lbl)

        layout.addStretch()

        # Progress
        self.progress = QProgressBar()
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"""
            QProgressBar {{ background: {Colors.BORDER}; border: none; border-radius: 2px; }} 
            QProgressBar::chunk {{ background: {Colors.PRIMARY}; border-radius: 2px; }}
        """)
        layout.addWidget(self.progress)

        main_layout.addWidget(self.container)

    def update_status(self, task_name: str, remaining_sec: int, next_break_sec: int, total_sec: int, mode: str = "Focused"):
        self.task_lbl.setText(task_name.upper())
        self.timer_lbl.setText(fmt_time(remaining_sec))

        if next_break_sec is not None:
            self.next_break_lbl.setText(f"NEXT BREAK IN: {fmt_time(next_break_sec)}")
        else:
            self.next_break_lbl.setText(f"{mode.upper()} FLOW ACTIVE")

        progress_val = int(((total_sec - remaining_sec) / total_sec) * 100) if total_sec > 0 else 0
        self.progress.setValue(progress_val)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
