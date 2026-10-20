# app/views/browse_view.py
"""
Browse/Search view - displays all approved listings with filtering.
Accessible to guests, tenants, and PMs. No login required.
"""
import flet as ft
from typing import Any
from storage.db import get_properties
from components.signup_banner import SignupBanner
from config.colors import COLORS


class BrowseView:
    """Browse all available listings with filters"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.colors = COLORS

    def property_card(self, property_data):
        """Return a property card control for a property dict."""
        name = property_data.get("name", "Property")
        price = property_data.get("price", 0)
        price = f"₱{price:,.0f}/mo"
        location = property_data.get("location", "N/A")
        availability = property_data.get("availability_status", "Available")
        property_id = property_data.get("id")
        image_url = property_data.get("image_url")

        def view_details(e):
            self.page.session.set("selected_property_id", property_id)
            self.page.session.set("property_source", "/browse")
            self.page.go("/property-details")

        # Choose color based on availability
        avail_bg = self.colors["available"] if availability == "Available" else self.colors["unavailable"]
        avail_text = self.colors["card_bg"]

        return ft.Container(
            bgcolor=self.colors["card_bg"],
            width=260,
            padding=15,
            margin=10,
            border_radius=8,
            border=ft.border.all(1, self.colors["border"]),
            shadow=ft.BoxShadow(
                blur_radius=15,
                spread_radius=1,
                color=ft.Colors.with_opacity(0.15, self.colors["text_light"])
            ),
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Container(
                        width=230,
                        height=150,
                        bgcolor=self.colors["border"],
                        border_radius=8,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        content=ft.Image(
                            src=image_url,
                            width=230,
                            height=150,
                            fit=ft.ImageFit.COVER,
                        ) if image_url else ft.Icon(ft.Icons.HOME, size=60, color=self.colors["text_light"])
                    ),
                    ft.Container(
                        padding=5,
                        content=ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text(name, weight=ft.FontWeight.BOLD, size=16, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, color=self.colors["text_dark"]),
                                ft.Row([
                                    ft.Icon(ft.Icons.LOCATION_ON, size=16, color=self.colors["secondary"]),
                                    ft.Text(location, size=14, color=self.colors["text_light"], max_lines=1)
                                ], spacing=4),
                                ft.Text(price, size=18, color=self.colors["primary"], weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    padding=ft.padding.symmetric(vertical=2, horizontal=6),
                                    bgcolor=avail_bg,
                                    border_radius=6,
                                    content=ft.Text(
                                        availability,
                                        size=12,
                                        color=avail_text,
                                        weight=ft.FontWeight.BOLD,
                                    )
                                ),
                                ft.Container(
                                    padding=ft.padding.symmetric(vertical=4, horizontal=8),
                                    bgcolor=self.colors["background"],
                                    border_radius=4,
                                    content=ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=5,
                                        controls=[
                                            ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=self.colors["primary"]),
                                            ft.Text("Sign in to reserve", size=11, color=self.colors["text_dark"], italic=True)
                                        ]
                                    )
                                )
                            ]
                        )
                    )
                ]
            ),
            on_click=view_details,
            ink=True,
            tooltip="Click to view details"
        )

    def build(self) -> ft.View:
        """Build browse view - matching model"""
        self.page.title = "CampusKubo Browse Listings"
        filters: dict[str, Any] = self.page.session.get("filters") or {}
        search_query = self.page.session.get("search_query") or ""

        # Get properties from database
        properties = get_properties(search_query, filters)


        def go_back(e):
            """Navigate to previous view or home if no history"""
            history = getattr(self.page, "_nav_history", [])
            if history:
                prev_route = history.pop()
                setattr(self.page, "_nav_history", history)
                setattr(self.page, "_nav_back_navigation", True)
                self.page.go(prev_route)
            else:
                # Fallback to home if no history
                self.page.go("/")

        back_button = ft.Container(
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color=self.colors["primary"],
                        icon_size=24,
                        tooltip="Back to home",
                        on_click=go_back
                    ),
                    ft.Text("Back to Home", size=14, color=self.colors["text_dark"])
                ]
            )
        )

        search_input = ft.TextField(
            hint_text="Search by keyword or location (press Enter to search)...",
            width=650,
            value=search_query,
            prefix_icon=ft.Icons.SEARCH,
            on_submit=lambda e: self._perform_search(e.control.value),
            on_change=lambda e: self._perform_search(e.control.value),
            bgcolor=self.colors["card_bg"],
            border_color=self.colors["border"],
            focused_border_color=self.colors["primary"],
            color=self.colors["text_dark"]
        )

        # Filter controls - Load saved values from session
        saved_price_max = filters.get("price_max", 50000)
        saved_room_types = filters.get("room_type")
        saved_amenities = filters.get("amenities")
        saved_availability = filters.get("availability", "All")
        saved_location = filters.get("location", "")

        price_label = ft.Text(
            f"₱1,000 to ₱{int(saved_price_max):,}",
            size=12,
            weight=ft.FontWeight.BOLD,
            color=self.colors["primary"]
        )

        price_slider = ft.Slider(
            min=1000,
            max=50000,
            value=saved_price_max,
            divisions=49,
            label="{value}",
            active_color=self.colors["primary"],
            inactive_color=self.colors["border"],
        )

        def update_price_label(e):
            max_val = int(price_slider.value)
            price_label.value = f"₱1,000 Up to ₱{max_val:,}"
            price_label.update()

        price_slider.on_change = update_price_label

        # Room Type Checkboxes
        room_types = ["Single", "Double", "Shared", "Studio"]
        saved_room_types = filters.get("room_type", [])

        room_type_checkboxes = [
            ft.Checkbox(
                label=rt,
                value=rt in saved_room_types
            )
            for rt in room_types
        ]

        # Amenities Checkboxes
        amenities = ["WiFi", "Air Conditioning", "Kitchen"]
        saved_amenities = filters.get("amenities", [])

        amenities_checkboxes = [
            ft.Checkbox(
                label=a,
                value=a in saved_amenities
            )
            for a in amenities
        ]


        availability_dropdown = ft.Dropdown(
            hint_text="Select status",
            width=210,
            text_size=12,
            dense=True,
            bgcolor=self.colors["background"],
            border_color=self.colors["border"],
            color=self.colors["text_dark"],
            options=[
                ft.dropdown.Option("All"),
                ft.dropdown.Option("Available"),
                ft.dropdown.Option("Reserved"),
                ft.dropdown.Option("Full"),
            ],
            value=saved_availability
        )

        location_input = ft.TextField(
            label="Location",
            hint_text="e.g., Near Campus",
            width=210,
            text_size=12,
            dense=True,
            value=saved_location,
            bgcolor=self.colors["background"],
            border_color=self.colors["border"],
            color=self.colors["text_dark"]
        )

        def apply_filters(e):
            new_filters = {
                "price_min": 1000.0,
                "price_max": float(price_slider.value),
                "room_type": [cb.label for cb in room_type_checkboxes if cb.value] or None,
                "amenities": [cb.label for cb in amenities_checkboxes if cb.value] or None,
                "availability": availability_dropdown.value if availability_dropdown.value and availability_dropdown.value != "All" else None,
                "location": location_input.value if location_input.value else None
            }
            new_filters = {k: v for k, v in new_filters.items() if v is not None and v!= [] and v != ""}

            self.page.session.set("filters", new_filters)
            self.page.views.clear()
            self.page.views.append(self.build())
            self.page.update()


        def clear_filters(e):
            # Clear session
            self.page.session.set("filters", {})
            self.page.session.set("search_query", "")

            # Reset ALL UI controls
            search_input.value = ""
            price_slider.value = 50000
            price_label.value = "₱1,000 to ₱50,000"
            price_label.update()

            for cb in room_type_checkboxes:
                cb.value = False
            for cb in amenities_checkboxes:
                cb.value = False

            availability_dropdown.value = "All"
            location_input.value = ""

            # Update everything
            self.page.views.clear()
            self.page.views.append(self.build())
            self.page.update()

        sidebar = ft.Container(
            width=230,
            padding=15,
            bgcolor=self.colors["card_bg"],
            border_radius=10,
            border=ft.border.all(1, self.colors["border"]),
            content=ft.Column(
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Text("Filters", size=24, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                    ft.Divider(height=1, color=self.colors["border"]),

                    # Price Range Section
                    ft.Container(
                        padding=5,
                        content=ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text("💰 Price Range", weight=ft.FontWeight.BOLD, size=13, color=self.colors["secondary"]),
                                price_label,
                                price_slider,
                            ]
                        )
                    ),
                    ft.Divider(height=1, color=self.colors["border"]),

                    # Room Type Section
                    ft.Container(
                        padding=5,
                        content=ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text("🛏 Room Type", weight=ft.FontWeight.BOLD, size=13, color=self.colors["secondary"]),
                                *room_type_checkboxes
                            ]
                        )
                    ),

                    # Amenities Section
                    ft.Container(
                        padding=5,
                        content=ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text("🏠 Amenities", weight=ft.FontWeight.BOLD, size=13, color=self.colors["secondary"]),
                                *amenities_checkboxes
                            ]
                        )
                    ),

                    ft.Divider(height=1, color=self.colors["border"]),

                    # Availability Section
                    ft.Container(
                        padding=5,
                        content=ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text("📅 Availability", weight=ft.FontWeight.BOLD, size=13, color=self.colors["secondary"]),
                                availability_dropdown,
                            ]
                        )
                    ),
                    ft.Divider(height=1, color=self.colors["border"]),

                    # Location Section
                    ft.Container(
                        padding=5,
                        content=ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text("📍 Location", weight=ft.FontWeight.BOLD, size=13, color=self.colors["secondary"]),
                                location_input,
                            ]
                        )
                    ),

                    ft.Container(height=10),

                    ft.ElevatedButton(
                        "Apply Filters",
                        width=200,
                        height=45,
                        bgcolor=self.colors["primary"],
                        color=self.colors["card_bg"],
                        on_click=apply_filters
                    ),
                    ft.OutlinedButton(
                        "Clear Filters",
                        width=200,
                        height=45,
                        on_click=clear_filters,
                        style=ft.ButtonStyle(
                            color=self.colors["text_dark"],
                            side=ft.BorderSide(color=self.colors["border"], width=1)
                        )
                    )
                ]
            )
        )

        # Property listing card moved to class method `property_card`

        active_filter_chips = []

        # Price filter chip
        if filters.get("price_max") and filters["price_max"] < 50000:
            active_filter_chips.append(
                ft.Chip(
                    label=ft.Text(f"Max: ₱{int(filters['price_max']):,}", color=self.colors["text_dark"]),
                    bgcolor=self.colors["background"],
                    delete_icon_color=self.colors["primary"],
                    on_delete=lambda e: clear_filters(e)  # optionally clear all price filter
                )
            )

        # Room type chips (multi-select)
        if filters.get("room_type"):
            for rt in filters["room_type"]:
                def remove_rt(e, rt=rt):
                    new_filters = filters.copy()
                    new_filters["room_type"] = [r for r in filters["room_type"] if r != rt]
                    if not new_filters["room_type"]:
                        new_filters.pop("room_type")
                    self.page.session.set("filters", new_filters)
                    self.page.views.clear()
                    self.page.views.append(self.build())
                    self.page.update()

                active_filter_chips.append(
                    ft.Chip(
                        label=ft.Text(f"Type: {rt}", color=self.colors["text_dark"]),
                        bgcolor=self.colors["background"],
                        delete_icon_color=self.colors["primary"],
                        on_delete=remove_rt
                    )
                )

        # Amenities chips (multi-select)
        if filters.get("amenities"):
            for amen in filters["amenities"]:
                def remove_amen(e, amen=amen):
                    new_filters = filters.copy()
                    new_filters["amenities"] = [a for a in filters["amenities"] if a != amen]
                    if not new_filters["amenities"]:
                        new_filters.pop("amenities")
                    self.page.session.set("filters", new_filters)
                    self.page.views.clear()
                    self.page.views.append(self.build())
                    self.page.update()
                active_filter_chips.append(
                    ft.Chip(
                        label=ft.Text(f"Amenity: {amen}", color=self.colors["text_dark"]),
                        bgcolor=self.colors["background"],
                        delete_icon_color=self.colors["primary"],
                        on_delete=remove_amen
                    )
                )

        # Availability chip
        if filters.get("availability"):
            def remove_avail(e):
                new_filters = filters.copy()
                new_filters.pop("availability", None)
                self.page.session.set("filters", new_filters)
                self.page.views.clear()
                self.page.views.append(self.build())
                self.page.update()

            active_filter_chips.append(
                ft.Chip(
                    label=ft.Text(f"Status: {filters['availability']}", color=self.colors["text_dark"]),
                    bgcolor=self.colors["background"],
                    delete_icon_color=self.colors["primary"],
                    on_delete=remove_avail
                )
            )

        # Location chip
        if filters.get("location"):
            def remove_location(e):
                new_filters = filters.copy()
                new_filters.pop("location", None)
                self.page.session.set("filters", new_filters)
                self.page.views.clear()
                self.page.views.append(self.build())
                self.page.update()
            active_filter_chips.append(
                ft.Chip(
                    label=ft.Text(f"Location: {filters['location']}", color=self.colors["text_dark"]),
                    bgcolor=self.colors["background"],
                    delete_icon_color=self.colors["primary"],
                    on_delete=remove_location
                )
            )

        # --- Then use it in property_grid ---
        # Prepare a mutable results_row control so we can update search results in-place
        if properties:
            results_row = ft.Row(
                wrap=True,
                spacing=15,
                run_spacing=15,
                alignment=ft.MainAxisAlignment.START,
                controls=[self.property_card(prop) for prop in properties]
            )
        else:
            results_row = ft.Container(
                padding=50,
                alignment=ft.alignment.center,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                    controls=[
                        ft.Icon(ft.Icons.SEARCH_OFF, size=80, color=self.colors["border"]),
                        ft.Text("No properties found", size=20, color=self.colors["text_dark"], weight=ft.FontWeight.BOLD),
                        ft.Text("Try adjusting your search or filters", size=14, color=self.colors["text_light"]),
                        ft.ElevatedButton(
                            "Clear Filters",
                            on_click=clear_filters,
                            bgcolor=self.colors["primary"],
                            color=self.colors["card_bg"]
                        )
                    ]
                )
            )

        # Keep reference for live updates
        try:
            setattr(self.page, '_browse_results_row', results_row)
        except Exception:
            pass

        property_grid = ft.Container(
            expand=True,
            padding=15,
            bgcolor=self.colors["card_bg"],
            border_radius=10,
            border=ft.border.all(1, self.colors["border"]),
            content=ft.Column(
                spacing=15,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Text(
                        f"Search Results for '{search_query}'" if search_query else "All Available Properties",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color=self.colors["text_dark"]
                    ),
                    ft.Text(
                        f"Showing {len(properties)} properties",
                        size=14,
                        color=self.colors["text_light"]
                    ),

                    # Active filters display container
                    ft.Container(
                        content=ft.Row(
                            wrap=True,
                            spacing=8,
                            controls=active_filter_chips
                        ),
                        visible=len(active_filter_chips) > 0
                    ),
                    ft.Divider(height=1, color=self.colors["border"]),

                    # Properties grid (mutable results_row inserted below)
                    results_row,
                ]
            )
        )


        # Show signup banner only for visitors (not logged in)
        is_logged_in = self.page.session.get("is_logged_in")
        is_visitor = not is_logged_in if is_logged_in is not None else True
        signup_banner = None
        if is_visitor:
            signup_banner = SignupBanner(
                page=self.page,
                on_create_click=lambda: self.page.go("/signup"),
                on_signin_click=lambda: self.page.go("/login")
            ).build()

        main_layout = ft.Row(
            spacing=20,
            vertical_alignment=ft.CrossAxisAlignment.START,
            expand=True,
            controls=[
                sidebar,
                property_grid
            ]
        )

        return ft.View(
            "/browse",
            padding=25,
            scroll=ft.ScrollMode.AUTO,
            bgcolor=self.colors["background"],
            controls=[
                back_button,
                ft.Container(height=10),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Browse Listings", size=28, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"])
                    ]
                ),
                ft.Container(height=10),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[search_input]
                ),
                ft.Container(height=20),
                main_layout,
            ] + ([signup_banner] if signup_banner else [])
        )

    def _perform_search(self, query):
        q = query.strip()
        self.page.session.set("search_query", q)

        # Attempt in-place update of results if available to preserve focus
        filters = getattr(self.page, '_browse_filters', self.page.session.get('filters') or {})
        properties = get_properties(q, filters)

        results_row = getattr(self.page, '_browse_results_row', None)
        if results_row is None:
            # Fallback: rebuild entire view
            self.page.views.clear()
            self.page.views.append(self.build())
            self.page.update()
            return

        # Update results in-place
        if properties:
            new_cards = [self.property_card(prop) for prop in properties]
            if isinstance(results_row, ft.Row):
                results_row.controls[:] = new_cards
            elif isinstance(results_row, ft.Container):
                results_row.content = ft.Row(
                    wrap=True,
                    spacing=15,
                    run_spacing=15,
                    alignment=ft.MainAxisAlignment.START,
                    controls=new_cards
                )
                setattr(self.page, '_browse_results_row', results_row.content)
            else:
                # Unexpected type - rebuild
                self.page.views.clear()
                self.page.views.append(self.build())
                self.page.update()
                return
        else:
            # No results - show informative container
            nores = ft.Container(
                padding=50,
                alignment=ft.alignment.center,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                    controls=[
                        ft.Icon(ft.Icons.SEARCH_OFF, size=80, color=self.colors["border"]),
                        ft.Text("No properties found", size=20, color=self.colors["text_dark"], weight=ft.FontWeight.BOLD),
                        ft.Text("Try adjusting your search or filters", size=14, color=self.colors["text_light"]),
                        ft.ElevatedButton(
                            "Clear Filters",
                            on_click=lambda e: (self.page.session.set('filters', {}), self.page.views.clear(), self.page.views.append(self.build()), self.page.update()),
                            bgcolor=self.colors["primary"],
                            color=self.colors["card_bg"]
                        )
                    ]
                )
            )

            if isinstance(results_row, ft.Row):
                results_row.controls[:] = [nores]
            elif isinstance(results_row, ft.Container):
                results_row.content = nores
            else:
                self.page.views.clear()
                self.page.views.append(self.build())
                self.page.update()
                return

        self.page.update()