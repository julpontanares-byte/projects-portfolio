from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QWidget, QProgressBar, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, QPoint
from focusbreaker.config import Palette, Colors
from focusbreaker.data.db import DBManager

def get_achievements_config(stats):
    """
    Returns the achievement list with live progress data injected.
    stats: dict from DBManager.get_achievement_stats()
    """
    return [
        {"id": 1, "cat": "Milestones", "icon": "🚀", "name": "First step", "desc": "Complete your first session", "cur": stats['sessions'], "target": 1},
        {"id": 2, "cat": "Milestones", "icon": "⚡", "name": "Ten strong", "desc": "Complete 10 sessions", "cur": stats['sessions'], "target": 10},
        {"id": 3, "cat": "Milestones", "icon": "🏅", "name": "Half century", "desc": "Complete 50 sessions", "cur": stats['sessions'], "target": 50},
        {"id": 4, "cat": "Milestones", "icon": "👑", "name": "Centurion", "desc": "Complete 100 sessions", "cur": stats['sessions'], "target": 100},
        
        {"id": 5, "cat": "Streaks", "icon": "🔥", "name": "On fire", "desc": "Reach a 5-day streak", "cur": stats['daily_streak'], "target": 5},
        {"id": 6, "cat": "Streaks", "icon": "💥", "name": "Blazing", "desc": "Reach a 10-day streak", "cur": stats['daily_streak'], "target": 10},
        {"id": 7, "cat": "Streaks", "icon": "🌪", "name": "Unstoppable", "desc": "Reach a 25-day streak", "cur": stats['daily_streak'], "target": 25},
        {"id": 8, "cat": "Streaks", "icon": "🏆", "name": "Legendary", "desc": "Reach a 50-day streak", "cur": stats['daily_streak'], "target": 50},
        
        {"id": 9, "cat": "Perfect", "icon": "⭐", "name": "Pristine", "desc": "Complete a perfect session", "cur": stats['perfect_sessions'], "target": 1},
        {"id": 10, "cat": "Perfect", "icon": "💎", "name": "Pure focus", "desc": "5 perfect sessions in a row", "cur": stats['consecutive_perfect'], "target": 5},
        {"id": 11, "cat": "Perfect", "icon": "🌟", "name": "Flawless", "desc": "10 consecutive perfect sessions", "cur": stats['consecutive_perfect'], "target": 10},
        
        {"id": 12, "cat": "Mode master", "icon": "⚔️", "name": "Iron will", "desc": "Complete 10 Strict mode sessions", "cur": stats['strict_sessions'], "target": 10},
        {"id": 13, "cat": "Mode master", "icon": "🔭", "name": "Deep diver", "desc": "Complete 10 Focused mode sessions", "cur": stats['focused_sessions'], "target": 10},
        {"id": 14, "cat": "Mode master", "icon": "⚖️", "name": "Balanced", "desc": "Use all 3 modes in one week", "cur": stats['modes_used'], "target": 3},
        
        {"id": 15, "cat": "Time", "icon": "⏳", "name": "Hour glass", "desc": "10 total hours of work", "cur": stats['hours'], "target": 10},
        {"id": 16, "cat": "Time", "icon": "🏃", "name": "Marathon", "desc": "50 total hours of work", "cur": stats['hours'], "target": 50},
        {"id": 17, "cat": "Time", "icon": "🎯", "name": "Century mark", "desc": "100 total hours of work", "cur": stats['hours'], "target": 100},
        
        {"id": 18, "cat": "Discipline", "icon": "✅", "name": "Break keeper", "desc": "Take all breaks across 10 sessions", "cur": stats['total_breaks'], "target": 100}, # Scaling example
        {"id": 19, "cat": "Discipline", "icon": "🔒", "name": "No escape", "desc": "30 sessions without emergency exit", "cur": stats['no_exit_sessions'], "target": 30},
        {"id": 20, "cat": "Discipline", "icon": "🌿", "name": "Break advocate", "desc": "100 total breaks taken", "cur": stats['total_breaks'], "target": 100},
    ]

class AchievementCard(QFrame):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.unlocked = data["cur"] >= data["target"]
        self._setup_ui()

    def _setup_ui(self):
        self.setMinimumHeight(100)
        self.setObjectName("achievement_card")
        
        self.setStyleSheet(f"""
            QFrame#achievement_card {{ 
                background-color: {Palette.SURFACE_WHITE}; 
                border-radius: 16px; 
                border: 1px solid {Palette.SURFACE_DARK};
            }}
            QFrame#achievement_card:hover {{
                border: 1px solid {Palette.BRAND_LIGHT};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        
        icon_lbl = QLabel(self.data["icon"])
        icon_lbl.setStyleSheet(f"font-size: 36px; {'opacity: 0.4;' if not self.unlocked else ''}")
        icon_lbl.setFixedWidth(44)
        layout.addWidget(icon_lbl)
        
        info = QVBoxLayout()
        info.setSpacing(2)
        
        name = QLabel(self.data["name"])
        name.setStyleSheet(f"font-weight: 800; font-size: 14px; color: {Palette.TEXT_PRIMARY};")
        
        desc = QLabel(self.data["desc"])
        desc.setStyleSheet(f"font-size: 11px; color: {Palette.TEXT_SECONDARY};")
        desc.setWordWrap(True)
        
        info.addWidget(name)
        info.addWidget(desc)
        
        if self.unlocked:
            badge = QLabel("UNLOCKED")
            badge.setStyleSheet(f"""
                background: {Palette.BRAND_LIGHT}; 
                color: {Palette.BRAND_PRIMARY}; 
                border-radius: 4px; 
                padding: 2px 8px; 
                font-size: 9px; 
                font-weight: 800;
            """)
            badge.setFixedWidth(70)
            info.addSpacing(6)
            info.addWidget(badge)
        else:
            bar = QProgressBar()
            bar.setFixedHeight(6)
            bar.setTextVisible(False)
            bar.setRange(0, self.data["target"])
            bar.setValue(min(self.data["cur"], self.data["target"]))
            bar.setStyleSheet(f"""
                QProgressBar {{ 
                    background: {Palette.SURFACE_DARK}; 
                    border-radius: 3px; 
                    border: none;
                }} 
                QProgressBar::chunk {{ 
                    background: {Palette.BRAND_PRIMARY}; 
                    border-radius: 3px; 
                }}
            """)
            
            prog_lbl = QLabel(f"{self.data['cur']} / {self.data['target']}")
            prog_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: {Palette.TEXT_MUTED};")
            
            info.addSpacing(10)
            info.addWidget(bar)
            info.addWidget(prog_lbl)

        layout.addLayout(info, 1)

class AchievementsModal(QDialog):
    def __init__(self, db: DBManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowModality(Qt.ApplicationModal)
        
        self.current_filter = "All"
        self._stats = self.db.get_achievement_stats()
        self._achievements_data = get_achievements_config(self._stats)
        self._grid_columns = 2
        
        # Increase dimension if parent is maximized (by 1/4 more than previous 960x780)
        if parent and parent.isMaximized():
            self.setFixedSize(1200, 980)
        else:
            self.setFixedSize(820, 680)

        # Center on parent
        if parent:
            self.move(parent.geometry().center() - self.rect().center())
            
        self._drag_pos = QPoint()
        self._setup_ui()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def exec(self):
        if self.parent() and hasattr(self.parent(), "show_dim"):
            self.parent().show_dim(True)
        res = super().exec()
        if self.parent() and hasattr(self.parent(), "show_dim"):
            self.parent().show_dim(False)
        return res

    def _column_count_for_width(self, width):
        """Determine number of columns based on window width."""
        if width <= 900:
            return 1
        else:
            return 2

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        self.container = QFrame()
        self.container.setObjectName("modal_container")
        self.container.setStyleSheet(f"""
            QFrame#modal_container {{ 
                background-color: {Palette.SURFACE_DEFAULT}; 
                border-radius: 24px; 
                border: 1px solid {Palette.SURFACE_DARK}; 
            }}
        """)
        root.addWidget(self.container)

        l = QVBoxLayout(self.container)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)
        
        header = QFrame()
        header.setObjectName("ach_header")
        header.setStyleSheet(f"QFrame#ach_header {{ border-bottom: 1px solid {Palette.SURFACE_DARK}; }}")
        header.setFixedHeight(100)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(32, 0, 32, 0)
        
        title_v = QVBoxLayout()
        title_v.setSpacing(4)
        title_v.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        t_lbl = QLabel("Achievements")
        t_lbl.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {Palette.TEXT_PRIMARY};")
        
        unlocked_count = sum(1 for a in self._achievements_data if a["cur"] >= a["target"])
        u_lbl = QLabel(f"{unlocked_count} of {len(self._achievements_data)} unlocked")
        u_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 11px; font-weight: 700; color: {Palette.TEXT_MUTED};")
        title_v.addWidget(t_lbl); title_v.addWidget(u_lbl)
        hl.addLayout(title_v)
        hl.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(36, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{ 
                background: transparent; 
                border: none; 
                border-radius: 6px; 
                color: {Palette.TEXT_PRIMARY}; 
                font-weight: 900; 
                font-size: 16px;
                font-family: 'Segoe UI';
            }} 
            QPushButton:hover {{ 
                background: #FF5F57; 
                color: white;
            }}
        """)
        close_btn.clicked.connect(self.reject)
        hl.addWidget(close_btn)
        l.addWidget(header)
        
        filters_scroll = QScrollArea()
        filters_scroll.setWidgetResizable(True)
        filters_scroll.setFixedHeight(64)
        filters_scroll.setFrameShape(QFrame.Shape.NoFrame)
        filters_scroll.setStyleSheet("background: transparent;")
        
        filters_widget = QWidget()
        fl = QHBoxLayout(filters_widget)
        fl.setContentsMargins(32, 12, 32, 12)
        fl.setSpacing(10)
        
        cats = ["All", "Milestones", "Streaks", "Perfect", "Mode master", "Time", "Discipline"]
        self.filter_btns = {}
        for cat in cats:
            btn = QPushButton(cat)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda _, c=cat: self._filter_changed(c))
            fl.addWidget(btn)
            self.filter_btns[cat] = btn
        fl.addStretch()
        filters_scroll.setWidget(filters_widget)
        l.addWidget(filters_scroll)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        
        self.grid_widget = QWidget()
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setSpacing(16)
        self.grid.setContentsMargins(32, 0, 32, 32)
        
        self.scroll.setWidget(self.grid_widget)
        l.addWidget(self.scroll)
        
        self._filter_changed("All")

    def _filter_changed(self, cat):
        self.current_filter = cat
        for c, btn in self.filter_btns.items():
            is_active = (c == cat)
            btn.setChecked(is_active)
            if is_active:
                btn.setStyleSheet(f"background: {Palette.BRAND_PRIMARY}; color: white; border-radius: 16px; padding: 0 16px; font-weight: 700; font-size: 12px;")
            else:
                btn.setStyleSheet(f"background: white; color: {Palette.TEXT_SECONDARY}; border: 1px solid {Palette.SURFACE_DARK}; border-radius: 16px; padding: 0 16px; font-weight: 600; font-size: 12px;")
        self._refresh_grid()

    def _refresh_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        filtered = self._achievements_data if self.current_filter == "All" else [d for d in self._achievements_data if d["cat"] == self.current_filter]
        
        columns = self._column_count_for_width(self.width())
        
        for i, data in enumerate(filtered):
            card = AchievementCard(data)
            self.grid.addWidget(card, i // columns, i % columns)
        
        self.grid.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding), (len(filtered) + 1) // 2, 0)

    def mousePressEvent(self, event):
        if not self.container.geometry().contains(self.container.mapFromGlobal(event.globalPosition().toPoint())):
            self.reject()
        super().mousePressEvent(event)
