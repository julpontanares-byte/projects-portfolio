import flet as ft
import os
from typing import Optional

class Sidebar:
    def __init__(self, page: ft.Page, role: str = "tenant"):
        self.page = page
        self.role = role.lower()
        self.sidebar_visible = False
        self.sidebar_overlay = None

    def create_sidebar(self):
        user_id = self.page.session.get("user_id")
        full_name = self.page.session.get("full_name") or self.page.session.get("email") or "User"

        # Get profile picture
        profile_dir = "uploads/profile_photos"
        profile_image_path = os.path.abspath(os.path.join(profile_dir, f"profile_{user_id}.png")) if user_id else None
        has_profile_image = profile_image_path and os.path.exists(profile_image_path)

        # Profile picture
        if has_profile_image:
            profile_avatar_sidebar = ft.Container(
                width=50,
                height=50,
                border_radius=25,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                content=ft.Image(
                    src=profile_image_path,
                    width=50,
                    height=50,
                    fit=ft.ImageFit.COVER,
                ),
            )
        else:
            initials = "".join([part[0].upper() for part in full_name.split()[:2] if part]) or "U"
            profile_avatar_sidebar = ft.CircleAvatar(
                content=ft.Text(initials, color="white", weight="bold"),
                bgcolor="#0078FF",
                radius=25,
            )

        # Navigation items based on role
        if self.role == "pm":
            nav_items = [
                {"icon": ft.Icons.DASHBOARD, "label": "Dashboard", "route": "/pm"},
                {"icon": ft.Icons.HOME, "label": "Rooms", "route": "/rooms"},
                {"icon": ft.Icons.PEOPLE, "label": "My Tenants", "route": "/my-tenants"},
                {"icon": ft.Icons.ANALYTICS, "label": "Analytics", "route": "/pm/analytics"},
                {"icon": ft.Icons.SETTINGS, "label": "Setting", "route": "/pm/profile"},
            ]
            role_display = "Property Manager"
        elif self.role == "admin":
            nav_items = [
                {"icon": ft.Icons.DASHBOARD, "label": "Dashboard", "route": "/admin"},
                {"icon": ft.Icons.PEOPLE, "label": "Users", "route": "/admin_users"},
                {"icon": ft.Icons.HOME, "label": "Listings", "route": "/admin_listings"},
                {"icon": ft.Icons.PAYMENT, "label": "Payments", "route": "/admin_payments"},
                {"icon": ft.Icons.REPORT, "label": "Reports", "route": "/admin_reports"},
                {"icon": ft.Icons.SETTINGS, "label": "Settings", "route": "/admin_profile"},
            ]
            role_display = "Administrator"
        else:  # tenant
            nav_items = [
                {"icon": ft.Icons.DASHBOARD, "label": "Dashboard", "route": "/tenant"},
                {"icon": ft.Icons.SEARCH, "label": "Browse", "route": "/browse"},
                {"icon": ft.Icons.SETTINGS, "label": "Profile", "route": "/tenant/profile"},
            ]
            role_display = "Tenant"

        def create_nav_item(item, is_active=False):
            def on_nav_click(e):
                self.close_sidebar(e)
                if item["route"]:
                    self.page.go(item["route"])
                else:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"{item['label']} feature coming soon!"),
                        bgcolor="#333333",
                        action="OK",
                        action_color="#0078FF",
                        margin=ft.margin.only(bottom=48),
                    )
                    self.page.snack_bar.open = True
                    self.page.update()

            # Create the navigation row
            nav_content = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(item["icon"], color="white", size=20),
                        ft.Text(item["label"], color="white", size=14, weight="bold" if is_active else "normal"),
                    ],
                    spacing=12,
                    vertical_alignment="center",
                ),
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
                on_click=on_nav_click,
                bgcolor="transparent",
                border_radius=8,
            )

            # Wrap in Stack to position indicator bar outside sidebar
            if is_active:
                return ft.Stack(
                    controls=[
                        nav_content,
                        # Orange indicator bar positioned to the left, outside the sidebar
                        ft.Container(
                            width=4,
                            height=32,
                            bgcolor="#FF6B35",
                            border_radius=2,
                            left=-4,
                            top=8,
                        ),
                    ],
                )
            else:
                return nav_content

        # Determine active route
        current_route = self.page.route
        active_label = None
        for item in nav_items:
            if item["route"] and (current_route == item["route"] or current_route.startswith(item["route"] + "/")):
                active_label = item["label"]
                break
        if not active_label:
            active_label = nav_items[0]["label"] if nav_items else None

        sidebar_column = ft.Column(
            spacing=0,
            expand=True,
            scroll="AUTO",
            controls=[
                # User Profile Section - improved styling
                ft.Container(
                    padding=ft.padding.all(24),
                    bgcolor="#4A3A8A",  # Slightly lighter purple for profile section
                    border_radius=0,
                    content=ft.Row(
                        controls=[
                            profile_avatar_sidebar,
                            ft.Column(
                                spacing=6,
                                expand=True,
                                controls=[
                                    ft.Text(
                                        full_name,
                                        color="white",
                                        size=18,
                                        weight="bold",
                                    ),
                                    ft.Text(
                                        role_display,
                                        color="white",
                                        size=13,
                                        opacity=0.9,
                                    ),
                                ],
                            ),
                            ft.IconButton(
                                icon=ft.Icons.KEYBOARD_ARROW_DOWN,
                                icon_color="white",
                                icon_size=20,
                                tooltip="More options",
                            ),
                        ],
                        spacing=14,
                        vertical_alignment="center",
                    ),
                ),
                ft.Divider(color="white", opacity=0.2, height=1),
                # Navigation Items
                ft.Container(
                    padding=ft.padding.symmetric(vertical=10),
                    expand=True,
                    content=ft.Column(
                        spacing=4,
                        controls=[
                            create_nav_item(item, is_active=(item["label"] == active_label))
                            for item in nav_items
                        ] + [
                            # Logout button after settings
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.LOGOUT, color="white", size=20),
                                        ft.Text("Logout", color="white", size=14, weight="normal"),
                                    ],
                                    spacing=12,
                                    vertical_alignment="center",
                                ),
                                padding=ft.padding.symmetric(horizontal=20, vertical=12),
                                on_click=lambda e: (self.close_sidebar(e), self.page.go("/logout")),
                                bgcolor="transparent",
                                border_radius=8,
                            )
                        ],
                    ),
                ),
            ],
        )

        return sidebar_column

    def create_sidebar_overlay(self):
        sidebar_content = self.create_sidebar()

        # Backdrop to close sidebar
        backdrop = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=self.close_sidebar,
            content=ft.Container(
                expand=True,
                bgcolor="#00000040",
            ),
        )

        # Sidebar container - darker purple with square edges
        # Start off-screen to the left, then animate in
        sidebar_container = ft.Container(
            width=280,
            left=-280,  # Start off-screen to the left
            top=0,
            height=self.page.height if hasattr(self.page, 'height') and self.page.height else None,
            bottom=0 if not (hasattr(self.page, 'height') and self.page.height) else None,
            bgcolor="#3F2E7A",
            border_radius=0,
            content=sidebar_content,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        )

        return ft.Stack(
            expand=True,
            controls=[
                backdrop,
                sidebar_container,
            ],
            clip_behavior=ft.ClipBehavior.NONE,  # Allow indicator bars to extend outside
        )

    def open_sidebar(self, e):
        try:
            # Check if user is logged in
            if not self.page.session.get("user_id"):
                self.page.go("/login")
                return

            # Close if already open
            if self.sidebar_visible and self.sidebar_overlay:
                self.close_sidebar(e)
                return

            # Create and show sidebar
            self.sidebar_overlay = self.create_sidebar_overlay()
            self.page.overlay.append(self.sidebar_overlay)
            self.sidebar_visible = True
            self.page.update()

            # Animate sidebar sliding in from left
            # Find the sidebar container in the overlay
            for control in self.sidebar_overlay.controls:
                if isinstance(control, ft.Container) and control.bgcolor == "#3F2E7A":
                    # Animate from left=-280 to left=0
                    control.left = 0
                    control.update()
                    break

            print("Sidebar opened")  # Debug
        except Exception as ex:
            print(f"Error opening sidebar: {ex}")
            import traceback
            traceback.print_exc()
            # Show error message instead of navigating
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error opening menu: {str(ex)}"),
                bgcolor="#F44336",
                action="OK",
                action_color="white",
                margin=ft.padding.only(bottom=48),
            )
            self.page.snack_bar.open = True
            self.page.update()

    def close_sidebar(self, e=None):
        try:
            if self.sidebar_visible and self.sidebar_overlay:
                # Store reference for nested function
                overlay_to_remove = self.sidebar_overlay

                # Animate sidebar sliding out to the left
                for control in self.sidebar_overlay.controls:
                    if isinstance(control, ft.Container) and control.bgcolor == "#3F2E7A":
                        control.left = -280  # Slide out to the left
                        control.update()
                        # Remove after a short delay for animation
                        def remove_after_animation():
                            try:
                                self.page.overlay.remove(overlay_to_remove)
                                self.sidebar_visible = False
                                self.page.update()
                            except:
                                pass

                        import threading
                        threading.Timer(0.3, remove_after_animation).start()
                        return

                # Fallback: remove immediately if container not found
                self.page.overlay.remove(self.sidebar_overlay)
                self.sidebar_visible = False
                self.page.update()
        except Exception as ex:
            print(f"Error closing sidebar: {ex}")
            import traceback
            traceback.print_exc()