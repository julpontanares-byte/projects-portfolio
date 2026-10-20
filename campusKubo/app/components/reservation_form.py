"""
Reservation form component
"""
import flet as ft
from datetime import datetime, timedelta

class ReservationForm:
    """Reservation form component"""

    def __init__(self, page: ft.Page, listing_id: int, on_submit=None):
        self.page = page
        self.listing_id = listing_id
        self.on_submit = on_submit

    def build(self):
        # Date pickers
        today = datetime.now()
        tomorrow = today + timedelta(days=1)

        self.start_date = ft.TextField(
            label="Check-in Date",
            hint_text="YYYY-MM-DD",
            value=today.strftime("%Y-%m-%d"),
            width=300,
            prefix_icon=ft.Icons.CALENDAR_TODAY,
            border_radius=10,
        )

        self.end_date = ft.TextField(
            label="Check-out Date",
            hint_text="YYYY-MM-DD",
            value=tomorrow.strftime("%Y-%m-%d"),
            width=300,
            prefix_icon=ft.Icons.CALENDAR_TODAY,
            border_radius=10,
        )

        self.msg = ft.Text(" ", size=12)

        return ft.Container(
            padding=20,
            bgcolor="#FFFFFF",
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color="#00000015",
            ),
            content=ft.Column(
                spacing=15,
                controls=[
                    ft.Text(
                        "Reserve This Property",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color="#1A1A1A"
                    ),
                    self.start_date,
                    self.end_date,
                    self.msg,
                    ft.ElevatedButton(
                        "Submit Reservation",
                        width=300,
                        icon=ft.Icons.CHECK_CIRCLE,
                        style=ft.ButtonStyle(
                            color="white",
                            bgcolor="#0078FF",
                        ),
                        on_click=self._handle_submit
                    )
                ]
            )
        )

    def _handle_submit(self, e):
        """Handle reservation submission"""
        if self.on_submit:
            self.on_submit(
                self.listing_id,
                self.start_date.value,
                self.end_date.value,
                self.msg
            )
            self.page.update()
