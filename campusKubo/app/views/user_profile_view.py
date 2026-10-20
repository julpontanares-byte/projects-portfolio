"""
User profile view (Tenant Profile)
"""
import flet as ft
from services.user_service import UserService
from services.reservation_service import ReservationService
from state.session_state import SessionState
from components.profile_section import ProfileSection


class UserProfileView:
    """User profile view for a logged-in user"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.session = SessionState(page)
        self.user_service = UserService()
        self.reservation_service = ReservationService()

    def build(self):
        # require authentication
        if not self.session.require_auth():
            return None

        user_id = self.session.get_user_id()
        email = self.session.get_email()

        # Fetch user object
        user = None
        if user_id:
            user = self.user_service.get_user_by_id(user_id)
        if not user and email:
            user = self.user_service.get_user_by_email(email)

        if not user:
            # Could not find user, log out and redirect
            self.session.logout()
            self.page.go('/login')
            return None

        # Load reservations for this user (returns rows)
        reservations = self.reservation_service.get_user_reservations(user.id)

        # Shared profile component
        profile_comp = ProfileSection(self.page, on_update=lambda: self.page.update())
        profile_section = ft.Container(
            bgcolor="#FFFFFF",
            padding=20,
            border_radius=8,
            content=ft.Column(
                spacing=10,
                controls=[
                    profile_comp.get_profile_info(),
                    ft.Divider(),
                    profile_comp.get_account_settings(),
                ],
            ),
        )

        # Reservations section
        reservation_cards = []
        for res in reservations:
            # Support both sqlite3.Row and tuple
            addr = res['address'] if isinstance(res, dict) or hasattr(res, 'keys') and 'address' in res.keys() else (res[3] if len(res) > 3 else 'Unknown')
            price = res['price'] if isinstance(res, dict) or (hasattr(res, 'keys') and 'price' in res.keys()) else (res[4] if len(res) > 4 else 0)
            start_date = res['start_date'] if 'start_date' in getattr(res, 'keys', lambda: [])() else (res[0] if len(res) > 0 else '')
            end_date = res['end_date'] if 'end_date' in getattr(res, 'keys', lambda: [])() else (res[1] if len(res) > 1 else '')
            status = res['status'] if 'status' in getattr(res, 'keys', lambda: [])() else (res[5] if len(res) > 5 else 'pending')

            reservation_cards.append(
                ft.Container(
                    bgcolor="#FFFFFF",
                    padding=16,
                    border_radius=8,
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            ft.Text(addr, size=16, weight=ft.FontWeight.BOLD),
                            ft.Text(f"₱{price:,.0f}/month" if price else "Price N/A", size=14, color="#0078FF"),
                            ft.Text(f"Check-in: {start_date}", size=12),
                            ft.Text(f"Check-out: {end_date}", size=12),
                            ft.Container(content=ft.Text(status.upper(), size=12, color="white"), bgcolor=("#4CAF50" if status == 'confirmed' else "#FFA726"), padding=ft.padding.symmetric(horizontal=8, vertical=4), border_radius=4)
                        ]
                    )
                )
            )

        reservations_section = ft.Container(
            bgcolor="#FFFFFF",
            padding=20,
            border_radius=8,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Text("My Reservations", size=20, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Column(spacing=10, controls=reservation_cards if reservation_cards else [ft.Text("No reservations yet")])
                ]
            )
        )

        # Page layout
        return ft.View(
            "/profile",
            padding=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(bgcolor="#FFFFFF", padding=ft.padding.symmetric(horizontal=20, vertical=12), content=ft.Row(controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: self.page.go('/tenant')),
                    ft.Text("My Profile", size=20, weight=ft.FontWeight.BOLD)
                ])),
                ft.Container(padding=20, content=ft.Column(spacing=20, controls=[profile_section, reservations_section]))
            ]
        )