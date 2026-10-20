"""
Break Window Implementation — All Three Modes
Implements Normal, Strict, and Focus break windows with split layouts, animations, and quality scoring.

Stack: Python 3.10+, PySide6 (Qt), SQLite3
"""

import random
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QFrame, QProgressBar, QStackedWidget, QGraphicsOpacityEffect,
    QGraphicsDropShadowEffect
)
import logging
logger = logging.getLogger(__name__)
from PySide6.QtCore import Qt, QTimer, Signal, QUrl, QPoint, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup
from PySide6.QtGui import QFont, QScreen, QGuiApplication, QPixmap, QMouseEvent, QColor, QPainter, QBrush, QPen
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget

from focusbreaker.config import Colors, MODES, UIConfig, Palette
from focusbreaker.core.timer import fmt_time
from focusbreaker.data.models import Break
from focusbreaker.core.escape_hatch import EscapeHatch

# ── Theme System ──────────────────────────────────────────────

class BreakTheme:
    """Color themes for break windows."""
    SCARY = {
        "bg": "#0F0F12",
        "side_bg": "#08080A",
        "accent": "#FF4444",
        "text": "#FFFFFF",
        "muted": "rgba(255, 255, 255, 0.4)",
        "card_bg": "rgba(255, 68, 68, 0.1)",
        "card_border": "#FF4444"
    }
    
    VIBRANT_THEMES = [
        # Teal / Mint
        {"bg": "#F2EDE3", "side_bg": "#FFFFFF", "accent": "#1B7F79", "text": "#1E2D2C", "muted": "#6B8886", "card_bg": "#E1F5F3", "card_border": "#1B7F79"},
        # Purple / Lavender
        {"bg": "#F5F3F9", "side_bg": "#FFFFFF", "accent": "#7C4DFF", "text": "#2D1E40", "muted": "#866B88", "card_bg": "#F0E1F5", "card_border": "#7C4DFF"},
        # Blue / Ocean
        {"bg": "#F3F7F9", "side_bg": "#FFFFFF", "accent": "#0D47A1", "text": "#1E242D", "muted": "#6B7688", "card_bg": "#E1EBF5", "card_border": "#0D47A1"},
        # Amber / Warm
        {"bg": "#F9F7F3", "side_bg": "#FFFFFF", "accent": "#E65100", "text": "#2D261E", "muted": "#887A6B", "card_bg": "#F5E9E1", "card_border": "#E65100"},
        # Emerald / Calm
        {"bg": "#F3F9F4", "side_bg": "#FFFFFF", "accent": "#1B5E20", "text": "#1E2D1F", "muted": "#6B886C", "card_bg": "#E1F5E3", "card_border": "#1B5E20"}
    ]

    @staticmethod
    def get_theme(mode: str, media_name: str = "") -> dict:
        scary_keywords = ["scary", "horror", "jumpscare", "dark", "ghost", "scream"]
        is_scary = any(k in media_name.lower() for k in scary_keywords) or mode in ["strict"]
        
        if is_scary:
            return BreakTheme.SCARY
        return random.choice(BreakTheme.VIBRANT_THEMES)

# ── Activity Tips ──────────────────────────────────────────────

BREAK_TIPS = [
    "Stretch your neck and shoulders.",
    "Look 20 feet away for 20 seconds.",
    "Take 3 deep, mindful breaths.",
    "Drink a glass of water.",
    "Stand up and do a quick stretch.",
    "Rest your eyes—blink slowly.",
    "Roll your wrists and ankles.",
    "Gently massage your temples.",
    "Clench and release your fists.",
    "Do a quick seated spinal twist."
]

class TipSlideshow(QFrame):
    """Slideshow for recommended activities during a break."""
    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setObjectName("tip_container")
        self.setFixedHeight(85)
        self.setStyleSheet(f"""
            QFrame#tip_container {{
                background: {theme['card_bg']};
                border: 1px dashed {theme['card_border']};
                border-radius: 12px;
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        head = QLabel("TIP")
        head.setStyleSheet(f"font-size: 9px; font-weight: 800; color: {theme['accent']}; letter-spacing: 2px;")
        layout.addWidget(head)
        
        self.tip_lbl = QLabel(random.choice(BREAK_TIPS))
        self.tip_lbl.setWordWrap(True)
        self.tip_lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {theme['text']}; line-height: 130%;")
        layout.addWidget(self.tip_lbl)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_tip)
        self.timer.start(8000)

    def next_tip(self):
        current = self.tip_lbl.text()
        options = [t for t in BREAK_TIPS if t != current]
        self.tip_lbl.setText(random.choice(options))

# ── Shared Components ──────────────────────────────────────────


class MediaContainer(QWidget):
    """Displays image or video with fallback placeholder."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(True)
        self.stack.addWidget(self.image_label)
        
        # Video display
        self.video_widget = QVideoWidget()
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.stack.addWidget(self.video_widget)
        
        # Fallback placeholder
        self.placeholder = QLabel()
        self.placeholder.setText("▶\nMEDIA PLAYING")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: rgba(255,255,255,0.2); font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif; font-size: 14px;")
        self.stack.addWidget(self.placeholder)
        
        # Show placeholder by default
        self._show_placeholder()

    def set_image(self, pixmap: QPixmap):
        self.image_label.setPixmap(pixmap)
        self.stack.setCurrentIndex(0)
        self.media_player.stop()

    def set_video(self, video_path: str):
        self.media_player.setSource(QUrl.fromLocalFile(video_path))
        self.stack.setCurrentIndex(1)
        self.media_player.play()
        self.media_player.setLoops(QMediaPlayer.Loops.Infinite)

    def _show_placeholder(self):
        self.stack.setCurrentIndex(2)
        self.media_player.stop()

    def stop(self):
        self.media_player.stop()


# ── Progress Strip ──────────────────────────────────────────


class CustomProgressStrip(QWidget):
    """3-4px progress strip with direction support."""
    def __init__(self, parent=None, direction="left_to_right", color="#17A696"):
        super().__init__(parent)
        self.direction = direction
        self.color = color
        self.value = 0
        self.maximum = 100
        self.setFixedHeight(3)
        
    def set_value(self, val):
        self.value = val
        self.update()
    
    def set_maximum(self, max_val):
        self.maximum = max_val
    
    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Calculate fill width
        fill_ratio = min(1.0, self.value / max(1, self.maximum))
        fill_width = int(self.width() * fill_ratio)
        
        # Draw fill
        if self.direction == "right_to_left":
            fill_x = self.width() - fill_width
        else:
            fill_x = 0
        
        painter.fillRect(fill_x, 0, fill_width, self.height(), QColor(self.color))


# ── Normal Break Window ──────────────────────────────────────────


class NormalBreakWindow(QDialog):
    """Refined popup for breaks with dynamic theme support."""
    action_taken = Signal(str)
    
    def __init__(self, brk: Break, mode: str, media_info=None, streak_count=0, audio_mgr=None, display_mgr=None, parent=None):
        super().__init__(parent)
        self.brk = brk
        self.mode = mode
        self.media_info = media_info or {}
        self.theme = BreakTheme.get_theme(mode, self.media_info.get('name', ''))
        
        self.total_secs = brk.duration_minutes * 60
        self._elapsed = 0
        self._streak_count = streak_count
        self.snooze_passes_remaining = 3
        self._drag_pos = None
        self.audio_mgr = audio_mgr
        self.display_mgr = display_mgr
        self._is_taken = False
        self._is_complete = False
        
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(820, 640) # Extra room for shadows and smooth edges
        self._center()
        self._setup_ui()
        self._load_media()
        self._trigger_audio_and_brightness()
        self._start_timer()
        self._setup_animations()

    def _center(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen.center() - self.rect().center())

    def _trigger_audio_and_brightness(self):
        if self.audio_mgr:
            try:
                self.audio_mgr.play_alarm()
                self.audio_mgr.play_surprise(mode=self.mode)
            except: pass
        if self.display_mgr:
            try:
                self.display_mgr.boost_brightness(level=95)
            except: pass

    def _load_media(self):
        path = self.media_info.get('path')
        if not path: return
        if self.media_info.get('type') == 'image':
            self.media_container.set_image(QPixmap(path))
        else:
            self.media_container.set_video(path)

    def _setup_animations(self):
        """Initialize animation effects for streak badge glow."""
        self.glow_effect = QGraphicsDropShadowEffect()
        self.glow_effect.setBlurRadius(20)
        self.glow_effect.setColor(QColor(self.theme['accent']))

    def _setup_ui(self):
        # Translucent full-window dialog with centered compact shell
        self.setStyleSheet("background: transparent; border: none;")
        
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        # 1. Dimmed backdrop - Centered container
        self.backdrop = QFrame()
        self.backdrop.setObjectName("break_backdrop")
        self.backdrop.setStyleSheet("QFrame#break_backdrop { background-color: transparent; border: none; }")
        root.addWidget(self.backdrop)
        
        main_l = QVBoxLayout(self.backdrop)
        main_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_l.setContentsMargins(40, 40, 40, 40) # Space for shadow to breathe
        
        # 2. Main Shell
        self.shell = QFrame()
        self.shell.setObjectName("window_shell")
        self.shell.setFixedSize(740, 560)
        self.shell.setStyleSheet(f"""
            QFrame#window_shell {{
                background-color: {self.theme['bg']};
                border-radius: 24px;
                border: 1px solid {self.theme['card_border']};
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60); shadow.setXOffset(0); shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.shell.setGraphicsEffect(shadow)
        main_l.addWidget(self.shell)

        layout = QHBoxLayout(self.shell)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ── Media Pane ──
        media_pane = QVBoxLayout()
        media_pane.setContentsMargins(0, 0, 0, 0)
        self.media_container = MediaContainer()
        self.media_container.setStyleSheet(f"background: #000; border-top-left-radius: 24px; border-bottom-left-radius: 24px; border: none;")
        media_pane.addWidget(self.media_container, 1)
        
        self.progress_strip = CustomProgressStrip(color=self.theme['accent'])
        media_pane.addWidget(self.progress_strip)
        layout.addLayout(media_pane, 1)
        
        # ── Side Pane ──
        self.side_pane = QFrame()
        self.side_pane.setFixedWidth(260)
        self.side_pane.setStyleSheet(f"background: {self.theme['side_bg']}; border-top-right-radius: 24px; border-bottom-right-radius: 24px; border: none;")
        sl = QVBoxLayout(self.side_pane)
        sl.setContentsMargins(24, 32, 24, 32)
        sl.setSpacing(16)
        
        mode_lbl = QLabel(self.mode.upper() + " BREAK")
        mode_lbl.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {self.theme['muted']}; letter-spacing: 2px; border: none;")
        sl.addWidget(mode_lbl)
        
        title = QLabel("Time to Rest")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {self.theme['text']}; border: none;")
        sl.addWidget(title)
        
        # Streak Card
        self.streak_box = QFrame()
        self.streak_box.setObjectName("streak_card")
        self.streak_box.setStyleSheet(f"""
            QFrame#streak_card {{
                background-color: {self.theme['card_bg']};
                border: 1.5px solid {self.theme['card_border']};
                border-radius: 16px;
            }}
        """)
        sbl = QHBoxLayout(self.streak_box)
        sbl.setContentsMargins(16, 12, 16, 12)
        
        st_num = QLabel(f"🔥 {getattr(self, '_streak_count', 0)}")
        st_num.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {self.theme['text']}; background: transparent; border: none;")
        sbl.addWidget(st_num)
        
        sbl.addStretch()
        
        st_lab = QLabel("STREAK")
        st_lab.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {self.theme['muted']}; background: transparent; border: none; letter-spacing: 1px;")
        sbl.addWidget(st_lab)
        sl.addWidget(self.streak_box)
        
        sl.addStretch()
        
        # Timer
        self.timer_lbl = QLabel(fmt_time(self.total_secs))
        self.timer_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 42px; font-weight: 800; color: {self.theme['accent']}; letter-spacing: -2px; border: none;")
        sl.addWidget(self.timer_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        rem_lbl = QLabel("REMAINING")
        rem_lbl.setStyleSheet(f"font-size: 9px; font-weight: 800; color: {self.theme['muted']}; border: none;")
        sl.addWidget(rem_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        sl.addSpacing(16)
        
        # Snooze Passes
        pass_l = QHBoxLayout(); pass_l.setSpacing(8); pass_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pass_dots = []
        for _ in range(3):
            d = QFrame(); d.setFixedSize(10, 10); d.setStyleSheet(f"background: {self.theme['accent']}; border-radius: 5px; border: none;")
            pass_l.addWidget(d); self.pass_dots.append(d)
        sl.addLayout(pass_l)
        
        sl.addSpacing(16)
        
        # Activity Tip (Initially hidden until 'TAKE' clicked)
        self.tip_box = TipSlideshow(self.theme)
        self.tip_box.hide()
        sl.addWidget(self.tip_box)
        
        sl.addStretch()
        
        # Action Buttons
        self.take_btn = QPushButton("TAKE")
        self.take_btn.setFixedHeight(48)
        self.take_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.take_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border-radius: 24px;
                font-weight: 800;
                font-size: 13px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {self.theme['text']};
            }}
        """)
        self.take_btn.clicked.connect(self._on_take_break)
        sl.addWidget(self.take_btn)
        
        self.snooze_btn = QPushButton("SNOOZE")
        self.snooze_btn.setFixedHeight(40)
        self.snooze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.snooze_btn.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid {self.theme['card_border']};
                color: {self.theme['accent']};
                border-radius: 20px;
                font-weight: 700;
                font-size: 12px;
                background: transparent;
            }}
            QPushButton:hover {{
                background: {self.theme['card_bg']};
            }}
        """)
        self.snooze_btn.clicked.connect(self._on_snooze_clicked)
        sl.addWidget(self.snooze_btn)
        
        self.skip_btn = QPushButton("SKIP")
        self.skip_btn.setStyleSheet(f"color: {self.theme['muted']}; font-weight: 700; font-size: 11px; background: transparent; border: none; padding: 10px;")
        self.skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.skip_btn.clicked.connect(self._on_skip_clicked)
        sl.addWidget(self.skip_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.side_pane)
        self._update_pass_dots()

    def _start_streak_glow(self):
        """Start pulsing glow animation on streak badge."""
        if hasattr(self, '_glow_anim') and self._glow_anim:
            return
            
        self.streak_box.setGraphicsEffect(self.glow_effect)
        
        self._glow_anim = QPropertyAnimation(self.glow_effect, b"color")
        self._glow_anim.setDuration(1500)
        self._glow_anim.setStartValue(QColor(self.theme['accent']))
        self._glow_anim.setEndValue(QColor(self.theme['text']))
        self._glow_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._glow_anim.setLoopCount(-1)
        self._glow_anim.start()
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            
            # Constrain movement within visible screen space
            screen = QGuiApplication.primaryScreen().availableGeometry()
            
            # Left/Right bounds
            x = max(screen.left(), min(new_pos.x(), screen.right() - self.width()))
            # Top/Bottom bounds
            y = max(screen.top(), min(new_pos.y(), screen.bottom() - self.height()))
            
            self.move(x, y)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None

    def _start_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)

    def _update_pass_dots(self):
        """Update pass dots display based on remaining snooze passes."""
        for i, dot in enumerate(self.pass_dots):
            opacity = 1.0 if i < self.snooze_passes_remaining else 0.2
            dot.setStyleSheet(f"background: {self.theme['accent']}; border-radius: 5px; opacity: {opacity};")
            
        self.snooze_btn.setEnabled(self.snooze_passes_remaining > 0)

    def _tick(self):
        self._elapsed += 1
        remaining = max(0, self.total_secs - self._elapsed)
        self.timer_lbl.setText(fmt_time(remaining))
        
        progress_val = int((remaining / self.total_secs) * 100)
        self.progress_strip.set_value(progress_val)
        
        if remaining < 30 and remaining > 0:
            self._start_streak_glow()
        
        if remaining <= 0:
            self._show_complete_state()

    def _show_complete_state(self):
        logger.info("NormalBreakWindow: Break timer finished. Showing complete state.")
        self._is_complete = True
        self.timer.stop()
        self.media_container.stop()
        
        # Simple feedback in side pane
        self.timer_lbl.setText("RESTED")
        self.timer_lbl.setStyleSheet(f"font-size: 32px; font-weight: 800; color: {self.theme['accent']};")
        self.take_btn.setText("RESUME WORK")
        self.take_btn.show() 
        self.snooze_btn.hide()
        self.skip_btn.hide()
        
        # Auto-finish after 5 seconds if no interaction
        QTimer.singleShot(5000, self._auto_finish)

    def _auto_finish(self):
        if self._is_complete:
            self._finish("taken")

    def _on_take_break(self):
        """User commits to the break. Hide take button, show tips, but window stays."""
        if self._is_complete:
            self._finish("taken")
            return
            
        self._is_taken = True
        self.take_btn.hide()
        self.tip_box.show()

    def _on_snooze_clicked(self):
        self._show_snooze_confirmation()

    def _on_snooze_confirmed(self):
        if self.snooze_passes_remaining > 0:
            self.snooze_passes_remaining -= 1
            self._update_pass_dots()
        self._finish("snoozed")

    def _on_skip_clicked(self):
        self._show_skip_confirmation()

    def _show_snooze_confirmation(self):
        # Using global confirm dialog for consistency
        from focusbreaker.ui.components.dialogs import ThemedConfirmDialog
        dlg = ThemedConfirmDialog("Snooze Break?", "Postpone for 5 minutes? This costs 1 snooze pass.", self)
        if dlg.exec():
            self._on_snooze_confirmed()

    def _show_skip_confirmation(self):
        from focusbreaker.ui.components.dialogs import ThemedConfirmDialog
        dlg = ThemedConfirmDialog("Skip Break?", "Skipping will end your streak and reduce your quality score.", self, danger=True)
        if dlg.exec():
            self._finish("skipped")

    def _finish(self, action):
        logger.info(f"NormalBreakWindow: Finishing with action='{action}'")
        self.timer.stop()
        self.media_container.stop()
        self.action_taken.emit(action)
        self.accept()

    def closeEvent(self, event):
        if self.display_mgr:
            try: self.display_mgr.restore_brightness()
            except: pass
        event.ignore()


# ── Strict Break Window ──────────────────────────────────────────


class StrictBreakWindow(QDialog):
    """Full-screen enforced break with the 'scary' dark theme."""
    action_taken = Signal(str)
    
    def __init__(self, brk: Break, mode: str, media_info=None, audio_mgr=None, display_mgr=None, parent=None, settings=None):
        super().__init__(parent)
        self.settings = settings
        self.brk = brk
        self.mode = mode
        self.media_info = media_info or {}
        self.theme = BreakTheme.SCARY
        
        self.audio_mgr = audio_mgr
        self.display_mgr = display_mgr
        self.total_secs = brk.duration_minutes * 60
        self._elapsed = 0
        
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.showFullScreen()
        self._setup_ui()
        self._load_media()
        self._trigger_audio_and_brightness()
        self._setup_recording_animation()
        self._setup_escape_hatch()
        self._start_timer()

    def _setup_recording_animation(self):
        self.recording_timer = QTimer(self)
        self.recording_timer.timeout.connect(self._update_recording)
        self.recording_timer.start(50)
        self._rec_alpha = 255
        self._rec_dir = -5

    def _update_recording(self):
        self._rec_alpha += self._rec_dir
        if self._rec_alpha <= 50 or self._rec_alpha >= 255: self._rec_dir *= -1
        self.rec_dot.setStyleSheet(f"background: rgba(255, 68, 68, {self._rec_alpha}); border-radius: 4px;")

    def _trigger_audio_and_brightness(self):
        if self.audio_mgr:
            try:
                self.audio_mgr.play_alarm()
                self.audio_mgr.play_surprise(mode=self.mode)
            except: pass
        if self.display_mgr:
            try: self.display_mgr.boost_brightness(level=100)
            except: pass

    def _load_media(self):
        path = self.media_info.get('path')
        if not path: return
        if self.media_info.get('type') == 'image':
            self.media_container.set_image(QPixmap(path))
        else: self.media_container.set_video(path)

    def _setup_ui(self):
        self.setStyleSheet("QDialog { background: transparent; }")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        # Backdrop
        self.backdrop = QFrame()
        self.backdrop.setObjectName("strict_backdrop")
        self.backdrop.setStyleSheet(f"QFrame#strict_backdrop {{ background-color: {self.theme['bg']}; border: none; }}")
        root.addWidget(self.backdrop)
        
        main_l = QHBoxLayout(self.backdrop)
        main_l.setContentsMargins(0, 0, 0, 0)
        main_l.setSpacing(0)
        
        # Media Pane
        media_pane = QVBoxLayout()
        media_pane.setContentsMargins(0, 0, 0, 0)
        self.media_container = MediaContainer()
        self.media_container.setStyleSheet("background: #000; border: none;")
        media_pane.addWidget(self.media_container, 1)
        self.progress_strip = CustomProgressStrip(direction="right_to_left", color=self.theme['accent'])
        media_pane.addWidget(self.progress_strip)
        main_l.addLayout(media_pane, 1)
        
        # Side Pane
        side = QFrame()
        side.setFixedWidth(240)
        side.setStyleSheet(f"background: {self.theme['side_bg']}; border: none;")
        sl = QVBoxLayout(side)
        sl.setContentsMargins(24, 40, 24, 40)
        sl.setSpacing(20)
        
        rec_l = QHBoxLayout()
        rec_l.setContentsMargins(0, 0, 0, 0)
        self.rec_dot = QFrame(); self.rec_dot.setFixedSize(8, 8)
        rec_l.addWidget(self.rec_dot)
        rec_txt = QLabel("ENFORCED BREAK"); rec_txt.setStyleSheet(f"color: {self.theme['accent']}; font-size: 10px; font-weight: 800; letter-spacing: 1px; border: none;")
        rec_l.addWidget(rec_txt); rec_l.addStretch()
        sl.addLayout(rec_l)
        
        sl.addStretch()
        self.timer_lbl = QLabel(fmt_time(self.total_secs))
        self.timer_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 48px; font-weight: 800; color: white; border: none;")
        sl.addWidget(self.timer_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        rem_lbl = QLabel("REMAINING")
        rem_lbl.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {self.theme['muted']}; border: none;")
        sl.addWidget(rem_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        sl.addStretch()
        
        # Activity Tip Slideshow
        self.tips = TipSlideshow(self.theme, self)
        sl.addWidget(self.tips)
        
        sl.addStretch()
        
        notice = QLabel("SESSIONS ARE LOCKED\nUNTIL REST COMPLETE")
        notice.setStyleSheet(f"color: {self.theme['muted']}; font-size: 11px; font-weight: 700; text-align: center; border: none;")
        sl.addWidget(notice, alignment=Qt.AlignmentFlag.AlignCenter)
        
        sl.addStretch()
        
        self.escape_label = QLabel("EMERGENCY EXIT")
        self.escape_label.setStyleSheet(f"font-size: 9px; font-weight: 800; color: {self.theme['muted']}; border: none;")
        sl.addWidget(self.escape_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.escape_progress = QProgressBar()
        self.escape_progress.setRange(0, 100); self.escape_progress.setValue(0); self.escape_progress.setFixedHeight(3)
        self.escape_progress.setTextVisible(False); self.escape_progress.setStyleSheet(f"QProgressBar {{ background: rgba(255,255,255,0.05); border: none; }} QProgressBar::chunk {{ background: {self.theme['accent']}; }}")
        self.escape_progress.hide()
        sl.addWidget(self.escape_progress)
        
        main_l.addWidget(side)

    def _setup_escape_hatch(self):
        if self.settings and not getattr(self.settings, 'escape_hatch_enabled', True):
            return
            
        combo = getattr(self.settings, 'escape_hatch_combo', "ctrl+alt+shift+e")
        duration = getattr(self.settings, 'escape_hatch_duration', 3.0)
            
        self.escape_hatch = EscapeHatch(combo=combo, hold_duration=duration, parent=self)
        self.escape_hatch.progress.connect(self._on_escape_progress)
        self.escape_hatch.triggered.connect(self._on_escape_triggered)
        self.escape_hatch.start_listening()

    def _on_escape_progress(self, val):
        if val > 0:
            self.escape_progress.show()
            self.escape_label.setText("HOLD TO EXIT")
            self.escape_label.setStyleSheet(f"color: {self.theme['accent']}; font-size: 9px; font-weight: 800;")
        self.escape_progress.setValue(int(val * 100))

    def _on_escape_triggered(self):
        self.timer.stop(); self.recording_timer.stop(); self.media_container.stop()
        self.escape_hatch.stop_listening()
        self.action_taken.emit("emergency_exit")
        self.accept()

    def _start_timer(self):
        self.timer = QTimer(self); self.timer.timeout.connect(self._tick); self.timer.start(1000)

    def _tick(self):
        self._elapsed += 1
        remaining = max(0, self.total_secs - self._elapsed)
        self.timer_lbl.setText(fmt_time(remaining))
        self.progress_strip.set_value(int((remaining/self.total_secs)*100))
        if remaining <= 0: self._finish_break()

    def _finish_break(self):
        self.timer.stop(); self.recording_timer.stop(); self.media_container.stop()
        if hasattr(self, 'escape_hatch'): self.escape_hatch.stop_listening()
        self.action_taken.emit("taken")
        self.accept()

    def closeEvent(self, event):
        if self.display_mgr:
            try: self.display_mgr.restore_brightness()
            except: pass
        event.ignore()

    def keyPressEvent(self, event): pass


# ── Focus End Break Window ──────────────────────────────────────────


class FocusEndBreakWindow(QDialog):
    """Full-screen summary and rest window with dynamic theme."""
    action_taken = Signal(str)
    
    def __init__(self, session_duration: int, mode: str = "focused", media_info=None, quality_score=1.0, task_name="", audio_mgr=None, display_mgr=None, parent=None, settings=None, rest_duration: int = 0):
        super().__init__(parent)
        self.settings = settings
        self.mode = mode
        self.media_info = media_info or {}
        self.theme = BreakTheme.SCARY
        
        self.audio_mgr = audio_mgr
        self.display_mgr = display_mgr
        self.session_duration = session_duration
        self.quality_score = quality_score
        self.task_name = task_name
        
        if rest_duration > 0:
            self.rest_duration = rest_duration
        else:
            if session_duration <= 120: self.rest_duration = 30
            elif session_duration <= 240: self.rest_duration = 45
            else: self.rest_duration = 60
        
        self.total_secs = self.rest_duration * 60
        self._elapsed = 0
        
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.showFullScreen()
        self._setup_ui()
        self._load_media()
        self._trigger_audio_and_brightness()
        self._setup_recording_animation()
        self._setup_escape_hatch()
        self._start_timer()

    def _setup_recording_animation(self):
        self.recording_timer = QTimer(self)
        self.recording_timer.timeout.connect(self._update_recording)
        self.recording_timer.start(50)
        self._rec_alpha = 255
        self._rec_dir = -5

    def _update_recording(self):
        self._rec_alpha += self._rec_dir
        if self._rec_alpha <= 50 or self._rec_alpha >= 255: self._rec_dir *= -1
        self.rec_dot.setStyleSheet(f"background: rgba(255, 68, 68, {self._rec_alpha}); border-radius: 4px;")

    def _load_media(self):
        path = self.media_info.get('path')
        if not path: return
        if self.media_info.get('type') == 'image': self.media_container.set_image(QPixmap(path))
        else: self.media_container.set_video(path)

    def _trigger_audio_and_brightness(self):
        if self.audio_mgr:
            try: self.audio_mgr.play_alarm(); self.audio_mgr.play_surprise(mode=self.mode)
            except: pass
        if self.display_mgr:
            try: self.display_mgr.boost_brightness(level=100)
            except: pass

    def _setup_ui(self):
        self.setStyleSheet("QDialog { background: transparent; }")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        # Backdrop
        self.backdrop = QFrame()
        self.backdrop.setObjectName("focus_backdrop")
        self.backdrop.setStyleSheet(f"QFrame#focus_backdrop {{ background-color: {self.theme['bg']}; border: none; }}")
        root.addWidget(self.backdrop)
        
        main_l = QHBoxLayout(self.backdrop)
        main_l.setContentsMargins(0, 0, 0, 0); main_l.setSpacing(0)
        
        # ── Media Pane (Left) ──
        media_pane = QVBoxLayout()
        media_pane.setContentsMargins(0, 0, 0, 0)
        self.media_container = MediaContainer()
        self.media_container.setStyleSheet("background: #000; border: none;")
        media_pane.addWidget(self.media_container, 1)
        
        self.progress_strip = CustomProgressStrip(direction="right_to_left", color=self.theme['accent'])
        media_pane.addWidget(self.progress_strip)
        main_l.addLayout(media_pane, 1)
        
        # ── Side Pane (Right) ──
        self.side_pane = QFrame()
        self.side_pane.setFixedWidth(240)
        self.side_pane.setStyleSheet(f"background: {self.theme['side_bg']}; border: none;")
        sl = QVBoxLayout(self.side_pane); sl.setContentsMargins(24, 40, 24, 40); sl.setSpacing(20)
        
        rec_l = QHBoxLayout()
        rec_l.setContentsMargins(0, 0, 0, 0)
        self.rec_dot = QFrame(); self.rec_dot.setFixedSize(8, 8)
        rec_l.addWidget(self.rec_dot)
        rec_txt = QLabel("FOCUS COMPLETE"); rec_txt.setStyleSheet(f"color: {self.theme['accent']}; font-size: 10px; font-weight: 800; letter-spacing: 1px; border: none;")
        rec_l.addWidget(rec_txt); rec_l.addStretch()
        sl.addLayout(rec_l)
        
        sl.addStretch()
        
        self.timer_lbl = QLabel(fmt_time(self.total_secs))
        self.timer_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 48px; font-weight: 800; color: white; border: none;")
        sl.addWidget(self.timer_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        rem_rest = QLabel("REMAINING REST")
        rem_rest.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {self.theme['muted']}; border: none;")
        sl.addWidget(rem_rest, alignment=Qt.AlignmentFlag.AlignCenter)
        
        sl.addStretch()
        
        # Summary Card (Small version to fit sidebar)
        qual_val = int(self.quality_score * 100)
        q_box = QFrame()
        q_box.setStyleSheet(f"background: {self.theme['card_bg']}; border: 1.5px solid {self.theme['card_border']}; border-radius: 12px; padding: 12px;")
        q_l = QVBoxLayout(q_box); q_l.setSpacing(4)
        q_t = QLabel(f"QUALITY: {qual_val}%")
        q_t.setStyleSheet(f"font-size: 10px; font-weight: 800; color: white; border: none;")
        q_l.addWidget(q_t)
        qp = QProgressBar(); qp.setRange(0, 100); qp.setValue(qual_val); qp.setFixedHeight(3); qp.setTextVisible(False)
        qp.setStyleSheet(f"QProgressBar {{ background: rgba(0,0,0,0.2); border: none; }} QProgressBar::chunk {{ background: {self.theme['accent']}; }}")
        q_l.addWidget(qp)
        sl.addWidget(q_box)
        
        sl.addStretch()
        
        # Activity Tip Slideshow
        self.tips = TipSlideshow(self.theme, self)
        sl.addWidget(self.tips)
        
        sl.addStretch()
        
        self.escape_label = QLabel("EMERGENCY EXIT")
        self.escape_label.setStyleSheet(f"font-size: 9px; font-weight: 800; color: {self.theme['muted']}; border: none;")
        sl.addWidget(self.escape_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.escape_progress = QProgressBar()
        self.escape_progress.setRange(0, 100); self.escape_progress.setValue(0); self.escape_progress.setFixedHeight(3); self.escape_progress.setTextVisible(False)
        self.escape_progress.setStyleSheet(f"QProgressBar {{ background: rgba(255,255,255,0.05); border: none; }} QProgressBar::chunk {{ background: {self.theme['accent']}; }}")
        self.escape_progress.hide()
        sl.addWidget(self.escape_progress)
        main_l.addWidget(self.side_pane)

    def _setup_escape_hatch(self):
        if self.settings and not getattr(self.settings, 'escape_hatch_enabled', True):
            return
            
        combo = getattr(self.settings, 'escape_hatch_combo', "ctrl+alt+shift+e")
        duration = getattr(self.settings, 'escape_hatch_duration', 3.0)
            
        self.escape_hatch = EscapeHatch(combo=combo, hold_duration=duration, parent=self)
        self.escape_hatch.progress.connect(self._on_escape_progress)
        self.escape_hatch.triggered.connect(self._on_escape_triggered)
        self.escape_hatch.start_listening()

    def _on_escape_progress(self, val):
        if val > 0: self.escape_progress.show()
        self.escape_progress.setValue(int(val * 100))

    def _on_escape_triggered(self):
        self.timer.stop(); self.recording_timer.stop(); self.media_container.stop()
        self.action_taken.emit("emergency_exit")
        self.accept()

    def _start_timer(self):
        self.timer = QTimer(self); self.timer.timeout.connect(self._tick); self.timer.start(1000)

    def _tick(self):
        self._elapsed += 1
        remaining = max(0, self.total_secs - self._elapsed)
        self.timer_lbl.setText(fmt_time(remaining))
        
        progress_val = int((remaining / self.total_secs) * 100) if self.total_secs > 0 else 0
        self.progress_strip.set_value(progress_val)
        
        if remaining <= 0: self._finish_rest()

    def _finish_rest(self):
        self.timer.stop(); self.recording_timer.stop(); self.media_container.stop()
        self.action_taken.emit("taken")
        self.accept()

    def closeEvent(self, event):
        if self.display_mgr:
            try: self.display_mgr.restore_brightness()
            except: pass
        event.ignore()

    def keyPressEvent(self, event): pass
