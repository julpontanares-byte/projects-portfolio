"""
3-Panel Task Creation Modal
Redesigned for modern HCI (Human-Computer Interaction) principles.
Focuses on visual hierarchy, clear process flow, and interactive feedback.
"""
import logging
from PySide6.QtCore import Qt, QTime, QTimer, Signal, QSize, QPropertyAnimation
from PySide6.QtGui import QIntValidator, QColor, QFont, QPainter, QBrush, QPen
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame,
    QWidget, QSizePolicy, QSpinBox, QRadioButton, QButtonGroup, QTimeEdit, 
    QGraphicsDropShadowEffect, QStackedWidget, QGridLayout, QApplication,
    QGraphicsOpacityEffect
)

from focusbreaker.config import Colors, MODES, Palette
from focusbreaker.data.models import Task
from focusbreaker.data.db import DBManager

logger = logging.getLogger("FocusBreaker")


class StepIndicator(QWidget):
    """Modern progress indicator with numbered steps and connection lines."""
    def __init__(self, total_steps=3, parent=None):
        super().__init__(parent)
        self.total_steps = total_steps
        self.current_step = 1
        self._setup_ui()
        
    def _setup_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(12)
        self.setFixedHeight(40)
        
        self.steps = []
        for i in range(self.total_steps):
            dot = QLabel(str(i + 1))
            dot.setObjectName("step_dot")
            dot.setFixedSize(32, 32)
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.steps.append(dot)
            self.main_layout.addWidget(dot)
            
            if i < self.total_steps - 1:
                line = QFrame()
                line.setFixedHeight(2)
                line.setStyleSheet(f"background-color: {Palette.SURFACE_DARK}; border-radius: 1px; border: none;")
                self.main_layout.addWidget(line, 1)
            
        self.set_step(1)
    
    def set_step(self, step: int):
        self.current_step = step
        for i, dot in enumerate(self.steps):
            if i + 1 == step:
                # Active step
                dot.setStyleSheet(f"""
                    QLabel#step_dot {{
                        background-color: {Palette.BRAND_PRIMARY}; 
                        color: white; 
                        border-radius: 16px; 
                        font-weight: 800; 
                        font-size: 13px;
                        border: none;
                    }}
                """)
            elif i + 1 < step:
                # Completed step
                dot.setStyleSheet(f"""
                    QLabel#step_dot {{
                        background-color: {Palette.BRAND_LIGHT}; 
                        color: {Palette.BRAND_PRIMARY}; 
                        border-radius: 16px; 
                        font-weight: 800; 
                        font-size: 13px; 
                        border: 2px solid {Palette.BRAND_PRIMARY};
                    }}
                """)
            else:
                # Future step
                dot.setStyleSheet(f"""
                    QLabel#step_dot {{
                        background-color: {Palette.SURFACE_DARK}; 
                        color: {Palette.TEXT_MUTED}; 
                        border-radius: 16px; 
                        font-weight: 800; 
                        font-size: 13px;
                        border: none;
                    }}
                """)


class ModeCard(QFrame):
    """Interactive card for focus mode selection with visual feedback."""
    clicked = Signal(str)
    
    def __init__(self, mode_key: str, parent=None):
        super().__init__(parent)
        self.setObjectName("mode_card")
        self.mode_key = mode_key
        self.mode_data = MODES[mode_key]
        self._selected = False
        
        self.icons = {
            "normal": "🌿",
            "strict": "⚔️",
            "focused": "🔭"
        }
        
        self._setup_ui()
        
    def _setup_ui(self):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(180)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 24, 20, 24)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.icon_lbl = QLabel(self.icons.get(self.mode_key, "•"))
        self.icon_lbl.setStyleSheet("font-size: 36px; background: transparent; border: none;")
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_lbl)
        
        self.title_lbl = QLabel(self.mode_data['name'])
        self.title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {Palette.TEXT_PRIMARY}; background: transparent; border: none;")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_lbl)
        
        self.desc_lbl = QLabel(self.mode_data['description'])
        self.desc_lbl.setStyleSheet(f"font-size: 11px; color: {Palette.TEXT_SECONDARY}; line-height: 1.2; background: transparent; border: none;")
        self.desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_lbl.setWordWrap(True)
        layout.addWidget(self.desc_lbl)
        
        self.set_selected(False)
    
    def set_selected(self, selected: bool):
        self._selected = selected
        border_color = Palette.BRAND_PRIMARY if selected else Palette.SURFACE_DARK
        border_width = "2px" if selected else "1.5px"
        
        self.setStyleSheet(f"""
            QFrame#mode_card {{
                background-color: {Palette.SURFACE_WHITE};
                border: {border_width} solid {border_color};
                border-radius: 20px;
            }}
        """)
        
        if selected:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(20)
            shadow.setXOffset(0)
            shadow.setYOffset(8)
            shadow.setColor(QColor(0, 0, 0, 40))
            self.setGraphicsEffect(shadow)
        else:
            self.setGraphicsEffect(None)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.mode_key)


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
            # Simple jump for now, can add animation later if needed
            self._knob_pos = 22 if self._checked else 2
            self.toggled.emit(self._checked)
            self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QPen, QBrush
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        color = self._active_color if self._checked else self._bg_color
        p.setBrush(QBrush(QColor(color)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        
        # Draw knob
        p.setBrush(QBrush(QColor("white")))
        p.drawEllipse(self._knob_pos, 2, 20, 20)

class TaskDialog(QDialog):
    """Modern 3-Step Task Creator Modal."""
    
    def __init__(self, db: DBManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        
        self.setFixedSize(500, 680)
        
        # Center on parent
        if parent:
            self.move(parent.geometry().center() - self.rect().center())
        
        self.task_data = {
            'name': '',
            'mode': 'normal',
            'duration': 60,
            'auto_breaks': True,
            'break_count': 0,
            'break_duration': 0,
        }
        
        self.current_panel = 1
        self.mode_cards = {}
        self._result_task = None
        self._drag_pos = None
        
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("QDialog { background: transparent; }")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        # Modal Shell
        self.container = QFrame()
        self.container.setObjectName("modal_shell")
        self.container.setStyleSheet(f"""
            QFrame#modal_shell {{ 
                background-color: {Palette.SURFACE_DEFAULT}; 
                border-radius: 24px; 
                border: 1px solid {Palette.SURFACE_DARK}; 
            }}
        """)
        root.addWidget(self.container)
        
        l = QVBoxLayout(self.container)
        l.setContentsMargins(32, 24, 32, 32)
        l.setSpacing(0)
        
        # Header: Close button
        header = QHBoxLayout()
        header.addStretch()
        
        self.close_btn = QPushButton()
        self.close_btn.setObjectName("modal_close_btn")
        self.close_btn.setFixedSize(36, 28)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setToolTip("Cancel and close")
        
        close_l = QVBoxLayout(self.close_btn)
        close_l.setContentsMargins(0, 0, 0, 0)
        close_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        close_icon = QLabel("✕")
        close_icon.setStyleSheet("font-family: 'Segoe UI Symbol'; font-size: 14px; font-weight: 600; color: inherit; background: transparent; border: none;")
        close_l.addWidget(close_icon)
        
        self.close_btn.setStyleSheet(f"""
            QPushButton#modal_close_btn {{ 
                background: transparent; 
                border: none; 
                outline: none;
                border-radius: 4px; 
                color: {Palette.TEXT_SECONDARY}; 
            }} 
            QPushButton#modal_close_btn:hover {{ background: #FF5F57; color: white; border: none; }}
        """)
        self.close_btn.clicked.connect(self.reject)
        header.addWidget(self.close_btn)
        l.addLayout(header)
        
        l.addSpacing(10)
        
        # Step Indicator
        self.step_indicator = StepIndicator(3, self)
        l.addWidget(self.step_indicator)
        l.addSpacing(32)
        
        # Title area
        self.title_lbl = QLabel("Create Session")
        self.title_lbl.setStyleSheet(f"font-size: 26px; font-weight: 800; color: {Palette.TEXT_PRIMARY}; letter-spacing: -0.5px;")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.title_lbl)
        
        self.subtitle_lbl = QLabel("What are we achieving today?")
        self.subtitle_lbl.setStyleSheet(f"font-size: 13px; font-weight: 500; color: {Palette.TEXT_SECONDARY};")
        self.subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.subtitle_lbl)
        
        l.addSpacing(40)
        
        # Stacked Panels
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_panel_1())
        self.stack.addWidget(self._build_panel_2())
        self.stack.addWidget(self._build_panel_3())
        l.addWidget(self.stack, 1)
        
        l.addSpacing(32)
        
        # Footer Buttons
        footer = QHBoxLayout()
        footer.setSpacing(12)
        
        self.back_btn = QPushButton("Go Back")
        self.back_btn.setFixedSize(120, 44)
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background: white;
                border: 1.5px solid {Palette.SURFACE_DARK};
                border-radius: 22px;
                color: {Palette.TEXT_SECONDARY};
                font-weight: 700;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: {Palette.SURFACE_DARK}; }}
        """)
        self.back_btn.clicked.connect(self._on_back)
        self.back_btn.hide()
        footer.addWidget(self.back_btn)
        
        footer.addStretch()
        
        self.next_btn = QPushButton("Continue")
        self.next_btn.setFixedSize(160, 44)
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Palette.BRAND_PRIMARY};
                border: none;
                border-radius: 22px;
                color: white;
                font-weight: 800;
                font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {Palette.BRAND_SECONDARY}; }}
            QPushButton:disabled {{ background-color: #CCC; color: #999; }}
        """)
        self.next_btn.clicked.connect(self._on_next)
        footer.addWidget(self.next_btn)
        
        l.addLayout(footer)
        
        self._validate_panel_1()

    def _build_panel_1(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Task Name
        group1 = QVBoxLayout(); group1.setSpacing(8)
        
        header_row = QHBoxLayout()
        label = QLabel("TASK NAME")
        label.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {Palette.TEXT_MUTED}; letter-spacing: 1px; border: none; background: transparent;")
        header_row.addWidget(label)
        header_row.addStretch()
        
        self.char_count_lbl = QLabel("0/60")
        self.char_count_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: {Palette.TEXT_MUTED};")
        header_row.addWidget(self.char_count_lbl)
        group1.addLayout(header_row)
        
        self.task_input = QLineEdit()
        self.task_input.setObjectName("session_task_input")
        self.task_input.setMaxLength(60)
        self.task_input.setPlaceholderText("e.g. Design System refinement")
        self.task_input.setMinimumHeight(48)
        self.task_input.setToolTip("Give your session a name you'll recognize in history.")
        self.task_input.setStyleSheet(f"""
            QLineEdit#session_task_input {{
                background-color: white;
                border: 2px solid {Palette.BRAND_PRIMARY};
                border-radius: 12px;
                padding: 12px 16px;
                padding-right: 50px; /* Space for counter if it were inside, but it's above for better visibility */
                font-size: 14px;
                color: {Palette.TEXT_PRIMARY};
            }}
        """)
        self.task_input.textChanged.connect(self._validate_panel_1)
        group1.addWidget(self.task_input)
        
        # Hint text
        self.name_hint = QLabel("A name is required to continue.")
        self.name_hint.setStyleSheet(f"font-size: 10px; color: #F44336; font-weight: 600;")
        group1.addWidget(self.name_hint)

        layout.addLayout(group1)
        
        # Mode Selection
        group2 = QVBoxLayout(); group2.setSpacing(8)
        label2 = QLabel("SELECT MODE")
        label2.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {Palette.TEXT_MUTED}; letter-spacing: 1px; border: none; background: transparent;")
        group2.addWidget(label2)
        
        modes_l = QHBoxLayout(); modes_l.setSpacing(12)
        for key in ["normal", "strict", "focused"]:
            card = ModeCard(key, self)
            card.setToolTip(f"Choose {key.capitalize()} mode for this session.")
            card.clicked.connect(self._on_mode_selected)
            if key == "normal":
                card.set_selected(True)
            self.mode_cards[key] = card
            modes_l.addWidget(card)
        group2.addLayout(modes_l)
        layout.addLayout(group2)
        
        # Mode Warning
        self.mode_warning = QLabel()
        self.mode_warning.setStyleSheet(f"color: #FF5F57; font-size: 11px; font-weight: 600; border: none; background: transparent; padding-top: 4px;")
        self.mode_warning.setWordWrap(True)
        self.mode_warning.hide()
        layout.addWidget(self.mode_warning)
        
        layout.addStretch()
        return w

    def _build_panel_3(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        
        # Confirmation Card
        card = QFrame()
        card.setObjectName("summary_card")
        card.setStyleSheet(f"QFrame#summary_card {{ background: white; border-radius: 20px; border: 1.5px solid {Palette.SURFACE_DARK}; }}")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 24, 24, 24)
        cl.setSpacing(16)
        
        self.summary_rows = {}
        rows = ["TASK", "MODE", "DURATION", "BREAKS"]
        for i, label in enumerate(rows):
            row_w = QWidget()
            row = QHBoxLayout(row_w)
            row.setContentsMargins(0, 4, 0, 4)
            l_lbl = QLabel(label)
            l_lbl.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {Palette.TEXT_MUTED}; border: none; letter-spacing: 1px;")
            r_lbl = QLabel("-")
            r_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {Palette.TEXT_PRIMARY}; border: none;")
            row.addWidget(l_lbl); row.addStretch(); row.addWidget(r_lbl)
            cl.addWidget(row_w)
            self.summary_rows[label] = r_lbl
            
            if i < len(rows) - 1:
                line = QFrame()
                line.setFixedHeight(1)
                line.setStyleSheet(f"background-color: {Palette.SURFACE_DARK}; border: none;")
                cl.addWidget(line)
            
        layout.addWidget(card)
        
        self.motivational = QLabel("Ready to dive in?")
        self.motivational.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {Palette.BRAND_SECONDARY};")
        self.motivational.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.motivational)
        
        layout.addStretch()
        return w

    def _on_mode_selected(self, key):
        self.task_data['mode'] = key
        for k, card in self.mode_cards.items():
            card.set_selected(k == key)
            
        if key == "strict":
            self.mode_warning.setText("⚠ STRICT: Breaks are enforced. Cooldown will apply.")
            self.mode_warning.show()
        elif key == "focused":
            self.mode_warning.setText("⚠ FOCUS: No breaks until the session is finished.")
            self.mode_warning.show()
        else:
            self.mode_warning.hide()
        
        self._update_break_preview()

    def _validate_panel_1(self):
        text = self.task_input.text()
        count = len(text)
        valid = count > 0
        
        # Update char counter
        self.char_count_lbl.setText(f"{count}/60")
        self.char_count_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: {'#F44336' if count >= 60 else Palette.TEXT_MUTED};")
        
        # Validation visual feedback
        border_color = Palette.BRAND_PRIMARY if valid else "#F44336"
        self.name_hint.setVisible(not valid)

        self.task_input.setStyleSheet(f"""
            QLineEdit#session_task_input {{
                background-color: white;
                border: 2px solid {border_color};
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 14px;
                color: {Palette.TEXT_PRIMARY};
            }}
        """)
        self.next_btn.setEnabled(valid)

    def _build_panel_2(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Duration Section Header with Unit Toggle
        group1 = QVBoxLayout(); group1.setSpacing(12)
        
        header_row = QHBoxLayout()
        label = QLabel("SESSION DURATION")
        label.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {Palette.TEXT_MUTED}; letter-spacing: 1px; border: none; background: transparent;")
        header_row.addWidget(label)
        header_row.addStretch()
        
        # Unit Switcher (Min vs Hr)
        unit_box = QWidget()
        unit_box.setObjectName("unit_switcher")
        unit_box.setStyleSheet(f"QWidget#unit_switcher {{ background: {Palette.SURFACE_DARK}; border-radius: 14px; padding: 2px; }}")
        unit_l = QHBoxLayout(unit_box); unit_l.setContentsMargins(0, 0, 0, 0); unit_l.setSpacing(0)
        
        self.btn_min = QPushButton("MINUTES")
        self.btn_hr = QPushButton("HOURS")
        for b in [self.btn_min, self.btn_hr]:
            b.setFixedSize(70, 24)
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(self._toggle_duration_unit)
        
        self.btn_min.setChecked(True)
        self._update_unit_styles()
        
        unit_l.addWidget(self.btn_min); unit_l.addWidget(self.btn_hr)
        header_row.addWidget(unit_box)
        group1.addLayout(header_row)
        
        # Stacked Duration Input
        self.dur_stack = QStackedWidget()
        
        # ── Panel 2.1: Total Minutes (Simple) ──
        min_page = QWidget()
        min_l = QHBoxLayout(min_page); min_l.setContentsMargins(0, 0, 0, 0)
        self.duration_input_raw = QLineEdit("60")
        self.duration_input_raw.setValidator(QIntValidator(5, 480))
        self.duration_input_raw.setMinimumHeight(48)
        self.duration_input_raw.setStyleSheet(self._input_style())
        self.duration_input_raw.textChanged.connect(self._update_break_preview)
        min_l.addWidget(self.duration_input_raw)
        self.dur_stack.addWidget(min_page)
        
        # ── Panel 2.2: Hours + Minutes (Detailed) ──
        hr_page = QWidget()
        hr_l = QHBoxLayout(hr_page); hr_l.setContentsMargins(0, 0, 0, 0); hr_l.setSpacing(12)
        
        self.duration_h = QSpinBox()
        self.duration_h.setRange(0, 8); self.duration_h.setValue(1); self.duration_h.setFixedSize(100, 48)
        self.duration_h.setStyleSheet(self._spinbox_style())
        self.duration_h.setPrefix("H: ")
        
        self.duration_m = QSpinBox()
        self.duration_m.setRange(0, 59); self.duration_m.setValue(0); self.duration_m.setFixedSize(100, 48)
        self.duration_m.setStyleSheet(self._spinbox_style())
        self.duration_m.setPrefix("M: ")
        
        self.duration_h.valueChanged.connect(self._update_break_preview)
        self.duration_m.valueChanged.connect(self._update_break_preview)
        
        hr_l.addWidget(self.duration_h); hr_l.addWidget(self.duration_m); hr_l.addStretch()
        self.dur_stack.addWidget(hr_page)
        
        group1.addWidget(self.dur_stack)
        layout.addLayout(group1)
        
        # Manual Break Settings
        self.manual_group = QWidget()
        ml = QVBoxLayout(self.manual_group)
        ml.setContentsMargins(0, 4, 0, 4)
        ml.setSpacing(12)

        # Break Auto/Manual Toggle
        auto_l = QHBoxLayout()
        auto_lbl = QLabel("Schedule breaks automatically")
        auto_lbl.setStyleSheet("font-size: 12px; font-weight: 600; border: none; background: transparent;")
        self.auto_btn = SlidingToggle()
        self.auto_btn.setChecked(True)
        self.auto_btn.toggled.connect(self._toggle_auto_breaks)
        auto_l.addWidget(auto_lbl); auto_l.addStretch(); auto_l.addWidget(self.auto_btn)
        ml.addLayout(auto_l)

        # Manual Controls Container
        self.manual_controls = QWidget()
        self.manual_controls.hide()
        mcl = QGridLayout(self.manual_controls)
        mcl.setContentsMargins(0, 4, 0, 4)
        mcl.setSpacing(12)

        self.break_count_lbl = QLabel("Number of breaks")
        mcl.addWidget(self.break_count_lbl, 0, 0)
        self.break_count_spin = QSpinBox()
        self.break_count_spin.setRange(1, 10)
        self.break_count_spin.setValue(2)
        self.break_count_spin.setFixedSize(80, 36)
        self.break_count_spin.setStyleSheet(self._spinbox_style(compact=True))
        mcl.addWidget(self.break_count_spin, 0, 1)

        self.break_dur_lbl = QLabel("Break duration (min)")
        mcl.addWidget(self.break_dur_lbl, 1, 0)
        self.break_dur_spin = QSpinBox()
        self.break_dur_spin.setRange(1, 60)
        self.break_dur_spin.setValue(5)
        self.break_dur_spin.setFixedSize(80, 36)
        self.break_dur_spin.setStyleSheet(self._spinbox_style(compact=True))
        mcl.addWidget(self.break_dur_spin, 1, 1)
        
        self.break_count_spin.valueChanged.connect(self._update_break_preview)
        self.break_dur_spin.valueChanged.connect(self._update_break_preview)
        
        ml.addWidget(self.manual_controls)
        layout.addWidget(self.manual_group)
        
        # Break Info Card
        self.break_card = QFrame()
        self.break_card.setObjectName("break_preview_card")
        self.break_card.setStyleSheet(f"QFrame#break_preview_card {{ background: {Palette.BRAND_LIGHT}; border-radius: 16px; border: 1px solid {Palette.BRAND_PRIMARY}; }}")
        bcl = QVBoxLayout(self.break_card)
        bcl.setContentsMargins(16, 16, 16, 16)
        bcl.setSpacing(6)
        
        self.break_title = QLabel("BREAK SCHEDULE")
        self.break_title.setStyleSheet(f"font-size: 10px; font-weight: 900; color: {Palette.BRAND_PRIMARY}; letter-spacing: 1px; border: none; background: transparent;")
        bcl.addWidget(self.break_title)
        
        self.break_preview = QLabel("-")
        self.break_preview.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {Palette.TEXT_PRIMARY}; border: none; background: transparent;")
        self.break_preview.setWordWrap(True)
        bcl.addWidget(self.break_preview)
        
        layout.addWidget(self.break_card)
        layout.addStretch()
        return w

    def _spinbox_style(self, compact=False):
        p = "4px 8px" if compact else "10px 16px"
        return f"""
            QSpinBox {{
                background-color: white;
                border: 2px solid {Palette.BORDER_DEFAULT};
                border-radius: 8px;
                padding: {p};
                font-size: 14px;
                font-weight: 700;
                color: {Palette.TEXT_PRIMARY};
            }}
            QSpinBox:focus {{ border: 2px solid {Palette.BRAND_PRIMARY}; }}
            QSpinBox::up-button, QSpinBox::down-button {{ width: 24px; border: none; background: transparent; }}
            QSpinBox::up-arrow {{ image: none; }}
            QSpinBox::down-arrow {{ image: none; }}
        """

    def _input_style(self):
        return f"""
            QLineEdit {{
                background-color: white;
                border: 2px solid {Palette.BORDER_DEFAULT};
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 14px;
                color: {Palette.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{ border: 2.5px solid {Palette.BRAND_PRIMARY}; }}
        """

    def _toggle_duration_unit(self):
        btn = self.sender()
        if btn == self.btn_min:
            self.btn_hr.setChecked(False)
            self.dur_stack.setCurrentIndex(0)
        else:
            self.btn_min.setChecked(False)
            self.dur_stack.setCurrentIndex(1)
        self._update_unit_styles()
        self._update_break_preview()

    def _update_unit_styles(self):
        for b in [self.btn_min, self.btn_hr]:
            active = b.isChecked()
            bg = Palette.SURFACE_WHITE if active else "transparent"
            fg = Palette.BRAND_PRIMARY if active else Palette.TEXT_SECONDARY
            b.setStyleSheet(f"""
                QPushButton {{
                    background: {bg};
                    color: {fg};
                    border-radius: 0px; /* Sharpened highlight */
                    font-size: 9px;
                    font-weight: 800;
                    letter-spacing: 0.5px;
                }}
            """)

    def _toggle_auto_breaks(self, on):
        self.manual_controls.setVisible(not on)
        self._update_break_preview()

    def _update_break_preview(self):
        if self.btn_min.isChecked():
            try:
                total_mins = int(self.duration_input_raw.text() or "0")
            except: total_mins = 0
        else:
            total_mins = (self.duration_h.value() * 60) + self.duration_m.value()
        
        # Validation feedback
        is_valid = total_mins >= 5
        
        mode = self.task_data['mode']
        is_auto = self.auto_btn.isChecked()

        # Manual break logic check: sum of breaks must be less than total duration
        if not is_auto and mode != "focused":
            count = self.break_count_spin.value()
            bdur = self.break_dur_spin.value()
            if (count * bdur) >= total_mins:
                is_valid = False
                self.break_preview.setText("⚠ Total break time exceeds session duration.")
                self.break_preview.setStyleSheet("font-size: 11px; font-weight: 700; color: #F44336; border: none; background: transparent;")
                self._apply_validation_style(False)
                self.next_btn.setEnabled(False)
                return

        self._apply_validation_style(is_valid)
        
        if not is_valid:
            self.break_preview.setText("⚠ Session must be at least 5 minutes.")
            self.break_preview.setStyleSheet(f"font-size: 11px; font-weight: 700; color: #F44336; border: none; background: transparent;")
            self.next_btn.setEnabled(False)
            return
        else:
            self.break_preview.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {Palette.TEXT_PRIMARY}; border: none; background: transparent;")
            self.next_btn.setEnabled(True)

        if mode == "focused":
            self.manual_group.setEnabled(True)
            self.auto_btn.setEnabled(True)
            
            if is_auto:
                self.manual_controls.hide()
                # Use scaling logic for default
                brk_dur = 30
                if total_mins >= 240: brk_dur = 60
                elif total_mins >= 120: brk_dur = 45
                
                msg = f"Deep flow state. {brk_dur} min mandatory rest after completion."
                self.task_data['break_count'] = 1
                self.task_data['break_duration'] = brk_dur
            else:
                self.manual_controls.show()
                # Hide count for focused mode as it's always 1
                self.break_count_lbl.hide()
                self.break_count_spin.hide()
                
                bdur = self.break_dur_spin.value()
                msg = f"Deep flow state. {bdur} min manual rest after completion."
                self.task_data['break_count'] = 1
                self.task_data['break_duration'] = bdur
        else:
            self.manual_group.setEnabled(True)
            self.auto_btn.setEnabled(True)
            self.break_count_lbl.show()
            self.break_count_spin.show()
            
            if is_auto:
                self.manual_controls.hide()
                if mode == "strict":
                    count = total_mins // 52
                    msg = f"{count} sessions of 52 min work + 17 min break."
                    self.task_data['break_count'] = count
                    self.task_data['break_duration'] = 17
                else:
                    count = total_mins // 25
                    msg = f"{count} blocks of 25 min work + 5 min break."
                    self.task_data['break_count'] = count
                    self.task_data['break_duration'] = 5
            else:
                self.manual_controls.show()
                count = self.break_count_spin.value()
                bdur = self.break_dur_spin.value()
                msg = f"Manual schedule: {count} breaks of {bdur} min each."
                self.task_data['break_count'] = count
                self.task_data['break_duration'] = bdur
            
        self.break_preview.setText(msg)

    def _apply_validation_style(self, is_valid):
        border_color = Palette.BRAND_PRIMARY if is_valid else "#F44336"
        if self.btn_min.isChecked():
            self.duration_input_raw.setStyleSheet(self._input_style().replace(Palette.BORDER_DEFAULT, border_color))
        else:
            self.duration_h.setStyleSheet(self._spinbox_style().replace(Palette.BORDER_DEFAULT, border_color))
            self.duration_m.setStyleSheet(self._spinbox_style().replace(Palette.BORDER_DEFAULT, border_color))

    def _on_next(self):
        if self.current_panel == 1:
            self.task_data['name'] = self.task_input.text().strip()
            self._show_panel(2)
        elif self.current_panel == 2:
            if self.btn_min.isChecked():
                try:
                    self.task_data['duration'] = int(self.duration_input_raw.text() or "60")
                except: self.task_data['duration'] = 60
            else:
                self.task_data['duration'] = (self.duration_h.value() * 60) + self.duration_m.value()

            self.task_data['auto_breaks'] = self.auto_btn.isChecked()
            self._show_panel(3)
        else:
            self._on_start()

    def _on_back(self):
        if self.current_panel > 1:
            self._show_panel(self.current_panel - 1)

    def _show_panel(self, num):
        self.current_panel = num
        self.stack.setCurrentIndex(num - 1)
        self.step_indicator.set_step(num)
        self.back_btn.setVisible(num > 1)
        
        if num == 3:
            self.title_lbl.setText("Confirm Session")
            self.subtitle_lbl.setText("Almost there!")
            self.next_btn.setText("Start Session")
            self._populate_summary()
        elif num == 2:
            self.title_lbl.setText("Set Duration")
            self.subtitle_lbl.setText("How long will we focus?")
            self.next_btn.setText("Continue")
            self._update_break_preview()
        else:
            self.title_lbl.setText("Start Session")
            self.subtitle_lbl.setText("What are we achieving today?")
            self.next_btn.setText("Continue")

    def _populate_summary(self):
        d = self.task_data
        self.summary_rows["TASK"].setText(d['name'])
        self.summary_rows["MODE"].setText(d['mode'].upper())
        
        h = d['duration'] // 60
        m = d['duration'] % 60
        dur_str = f"{h}h {m}m" if h > 0 else f"{m}m"
        self.summary_rows["DURATION"].setText(dur_str)
        
        if d['mode'] == "focused":
            self.summary_rows["BREAKS"].setText("Rest at end")
            self.motivational.setText("Deep work mode. No distractions.")
        else:
            b_info = f"{d['break_count']} x {d['break_duration']} min"
            type_str = "Auto" if d['auto_breaks'] else "Manual"
            self.summary_rows["BREAKS"].setText(f"{type_str}: {b_info}")
            self.motivational.setText("Steady progress leads to success.")

    def _on_start(self):
        task = Task(
            name=self.task_data['name'],
            allocated_time_minutes=self.task_data['duration'],
            mode=self.task_data['mode'],
            auto_calculate_breaks=self.task_data['auto_breaks'],
            manual_break_count=self.task_data['break_count'],
            manual_break_duration=self.task_data['break_duration']
        )
        logger.info(
            "Creating task: name=%s duration=%s mode=%s auto_breaks=%s manual_break_count=%s manual_break_duration=%s",
            task.name,
            task.allocated_time_minutes,
            task.mode,
            task.auto_calculate_breaks,
            task.manual_break_count,
            task.manual_break_duration,
        )
        task_id = self.db.create_task(task)
        logger.info("Task created successfully: id=%s name=%s", task_id, task.name)
        self._result_task = task
        self.accept()

    def get_task(self): return getattr(self, "_result_task", None)
    def get_session_data(self): return self.task_data

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
