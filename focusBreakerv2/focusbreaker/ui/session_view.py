from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from focusbreaker.config import Colors, UIConfig
from focusbreaker.core.timer import fmt_time
from focusbreaker.ui.components.progress_ring import ProgressRing

class SessionView(QWidget):
    """
    PAGE 3 — Active Session View (Normal Mode)
    PAGE 4 — Active Session View (Strict / Focused Mode)
    Refined with custom fonts and modern spacing.
    """
    stop_requested = Signal()
    pause_requested = Signal()
    resume_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 60, 0, 80)
        self.main_layout.setSpacing(0)

        # 1. Top Task Label
        self.task_lbl = QLabel("CODING SESSION")
        self.task_lbl.setStyleSheet(f"""
            font-family: 'Plus Jakarta Sans'; 
            font-size: 13px; 
            font-weight: 700; 
            color: {Colors.TEXT_MUTED}; 
            letter-spacing: 0.15em;
        """)
        self.main_layout.addWidget(self.task_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addStretch(1)

        # 2. Progress Ring Area
        self.ring_container = QWidget()
        self.ring_container.setFixedSize(480, 480)
        
        # Center Ring
        self.ring = ProgressRing(self.ring_container)
        self.ring.setFixedSize(360, 360)
        self.ring.move(60, 60) # Centered in 480x480
        
        # Center Content Layout (Inside Ring)
        self.inner_content = QWidget(self.ring_container)
        self.inner_content.setFixedSize(300, 300)
        self.inner_content.move(90, 90) # Centered in 480x480
        icl = QVBoxLayout(self.inner_content)
        icl.setContentsMargins(0, 0, 0, 0)
        icl.setSpacing(4)
        icl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.focus_lbl = QLabel("FOCUSING:")
        self.focus_lbl.setStyleSheet(f"""
            font-family: 'Plus Jakarta Sans';
            font-size: 11px; 
            font-weight: 800; 
            color: {Colors.TEXT_MUTED}; 
            letter-spacing: 0.12em;
        """)
        
        self.timer_lbl = QLabel("24:59")
        self.timer_lbl.setStyleSheet(f"""
            font-family: 'JetBrains Mono'; 
            font-size: 64px; 
            font-weight: 700; 
            color: {Colors.TEXT};
            letter-spacing: -2px;
        """)
        
        self.rem_lbl = QLabel("REMAINING")
        self.rem_lbl.setStyleSheet(f"""
            font-family: 'Plus Jakarta Sans';
            font-size: 11px; 
            font-weight: 700; 
            color: {Colors.TEXT_MUTED}; 
            letter-spacing: 0.08em;
        """)

        icl.addWidget(self.focus_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        icl.addWidget(self.timer_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        icl.addWidget(self.rem_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        # Break Rhythm Panel (Positioned relative to ring)
        self.rhythm_panel = QFrame(self.ring_container)
        self.rhythm_panel.setFixedSize(140, 70)
        self.rhythm_panel.move(340, 360) # Bottom right overlap
        rpl = QVBoxLayout(self.rhythm_panel)
        rpl.setContentsMargins(12, 8, 12, 8)
        rpl.setSpacing(2)
        
        rp_title = QLabel("NEXT BREAK")
        rp_title.setStyleSheet(f"font-family: 'Plus Jakarta Sans'; font-size: 9px; font-weight: 800; color: {Colors.TEXT_MUTED}; letter-spacing: 0.1em;")
        self.next_break_val = QLabel("05:00")
        self.next_break_val.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 16px; font-weight: 700; color: {Colors.TEXT};")
        
        self.dot_layout = QHBoxLayout()
        self.dot_layout.setSpacing(6)
        self.dots = []
        for _ in range(3):
            dot = QFrame()
            dot.setFixedSize(6, 6)
            dot.setStyleSheet(f"background: {Colors.BORDER}; border-radius: 3px;")
            self.dots.append(dot)
            self.dot_layout.addWidget(dot)
        self.dot_layout.addStretch()

        rpl.addWidget(rp_title)
        rpl.addWidget(self.next_break_val)
        rpl.addLayout(self.dot_layout)

        self.main_layout.addWidget(self.ring_container, alignment=Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addStretch(1)

        # 3. Controls
        self.controls = QHBoxLayout()
        self.controls.setSpacing(16)
        self.controls.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.pause_btn = QPushButton("PAUSE")
        self.pause_btn.setFixedSize(140, 44)
        self.pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_btn.setObjectName("secondary_btn")
        self.pause_btn.clicked.connect(self._toggle_pause)
        
        self.end_btn = QPushButton("END SESSION")
        self.end_btn.setFixedSize(140, 44)
        self.end_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.end_btn.setObjectName("primary_btn")
        self.end_btn.clicked.connect(self.stop_requested.emit)

        self.controls.addWidget(self.pause_btn)
        self.controls.addWidget(self.end_btn)
        self.main_layout.addLayout(self.controls)

    def update_session(self, task_name: str, mode: str, remaining_sec: int, total_sec: int, is_paused: bool, next_break_sec: int = 0, breaks_done: int = 0):
        self.task_lbl.setText(task_name.upper())
        self.timer_lbl.setText(fmt_time(remaining_sec))
        
        progress = (total_sec - remaining_sec) / total_sec if total_sec > 0 else 0
        self.ring.value = float(progress)  # type: ignore[assignment]
        
        if next_break_sec is not None:
            self.next_break_val.setText(fmt_time(next_break_sec))
        else:
            self.next_break_val.setText("--:--")
            
        self.pause_btn.setText("RESUME" if is_paused else "PAUSE")
        
        # Update Rhythm Dots
        for i, dot in enumerate(self.dots):
            color = Colors.PRIMARY if i < breaks_done else Colors.BORDER
            dot.setStyleSheet(f"background: {color}; border-radius: 3px;")

        # Apply Theming
        if mode.lower() in ["strict", "focused"]:
            self._apply_dark_theme(mode)
        else:
            self._apply_light_theme()

    def _apply_light_theme(self):
        self.setStyleSheet(f"background-color: {Colors.BG};")
        self.timer_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 64px; font-weight: 700; color: {Colors.TEXT}; letter-spacing: -2px;")
        self.next_break_val.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 16px; font-weight: 700; color: {Colors.TEXT};")
        self.ring.set_colors(Colors.PRIMARY, Colors.BORDER)
        self.pause_btn.show()
        self.end_btn.show()

    def _apply_dark_theme(self, mode):
        self.setStyleSheet(f"background-color: {Colors.DARK};")
        self.task_lbl.setStyleSheet(f"font-family: 'Plus Jakarta Sans'; font-size: 13px; font-weight: 700; color: {Colors.TEXT_SECONDARY}; letter-spacing: 0.15em;")
        self.timer_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 64px; font-weight: 700; color: {Colors.TEXT_INVERSE}; letter-spacing: -2px;")
        self.next_break_val.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 16px; font-weight: 700; color: {Colors.TEXT_INVERSE};")
        self.focus_lbl.setStyleSheet(f"font-family: 'Plus Jakarta Sans'; font-size: 11px; font-weight: 800; color: rgba(255,255,255,0.5); letter-spacing: 0.12em;")
        self.rem_lbl.setStyleSheet(f"font-family: 'Plus Jakarta Sans'; font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.5); letter-spacing: 0.08em;")
        
        ring_color = Colors.ACCENT if mode.lower() == "strict" else Colors.PRIMARY
        self.ring.set_colors(ring_color, "rgba(255,255,255,0.06)")
        
        # Hide controls in Strict/Focused
        self.pause_btn.hide()
        self.end_btn.hide()

    def _toggle_pause(self):
        if self.pause_btn.text() == "PAUSE":
            self.pause_requested.emit()
        else:
            self.resume_requested.emit()
