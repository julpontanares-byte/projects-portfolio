"""
Tenant Messages View
"""
import flet as ft
from state.session_state import SessionState


class TenantMessagesView:
    """View for tenant to see and send messages"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.session = SessionState(page)

    def build(self):
        """Build the messages view"""
        # Require authentication
        if not self.session.require_auth():
            return None

        user_id = self.session.get_user_id()
        if not user_id:
            self.page.go("/login")
            return None

        # Mock conversation list (to be replaced with real data)
        conversations = [
            {
                "id": 1,
                "property_name": "Cozy Studio Apartment",
                "last_message": "Thank you for your inquiry!",
                "timestamp": "2 hours ago",
                "unread": True
            },
            {
                "id": 2,
                "property_name": "Downtown Boarding House",
                "last_message": "The room is still available.",
                "timestamp": "Yesterday",
                "unread": False
            }
        ]

        # Create conversation cards
        conversation_cards = []
        for conv in conversations:
            card = ft.Container(
                bgcolor="#FFFFFF",
                padding=16,
                border_radius=8,
                border=ft.border.all(2 if conv.get("unread") else 1, "#0078FF" if conv.get("unread") else "#E0E0E0"),
                content=ft.Row(
                    controls=[
                        ft.Container(
                            width=50,
                            height=50,
                            border_radius=25,
                            bgcolor="#E3F2FD",
                            content=ft.Icon(ft.Icons.HOME, color="#0078FF", size=24),
                            alignment=ft.alignment.center
                        ),
                        ft.Container(
                            expand=True,
                            content=ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text(
                                        conv.get("property_name", "Unknown"),
                                        size=16,
                                        weight=ft.FontWeight.BOLD if conv.get("unread") else ft.FontWeight.NORMAL
                                    ),
                                    ft.Text(
                                        conv.get("last_message", ""),
                                        size=14,
                                        color="#666",
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS
                                    ),
                                    ft.Text(
                                        conv.get("timestamp", ""),
                                        size=12,
                                        color="#999"
                                    )
                                ]
                            )
                        ),
                        ft.Icon(
                            ft.Icons.CIRCLE,
                            size=12,
                            color="#0078FF" if conv.get("unread") else "transparent"
                        )
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                on_click=lambda e, c=conv: self._open_conversation(c),
                ink=True
            )
            conversation_cards.append(card)

        # Build the view
        return ft.View(
            "/tenant/messages",
            controls=[
                ft.Container(
                    bgcolor="#F5F7FA",
                    expand=True,
                    padding=40,
                    content=ft.Column(
                        spacing=20,
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            # Header
                            ft.Row(
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.ARROW_BACK,
                                        on_click=lambda _: self.page.go("/tenant"),
                                        tooltip="Back to Dashboard"
                                    ),
                                    ft.Text("Messages", size=32, weight=ft.FontWeight.BOLD),
                                    ft.Container(expand=True),
                                    ft.IconButton(
                                        icon=ft.Icons.ADD,
                                        tooltip="New Message",
                                        on_click=lambda _: self._new_message()
                                    )
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            # Messages/Conversations list
                            ft.Container(
                                content=ft.Column(
                                    spacing=12,
                                    controls=conversation_cards if conversation_cards else [
                                        ft.Container(
                                            padding=40,
                                            content=ft.Column(
                                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                controls=[
                                                    ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, size=64, color="#999"),
                                                    ft.Text("No messages yet", size=20, weight=ft.FontWeight.BOLD, color="#666"),
                                                    ft.Text("Start a conversation with property owners", size=14, color="#999"),
                                                    ft.ElevatedButton(
                                                        "Browse Listings",
                                                        icon=ft.Icons.SEARCH,
                                                        on_click=lambda _: self.page.go("/browse")
                                                    )
                                                ],
                                                spacing=16
                                            )
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                )
            ],
            padding=0,
            bgcolor="#F5F7FA"
        )

    def _open_conversation(self, conversation):
        """Open a specific conversation"""
        self.page.open(ft.SnackBar(
            content=ft.Text(f"Opening conversation about {conversation.get('property_name')}"),
            bgcolor="#0078FF"


        ))
        self.page.update()

    def _new_message(self):
        """Start a new message"""
        self.page.open(ft.SnackBar(
            content=ft.Text("New message feature coming soon!"),
            bgcolor="#0078FF"


        ))
        self.page.update()
