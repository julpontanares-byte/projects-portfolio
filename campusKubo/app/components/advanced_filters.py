# app/components/advanced_filters.py
"""
Advanced filter component for property search (price, location, amenities).
Reusable across browse and home views.
"""
import flet as ft
from typing import Callable, Optional, Dict, Any


class AdvancedFilters:
    """Advanced filter panel with price range, location, and amenity selectors"""

    def __init__(self, page_or_on_apply: Callable[[Dict], None] | None = None, on_clear: Callable[[], None] | None = None):
        # Allow calling AdvancedFilters(page) in tests — provide no-op callbacks
        if callable(page_or_on_apply):
            self.on_apply = page_or_on_apply
            self.on_clear = on_clear or (lambda: None)
        else:
            self.on_apply = (lambda _: None)
            self.on_clear = (lambda: None)
        """
        Args:
            on_apply: Callback(filters_dict) when Apply is clicked
            on_clear: Callback() when Clear is clicked
        """
        # values already set above; keep backward-compatible defaults here
        pass

        # Filter input fields
        self.price_min = ft.TextField(
            label="Min Price (₱)",
            hint_text="e.g., 1000",
            width=100,
            text_size=12,
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=True
        )

        self.price_max = ft.TextField(
            label="Max Price (₱)",
            hint_text="e.g., 5000",
            width=100,
            text_size=12,
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=True
        )

        self.location_input = ft.TextField(
            label="Location",
            hint_text="e.g., Quezon City",
            width=210,
            text_size=12,
            dense=True
        )

        # Room Type dropdown
        self.room_type_dropdown = ft.Dropdown(
            label="Room Type",
            hint_text="Select room type",
            options=[
                ft.dropdown.Option("Single"),
                ft.dropdown.Option("Double"),
                ft.dropdown.Option("Shared"),
                ft.dropdown.Option("Studio"),
            ],
            width=210,
            text_size=12,
            dense=True
        )

        # Amenities dropdown (multi-select via multiple fields)
        self.amenities_dropdown = ft.Dropdown(
            label="Amenities",
            hint_text="Select amenity",
            options=[
                ft.dropdown.Option("WiFi"),
                ft.dropdown.Option("Air Conditioning"),
                ft.dropdown.Option("Kitchen"),
                ft.dropdown.Option("Laundry"),
                ft.dropdown.Option("Parking"),
                ft.dropdown.Option("Security"),
                ft.dropdown.Option("Gym"),
                ft.dropdown.Option("Swimming Pool"),
            ],
            width=210,
            text_size=12,
            dense=True
        )

        # Availability/Status dropdown
        self.availability_dropdown = ft.Dropdown(
            label="Availability",
            hint_text="Select status",
            options=[
                ft.dropdown.Option("All"),
                ft.dropdown.Option("Available"),
                ft.dropdown.Option("Reserved"),
                ft.dropdown.Option("Full"),
            ],
            value="All",
            width=210,
            text_size=12,
            dense=True
        )

    def build_sidebar(self) -> ft.Container:
        """Build filter sidebar container"""
        return ft.Container(
            width=230,
            padding=15,
            bgcolor="#ffffff",
            border_radius=10,
            content=ft.Column(
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Text("Filters", size=24, weight=ft.FontWeight.BOLD, color="black"),
                    ft.Divider(height=1, color="#ddd"),

                    # Price Range Section
                    ft.Container(
                        padding=5,
                        content=ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text("💰 Price Range", weight=ft.FontWeight.BOLD, size=13, color="#0078FF"),
                                ft.Row([self.price_min, self.price_max], spacing=8),
                            ]
                        )
                    ),
                    ft.Divider(height=1, color="#e0e0e0"),

                    # Location Section
                    ft.Container(
                        padding=5,
                        content=ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text("📍 Location", weight=ft.FontWeight.BOLD, size=13, color="#ff9800"),
                                self.location_input,
                            ]
                        )
                    ),
                    ft.Divider(height=1, color="#e0e0e0"),

                    # Room Type Section
                    ft.Container(
                        padding=5,
                        content=ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text("🛏 Room Type", weight=ft.FontWeight.BOLD, size=13, color="#4CAF50"),
                                self.room_type_dropdown,
                            ]
                        )
                    ),
                    ft.Divider(height=1, color="#e0e0e0"),

                    # Amenities Section
                    ft.Container(
                        padding=5,
                        content=ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text("🏠 Amenities", weight=ft.FontWeight.BOLD, size=13, color="#E91E63"),
                                self.amenities_dropdown,
                            ]
                        )
                    ),
                    ft.Divider(height=1, color="#e0e0e0"),

                    # Availability Section
                    ft.Container(
                        padding=5,
                        content=ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text("📅 Availability", weight=ft.FontWeight.BOLD, size=13, color="#673AB7"),
                                self.availability_dropdown,
                            ]
                        )
                    ),

                    ft.Container(height=10),

                    # Apply and Clear buttons
                    ft.ElevatedButton(
                        "Apply Filters",
                        width=200,
                        height=45,
                        bgcolor="#0078ff",
                        color="white",
                        on_click=lambda _: self._apply_filters()
                    ),
                    ft.OutlinedButton(
                        "Clear Filters",
                        width=200,
                        height=45,
                        on_click=lambda _: self._clear_filters()
                    )
                ]
            )
        )

    def _apply_filters(self):
        """Collect filter values and call callback"""
        filters = {
            "price_min": float(self.price_min.value) if self.price_min.value else None,
            "price_max": float(self.price_max.value) if self.price_max.value else None,
            "location": self.location_input.value if self.location_input.value else None,
            "room_type": self.room_type_dropdown.value if self.room_type_dropdown.value else None,
            "amenities": self.amenities_dropdown.value if self.amenities_dropdown.value else None,
            "availability": self.availability_dropdown.value if self.availability_dropdown.value and self.availability_dropdown.value != "All" else None,
        }
        self.on_apply(filters)

    def _clear_filters(self):
        """Reset all filters and call callback"""
        self.price_min.value = ""
        self.price_max.value = ""
        self.location_input.value = ""
        self.room_type_dropdown.value = None
        self.amenities_dropdown.value = None
        self.availability_dropdown.value = "All"
        self.price_min.update()
        self.price_max.update()
        self.location_input.update()
        self.room_type_dropdown.update()
        self.amenities_dropdown.update()
        self.availability_dropdown.update()
        self.on_clear()

    def get_filters(self) -> Dict[str, Any]:
        """Get current filter values as dict"""
        return {
            "price_min": float(self.price_min.value) if self.price_min.value else None,
            "price_max": float(self.price_max.value) if self.price_max.value else None,
            "location": self.location_input.value if self.location_input.value else None,
            "room_type": self.room_type_dropdown.value if self.room_type_dropdown.value else None,
            "amenities": self.amenities_dropdown.value if self.amenities_dropdown.value else None,
            "availability": self.availability_dropdown.value if self.availability_dropdown.value and self.availability_dropdown.value != "All" else None,
        }

    def build(self) -> ft.Container:
        """Compatibility: return the sidebar container via `.build()`"""
        return self.build_sidebar()
