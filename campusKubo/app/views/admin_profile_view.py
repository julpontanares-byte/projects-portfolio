# app/views/admin_profile_view.py

import flet as ft
from state.session_state import SessionState
from components.navbar import DashboardNavBar
from components.footer import Footer
from components.profile_section import ProfileSection
from services.admin_service import AdminService
from services.settings_service import SettingsService
from services.activity_service import ActivityService

class AdminProfileView:
    """Admin Profile Page"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.session = SessionState(page)
        self.admin_service = AdminService()
        # SettingsService methods are classmethods; no instance required
        # form controls
        self.full_name_field = None
        self.email_field = None
        self.password_field = None
        self.confirm_password_field = None
        self.enable_2fa_checkbox = None
        self.password_min_length_field = None

        # Register for global refresh events
        try:
            from services.refresh_service import register as _register_refresh
            _register_refresh(self._on_global_refresh)
        except Exception:
            pass

    def _on_global_refresh(self):
        """Handle global refresh event"""
        try:
            # Trigger page refresh by re-navigating to profile
            if hasattr(self.page, 'route') and self.page.route == '/admin_profile':
                self.page.go('/admin_profile')
        except Exception:
            pass

    def build(self):
        # Runtime logging around view build
        try:
            print(f"[AdminProfileView.build] invoked; session_user={self.session.get_user_id()}")
        except Exception:
            pass

        # Auth
        if not self.session.require_auth():
            return None

        if not self.session.is_admin():
            self.page.go("/")
            return None

        # Fetch user info
        user_id = self.session.get_user_id()
        if not user_id:
            self.page.go("/login")
            return None

        try:
            profile = self.admin_service.get_user_by_id(user_id)
        except Exception as e:
            print(f"[AdminProfileView] Failed to load admin profile: {e}")
            profile = None

        if not profile:
            return ft.View(
                "/admin_profile",
                controls=[ft.Text("Error loading profile", color="red")]
            )

        back_button = ft.Container(ft.OutlinedButton(
            on_click=lambda _: self.page.go("/admin"),
            icon=ft.Icons.ARROW_BACK

        ),
        alignment=ft.alignment.center_left)
        # Navbar
        navbar = DashboardNavBar(
            page=self.page,
            title="My Profile",
            user_email=self.session.get_email() or "",
            show_add_button=False,
            on_logout=lambda _: self._logout()
        ).view()

        footer = Footer().view()

        # helper to avoid static typing issues with Page.snack_bar
        page_any = self.page

        # Use shared ProfileSection component for profile + account settings
        profile_comp = ProfileSection(self.page, on_update=lambda: self.page.update())

        # Admin-level security controls
        # Make these instance attributes so other handlers can access them
        self.enable_2fa_checkbox = ft.Checkbox(label="Enable 2FA (system-wide)", value=SettingsService.get_security_settings().enable_2fa if hasattr(SettingsService, 'get_security_settings') else False)
        self.password_min_length_field = ft.TextField(label="Password min length (system-wide)", value=str(SettingsService.get_security_settings().password_min_length if hasattr(SettingsService, 'get_security_settings') else 8), keyboard_type=ft.KeyboardType.NUMBER)

        def _save_admin_settings(e):
            # Update profile via ProfileSection state
            try:
                user_id = self.session.get_user_id()
                full_name = f"{profile_comp.state.first_name} {profile_comp.state.last_name}".strip()
                email = profile_comp.state.email
                # Debug: log values being saved
                try:
                    print(f"[AdminProfileView] Saving admin profile user_id={user_id} full_name={full_name} email={email}", file=__import__('sys').stderr)
                except Exception:
                    pass

                if not user_id:
                    page_any.open(ft.SnackBar(ft.Text("Invalid user ID"), bgcolor="#F44336"))
                    return

                ok, msg = self.admin_service.update_user_account(user_id, full_name, email, role=self.session.get_role() or 'admin', is_active=True)
                try:
                    print(f"[AdminProfileView] update_user_account returned: ok={ok} msg={msg}", file=__import__('sys').stderr)
                except Exception:
                    pass
                if not ok:
                    page_any.open(ft.SnackBar(ft.Text(f"Failed to update profile: {msg}"), bgcolor="#F44336"))
                    page_any.update()
                    return
                # Update system security settings
                try:
                    pwd_field = getattr(self, 'password_min_length_field', None)
                    if pwd_field and getattr(pwd_field, 'value', None):
                        pwd_min_int = int(pwd_field.value)
                        SettingsService.update_setting('security', 'password_min_length', pwd_min_int)
                except Exception:
                    pass
                enable_2fa_checkbox = getattr(self, 'enable_2fa_checkbox', None)
                if enable_2fa_checkbox:
                    SettingsService.update_setting('security', 'enable_2fa', bool(enable_2fa_checkbox.value))
                if user_id:
                    ActivityService.log_activity(user_id, "Admin Profile Updated", f"Admin {user_id} updated profile and security settings")
                page_any.open(ft.SnackBar(ft.Text("Profile updated"), bgcolor="#4CAF50"))
                # Defensive re-fetch: refresh the profile component state and session values
                try:
                    if user_id:
                        refreshed = self.admin_service.get_user_by_id(user_id)
                        if refreshed:
                            # refreshed is a User object; update session from its attributes
                            try:
                                self.page.session.set("email", getattr(refreshed, 'email', None) or self.page.session.get("email"))
                                self.page.session.set("full_name", getattr(refreshed, 'full_name', None) or self.page.session.get("full_name"))
                                # also update avatar if available on refreshed user (some adapters store it)
                                try:
                                    avatar_val = getattr(refreshed, 'avatar', None)
                                    if avatar_val:
                                        self.page.session.set("avatar", avatar_val)
                                except Exception:
                                    pass
                            except Exception:
                                pass
                        # Request UI update
                        if callable(profile_comp.on_update):
                            profile_comp.on_update()
                        else:
                            page_any.update()
                except Exception:
                    pass

                page_any.update()
            except Exception as ex:
                page_any.open(ft.SnackBar(ft.Text(f"Error saving admin profile: {ex}"), bgcolor="#F44336"))
                page_any.update()

        def _confirm_save(e):
            confirm = ft.AlertDialog(
                title=ft.Text("Confirm Save"),
                content=ft.Text("Save all admin profile changes and system security settings?"),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda ev: page_any.close(confirm)),
                    ft.ElevatedButton("Save", on_click=lambda ev: (_save_admin_settings(ev), page_any.close(confirm)))
                ]
            )
            page_any.open(confirm)

        def _confirm_logout(e):
            confirm = ft.AlertDialog(
                title=ft.Text("Confirm Logout"),
                content=ft.Text("Are you sure you want to log out?"),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda ev: page_any.close(confirm)),
                    ft.ElevatedButton("Log Out", on_click=lambda ev: (self._logout(), page_any.close(confirm)))
                ]
            )
            page_any.open(confirm)

        # Build tabbed profile layout similar to tenant dashboard
        active_tab = ["personal_info"]

        def switch_tab(tab_name: str):
            active_tab[0] = tab_name
            refresh_content()

        def create_tab_button(label: str, tab_id: str):
            is_active = active_tab[0] == tab_id
            return ft.Container(
                content=ft.Text(label, weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL, color=ft.Colors.BLACK if is_active else ft.Colors.GREY_600),
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
                border=ft.border.all(2, ft.Colors.BLACK) if is_active else None,
                border_radius=20,
                on_click=lambda ev: switch_tab(tab_id),
                ink=True,
            )

        tab_definitions = [
            ("Personal Info", "personal_info"),
            ("Account Settings", "account_settings"),
            ("Admin Settings", "admin_settings"),
        ]

        tabs = ft.Row(
            controls=[*(create_tab_button(label, tab_id) for label, tab_id in tab_definitions)],
            wrap=True,
            alignment=ft.MainAxisAlignment.START,
            spacing=10,
        )

        content_area = ft.Column(spacing=20)

        def get_admin_settings_section():
            controls = [
                ft.Text("System Security Settings", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
            ]
            # only include optional controls if they are not None to satisfy type checks
            if getattr(self, "enable_2fa_checkbox", None) is not None:
                controls.append(self.enable_2fa_checkbox)
            if getattr(self, "password_min_length_field", None) is not None:
                controls.append(self.password_min_length_field)

            controls.extend([
                ft.Divider(),
                ft.Row(controls=[
                    ft.ElevatedButton("Save Changes", on_click=_confirm_save, bgcolor="#4CAF50", color="white"),
                    ft.ElevatedButton("Log Out", on_click=_confirm_logout, bgcolor="red", color="white"),
                ], alignment=ft.MainAxisAlignment.END),
            ])

            return ft.Column(
                controls=controls,
                spacing=12,
            )

        def refresh_content():
            content_area.controls.clear()
            if active_tab[0] == "personal_info":
                # Don't reload state here - it would reset unsaved changes in other tabs
                # State is only reloaded after successful save or initial load
                content_area.controls.extend([profile_comp.get_profile_info(), ft.Container(height=20)])
            elif active_tab[0] == "account_settings":
                content_area.controls.append(profile_comp.get_account_settings())
            elif active_tab[0] == "admin_settings":
                content_area.controls.append(get_admin_settings_section())

            tabs.controls.clear()
            tabs.controls.extend([create_tab_button(label, tab_id) for label, tab_id in tab_definitions])
            self.page.update()

        def on_resize(event):
            width = self.page.width or 0
            is_small_screen = width < 800
            if is_small_screen:
                padding_val = ft.padding.symmetric(horizontal=20, vertical=20)
                tabs.alignment = ft.MainAxisAlignment.CENTER
            else:
                padding_val = ft.padding.symmetric(horizontal=50, vertical=30)
                tabs.alignment = ft.MainAxisAlignment.START
            # adjust container padding by rebuilding the main container below during view creation
            self.page.update()

        self.page.on_resized = on_resize

        main_scroll_area = ft.ListView(
            controls=[
                back_button,
                ft.Text("My Profile", size=28, weight=ft.FontWeight.BOLD),
                ft.Container(height=20),
                tabs,
                ft.Container(height=20),
                content_area,
            ],
            expand=True,
            spacing=0,
        )

        main_container = ft.Container(
            content=main_scroll_area,
            padding=ft.padding.symmetric(horizontal=40, vertical=30),
            bgcolor="white",
            border_radius=12,
        )

        # ensure ProfileSection triggers a refresh of the admin layout when it updates
        try:
            profile_comp.on_update = refresh_content
        except Exception:
            pass

        # initial populate
        refresh_content()

        return ft.View(
            "/admin_profile",
            scroll=ft.ScrollMode.AUTO,
            controls=[navbar, ft.Container(padding=40, content=ft.Column(spacing=20, controls=[ft.Container(content=main_container)])), footer],
        )

    def _logout(self):
        self.session.logout()
        self.page.go("/")

    def _handle_save(self, e):
        # Read form controls by key (fall back to stored profile/session values)
        page_any = self.page
        user_id = self.session.get_user_id()
        if not user_id:
            page_any.go("/login")
            return

        try:
            import traceback
            print(f"[AdminProfileView._handle_save] invoked for user_id={user_id}")
            if getattr(self, 'full_name_field', None) and hasattr(self.full_name_field, 'value') and self.full_name_field.value is not None:
                full_name = self.full_name_field.value.strip()
            else:
                # try fetching existing profile
                try:
                    prof = self.admin_service.get_user_by_id(user_id)
                    full_name = getattr(prof, 'full_name', None) or f"{self.session.get_full_name() or ''}".strip() if prof else (self.session.get_full_name() or "").strip()
                except Exception:
                    full_name = (self.session.get_full_name() or "").strip()

            if getattr(self, 'email_field', None) and hasattr(self.email_field, 'value') and self.email_field.value is not None:
                email = self.email_field.value.strip()
            else:
                try:
                    prof = prof if 'prof' in locals() else self.admin_service.get_user_by_id(user_id)
                    email = getattr(prof, 'email', None) or self.session.get_email() or "" if prof else (self.session.get_email() or "")
                except Exception:
                    email = self.session.get_email() or ""

            password = (getattr(self, 'password_field', None) and getattr(self.password_field, 'value', None)) or ""
            confirm = (getattr(self, 'confirm_password_field', None) and getattr(self.confirm_password_field, 'value', None)) or ""
            enable_2fa_val = bool(getattr(self, 'enable_2fa_checkbox', None) and getattr(self.enable_2fa_checkbox, 'value', False))
            pwd_min = getattr(self, 'password_min_length_field', None) and getattr(self.password_min_length_field, 'value', None)
        except Exception:
            page_any.open(ft.SnackBar(ft.Text("Error reading form fields"), bgcolor="#F44336"))
            page_any.update()
            return
        # Validate basic fields
        if not full_name or not email:
            page_any.open(ft.SnackBar(ft.Text("Name and email are required"), bgcolor="#F44336"))
            page_any.update()
            return

        # Update user info
        ok, msg = self.admin_service.update_user_account(user_id, full_name, email, role=self.session.get_role() or 'admin', is_active=True)
        if not ok:
            page_any.open(ft.SnackBar(ft.Text(f"Failed to update profile: {msg}"), bgcolor="#F44336"))
            page_any.update()
            return

        # Update password if provided
        if password:
            if password != confirm:
                page_any.open(ft.SnackBar(ft.Text("Passwords do not match"), bgcolor="#F44336"))
                page_any.update()
                return
            okp, msgp = self.admin_service.reset_user_password(user_id, password)
            if not okp:
                page_any.open(ft.SnackBar(ft.Text(f"Failed to update password: {msgp}"), bgcolor="#F44336"))
                page_any.update()
                return

        # Update system security settings (admin-level)
        try:
            # password_min_length
            try:
                pwd_min_int = int(pwd_min) if pwd_min is not None else None
                if pwd_min_int is not None:
                    SettingsService.update_setting('security', 'password_min_length', pwd_min_int)
            except Exception:
                pass

            # enable_2fa
            SettingsService.update_setting('security', 'enable_2fa', bool(enable_2fa_val))
        except Exception:
            pass

        # Log activity
        try:
            ActivityService.log_activity(user_id, "Admin Profile Updated", f"Admin {user_id} updated profile and security settings")
        except Exception:
            pass

        # Notify refresh and show feedback
        try:
            from services.refresh_service import notify as _notify
            _notify()
        except Exception:
            pass

        page_any.open(ft.SnackBar(ft.Text("Profile updated"), bgcolor="#4CAF50"))
        page_any.update()

