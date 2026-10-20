"""Property Manager dashboard view - integrated design"""
import flet as ft
from services.listing_service import ListingService
from services.refresh_service import register as register_refresh
from components.listing_card import create_pm_listing_card
from state.session_state import SessionState
from components.navbar import DashboardNavBar


_active_pm_dashboard = None


class PMDashboardView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.listing_service = ListingService()
        self.session = SessionState(page)
        self._listings_container: ft.Column | None = None
        self._user_id: int | None = None

    def build(self):
        global _active_pm_dashboard
        page = self.page
        user_id = self.session.get_user_id()
        if not user_id:
            page.go("/login")
            return None

        role_value = (self.session.get_role() or "pm").lower()
        if role_value not in ("pm", "property_manager") and self.session.get_role():
            page.go("/login")
            return None

        _active_pm_dashboard = self
        self._user_id = user_id
        self._listings_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)

        pm_full_name = self.session.get_full_name() or self.session.get_email() or "User"

        self._load_listings()

        # Use the dashboard navbar to keep header consistent across dashboards
        navbar = DashboardNavBar(
            page=page,
            title="Property Manager Dashboard",
            user_email=self.session.get_email() or pm_full_name,
            show_add_button=True,
            on_add_click=lambda e: page.go("/pm/add"),
            on_logout=lambda e: page.go("/logout"),
        ).view()

        listings_section = ft.Container(
            padding=40,
            content=ft.Column(
                spacing=20,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.HOME, size=24, color="#0078FF"),
                            ft.Text(
                                "My Listings",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color="#1A1A1A",
                            ),
                        ],
                        spacing=10,
                    ),
                    self._listings_container,
                ],
            ),
        )

        main_column = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            controls=[navbar, listings_section],
        )

        return ft.View(
            "/pm",
            padding=0,
            bgcolor="#F5F7FA",
            controls=[main_column],
        )

    def refresh_listings(self):
        if not self._listings_container:
            return
        self._load_listings()
        try:
            self.page.update()
        except Exception:
            pass

    def _load_listings(self):
        if not self._listings_container or not self._user_id:
            return
        container = self._listings_container
        container.controls.clear()

        listings = self.listing_service.get_all_listings(owner_id=self._user_id)
        if not listings:
            container.controls.append(self._build_empty_state())
            return

        for listing in listings:
            is_available = self.listing_service.check_availability(listing.id)
            container.controls.append(
                self._create_listing_card(
                    listing=listing,
                    images=getattr(listing, "images", []) or [],
                    is_available=is_available,
                )
            )

    def _build_empty_state(self) -> ft.Container:
        return ft.Container(
            padding=40,
            width=800,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
                controls=[
                    ft.Icon(ft.Icons.ADD_HOME, size=64, color=ft.Colors.BLACK),
                    ft.Text("No listings yet", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                    ft.Text(
                        "Use the \"Add New Listing\" button above to create your first property.",
                        size=14,
                        color=ft.Colors.BLACK,
                    ),
                ],
            ),
        )

    def _create_listing_card(self, listing, images, is_available):
        listing_id = getattr(listing, "id", None) or getattr(listing, "listing_id", None)
        listing_name = getattr(listing, "property_name", None) or getattr(listing, "address", "Listing")

        def delete_handler(e):
            self._show_delete_confirmation(listing_id, listing_name)

        def edit_handler(e):
            if listing_id:
                self.page.go(f"/pm/edit/{listing_id}")

        def preview_handler(e):
            try:
                self.page.session.set("selected_property_id", listing_id)
            except Exception:
                pass
            self.page.go("/property-details")

        return create_pm_listing_card(
            listing=listing,
            images=images if images else None,
            is_available=is_available,
            owner_id=self._user_id,
            on_preview=preview_handler,
            on_edit=edit_handler,
            on_delete=delete_handler,
        )

    def _show_delete_confirmation(self, listing_id, listing_name):
        if not listing_id:
            return

        page = self.page

        def on_confirm(e):
            dlg.open = False
            page.update()
            self._perform_delete(listing_id, listing_name)

        def on_cancel(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING, color="#F44336", size=28),
                    ft.Text("Confirm Deletion", size=20, weight=ft.FontWeight.BOLD, color="#1A1A1A"),
                ],
                spacing=10,
            ),
            content=ft.Column(
                spacing=15,
                tight=True,
                controls=[
                    ft.Text(
                        f'Are you sure you want to delete "{listing_name}"?',
                        size=14,
                        color="#333333",
                    ),
                    ft.Text(
                        "This action cannot be undone. All associated data, including images, will be permanently deleted.",
                        size=12,
                        color=ft.Colors.BLACK,
                    ),
                ],
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=on_cancel,
                    style=ft.ButtonStyle(color=ft.Colors.BLACK),
                ),
                ft.ElevatedButton(
                    "Delete",
                    on_click=on_confirm,
                    style=ft.ButtonStyle(color="white", bgcolor="#F44336"),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = dlg
        dlg.open = True
        page.update()

    def _perform_delete(self, listing_id, listing_name):
        if not listing_id or not self._user_id:
            self._show_feedback("Error: Invalid listing or user", success=False)
            return

        try:
            success, message = self.listing_service.delete_listing_by_id(listing_id, self._user_id)
            if success:
                self._show_feedback(f"Listing \"{listing_name}\" deleted successfully", success=True)
                self.refresh_listings()
            else:
                self._show_feedback(message or "Failed to delete listing", success=False)
        except Exception as ex:
            self._show_feedback(f"Error deleting listing: {str(ex)}", success=False)

    def _show_feedback(self, message, success=True):
        page = self.page
        color = "#4CAF50" if success else "#F44336"
        icon = ft.Icons.CHECK_CIRCLE if success else ft.Icons.ERROR
        snack = ft.SnackBar(
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(icon, color="white"),
                    ft.Text(message, color="white"),
                ],
            ),
            bgcolor=color,
            action="OK",
            action_color="white",
        )
        page.open(snack)
        page.update()


def _handle_pm_dashboard_refresh():
    dashboard = _active_pm_dashboard
    if dashboard:
        dashboard.refresh_listings()


try:
    register_refresh(_handle_pm_dashboard_refresh)
except Exception:
    pass
