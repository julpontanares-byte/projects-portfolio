"""
Tenant Reservations View
"""
import flet as ft
from state.session_state import SessionState
from services.reservation_service import ReservationService
from storage.db import get_listing_by_id


class TenantReservationsView:
    """View for tenant to see their reservations"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.session = SessionState(page)
        self.reservation_service = ReservationService()

    def build(self):
        """Build the reservations view"""
        # Require authentication
        if not self.session.require_auth():
            return None

        user_id = self.session.get_user_id()
        if not user_id:
            self.page.go("/login")
            return None

        # Get user's reservations
        reservations = self.reservation_service.get_user_reservations(user_id)

        # Create reservation cards
        reservation_cards = []
        if reservations:
            for reservation in reservations:
                # Get listing details
                listing = get_listing_by_id(reservation.listing_id) if hasattr(reservation, 'listing_id') else None

                # Safely get property name
                property_name = "Unknown Property"
                if listing:
                    try:
                        property_name = listing.get("property_name") or listing.get("address") or "Unknown Property"
                    except (AttributeError, TypeError):
                        property_name = "Unknown Property"

                # Safely get status
                status = getattr(reservation, 'status', 'pending')
                status_color = {
                    'pending': "#FF9800",
                    'confirmed': "#4CAF50",
                    'cancelled': "#F44336",
                    'completed': "#2196F3"
                }.get(status, "#999999")

                # Safely get dates
                check_in = getattr(reservation, 'check_in_date', 'N/A')
                check_out = getattr(reservation, 'check_out_date', 'N/A')

                card = ft.Container(
                    bgcolor="#FFFFFF",
                    padding=20,
                    border_radius=12,
                    border=ft.border.all(1, "#E0E0E0"),
                    content=ft.Column(
                        spacing=12,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(property_name, size=18, weight=ft.FontWeight.BOLD),
                                    ft.Container(expand=True),
                                    ft.Container(
                                        content=ft.Text(
                                            status.capitalize(),
                                            size=12,
                                            color="white",
                                            weight=ft.FontWeight.BOLD
                                        ),
                                        bgcolor=status_color,
                                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                        border_radius=20
                                    )
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            ft.Divider(height=1, color="#E0E0E0"),
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color="#666"),
                                    ft.Text(f"Check-in: {check_in}", size=14, color="#333")
                                ],
                                spacing=8
                            ),
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color="#666"),
                                    ft.Text(f"Check-out: {check_out}", size=14, color="#333")
                                ],
                                spacing=8
                            ),
                            ft.Row(
                                controls=[
                                    ft.OutlinedButton(
                                        "View Details",
                                        icon=ft.Icons.VISIBILITY,
                                        on_click=lambda e, r=reservation: self._view_details(r)
                                    ),
                                    ft.ElevatedButton(
                                        "Cancel" if status == 'pending' else "View",
                                        icon=ft.Icons.CANCEL if status == 'pending' else ft.Icons.INFO,
                                        style=ft.ButtonStyle(
                                            bgcolor="#F44336" if status == 'pending' else "#0078FF",
                                            color="white"
                                        ),
                                        on_click=lambda e, r=reservation: self._cancel_reservation(r) if status == 'pending' else self._view_details(r),
                                        disabled=status in ['cancelled', 'completed']
                                    )
                                ],
                                spacing=12
                            )
                        ]
                    )
                )
                reservation_cards.append(card)

        # Build the view
        return ft.View(
            "/tenant/reservations",
            controls=[
                ft.Container(
                    bgcolor="#F5F7FA",
                    expand=True,
                    padding=40,
                    content=ft.Column(
                        spacing=20,
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            # Header
                            ft.Row(
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.ARROW_BACK,
                                        on_click=lambda _: self.page.go("/tenant"),
                                        tooltip="Back to Dashboard"
                                    ),
                                    ft.Text("My Reservations", size=32, weight=ft.FontWeight.BOLD),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            # Reservations list
                            ft.Container(
                                content=ft.Column(
                                    spacing=16,
                                    controls=reservation_cards if reservation_cards else [
                                        ft.Container(
                                            padding=40,
                                            content=ft.Column(
                                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                controls=[
                                                    ft.Icon(ft.Icons.BOOKMARK_BORDER, size=64, color="#999"),
                                                    ft.Text("No reservations yet", size=20, weight=ft.FontWeight.BOLD, color="#666"),
                                                    ft.Text("Browse listings to make a reservation", size=14, color="#999"),
                                                    ft.ElevatedButton(
                                                        "Browse Listings",
                                                        icon=ft.Icons.SEARCH,
                                                        on_click=lambda _: self.page.go("/browse")
                                                    )
                                                ],
                                                spacing=16
                                            )
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                )
            ],
            padding=0,
            bgcolor="#F5F7FA"
        )

    def _view_details(self, reservation):
        """Show reservation details"""
        self.page.open(ft.SnackBar(
            content=ft.Text("Reservation details coming soon!"),
            bgcolor="#0078FF"


        ))
        self.page.update()

    def _cancel_reservation(self, reservation):
        """Cancel a reservation"""
        self.page.open(ft.SnackBar(
            content=ft.Text("Cancellation feature coming soon!"),
            bgcolor="#FF9800"


        ))
        self.page.update()
