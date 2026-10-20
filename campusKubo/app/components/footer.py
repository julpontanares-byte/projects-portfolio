import flet as ft


class Footer:
    """Footer component

    Backwards-compatible with older tests that instantiate `Footer(page)`
    and call `.build()`.
    """

    def __init__(self, page: ft.Page | None = None):
        self.page = page

    def view(self):
        return ft.Container(
            bgcolor="#1A1A1A",
            padding=40,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=40,
                        controls=[
                            ft.Column(
                                spacing=10,
                                controls=[
                                    ft.Text(
                                        "CampusKubo",
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        color="white"
                                    ),
                                    ft.Text(
                                        "Find your perfect student accommodation",
                                        size=12,
                                        color=ft.Colors.BLACK
                                    )
                                ]
                            ),
                            ft.Column(
                                spacing=10,
                                controls=[
                                    ft.Text(
                                        "Quick Links",
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color="white"
                                    ),
                                    ft.TextButton("Home", style=ft.ButtonStyle(color=ft.Colors.BLACK)),
                                    ft.TextButton("Browse Listings", style=ft.ButtonStyle(color=ft.Colors.BLACK)),
                                    ft.TextButton("About Us", style=ft.ButtonStyle(color=ft.Colors.BLACK)),
                                ]
                            ),
                            ft.Column(
                                spacing=10,
                                controls=[
                                    ft.Text(
                                        "Contact",
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color="white"
                                    ),
                                    ft.Text("Email: info@campuskubo.com", size=12, color=ft.Colors.BLACK),
                                    ft.Text("Phone: +63 123 456 7890", size=12, color=ft.Colors.BLACK),
                                ]
                            )
                        ]
                    ),
                    ft.Divider(color="#333"),
                    ft.Text(
                        "© 2024 CampusKubo. All rights reserved.",
                        size=12,
                        color=ft.Colors.BLACK,
                        text_align=ft.TextAlign.CENTER
                    )
                ]
            )
        )

    def build(self) -> ft.Control:
        """Compatibility wrapper for tests expecting `.build()`."""
        return self.view()
