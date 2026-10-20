from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QPushButton, QFrame, QLineEdit, QScrollArea, QWidget, QStackedWidget,
    QFileDialog, QMessageBox, QCheckBox, QListWidget, QListWidgetItem,
    QGridLayout, QSizePolicy, QLayout, QBoxLayout, QSpacerItem, QDialog,
    QApplication,
    QProgressBar
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QTime, QPoint, QUrl
from PySide6.QtGui import QColor, QPixmap, QIcon, QKeySequence, QPainter, QBrush, QDesktopServices

from focusbreaker.config import UIConfig, AppPaths, MediaConfig, Palette
from focusbreaker.data.db import DBManager
from focusbreaker.data.models import Settings
from focusbreaker.system.media_manager import MediaManager
from focusbreaker.ui.components.dialogs import ThemedConfirmDialog, ThemedMessageDialog

def _section(title: str) -> QWidget:
    w = QWidget()
    l = QVBoxLayout(w)
    l.setContentsMargins(0, 20, 0, 8) # Add top margin for clear separation
    l.setSpacing(8)
    
    lbl = QLabel(title.upper())
    lbl.setObjectName("section_title")
    lbl.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {Palette.BRAND_PRIMARY}; letter-spacing: 2px;")
    l.addWidget(lbl)
    
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet(f"background-color: {Palette.SURFACE_DARK}; border: none;")
    l.addWidget(line)
    
    return w

class SettingsRow(QWidget):
    """A consistent setting row with label, widget, and optional subtitle."""
    def __init__(self, label: str, widget, parent=None, subtitle=""):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(6)
        
        content = QHBoxLayout()
        content.setSpacing(20)
        
        text_v = QVBoxLayout()
        text_v.setSpacing(2)
        self.lbl = QLabel(label)
        self.lbl.setStyleSheet(f"color: {Palette.TEXT_PRIMARY}; font-size: 14px; font-weight: 700;")
        text_v.addWidget(self.lbl)
        
        if subtitle:
            self.sub = QLabel(subtitle)
            self.sub.setStyleSheet(f"color: {Palette.TEXT_SECONDARY}; font-size: 12px; font-weight: 500; border: none; background: transparent;")
            self.sub.setWordWrap(True)
            text_v.addWidget(self.sub)
            
        content.addLayout(text_v, 1)
        
        self.widget = widget
        content.addWidget(self.widget)
        self.main_layout.addLayout(content)
        self.main_layout.addSpacing(16)

def _spinbox(min_val: int, max_val: int, val: int, suffix: str = " MIN") -> QSpinBox:
    sb = QSpinBox()
    sb.setRange(min_val, max_val)
    sb.setValue(val)
    sb.setSuffix(suffix.upper())
    sb.setFixedWidth(130)
    sb.setFixedHeight(40)
    return sb

class SlidingToggle(QWidget):
    """A professional sliding toggle switch (HCI standard)."""
    toggled = Signal(bool)

    def __init__(self, parent=None, active_color=Palette.BRAND_PRIMARY, bg_color=Palette.TEXT_MUTED):
        super().__init__(parent)
        self.setFixedSize(44, 24)
        self._checked = True
        self._active_color = active_color
        self._bg_color = bg_color
        self._knob_pos = 22 # Start at 'on' position
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self): return self._checked
    def setChecked(self, checked):
        self._checked = checked
        self._knob_pos = 22 if checked else 2
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            self._knob_pos = 22 if self._checked else 2
            self.toggled.emit(self._checked)
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        color = self._active_color if self._checked else self._bg_color
        p.setBrush(QBrush(QColor(color)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        
        p.setBrush(QBrush(QColor("white")))
        p.drawEllipse(self._knob_pos, 2, 20, 20)

class KeyCaptureModal(QDialog):
    """Modal for capturing a keyboard shortcut combination."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        self.current_keys = set()
        self.final_combo = ""
        
        self._setup_ui()
        
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        # Backdrop container with specific ID to prevent inheritance
        self.bg = QFrame()
        self.bg.setObjectName("key_capture_shell")
        self.bg.setStyleSheet(f"""
            QFrame#key_capture_shell {{ 
                background-color: {Palette.SURFACE_WHITE}; 
                border-radius: 20px; 
                border: 2px solid {Palette.BRAND_PRIMARY}; 
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        root.addWidget(self.bg)
        
        l = QVBoxLayout(self.bg)
        l.setContentsMargins(30, 30, 30, 30)
        l.setSpacing(20)
        
        title = QLabel("SET ESCAPE HATCH")
        title.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {Palette.TEXT_MUTED}; letter-spacing: 1.5px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(title)
        
        self.instruction = QLabel("Press your key combination...")
        self.instruction.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {Palette.TEXT_PRIMARY};")
        self.instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.instruction)
        
        self.combo_display = QLabel("---")
        self.combo_display.setStyleSheet(f"""
            background: {Palette.SURFACE_DARK}; 
            color: {Palette.BRAND_PRIMARY}; 
            font-family: 'JetBrains Mono'; 
            font-size: 20px; 
            font-weight: 800; 
            padding: 15px; 
            border-radius: 10px;
            border: none;
        """)
        self.combo_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.combo_display)
        
        self.hint = QLabel("Hold for 3 seconds to confirm")
        self.hint.setStyleSheet(f"font-size: 11px; color: {Palette.TEXT_SECONDARY};")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.hint)
        
        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 3000)
        self.progress.setValue(0)
        self.progress.setStyleSheet(f"""
            QProgressBar {{ background: {Palette.SURFACE_DARK}; border-radius: 3px; border: none; }}
            QProgressBar::chunk {{ background: {Palette.BRAND_PRIMARY}; border-radius: 3px; }}
        """)
        l.addWidget(self.progress)
        
        self.hold_timer = QTimer(self)
        self.hold_timer.setInterval(50)
        self.hold_timer.timeout.connect(self._on_hold_tick)
        self.hold_start_time = 0

    def keyPressEvent(self, event):
        if event.isAutoRepeat(): return
        
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.reject()
            return
            
        self.current_keys.add(key)
        self._update_display()
        
        if not self.hold_timer.isActive():
            self.hold_start_time = QTime.currentTime().msecsSinceStartOfDay()
            self.hold_timer.start()
            
    def keyReleaseEvent(self, event):
        if event.isAutoRepeat(): return
        self.current_keys.discard(event.key())
        self._update_display()
        
        if not self.current_keys:
            self.hold_timer.stop()
            self.progress.setValue(0)

    def _update_display(self):
        names = []
        # Sort to keep standard order: Modifiers then Keys
        mods = []
        others = []
        for k in self.current_keys:
            name = self._key_to_name(k)
            if name in ["CTRL", "ALT", "SHIFT", "META"]:
                mods.append(name)
            else:
                others.append(name)
        
        names = sorted(mods) + sorted(others)
        self.final_combo = "+".join(names)
        self.combo_display.setText(self.final_combo if self.final_combo else "---")

    def _on_hold_tick(self):
        if not self.current_keys: return
        
        elapsed = QTime.currentTime().msecsSinceStartOfDay() - self.hold_start_time
        self.progress.setValue(elapsed)
        
        if elapsed >= 3000:
            self.hold_timer.stop()
            self.accept()

    def _key_to_name(self, k):
        m = {
            Qt.Key.Key_Control: "CTRL", Qt.Key.Key_Alt: "ALT", 
            Qt.Key.Key_Shift: "SHIFT", Qt.Key.Key_Meta: "META",
            Qt.Key.Key_Return: "ENTER", Qt.Key.Key_Space: "SPACE"
        }
        if k in m: return m[k]
        return QKeySequence(k).toString().upper()

class SettingsPage(QDialog):
    """
    Redesigned Settings Modal Dialog
    Modern frameless implementation with custom tab switcher.
    """
    settings_saved = Signal()

    def __init__(self, db: DBManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.settings = db.get_settings()
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowModality(Qt.ApplicationModal)
        
        self.current_tab = "General"
        
        # Increase dimension if parent is maximized (by 1/4 more than previous 960x780)
        if parent and parent.isMaximized():
            self.setFixedSize(1200, 980)
        else:
            self.setFixedSize(820, 680)

        self._media_edit_mode = False
        self._selected_media = set()  # set of file paths
        self.media_grids = {}
        self.media_edit_btns = {} # mode -> button container

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
            QLineEdit {{
                background-color: white;
                border: 1.5px solid {Palette.BORDER_DEFAULT};
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                color: {Palette.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border: 1.5px solid {Palette.BRAND_PRIMARY};
            }}
            QSpinBox {{
                background-color: white;
                border: 1.5px solid {Palette.BORDER_DEFAULT};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 700;
                color: {Palette.TEXT_PRIMARY};
            }}
            QSpinBox:focus {{
                border: 1.5px solid {Palette.BRAND_PRIMARY};
            }}
            QCheckBox {{
                color: {Palette.TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 500;
                spacing: 12px;
                outline: none;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 6px;
                border: 2px solid {Palette.BORDER_DEFAULT};
                background-color: white;
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid {Palette.BRAND_PRIMARY};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Palette.BRAND_PRIMARY};
                border: 2px solid {Palette.BRAND_PRIMARY};
                image: url(assets/images/check_white.png);
            }}
        """)
        root.addWidget(self.container)

        l = QVBoxLayout(self.container)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setObjectName("settings_header")
        header.setStyleSheet(f"QFrame#settings_header {{ border-bottom: 1px solid {Palette.SURFACE_DARK}; }}")
        header.setFixedHeight(100)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(32, 0, 32, 0)
        
        title_v = QVBoxLayout()
        title_v.setSpacing(4)
        title_v.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        t_lbl = QLabel("Settings")
        t_lbl.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {Palette.TEXT_PRIMARY};")
        
        sub_lbl = QLabel("Tailor your focus experience")
        sub_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {Palette.TEXT_SECONDARY};")
        title_v.addWidget(t_lbl); title_v.addWidget(sub_lbl)
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
                color: {Palette.TEXT_SECONDARY}; 
                font-weight: 900; 
                font-size: 16px;
                font-family: 'Segoe UI';
            }} 
            QPushButton:hover {{ background: #FF5F57; color: white; }}
        """)
        close_btn.clicked.connect(self.reject)
        hl.addWidget(close_btn)
        l.addWidget(header)
        
        # Custom Tab Switcher
        tabs_container = QWidget()
        tabs_container.setFixedHeight(64)
        tabs_l = QHBoxLayout(tabs_container)
        tabs_l.setContentsMargins(32, 12, 32, 12)
        tabs_l.setSpacing(10)
        
        self.tab_btns = {}
        for name in ["General", "Focus Modes", "Media Library", "Emergency"]:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, n=name: self._switch_tab(n))
            tabs_l.addWidget(btn)
            self.tab_btns[name] = btn
            
        tabs_l.addStretch()
        l.addWidget(tabs_container)
        
        # Content Stack
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        
        self.stack.addWidget(self._scroll_wrap(self._general_tab()))
        self.stack.addWidget(self._scroll_wrap(self._timing_tab()))
        self.stack.addWidget(self._scroll_wrap(self._media_tab()))
        self.stack.addWidget(self._scroll_wrap(self._advanced_tab()))
        
        l.addWidget(self.stack, 1)
        
        # Footer
        footer = QFrame()
        footer.setFixedHeight(80)
        footer.setStyleSheet(f"border-top: 1px solid {Palette.SURFACE_DARK};")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(32, 0, 32, 0)
        fl.addStretch()
        
        save_btn = QPushButton("Save Preferences")
        save_btn.setFixedHeight(44)
        save_btn.setMinimumWidth(180)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Palette.BRAND_PRIMARY};
                color: white;
                border: none;
                border-radius: 22px;
                font-weight: 800;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {Palette.BRAND_SECONDARY};
            }}
        """)
        save_btn.clicked.connect(self._save)
        fl.addWidget(save_btn)
        
        l.addWidget(footer)
        self._switch_tab("General")

    def _switch_tab(self, name):
        self.current_tab = name
        idx = {"General": 0, "Focus Modes": 1, "Media Library": 2, "Emergency": 3}.get(name, 0)
        self.stack.setCurrentIndex(idx)
        
        for n, btn in self.tab_btns.items():
            is_active = (n == name)
            btn.setChecked(is_active)
            if is_active:
                btn.setStyleSheet(f"background: {Palette.BRAND_PRIMARY}; color: white; border-radius: 16px; padding: 0 20px; font-weight: 700; font-size: 12px;")
            else:
                btn.setStyleSheet(f"background: white; color: {Palette.TEXT_SECONDARY}; border: 1px solid {Palette.SURFACE_DARK}; border-radius: 16px; padding: 0 20px; font-weight: 600; font-size: 12px;")

    def _scroll_wrap(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setWidget(widget)
        return scroll

    def _general_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(32, 10, 32, 32)
        layout.setSpacing(24)
        
        layout.addWidget(_section("Profile Settings"))
        self.username_input = QLineEdit(getattr(self.settings, 'username', 'User'))
        self.username_input.setPlaceholderText("Enter your display name")
        self.username_input.setToolTip("Your name as it appears on the dashboard greeting.")
        layout.addWidget(self.username_input)
        
        layout.addSpacing(8)
        layout.addWidget(_section("Audio & Notifications"))
        self.media_vol = _spinbox(0, 100, getattr(self.settings, 'media_volume', 80), " %")
        layout.addWidget(SettingsRow("Media Playback Volume", self.media_vol, subtitle="Volume for background music and videos during breaks."))
        
        self.alarm_vol = _spinbox(0, 100, getattr(self.settings, 'alarm_volume', 70), " %")
        layout.addWidget(SettingsRow("Break Alarm Volume", self.alarm_vol, subtitle="Sound level for break and session ending alerts."))
        
        layout.addSpacing(8)
        layout.addWidget(_section("Visual Feedback"))
        self.bright_boost = _spinbox(0, 100, getattr(self.settings, 'brightness_boost', 0), " %")
        layout.addWidget(SettingsRow("Screen Brightness Dimming", self.bright_boost, subtitle="Dims your screen during strict sessions (if supported)."))
        
        layout.addStretch()
        return w

    def _timing_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(32, 10, 32, 32)
        layout.setSpacing(24)
        
        self._normal_work_interval = _spinbox(1, 480, self.settings.normal_work_interval)
        self._normal_break_duration = _spinbox(1, 480, self.settings.normal_break_duration)
        self._normal_snooze_duration = _spinbox(1, 480, self.settings.normal_snooze_duration)
        
        layout.addWidget(_section("Normal Focus Preferences"))
        layout.addWidget(SettingsRow("Work Window", self._normal_work_interval, subtitle="Active time before a break is triggered."))
        layout.addWidget(SettingsRow("Break Time", self._normal_break_duration, subtitle="Duration of standard rest periods."))
        layout.addWidget(SettingsRow("Snooze Time", self._normal_snooze_duration, subtitle="Delay added when you postpone a break."))
        
        layout.addSpacing(16)
        layout.addWidget(_section("Strict Focus Preferences"))
        self._strict_work_interval = _spinbox(1, 480, self.settings.strict_work_interval)
        self._strict_break_duration = _spinbox(1, 480, self.settings.strict_break_duration)
        self._strict_cooldown = _spinbox(1, 480, self.settings.strict_cooldown)
        
        layout.addWidget(SettingsRow("Work Window", self._strict_work_interval, subtitle="Mandatory high-intensity focus duration."))
        layout.addWidget(SettingsRow("Locked Break Time", self._strict_break_duration, subtitle="Forced break length (cannot be skipped)."))
        layout.addWidget(SettingsRow("Forced Rest After", self._strict_cooldown, subtitle="Mandatory downtime after completing a session."))
        
        layout.addSpacing(16)
        layout.addWidget(_section("Deep Work Preferences"))
        self._focused_mandatory_break = _spinbox(1, 480, self.settings.focused_mandatory_break)
        layout.addWidget(SettingsRow("Mandatory Post-Session Rest", self._focused_mandatory_break, subtitle="Required recovery period after deep-work sessions."))
        
        layout.addStretch()
        return w

    def _media_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(32, 10, 32, 32)
        layout.setSpacing(24)
        
    def _media_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(32, 10, 32, 32)
        layout.setSpacing(16)
        
        header_l = QHBoxLayout()
        header_l.addWidget(_section("Media Library"))
        header_l.addStretch()
        
        self.master_edit_btn = QPushButton("EDIT")
        self.master_edit_btn.setFixedSize(80, 30)
        self.master_edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.master_edit_btn.setStyleSheet(f"""
            QPushButton {{ 
                background: {Palette.SURFACE_DARK}; color: {Palette.TEXT_PRIMARY}; 
                border-radius: 15px; font-weight: 800; font-size: 10px;
            }}
            QPushButton:hover {{ background: {Palette.BORDER_DEFAULT}; }}
        """)
        self.master_edit_btn.clicked.connect(self._toggle_media_edit_mode)
        header_l.addWidget(self.master_edit_btn)
        layout.addLayout(header_l)

        from PySide6.QtWidgets import QTabWidget
        self.media_tabs = QTabWidget()
        self.media_tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {Palette.SURFACE_DARK}; border-radius: 16px; background: white; }}
            QTabBar::tab {{
                background: {Palette.SURFACE_DEFAULT};
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-weight: 700;
                color: {Palette.TEXT_SECONDARY};
            }}
            QTabBar::tab:selected {{
                background: white;
                color: {Palette.BRAND_PRIMARY};
                border: 1px solid {Palette.SURFACE_DARK};
                border-bottom: none;
            }}
        """)

        for mode in ["normal", "strict", "focused"]:
            page = QWidget()
            page_l = QVBoxLayout(page)
            page_l.setContentsMargins(20, 20, 20, 20)
            page_l.setSpacing(12)
            
            # Action Row (Dynamic based on Edit Mode)
            action_container = QWidget()
            actions = QHBoxLayout(action_container)
            actions.setContentsMargins(0, 0, 0, 0)
            
            # Default View Controls
            self.upload_btn = QPushButton("+ UPLOAD")
            self.upload_btn.setFixedSize(100, 32)
            self.upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.upload_btn.setStyleSheet(f"background: {Palette.BRAND_PRIMARY}; color: white; border-radius: 16px; font-weight: 800; font-size: 11px;")
            self.upload_btn.clicked.connect(lambda _, m=mode: self._on_upload_media(m))
            
            # Edit Mode Controls
            self.edit_controls = QWidget()
            ec_l = QHBoxLayout(self.edit_controls)
            ec_l.setContentsMargins(0, 0, 0, 0)
            ec_l.setSpacing(8)
            
            sel_all = QPushButton("SELECT ALL")
            sel_all.setStyleSheet(f"color: {Palette.BRAND_PRIMARY}; font-weight: 800; font-size: 10px; background: transparent; border: none;")
            sel_all.clicked.connect(lambda _, m=mode: self._select_all_media(m))
            
            del_sel = QPushButton("DELETE SELECTED")
            del_sel.setStyleSheet(f"color: #FF5F57; font-weight: 800; font-size: 10px; background: transparent; border: none;")
            del_sel.clicked.connect(lambda _, m=mode: self._delete_selected_media(m))
            
            ec_l.addWidget(sel_all)
            ec_l.addWidget(del_sel)
            ec_l.addStretch()
            
            self.edit_controls.setVisible(False)
            
            actions.addWidget(self.upload_btn)
            actions.addWidget(self.edit_controls)
            actions.addStretch()
            
            page_l.addWidget(action_container)
            
            # Save references to toggle
            self.media_edit_btns[mode] = (self.upload_btn, self.edit_controls)
            
            # Gallery Area
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setStyleSheet("background: transparent;")
            
            grid_container = QWidget()
            grid_container.setStyleSheet("background: transparent;")
            grid = QGridLayout(grid_container)
            grid.setSpacing(16)
            grid.setContentsMargins(0, 8, 0, 0)
            
            self.media_grids[mode] = grid
            self._populate_media_grid(mode)
            
            scroll.setWidget(grid_container)
            page_l.addWidget(scroll)
            
            self.media_tabs.addTab(page, mode.capitalize())

        layout.addWidget(self.media_tabs)
        return w

    def _populate_media_grid(self, mode):
        grid = self.media_grids[mode]
        # Clear existing
        while grid.count():
            item = grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        from focusbreaker.system.media_manager import MediaManager
        all_m = MediaManager.get_all_media(mode)
        
        if not all_m:
            empty = QLabel("No media found for this mode.")
            empty.setStyleSheet(f"color: {Palette.TEXT_MUTED}; font-size: 14px; font-weight: 600; padding: 40px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(empty, 0, 0)
            return

        cols = 3 if self.width() < 1000 else 4
        for i, m in enumerate(all_m):
            card = QFrame()
            card.setObjectName("media_card")
            card.setFixedSize(220, 180)
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            
            is_selected = m['path'] in self._selected_media
            border_c = Palette.BRAND_PRIMARY if is_selected else Palette.BORDER_DEFAULT
            bg_c = Palette.SURFACE_DEFAULT if is_selected else "white"
            
            card.setStyleSheet(f"""
                QFrame#media_card {{
                    background: {bg_c};
                    border: 2px solid {border_c};
                    border-radius: 14px;
                }}
                QFrame#media_card:hover {{ border-color: {Palette.BRAND_PRIMARY}; background: {Palette.SURFACE_DEFAULT}; }}
            """)
            
            # Click Behavior
            def on_card_click(e, path=m['path'], mo=mode):
                if self._media_edit_mode:
                    self._toggle_media_selection(path, mo)
                else:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(path)))
            card.mousePressEvent = on_card_click
            
            layout = QVBoxLayout(card)
            layout.setContentsMargins(1, 1, 1, 8)
            layout.setSpacing(6)
            
            # Preview Area
            preview = QLabel()
            preview.setFixedSize(216, 110)
            preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            preview.setStyleSheet("border-top-left-radius: 12px; border-top-right-radius: 12px; background: #e8e8e8; border: none;")
            
            import os
            m_abs_path = os.path.abspath(m['path'])
            if m['type'] == 'image':
                pix = QPixmap(m_abs_path)
                if not pix.isNull():
                    preview.setPixmap(pix.scaled(216, 110, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
                else:
                    preview.setText("🖼️\nLOAD ERROR")
                    preview.setStyleSheet("color: #999; font-size: 10px; font-weight: 800; background: #eee;")
            else:
                preview.setText("🎬\nVIDEO")
                preview.setStyleSheet("font-weight: 900; font-size: 16px; color: #777; border-top-left-radius: 12px; border-top-right-radius: 12px; background: #ddd;")
            
            # Selection Checkbox Overlay (Visual Only, card click handles it)
            if self._media_edit_mode:
                check_icon = QLabel(preview)
                check_icon.setFixedSize(24, 24)
                check_icon.move(184, 8)
                check_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if is_selected:
                    check_icon.setText("✓")
                    check_icon.setStyleSheet(f"background: {Palette.BRAND_PRIMARY}; color: white; border-radius: 12px; font-weight: 800; border: none;")
                else:
                    check_icon.setStyleSheet(f"background: rgba(255,255,255,0.7); border: 2px solid {Palette.TEXT_MUTED}; border-radius: 12px; border: none;")

            layout.addWidget(preview)
            
            info = QVBoxLayout()
            info.setContentsMargins(12, 4, 12, 4)
            info.setSpacing(4)
            
            name = QLabel(m['name'])
            name.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {Palette.TEXT_PRIMARY}; background: transparent; border: none;")
            name.setWordWrap(False)
            
            metrics = QHBoxLayout()
            type_tag = QLabel("USER" if m['is_user'] else "SYSTEM")
            type_tag.setStyleSheet(f"font-size: 8px; font-weight: 900; color: {'#2A9B93' if m['is_user'] else '#9AAEAC'}; background: transparent; border: none;")
            metrics.addWidget(type_tag)
            metrics.addStretch()
            
            info.addWidget(name)
            info.addLayout(metrics)
            layout.addLayout(info)
            
            grid.addWidget(card, i // cols, i % cols)
        
        # Add stretch to keep items at top
        if len(all_m) < cols:
            grid.setColumnStretch(cols - 1, 1)

    def _toggle_media_edit_mode(self):
        self._media_edit_mode = not self._media_edit_mode
        self.master_edit_btn.setText("CANCEL" if self._media_edit_mode else "EDIT")
        self.master_edit_btn.setStyleSheet(f"""
            QPushButton {{ 
                background: {Palette.BRAND_PRIMARY if self._media_edit_mode else Palette.SURFACE_DARK}; 
                color: {'white' if self._media_edit_mode else Palette.TEXT_PRIMARY}; 
                border-radius: 15px; font-weight: 800; font-size: 10px;
            }}
        """)
        
        if not self._media_edit_mode:
            self._selected_media.clear()
            
        # Update all grid views
        for mode, (up, ed) in self.media_edit_btns.items():
            up.setVisible(not self._media_edit_mode)
            ed.setVisible(self._media_edit_mode)
            self._populate_media_grid(mode)

    def _toggle_media_selection(self, path, mode):
        if path in self._selected_media:
            self._selected_media.remove(path)
        else:
            self._selected_media.add(path)
        self._populate_media_grid(mode)

    def _select_all_media(self, mode):
        from focusbreaker.system.media_manager import MediaManager
        all_m = MediaManager.get_all_media(mode)
        # Only select user media (optional, but usually users don't want to delete system media)
        # Actually, the user wants to "remove", and system media is protected in media_manager.
        for m in all_m:
            self._selected_media.add(m['path'])
        self._populate_media_grid(mode)

    def _delete_selected_media(self, mode):
        if not self._selected_media: return
        
        count = len(self._selected_media)
        dlg = ThemedConfirmDialog("Remove Media?", f"Are you sure you want to delete {count} selected item(s)? This cannot be undone.", self, danger=True)
        if dlg.exec():
            from focusbreaker.system.media_manager import MediaManager
            for path in list(self._selected_media):
                MediaManager.delete_user_media(path)
                self._selected_media.remove(path)
            
            # Exit edit mode after bulk delete
            self._toggle_media_edit_mode()
            self._populate_media_grid(mode)

    def _on_upload_media(self, mode):
        from PySide6.QtWidgets import QFileDialog
        from focusbreaker.config import MediaConfig
        filter_str = f"Media ({' '.join(['*' + f for f in MediaConfig.SUPPORTED_IMAGE_FORMATS | MediaConfig.SUPPORTED_VIDEO_FORMATS])})"
        files, _ = QFileDialog.getOpenFileNames(self, f"Upload Media for {mode.capitalize()}", "", filter_str)
        
        if files:
            from focusbreaker.system.media_manager import MediaManager
            for f in files:
                MediaManager.add_user_media(f, mode)
            self._populate_media_grid(mode)
            ThemedMessageDialog("Upload Complete", f"Successfully added {len(files)} items to your {mode} library.", self).exec()

    def _advanced_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(32, 10, 32, 32)
        layout.setSpacing(24)
        
        layout.addWidget(_section("Emergency Override System"))
        
        # Enable Toggle
        hce_layout = QHBoxLayout()
        self.hc_enabled_lbl = QLabel("Enable Keyboard Escape Hatch")
        self.hc_enabled_lbl.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.hc_toggle = SlidingToggle()
        self.hc_toggle.setChecked(getattr(self.settings, 'escape_hatch_enabled', True))
        self.hc_toggle.toggled.connect(self._on_escape_hatch_toggled)
        hce_layout.addWidget(self.hc_enabled_lbl); hce_layout.addStretch(); hce_layout.addWidget(self.hc_toggle)
        layout.addLayout(hce_layout)
        
        # Subtitle for toggle
        hce_sub = QLabel("Allow using a key combination to force-close break windows in emergencies.")
        hce_sub.setStyleSheet(f"color: {Palette.TEXT_SECONDARY}; font-size: 12px; font-weight: 500;")
        hce_sub.setWordWrap(True)
        layout.addWidget(hce_sub)
        
        # Combo Setup Row
        layout.addSpacing(8)
        self.combo_btn = QPushButton(getattr(self.settings, 'escape_hatch_combo', 'CTRL+ALT+SHIFT+E'))
        self.combo_btn.setFixedHeight(44)
        self.combo_btn.setMinimumWidth(200)
        self.combo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_btn.setStyleSheet(f"""
            QPushButton {{
                background: white;
                border: 2px solid {Palette.BORDER_DEFAULT};
                border-radius: 8px;
                color: {Palette.BRAND_PRIMARY};
                font-family: 'JetBrains Mono';
                font-weight: 800;
                font-size: 14px;
                padding: 0 16px;
            }}
            QPushButton:hover {{ border-color: {Palette.BRAND_PRIMARY}; }}
        """)
        self.combo_btn.clicked.connect(self._setup_key_combo)
        self.combo_row = SettingsRow("Override Key Sequence", self.combo_btn, subtitle="Click to re-record your emergency shortcut.")
        layout.addWidget(self.combo_row)
        
        self.hc_dur = _spinbox(1, 5, getattr(self.settings, 'escape_hatch_duration', 3), " SEC")
        self.dur_row = SettingsRow("Activation Hold Time", self.hc_dur, subtitle="Seconds you must hold the keys to override focus.")
        layout.addWidget(self.dur_row)
        
        # Initial state sync
        self._on_escape_hatch_toggled(self.hc_toggle.isChecked())
        
        layout.addSpacing(24)
        layout.addWidget(_section("Application Maintenance"))
        reset_btn = QPushButton("Reset App Data & History")
        reset_btn.setToolTip("Permanently delete all sessions, statistics, and reset your profile name and settings.")
        reset_btn.setFixedHeight(44)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1.5px solid #FF5F57;
                color: #FF5F57;
                border-radius: 8px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #FF5F57;
                color: white;
            }}
        """)
        reset_btn.clicked.connect(self._reset_all)
        layout.addWidget(reset_btn)
        
        layout.addStretch()
        return w

    def _setup_key_combo(self):
        dlg = KeyCaptureModal(self)
        if dlg.exec():
            new_combo = dlg.final_combo
            if new_combo:
                self.combo_btn.setText(new_combo)

    def _on_escape_hatch_toggled(self, enabled):
        self.combo_btn.setEnabled(enabled)
        self.hc_dur.setEnabled(enabled)
        # Visually dim the rows when disabled
        opacity = 1.0 if enabled else 0.5
        for row in [self.combo_row, self.dur_row]:
            row.setGraphicsEffect(None) # Clear previous
            if not enabled:
                from PySide6.QtWidgets import QGraphicsOpacityEffect
                eff = QGraphicsOpacityEffect()
                eff.setOpacity(opacity)
                row.setGraphicsEffect(eff)

    def _reset_all(self):
        dlg = ThemedConfirmDialog(
            "Wipe Data?", 
            "This will permanently delete all your work sessions, stats, and reset your name and settings. This cannot be undone.",
            parent=self,
            danger=True
        )
        if dlg.exec():
            self.db.reset_database()
            self.accept()

            app = QApplication.instance()
            if app is not None:
                QTimer.singleShot(0, lambda: app.exit(1000))

    def _save(self):
        s = self.settings
        s.username = self.username_input.text().strip() or "User"
        s.media_volume = self.media_vol.value()
        s.alarm_volume = self.alarm_vol.value()
        s.brightness_boost = self.bright_boost.value()
        
        s.normal_work_interval = self._normal_work_interval.value()
        s.normal_break_duration = self._normal_break_duration.value()
        s.normal_snooze_duration = self._normal_snooze_duration.value()
        s.strict_work_interval = self._strict_work_interval.value()
        s.strict_break_duration = self._strict_break_duration.value()
        s.strict_cooldown = self._strict_cooldown.value()
        s.focused_mandatory_break = self._focused_mandatory_break.value()
        
        s.escape_hatch_enabled = self.hc_toggle.isChecked()
        s.escape_hatch_combo = self.combo_btn.text().strip().upper()
        s.escape_hatch_duration = self.hc_dur.value()
        
        self.db.save_settings(s)
        self.settings_saved.emit()
        
        msg = ThemedMessageDialog("Settings Saved", "Your preferences have been updated successfully.", self)
        msg.exec()
        self.accept()

    def mousePressEvent(self, event):
        if not self.container.geometry().contains(self.container.mapFromGlobal(event.globalPosition().toPoint())):
            self.reject()
        super().mousePressEvent(event)
