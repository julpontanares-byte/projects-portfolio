# components/signup_banner.py
"""
SignupBanner component
"""
import flet as ft
from typing import Optional, Callable
from config.colors import COLORS


class SignupBanner:
    """Reusable signup promotion banner component for the home page."""

    def __init__(self, page: ft.Page, on_create_click: Optional[Callable] = None, on_signin_click: Optional[Callable] = None):
        self.page = page
        self.on_create_click = on_create_click
        self.on_signin_click = on_signin_click
        self.colors = COLORS

    def build(self) -> ft.Container:
        """Build and return the banner container control"""
        def _create_click(_e=None):
            if self.on_create_click:
                try:
                    self.on_create_click()
                except Exception:
                    pass
            else:
                try:
                    self.page.go("/signup")
                except Exception:
                    pass

        def _signin_click(_e=None):
            if self.on_signin_click:
                try:
                    self.on_signin_click()
                except Exception:
                    pass
            else:
                try:
                    self.page.go("/login")
                except Exception:
                    pass

        banner = ft.Container(
            margin=ft.margin.only(top=20),
            padding=25,
            bgcolor=self.colors["card_bg"],
            border_radius=10,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
                controls=[
                    ft.Icon(ft.Icons.STARS, size=40, color=self.colors["secondary"]),
                    ft.Text("📝 Ready to Find Your Perfect Home?", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text("Create a free account to unlock these features:", size=14, color=self.colors["text_dark"]),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        wrap=True,
                        spacing=20,
                        controls=[
                            ft.Column([
                                ft.Icon(ft.Icons.BOOKMARK, color=self.colors["secondary"]),
                                ft.Text("Save Favorites", size=12, text_align=ft.TextAlign.CENTER)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                            ft.Column([
                                ft.Icon(ft.Icons.CALENDAR_TODAY, color=self.colors["secondary"]),
                                ft.Text("Reserve Now", size=12, text_align=ft.TextAlign.CENTER)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                            ft.Column([
                                ft.Icon(ft.Icons.MESSAGE, color=self.colors["secondary"]),
                                ft.Text("Chat with Owners", size=12, text_align=ft.TextAlign.CENTER)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                            ft.Column([
                                ft.Icon(ft.Icons.NOTIFICATIONS, color=self.colors["secondary"]),
                                ft.Text("Get Updates", size=12, text_align=ft.TextAlign.CENTER)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                        ]
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.ElevatedButton(
                                "Create Free Account",
                                icon=ft.Icons.PERSON_ADD,
                                on_click=_create_click,
                                bgcolor=self.colors["focus"],
                                color="white",
                                height=50,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                            ),
                            ft.OutlinedButton(
                                "Already have an account? Sign In",
                                icon=ft.Icons.LOGIN,
                                on_click=_signin_click,
                                height=50,
                            ),
                        ]
                    )
                ]
            )
        )
        return banner
