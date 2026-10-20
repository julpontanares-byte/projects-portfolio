# app/views/listing_detail_extended_view.py
"""
Extended listing detail view with property images, amenities, description,
and guest/tenant action prompts.
Complements existing listing_detail_view.py with enhanced UX.
"""
import flet as ft
from services.listing_service import ListingService
from state.session_state import SessionState
from utils.navigation import go_back


class ListingDetailExtendedView:
    """Enhanced listing detail page with better guest experience"""

    def __init__(self, page: ft.Page, listing_id: int):
        self.page = page
        self.listing_id = listing_id
        self.listing_service = ListingService()
        self.session = SessionState(page)

    def build(self) -> ft.View:
        """Build extended listing detail view"""

        # Fetch listing
        listing = self.listing_service.get_listing_by_id(self.listing_id)
        if not listing:
            # Fallback to simple error message
            return ft.View(
                "/",
                controls=[
                    ft.Container(
                        padding=50,
                        alignment=ft.alignment.center,
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=15,
                            controls=[
                                ft.Icon(ft.Icons.ERROR, size=80, color="#f44336"),
                                ft.Text("Property not found", size=20, color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD),
                                ft.ElevatedButton(
                                    "Back to Browse",
                                    on_click=lambda _: self.page.go("/browse")
                                )
                            ]
                        )
                    )
                ]
            )

        # Extract listing info
        address = listing.address if hasattr(listing, 'address') else "N/A"
        price = listing.price if hasattr(listing, 'price') else 0
        description = listing.description if hasattr(listing, 'description') else ""
        lodging_details = listing.lodging_details if hasattr(listing, 'lodging_details') else ""

        # Format amenities from lodging_details
        amenities_list = [a.strip() for a in lodging_details.split(",") if a.strip()] if lodging_details else []

        # Check if user is logged in
        user_email = self.session.get_email()
        is_logged_in = user_email is not None

        # Action button logic
        def on_action_click(e):
            print(f"[DEBUG] on_action_click - is_logged_in={is_logged_in}")
            if not is_logged_in:
                show_auth_dialog()
            else:
                # Check user role
                user_role = self.session.get_role()
                print(f"[DEBUG] on_action_click - user_role={user_role}")
                if user_role == "tenant":
                    # Redirect tenant to dashboard for reservation
                    self.page.go("/reservations")
                    snack = ft.SnackBar(content=ft.Text("Redirecting to dashboard for reservation..."))
                    self.page.overlay.append(snack)
                    snack.open = True
                    self.page.update()
                else:
                    # For other roles, show coming soon message
                    snack = ft.SnackBar(content=ft.Text("Reservation feature coming soon!"))
                    self.page.overlay.append(snack)
                    snack.open = True
                    self.page.update()

        def show_auth_dialog():
            """Show dialog prompting sign-up/login"""
            dlg = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.LOCK_PERSON, color="#f57c00", size=30),
                    ft.Text("Account Required", weight=ft.FontWeight.BOLD)
                ], spacing=10),
                content=ft.Container(
                    width=300,
                    content=ft.Column(
                        tight=True,
                        spacing=10,
                        controls=[
                            ft.Text(
                                "To reserve this property, you need to create an account or sign in.",
                                size=14
                            ),
                            ft.Divider(height=1),
                            ft.Text("✨ Benefits of signing up:", size=13, weight=ft.FontWeight.BOLD),
                            ft.Text("• Reserve properties instantly", size=12),
                            ft.Text("• Contact property owners", size=12),
                            ft.Text("• Save favorite listings", size=12),
                        ]
                    )
                ),
                actions=[
                    ft.ElevatedButton(
                        "Create Account",
                        icon=ft.Icons.PERSON_ADD,
                        bgcolor="#4caf50",
                        color="white",
                        on_click=lambda _: self._close_and_navigate("/signup", dlg)
                    ),
                    ft.OutlinedButton(
                        "Sign In",
                        icon=ft.Icons.LOGIN,
                        on_click=lambda _: self._close_and_navigate("/login", dlg)
                    ),
                    ft.TextButton("Maybe Later", on_click=lambda _: self._close_dialog(dlg)),
                ],
                actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
            self.page.open(dlg)

        # Action button
        action_button = ft.ElevatedButton(
            "Reserve Now" if listing.status == 'approved' else "Contact Owner",
            width=300,
            height=50,
            on_click=on_action_click,
            bgcolor="#0078ff",
            color="white"
        )

        # Navbar
        from components.logo import Logo

        nav_bar = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row([
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: go_back(self.page)),
                    Logo(size=22),
                ]),
                ft.Row([
                    ft.TextButton("Login", on_click=lambda _: self.page.go("/login")) if not is_logged_in else ft.Container(),
                    ft.TextButton("Register", on_click=lambda _: self.page.go("/signup")) if not is_logged_in else ft.Container(),
                    ft.IconButton(icon=ft.Icons.NOTIFICATIONS, tooltip="Notifications")
                ])
            ]
        )

        return ft.View(
            f"/listing/{self.listing_id}",
            padding=25,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                nav_bar,
                ft.Container(height=20),

                # Header section
                ft.Container(
                    bgcolor="#f5f5f5",
                    padding=10,
                    border_radius=6,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                expand=True,
                                spacing=10,
                                controls=[
                                    ft.Text(listing.address, size=32, weight=ft.FontWeight.BOLD),
                                    ft.Row([
                                        ft.Icon(ft.Icons.LOCATION_ON, size=20, color="#0078ff"),
                                        ft.Text(address, size=16, color="black")
                                    ], spacing=5),
                                ]
                            ),
                            ft.Container(
                                bgcolor="#f0f7ff",
                                padding=15,
                                border_radius=8,
                                content=ft.Column(
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=10,
                                    controls=[
                                        ft.Text("Monthly Rent", size=14, color="black"),
                                        ft.Text(f"₱{price:,.0f}", size=24, weight=ft.FontWeight.BOLD, color="#0078ff")
                                    ]
                                )
                            )
                        ]
                    )
                ),
                ft.Container(height=20),

                # Image gallery placeholder
                ft.Container(
                    bgcolor="#ffffff",
                    padding=20,
                    border_radius=10,
                    content=ft.Column(
                        spacing=15,
                        controls=[
                            ft.Text("Photos", size=20, weight=ft.FontWeight.BOLD, color="black"),
                            ft.Container(
                                width=None,
                                height=400,
                                bgcolor="#dfdfdf",
                                border_radius=10,
                                content=ft.Column(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Icon(ft.Icons.IMAGE, size=80, color="#999"),
                                        ft.Text("Property images will be displayed here", color="black")
                                    ]
                                )
                            ),
                        ]
                    )
                ),
                ft.Container(height=20),

                # Description Section
                ft.Container(
                    bgcolor="#ffffff",
                    padding=20,
                    border_radius=10,
                    content=ft.Column(
                        spacing=15,
                        controls=[
                            ft.Text("Description", size=20, weight=ft.FontWeight.BOLD, color="black"),
                            ft.Text(
                                description,
                                size=15,
                                color="#444",
                                text_align=ft.TextAlign.JUSTIFY
                            ),
                        ]
                    )
                ),
                ft.Container(height=20),

                # Amenities Section
                ft.Container(
                    bgcolor="#ffffff",
                    padding=20,
                    border_radius=10,
                    content=ft.Column(
                        spacing=15,
                        controls=[
                            ft.Text("Amenities & Features", size=20, weight=ft.FontWeight.BOLD, color="#333"),
                            ft.Column(
                                spacing=10,
                                controls=[
                                    ft.Row([
                                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=20, color="#4caf50"),
                                        ft.Text(amenity, size=15, color="#444")
                                    ], spacing=10) for amenity in amenities_list
                                ] if amenities_list else [
                                    ft.Text("No amenities listed", size=14, color="#999", italic=True)
                                ]
                            )
                        ]
                    )
                ),
                ft.Container(height=30),

                # Action Button
                ft.Container(
                    bgcolor="#ffffff",
                    padding=20,
                    border_radius=10,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=10,
                                controls=[
                                    action_button,
                                    ft.Text(
                                        "Sign in to make a reservation" if not is_logged_in else "",
                                        size=12,
                                        color="black",
                                        italic=True
                                    )
                                ]
                            )
                        ]
                    )
                ),
                ft.Container(height=20),
            ]
        )

    def _close_and_navigate(self, route: str, dlg: ft.AlertDialog):
        """Close dialog and navigate"""
        self.page.close(dlg)
        self.page.go(route)

    def _close_dialog(self, dlg: ft.AlertDialog):
        """Close dialog"""
        self.page.close(dlg)
