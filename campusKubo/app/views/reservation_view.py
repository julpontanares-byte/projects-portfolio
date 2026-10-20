"""
Reservation management view (placeholder)
"""
import flet as ft


class ReservationView:
    """Reservation view placeholder"""

    def __init__(self, page: ft.Page):
        self.page = page

    def build(self):
        """Build reservation view"""
        return ft.View(
            "/reservations",
            padding=40,
            controls=[
                ft.Container(
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20,
                        controls=[
                            ft.Icon(ft.Icons.CALENDAR_TODAY, size=80, color="#0078FF"),
                            ft.Text(
                                "Reservation Management",
                                size=32,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                "Coming soon...",
                                size=16,
                                color=ft.Colors.BLACK
                            ),
                            ft.ElevatedButton(
                                "Back to Dashboard",
                                on_click=lambda _: self.page.go("/pm")
                            )
                        ]
                    )
                )
            ]
        )
