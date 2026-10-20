"""
Signup form component
"""
import flet as ft
from components.password_requirements import PasswordRequirements
from services.auth_service import AuthService

class SignupForm:
    """Signup form component"""

    def __init__(self, page: ft.Page, on_signup=None):
        self.page = page
        self.on_signup = on_signup
        self.selected_role = "Tenant"
        self.auth_service = AuthService()

        # Role buttons placeholders
        self.tenant_button = None
        self.pm_button = None

        # Password validation
        self.password_requirements = PasswordRequirements()
        self.password_req_display = None

        # Form fields
        self.full_name = ft.TextField(
            label="Full Name",
            width=400,
            height=50,
            prefix_icon=ft.Icons.PERSON,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
            on_change=self._validate_full_name,
        )

        self.email = ft.TextField(
            label="Email Address",
            width=400,
            height=50,
            prefix_icon=ft.Icons.EMAIL,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
            on_change=self._validate_email,
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
            on_change=self._on_password_change,
        )

        self.confirm_pw = ft.TextField(
            label="Confirm Password",
            width=400,
            height=50,
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#E0E0E0",
            focused_border_color="#0078FF",
            on_change=self._validate_confirm_password,
        )

        self.agree = ft.Checkbox()
        self.msg = ft.Text(" ", size=12)

    def _validate_full_name(self, e):
        """Validate full name in real-time"""
        is_valid, message = self.auth_service.validate_full_name(self.full_name.value or "")
        self.full_name.border_color = "#4CAF50" if is_valid or not self.full_name.value else "#FF6B6B"
        self.page.update()

    def _validate_email(self, e):
        """Validate email in real-time"""
        is_valid, message = self.auth_service.validate_email(self.email.value or "")
        self.email.border_color = "#4CAF50" if is_valid or not self.email.value else "#FF6B6B"
        self.page.update()

    def _on_password_change(self, e):
        """Update password requirements display on password change"""
        self.password_requirements.update_requirements(self.password.value or "")
        if self.password_req_display:
            self.password_req_display.content = self.password_requirements.build().content
            self.page.update()

    def _validate_confirm_password(self, e):
        """Validate confirm password matches password"""
        if self.confirm_pw.value and self.password.value != self.confirm_pw.value:
            self.confirm_pw.border_color = "#FF6B6B"
        elif self.confirm_pw.value:
            self.confirm_pw.border_color = "#4CAF50"
        else:
            self.confirm_pw.border_color = "#E0E0E0"
        self.page.update()

    def _change_role(self, role: str):
        """Update role button styles"""
        self.selected_role = role
        if self.tenant_button and self.pm_button:
            self.tenant_button.style = ft.ButtonStyle(
                color="white" if role == "Tenant" else "#1A1A1A",
                bgcolor="#0078FF" if role == "Tenant" else "#F5F5F5",
            )
            self.pm_button.style = ft.ButtonStyle(
                color="white" if role == "Property Manager" else "#1A1A1A",
                bgcolor="#0078FF" if role == "Property Manager" else "#F5F5F5",
            )
            self.page.update()

    def build(self):
        """Return the signup form as a control"""
        # Initialize password requirements display
        self.password_req_display = self.password_requirements.build()

        # Role selection buttons
        self.tenant_button = ft.ElevatedButton(
            "Tenant",
            expand=True,
            height=45,
            icon=ft.Icons.PERSON,
            style=ft.ButtonStyle(
                color="white",
                bgcolor="#0078FF",
            ),
            on_click=lambda _: self._change_role("Tenant")
        )
        self.pm_button = ft.ElevatedButton(
            "Property Manager",
            expand=True,
            height=45,
            icon=ft.Icons.BUSINESS,
            style=ft.ButtonStyle(
                color="#1A1A1A",
                bgcolor="#F5F5F5",
            ),
            on_click=lambda _: self._change_role("Property Manager")
        )

        return ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            controls=[
                ft.Container(
                    content=ft.Column(
                        spacing=8,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.PERSON_ADD, size=48, color="#0078FF"),
                            ft.Text(
                                "Create Account",
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color="#1A1A1A"
                            ),
                            ft.Text("Join CampusKubo today", size=14, color=ft.Colors.BLACK)
                        ]
                    )
                ),
                ft.Container(height=10),
                ft.Container(
                    width=400,
                    content=ft.Row(
                        spacing=15,
                        controls=[self.tenant_button, self.pm_button]
                    )
                ),
                self.full_name,
                self.email,
                self.password,
                self.password_req_display,
                self.confirm_pw,
                ft.Row(
                    controls=[
                        self.agree,
                        ft.Text(
                            "I agree to the Terms and Conditions and Privacy Policies",
                            size=12
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    width=400
                ),
                self.msg,
                ft.ElevatedButton(
                    "Create Account",
                    width=400,
                    height=50,
                    icon=ft.Icons.CHECK_CIRCLE,
                    style=ft.ButtonStyle(
                        color="white",
                        bgcolor="#0078FF",
                    ),
                    on_click=self._handle_signup
                ),
                ft.Divider(height=1),
                ft.TextButton(
                    "Already have an account? Login",
                    icon=ft.Icons.LOGIN,
                    on_click=lambda _: self.page.go("/login")
                )
            ]
        )

    def _handle_signup(self, e):
        """Handle signup button click"""
        if not self.agree.value:
            self.msg.value = "You must agree before creating an account"
            self.msg.color = "red"
            self.page.update()
            return

        if self.password.value != self.confirm_pw.value:
            self.msg.value = "Passwords do not match"
            self.msg.color = "red"
            self.page.update()
            return

        email = self.email.value.strip() if self.email.value else ""
        if not email:
            self.msg.value = "Please enter a valid email address"
            self.msg.color = "red"
            self.page.update()
            return

        if self.on_signup:
            role = "pm" if self.selected_role == "Property Manager" else "tenant"
            self.on_signup(
                email,
                self.password.value,
                role,
                self.full_name.value,
                self.msg
            )
