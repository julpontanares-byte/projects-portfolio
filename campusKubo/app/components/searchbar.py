"""
Search bar component
"""
import flet as ft


class SearchBar(ft.Container):
    """Search bar with filter options"""

    def __init__(self, on_search=None, on_filter_click=None):
        super().__init__()
        self.on_search = on_search
        self.on_filter_click = on_filter_click

        self.content = self.build()

    def build(self):
        search_input = ft.TextField(
            hint_text="Search by Keyword or Location...",
            width=700,
            height=50,
            prefix_icon=ft.Icons.SEARCH,
            border_radius=25,
            bgcolor="#FFFFFF",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
            content_padding=ft.padding.only(left=20, top=15, right=20, bottom=15),
            on_change=lambda e: self.on_search(e.control.value) if self.on_search else None
        )

        return ft.Container(
            content=search_input,
            alignment=ft.alignment.center
        )
