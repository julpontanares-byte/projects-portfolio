# views/login_view.py
"""
Login view
"""
import flet as ft
from storage.db import validate_user
from config.colors import COLORS
from utils.navigation import go_home


class LoginView:
    """Login page view"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.colors = COLORS

    def build(self):
        """Build login view - matching model"""
        self.page.title = "CampusKubo - Login"
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER

        email = ft.TextField(
            label="Email Address",
            width=330,
            bgcolor=self.colors["background"],
            border_color=self.colors["border"],
            focused_border_color=self.colors["primary"],
            color=self.colors["text_dark"],
            on_change=lambda e: setattr(e.control, 'error_text', ''),
            autofocus=True
        )
        password = ft.TextField(
            label="Password",
            width=330,
            password=True,
            can_reveal_password=True,
            bgcolor=self.colors["background"],
            border_color=self.colors["border"],
            focused_border_color=self.colors["primary"],
            color=self.colors["text_dark"],
            on_change=lambda e: setattr(e.control, 'error_text', '')
        )

        # Loading indicator
        loading = ft.ProgressRing(visible=False, width=20, height=20, color=self.colors["primary"])

        # Message text for lockout notifications
        msg = ft.Text("", size=14, color=self.colors["error"])

        # Define login button (will set on_click after do_login is defined)
        login_btn = ft.ElevatedButton(
            "Log In",
            width=330,
            height=45,
            bgcolor=self.colors["primary"],
            color=self.colors["card_bg"]
        )

        def do_login(e):
            # Clear previous errors
            email.error_text = ""
            password.error_text = ""
            msg.value = ""
            loading.visible = True
            self.page.update()

            email_val = email.value or ""
            password_val = password.value or ""
            print(f"Login attempt: email={email_val}, password provided={bool(password_val)}")

            # Validate email field is filled
            if not email_val.strip():
                email.error_text = "Please fill out this field."
                loading.visible = False
                email.update()
                loading.update()
                return

            # Validate password field is filled
            if not password_val:
                password.error_text = "Please fill out this field."
                loading.visible = False
                password.update()
                loading.update()
                return

            # Basic client-side email format validation: require '@' and '.'
            if '@' not in email_val or '.' not in email_val:
                email.error_text = "Please enter a valid email address"
                loading.visible = False
                email.update()
                loading.update()
                return

            # Import lockout check
            from storage.db import is_account_locked

            # Check if account is locked
            is_locked, unlock_time = is_account_locked(email_val)
            if is_locked and unlock_time:
                from datetime import datetime
                try:
                    unlock_dt = datetime.fromisoformat(unlock_time)
                    time_remaining = int((unlock_dt - datetime.utcnow()).total_seconds())
                    msg.value = f"Account temporarily locked due to multiple failed login attempts. Try again in {time_remaining} seconds."
                    # visually grey out the button
                    login_btn.disabled = True
                    login_btn.bgcolor = self.colors.get("border", "#cccccc")

                    # start a background countdown thread if not already running
                    try:
                        import threading, time as _time

                        existing = getattr(self.page, '_login_cooldown_thread', None)
                        if not (existing and getattr(existing, 'is_alive', lambda: False)()):
                            # control flag to stop the thread early if needed
                            setattr(self.page, '_login_cooldown_stop', False)

                            def _countdown_loop():
                                while True:
                                    if getattr(self.page, '_login_cooldown_stop', False):
                                        break
                                    remaining = int((unlock_dt - datetime.utcnow()).total_seconds())
                                    if remaining <= 0:
                                        # cooldown finished
                                        login_btn.disabled = False
                                        login_btn.bgcolor = self.colors.get("primary", "#0078FF")
                                        msg.value = ""
                                        try:
                                            self.page.update()
                                        except Exception:
                                            pass
                                        break
                                    msg.value = f"Account temporarily locked due to multiple failed login attempts. Try again in {remaining} seconds."
                                    try:
                                        self.page.update()
                                    except Exception:
                                        pass
                                    _time.sleep(1)

                            th = threading.Thread(target=_countdown_loop, daemon=True)
                            setattr(self.page, '_login_cooldown_thread', th)
                            th.start()
                    except Exception:
                        # If threading fails, just show static message
                        pass
                except:
                    msg.value = "Account temporarily locked. Please try again later."
                    login_btn.disabled = True
                    login_btn.bgcolor = self.colors.get("border", "#cccccc")
                self.page.update()
                return

            # Re-enable login button if it was disabled and stop any cooldown thread
            login_btn.disabled = False
            login_btn.bgcolor = self.colors.get("primary", "#0078FF")
            try:
                setattr(self.page, '_login_cooldown_stop', True)
            except Exception:
                pass
            msg.value = ""
            login_btn.bgcolor = self.colors.get("primary", "#0078FF")
            try:
                setattr(self.page, '_login_cooldown_stop', True)
            except Exception:
                pass

            user = validate_user(email_val, password_val)
            print(f"User validated: {user}")

            loading.visible = False
            loading.update()

            if user:
                # Set all session data properly
                from datetime import datetime
                self.page.session.set("user_id", user.get('id'))
                self.page.session.set("email", user.get('email'))
                self.page.session.set("role", user.get('role'))
                self.page.session.set("full_name", user.get('full_name', ''))
                self.page.session.set("is_logged_in", True)
                self.page.session.set("last_activity", datetime.utcnow().isoformat())

                user_role = user.get('role')
                print(f"Login successful - ID: {user.get('id')}, Role: {user_role}, Email: {user.get('email')}")

                # Show success message
                msg.value = f"✅ Welcome back, {user.get('full_name', 'User')}!"
                msg.color = self.colors["success"]
                self.page.update()

                # Map DB role to routes used in the app
                if user_role in ("pm", "property_manager"):
                    self.page.go("/pm")
                elif user_role == "tenant":
                    self.page.go("/tenant")
                elif user_role == "admin":
                    self.page.go("/admin")
                else:
                    self.page.go("/")
            else:
                print("Login failed")
                # Clear any previous messages and show error on password field
                msg.value = ""
                password.error_text = "Incorrect email or password"
                password.update()

        def show_forgot_password(e):
            reset_email = ft.TextField(
                label="Enter your email address",
                hint_text="email@example.com",
                width=350,
                bgcolor=self.colors["background"],
                border_color=self.colors["border"],
                color=self.colors["text_dark"],
                on_change=lambda e: setattr(e.control, 'error_text', '')
            )

            def send_reset_link(e):
                if not reset_email.value or not reset_email.value.strip():
                    reset_email.error_text = "Please enter your email address"
                    reset_email.update()
                    return

                if '@' not in reset_email.value or '.' not in reset_email.value:
                    reset_email.error_text = "Please enter a valid email address"
                    reset_email.update()
                    return

                # TODO: Implement actual password reset logic here
                dialog.open = False
                self.page.update()

                setattr(self.page, "snack_bar", ft.SnackBar(
                    content=ft.Text(f"✅ Password reset link sent to {reset_email.value}"),
                    bgcolor=self.colors["success"],
                    duration=4000,
                ))
                getattr(self.page, "snack_bar").open = True
                self.page.update()

            dialog = ft.AlertDialog(
                title=ft.Text(
                    "🔑 Reset Password",
                    color=self.colors["text_dark"],
                    size=18
                ),
                content=ft.Container(
                    width=400,
                    padding=10,
                    content=ft.Column([
                        ft.Text(
                            "Enter your email address and we'll send you a link to reset your password.",
                            size=14,
                            color=self.colors["text_light"]
                        ),
                        ft.Container(height=10),
                        reset_email,
                    ], tight=True)
                ),
                actions=[
                    ft.TextButton(
                        "Cancel",
                        on_click=lambda e: self._close_dialog(dialog),
                        style=ft.ButtonStyle(color=self.colors["text_light"])
                    ),
                    ft.ElevatedButton(
                        "Send Reset Link",
                        on_click=send_reset_link,
                        bgcolor=self.colors["primary"],
                        color=self.colors["card_bg"]
                    )
                ],
                bgcolor=self.colors["card_bg"]
            )
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

        # Set the on_click handler for login button
        login_btn.on_click = do_login

        return ft.View("/login",
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            bgcolor=self.colors["background"],
            controls=[
                ft.Stack(
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
                                    ft.Text("Sign In", size=26, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                    email,
                                    password,
                                    msg,
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.END,
                                        width=330,
                                        controls=[
                                            ft.TextButton(
                                                "Forgot Password?",
                                                on_click=show_forgot_password,
                                                style=ft.ButtonStyle(color=self.colors["primary"])
                                            )
                                        ]
                                    ),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        controls=[loading]
                                    ),
                                    login_btn,
                                    ft.TextButton(
                                        "Don't have an account? Sign Up",
                                        on_click=lambda _: self.page.go("/signup"),
                                        style=ft.ButtonStyle(color=self.colors["text_dark"])
                                    ),
                                    ft.Container(
                                        padding=10,
                                        bgcolor=self.colors["background"],
                                        border_radius=6,
                                        content=ft.TextButton(
                                            "Continue as Guest → Browse Listings",
                                            on_click=lambda _: self.page.go("/browse"),
                                            style=ft.ButtonStyle(color=self.colors["text_light"])
                                        )
                                    )
                                ]
                            )
                        )
                    ]
                )
            ]
        )

    def _close_dialog(self, dialog):
        dialog.open = False
        self.page.update()
