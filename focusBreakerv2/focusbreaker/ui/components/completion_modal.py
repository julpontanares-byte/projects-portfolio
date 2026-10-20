from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QApplication
from PySide6.QtCore import Qt
from focusbreaker.config import Palette
from focusbreaker.data.models import WorkSession

class SessionCompleteModal(QDialog):
    def __init__(self, session: WorkSession, milestones: list, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)

        self.setFixedSize(500, 600)
        # Center on parent
        if parent:
            self.move(parent.geometry().center() - self.rect().center())

        self._setup_ui(session, milestones)

    def _setup_ui(self, session, milestones):
        self.setStyleSheet("QDialog { background: transparent; }")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        self.shell = QFrame()
        self.shell.setObjectName("completion_shell")
        self.shell.setStyleSheet(f"""
            QFrame#completion_shell {{ 
                background-color: {Palette.SURFACE_WHITE}; 
                border-radius: 32px; 
                border: 1px solid {Palette.SURFACE_DARK};
            }}
        """)
        root.addWidget(self.shell)

        l = QVBoxLayout(self.shell)
        l.setContentsMargins(40, 40, 40, 40)
        l.setSpacing(24)

        # Header: Icon & Celebration
        header = QVBoxLayout()
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl = QLabel("🎉")
        icon_lbl.setStyleSheet("font-size: 64px; background: transparent; border: none;")
        header.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        congrats = QLabel("EXCELLENT WORK!")
        congrats.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {Palette.BRAND_PRIMARY}; letter-spacing: 3px; background: transparent; border: none;")
        header.addWidget(congrats, alignment=Qt.AlignmentFlag.AlignCenter)
        
        task_name = QLabel(session.task_name)
        task_name.setWordWrap(True)
        task_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        task_name.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {Palette.TEXT_PRIMARY}; background: transparent; border: none;")
        header.addWidget(task_name)
        
        summary_text = f"You completed a {session.mode.capitalize()} session for {session.actual_duration_minutes} minutes."
        subtitle = QLabel(summary_text)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {Palette.TEXT_SECONDARY}; background: transparent; border: none;")
        header.addWidget(subtitle)
        
        l.addLayout(header)

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {Palette.SURFACE_DARK}; border: none;")
        l.addWidget(div)

        # Summary Stats
        stats_grid = QHBoxLayout()
        stats_grid.setSpacing(20)
        
        def add_stat(label, value, icon):
            v = QVBoxLayout()
            v.setSpacing(4)
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val = QLabel(f"{icon} {value}")
            val.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 20px; font-weight: 700; color: {Palette.TEXT_PRIMARY}; background: transparent; border: none;")
            lab = QLabel(label.upper())
            lab.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {Palette.TEXT_MUTED}; letter-spacing: 1px; background: transparent; border: none;")
            v.addWidget(val); v.addWidget(lab)
            stats_grid.addLayout(v)

        add_stat("Duration", f"{session.actual_duration_minutes}m", "⏱")
        quality_score = int(session.quality_score * 100)
        add_stat("Quality", f"{quality_score}%", "🎯")
        add_stat("Breaks", str(session.breaks_taken), "☕")
        
        l.addLayout(stats_grid)

        # Milestones Section
        if milestones:
            m_box = QFrame()
            m_box.setStyleSheet(f"background: {Palette.BRAND_LIGHT}; border-radius: 16px; border: 1.5px solid {Palette.BRAND_PRIMARY};")
            ml = QVBoxLayout(m_box)
            ml.setContentsMargins(16, 16, 16, 16)
            ml.setSpacing(10)
            
            m_title = QLabel("MILESTONES ACHIEVED")
            m_title.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {Palette.BRAND_PRIMARY}; letter-spacing: 1px; border: none; background: transparent;")
            ml.addWidget(m_title)
            
            for m in milestones:
                row = QHBoxLayout()
                m_icon = QLabel("🏆")
                m_icon.setStyleSheet("font-size: 16px; background: transparent; border: none;")
                m_txt = QLabel(m.get("message", "Achievement unlocked!"))
                m_txt.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {Palette.TEXT_PRIMARY}; background: transparent; border: none;")
                row.addWidget(m_icon); row.addWidget(m_txt, 1)
                ml.addLayout(row)
            l.addWidget(m_box)

        # Done Button
        btn = QPushButton("Done")
        btn.setFixedHeight(54)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Palette.BRAND_PRIMARY};
                color: white;
                border-radius: 27px;
                font-weight: 800;
                font-size: 15px;
                margin-top: 10px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {Palette.BRAND_SECONDARY};
            }}
        """)
        btn.clicked.connect(self.accept)
        l.addWidget(btn)
