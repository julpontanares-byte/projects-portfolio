"""
Home/Landing page view
"""
import flet as ft
from typing import Any
import random
from storage.db import get_properties
from components.signup_banner import SignupBanner
from components.listing_card import create_home_listing_card
from config.colors import COLORS

class HomeView:
    """Home page view"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.colors = COLORS

    def build(self) -> ft.View:
        """Build home view - matching model"""

        # Fetch properties for featured section
        try:
            all_properties = get_properties() or []
            random.shuffle(all_properties)
            featured_properties = all_properties[:5]  # Show up to 5 properties in grid
        except Exception:
            featured_properties = []

        # Featured Listings Cards
        def listing_card(property_data, show_details_button=True):
            listing_payload = dict(property_data)
            listing_payload.setdefault("property_name", property_data.get("name") or property_data.get("address"))
            listing_payload.setdefault("description", property_data.get("description", ""))
            listing_payload.setdefault("price", property_data.get("price", 0))

            image_url = property_data.get("image_url")
            property_id = property_data.get("id")
            availability = property_data.get("availability_status", "Available")
            is_available = str(availability).lower() == "available"

            def view_details(_):
                self.page.session.set("selected_property_id", property_id)
                self.page.session.set("property_source", "/")
                self.page.go("/property-details")

            return create_home_listing_card(
                listing=listing_payload,
                image_url=image_url,
                is_available=is_available,
                on_click=view_details if show_details_button else None,
                show_cta=show_details_button,
                page=self.page,
            )

        # Grid layout for featured properties - 5 cards in one row centered
        featured_grid = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            controls=[listing_card(prop) for prop in featured_properties] if featured_properties else [ft.Text("No properties available", size=16, color=self.colors["text_light"])]
        )

        from components.logo import Logo

        nav_bar = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                Logo(size=22, color=self.colors["primary"]),
                ft.Row([
                    ft.TextButton(
                        "Login",
                        on_click=lambda _: self.page.go("/login"),
                        style=ft.ButtonStyle(color=self.colors["text_dark"])
                    ),
                    ft.TextButton(
                        "Register",
                        on_click=lambda _: self.page.go("/signup"),
                        style=ft.ButtonStyle(color=self.colors["text_dark"])
                    )
                ])
            ]
        )

        # Hero section with text and images
        hero_section = ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=30,
                controls=[
                    ft.Text(
                        "Where Every Student Finds Comfort",
                        size=48,
                        weight=ft.FontWeight.BOLD,
                        color=self.colors["text_dark"],
                        text_align=ft.TextAlign.CENTER
                    ),
                    featured_grid,
                ]
            ),
            padding=ft.padding.only(top=40, bottom=40)
        )

        # About Section
        about_section = ft.Container(
            padding=30,
            bgcolor=self.colors["card_bg"],
            border_radius=12,
            border=ft.border.all(1, self.colors["border"]),
            shadow=ft.BoxShadow(blur_radius=10, spread_radius=2, color="#D4C4B080"),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
                controls=[
                    ft.Text(
                        "About CampusKubo",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=self.colors["primary"]
                    ),
                    ft.Container(
                        width=60,
                        height=3,
                        bgcolor=self.colors["accent"],
                        border_radius=2
                    ),
                    ft.Text(
                        "Your trusted platform for finding comfortable and affordable student accommodation near campus.",
                        size=16,
                        color=self.colors["text_dark"],
                        text_align=ft.TextAlign.CENTER,
                        max_lines=3
                    ),
                    ft.Container(height=10),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=40,
                        controls=[
                            ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=5,
                                controls=[
                                    ft.Icon(ft.Icons.HOME_WORK, size=40, color=self.colors["primary"]),
                                    ft.Text("Verified Listings", weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                    ft.Text("Quality-checked properties", size=12, color=self.colors["text_light"])
                                ]
                            ),
                            ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=5,
                                controls=[
                                    ft.Icon(ft.Icons.SHIELD, size=40, color=self.colors["secondary"]),
                                    ft.Text("Safe & Secure", weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                    ft.Text("Protected transactions", size=12, color=self.colors["text_light"])
                                ]
                            ),
                            ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=5,
                                controls=[
                                    ft.Icon(ft.Icons.SUPPORT_AGENT, size=40, color=self.colors["accent"]),
                                    ft.Text("24/7 Support", weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                    ft.Text("Always here to help", size=12, color=self.colors["text_light"])
                                ]
                            )
                        ]
                    )
                ]
            )
        )

        return ft.View(
            "/",
            padding=25,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            bgcolor=self.colors["background"],
            controls=[
                nav_bar,
                hero_section,
                ft.Container(height=30),
                ft.Container(
                    padding=20,
                    bgcolor=self.colors["card_bg"],
                    border_radius=8,
                    border=ft.border.all(1, self.colors["border"]),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                "🔍 Want to explore more listings?",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=self.colors["text_dark"]
                            ),
                            ft.Text(
                                "Browse all available properties without creating an account.",
                                size=14,
                                color=self.colors["text_light"]
                            ),
                            ft.ElevatedButton(
                                "Browse Listings as Guest",
                                icon=ft.Icons.SEARCH,
                                on_click=lambda _: self.page.go("/browse"),
                                bgcolor=self.colors["accent"],
                                color=self.colors["card_bg"]
                            )
                        ]
                    )
                ),
                ft.Container(height=30),
                about_section,
            ]
        )