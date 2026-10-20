import flet as ft

class SearchFilter:
    """Filter buttons for search"""

    def __init__(self, page: ft.Page):
        self.page = page

    def _show_filter_dialog(self, filter_name: str):
        snackbar = ft.SnackBar(
            content=ft.Text(f"{filter_name} filter coming soon!"),
            bgcolor="#333333",
            action="OK",
            action_color="#0078FF"
        )
        self.page.open(snackbar)

    def build(self):
        filters = [
            ("💰 Price Range", "price"),
            ("🏠 Amenities", "amenities"),
            ("🛏 Room Type", "room_type"),
            ("📅 Availability", "availability"),
            ("📍 Location", "location"),
        ]

        filter_buttons = []
        for label, filter_id in filters:
            filter_buttons.append(
                ft.Container(
                    content=ft.OutlinedButton(
                        label,
                        style=ft.ButtonStyle(
                            color="#333333",
                            shape=ft.RoundedRectangleBorder(radius=24),
                        ),
                        icon=ft.Icon(_choose_icon(label), color="#0078FF"),
                        on_click=lambda e, f=label: self._show_filter_dialog(f)
                    ),
                )
            )

        row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,
            wrap=True,
            controls=filter_buttons
        )
        return ft.Container(content=row)


def _choose_icon(label: str):
    """Return a suitable icon for a given filter label"""
    mapping = {
        "💰 Price Range": ft.Icons.PAYMENT,
        "🏠 Amenities": ft.Icons.HOME,
        "🛏 Room Type": ft.Icons.BED,
        "📅 Availability": ft.Icons.CALENDAR_MONTH,
        "📍 Location": ft.Icons.PLACE,
    }
    return mapping.get(label, ft.Icons.FILTER_LIST)
