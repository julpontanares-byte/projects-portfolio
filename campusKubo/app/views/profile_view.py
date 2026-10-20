"""Profile view for tenants, PMs, and admins"""
import flet as ft
from state.session_state import SessionState
from storage.db import (
    get_user_by_id,
    update_user_settings,
    update_user_address,
    update_user_password

)


class ProfileView:
    def __init__(self, page: ft.Page, role: str):
        self.page = page
        self.role = role  # 'tenant', 'pm', 'admin'
        self.session = SessionState(page)
        self.user_id = self.session.get_user_id()
        if not self.user_id:
            raise ValueError("User not logged in")
        self.db = None  # Will set to db module
        self.active_tab = "personal_info"
        self.password_visible = False
        self.popup_notifications = True
        self.chat_notifications = True
        self.email_notifications = True
        self.notification_preferences = {
            "reservation_confirmation": True,
            "cancellation": True,
            "payment_update": True,
            "rent_reminders": True
        }
        self.saved_listings = []
        self.reservations = []
        self.first_name = ""
        self.last_name = ""
        self.gender = ""
        self.email = ""
        self.phone = ""
        self.house_no = ""
        self.street = ""
        self.barangay = ""
        self.city = ""
        self.avatar_url = ""
        self.password = ""
        self.actual_password = ""

    def load_user_data(self):
        if self.user_id:
            user = get_user_by_id(self.user_id)
            if user:
                # Handle both dict and object responses
                def get_attr(obj, key, default=''):
                    if isinstance(obj, dict):
                        return obj.get(key, default)
                    return getattr(obj, key, default)

                self.first_name = get_attr(user, 'first_name', '')
                self.last_name = get_attr(user, 'last_name', '')
                self.gender = get_attr(user, 'gender', '')
                self.email = get_attr(user, 'email', '')
                self.phone = get_attr(user, 'phone', '')
                self.house_no = get_attr(user, 'house_no', '')
                self.street = get_attr(user, 'street', '')
                self.barangay = get_attr(user, 'barangay', '')
                self.city = get_attr(user, 'city', '')
                self.avatar_url = get_attr(user, 'avatar_url', '')

                # Don't expose actual password
                self.password = "••••••••"
                self.actual_password = ""

    def load_saved_listings(self):
        # For tenant, load saved listings
        if self.role == 'tenant':
            # Implement loading saved listings
            pass

    def load_reservations(self):
        # Load reservations
        pass

    def switch_tab(self, tab_name):
        self.active_tab = tab_name
        # Rebuild the view if needed
        self.page.update()



    def build(self):
        self.load_user_data()

        # Simple profile view
        header = ft.Container(
            bgcolor="#FFFFFF",
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color="#00000010"),
            content=ft.Row(
                controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: self.page.go(f"/{self.role}")),
                    ft.Text(f"{self.role.title()} Profile", size=24, weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.START
            )
        )

        content = ft.Container(
            padding=ft.padding.all(20),
            content=ft.Column(
                controls=[
                    ft.Text(f"Name: {self.first_name} {self.last_name}"),
                    ft.Text(f"Email: {self.email}"),
                    ft.Text(f"Phone: {self.phone}"),
                ],
                spacing=10
            )
        )

        return ft.View(
            f"/{self.role}_profile",
            controls=[
                ft.Column(
                    controls=[header, content],
                    expand=True
                )
            ]
        )