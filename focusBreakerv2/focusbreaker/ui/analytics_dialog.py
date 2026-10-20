import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from datetime import date, timedelta

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QFrame, QGridLayout, QScrollArea, QSizePolicy, QBoxLayout,
    QProgressBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPixmap

from focusbreaker.config import Colors, MODES, UIConfig, Palette
from focusbreaker.data.db import DBManager

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, facecolor='none')
        self.axes = fig.add_subplot(111)
        fig.patch.set_alpha(0)
        self.axes.set_facecolor('none')
        super().__init__(fig)

class ChartCard(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("chart_card_frame")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        
        header_l = QHBoxLayout()
        header = QLabel(title.upper())
        header.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 11px; font-weight: 800; color: {Palette.TEXT_MUTED}; letter-spacing: 1.5px;")
        header_l.addWidget(header)
        
        # Standardized info icon
        self.info_btn = QLabel("i")
        self.info_btn.setObjectName("info_icon_btn")
        self.info_btn.setFixedSize(18, 18)
        self.info_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_btn.setCursor(Qt.CursorShape.WhatsThisCursor)
        
        header_l.addStretch()
        header_l.addWidget(self.info_btn)
        layout.addLayout(header_l)
        
        self.container = QWidget()
        self.chart_layout = QVBoxLayout(self.container)
        self.chart_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.container, 1)


class AnalyticsPage(QWidget):
    def __init__(self, db: DBManager, parent=None):
        super().__init__(parent)
        self.db = db
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(60, 40, 60, 60)
        main_layout.setSpacing(32)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 1. Overview Row
        self.overview_l = QHBoxLayout()
        self.overview_l.setSpacing(16)
        main_layout.addLayout(self.overview_l)

        # 2. Charts Row 1
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        self.bar_card = ChartCard("Work Hours / Day")
        self.bar_card.info_btn.setToolTip("Your work habits\nthis week.")
        self.line_card = ChartCard("Break Compliance (%)")
        self.line_card.info_btn.setToolTip("How your break habits\nchange over time.")
        row1.addWidget(self.bar_card)
        row1.addWidget(self.line_card)
        main_layout.addLayout(row1)

        # 3. Charts Row 2
        row2 = QHBoxLayout()
        row2.setSpacing(16)
        self.donut_card = ChartCard("Mode Distribution")
        self.donut_card.info_btn.setToolTip("The work styles\nyou use most.")
        self.heatmap_card = ChartCard("Activity Heatmap")
        self.heatmap_card.info_btn.setToolTip("A map of your\nfocus consistency.")
        row2.addWidget(self.donut_card)
        row2.addWidget(self.heatmap_card)
        main_layout.addLayout(row2)

        # 4. Bottom Row
        row3 = QHBoxLayout()
        row3.setSpacing(16)
        self.break_card = ChartCard("Break Breakdown")
        self.break_card.info_btn.setToolTip("A look at how you\nhandle your breaks.")
        self.highlights_card = ChartCard("Highlights")
        self.highlights_card.info_btn.setToolTip("Fun facts about\nyour productivity.")
        self.streaks_card = ChartCard("All Streaks")
        self.streaks_card.info_btn.setToolTip("Your current best\nfocus records.")
        row3.addWidget(self.break_card)
        row3.addWidget(self.highlights_card)
        row3.addWidget(self.streaks_card)
        main_layout.addLayout(row3)

        scroll.setWidget(container)
        root.addWidget(scroll)

    def _metric_card(self, value, label, delta):
        card = QFrame()
        card.setObjectName("metric_card_frame")
        
        # Tooltips for metrics (shorter text for compact tooltips)
        tooltips = {
            "Total work hours": "Total time you've\nspent focusing.",
            "Sessions completed": "Total sessions you've\nsuccessfully finished.",
            "Break compliance": "How good you are\nat taking your breaks.",
            "Avg quality score": "Your overall score\nfor focus discipline."
        }
        tip_text = tooltips.get(label, "")

        l = QVBoxLayout(card)
        l.setContentsMargins(24, 24, 24, 24)
        l.setSpacing(12)
        
        top_l = QHBoxLayout()
        top_l.setContentsMargins(0, 0, 0, 0)
        
        val_lbl = QLabel(str(value))
        val_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 32px; font-weight: 700; color: {Palette.TEXT_PRIMARY};")
        top_l.addWidget(val_lbl)
        
        if tip_text:
            # Standardized info icon
            info = QLabel("i")
            info.setObjectName("info_icon_btn")
            info.setFixedSize(18, 18)
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info.setCursor(Qt.CursorShape.WhatsThisCursor)
            info.setToolTip(tip_text)
            top_l.addStretch()
            top_l.addWidget(info, alignment=Qt.AlignmentFlag.AlignTop)
        
        l.addLayout(top_l)
        
        txt_lbl = QLabel(label.upper())
        txt_lbl.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {Palette.TEXT_SECONDARY}; letter-spacing: 0.5px;")
        
        delta_lbl = QLabel(delta)
        delta_color = "#4CAF50" if "↑" in delta or "+" in delta else ("#F44336" if "↓" in delta or "-" in delta else Palette.TEXT_MUTED)
        delta_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: {delta_color}; margin-top: 8px;")
        
        l.addWidget(txt_lbl)
        l.addWidget(delta_lbl)
        return card

    def refresh_data(self):
        data = self.db.get_detailed_stats()
        
        # 1. Update Overview
        while self.overview_l.count():
            item = self.overview_l.takeAt(0)
            widget = item.widget() if item else None
            if widget: widget.deleteLater()
            
        ov = data['overview']
        dl = data.get('deltas', {"hours": 0, "sessions": 0, "quality": 0, "compliance": 0})
        
        def fmt_d(val, suffix=""):
            if val > 0: return f"↑ +{val}{suffix} vs prev"
            elif val < 0: return f"↓ {abs(val)}{suffix} vs prev"
            return "- strict baseline"

        self.overview_l.addWidget(self._metric_card(ov['total_hours'], "Total work hours", fmt_d(dl['hours'])))
        self.overview_l.addWidget(self._metric_card(ov['total_sessions'], "Sessions completed", fmt_d(dl['sessions'])))
        self.overview_l.addWidget(self._metric_card(f"{ov['break_compliance']}%", "Break compliance", fmt_d(dl['compliance'], "%")))
        self.overview_l.addWidget(self._metric_card(ov['avg_quality'], "Avg quality score", fmt_d(dl['quality'])))

        # 2. Bar Chart
        bar_data = data['bar']['data']
        if not any(v > 0 for v in bar_data):
            self._show_empty_state(self.bar_card.chart_layout, "No focus data this week")
        else:
            self._clear_layout(self.bar_card.chart_layout)
            bar_canvas = MplCanvas(self, width=5, height=3)
            bar_canvas.axes.bar(data['bar']['labels'], bar_data, color=Palette.BRAND_PRIMARY, alpha=0.8, width=0.6)
            bar_canvas.axes.set_ylim(0, max(bar_data) * 1.2)
            self._style_axes(bar_canvas.axes)
            self.bar_card.chart_layout.addWidget(bar_canvas)

        # 3. Line Chart
        line_data = data['line']['data']
        # For compliance, we only consider it "empty" if all weeks are 0 or 100 with no sessions (handled by DB)
        # But usually just check if there's any variation or actual session data
        if not any(v > 0 for v in line_data) and ov['total_sessions'] == 0:
            self._show_empty_state(self.line_card.chart_layout, "Insufficient data for compliance")
        else:
            self._clear_layout(self.line_card.chart_layout)
            line_canvas = MplCanvas(self, width=5, height=3)
            line_canvas.axes.plot(data['line']['labels'], line_data, marker='o', color=Palette.BRAND_SECONDARY, linewidth=2, markersize=4)
            line_canvas.axes.fill_between(data['line']['labels'], line_data, color=Palette.BRAND_SECONDARY, alpha=0.1)
            line_canvas.axes.set_ylim(0, 105)
            self._style_axes(line_canvas.axes)
            self.line_card.chart_layout.addWidget(line_canvas)

        # 4. Donut
        if not data['donut']:
            self._show_empty_state(self.donut_card.chart_layout, "No mode usage data")
        else:
            self._clear_layout(self.donut_card.chart_layout)
            donut_widget = QWidget()
            dl_layout = QHBoxLayout(donut_widget); dl_layout.setContentsMargins(0, 0, 0, 0)
            donut_canvas = MplCanvas(self, width=3, height=3)
            labels = list(data['donut'].keys())
            values = list(data['donut'].values())
            colors = [Palette.MODE_NORMAL_FILL, Palette.MODE_STRICT_FILL, Palette.MODE_FOCUS_FILL]
            donut_canvas.axes.pie(values, colors=colors[:len(values)], startangle=90, wedgeprops={'width': 0.4})
            dl_layout.addWidget(donut_canvas, 1)
            
            legend = QVBoxLayout(); legend.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            for i, (name, pc) in enumerate(data['donut'].items()):
                row = QHBoxLayout()
                swatch = QFrame(); swatch.setFixedSize(10, 10); swatch.setStyleSheet(f"background: {colors[i]}; border-radius: 2px;")
                n_lbl = QLabel(name.capitalize()); n_lbl.setStyleSheet("font-weight: 600; font-size: 12px;")
                p_lbl = QLabel(f"{pc}%"); p_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 10px; color: {Palette.TEXT_MUTED};")
                v = QVBoxLayout(); v.setSpacing(0); v.addWidget(n_lbl); v.addWidget(p_lbl)
                row.addWidget(swatch); row.addLayout(v); row.addStretch()
                legend.addLayout(row)
            dl_layout.addLayout(legend, 1)
            self.donut_card.chart_layout.addWidget(donut_widget)

        # 5. Heatmap with day labels and legend
        self._clear_layout(self.heatmap_card.chart_layout)
        
        # Main container for heatmap and legend
        heatmap_container = QVBoxLayout()
        heatmap_container.setSpacing(12)
        
        # Heatmap grid (with day labels on left)
        main_grid = QGridLayout()
        main_grid.setSpacing(2)
        main_grid.setContentsMargins(0, 0, 0, 0)
        
        hdata = data['heatmap']
        h_max = max(hdata.values()) if hdata.values() else 1
        if h_max == 0:
            h_max = 1
        dates = sorted(hdata.keys())
        
        # Color mapping function based on intensity (0.0 to 1.0)
        def get_cell_color(count, max_count):
            if count == 0:
                return "#F0F0F0", 0.0
            # Normalize count to 0-1 range
            intensity = min(count / max(max_count, 1), 1.0)
            # Linear gradient from light to dark
            # Start: #D4E9F7 (very light blue)
            # End: #0D47A1 (dark blue)
            r = int(212 * (1 - intensity) + 13 * intensity)
            g = int(233 * (1 - intensity) + 71 * intensity)
            b = int(247 * (1 - intensity) + 161 * intensity)
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            return hex_color, intensity
        
        # Add day-of-week labels (rows)
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for row_idx, day_name in enumerate(day_names):
            day_lbl = QLabel(day_name)
            day_lbl.setFixedWidth(30)
            day_lbl.setStyleSheet("font-size: 9px; color: #999; font-weight: 600; text-align: center;")
            day_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_grid.addWidget(day_lbl, row_idx, 0)
        
        # Add heatmap cells
        first_date = date.fromisoformat(dates[0])
        for d in dates:
            dt = date.fromisoformat(d)
            # weekday() returns 0 for Monday, 6 for Sunday
            row = dt.weekday()
            # Calculate column based on week alignment
            days_since_start = (dt - first_date).days
            col = (days_since_start + first_date.weekday()) // 7 + 1
            
            cell = QFrame()
            cell.setFixedSize(16, 16)
            count = hdata[d]
            color, intensity = get_cell_color(count, h_max)
            
            cell.setStyleSheet(f"background: {color}; border-radius: 2px; border: 1px solid #DDD;")
            if count > 0:
                cell.setToolTip(f"{d}: {count} session{'s' if count != 1 else ''}")
            else:
                cell.setToolTip(f"{d}: No activity")
            main_grid.addWidget(cell, row, col)
        
        heatmap_container.addLayout(main_grid)
        
        # Add legend with intensity scale
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(8)
        legend_layout.addStretch()
        
        legend_lbl = QLabel("Activity Intensity:")
        legend_lbl.setStyleSheet("font-size: 10px; font-weight: 600; color: #666;")
        legend_layout.addWidget(legend_lbl)
        
        # Show 5-step gradient legend
        for intensity_step in [0.0, 0.25, 0.5, 0.75, 1.0]:
            r = int(212 * (1 - intensity_step) + 13 * intensity_step)
            g = int(233 * (1 - intensity_step) + 71 * intensity_step)
            b = int(247 * (1 - intensity_step) + 161 * intensity_step)
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            color_box = QFrame()
            color_box.setFixedSize(12, 12)
            color_box.setStyleSheet(f"background: {color}; border-radius: 2px; border: 1px solid #CCC;")
            legend_layout.addWidget(color_box)
        
        scale_lbl = QLabel(f"0 → {h_max}+ sessions/day")
        scale_lbl.setStyleSheet("font-size: 9px; color: #999; margin-left: 6px;")
        legend_layout.addWidget(scale_lbl)
        legend_layout.addStretch()
        
        heatmap_container.addLayout(legend_layout)
        self.heatmap_card.chart_layout.addLayout(heatmap_container)

        # 6. Break Breakdown
        self._clear_layout(self.break_card.chart_layout)
        bb = data['break_breakdown']
        total_b = sum(bb.values())
        break_data = [
            ("Taken", bb.get('completed', 0), "#4CAF50"),
            ("Snoozed", bb.get('snoozed', 0), "#FFC107"),
            ("Skipped", bb.get('skipped', 0), "#F44336")
        ]
        bl = QVBoxLayout(); bl.setSpacing(16)
        for label, val, color in break_data:
            pc = round(val/total_b*100) if total_b > 0 else 0
            row = QHBoxLayout()
            lbl1 = QLabel(label)
            lbl1.setStyleSheet("font-weight: 600; font-size: 12px;")
            row.addWidget(lbl1)
            row.addStretch()
            lbl2 = QLabel(f"{pc}%")
            lbl2.setStyleSheet("font-family: 'JetBrains Mono'; font-weight: 700; font-size: 12px;")
            row.addWidget(lbl2)
            bl.addLayout(row)
            bar = QProgressBar(); bar.setFixedHeight(4); bar.setTextVisible(False); bar.setValue(pc)
            bar.setStyleSheet(f"QProgressBar::chunk {{ background: {color}; border-radius: 2px; }} QProgressBar {{ background: {Palette.SURFACE_DARK}; border-radius: 2px; }}")
            bl.addWidget(bar)
        self.break_card.chart_layout.addLayout(bl)

        # 7. Highlights
        self._clear_layout(self.highlights_card.chart_layout)
        hi = data['highlights']
        hl = QVBoxLayout(); hl.setSpacing(12)
        items = [
            ("Most productive day", hi['prod_day']),
            ("Favorite mode", hi['fav_mode']),
            ("Emergency exits", str(hi['exits'])),
            ("Avg session length", hi['avg_len']),
            ("Perfect sessions", str(hi['perfects']))
        ]
        for k, v in items:
            row = QHBoxLayout()
            k_lbl = QLabel(k)
            k_lbl.setStyleSheet(f"color: {Palette.TEXT_SECONDARY}; font-size: 12px;")
            row.addWidget(k_lbl)
            row.addStretch()
            v_lbl = QLabel(v)
            v_lbl.setStyleSheet("font-weight: 700; font-size: 12px; color: #1E2D2C;")
            row.addWidget(v_lbl)
            hl.addLayout(row)
        self.highlights_card.chart_layout.addLayout(hl)

        # 8. All Streaks
        self._clear_layout(self.streaks_card.chart_layout)
        sl = QVBoxLayout(); sl.setSpacing(12)
        streaks = self.db.get_streaks()
        streak_items = [
            ("🔥", "Session", streaks['session_streak']),
            ("⭐", "Perfect", streaks['perfect_session']),
            ("📅", "Daily", streaks['daily_consistency'])
        ]
        for ic, lab, s in streak_items:
            row = QHBoxLayout()
            left = QHBoxLayout(); left.setSpacing(8)
            ic_lbl = QLabel(ic)
            ic_lbl.setStyleSheet("font-size: 18px;")
            left.addWidget(ic_lbl)
            lab_lbl = QLabel(lab)
            lab_lbl.setStyleSheet("font-weight: 600; font-size: 13px;")
            left.addWidget(lab_lbl)
            row.addLayout(left)
            right = QVBoxLayout(); right.setSpacing(0)
            c_lbl = QLabel(str(s.current_count))
            c_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 18px; font-weight: 700; color: {Palette.BRAND_SECONDARY};")
            b_lbl = QLabel(f"best: {s.best_count}")
            b_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 9px; color: {Palette.TEXT_MUTED};")
            right.addWidget(c_lbl, alignment=Qt.AlignmentFlag.AlignRight); right.addWidget(b_lbl, alignment=Qt.AlignmentFlag.AlignRight)
            row.addLayout(right); sl.addLayout(row)
        self.streaks_card.chart_layout.addLayout(sl)

    def _show_empty_state(self, layout, message):
        """Display a clean empty state message in a chart card."""
        self._clear_layout(layout)
        container = QWidget()
        l = QVBoxLayout(container)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl = QLabel(message)
        lbl.setStyleSheet(f"color: {Palette.TEXT_MUTED}; font-size: 12px; font-weight: 500;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(lbl)
        layout.addWidget(container)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): self._clear_layout(item.layout())

    def _style_axes(self, ax):
        ax.tick_params(colors=Palette.TEXT_MUTED, labelsize=8)
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.yaxis.grid(True, linestyle='--', alpha=0.3, color=Palette.BORDER_DEFAULT)
        # Fix for tight layout to prevent squashing
        ax.figure.tight_layout()
