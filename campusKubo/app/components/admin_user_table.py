# app/components/admin_user_table.py
import flet as ft
from models.user import UserRole, User
from typing import List, Optional, Callable

class AdminUserTable:
    def __init__(
        self,
        users: List[User],
        role: UserRole,
        on_activate: Optional[Callable[[int], None]] = None,
        on_deactivate: Optional[Callable[[int], None]] = None,
        on_approve: Optional[Callable[[int], None]] = None,
        on_reject: Optional[Callable[[int], None]] = None
    ):
        self.users = users
        self.role = role
        self.on_activate = on_activate
        self.on_deactivate = on_deactivate
        self.on_approve = on_approve
        self.on_reject = on_reject

    def build(self):
        rows = []
        for user in self.users:
            action_buttons = []

            # PM Approve/Reject buttons
            if self.role == UserRole.PROPERTY_MANAGER:
                if self.on_approve:
                    handler = self.on_approve
                    action_buttons.append(
                        ft.IconButton(
                            icon=ft.Icons.CHECK,
                            icon_color="green",
                            tooltip="Approve",
                            on_click=lambda e, uid=user.id, handler=handler: handler(uid)
                        )
                    )
                if self.on_reject:
                    handler = self.on_reject
                    action_buttons.append(
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_color="red",
                            tooltip="Reject",
                            on_click=lambda e, uid=user.id, handler=handler: handler(uid)
                        )
                    )

            # Activate/Deactivate buttons
            if user.role == self.role:
                if self.on_activate:
                    handler = self.on_activate
                    action_buttons.append(
                        ft.IconButton(
                            icon=ft.Icons.PLAY_ARROW,
                            icon_color="blue",
                            tooltip="Activate",
                            on_click=lambda e, uid=user.id, handler=handler: handler(uid)
                        )
                    )
                if self.on_deactivate:
                    handler = self.on_deactivate
                    action_buttons.append(
                        ft.IconButton(
                            icon=ft.Icons.PAUSE,
                            icon_color="orange",
                            tooltip="Deactivate",
                            on_click=lambda e, uid=user.id, handler=handler: handler(uid)
                        )
                    )

            rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(user.id))),
                    ft.DataCell(ft.Text(user.email)),
                    ft.DataCell(ft.Text(user.full_name or "")),
                    ft.DataCell(ft.Text(user.role.value)),
                    ft.DataCell(ft.Row(controls=action_buttons, spacing=5))
                ])
            )

        # Match the simple DataTable style: numeric ID, simple columns, rows built from DataRow
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID"), numeric=True),
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Full Name")),
                ft.DataColumn(ft.Text("Role")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=rows,
            column_spacing=12,
            expand=True,
        )
