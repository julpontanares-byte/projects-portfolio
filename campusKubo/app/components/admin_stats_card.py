# app/components/admin_stats_card.py
import flet as ft


class AdminStatsCard:
    def __init__(self, title, value, icon=None, trend_value=None, trend_up=True,
                 color="#0078FF", on_click=None, width: int = 220, height: int = 150):
        """Reusable admin KPI card.

        Args:
            title (str): Card title.
            value (int|str): Main numeric value to display.
            icon (ft.Icon | any): Either an `ft.Icon` instance or an Icons enum to render.
            trend_value (int|None): Optional percentage to show as trend.
            trend_up (bool): True if trend is positive (up arrow), False for down.
            color (str): Primary color for icon/background (hex or named).
            on_click (callable|None): Optional tap handler.
            width (int): Card width in pixels.
            height (int): Card height in pixels.
        """
        self.title = title
        self.value = value
        self.icon = icon
        self.trend_value = trend_value
        self.trend_up = trend_up
        self.color = color
        self.on_click = on_click
        self.width = width
        self.height = height

    def _build_icon(self):
        # Accept either an ft.Icon or an icon constant
        if isinstance(self.icon, ft.Icon):
            ic = self.icon
        else:
            try:
                ic = ft.Icon(self.icon if self.icon is not None else ft.Icons.INFO, size=24, color=self.color)
            except Exception:
                ic = ft.Icon(ft.Icons.INFO, size=24, color=self.color)

        return ft.Container(
            width=48,
            height=48,
            bgcolor=f"{self.color}1F",
            border_radius=14,
            alignment=ft.alignment.center,
            content=ic,
        )

    def build(self):
        trend_badge = None
        if self.trend_value is not None:
            trend_icon = ft.Icons.TRENDING_UP if self.trend_up else ft.Icons.TRENDING_DOWN
            trend_color = "#4CAF50" if self.trend_up else "#F44336"
            trend_badge = ft.Row(
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(trend_icon, size=18, color=trend_color),
                    ft.Text(
                        f"{self.trend_value}%",
                        size=13,
                        color=trend_color,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
            )

        # Header section with icon + title text stacked neatly
        header_section = ft.Row(
            alignment=ft.MainAxisAlignment.START,
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self._build_icon(),
                ft.Column(
                    spacing=4,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Text(self.title.upper(), size=12, color="#6B7280", weight=ft.FontWeight.BOLD),
                        ft.Text("Overview", size=11, color="#A0AEC0"),
                    ],
                ),
            ],
        )

        trend_column = ft.Column(
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            controls=[
                trend_badge or ft.Container(width=0, height=0),
                ft.Text("vs last period", size=11, color="#94A3B8"),
            ],
        )

        value_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    str(self.value),
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color="#0F172A",
                ),
                trend_column,
            ],
        )

        chevron = ft.Icon(ft.Icons.CHEVRON_RIGHT, size=20, color="#CBD5F5")
        if self.on_click:
            chevron = ft.GestureDetector(on_tap=self.on_click, content=chevron, mouse_cursor=ft.MouseCursor.CLICK)

        content = ft.Column(
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[header_section, chevron],
                ),
                value_row,
            ],
        )

        inner = ft.Container(
            bgcolor="white",
            padding=ft.padding.symmetric(horizontal=20, vertical=18),
            width=self.width,
            height=self.height,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=15, spread_radius=1, color="#00000015"),
            border=ft.border.all(1, "#E0E0E0"),
            content=content,
        )

        if self.on_click:
            return ft.GestureDetector(content=inner, on_tap=self.on_click, mouse_cursor=ft.MouseCursor.CLICK)

        return inner

