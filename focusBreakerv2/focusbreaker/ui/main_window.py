import sys
import logging
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QStackedWidget, QSizePolicy,
    QSpacerItem, QMessageBox, QTableWidget, QHeaderView, QInputDialog,
    QBoxLayout, QLineEdit, QSizeGrip, QProgressBar, QDialog, QComboBox, QApplication
)

from PySide6.QtCore import Qt, Signal, QPoint, QSize, Property, QTimer, QEvent
from PySide6.QtGui import QFont, QCursor, QCloseEvent, QIcon, QPixmap, QPainter, QColor

from focusbreaker.config import Colors, MODES, UIConfig, Palette, APP_NAME, AppPaths

from focusbreaker.core.session_manager import SessionManager
from focusbreaker.core.timer import fmt_time

logger = logging.getLogger(__name__)
from focusbreaker.data.db import DBManager
from focusbreaker.data.models import Task, WorkSession, Streak
from focusbreaker.ui.task_dialog import TaskDialog
from focusbreaker.ui.settings_dialog import SettingsPage
from focusbreaker.ui.analytics_dialog import AnalyticsPage
from focusbreaker.ui.tray_icon import SystemTrayManager
from focusbreaker.ui.floating_session import FloatingSessionWindow

from focusbreaker.ui.break_window import NormalBreakWindow, StrictBreakWindow, FocusEndBreakWindow

from focusbreaker.ui.achievements_modal import AchievementsModal
from focusbreaker.ui.components.progress_ring import ProgressRing
from focusbreaker.ui.components.dialogs import ThemedConfirmDialog, ThemedMessageDialog
from focusbreaker.ui.components.completion_modal import SessionCompleteModal
from focusbreaker.system.audio import AudioManager
from focusbreaker.system.display import DisplayController
from focusbreaker.system.input_blocker import InputBlocker
from focusbreaker.system.media_manager import MediaManager

# ── Shared Components ──────────────────────────────────────────

class SectionHeader(QWidget):
    def __init__(self, title, action_text=None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        self.lbl = QLabel(title.upper())
        self.lbl.setObjectName("section_label")
        layout.addWidget(self.lbl)
        
        self.divider = QWidget()
        self.divider.setObjectName("section_divider")
        self.divider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.divider.setFixedHeight(1)
        layout.addWidget(self.divider)
        
        if action_text:
            self.btn = QPushButton(action_text)
            self.btn.setStyleSheet(f"color: {Palette.BRAND_SECONDARY}; font-weight: 700; font-size: 12px; background: transparent; border: none;")
            self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(self.btn)

class SegmentedSwitcher(QWidget):
    tab_changed = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tab_switcher_container")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        
        self.tabs = {}
        items = [("home", "Home"), ("analytics", "Analytics"), ("history", "History")]
        for key, label in items:
            btn = QPushButton(label)
            btn.setProperty("active", "false")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setObjectName("nav_tab")
            btn.clicked.connect(lambda _, k=key: self._on_clicked(k))
            layout.addWidget(btn)
            self.tabs[key] = btn
            
        self.set_active("home")

    def _on_clicked(self, key):
        self.set_active(key)
        self.tab_changed.emit(key)

    def set_active(self, key):
        for k, btn in self.tabs.items():
            is_active = (k == key)
            btn.setProperty("active", "true" if is_active else "false")
            btn.setChecked(is_active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

# ── Utility Dialog Components ──────────────────────────────

# ── Home Page Components ───────────────────────────────────────


class StreakCard(QFrame):
    def __init__(self, icon, title, count, best, parent=None, tip=""):
        super().__init__(parent)
        self.setObjectName("metric_card")
        self.setMinimumHeight(160)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(4)
        
        header = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 28px; margin-bottom: 4px;")
        header.addWidget(icon_lbl)
        
        if tip:
            # Polished CSS-drawn italicized info icon
            info = QLabel("i")
            info.setObjectName("info_icon_btn")
            info.setFixedSize(18, 18)
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info.setCursor(Qt.CursorShape.WhatsThisCursor)
            info.setToolTip(tip)
            header.addStretch()
            header.addWidget(info)
        
        layout.addLayout(header)
        
        title_lbl = QLabel(title.upper())
        title_lbl.setStyleSheet(f"font-weight: 800; color: {Palette.TEXT_MUTED}; font-size: 10px; letter-spacing: 1px;")
        layout.addWidget(title_lbl)

        self.val_lbl = QLabel(str(count))
        self.val_lbl.setObjectName("metric_value")
        self.val_lbl.setStyleSheet(f"color: {Palette.TEXT_PRIMARY};")
        layout.addWidget(self.val_lbl)
        
        self.best_lbl = QLabel(f"BEST: {best}")
        self.best_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 9px; font-weight: 700; color: {Palette.BRAND_SECONDARY};")
        layout.addWidget(self.best_lbl)

class AchievementBadgeTile(QFrame):
    def __init__(self, name, icon, locked=False, parent=None):
        super().__init__(parent)
        self.setObjectName("achievement_tile")
        self.setProperty("locked", "true" if locked else "false")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)
        
        icon_lbl = QLabel(icon)
        icon_lbl.setObjectName("ach_icon")
        layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        name_box = QWidget()
        name_box.setObjectName("ach_name_box")
        name_box_l = QHBoxLayout(name_box)
        name_box_l.setContentsMargins(6, 2, 6, 2)
        
        name_lbl = QLabel(name.upper())
        name_lbl.setObjectName("ach_name_text")
        name_box_l.addWidget(name_lbl)
        layout.addWidget(name_box, alignment=Qt.AlignmentFlag.AlignCenter)

class QuickStatCard(QFrame):
    def __init__(self, value, label, parent=None, tip=""):
        super().__init__(parent)
        self.setObjectName("metric_card")
        self.setMinimumHeight(120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(4)
        
        header = QHBoxLayout()
        self.l = QLabel(label.upper())
        self.l.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {Palette.TEXT_MUTED}; letter-spacing: 0.5px;")
        header.addWidget(self.l)
        
        if tip:
            # Polished CSS-drawn italicized info icon
            info = QLabel("i")
            info.setObjectName("info_icon_btn")
            info.setFixedSize(18, 18)
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info.setCursor(Qt.CursorShape.WhatsThisCursor)
            info.setToolTip(tip)
            header.addStretch()
            header.addWidget(info)
        
        layout.addLayout(header)

        self.v = QLabel(str(value))
        self.v.setObjectName("metric_value")
        self.v.setStyleSheet(f"font-size: 28px; color: {Palette.BRAND_PRIMARY};")
        layout.addWidget(self.v)

# ── History Page Components ─────────────────────────────────────

class HistoryRow(QFrame):
    def __init__(self, session: WorkSession, parent=None):
        super().__init__(parent)
        self.setObjectName("history_row")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(20)
        
        # Quality dot
        score = int(session.quality_score * 100)
        dot = QFrame()
        dot.setFixedSize(8, 8)
        color = "#4CAF50" if score >= 80 else ("#FFC107" if score >= 50 else "#F44336")
        dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
        layout.addWidget(dot)
        
        # Task info
        info = QVBoxLayout()
        name_txt = session.task_name
        if len(name_txt) > 40: name_txt = name_txt[:37] + "..."
        name = QLabel(name_txt)
        name.setStyleSheet("font-weight: 600; font-size: 14px; color: #1E2D2C;")
        info.addWidget(name)
        
        sub = QHBoxLayout()
        sub.setSpacing(10)
        mode = QLabel(session.mode.upper())
        mode.setStyleSheet(f"font-size: 9px; font-weight: 800; color: {Palette.TEXT_MUTED}; border: 1.5px solid {Palette.BORDER_DEFAULT}; border-radius: 4px; padding: 1px 6px;")
        
        # Parse date
        try:
            dt = datetime.fromisoformat(session.start_time)
            date_str = dt.strftime("%b %d, %I:%M %p")
            # Special case for "Today" and "Yesterday"
            today = datetime.now().date()
            if dt.date() == today:
                date_str = f"Today, {dt.strftime('%I:%M %p')}"
            elif dt.date() == today - timedelta(days=1):
                date_str = f"Yesterday, {dt.strftime('%I:%M %p')}"
        except:
            date_str = session.start_time
            
        meta = QLabel(f"{date_str}  •  {session.actual_duration_minutes} min")
        meta.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 10px; color: {Palette.TEXT_MUTED};")
        
        sub.addWidget(mode)
        sub.addWidget(meta)
        if session.emergency_exits > 0:
            warn = QLabel(f"⚠ {session.emergency_exits} emergency")
            warn.setStyleSheet("font-size: 9px; font-weight: 800; color: #F44336;")
            sub.addWidget(warn)
        sub.addStretch()
        info.addLayout(sub)
        layout.addLayout(info, 1)
        
        # Stats (Taken, Snoozed, Skipped)
        for val in [session.breaks_taken, session.breaks_snoozed, session.breaks_skipped]:
            lbl = QLabel(str(val))
            lbl.setFixedWidth(60)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 12px; font-weight: 600;")
            layout.addWidget(lbl)
            
        score_val = session.quality_score * 100
        score_txt = f"{score_val:.1f}%".replace(".0%", "%")
        score_lbl = QLabel(score_txt)
        score_lbl.setFixedWidth(60)
        score_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        score_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 13px; font-weight: 700; color: {color};")
        layout.addWidget(score_lbl)

from datetime import timedelta

# ── Main Window ──────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, db: DBManager):
        super().__init__()
        self.db = db
        self.session_mgr = SessionManager(db, self)
        self.audio = AudioManager()
        self.display = DisplayController(self)
        self.input_blocker = InputBlocker()
        self.tray = SystemTrayManager(self)
        
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowSystemMenuHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.resize(1000, 750)
        self.floating_window = None
        self._setup_signals()
        self._build_ui()
        self._refresh_dashboard()
        
        self._drag_pos = QPoint()

    def _setup_signals(self):
        self.session_mgr.tick.connect(self._on_tick)
        self.session_mgr.break_due.connect(self._on_break_due)
        self.session_mgr.warning_emitted.connect(self._on_warning_emitted)
        self.session_mgr.session_started.connect(self._on_session_started)
        self.session_mgr.session_completed.connect(self._on_session_complete)
        self.session_mgr.session_finished_normal.connect(self._on_session_finished_normal)
        self.session_mgr.status_changed.connect(self._on_status_changed)
        
        # Tray signal connections
        self.tray.show_window_requested.connect(self._on_show_window)
        self.tray.new_task_requested.connect(self._on_new_task_tray)
        self.tray.settings_requested.connect(self._on_settings_tray)
        self.tray.end_session_requested.connect(self._on_end_session_tray)
        self.tray.quit_requested.connect(self._on_quit_requested)
        self.tray.show()

    def _build_ui(self):
        self.main_shell = QWidget()
        self.main_shell.setObjectName("main_shell")
        self.setCentralWidget(self.main_shell)
        
        shell_l = QVBoxLayout(self.main_shell)
        shell_l.setContentsMargins(0, 0, 0, 0)
        
        self.content_root = QWidget()
        self.content_root.setObjectName("content_root")
        shell_l.addWidget(self.content_root)

        # 4. Global Dim Overlay (covers everything for modals)
        self.dim_overlay = QFrame(self.main_shell)
        self.dim_overlay.setObjectName("global_dim_overlay")
        self.dim_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.5); border-radius: 24px;")
        self.dim_overlay.hide()
        self.main_shell.installEventFilter(self)
        
        self.main_layout = QVBoxLayout(self.content_root)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Top Navigation
        self.top_nav = QWidget()
        self.top_nav.setObjectName("top_nav")
        nav_l = QHBoxLayout(self.top_nav)
        nav_l.setContentsMargins(30, 0, 30, 0)
        nav_l.setSpacing(0)
        
        # ── Left Container (Fixed width for true centering) ──
        left_container = QWidget()
        left_container.setFixedWidth(250)
        left_l = QHBoxLayout(left_container)
        left_l.setContentsMargins(0, 0, 0, 0)
        left_l.setSpacing(12)
        
        # Logo
        logo_lbl = QLabel()
        logo_pixmap = QPixmap(str(AppPaths.IMAGES_DIR / "focusBreaker_circle_logo.png"))
        if not logo_pixmap.isNull():
            logo_lbl.setPixmap(logo_pixmap.scaledToHeight(28, Qt.TransformationMode.SmoothTransformation))
        else:
            logo_lbl.setText("focusBreaker")
            logo_lbl.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {Palette.TEXT_PRIMARY};")
        left_l.addWidget(logo_lbl)
        
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(24, 24)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setStyleSheet("font-size: 18px; color: #1E2D2C; background: transparent; border: none;")
        self.settings_btn.clicked.connect(self._open_settings)
        left_l.addWidget(self.settings_btn)
        left_l.addStretch()
        
        nav_l.addWidget(left_container)
        
        # ── Center Area ──
        nav_l.addStretch()
        self.switcher = SegmentedSwitcher()
        self.switcher.tab_changed.connect(self._navigate)
        nav_l.addWidget(self.switcher)
        nav_l.addStretch()
        
        # ── Right Container (Mirrors left width for true centering) ──
        right_container = QWidget()
        right_container.setFixedWidth(250)
        right_l = QHBoxLayout(right_container)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.setSpacing(2) # Decreased spacing as requested
        right_l.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Modern Window Controls (Standardized symbols)
        self.btn_minimize = QPushButton("—")
        self.btn_maximize = QPushButton("▢") 
        self.btn_close = QPushButton("✕")
        
        for btn in [self.btn_minimize, self.btn_maximize, self.btn_close]:
            btn.setFixedSize(40, 32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Hover effects
            hover_bg = "#FF5F57" if btn == self.btn_close else Palette.SURFACE_DARK
            hover_text = "white" if btn == self.btn_close else Palette.TEXT_PRIMARY
            
            # Sub-layout for icons to ensure perfect alignment
            il = QVBoxLayout(btn)
            il.setContentsMargins(0, 0, 0, 0)
            il.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl = QLabel(btn.text())
            btn.setText("") # Remove text from button, use label
            
            # Icon styling
            f_size = 14 if btn == self.btn_minimize else (12 if btn == self.btn_maximize else 14)
            lbl.setStyleSheet(f"font-family: 'Segoe UI Symbol', 'Segoe UI'; font-size: {f_size}px; font-weight: 600; color: inherit;")
            il.addWidget(lbl)
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border-radius: 4px;
                    color: {Palette.TEXT_PRIMARY};
                }}
                QPushButton:hover {{
                    background: {hover_bg};
                    color: {hover_text};
                }}
            """)
            right_l.addWidget(btn)

        self.btn_minimize.clicked.connect(self.showMinimized)
        self.btn_maximize.clicked.connect(self._toggle_max)
        self.btn_close.clicked.connect(self.close)
        
        nav_l.addWidget(right_container)
        
        self.main_layout.addWidget(self.top_nav)

        # 2. Main Stack
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        # Add stack pages in order:
        # 0 = Home, 1 = History, 2 = Analytics, 3 = Settings (placeholder), 4 = Session view
        self.stack.addWidget(self._init_home())      # 0
        self.stack.addWidget(self._init_history())   # 1
        self.analytics_page = AnalyticsPage(self.db)
        self.stack.addWidget(self.analytics_page)    # 2
        
        # Placeholders for tests/future use
        self.stack.addWidget(QWidget())              # 3
        self.stack.addWidget(QWidget())              # 4

        # Settings is now a modal dialog reference
        self.settings_dialog = None

        # Top navbar already controls navigation via SegmentedSwitcher -> _navigate()

        # FAB
        self.fab = QPushButton("+", self.content_root)
        self.fab.setObjectName("fab_add")
        self.fab.setFixedSize(70, 70)
        self.fab.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fab.setToolTip("Start a new session")
        self.fab.clicked.connect(self._on_new_task)
        self._reposition_fab()

        # Set default tab
        self._navigate("home")

    def _init_home(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        l = QVBoxLayout(content)
        l.setContentsMargins(60, 40, 60, 60)
        l.setSpacing(40)
        l.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Greeting
        greet = QVBoxLayout()
        self.greet_title = QLabel("Good morning, Annuh!")
        self.greet_title.setObjectName("page_title")
        self.greet_date = QLabel(datetime.now().strftime("%B %d, %Y"))
        self.greet_date.setStyleSheet(f"font-size: 14px; color: {Palette.BRAND_SECONDARY}; font-weight: 600;")
        greet.addWidget(self.greet_title); greet.addWidget(self.greet_date)
        l.addLayout(greet)

        # Section 1: Active Session
        self.active_sec_header = SectionHeader("Active Session")
        l.addWidget(self.active_sec_header)
        
        self.active_card = QFrame()
        self.active_card.setObjectName("active_session_card")
        self.active_card.setCursor(Qt.CursorShape.PointingHandCursor)
        self.active_card.installEventFilter(self)
        acl = QVBoxLayout(self.active_card)
        acl.setContentsMargins(0, 0, 0, 0)
        acl.setSpacing(0)
        
        # Main content area (Split left/right)
        content_v = QVBoxLayout()
        content_v.setContentsMargins(32, 32, 32, 24)
        content_v.setSpacing(32)
        
        top_split = QHBoxLayout()
        top_split.setSpacing(40)
        
        # Left: Task Info
        task_info = QVBoxLayout()
        task_info.setSpacing(16)
        
        self.active_task = QLabel("No active task")
        self.active_task.setObjectName("task_name_heading")
        self.active_task.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {Palette.TEXT_PRIMARY};")
        
        badges = QHBoxLayout()
        badges.setSpacing(10)
        self.active_mode = QLabel("NORMAL"); self.active_mode.setProperty("class", "badge badge_mode")
        self.active_live = QLabel("• LIVE"); self.active_live.setProperty("class", "badge badge_live")
        badges.addWidget(self.active_mode); badges.addWidget(self.active_live); badges.addStretch()
        
        self.alert_banner = QFrame()
        self.alert_banner.setObjectName("active_alert_banner")
        self.alert_banner.setFixedHeight(48)
        self.alert_banner.setStyleSheet(f"QFrame#active_alert_banner {{ background: {Palette.BRAND_LIGHT}; border-radius: 12px; border: 1.5px solid {Palette.BRAND_PRIMARY}; }}")
        al_l = QHBoxLayout(self.alert_banner)
        al_l.setContentsMargins(16, 0, 16, 0)
        al_l.setSpacing(12)
        
        alert_icon = QLabel("i")
        alert_icon.setFixedSize(16, 16)
        alert_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alert_icon.setStyleSheet(f"background: {Palette.BRAND_PRIMARY}; color: white; border-radius: 8px; font-family: 'Georgia'; font-style: italic; font-weight: bold; font-size: 10px; border: none;")
        al_l.addWidget(alert_icon)
        
        self.alert_top = QLabel("ends in")
        self.alert_top.setStyleSheet(f"font-size: 11px; color: {Palette.TEXT_SECONDARY}; font-weight: 600; border: none; background: transparent;")
        self.alert_bot = QLabel("00:00")
        self.alert_bot.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 13px; font-weight: 800; color: {Palette.BRAND_PRIMARY}; border: none; background: transparent;")
        
        al_l.addWidget(self.alert_top)
        al_l.addWidget(self.alert_bot)
        al_l.addStretch()
        
        task_info.addWidget(self.active_task)
        task_info.addLayout(badges)
        task_info.addStretch()
        task_info.addWidget(self.alert_banner)
        
        top_split.addLayout(task_info, 1)
        
        # Right: Timer & Ring
        timer_container = QVBoxLayout()
        timer_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        ring_box = QWidget()
        ring_box.setFixedSize(180, 180)
        
        self.progress_ring = ProgressRing(ring_box)
        self.progress_ring.setFixedSize(180, 180)
        self.progress_ring.set_colors(Palette.BRAND_PRIMARY, Palette.SURFACE_DARK)
        
        timer_overlay = QVBoxLayout(ring_box)
        timer_overlay.setContentsMargins(0, 0, 0, 0)
        timer_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_overlay.setSpacing(0)
        
        self.active_timer = QLabel("00:00")
        self.active_timer.setObjectName("timer_display")
        self.active_timer.setStyleSheet(f"font-size: 42px; font-weight: 800; color: {Palette.TEXT_PRIMARY}; letter-spacing: -2px; border: none; background: transparent;")
        
        rem_l = QLabel("REMAINING")
        rem_l.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 9px; font-weight: 800; color: {Palette.TEXT_MUTED}; letter-spacing: 1px; border: none; background: transparent;")
        
        timer_overlay.addWidget(self.active_timer, alignment=Qt.AlignmentFlag.AlignCenter)
        timer_overlay.addWidget(rem_l, alignment=Qt.AlignmentFlag.AlignCenter)
        
        timer_container.addWidget(ring_box)
        top_split.addLayout(timer_container)
        
        content_v.addLayout(top_split)
        
        # Bottom Stats Bar
        stats_bar = QFrame()
        stats_bar.setObjectName("active_stats_bar")
        stats_bar.setStyleSheet(f"QFrame#active_stats_bar {{ background: {Palette.SURFACE_DARK}; border-bottom-left-radius: 24px; border-bottom-right-radius: 24px; border: none; }}")
        stats_bar.setFixedHeight(80)
        self.stat_row = QHBoxLayout(stats_bar)
        self.stat_row.setContentsMargins(32, 0, 32, 0)
        self.stat_row.setSpacing(0)
        
        self.stat_labels = {}
        stat_keys = ["elapsed", "breaks taken", "snoozed", "snooze passes"]
        for i, key in enumerate(stat_keys):
            v = QVBoxLayout()
            v.setSpacing(2)
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            val = QLabel("00:00" if "elapsed" in key else "0")
            val.setStyleSheet(f"font-family: 'JetBrains Mono'; font-weight: 700; font-size: 20px; color: {Palette.TEXT_PRIMARY}; border: none; background: transparent;")
            
            lab = QLabel(key.upper())
            lab.setStyleSheet(f"font-size: 9px; color: {Palette.TEXT_MUTED}; font-weight: 800; letter-spacing: 0.5px; border: none; background: transparent;")
            
            v.addWidget(val); v.addWidget(lab)
            self.stat_row.addLayout(v)
            self.stat_labels[key] = val
            
            if i < len(stat_keys) - 1:
                sep = QFrame()
                sep.setFixedSize(1, 30)
                sep.setStyleSheet(f"background: {Palette.BORDER_DEFAULT}; border: none;")
                self.stat_row.addWidget(sep)
        
        acl.addLayout(content_v)
        acl.addWidget(stats_bar)
        
        # Empty state for no active session
        self.active_empty = QFrame()
        self.active_empty.setObjectName("active_session_empty")
        self.active_empty.setMinimumHeight(200)
        empty_l = QVBoxLayout(self.active_empty)
        empty_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_l.setSpacing(12)
        
        empty_icon = QLabel("⏳")
        empty_icon.setStyleSheet("font-size: 48px; margin-bottom: 8px;")
        empty_l.addWidget(empty_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        
        empty_msg = QLabel("No Active Session")
        empty_msg.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {Palette.TEXT_PRIMARY};")
        empty_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_hint = QLabel("Ready to get things done? Start a session.")
        empty_hint.setStyleSheet(f"font-size: 14px; color: {Palette.TEXT_SECONDARY};")
        empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        start_btn = QPushButton("Start Focusing")
        start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        start_btn.setFixedSize(160, 40)
        start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Palette.BRAND_PRIMARY};
                color: white;
                border-radius: 20px;
                font-weight: 700;
                font-size: 13px;
                margin-top: 10px;
            }}
            QPushButton:hover {{
                background-color: {Palette.BRAND_SECONDARY};
            }}
        """)
        start_btn.clicked.connect(self._on_new_task)
        
        empty_l.addWidget(empty_msg)
        empty_l.addWidget(empty_hint)
        empty_l.addWidget(start_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        l.addWidget(self.active_card)
        l.addWidget(self.active_empty)
        
        # Section 2: Streaks
        l.addWidget(SectionHeader("Streaks"))
        streaks_l = QHBoxLayout()
        streaks_l.setSpacing(16)
        self.streak_session = StreakCard("🔥", "Session streak", 0, 0, tip="How many sessions you've\ndone in a row.")
        self.streak_perfect = StreakCard("⭐", "Perfect streak", 0, 0, tip="Sessions where you\ntook every single break.")
        self.streak_daily = StreakCard("📅", "Day consistency", 0, 0, tip="How many days in a\nrow you've used the app.")
        streaks_l.addWidget(self.streak_session); streaks_l.addWidget(self.streak_perfect); streaks_l.addWidget(self.streak_daily)
        l.addLayout(streaks_l)
        
        # Section 3: Achievements
        ach_head = SectionHeader("Achievements", "View all →")
        ach_head.btn.clicked.connect(self._show_achievements)
        l.addWidget(ach_head)
        ach_card = QFrame()
        ach_card.setObjectName("card")
        ach_card_l = QVBoxLayout(ach_card)
        ach_card_l.setContentsMargins(24, 24, 24, 24)
        ach_card_l.setSpacing(16)
        self.ach_unlocked_lbl = QLabel("0 of 20 unlocked")
        self.ach_unlocked_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 11px; font-weight: 700; color: {Palette.TEXT_MUTED};")
        ach_card_l.addWidget(self.ach_unlocked_lbl)
        self.ach_strip = QHBoxLayout()
        self.ach_strip.setSpacing(12)
        ach_card_l.addLayout(self.ach_strip)
        l.addWidget(ach_card)
        
        # Section 4: Quick Stats
        qs_head = SectionHeader("Quick Stats", "View all →")
        qs_head.btn.clicked.connect(lambda: self.switcher._on_clicked("analytics"))
        l.addWidget(qs_head)
        qs_l = QHBoxLayout()
        qs_l.setSpacing(16)
        self.qs_total = QuickStatCard("0", "Total sessions", tip="Total sessions you've\never started.")
        self.qs_hours = QuickStatCard("0h", "Total work time", tip="Total time you've\nspent focusing.")
        self.qs_comp = QuickStatCard("0%", "Break compliance", tip="How good you are\nat taking your breaks.")
        self.qs_qual = QuickStatCard("0.0", "Avg quality", tip="Your overall score\nfor focus discipline.")
        qs_l.addWidget(self.qs_total); qs_l.addWidget(self.qs_hours); qs_l.addWidget(self.qs_comp); qs_l.addWidget(self.qs_qual)
        l.addLayout(qs_l)
        
        l.addStretch()
        scroll.setWidget(content)
        return scroll

    def _init_history(self) -> QWidget:
        page = QWidget()
        l = QVBoxLayout(page)
        l.setContentsMargins(60, 40, 60, 60)
        l.setSpacing(24)
        
        # Header with title and count
        head = QHBoxLayout()
        t = QLabel("Session history")
        t.setObjectName("section_label")
        head.addWidget(t)
        self.hist_count = QLabel("0 sessions")
        self.hist_count.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 11px; color: {Palette.TEXT_MUTED};")
        head.addStretch()
        head.addWidget(self.hist_count)
        l.addLayout(head)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)
        
        # Search input
        self.hist_search = QLineEdit()
        self.hist_search.setPlaceholderText("Search by task name...")
        self.hist_search.setMaximumWidth(250)
        self.hist_search.setStyleSheet(f"""
            QLineEdit {{
                background: {Palette.SURFACE_WHITE};
                border: 1px solid {Palette.SURFACE_DARK};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
            }}
            QLineEdit:focus {{ border: 1px solid {Palette.BRAND_PRIMARY}; }}
        """)
        self.hist_search.textChanged.connect(self._on_history_filter_changed)
        filter_layout.addWidget(self.hist_search)
        
        # Mode filter
        self.hist_mode_filter = QComboBox()
        self.hist_mode_filter.addItems(["All Modes", "Normal", "Strict", "Focused"])
        self.hist_mode_filter.setMaximumWidth(150)
        self.hist_mode_filter.setStyleSheet(f"""
            QComboBox {{
                background: {Palette.SURFACE_WHITE};
                border: 1px solid {Palette.SURFACE_DARK};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                color: {Palette.TEXT_PRIMARY};
                font-weight: 500;
            }}
            QComboBox:focus {{ border: 1px solid {Palette.BRAND_PRIMARY}; }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 4px;
            }}
            QAbstractItemView {{
                background: {Palette.SURFACE_WHITE};
                border: 1px solid {Palette.BORDER_DEFAULT};
                border-radius: 4px;
                color: {Palette.TEXT_PRIMARY};
                selection-background-color: {Palette.BRAND_LIGHT};
                selection-color: {Palette.BRAND_PRIMARY};
                outline: none;
            }}
            QAbstractItemView::item:hover {{
                background: {Palette.SURFACE_DARK};
            }}
        """)
        self.hist_mode_filter.currentTextChanged.connect(self._on_history_filter_changed)
        filter_layout.addWidget(self.hist_mode_filter)
        
        # Sort option
        self.hist_sort = QComboBox()
        self.hist_sort.addItems(["Newest First", "Oldest First", "Longest Duration", "Highest Score"])
        self.hist_sort.setMaximumWidth(150)
        self.hist_sort.setStyleSheet(f"""
            QComboBox {{
                background: {Palette.SURFACE_WHITE};
                border: 1px solid {Palette.SURFACE_DARK};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                color: {Palette.TEXT_PRIMARY};
                font-weight: 500;
            }}
            QComboBox:focus {{ border: 1px solid {Palette.BRAND_PRIMARY}; }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 4px;
            }}
            QAbstractItemView {{
                background: {Palette.SURFACE_WHITE};
                border: 1px solid {Palette.BORDER_DEFAULT};
                border-radius: 4px;
                color: {Palette.TEXT_PRIMARY};
                selection-background-color: {Palette.BRAND_LIGHT};
                selection-color: {Palette.BRAND_PRIMARY};
                outline: none;
            }}
            QAbstractItemView::item:hover {{
                background: {Palette.SURFACE_DARK};
            }}
        """)
        self.hist_sort.currentTextChanged.connect(self._on_history_filter_changed)
        filter_layout.addWidget(self.hist_sort)
        
        filter_layout.addStretch()

        # Import/Export buttons
        btn_style = f"""
            QPushButton {{
                background: {Palette.SURFACE_WHITE};
                border: 1px solid {Palette.SURFACE_DARK};
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 11px;
                font-weight: 700;
                color: {Palette.TEXT_SECONDARY};
            }}
            QPushButton:hover {{ background: {Palette.SURFACE_DARK}; color: {Palette.TEXT_PRIMARY}; }}
        """
        self.btn_export = QPushButton("Export CSV")
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.setStyleSheet(btn_style)
        self.btn_export.clicked.connect(self._on_export_history)
        
        filter_layout.addWidget(self.btn_export)
        
        l.addLayout(filter_layout)
        
        # Column headers
        cols = QHBoxLayout()
        cols.setContentsMargins(40, 0, 16, 0)
        for txt, w in [("Task", 0), ("Taken", 60), ("Snoozed", 60), ("Skipped", 60), ("Score", 60)]:
            lbl = QLabel(txt)
            lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {Palette.TEXT_MUTED};")
            if w == 0: cols.addWidget(lbl, 1)
            else: lbl.setFixedWidth(w); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter if txt != "Score" else Qt.AlignmentFlag.AlignRight); cols.addWidget(lbl)
        l.addLayout(cols)
        
        # Scrollable session list
        self.hist_scroll = QScrollArea()
        self.hist_scroll.setWidgetResizable(True)
        self.hist_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.hist_container = QWidget()
        self.hist_list = QVBoxLayout(self.hist_container)
        self.hist_list.setContentsMargins(0, 0, 0, 0)
        self.hist_list.setSpacing(10)
        self.hist_list.addStretch()
        self.hist_scroll.setWidget(self.hist_container)
        l.addWidget(self.hist_scroll)
        return page

    def _refresh_dashboard(self):
        settings = self.db.get_settings()
        self.greet_title.setText(f"Good morning, {settings.username}!")
        
        # Streaks
        streaks = self.db.get_streaks()
        s_sess = streaks.get("session_streak")
        if s_sess:
            self.streak_session.val_lbl.setText(str(s_sess.current_count))
            self.streak_session.best_lbl.setText(f"best: {s_sess.best_count}")
        
        s_perf = streaks.get("perfect_session")
        if s_perf:
            self.streak_perfect.val_lbl.setText(str(s_perf.current_count))
            self.streak_perfect.best_lbl.setText(f"best: {s_perf.best_count}")
        
        s_day = streaks.get("daily_consistency")
        if s_day:
            self.streak_daily.val_lbl.setText(str(s_day.current_count))
            self.streak_daily.best_lbl.setText(f"best: {s_day.best_count}")
        
        # Quick Stats
        stats = self.db.get_stats() or {}
        self.qs_total.v.setText(str(stats.get("total_sessions", 0)))
        self.qs_hours.v.setText(f"{stats.get('total_hours', 0)}h")
        self.qs_comp.v.setText(f"{stats.get('break_compliance', 0)}%")
        self.qs_qual.v.setText(str(round(stats.get('avg_quality', 0.0), 2)))
        
        # Active Card
        active = self.session_mgr.session is not None
        self.active_card.setVisible(active)
        self.active_empty.setVisible(not active)
        if active and self.session_mgr.session:
            s = self.session_mgr.session
            self.active_task.setText(s.task_name)
            self.active_mode.setText(s.mode.upper())
            # Color indicator based on mode
            if s.mode == "strict": border_color = Palette.MODE_STRICT_BORDER
            elif s.mode == "focused": border_color = Palette.MODE_FOCUS_BORDER
            else: border_color = Palette.MODE_NORMAL_BORDER
            
            self.active_card.setStyleSheet(f"""
                QFrame#active_session_card {{
                    background-color: {Palette.SURFACE_WHITE};
                    border-radius: 20px;
                    border: 1px solid {Palette.SURFACE_DARK};
                    border-top: 5px solid {border_color};
                }}
            """)
            
        # History
        self._refresh_history()
        
        # Achievements Strip
        while self.ach_strip.count():
            item = self.ach_strip.takeAt(0)
            widget = item.widget() if item else None
            if widget: widget.deleteLater()
        
        from focusbreaker.ui.achievements_modal import get_achievements_config
        ach_stats = self.db.get_achievement_stats() or {}
        if not isinstance(ach_stats, dict):
            ach_stats = {}
       
        # Ensure required keys exist so the achievements config builder doesn't KeyError
        for k in ['sessions','daily_streak','perfect_sessions','consecutive_perfect','strict_sessions','focused_sessions','modes_used','hours','total_breaks','no_exit_sessions']:
            if k not in ach_stats:
                ach_stats[k] = 0
        ach_data = get_achievements_config(ach_stats)
        
        unlocked_count = 0
        added = 0
        for ach in ach_data:
            if ach["cur"] >= ach["target"]:
                unlocked_count += 1
                if added < 5:
                    self.ach_strip.addWidget(AchievementBadgeTile(ach["name"], ach["icon"], locked=False))
                    added += 1
        
        locked_added = 0
        for ach in ach_data:
            if ach["cur"] < ach["target"] and locked_added < 3:
                self.ach_strip.addWidget(AchievementBadgeTile(ach["name"], ach["icon"], locked=True))
                locked_added += 1
                
        self.ach_unlocked_lbl.setText(f"{unlocked_count} of {len(ach_data)} unlocked")
        self.ach_strip.addStretch()

    def _refresh_history(self):
        """Refresh history with current filters applied."""
        while self.hist_list.count() > 1:
            item = self.hist_list.takeAt(0)
            widget = item.widget() if item else None
            if widget: widget.deleteLater()
        
        # Get all sessions (no limit)
        all_sessions = self.db.get_all_sessions(limit=None)
        
        # Apply filters
        search_term = self.hist_search.text().lower()
        mode_filter = self.hist_mode_filter.currentText()
        sort_option = self.hist_sort.currentText()
        
        filtered_sessions = all_sessions
        
        # Filter by search term
        if search_term:
            filtered_sessions = [s for s in filtered_sessions if search_term in s.task_name.lower()]
        
        # Filter by mode
        if mode_filter != "All Modes":
            mode_filter_lower = mode_filter.lower()
            filtered_sessions = [s for s in filtered_sessions if s.mode.lower() == mode_filter_lower]
        
        # Sort
        if sort_option == "Newest First":
            filtered_sessions.sort(key=lambda s: s.start_time, reverse=True)
        elif sort_option == "Oldest First":
            filtered_sessions.sort(key=lambda s: s.start_time)
        elif sort_option == "Longest Duration":
            filtered_sessions.sort(key=lambda s: s.actual_duration_minutes, reverse=True)
        elif sort_option == "Highest Score":
            filtered_sessions.sort(key=lambda s: s.quality_score, reverse=True)
        
        # Display
        self.hist_count.setText(f"{len(filtered_sessions)} sessions")
        
        if not filtered_sessions:
            empty_container = QWidget()
            empty_l = QVBoxLayout(empty_container)
            empty_l.setContentsMargins(0, 100, 0, 100)
            empty_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_l.setSpacing(16)
            
            empty_icon = QLabel("📜")
            empty_icon.setStyleSheet("font-size: 48px;")
            empty_l.addWidget(empty_icon, alignment=Qt.AlignmentFlag.AlignCenter)
            
            empty_msg = QLabel("Your history is empty")
            empty_msg.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {Palette.TEXT_SECONDARY};")
            empty_l.addWidget(empty_msg, alignment=Qt.AlignmentFlag.AlignCenter)
            
            empty_hint = QLabel("Complete sessions to see them listed here.")
            empty_hint.setStyleSheet(f"font-size: 13px; color: {Palette.TEXT_MUTED};")
            empty_l.addWidget(empty_hint, alignment=Qt.AlignmentFlag.AlignCenter)
            
            start_btn = QPushButton("Start Your First Session")
            start_btn.setFixedSize(200, 44)
            start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            start_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Palette.BRAND_PRIMARY};
                    color: white;
                    border-radius: 22px;
                    font-weight: 700;
                    font-size: 13px;
                    margin-top: 10px;
                }}
                QPushButton:hover {{
                    background-color: {Palette.BRAND_SECONDARY};
                }}
            """)
            start_btn.clicked.connect(self._on_new_task)
            empty_l.addWidget(start_btn, alignment=Qt.AlignmentFlag.AlignCenter)
            
            self.hist_list.insertWidget(0, empty_container)
        else:
            for s in filtered_sessions:
                self.hist_list.insertWidget(self.hist_list.count()-1, HistoryRow(s))
    
    def _on_history_filter_changed(self):
        """Called when any filter changes."""
        self._refresh_history()

    def _navigate(self, key):
        idx = {"home": 0, "analytics": 2, "history": 1, "settings": 3}.get(key, 0)
        
        # Ensure data is fresh when switching to Analytics or History
        if idx == 2:
            try:
                self.analytics_page.refresh_data()
            except Exception:
                pass
        elif idx == 1:
            try:
                self._refresh_history()
            except Exception:
                pass
            
        self.stack.setCurrentIndex(idx)

    def _on_tick(self, elapsed, remaining):
        self.active_timer.setText(fmt_time(remaining))
        total = self.session_mgr.session.planned_duration_minutes * 60 if self.session_mgr.session else 1
        progress_val = elapsed / total
        if hasattr(self, 'progress_ring'):
            self.progress_ring.value = progress_val

        self.stat_labels["elapsed"].setText(fmt_time(elapsed))
        if self.session_mgr.session:
            s = self.session_mgr.session
            self.stat_labels["breaks taken"].setText(str(s.breaks_taken))
            self.stat_labels["snoozed"].setText(str(s.breaks_snoozed))
            self.stat_labels["snooze passes"].setText(str(s.snooze_passes_remaining))
            next_brk = self.session_mgr.get_next_break_seconds()
            
            if s.mode == "focused":
                alert_t = "no breaks until"
                alert_b = "SESSION ENDS"
            else:
                if next_brk: 
                    alert_t = "next break in"
                    alert_b = f"{fmt_time(next_brk)}"
                else: 
                    alert_t = "session ends in"
                    alert_b = f"{fmt_time(remaining)}"
            
            self.alert_top.setText(alert_t)
            self.alert_bot.setText(alert_b)
            
            if self.floating_window:
                self.floating_window.update_status(
                    s.task_name,
                    remaining,
                    next_brk,
                    total,
                    s.mode
                )

    def _on_break_due(self, brk):
        """Show break window when break is due."""
        import logging
        logger = logging.getLogger("FocusBreaker")
        logger.info(f"_on_break_due called for break: offset={brk.scheduled_offset_minutes}min, duration={brk.duration_minutes}min")
        
        # Minimize main window instead of full hide to ensure break window visibility
        # Some window managers have issues showing new windows when everything is hidden
        self.showMinimized()
        
        # Notify user that break is starting
        mode = 'normal'
        if self.session_mgr.session:
            mode = self.session_mgr.session.mode
        
        if mode in ["normal", "strict"]:
            self.tray.notify("Break Time", "Take a break now! A break window is opening.", duration_ms=3000)
        
        try:
            # Get current streak count for the break window
            streaks = self.db.get_streaks()
            streak_count = streaks.get("session_streak").current_count if streaks.get("session_streak") else 0
            
            # Load media for the break window
            media_info = MediaManager.get_random_media(mode)
            
            # Create and show break window based on mode (parent=None for top-level)
            settings = self.db.get_settings()
            if mode == "strict":
                break_window = StrictBreakWindow(brk, mode, media_info=media_info, audio_mgr=self.audio, display_mgr=self.display, settings=settings)
            elif mode == "focused":
                # FocusEndBreakWindow needs session duration, quality score, and task name
                session_duration = self.session_mgr.session.planned_duration_minutes if self.session_mgr.session else 60
                quality_score = self.session_mgr.session.quality_score if self.session_mgr.session else 1.0
                task_name = self.session_mgr.session.task_name if self.session_mgr.session else "Unknown"
                break_window = FocusEndBreakWindow(
                    session_duration=session_duration,
                    mode=mode,
                    media_info=media_info,
                    quality_score=quality_score,
                    task_name=task_name,
                    audio_mgr=self.audio,
                    display_mgr=self.display,
                    settings=settings,
                    rest_duration=brk.duration_minutes
                )
            else:  # normal mode
                break_window = NormalBreakWindow(brk, mode, media_info=media_info, streak_count=streak_count, audio_mgr=self.audio, display_mgr=self.display)
            
            break_window.action_taken.connect(self._on_break_action)
            
            # Now hide to tray fully if needed, but show break window first
            # We use a single shot timer to hide after the break window has definitely appeared
            QTimer.singleShot(500, self.hide)
            
            break_window.exec()
        except Exception as e:
            logger.error(f"Error showing break window: {e}", exc_info=True)
            # Show main window again if there's an error
            self.showNormal()
            self.raise_()
            self.activateWindow()
            # Show main window again if there's an error
            self.showNormal()

    def _on_warning_emitted(self, message: str):
        """Handle warning messages from session manager."""
        # Show tray notification for break warnings
        if "Break in" in message and (self.session_mgr.session and self.session_mgr.session.mode in ["normal", "strict"]):
            self.tray.notify("Break Upcoming", message, duration_ms=5000)

    def _on_session_started(self, session):
        """Notify when a session starts."""
        mode_clean = session.mode.capitalize()
        self.tray.notify("Session Started", f'"{session.task_name}" in {mode_clean} mode', duration_ms=4000)
        
        try:
            if hasattr(self, 'stack'):
                self.stack.setCurrentIndex(0)
                if hasattr(self, 'switcher'):
                    self.switcher.set_active("home")
        except Exception:
            pass
        
        self._refresh_dashboard()
        
        # Show Floating Mini Window
        if not self.floating_window:
            self.floating_window = FloatingSessionWindow(None) # Top level
            self.floating_window.close_requested.connect(self._close_floating)
            
        self.floating_window.show()
        
        # Hide main window immediately
        self.hide()

    def _close_floating(self):
        if self.floating_window:
            self.floating_window.hide()

    def _on_session_complete(self, session, milestones):
        if self.floating_window:
            self.floating_window.close()
            self.floating_window = None
            
        # Ensure we are visible to show completion
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_break_action(self, action: str):
        """Handle break window action."""
        import logging
        logger = logging.getLogger("FocusBreaker")
        
        try:
            self.session_mgr.handle_break_action(action)
        except Exception as e:
            logger.error(f"Error handling break action '{action}': {e}", exc_info=True)
        
        # Keep the main window hidden while the active session continues.
        # But if the action was 'emergency_exit' or 'taken' at the very end, 
        # the session might be finished, so we check first.
        if self.session_mgr.is_active:
            self.hide()
        else:
            # If session ended, bring window to front
            self.showNormal()
            self.raise_()
            self.activateWindow()

        try:
            # Send notifications based on action
            if action == "taken":
                self.tray.notify("Break Done", "Your break is complete.", duration_ms=4000)
            elif action == "snoozed":
                self.tray.notify("Break Snoozed", "Your snooze pass has been used.", duration_ms=4000)
            elif action == "skipped":
                self.tray.notify("Break Skipped", "Your streak has been affected.", duration_ms=4000)
            elif action == "emergency_exit":
                self.tray.notify("Emergency Exit", "Emergency exit used — perfect streak affected.", duration_ms=5000)
        except Exception as e:
            logger.error(f"Error sending notification for action '{action}': {e}", exc_info=True)
        
        # Main window stays hidden during active session - it will be shown when session ends

    def _on_session_complete(self, session, milestones):
        logger.info(f"MainWindow: Handling session completion for '{getattr(session, 'task_name', 'Unknown')}'")
        
        # Show main window when session completes - Be aggressive to bring it to front
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.show()
        self.raise_()
        self.activateWindow()
        
        # 1. Refresh all content simultaneously with safety
        try:
            self._refresh_dashboard() # Refreshes Home and History
        except Exception as e:
            logger.error(f"Error refreshing dashboard on completion: {e}")

        try:
            if hasattr(self, 'analytics_page'):
                self.analytics_page.refresh_data()
        except Exception as e:
            logger.error(f"Error refreshing analytics on completion: {e}")
            
        # 2. Show Celebratory Success Modal (replaces tray notification)
        try:
            logger.info("MainWindow: Showing SessionCompleteModal")
            modal = SessionCompleteModal(session, milestones, self)
            modal.exec()
        except Exception as e:
            logger.error(f"FATAL UI ERROR: Failed to show completion modal: {e}", exc_info=True)
            # Fallback to tray if modal fails
            self.tray.notify("Session Complete", f'"{getattr(session, "task_name", "Task")}" completed!')

    def _on_session_finished_normal(self, session):
        self.session_mgr.complete_session()

    def _on_new_task(self):
        dlg = TaskDialog(self.db, self)
        if dlg.exec():
            task = dlg.get_task()
            session_data = dlg.get_session_data()
            if not isinstance(session_data, dict):
                session_data = {}
            if task:
                # If a session is already active, confirm overwrite/end before starting new
                if self.session_mgr.is_active:
                    conf = ThemedConfirmDialog("Replace Session?", "A session is already running. Do you want to end the current session and start a new one?", self)
                    if conf.exec():
                        # End existing session (mark as abandoned) before starting new
                        try:
                            self.session_mgr.stop_session(status='abandoned')
                        except Exception:
                            pass
                    else:
                        # User chose not to replace; abort
                        return
                # Prefer explicit duration from session data; fallback to task.allocated_time_minutes
                try:
                    duration = int(session_data.get('duration', task.allocated_time_minutes))
                except Exception:
                    try:
                        duration = int(task.allocated_time_minutes)
                    except Exception:
                        duration = 60
                if hasattr(self, 'stack'):
                    self.stack.setCurrentIndex(0)
                self.session_mgr.start_session(task.name, duration, task.mode, task)
                # Minimize window to tray when session starts
                self.hide()
        self._refresh_dashboard()

    def _open_settings(self):
        """Open settings as a modal dialog."""
        self.settings_dialog = SettingsPage(self.db, self)
        self.settings_dialog.exec()

    def _show_achievements(self):
        modal = AchievementsModal(self.db, self)
        modal.exec()

    def _toggle_max(self):
        if self.isMaximized(): self.showNormal()
        else: self.showMaximized()

    def _on_export_history(self):
        import csv
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "Export History", "focusbreaker_history.csv", "CSV Files (*.csv)")
        if not path: return
        
        sessions = self.db.get_all_sessions(limit=None)
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Task Name", "Mode", "Start Time", "End Time", "Planned Min", "Actual Min", "Status", "Breaks Taken", "Breaks Snoozed", "Breaks Skipped", "Quality Score"])
                for s in sessions:
                    writer.writerow([s.id, s.task_name, s.mode, s.start_time, s.end_time, s.planned_duration_minutes, s.actual_duration_minutes, s.status, s.breaks_taken, s.breaks_snoozed, s.breaks_skipped, s.quality_score])
            from focusbreaker.ui.components.dialogs import ThemedMessageDialog
            ThemedMessageDialog("Export Complete", f"Successfully exported {len(sessions)} sessions to {path}", self).exec()
        except Exception as e:
            from focusbreaker.ui.components.dialogs import ThemedMessageDialog
            ThemedMessageDialog("Export Failed", f"An error occurred: {e}", self).exec()

    def _on_import_history(self):
        import csv
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Import History", "", "CSV Files (*.csv)")
        if not path: return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    # Very basic import logic - could be enhanced with validation
                    # Note: ID is ignored to prevent collisions
                    from focusbreaker.data.models import WorkSession
                    s = WorkSession(
                        task_name=row.get("Task Name", "Imported"),
                        mode=row.get("Mode", "normal"),
                        start_time=row.get("Start Time"),
                        end_time=row.get("End Time"),
                        planned_duration_minutes=int(row.get("Planned Min", 0)),
                        actual_duration_minutes=int(row.get("Actual Min", 0)),
                        status=row.get("Status", "completed"),
                        breaks_taken=int(row.get("Breaks Taken", 0)),
                        breaks_snoozed=int(row.get("Breaks Snoozed", 0)),
                        breaks_skipped=int(row.get("Breaks Skipped", 0)),
                        quality_score=float(row.get("Quality Score", 1.0))
                    )
                    # Use internal DB method if available or just raw SQL
                    self.db.cursor.execute("""
                        INSERT INTO work_sessions (task_name, mode, start_time, end_time, planned_duration_minutes, actual_duration_minutes, status, breaks_taken, breaks_snoozed, breaks_skipped, quality_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (s.task_name, s.mode, s.start_time, s.end_time, s.planned_duration_minutes, s.actual_duration_minutes, s.status, s.breaks_taken, s.breaks_snoozed, s.breaks_skipped, s.quality_score))
                    count += 1
                self.db.conn.commit()
            self._on_history_filter_changed() # Refresh UI
            from focusbreaker.ui.components.dialogs import ThemedMessageDialog
            ThemedMessageDialog("Import Complete", f"Successfully imported {count} sessions. Your history has been updated.", self).exec()
        except Exception as e:
            from focusbreaker.ui.components.dialogs import ThemedMessageDialog
            ThemedMessageDialog("Import Failed", f"An error occurred during import: {e}", self).exec()

    def _reposition_fab(self):
        self.fab.move(self.width() - 100, self.height() - 100)

    # Note: resize handling for FAB is implemented later; hamburger removed.

    def _on_show_window(self):
        """Show the window from tray."""
        self.showNormal()
        self.raise_()
        self.activateWindow()
    
    def _on_quit_requested(self):
        """Actually quit the application (from tray menu)."""
        # Hide tray before quitting
        if self.tray:
            self.tray.tray_icon.hide()
        # Quit the application
        QApplication.quit()
    
    def _on_new_task_tray(self):
        """Create new task from tray menu."""
        self._on_new_task()
    
    def _on_settings_tray(self):
        """Open settings from tray menu."""
        self._open_settings()
    
    def _on_status_changed(self, status: str):
        """Handle session status changes and update tray menu."""
        self._refresh_dashboard()
        is_active = self.session_mgr.is_active if self.session_mgr else False
        self.tray.update_session_state(is_active)
    
    def _on_end_session_tray(self):
        """End session from tray menu."""
        if self.session_mgr and self.session_mgr.session:
            dlg = ThemedConfirmDialog(
                "End Session",
                "Are you sure you want to end the current session?",
                parent=self
            )
            if dlg.exec():
                self.session_mgr.stop_session("ended_by_user")
    def closeEvent(self, event: QCloseEvent):
        """Handle window close - always minimize to tray (app runs in background)."""
        # Per spec: FocusBreaker is a background tray application
        # Closing the window should NOT exit the app, only hide it to tray
        self.hide()
        
        # Show first close notification (one time only)
        settings = self.db.get_settings()
        if not settings.first_close_notified:
            self.tray.notify(
                "FocusBreaker",
                "FocusBreaker is still running in the background.\nUse the tray icon to access it.",
                duration_ms=7000
            )
            settings.first_close_notified = True
            self.db.save_settings(settings)
        
        event.ignore()  # Don't close the app, just hide the window
    
    def changeEvent(self, event):
        """Handle window state changes."""
        if event.type() == QEvent.Type.WindowStateChange:
            # Note: We no longer auto-hide to tray on minimize per user request.
            # Standard taskbar minimization is now the default behavior.
            pass
        super().changeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_fab()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
    def show_dim(self, show: bool):
        """Toggle the window-level dimming overlay for modals."""
        if show:
            self.dim_overlay.show()
            self.dim_overlay.raise_()
        else:
            self.dim_overlay.hide()

    def eventFilter(self, obj, event):
        if obj == self.main_shell and event.type() == QEvent.Type.Resize:
            if hasattr(self, 'dim_overlay'):
                self.dim_overlay.resize(self.main_shell.size())
        elif obj == self.active_card and event.type() == QEvent.Type.MouseButtonRelease:
            if self.floating_window:
                self.floating_window.show()
                self.floating_window.raise_()
                self.floating_window.activateWindow()
        return super().eventFilter(obj, event)

