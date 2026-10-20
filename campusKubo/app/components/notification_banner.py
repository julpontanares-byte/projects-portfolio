"""
Notification banner component
"""

import flet as ft


class NotificationBanner:
    """Notification banner for displaying messages (info, success, warning, error)"""

    def __init__(self, page_or_message, message_or_type=None, type_or_none=None, on_close=None):
        # Accept signatures: (message, type, on_close) or (page, message, type)
        if hasattr(page_or_message, "session"):
            # (page, message, type)
            self.page = page_or_message
            self.message = message_or_type
            self.type = type_or_none or "info"
        else:
            self.page = None
            self.message = page_or_message
            self.type = message_or_type or "info"
        self.on_close = on_close

    def view(self):
        # Colors & icons per type
        colors = {
            "info":    {"bg": "#E3F2FD", "icon": ft.Icons.INFO,            "icon_color": "#0078FF"},
            "success": {"bg": "#E8F5E9", "icon": ft.Icons.CHECK_CIRCLE,    "icon_color": "#4CAF50"},
            "warning": {"bg": "#FFF3E0", "icon": ft.Icons.WARNING_AMBER,   "icon_color": "#FF9800"},
            "error":   {"bg": "#FFEBEE", "icon": ft.Icons.ERROR,           "icon_color": "#F44336"},
        }

        style = colors.get(self.type, colors["info"])

        container = ft.Container(
            bgcolor=style["bg"],
            padding=15,
            border_radius=10,
            content=ft.Row(
                spacing=10,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    # Icon + Message
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(style["icon"], color=style["icon_color"], size=22),
                            ft.Text(self.message, size=14, weight=ft.FontWeight.W_500, color="#333")
                        ],
                    ),

                    # Close button
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=16,
                        icon_color=ft.Colors.BLACK,
                        tooltip="Dismiss",
                        on_click=self.on_close
                    ) if self.on_close else ft.Container()
                ]
            )
        )
        return container

    def build(self):
        return self.view()
