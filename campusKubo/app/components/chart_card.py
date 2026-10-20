# app/components/chart_card.py
import flet as ft
from typing import Optional, Sequence

class ChartCard:
    def __init__(
        self,
        title: str,
        chart: ft.Control,
        subtitle: Optional[str] = None,
        icon: Optional[ft.Icon] = None,
        footer: Optional[ft.Control] = None,
        legend: Optional[ft.Control] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        padding: int = 20,
        on_click=None,
    ):
        self.title = title
        self.chart = chart
        self.subtitle = subtitle
        self.icon = icon
        self.footer = footer
        self.legend = legend
        self.width = width
        self.height = height
        self.padding = padding
        self.on_click = on_click

    def _build_header(self) -> ft.Row:
        title_column = ft.Column([
            ft.Text(self.title, size=16, weight=ft.FontWeight.BOLD)
        ], spacing=2)
        if self.subtitle:
            title_column.controls.append(ft.Text(self.subtitle, size=11, color=ft.Colors.GREY_600))

        header_controls: list[ft.Control] = [title_column]

        action_row = ft.Row(controls=[], spacing=8)
        if self.icon:
            action_row.controls.append(self.icon)
        if self.on_click:
            action_row.controls.append(ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=ft.Colors.GREY))
        if action_row.controls:
            header_controls.append(action_row)

        header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=header_controls,
        )
        return header

    def build(self) -> ft.Control:
        chart_column_controls: list[ft.Control] = [self.chart]
        if self.legend:
            chart_column_controls.append(self.legend)
        if self.footer:
            chart_column_controls.append(self.footer)

        chart_column = ft.Column(
            spacing=10,
            controls=[
                self._build_header(),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                *chart_column_controls,
            ],
            expand=True,
        )

        inner = ft.Container(
            width=self.width,
            height=self.height,
            padding=self.padding,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.GREY_100,
                offset=ft.Offset(0, 2)
            ),
            content=chart_column,
        )

        if self.on_click:
            return ft.GestureDetector(content=inner, on_tap=self.on_click, mouse_cursor=ft.MouseCursor.CLICK)
        return inner
