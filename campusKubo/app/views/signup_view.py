"""
Signup view
"""
import flet as ft
from storage.db import create_user, validate_password, validate_email
from config.colors import COLORS
from utils.navigation import go_home


class SignupView:
    """Signup page view"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.selected_role = ft.Text("Tenant", visible=False)
        self.colors = COLORS

    def change_role(self, role):
        self.selected_role.value = role
        self.tenant_button.bgcolor = self.colors["primary"] if role == "Tenant" else self.colors["background"]
        self.tenant_button.color = self.colors["card_bg"] if role == "Tenant" else self.colors["text_dark"]
        self.pm_button.bgcolor = self.colors["primary"] if role == "Property Manager" else self.colors["background"]
        self.pm_button.color = self.colors["card_bg"] if role == "Property Manager" else self.colors["text_dark"]
        self.page.update()

    def build(self):
        """Build signup view - matching model"""
        self.page.title = "CampusKubo - Sign Up"

        self.tenant_button = ft.ElevatedButton(
            "🏠 Tenant",
            width=150,
            bgcolor=self.colors["primary"],
            color=self.colors["card_bg"],
            on_click=lambda _: self.change_role("Tenant")
        )

        self.pm_button = ft.ElevatedButton(
            "🏢 Property Manager",
            width=160,
            bgcolor=self.colors["background"],
            color=self.colors["text_dark"],
            on_click=lambda _: self.change_role("Property Manager")
        )

        # Form fields with real-time validation hints
        full_name = ft.TextField(
            label="Full Name",
            width=330,
            hint_text="e.g., Juan Dela Cruz",
            prefix_icon=ft.Icons.PERSON,
            bgcolor=self.colors["background"],
            border_color=self.colors["border"],
            focused_border_color=self.colors["primary"],
            color=self.colors["text_dark"],
            on_change=lambda e: setattr(e.control, 'error_text', ''),
            autofocus=True
        )

        email = ft.TextField(
            label="Email Address",
            width=330,
            hint_text="e.g., juan@example.com",
            prefix_icon=ft.Icons.EMAIL,
            keyboard_type=ft.KeyboardType.EMAIL,
            bgcolor=self.colors["background"],
            border_color=self.colors["border"],
            focused_border_color=self.colors["primary"],
            color=self.colors["text_dark"],
            on_change=lambda e: setattr(e.control, 'error_text', '')
        )

        # Password requirements display
        req_length = ft.Row([
            ft.Icon(ft.Icons.CIRCLE, size=12, color=self.colors["border"]),
            ft.Text("At least 8 characters", size=11, color=self.colors["text_light"])
        ], spacing=5)

        req_uppercase = ft.Row([
            ft.Icon(ft.Icons.CIRCLE, size=12, color=self.colors["border"]),
            ft.Text("One uppercase letter", size=11, color=self.colors["text_light"])
        ], spacing=5)

        req_number = ft.Row([
            ft.Icon(ft.Icons.CIRCLE, size=12, color=self.colors["border"]),
            ft.Text("One number", size=11, color=self.colors["text_light"])
        ], spacing=5)

        req_special = ft.Row([
            ft.Icon(ft.Icons.CIRCLE, size=12, color=self.colors["border"]),
            ft.Text("One special character (!@#$%^&*)", size=11, color=self.colors["text_light"])
        ], spacing=5)

        password_requirements = ft.Column(
            visible=False,
            spacing=5,
            controls=[
                ft.Text("Password requirements:", size=12, color=self.colors["text_dark"], weight=ft.FontWeight.BOLD),
                req_length,
                req_uppercase,
                req_number,
                req_special,
            ]
        )

        def validate_password_live(e):
            """Real-time password validation with visual feedback"""
            pwd = password.value or ""
            password_requirements.visible = True
            # Clear error text when typing
            password.error_text = ""

            # Check each requirement
            has_length = len(pwd) >= 8
            has_uppercase = any(c.isupper() for c in pwd)
            has_number = any(c.isdigit() for c in pwd)
            has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in pwd)

            # Update length requirement
            req_length.controls[0] = ft.Icon(ft.Icons.CHECK_CIRCLE if has_length else ft.Icons.CIRCLE, size=12, color=self.colors["success"] if has_length else self.colors["border"])
            req_length.controls[1] = ft.Text("At least 8 characters", size=11, color=self.colors["success"] if has_length else self.colors["text_light"])

            # Update uppercase requirement
            req_uppercase.controls[0] = ft.Icon(ft.Icons.CHECK_CIRCLE if has_uppercase else ft.Icons.CIRCLE, size=12, color=self.colors["success"] if has_uppercase else self.colors["border"])
            req_uppercase.controls[1] = ft.Text("One uppercase letter", size=11, color=self.colors["success"] if has_uppercase else self.colors["text_light"])

            # Update number requirement
            req_number.controls[0] = ft.Icon(ft.Icons.CHECK_CIRCLE if has_number else ft.Icons.CIRCLE, size=12, color=self.colors["success"] if has_number else self.colors["border"])
            req_number.controls[1] = ft.Text("One number", size=11, color=self.colors["success"] if has_number else self.colors["text_light"])

            # Update special character requirement
            req_special.controls[0] = ft.Icon(ft.Icons.CHECK_CIRCLE if has_special else ft.Icons.CIRCLE, size=12, color=self.colors["success"] if has_special else self.colors["border"])
            req_special.controls[1] = ft.Text("One special character (!@#$%^&*)", size=11, color=self.colors["success"] if has_special else self.colors["text_light"])

            password_requirements.update()

        password = ft.TextField(
            label="Password",
            width=330,
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK,
            on_change=validate_password_live,
            bgcolor=self.colors["background"],
            border_color=self.colors["border"],
            focused_border_color=self.colors["primary"],
            color=self.colors["text_dark"]
        )

        confirm_pw = ft.TextField(
            label="Confirm Password",
            width=330,
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            bgcolor=self.colors["background"],
            border_color=self.colors["border"],
            focused_border_color=self.colors["primary"],
            color=self.colors["text_dark"],
            on_change=lambda e: setattr(e.control, 'error_text', '')
        )

        # Terms checkbox
        agree = ft.Checkbox(
            value=False,
            active_color=self.colors["primary"]
        )

        terms_row = ft.Row(
            controls=[
                agree,
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("I agree to the ", size=14, color=self.colors["text_dark"]),
                                ft.TextButton(
                                    "Terms and Conditions",
                                    on_click=lambda _: self.page.go("/terms"),
                                    style=ft.ButtonStyle(
                                        padding=0,
                                        color=self.colors["primary"]
                                    ),
                                ),
                            ],
                            spacing=0,
                        ),
                        ft.Row(
                            controls=[
                                ft.Text("and ", size=14, color=self.colors["text_dark"]),
                                ft.TextButton(
                                    "Privacy Policies",
                                    on_click=lambda _: self.page.go("/privacy"),
                                    style=ft.ButtonStyle(
                                        padding=0,
                                        color=self.colors["primary"]
                                    ),
                                ),
                            ],
                            spacing=0,
                        ),
                    ],
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        )

        loading = ft.ProgressRing(visible=False, width=20, height=20, color=self.colors["primary"])

        def do_signup(e):
            # Clear previous error messages
            full_name.error_text = ""
            email.error_text = ""
            password.error_text = ""
            confirm_pw.error_text = ""

            loading.visible = True
            self.page.update()

            # Validate all fields are filled
            if not full_name.value or not full_name.value.strip():
                full_name.error_text = "Please fill out this field."
                loading.visible = False
                full_name.update()
                loading.update()
                return

            if not email.value or not email.value.strip():
                email.error_text = "Please fill out this field."
                loading.visible = False
                email.update()
                loading.update()
                return

            if not password.value:
                password.error_text = "Please fill out this field."
                loading.visible = False
                password.update()
                loading.update()
                return

            if not confirm_pw.value:
                confirm_pw.error_text = "Please fill out this field."
                loading.visible = False
                confirm_pw.update()
                loading.update()
                return

            # Check if passwords match
            if password.value != confirm_pw.value:
                confirm_pw.error_text = "Passwords do not match"
                loading.visible = False
                confirm_pw.update()
                loading.update()
                return

            # Check terms agreement
            if not agree.value:
                sb = ft.SnackBar(
                    content=ft.Text("❌ You must agree to the Terms and Conditions"),
                    bgcolor=self.colors["error"],
                )
                show_snack = getattr(self.page, "show_snack_bar", None)
                if callable(show_snack):
                    show_snack(sb)
                else:
                    self.page.open(sb)
                loading.visible = False
                loading.update()
                return

            # Validate password requirements
            is_valid, validation_msg = validate_password(password.value)
            if not is_valid:
                password.error_text = validation_msg
                loading.visible = False
                password.update()
                loading.update()
                return

            # Validate email format
            is_valid, validation_msg = validate_email(email.value)
            if not is_valid:
                email.error_text = validation_msg
                loading.visible = False
                email.update()
                loading.update()
                return

            # Create user
            success, message = create_user(
                full_name.value,
                email.value,
                password.value,
                "tenant" if self.selected_role.value == "Tenant" else "pm"
            )

            loading.visible = False

            if success:
                # Show success message
                sb = ft.SnackBar(
                    content=ft.Text(
                        f"✅ {message}!\n"
                        f"A confirmation email has been sent to {email.value}.\n"
                        "You may now log in."
                    ),
                    bgcolor=self.colors["success"],
                    duration=5000,
                )
                show_snack = getattr(self.page, "show_snack_bar", None)
                if callable(show_snack):
                    show_snack(sb)
                else:
                    self.page.open(sb)

                # Clear form after successful registration
                full_name.value = ""
                email.value = ""
                password.value = ""
                confirm_pw.value = ""
                agree.value = False
                password_requirements.visible = False

                full_name.update()
                email.update()
                password.update()
                confirm_pw.update()
                agree.update()
                password_requirements.update()

                # Redirect to login after 2 seconds
                import time
                time.sleep(2)
                self.page.go("/login")
            else:
                # Show error message
                sb = ft.SnackBar(
                    content=ft.Text(f"❌ {message}"),
                    bgcolor=self.colors["error"],
                )
                show_snack = getattr(self.page, "show_snack_bar", None)
                if callable(show_snack):
                    show_snack(sb)
                else:
                    self.page.open(sb)

            loading.update()

        # Role selection info box
        role_info = ft.Container(
            padding=10,
            bgcolor=self.colors["background"],
            border_radius=6,
            border=ft.border.all(1, self.colors["border"]),
            content=ft.Column(
                spacing=5,
                controls=[
                    ft.Text("Choose your role:", size=12, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                    ft.Text("🏠 Tenant - Search and book accommodations", size=11, color=self.colors["text_light"]),
                    ft.Text("🏢 Property Manager - List and manage properties", size=11, color=self.colors["text_light"]),
                ]
            )
        )

        return ft.View(
            "/signup",
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            bgcolor=self.colors["background"],
            controls=[
                ft.Container(
                    width=400,
                    padding=20,
                    bgcolor=self.colors["card_bg"],
                    border_radius=12,
                    border=ft.border.all(1, self.colors["border"]),
                    shadow=ft.BoxShadow(
                        blur_radius=15,
                        spread_radius=2,
                        color=ft.Colors.with_opacity(0.1, self.colors["text_light"])
                    ),
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=15,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.START,
                                controls=[
                                    ft.TextButton(
                                        content=ft.Row(
                                            controls=[
                                                ft.Icon(ft.Icons.ARROW_BACK, color=self.colors["primary"]),
                                                ft.Text("Back to Home", color=self.colors["text_dark"])
                                            ]
                                        ),
                                        on_click=lambda _: go_home(self.page)
                                    ),
                                ]
                            ),

                            # Header
                            ft.Text("Create Account", size=26, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                            ft.Text("Join CampusKubo today!", size=14, weight=ft.FontWeight.BOLD, color=self.colors["text_light"]),

                            ft.Container(height=5),

                            # Role selection
                            role_info,
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[self.tenant_button, self.pm_button]
                            ),

                            ft.Container(height=5),

                            # Form fields
                            full_name,
                            email,
                            password,
                            password_requirements,
                            confirm_pw,

                            # Terms checkbox
                            terms_row,

                            # Loading indicator
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[loading]
                            ),

                            # Submit button
                            ft.ElevatedButton(
                                "Create Account",
                                width=330,
                                height=45,
                                on_click=do_signup,
                                bgcolor=self.colors["primary"],
                                color=self.colors["card_bg"]
                            ),

                            # Login link
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Text("Already have an account?", size=13, color=self.colors["text_dark"]),
                                    ft.TextButton(
                                        "Login",
                                        on_click=lambda _: self.page.go("/login"),
                                        style=ft.ButtonStyle(color=self.colors["primary"])
                                    ),
                                ]
                            )
                        ]
                    )
                )
            ]
        )
