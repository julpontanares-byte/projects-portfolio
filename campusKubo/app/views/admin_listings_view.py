# app/views/admin_listings_view.py

import flet as ft
from services.listing_service import ListingService
from services.admin_service import AdminService
from components.navbar import DashboardNavBar
from components.listing_card import create_admin_listing_card
from state.session_state import SessionState
from collections import defaultdict
from services.refresh_service import register as _register_refresh


class AdminListingsView:

    def __init__(self, page: ft.Page):
        self.page = page
        self.session = SessionState(page)
        self.listing_service = ListingService()
        self.admin_service = AdminService()

        # UI State
        self.search_field = ft.TextField(
            hint_text="Search by address or description",
            expand=True,
            on_change=self.on_filters_changed
        )

        # Tab state
        self.current_tab = "active"  # active, pending, rejected, archived

        # Filter state
        self.price_min = ft.TextField(
            label="Min Price",
            value="",
            width=120,
            on_change=self.on_filters_changed
        )
        self.price_max = ft.TextField(
            label="Max Price",
            value="",
            width=120,
            on_change=self.on_filters_changed
        )

        self.location_filter = ft.TextField(
            label="Location",
            value="",
            width=150,
            on_change=self.on_filters_changed
        )

        self.pm_filter = ft.Dropdown(
            label="PM Owner",
            options=[ft.dropdown.Option("All")],
            value="All",
            on_change=self.on_filters_changed,
            width=180
        )

        self.listings_column = ft.Column(expand=True)
        self.tab_content = ft.Column(expand=True)

        # Create/edit listing form fields
        self.listing_form_pm = ft.Dropdown(label="PM Owner", width=280)
        self.listing_form_address = ft.TextField(label="Address", width=360)
        self.listing_form_price = ft.TextField(label="Price (PHP)", width=180)
        self.listing_form_description = ft.TextField(label="Description", width=360, min_lines=3, max_lines=5)
        self.listing_form_lodging = ft.TextField(label="Lodging Details", width=360, min_lines=2, max_lines=4)
        self.listing_form_status = ft.Dropdown(
            label="Status",
            options=[
                ft.dropdown.Option("Pending", "pending"),
                ft.dropdown.Option("Approved", "approved"),
                ft.dropdown.Option("Active", "active"),
                ft.dropdown.Option("Rejected", "rejected"),
                ft.dropdown.Option("Archived", "archived")
            ],
            value="pending",
            width=220
        )
        self._editing_listing = None
        # Inline form container visibility/state
        self.inline_form_container = ft.Container(visible=False)
        self.inline_form_visible = False

        try:
            _register_refresh(self._on_global_refresh)
        except Exception:
            pass

    def _on_global_refresh(self):
        try:
            self.refresh_listings()
        except Exception:
            pass


    # ----------------------------------------------------
    # Build view
    # ----------------------------------------------------
    def build(self):
        if not self.session.require_auth():
            return None
        if not self.session.is_admin():
            self.page.go("/")
            return None

        self._populate_pm_filter()
        self.refresh_listings()

        # Build inline form content
        form_action_label = "Update Listing" if self._editing_listing else "Create Listing"
        self.inline_form_container.visible = self.inline_form_visible
        self.inline_form_container.content = ft.Container(
            bgcolor=ft.Colors.GREY_50,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=10,
            padding=15,
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Row([
                        ft.Text(form_action_label, size=16, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.OutlinedButton("Cancel", on_click=lambda e: self._hide_listing_form()),
                        ft.ElevatedButton("Save", icon=ft.Icons.SAVE, on_click=lambda e: self._submit_listing_form()),
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.ResponsiveRow(
                        spacing=12,
                        run_spacing=12,
                        controls=[
                            ft.Container(content=self.listing_form_address, col={"xs":12, "md":6}),
                            ft.Container(content=self.listing_form_price, col={"xs":12, "md":3}),
                            ft.Container(content=self.listing_form_status, col={"xs":12, "md":3}),
                            ft.Container(content=self.listing_form_pm, col={"xs":12, "md":6}),
                            ft.Container(content=self.listing_form_description, col={"xs":12, "md":12}),
                            ft.Container(content=self.listing_form_lodging, col={"xs":12, "md":12}),
                        ],
                    ),
                ],
            )
        )

        return ft.View(
            "/admin_listings",
            scroll=ft.ScrollMode.AUTO,
            controls=[
                DashboardNavBar(self.page, "Listing Management",
                                self.session.get_email() or "").view(),

                ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Row(controls=[
                            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.page.go('/admin')),
                            ft.Text("Listing Management", size=26, weight=ft.FontWeight.BOLD)
                        ], alignment=ft.MainAxisAlignment.START),

                        # Tabs for status filtering (render labels only).
                        # We avoid embedding the same `tab_content` control into
                        # multiple Tab.content instances because reusing a control
                        # in multiple parents can lead to layout/display issues.
                        ft.Row(
                            spacing=12,
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(
                                    expand=True,
                                    content=ft.Tabs(
                                        selected_index=self._get_tab_index(),
                                        on_change=self._on_tab_change,
                                        tabs=[
                                            ft.Tab(text="Active"),
                                            ft.Tab(text="Pending Approval"),
                                            ft.Tab(text="Rejected"),
                                            ft.Tab(text="Archived"),
                                        ]
                                    )
                                ),
                                ft.ElevatedButton(
                                    "Add Listing",
                                    icon=ft.Icons.ADD,
                                    on_click=lambda e: self._show_listing_form()
                                )
                            ]
                        ),

                        # Inline create/edit form
                        self.inline_form_container,

                        ft.Divider(),

                        # Search bar
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.SEARCH),
                                self.search_field
                            ],
                            alignment=ft.MainAxisAlignment.START
                        ),

                        # Filters row
                        ft.Row(
                            controls=[
                                self.price_min,
                                self.price_max,
                                self.location_filter,
                                self.pm_filter
                            ],
                            wrap=True,
                            spacing=10
                        ),

                        ft.Divider(),

                        # Main tab content area (populated by `refresh_listings`).
                        # Use a fixed-height container like other admin views for
                        # visual consistency and to avoid header/content overlap.
                        ft.Container(height=520, content=self.tab_content),

                        # Analytics section (optional)
                        ft.ExpansionTile(
                            title=ft.Text("Analytics", weight=ft.FontWeight.BOLD),
                            controls=[
                                ft.Container(
                                    height=300,
                                    content=ft.Column([
                                        ft.Text("Listings per Location", size=14, weight=ft.FontWeight.BOLD),
                                        self._build_location_chart()
                                    ], expand=True)
                                )
                            ]
                        ),

                        ft.Divider(),
                    ], expand=True)
                )
            ]
        )

    def _switch_tab(self, tab_name: str):
        """Switch to a different tab and refresh listings."""
        self.current_tab = tab_name
        self.refresh_listings()

    def _get_tab_index(self):
        """Get the current tab index for ft.Tabs."""
        tab_map = {"active": 0, "pending": 1, "rejected": 2, "archived": 3}
        return tab_map.get(self.current_tab, 0)

    def _on_tab_change(self, e):
        """Handle tab change event."""
        tab_names = ["active", "pending", "rejected", "archived"]
        if e.control.selected_index < len(tab_names):
            self._switch_tab(tab_names[e.control.selected_index])

    def _populate_pm_filter(self):
        """Populate PM filter dropdown with all PM owners."""
        all_listings = self.listing_service.get_all_listings()
        pm_set = set()
        for listing in all_listings:
            if hasattr(listing, 'pm_id') and listing.pm_id:
                pm_set.add(str(listing.pm_id))

        options = [ft.dropdown.Option("All")]
        for pm_id in sorted(pm_set):
            options.append(ft.dropdown.Option(f"PM {pm_id}"))

        self.pm_filter.options = options
        self.pm_filter.value = "All"

    def _build_location_chart(self):
        """Build a pie chart showing listings per location."""
        all_listings = self.listing_service.get_all_listings()
        location_count = defaultdict(int)

        for listing in all_listings:
            addr = getattr(listing, 'address', 'Unknown')
            # Group by city/area (first part of address)
            area = addr.split(',')[0] if ',' in addr else addr
            location_count[area] += 1

        if not location_count:
            return ft.Text("No data available", size=12, color=ft.Colors.GREY)

        # Create pie chart data
        total_listings = sum(location_count.values())
        colors = [ft.Colors.BLUE, ft.Colors.GREEN, ft.Colors.ORANGE, ft.Colors.RED,
                 ft.Colors.PURPLE, ft.Colors.YELLOW, ft.Colors.PINK, ft.Colors.CYAN]

        # Sort by count descending and take top 8
        sorted_locations = sorted(location_count.items(), key=lambda x: x[1], reverse=True)[:8]

        pie_sections = []
        legend_items = []

        for i, (location, count) in enumerate(sorted_locations):
            # Calculate percentage
            percentage = (count / total_listings) * 100

            # Create pie section (using containers to simulate pie slices)
            color = colors[i % len(colors)]

            # Simple pie slice representation using containers
            pie_sections.append(
                ft.Container(
                    width=percentage * 3,  # Scale width by percentage
                    height=30,
                    bgcolor=color,
                    border_radius=ft.border_radius.only(
                        top_left=15 if i == 0 else 0,
                        bottom_left=15 if i == 0 else 0,
                        top_right=15 if i == len(sorted_locations)-1 else 0,
                        bottom_right=15 if i == len(sorted_locations)-1 else 0
                    ),
                    content=ft.Text(f"{percentage:.1f}%", size=10, color=ft.Colors.WHITE,
                                  text_align=ft.TextAlign.CENTER)
                )
            )

            # Legend item
            legend_items.append(
                ft.Row([
                    ft.Container(width=15, height=15, bgcolor=color, border_radius=2),
                    ft.Text(f"{location}: {count} ({percentage:.1f}%)", size=11)
                ], spacing=8)
            )

        return ft.Column([
            ft.Text("Listings by Location", size=14, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            # Pie chart representation
            ft.Container(
                content=ft.Row(pie_sections, spacing=0),
                height=120,
                alignment=ft.alignment.center
            ),
            ft.Container(height=12),
            # Legend
            ft.Column(legend_items, spacing=5)
        ], spacing=5)

    # ----------------------------------------------------
    # Refresh data
    # ----------------------------------------------------
    def refresh_listings(self):
        """Loads all listings, applies filters based on current tab, and rebuilds grid."""
        all_listings = self.listing_service.get_all_listings()

        # Filter by tab (status)
        # Note: seeded demo data uses status 'approved' for active listings,
        # so include 'approved' alongside 'active' to show seeded rows.
        status_map = {
            "active": ["active", "approved", "available"],
            "pending": ["pending"],
            "rejected": ["rejected"],
            "archived": ["archived"]
        }
        target_statuses = status_map.get(self.current_tab, [])
        filtered = [l for l in all_listings if getattr(l, 'status', '').lower() in [s.lower() for s in target_statuses]]

        # Apply search
        query = self.search_field.value or ""
        if query:
            filtered = self.listing_service.search_listings(query, filtered)

        # Apply price filter
        try:
            min_price = float(self.price_min.value) if self.price_min.value else None
            max_price = float(self.price_max.value) if self.price_max.value else None
            if min_price is not None:
                filtered = [l for l in filtered if float(getattr(l, 'price', 0)) >= min_price]
            if max_price is not None:
                filtered = [l for l in filtered if float(getattr(l, 'price', 0)) <= max_price]
        except (ValueError, TypeError):
            pass

        # Apply location filter
        location = self.location_filter.value or ""
        if location:
            filtered = [l for l in filtered if location.lower() in getattr(l, 'address', '').lower()]

        # Apply PM filter
        pm = self.pm_filter.value or ""
        if pm and pm != "All":
            pm_id = pm.replace("PM ", "")
            try:
                pm_id_num = int(pm_id)
                filtered = [l for l in filtered if getattr(l, 'pm_id', None) == pm_id_num]
            except (ValueError, TypeError):
                pass

        # Build grid layout
        cards = [self.build_listing_card(listing) for listing in filtered]

        if not cards:
            self.tab_content.controls = [
                ft.Container(
                    alignment=ft.alignment.center,
                    padding=40,
                    content=ft.Text("No listings found", size=14, color=ft.Colors.GREY)
                )
            ]
        else:
            # Create a grid layout using Row wrapping
            grid_rows = []
            for i in range(0, len(cards), 2):
                grid_rows.append(
                    ft.Row([cards[i], cards[i+1]] if i+1 < len(cards) else [cards[i]], spacing=15)
                )

            self.tab_content.controls = [ft.Column(grid_rows, spacing=15, expand=True)]

        self.page.update()

    # ----------------------------------------------------
    # Triggered when search or filter changes
    # ----------------------------------------------------
    def on_filters_changed(self, _):
        self.refresh_listings()

    # ----------------------------------------------------
    # Build each listing card (for grid)
    # ----------------------------------------------------
    def build_listing_card(self, listing):
        """Creates a compact card for each listing in grid view."""
        images = getattr(listing, "images", [])
        pm_email = getattr(listing, "pm_email", "N/A")
        status = getattr(listing, "status", "Unknown")
        status_lower = str(status).lower()
        listing_id = getattr(listing, "id", None)

        def _confirm_listing_action(action: str, lid: int):
            title = "Confirm"
            msg = f"Are you sure you want to {action} this listing?"
            dlg = ft.AlertDialog(
                title=ft.Text(title),
                content=ft.Text(msg),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: self._close_dialog()),
                    ft.ElevatedButton(action.capitalize(), on_click=lambda e, a=action, id=lid: self._perform_listing_action(a, id))
                ]
            )
            setattr(self.page, "dialog", dlg)
            dlg.open = True
            self.page.update()

        def preview_handler(_):
            if listing_id:
                try:
                    self.page.session.set("selected_property_id", listing_id)
                except Exception:
                    pass
            self.page.go("/property-details")

        edit_handler = None
        if status_lower in ["active", "approved", "pending"]:
            edit_handler = lambda e, l=listing: self._show_listing_form(l)

        approve_handler = None
        reject_handler = None
        if status_lower == "pending" and listing_id is not None:
            approve_handler = lambda e, lid=listing_id: _confirm_listing_action('approve', lid)
            reject_handler = lambda e, lid=listing_id: _confirm_listing_action('reject', lid)

        delete_handler = None
        if status_lower not in ["pending"] and listing_id is not None:
            delete_handler = lambda e, lid=listing_id: self._confirm_delete_listing(lid)

        is_available = status_lower in ("active", "approved", "available")

        return create_admin_listing_card(
            listing=listing,
            images=images,
            status=status,
            pm_contact=pm_email,
            is_available=is_available,
            on_preview=preview_handler,
            on_edit=edit_handler,
            on_approve=approve_handler,
            on_reject=reject_handler,
            on_delete=delete_handler,
        )

    # ----------------------------------------------------
    # Create/Edit listing inline form methods
    # ----------------------------------------------------
    def _reset_listing_form(self):
        self._editing_listing = None
        self.listing_form_address.value = ''
        self.listing_form_price.value = ''
        self.listing_form_description.value = ''
        self.listing_form_lodging.value = ''
        self.listing_form_status.value = 'pending'
        self.listing_form_pm.value = None

    def _populate_pm_dropdown(self):
        try:
            pms = self.admin_service.get_all_users_by_role('pm')
            pm_options = [ft.dropdown.Option(f"{pm.full_name} ({pm.email})", str(pm.id)) for pm in pms]
            self.listing_form_pm.options = pm_options
        except Exception:
            self.listing_form_pm.options = []

    def _show_listing_form(self, listing=None):
        """Show inline create/edit form with populated fields."""
        self._populate_pm_dropdown()

        if listing:
            self._editing_listing = listing
            self.listing_form_address.value = getattr(listing, 'address', '') or ''
            try:
                price = float(getattr(listing, 'price', 0) or 0)
                self.listing_form_price.value = str(int(price)) if price == int(price) else str(price)
            except (ValueError, TypeError):
                self.listing_form_price.value = str(getattr(listing, 'price', '') or '')
            self.listing_form_description.value = getattr(listing, 'description', '') or ''
            self.listing_form_lodging.value = getattr(listing, 'lodging_details', '') or ''
            self.listing_form_status.value = getattr(listing, 'status', 'pending') or 'pending'
            pm_id = getattr(listing, 'pm_id', None)
            self.listing_form_pm.value = str(pm_id) if pm_id else None
        else:
            self._reset_listing_form()

        self.inline_form_visible = True
        self.inline_form_container.visible = True
        try:
            self.page.update()
        except Exception:
            pass

    def _hide_listing_form(self, *_):
        self.inline_form_visible = False
        self.inline_form_container.visible = False
        self._reset_listing_form()
        try:
            self.page.update()
        except Exception:
            pass

    def _submit_listing_form(self):
        """Validate and submit the listing form."""
        # Validate required fields
        address = (self.listing_form_address.value or "").strip()
        price_str = (self.listing_form_price.value or "").strip()
        pm_id_str = self.listing_form_pm.value
        status = self.listing_form_status.value or 'pending'
        description = (self.listing_form_description.value or "").strip()
        lodging = (self.listing_form_lodging.value or "").strip()

        # Validate address
        if not address:
            self.page.open(ft.SnackBar(ft.Text("Address is required")))
            return

        # Validate price
        try:
            price = float(price_str)
            if price < 0:
                raise ValueError("Price cannot be negative")
        except (ValueError, TypeError):
            self.page.open(ft.SnackBar(ft.Text("Enter a valid price")))
            return

        # Validate PM owner
        if not pm_id_str:
            self.page.open(ft.SnackBar(ft.Text("Please select a PM owner")))
            return

        try:
            pm_id = int(pm_id_str)
        except (ValueError, TypeError):
            self.page.open(ft.SnackBar(ft.Text("Invalid PM owner")))
            return

        # Call service
        if self._editing_listing:
            # Update existing listing
            success, message = self.admin_service.update_listing_admin(
                listing_id=self._editing_listing.id,
                address=address,
                price=price,
                description=description,
                lodging_details=lodging,
                status=status,
                pm_id=pm_id
            )
        else:
            # Create new listing
            success, message, listing_id = self.admin_service.create_listing_admin(
                address=address,
                price=price,
                description=description,
                lodging_details=lodging,
                status=status,
                pm_id=pm_id
            )

        # Show feedback
        self.page.open(ft.SnackBar(ft.Text(message)))

        # Close form and refresh if successful
        if success:
            # Notify global refresh service
            try:
                from services.refresh_service import notify as _notify
                _notify()
            except Exception:
                pass

            self._hide_listing_form()
            self.refresh_listings()
    # Deletion handler
    # ----------------------------------------------------
    def _confirm_delete_listing(self, listing_id):
        """Show confirmation dialog before deleting a listing."""
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Text(
                    "Are you sure you want to permanently delete this listing? This action cannot be undone.",
                    size=14
                ),
                width=400
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton(
                    "Delete",
                    bgcolor=ft.Colors.RED,
                    color=ft.Colors.WHITE,
                    on_click=lambda e, lid=listing_id: self._perform_delete_listing(lid)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        setattr(self.page, "dialog", dlg)
        dlg.open = True
        self.page.update()

    def _perform_delete_listing(self, listing_id):
        """Perform the actual deletion after confirmation."""
        self._close_dialog()

        # Use admin-level deletion
        ok, msg = self.listing_service.delete_listing_by_admin(listing_id)
        snack_bar = ft.SnackBar(ft.Text(msg))
        self.page.open(snack_bar)

        # Notify global refresh service
        try:
            from services.refresh_service import notify as _notify
            _notify()
        except Exception:
            pass

        self.refresh_listings()
    def _close_dialog(self):
        dlg = getattr(self.page, "dialog", None)
        if dlg:
            dlg.open = False
            self.page.update()
            # clear the dialog attribute to keep the page object consistent
            setattr(self.page, "dialog", None)
            self.page.update()

    def _perform_listing_action(self, action: str, listing_id: int):
        self._close_dialog()
        if action == 'approve':
            ok = self.admin_service.approve_listing(listing_id)
            msg = 'Listing approved' if ok else 'Failed to approve listing'
        else:
            ok = self.admin_service.reject_listing(listing_id)
            msg = 'Listing rejected' if ok else 'Failed to reject listing'

        self.page.open(ft.SnackBar(ft.Text(msg)))

        # Notify global refresh service
        try:
            from services.refresh_service import notify as _notify
            _notify()
        except Exception:
            pass

        self.refresh_listings()
