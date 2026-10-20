import flet as ft
from services.admin_service import AdminService
from components.navbar import DashboardNavBar
from components.admin_utils import format_id, format_name, format_datetime
from components.table_card import TableCard
from state.session_state import SessionState
from typing import Optional, Any
from services.refresh_service import register as _register_refresh


class AdminPMVerificationView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.session = SessionState(page)
        self.admin_service = AdminService()

        # pagination state
        self.page_index = 0
        self.page_size = 8
        self.table_container = ft.Container()
        try:
            _register_refresh(self._on_global_refresh)
        except Exception:
            pass

    def _on_global_refresh(self):
        # Recompute pending list and rebuild view
        try:
            # keep the same page index when refreshing
            self.page.go('/admin_pm_verification')
        except Exception:
            pass

    def build(self):
        if not self.session.require_auth():
            return None
        if not self.session.is_admin():
            self.page.go("/")
            return None

        pending = self.admin_service.get_pending_pm_accounts()
        total = len(pending)

        start = self.page_index * self.page_size
        end = start + self.page_size
        # Clamp page_index before slicing so empty tabs don't corrupt pagination
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self.page_index >= total_pages:
            self.page_index = max(0, total_pages - 1)
        page_items = pending[start:end]

        rows = []
        for pm in page_items:
            pid = getattr(pm, 'id', None)
            name = getattr(pm, 'full_name', '')
            email = getattr(pm, 'email', '')
            created_at = getattr(pm, 'created_at', '')

            view_btn = ft.ElevatedButton("View", on_click=lambda e, m=pm: self._open_pm_dialog(m))
            approve_btn = ft.ElevatedButton("Approve", on_click=lambda e, uid=pid: self._confirm_action('approve', uid))
            reject_btn = ft.OutlinedButton("Reject", on_click=lambda e, uid=pid: self._confirm_action('reject', uid))

            rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(format_id('PM', pid))),
                    ft.DataCell(ft.Text(format_name(name))),
                    ft.DataCell(ft.Text(email)),
                    ft.DataCell(ft.Text(format_datetime(created_at))),
                    ft.DataCell(ft.Row([view_btn, approve_btn, reject_btn], spacing=6))
                ])
            )

        if not page_items:
            self.table_container.content = ft.Container(
                content=ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Icon(ft.Icons.INBOX, size=48, color=ft.Colors.GREY),
                    ft.Text("No Data Yet", size=14, color=ft.Colors.GREY),
                    ft.Text("There are no pending applications.", size=12, color=ft.Colors.GREY_600),
                ]),
                padding=ft.padding.symmetric(vertical=24, horizontal=8),
                alignment=ft.alignment.center,
                expand=True,
            )
            return

        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Applied At")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=rows,
            column_spacing=14,
            expand=True,
            border=ft.border.all(1, "#E0E0E0"),
            heading_row_color="#F9F9F9",
            heading_row_height=48,
        )

        # Display DataTable directly without TableCard for a minimal appearance
        self.table_container.content = ft.Container(content=table, expand=True, padding=ft.padding.only(top=6, bottom=6))

        # pagination controls - compute total pages and clamp index
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self.page_index >= total_pages:
            self.page_index = max(0, total_pages - 1)

        prev_disabled = self.page_index <= 0
        next_disabled = self.page_index >= (total_pages - 1)

        pagination = ft.Row(
            controls=[
                ft.ElevatedButton("Prev", disabled=prev_disabled, on_click=lambda e: self._change_page(-1)),
                ft.Text(f"Page {self.page_index + 1} of {total_pages}"),
                ft.ElevatedButton("Next", disabled=next_disabled, on_click=lambda e: self._change_page(1)),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12
        )

        return ft.View(
            "/admin_pm_verification",
            scroll=ft.ScrollMode.AUTO,
            controls=[
                DashboardNavBar(self.page, "PM Verification", self.session.get_email() or "").view(),
                ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Row(controls=[
                            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.page.go('/admin')),
                            ft.Text("Pending Property Manager Applications", size=20, weight=ft.FontWeight.BOLD)
                        ], alignment=ft.MainAxisAlignment.START),
                        ft.Divider(),
                        ft.Container(height=440, content=self.table_container),
                        ft.Divider(),
                        pagination
                    ])
                )
            ]
        )

    def _change_page(self, delta: int):
        self.page_index = max(0, self.page_index + delta)
        self.page.go('/admin_pm_verification')

    def _confirm_action(self, action: str, user_id: Optional[int]):
        title = "Confirm"
        msg = f"Are you sure you want to {action} this Property Manager?"
        dlg = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(msg),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton(action.capitalize(), on_click=lambda e, a=action, uid=user_id: self._perform_action(a, uid))
            ]
        )
        setattr(self.page, 'dialog', dlg)
        dlg.open = True
        self.page.update()

    def _close_dialog(self):
        dlg = getattr(self.page, 'dialog', None)
        if dlg:
            dlg.open = False
            self.page.update()

    def _perform_action(self, action: str, user_id: Optional[int]):
        self._close_dialog()
        # guard against missing id
        if user_id is None:
            setattr(self.page, 'snack_bar', ft.SnackBar(ft.Text('Invalid user id')))
            sb = getattr(self.page, 'snack_bar', None)
            if sb and hasattr(self.page, 'open'):
                try:
                    self.page.open(sb)
                except Exception:
                    pass
            self.page.update()
            return

        if action == 'approve':
            ok = self.admin_service.approve_pm(user_id)
            if ok:
                setattr(self.page, 'snack_bar', ft.SnackBar(ft.Text('Property Manager approved')))
            else:
                setattr(self.page, 'snack_bar', ft.SnackBar(ft.Text('Failed to approve')))
        else:
            ok = self.admin_service.reject_pm(user_id)
            if ok:
                setattr(self.page, 'snack_bar', ft.SnackBar(ft.Text('Property Manager rejected')))
            else:
                setattr(self.page, 'snack_bar', ft.SnackBar(ft.Text('Failed to reject')))

        sb = getattr(self.page, 'snack_bar', None)
        if sb and hasattr(self.page, 'open'):
            try:
                self.page.open(sb)
            except Exception:
                pass

        # Notify global refresh service
        try:
            from services.refresh_service import notify as _notify
            _notify()
        except Exception:
            pass

        self.page.update()
        # refresh view
        self.page.go('/admin_pm_verification')

    def _open_pm_dialog(self, pm):
        # show details modal with approve/reject
        name = getattr(pm, 'full_name', '')
        email = getattr(pm, 'email', '')
        bio = getattr(pm, 'bio', '') if hasattr(pm, 'bio') else ''
        content = ft.Column([
            ft.Text(f"Name: {name}"),
            ft.Text(f"Email: {email}"),
            ft.Text(f"Notes: {bio}"),
        ])
        dlg = ft.AlertDialog(
            title=ft.Text("Property Manager Application"),
            content=content,
            actions=[
                ft.TextButton("Close", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Approve", on_click=lambda e, uid=getattr(pm, 'id', None): self._perform_action('approve', uid)),
                ft.OutlinedButton("Reject", on_click=lambda e, uid=getattr(pm, 'id', None): self._perform_action('reject', uid)),
            ]
        )
        setattr(self.page, 'dialog', dlg)
        dlg.open = True
        self.page.update()
