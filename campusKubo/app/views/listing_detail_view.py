"""
Listing detail view
"""
import flet as ft
import os
from typing import cast
from utils.navigation import go_home
from services.listing_service import ListingService
from components.reservation_form import ReservationForm
from services.reservation_service import ReservationService
from state.session_state import SessionState


class ListingDetailView:
    """Listing detail page view"""

    def __init__(self, page: ft.Page, listing_id: int):
        self.page = page
        self.listing_id = listing_id
        self.listing_service = ListingService()
        self.reservation_service = ReservationService()
        self.session = SessionState(page)

    def handle_reservation(self, listing_id: int, start_date: str, end_date: str, msg_field: ft.Text):
        """Handle reservation submission"""
        if not self.session.is_logged_in():
            self.page.go("/login")
            return

        if not self.session.is_tenant():
            msg_field.value = "Only tenants can make reservations"
            msg_field.color = "red"
            msg_field.update()
            return

        user_id = self.session.get_user_id()
        if user_id is None:
            msg_field.value = "User ID not found"
            msg_field.color = "red"
            msg_field.update()
            return
        success, message = self.reservation_service.create_new_reservation(
            listing_id, user_id, start_date, end_date
        )

        if success:
            self.page.open(
                ft.SnackBar(
                    content=ft.Text("Reservation created successfully!", color="white"),
                    bgcolor="#4CAF50"
                )
            )
        else:
            msg_field.value = message
            msg_field.color = "red"
            msg_field.update()

    def build(self):
        """Build listing detail view"""
        # Get listing data
        listing = self.listing_service.get_listing_by_id(self.listing_id)

        if not listing:
            return ft.View(
                f"/listing/{self.listing_id}",
                controls=[
                    ft.Container(
                        padding=40,
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.Icons.ERROR, size=64, color="#F44336"),
                                ft.Text("Listing not found", size=24, color=ft.Colors.BLACK),
                                ft.ElevatedButton(
                                    "Back to Home",
                                    on_click=lambda _: go_home(self.page)
                                )
                            ]
                        )
                    )
                ]
            )

        is_available = self.listing_service.check_availability(listing.id)

        # Image gallery
        image_gallery = ft.Row(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(
                    width=600,
                    height=400,
                    bgcolor="#E8E8E8",
                    border_radius=12,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    content=ft.Image(
                        src=listing.images[0],
                        width=600,
                        height=400,
                        fit=ft.ImageFit.COVER
                    ) if listing.images and os.path.exists(listing.images[0]) else ft.Container(
                        content=ft.Icon(ft.Icons.HOME, size=100, color=ft.Colors.BLACK),
                        alignment=ft.alignment.center
                    )
                )
            ] + [
                ft.Container(
                    width=150,
                    height=150,
                    bgcolor="#E8E8E8",
                    border_radius=8,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    content=ft.Image(
                        src=img,
                        width=150,
                        height=150,
                        fit=ft.ImageFit.COVER
                    )
                ) for img in listing.images[1:] if os.path.exists(img)
            ]
        )

        # Availability badge
        availability_badge = ft.Container(
            content=ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE if is_available else ft.Icons.CANCEL,
                        size=16,
                        color="white"
                    ),
                    ft.Text(
                        "Available" if is_available else "Occupied",
                        size=14,
                        color="white",
                        weight=ft.FontWeight.BOLD
                    )
                ]
            ),
            bgcolor="#4CAF50" if is_available else "#F44336",
            padding=ft.padding.symmetric(horizontal=15, vertical=8),
            border_radius=20,
        )

        # Listing details
        # Safely format price since listing.price may be a string
        try:
            price_val = float(listing.price)
            price_text = f"\u20b1{price_val:,.0f}"
        except (TypeError, ValueError, AttributeError):
            try:
                price_val = float(str(listing.price).replace(',', '').strip())
                price_text = f"\u20b1{price_val:,.0f}"
            except Exception as e:
                print(f"[handle_reserve] Failed to create reservation: {e}")
                price_text = f"\u20b1{listing.price}"

        details_section = ft.Container(
            bgcolor="#FFFFFF",
            padding=30,
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color="#00000015",
            ),
            content=ft.Column(
                spacing=20,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                listing.address,
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color="#1A1A1A"
                            ),
                            availability_badge
                        ]
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(
                                price_text,
                                size=32,
                                color="#0078FF",
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text("/month", size=18, color=ft.Colors.BLACK)
                        ],
                        spacing=5
                    ),
                    ft.Divider(),
                    ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text("Description", size=20, weight=ft.FontWeight.BOLD),
                            ft.Text(listing.description, size=14, color=ft.Colors.BLACK)
                        ]
                    ),
                    ft.Divider(),
                    ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text("Lodging Details", size=20, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                listing.lodging_details or "No additional details provided",
                                size=14,
                                color=ft.Colors.BLACK
                            )
                        ]
                    )
                ]
            )
        )

        # Reservation form (only for tenants)
        reservation_section = ft.Container()
        if self.session.is_tenant() and is_available:
            reservation_section = ReservationForm(
                page=self.page,
                listing_id=listing.id,
                on_submit=self.handle_reservation
            )

        elif not self.session.is_logged_in() and is_available:
            reservation_section = ft.Container(
                padding=20,
                bgcolor="#FFFFFF",
                border_radius=12,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=10,
                    color="#00000015",
                ),
                content=ft.Column(
                    spacing=15,
                    controls=[
                        ft.Text(
                            "Reserve This Property",
                            size=20,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(
                            "Please login to make a reservation",
                            size=14,
                            color=ft.Colors.BLACK
                        ),
                        ft.ElevatedButton(
                            "Login",
                            icon=ft.Icons.LOGIN,
                            style=ft.ButtonStyle(
                                color="white",
                                bgcolor="#0078FF",
                            ),
                            on_click=lambda _: self.page.go("/login")
                        )
                    ]
                )
            )

        return ft.View(
            f"/listing/{self.listing_id}",
            padding=0,
            scroll=ft.ScrollMode.AUTO,
            bgcolor="#F5F7FA",
            controls=[
                ft.Container(
                    bgcolor="#FFFFFF",
                    padding=ft.padding.symmetric(horizontal=40, vertical=20),
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=10,
                        color="#00000008",
                        offset=ft.Offset(0, 2)
                    ),
                    content=ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                icon_color=ft.Colors.BLACK,
                                tooltip="Back",
                                on_click=lambda _: self.page.go("/")
                            ),
                            ft.Text(
                                "Listing Details",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color="#1A1A1A"
                            )
                        ]
                    )
                ),
                ft.Container(
                    padding=40,
                    content=ft.Row(
                        spacing=30,
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Column(
                                spacing=20,
                                controls=[
                                    image_gallery,
                                    details_section
                                ],
                                width=650
                            ),
                            ft.Column(
                                spacing=20,
                                controls=[cast(ft.Control, reservation_section)],
                                width=350
                            )
                        ]
                    )
                )
            ]
        )