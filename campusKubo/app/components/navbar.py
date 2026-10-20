"""Navigation bar components."""

from typing import Callable, Iterable, Optional

import flet as ft
import os
from components.profile_section import ProfileSection
from components.logo import Logo
from components.sidebar import Sidebar


def _resolve_profile_image_path(user_id: int | None) -> str | None:
    """Locate a user profile photo across the known upload locations."""
    if not user_id:
        return None

    candidates = [
        os.path.join("assets", "uploads", "profile_photos", f"profile_{user_id}.png"),
        os.path.join("uploads", "profile_photos", f"profile_{user_id}.png"),
        os.path.join("app", "assets", "profile_photos", f"profile_{user_id}.png"),
        os.path.join("app", "assets", "uploads", "profile_photos", f"profile_{user_id}.png"),
    ]

    for candidate in candidates:
        abs_path = os.path.abspath(candidate)
        if os.path.exists(abs_path):
            return abs_path

    return os.path.abspath(candidates[0]) if candidates else None


class NavBar:
    """Top navigation bar component for guests/browsing."""

    def __init__(self, page: ft.Page, show_auth_buttons: bool = True):
        self.page = page
        self.show_auth_buttons = show_auth_buttons

    def view(self):
        logo_section = Logo(size=22, color="#1A1A1A")

        auth_buttons = (
            ft.Row(
                spacing=12,
                controls=[
                    ft.TextButton("Login", on_click=lambda _: self.page.go("/login")),
                    ft.TextButton("Register", on_click=lambda _: self.page.go("/signup")),
                ]
            ) if self.show_auth_buttons else ft.Container()
        )

        return ft.Container(
            bgcolor="#FFFFFF",
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color="#00000008",
                offset=ft.Offset(0, 2)
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    logo_section,
                    auth_buttons
                ]
            )
        )


class DashboardNavBar:
    """Dashboard navigation bar with user info"""

    def __init__(
        self,
        page: ft.Page,
        title: str,
        user_email: str,
        role: str = "admin",
        show_add_button: bool = False,
        on_add_click=None,
        on_logout=None
    ):
        self.page = page
        self.title = title
        self.user_email = user_email
        self.role = role
        self.show_add_button = show_add_button
        self.on_add_click = on_add_click
        self.on_logout = on_logout
        self.sidebar = Sidebar(self.page, self.role)

    def view(self):
        # Logo section
        # Build a clickable square avatar and show the user's full name + email
        user_id = self.page.session.get("user_id")
        full_name = self.page.session.get("full_name") or self.user_email or "User"
        initials = "".join([part[0].upper() for part in full_name.split()[:2] if part]) or "U"

        # Prefer an avatar explicitly stored in session (updated after upload).
        session_avatar = None
        try:
            session_avatar = self.page.session.get("avatar")
        except Exception:
            try:
                session_avatar = self.page.session["avatar"] if "avatar" in self.page.session else None
            except Exception:
                session_avatar = None

        profile_image_path = None
        if session_avatar:
            if isinstance(session_avatar, str) and (session_avatar.startswith("http://") or session_avatar.startswith("https://") or os.path.exists(session_avatar)):
                profile_image_path = session_avatar

        if not profile_image_path:
            profile_image_path = _resolve_profile_image_path(user_id)

        has_profile_image = profile_image_path and (profile_image_path.startswith("http") or os.path.exists(profile_image_path))

        def _open_profile(e=None):
            # Navigate to the admin profile page (page, not modal)
            try:
                self.page.go("/admin_profile")
            except Exception:
                # Fallback: try direct navigation via page.route if available
                try:
                    self.page.route = "/admin_profile"
                    self.page.update()
                except Exception:
                    pass

        if has_profile_image:
            avatar = ft.Container(
                width=40,
                height=40,
                border_radius=6,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                content=ft.Image(src=profile_image_path, width=40, height=40, fit=ft.ImageFit.COVER),
                on_click=self.sidebar.open_sidebar,
                tooltip="Open menu",
            )
        else:
            avatar = ft.Container(
                width=40,
                height=40,
                border_radius=6,
                bgcolor="#0078FF",
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[ft.Text(initials, color="white", weight=ft.FontWeight.BOLD)],
                ),
                on_click=self.sidebar.open_sidebar,
                tooltip="Open menu",
            )

        logo_section = ft.Row(
            spacing=8,
            controls=[
                avatar,
                ft.Column(
                    spacing=0,
                    controls=[
                        ft.Text(full_name, size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(self.user_email, size=12, color=ft.Colors.BLACK)
                    ]
                )
            ]
        )


        # Action buttons
        action_buttons = []

        if self.show_add_button:
            action_buttons.append(
                ft.ElevatedButton(
                    "Add New Listing",
                    icon=ft.Icons.ADD_CIRCLE,
                    bgcolor="#0078FF",
                    color="white",
                    on_click=self.on_add_click
                )
            )

        # ADMIN / DASHBOARD PROFILE BUTTON - opens inline ProfileSection dialog
        def _open_profile(e):
            try:
                profile_comp = ProfileSection(self.page, on_update=lambda: self.page.update())
                content = profile_comp.get_tabbed_view()
                dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("My Profile"),
                    content=ft.Container(content=content, width=760),
                    actions=[ft.TextButton("Close", on_click=lambda ev: self.page.close(dialog))]
                )
                self.page.open(dialog)
            except Exception:
                # Fallback to route if dialog cannot be opened
                try:
                    self.page.go("/admin_profile")
                except Exception:
                    pass

        logout_button = ft.OutlinedButton(
            "Logout",
            icon=ft.Icons.LOGOUT,
            on_click=self.on_logout
        )

        # Global refresh button (not shown on all pages) - will call RefreshService
        try:
            from services.refresh_service import notify as _global_refresh
            action_buttons.insert(0, ft.IconButton(icon=ft.Icons.REFRESH, tooltip="Refresh", on_click=lambda e: _global_refresh()))
        except Exception:
            # If the refresh service cannot be imported (tests or other contexts), skip it
            pass

        # Only keep refresh (if available) and logout in the action area
        action_buttons.append(logout_button)

        return ft.Container(
            bgcolor="#FFFFFF",
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color="#00000008",
                offset=ft.Offset(0, 2)
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    logo_section,
                    ft.Row(spacing=10, controls=action_buttons)
                ]
            )
        )


class RegisteredUserNavBar:
    """Navbar for logged-in users with avatar, notifications, messages, and logout."""

    def __init__(
        self,
        page: ft.Page,
        open_sidebar_callback: Callable[[ft.ControlEvent], None],
        brand_controls: Optional[Iterable[ft.Control]] = None,
        extra_actions: Optional[Iterable[ft.Control]] = None,
        on_notifications: Optional[Callable[[ft.ControlEvent], None]] = None,
        on_messages: Optional[Callable[[ft.ControlEvent], None]] = None,
        on_logout: Optional[Callable[[ft.ControlEvent], None]] = None,
    ) -> None:
        self.page = page
        self.open_sidebar_callback = open_sidebar_callback
        self.brand_controls = list(brand_controls or [
            Logo(size=24, color="#1A1A1A")
        ])
        self.extra_actions = list(extra_actions or [])
        self.on_notifications = on_notifications
        self.on_messages = on_messages
        self.on_logout = on_logout

    def _build_avatar(self) -> ft.Control:
        """Build an avatar using a profile photo when available, otherwise user initials."""
        user_id = self.page.session.get("user_id")
        full_name = self.page.session.get("full_name") or self.page.session.get("email") or "User"
        initials = "".join([part[0].upper() for part in full_name.split()[:2] if part]) or "U"

        # prefer session avatar if present
        session_avatar = None
        try:
            session_avatar = self.page.session.get("avatar")
        except Exception:
            try:
                session_avatar = self.page.session["avatar"] if "avatar" in self.page.session else None
            except Exception:
                session_avatar = None

        profile_image_path = None
        if session_avatar:
            if isinstance(session_avatar, str) and (session_avatar.startswith("http://") or session_avatar.startswith("https://") or os.path.exists(session_avatar)):
                profile_image_path = session_avatar

        if not profile_image_path:
            profile_image_path = _resolve_profile_image_path(user_id)

        has_profile_image = profile_image_path and (profile_image_path.startswith("http") or os.path.exists(profile_image_path))

        if has_profile_image:
            return ft.Container(
                width=36,
                height=36,
                border_radius=18,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                content=ft.Image(
                    src=profile_image_path,
                    width=36,
                    height=36,
                    fit=ft.ImageFit.COVER,
                ),
                on_click=self.open_sidebar_callback,
                tooltip="Open menu",
            )

        return ft.Container(
            content=ft.CircleAvatar(
                content=ft.Text(initials, color="white", weight= ft.FontWeight.BOLD),
                bgcolor="#0078FF",
                radius=18,
            ),
            on_click=self.open_sidebar_callback,
            tooltip="Open menu",
        )

    def _show_snack_bar(self, message: str, action_color: str = "#FFFFFF") -> None:
        self.page.open(ft.SnackBar(
            content=ft.Text(message),
            bgcolor="#333333",
            action="OK",
            margin=ft.padding.only(bottom=48),
            action_color=action_color,


        ))
        self.page.update()

    def _default_notifications(self, e: ft.ControlEvent) -> None:
        self._show_snack_bar("Notifications feature coming soon.")

    def _default_messages(self, e: ft.ControlEvent) -> None:
        self._show_snack_bar("Messages feature coming soon.", action_color="#0078FF")

    def _default_logout(self, e: ft.ControlEvent) -> None:
        self.page.go("/logout")

    def build(self) -> ft.Row:
        avatar = self._build_avatar()

        brand_row = ft.Row(
            controls=self.brand_controls,
            spacing=2,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        actions = list(self.extra_actions)
        actions.extend(
            [
                ft.IconButton(
                    icon=ft.Icons.NOTIFICATIONS_OUTLINED,
                    tooltip="Notifications",
                    icon_color="#000000",
                    on_click=self.on_notifications or self._default_notifications,
                ),
                ft.IconButton(
                    icon=ft.Icons.CHAT_BUBBLE_OUTLINE,
                    tooltip="Messages",
                    icon_color="#000000",
                    on_click=self.on_messages or self._default_messages,
                ),
                ft.IconButton(
                    icon=ft.Icons.LOGOUT,
                    tooltip="Logout",
                    icon_color="#D32F2F",
                    on_click=self.on_logout or self._default_logout,
                ),
            ]
        )

        return ft.Row(
            controls=[
                avatar,
                brand_row,
                ft.Container(expand=True),
                *actions,
            ],
            spacing=8,
            vertical_alignment= ft.CrossAxisAlignment.CENTER,
        )
