"""
Login form component
"""
import flet as ft

import flet as ft

class LoginForm:
    """Login form component"""

    def __init__(self, page: ft.Page, on_login=None):
        self.page = page
        self.on_login = on_login

        # form fields
        self.email = ft.TextField(
            label="Email Address",
            width=400,
            height=50,
            prefix_icon=ft.Icons.EMAIL,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
        )

        self.password = ft.TextField(
            label="Password",
            width=400,
            height=50,
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
        )

        self.msg = ft.Text(" ", size=12, color="red")

    def build(self):
        """Return the login form as a control"""
        content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            controls=[
                ft.Container(
                    content=ft.Column(
                        spacing=8,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.LOGIN, size=48, color="#0078FF"),
                            ft.Text(
                                "Welcome Back",
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color="#1A1A1A"
                            ),
                            ft.Text(
                                "Sign in to your account",
                                size=14,
                                color=ft.Colors.BLACK
                            )
                        ]
                    )
                ),
                ft.Container(height=10),
                self.email,
                self.password,
                self.msg,
                ft.ElevatedButton(
                    "Log In",
                    width=400,
                    height=50,
                    icon=ft.Icons.LOGIN,
                    style=ft.ButtonStyle(
                        color="white",
                        bgcolor="#0078FF",
                    ),
                    on_click=self._handle_login
                ),
                ft.Divider(height=1),
                ft.TextButton(
                    "Don't have an account? Sign Up",
                    icon=ft.Icons.PERSON_ADD,
                    on_click=lambda _: self.page.go("/signup")
                ),
                ft.TextButton(
                    "Continue as Guest → Browse Listings",
                    icon=ft.Icons.ARROW_FORWARD,
                    on_click=lambda _: self.page.go("/browse")
                )
            ]
        )
        return ft.Container(content=content)

    def _handle_login(self, e):
        """Handle login button click"""
        email = self.email.value.strip() if self.email.value else ""
        password = self.password.value if self.password.value else ""

        if not email or not password:
            self.msg.value = "Please enter both email and password"
            self.msg.color = "red"
            # update the form
            self.page.update()
            return

        if self.on_login:
            self.on_login(email, password, self.msg)
