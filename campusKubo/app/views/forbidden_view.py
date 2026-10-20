"""403 Forbidden View - Access Denied"""
import flet as ft
from components.navbar import NavBar


class ForbiddenView:
    """View displayed when user tries to access unauthorized resource"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.colors = {
            "primary": "#0078FF",
            "danger": "#FF4444",
            "background": "#F8F9FA",
            "text_dark": "#1A1A1A",
            "text_muted": "#6C757D"
        }

    def view(self):
        """Build the 403 forbidden page"""

        def go_home(e):
            """Navigate to home or appropriate dashboard"""
            role = self.page.session.get("role")
            if role == "admin":
                self.page.go("/admin")
            elif role == "pm":
                self.page.go("/pm")
            elif role == "tenant":
                self.page.go("/tenant")
            else:
                self.page.go("/")

        def go_back(e):
            """Navigate back to previous page"""
            history = getattr(self.page, "_nav_history", [])
            if history:
                prev_route = history.pop()
                setattr(self.page, "_nav_history", history)
                setattr(self.page, "_nav_back_navigation", True)
                self.page.go(prev_route)
            else:
                go_home(e)

        # Main content
        content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(height=80),

                # Error icon
                ft.Icon(
                    ft.Icons.BLOCK,
                    size=120,
                    color=self.colors["danger"]
                ),

                ft.Container(height=30),

                # Error message
                ft.Text(
                    "403 - Access Denied",
                    size=42,
                    weight=ft.FontWeight.BOLD,
                    color=self.colors["text_dark"]
                ),

                ft.Container(height=20),

                ft.Text(
                    "You don't have permission to access this resource.",
                    size=18,
                    color=self.colors["text_muted"],
                    text_align=ft.TextAlign.CENTER
                ),

                ft.Container(height=10),

                ft.Text(
                    "Please contact an administrator if you believe this is an error.",
                    size=14,
                    color=self.colors["text_muted"],
                    text_align=ft.TextAlign.CENTER
                ),

                ft.Container(height=40),

                # Action buttons
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                    controls=[
                        ft.ElevatedButton(
                            "Go Back",
                            icon=ft.Icons.ARROW_BACK,
                            on_click=go_back,
                            bgcolor=self.colors["text_muted"],
                            color="white",
                            height=45,
                            width=150
                        ),
                        ft.ElevatedButton(
                            "Go Home",
                            icon=ft.Icons.HOME,
                            on_click=go_home,
                            bgcolor=self.colors["primary"],
                            color="white",
                            height=45,
                            width=150
                        )
                    ]
                )
            ]
        )

        # Check if user is logged in for navbar
        is_logged_in_val = self.page.session.get("is_logged_in")
        is_logged_in = is_logged_in_val if is_logged_in_val is not None else False

        return ft.View(
            "/403",
            controls=[
                NavBar(self.page, show_auth_buttons=not is_logged_in).view(),
                ft.Container(
                    content=content,
                    bgcolor=self.colors["background"],
                    expand=True,
                    padding=20
                )
            ],
            bgcolor=self.colors["background"]
        )
