# app/components/table_card.py
import flet as ft
from typing import List, Optional


class TableCard:
    def __init__(
        self,
        title: str,
        table: ft.Control,
        actions: Optional[List[ft.Control]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        expand: bool = True,
        enable_horizontal_scroll: bool = True,
        table_min_width: Optional[int] = 640,
        table_max_width: Optional[int] = None,
    ):
        self.title = title
        self.table = table
        self.actions = actions or []
        self.width = width
        self.height = height
        self.expand = expand
        self.enable_horizontal_scroll = enable_horizontal_scroll
        self.table_min_width = table_min_width
        self.table_max_width = table_max_width

    def _build_header(self) -> ft.Row:
        header_controls: List[ft.Control] = [
            ft.Text(self.title, size=16, weight=ft.FontWeight.BOLD)
        ]
        if self.actions:
            header_controls.append(
                ft.Row(controls=self.actions, spacing=8)
            )
        header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=header_controls,
        )
        return header

    def _build_table_wrapper(self) -> ft.Control:
        table_container_kwargs = {
            "content": self.table,
            "alignment": ft.alignment.center_left,
            "padding": ft.padding.only(bottom=4),
        }
        # Flet Container does not support constraints in this version; approximate min width via width
        if self.table_min_width is not None:
            table_container_kwargs["width"] = self.table_min_width

        table_inner = ft.Container(**table_container_kwargs)

        table_row = ft.Row(
            controls=[table_inner],
            wrap=False,
            alignment=ft.MainAxisAlignment.START,
        )

        scroll_mode = getattr(ft, "ScrollMode", None)
        horizontal_scroll = getattr(scroll_mode, "HORIZONTAL", None) if scroll_mode is not None else None

        wrapper_kwargs = {
            "expand": True,
            "clip_behavior": ft.ClipBehavior.ANTI_ALIAS,
            "content": table_row,
        }
        if self.enable_horizontal_scroll and horizontal_scroll is not None:
            wrapper_kwargs["scroll"] = horizontal_scroll

        return ft.Container(**wrapper_kwargs)

    def build(self) -> ft.Control:
        table_wrapper = self._build_table_wrapper()
        content_column = ft.Column(
            spacing=10,
            controls=[
                self._build_header(),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                table_wrapper,
            ],
            expand=True,
        )

        outer_width = self.width if not self.expand else None
        outer = ft.Container(
            padding=12,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            width=outer_width,
            height=self.height,
            border=ft.border.all(1, "#E0E0E0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.Colors.GREY_100, offset=ft.Offset(0, 2)),
            content=content_column,
            expand=self.expand,
        )

        return outer
