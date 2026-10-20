"""
Terms and Conditions view
"""
import flet as ft
from config.colors import COLORS
from utils.navigation import go_back


class TermsView:
    """Terms and Conditions page"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.colors = COLORS

    def build(self):
        return ft.View(
            "/terms",
            bgcolor=self.colors["card_bg"],
            controls=[
                ft.Container(
                    width=750,
                    height=600,
                    bgcolor=self.colors["card_bg"],
                    border_radius=16,
                    padding=0,
                    shadow=ft.BoxShadow(
                        blur_radius=20,
                        spread_radius=5,
                        color=ft.Colors.with_opacity(0.3, "#00000000")
                    ),
                    content=ft.Column(
                        spacing=0,
                        controls=[
                            # Header
                            ft.Container(
                                padding=20,
                                content=ft.Row(
                                    controls=[
                                        ft.IconButton(
                                            icon=ft.Icons.ARROW_BACK,
                                            tooltip="Back",
                                            on_click=lambda _: go_back(self.page, "/")
                                        ),
                                        ft.Icon(
                                            ft.Icons.DESCRIPTION_OUTLINED,
                                            color=self.colors["primary"],
                                            size=32
                                        ),
                                        ft.Column(
                                            spacing=2,
                                            controls=[
                                                ft.Text(
                                                    "Terms & Conditions",
                                                    size=24,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=self.colors["text_dark"]
                                                ),
                                                ft.Text(
                                                    "Last updated: December 10, 2025",
                                                    size=13,
                                                    color=self.colors["text_light"],
                                                ),
                                            ]
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.START,
                                    spacing=12,
                                ),
                            ),

                            ft.Divider(height=1, color=self.colors["border"]),

                            # Scrollable content
                            ft.Container(
                                expand=True,
                                padding=ft.padding.only(left=20, right=20, top=20, bottom=10),
                                content=ft.Column(
                                    scroll=ft.ScrollMode.AUTO,
                                    spacing=20,
                                    controls=[
                                        ft.Text(
                                            "Full Legal Text",
                                            size=20,
                                            weight=ft.FontWeight.BOLD,
                                            color=self.colors["text_dark"]
                                        ),

                                        ft.Text("1. Introduction", size=16, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                        ft.Text(
                                            "By accessing and using CampusKubo, you accept and agree to be bound by the terms and provision of this agreement. Do not continue to use CampusKubo if you do not agree to take all of the terms and conditions stated on this page.",
                                            size=14,
                                            color=self.colors["text_dark"]
                                        ),

                                        ft.Text("2. Account Responsibilities", size=16, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                        ft.Text(
                                            "You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account. You must notify us immediately of any unauthorized use of your account.",
                                            size=14,
                                            color=self.colors["text_dark"]
                                        ),

                                        ft.Text("3. Property Listings", size=16, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                        ft.Text(
                                            "Other than the content you own, under these Terms, CampusKubo and/or its licensors own all the intellectual property rights and materials contained in this application. You are granted limited license only for purposes of viewing the material contained on this application.",
                                            size=14,
                                            color=self.colors["text_dark"]
                                        ),

                                        ft.Text("4. Booking and Payments", size=16, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                        ft.Text(
                                            "All bookings are subject to availability and acceptance by the Property Manager. Payment terms and cancellation policies vary by property and should be reviewed before booking.",
                                            size=14,
                                            color=self.colors["text_dark"]
                                        ),

                                        ft.Text("5. User Conduct", size=16, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                        ft.Text(
                                            "Users agree not to use CampusKubo for any unlawful purpose or in any way that could damage, disable, or impair the service. Harassment, fraud, or misuse of the platform may result in account termination.",
                                            size=14,
                                            color=self.colors["text_dark"]
                                        ),

                                        ft.Text("6. Disclaimer", size=16, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                        ft.Text(
                                            "CampusKubo is provided 'as is' without warranties of any kind. We do not guarantee the availability, accuracy, or reliability of the service and are not liable for any damages arising from its use.",
                                            size=14,
                                            color=self.colors["text_dark"]
                                        ),

                                        ft.Text("7. Modifications", size=16, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                        ft.Text(
                                            "We reserve the right to modify these terms at any time. Continued use of CampusKubo after changes indicates acceptance of the modified terms.",
                                            size=14,
                                            color=self.colors["text_dark"]
                                        ),

                                        ft.Container(height=10),  # Bottom padding
                                    ],
                                ),
                            ),

                            ft.Divider(height=1, color=self.colors["border"]),

                            # Footer buttons
                            ft.Container(
                                padding=20,
                                content=ft.Row(
                                    controls=[
                                        ft.Container(expand=True),
                                        ft.ElevatedButton(
                                            "I Understand",
                                            on_click=lambda _: self.page.go("/signup"),
                                            style=ft.ButtonStyle(
                                                bgcolor=self.colors["background"],
                                                color=self.colors["text_light"],
                                                padding=15,
                                            ),
                                        ),
                                    ],
                                    spacing=10,
                                ),
                            ),
                        ],
                    ),
                ),
            ],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
