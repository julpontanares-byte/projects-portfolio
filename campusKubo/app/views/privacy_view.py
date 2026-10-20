"""
Privacy Policy view
"""
import flet as ft
from config.colors import COLORS


class PrivacyView:
    """Privacy Policy page"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.colors = COLORS

    def build(self):
        return ft.View(
            "/privacy",
            bgcolor=self.colors["card_bg"],  # Semi-transparent overlay
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
                                        ft.Icon(
                                            ft.Icons.PRIVACY_TIP_OUTLINED,
                                            color=self.colors["primary"],
                                            size=32
                                        ),
                                        ft.Column(
                                            spacing=2,
                                            controls=[
                                                ft.Text(
                                                    "Privacy Policy",
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
                                            "Full Privacy Policy",
                                            size=20,
                                            weight=ft.FontWeight.BOLD,
                                            color=self.colors["text_dark"]
                                        ),
                                        
                                        ft.Text("1. Information We Collect", size=16, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                        ft.Text(
                                            "We collect information you provide when creating an account, including your name, email address, and role (Tenant or Property Manager). Property Managers may also provide property details and contact information.",
                                            size=14,
                                            color=self.colors["text_dark"]
                                        ),

                                        ft.Text("2. How We Use Your Information", size=16, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                        ft.Text(
                                            "We use your information to provide and improve CampusKubo services, facilitate bookings between tenants and property managers, send important notifications, and ensure platform security.",
                                            size=14,
                                            color=self.colors["text_dark"]
                                        ),

                                        ft.Text("3. Information Sharing", size=16, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                        ft.Text(
                                            "We do not share your personal information with third parties except as described in this policy or with your consent. We may share information with service providers who perform services on our behalf.",
                                            size=14,
                                            color=self.colors["text_dark"]
                                        ),

                                        ft.Text("4. Data Security", size=16, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                        ft.Text(
                                            "We take reasonable measures to help protect your personal information from loss, theft, misuse, unauthorized access, disclosure, alteration, and destruction using industry-standard security practices.",
                                            size=14,
                                            color=self.colors["text_dark"]
                                        ),

                                        ft.Text("5. Your Rights", size=16, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                        ft.Text(
                                            "You have the right to access, update, or delete your personal information at any time through your account settings. You can also request a copy of your data or object to certain data processing activities.",
                                            size=14,
                                            color=self.colors["text_dark"]
                                        ),

                                        ft.Text("6. Cookies and Tracking", size=16, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                        ft.Text(
                                            "CampusKubo uses cookies and similar technologies to enhance user experience, analyze usage patterns, and maintain session information. You can control cookie preferences through your browser settings.",
                                            size=14,
                                            color=self.colors["text_dark"]
                                        ),

                                        ft.Text("7. Data Retention", size=16, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                        ft.Text(
                                            "We retain your information for as long as your account is active or as needed to provide services. If you delete your account, we will remove your personal data within 30 days, except as required by law.",
                                            size=14,
                                            color=self.colors["text_dark"]
                                        ),

                                        ft.Text("8. Contact Us", size=16, weight=ft.FontWeight.BOLD, color=self.colors["text_dark"]),
                                        ft.Text(
                                            "If you have questions or concerns about this privacy policy or our data practices, please contact us at privacy@campuskubo.com",
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