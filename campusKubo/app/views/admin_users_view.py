# app/views/admin_users_view.py

import flet as ft
from typing import Optional
from services.admin_service import AdminService
from components.admin_utils import format_id, format_name, format_datetime
from state.session_state import SessionState
from components.navbar import DashboardNavBar
from components.footer import Footer
from models.user import User, UserRole
from storage.db import get_connection, get_recent_activity
from datetime import datetime
from services.refresh_service import register as _register_refresh, unregister as _unregister_refresh, notify as _notify

class AdminUsersView:

    def __init__(self, page: ft.Page):
        self.page = page
        self.session = SessionState(page)
        self.admin_service = AdminService()
        # UI state: search and role filter
        self.search_field = ft.TextField(hint_text="Search users by name or email", expand=True, on_change=self._on_filters_changed)
        self.role_filter = ft.Dropdown(
            label="Role",
            options=[
                ft.dropdown.Option("All"),
                ft.dropdown.Option("Tenants"),
                ft.dropdown.Option("PMs"),
                ft.dropdown.Option("Admins")
            ],
            value="All",
            on_change=self._on_filters_changed,
            width=200
        )

        # Container to hold the table so we can refresh it in-place
        self.table_container = ft.Container()
        # Container to hold pagination so it can be re-rendered when table changes
        self.pagination_container = ft.Container()
        # pagination
        self.page_index = 0
        self.page_size = 8
        # Tabs state
        self.active_tab = "all"

        # Create/edit user form fields
        self.user_form_full_name = ft.TextField(label="Full Name", width=360)
        self.user_form_email = ft.TextField(label="Email", width=360)
        self.user_form_phone = ft.TextField(label="Phone", width=260)
        self.user_form_role = ft.Dropdown(
            label="Role",
            options=[
                ft.dropdown.Option("Admin", "admin"),
                ft.dropdown.Option("Property Manager", "pm"),
                ft.dropdown.Option("Tenant", "tenant")
            ],
            value=UserRole.TENANT.value,
            width=220
        )
        self.user_form_password = ft.TextField(label="Password", password=True, can_reveal_password=True, width=320)
        self.user_form_active = ft.Switch(label="Active", value=True)
        self._editing_user: Optional[User] = None
        # Inline form container (shown instead of modal dialogs)
        self.inline_form_container = ft.Container(visible=False)
        self.inline_form_visible = False

        # Status and date filters
        self.status_filter2 = ft.Dropdown(
            label="Status",
            options=[ft.dropdown.Option("All"), ft.dropdown.Option("Active"), ft.dropdown.Option("Deactivated")],
            value="All",
            on_change=self._on_filters_changed,
            width=180
        )

        # Use text fields for date input to support a wider range of Flet versions
        self.date_from = ft.TextField(hint_text="From (YYYY-MM-DD)", width=160)
        self.date_to = ft.TextField(hint_text="To (YYYY-MM-DD)", width=160)
        # Register for global refresh notifications
        try:
            _register_refresh(self._on_global_refresh)
        except Exception:
            pass

    def _on_global_refresh(self):
        # Re-render current table when a global refresh is requested
        try:
            self._render_table()
            self.page.update()
        except Exception:
            pass

    def build(self):

        if not self.session.require_auth(): return None
        if not self.session.is_admin(): self.page.go("/"); return None

        # Initial render of users table
        self._render_table()

        navbar = DashboardNavBar(
            page=self.page,
            title="User Management",
            user_email=self.session.get_email() or "",
        ).view()

        # Build header row with search and filters
        filters_row = ft.Row(controls=[self.search_field, self.role_filter, self.status_filter2, self.date_from, self.date_to], spacing=12)

        # Tabs (removed Activity Logs - moved to a dedicated Activity Logs view)
        tabs_control = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="All Users"),
                ft.Tab(text="Tenants"),
                ft.Tab(text="Admins"),
                ft.Tab(text="Property Managers"),
                ft.Tab(text="Deactivated Users"),
            ],
            on_change=self._on_tab_change
        )

        # Inline form content (rebuilt each build)
        form_action_label = "Update User" if self._editing_user else "Create User"
        self.inline_form_container.visible = self.inline_form_visible
        self.inline_form_container.content = ft.Column(
            spacing=12,
            controls=[
                ft.Row([
                    ft.Text(form_action_label, size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.OutlinedButton("Cancel", on_click=lambda e: self._hide_user_form()),
                    ft.ElevatedButton("Save", icon=ft.Icons.SAVE, on_click=self._submit_user_form),
                ], alignment=ft.MainAxisAlignment.START),
                ft.ResponsiveRow(
                    spacing=12,
                    run_spacing=12,
                    controls=[
                        ft.Container(content=self.user_form_full_name, col={"xs":12, "md":6}),
                        ft.Container(content=self.user_form_email, col={"xs":12, "md":6}),
                        ft.Container(content=self.user_form_phone, col={"xs":12, "md":4}),
                        ft.Container(content=self.user_form_role, col={"xs":12, "md":4}),
                        ft.Container(content=self.user_form_active, col={"xs":12, "md":4}),
                        ft.Container(content=self.user_form_password, col={"xs":12, "md":12}),
                    ],
                ),
            ],
        )

        return ft.View(
            "/admin_users",
            scroll=ft.ScrollMode.AUTO,
            controls=[
                navbar,
                ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Row(controls=[
                            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.page.go('/admin')),
                            ft.Text("All Registered Users", size=26, weight= ft.FontWeight.BOLD)
                        ], alignment=ft.MainAxisAlignment.START),
                        ft.Divider(),
                        ft.Row(
                            spacing=12,
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(expand=True, content=tabs_control),
                                ft.ElevatedButton(
                                    "Add User",
                                    icon=ft.Icons.ADD,
                                    on_click=lambda e: self._show_user_form()
                                )
                            ]
                        ),
                        self.inline_form_container,
                        filters_row,
                        ft.Divider(),
                        # Charts area
                        ft.Row(controls=[self._build_registration_chart_container(), self._build_active_inactive_card()], spacing=16),
                        ft.Divider(),
                        ft.Container(height=420, content=ft.ListView(expand=True, spacing=8, padding=ft.padding.all(0), controls=[self.table_container])),
                        ft.Divider(),
                        self.pagination_container
                    ])
                )
            ]
        )

    def _set_active(self, user_id: int, active: bool):
        # Show confirmation dialog before changing active status
        from components.dialog_helper import open_dialog, close_dialog
        from services.admin_service import AdminService

        verb = "Activate" if active else "Deactivate"
        dlg = ft.AlertDialog(
            title=ft.Text(f"{verb} User", weight=ft.FontWeight.BOLD),
            content=ft.Text(f"Are you sure you want to {verb.lower()} this user?"),
            modal=True,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e, d=None: close_dialog(self.page, dlg)),
                ft.ElevatedButton(verb, bgcolor=("#4CAF50" if active else "#D32F2F"), color="white", on_click=lambda e, uid=user_id: self._perform_set_active(uid, active, dlg))
            ]
        )
        open_dialog(self.page, dlg)
        # Fallback: ensure dialog is set on page.dialog for Flet variants
        try:
            if hasattr(self.page, "dialog"):
                setattr(self.page, "dialog", dlg)
            self.page.update()
        except Exception:
            pass

    def _confirm_delete(self, user_id: int):
        from components.dialog_helper import open_dialog, close_dialog

        dlg = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text("Are you sure you want to permanently delete this user? This action cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_dialog(self.page, dlg)),
                ft.ElevatedButton("Delete", bgcolor="#D32F2F", color="white", on_click=lambda e, uid=user_id: self._perform_delete(uid, dlg))
            ]
        )
        open_dialog(self.page, dlg)
        try:
            self.page.update()
        except Exception:
            pass

    def _perform_delete(self, user_id: int, dlg: ft.AlertDialog):
        from components.dialog_helper import close_dialog
        svc = AdminService()
        ok = svc.delete_user(user_id)
        # Close dialog reliably using helper
        try:
            close_dialog(self.page, dlg)
        except Exception:
            try:
                dlg.open = False
            except Exception:
                pass

        from services.refresh_service import notify as _notify

        if ok:
            try:
                self.page.open(ft.SnackBar(ft.Text('User deleted')))
            except Exception:
                pass
        else:
            try:
                self.page.open(ft.SnackBar(ft.Text('Failed to delete user')))
            except Exception:
                pass

        # refresh
        try:
            # Notify other views and re-render current table
            try:
                _notify()
            except Exception:
                pass
            self._render_table()
            self.page.update()
        except Exception:
            pass

    def _perform_set_active(self, user_id: int, active: bool, dlg: ft.AlertDialog):
        """Perform activate/deactivate after confirmation dialog."""
        from components.dialog_helper import close_dialog
        svc = AdminService()
        ok = False

        # Close the dialog first so the scrim disappears even if service call fails
        try:
            close_dialog(self.page, dlg)
        except Exception:
            try:
                dlg.open = False
            except Exception:
                pass

        try:
            ok = svc.activate_user(user_id) if active else svc.deactivate_user(user_id)
        except Exception:
            ok = False

        from services.refresh_service import notify as _notify

        if ok:
            try:
                self.page.open(ft.SnackBar(ft.Text('User status updated')))
            except Exception:
                pass
        else:
            try:
                self.page.open(ft.SnackBar(ft.Text('Failed to update user')))
            except Exception:
                pass

        # Re-render the table in-place so current tab updates immediately
        try:
            try:
                _notify()
            except Exception:
                pass
            self._render_table()
            self.page.update()
        except Exception:
            pass

    # --------------------
    # Filtering / rendering
    # --------------------
    def _on_filters_changed(self, e):
        # Re-render table with new filters
        self._render_table()
        self.page.update()

    def _render_table(self):
        # Build SQL-backed filters (role, status, date range)
        role_tab = self.active_tab  # 'all', 'tenants', 'pms', 'deactivated', 'activity'

        # role filter from dropdown still applies in combination
        role_val = (self.role_filter.value or "All").lower()
        role_enum = None
        if role_val == 'tenants':
            role_enum = UserRole.TENANT
        elif role_val == 'pms':
            role_enum = UserRole.PROPERTY_MANAGER
        elif role_val == 'admins':
            role_enum = UserRole.ADMIN

        # status filter from second dropdown
        status_val = (self.status_filter2.value or "All").lower()
        status_active = None
        if status_val == 'active':
            status_active = 1
        elif status_val == 'deactivated':
            status_active = 0

        # date filters
        df = getattr(self.date_from, 'value', None)
        dt = getattr(self.date_to, 'value', None)

        users = self._fetch_users(role=role_enum, active=status_active, date_from=df, date_to=dt, tab=role_tab)

        # Apply search filter client-side
        q = (self.search_field.value or "").strip().lower()
        if q:
            users = [u for u in users if (getattr(u, 'full_name', '') or '').lower().find(q) != -1 or (getattr(u, 'email', '') or '').lower().find(q) != -1]

        # Pagination slice: clamp page index so tab switches don't leave invalid page indices
        total = len(users)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self.page_index >= total_pages:
            self.page_index = max(0, total_pages - 1)
        start = self.page_index * self.page_size
        end = start + self.page_size
        page_items = users[start:end]

        rows = []
        for u in page_items:
            uid = getattr(u, 'id', None)
            if uid is None:
                continue  # Skip rows without valid user IDs

            name = getattr(u, 'full_name', '')
            email = getattr(u, 'email', '')
            role = getattr(u, 'role', '') if not isinstance(getattr(u, 'role', ''), UserRole) else getattr(u, 'role').value
            activate_btn = ft.ElevatedButton("Activate", on_click=lambda e, _id=uid: self._set_active(_id, True))
            deactivate_btn = ft.OutlinedButton("Deactivate", on_click=lambda e, _id=uid: self._set_active(_id, False))
            delete_btn = ft.IconButton(ft.Icons.DELETE, tooltip="Delete user", on_click=lambda e, _id=uid: self._confirm_delete(_id))
            edit_btn = ft.IconButton(ft.Icons.EDIT, tooltip="Edit user", on_click=lambda e, user=u: self._show_user_form(user))
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(format_id('U', uid))),
                ft.DataCell(ft.Text(format_name(name))),
                ft.DataCell(ft.Text(email)),
                ft.DataCell(ft.Text((role or '').title())),
                ft.DataCell(ft.Row([edit_btn, activate_btn, deactivate_btn, delete_btn], spacing=6))
            ]))

        # If nothing to show, display friendly empty state
        if not page_items:
            self.table_container.content = ft.Container(
                content=ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Icon(ft.Icons.INBOX, size=48, color=ft.Colors.GREY),
                    ft.Text("No Data Yet", size=14, color=ft.Colors.GREY),
                    ft.Text("There are no results for the selected filters.", size=12, color=ft.Colors.GREY_600),
                ]),
                padding=ft.padding.symmetric(vertical=24, horizontal=8),
                alignment=ft.alignment.center,
                expand=True,
            )
            # Ensure pagination reflects current total/pages even when there are
            # no items on the current page (so buttons and page number update).
            try:
                self.pagination_container.content = self._build_pagination()
            except Exception:
                # In case pagination container hasn't been created yet (older calls), ignore.
                pass
            return

        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Role")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=rows,
            column_spacing=16,
            expand=True,
            border=ft.border.all(1, "#E0E0E0"),
            heading_row_color="#F9F9F9",
            heading_row_height=48,
        )

        # Use reusable TableContainer component to wrap the DataTable
        # Use the simpler DataTable layout directly inside a container (no TableCard)
        self.table_container.content = ft.Container(content=table, expand=True, padding=ft.padding.only(top=6, bottom=6))
        # Update pagination to reflect the current filtered dataset and page index
        try:
            self.pagination_container.content = self._build_pagination()
        except Exception:
            pass

    def _reset_form_fields(self):
        self._editing_user = None
        self.user_form_full_name.value = ""
        self.user_form_email.value = ""
        self.user_form_phone.value = ""
        self.user_form_role.value = UserRole.TENANT.value
        self.user_form_active.value = True
        self.user_form_password.value = ""
        self.user_form_password.hint_text = "Set a password for the new user"

    def _show_user_form(self, user: Optional[User] = None):
        # Populate fields for edit or reset for create
        if user:
            self._editing_user = user
            self.user_form_full_name.value = user.full_name or ""
            self.user_form_email.value = user.email or ""
            self.user_form_phone.value = user.phone or ""
            self.user_form_role.value = user.role.value if hasattr(user, 'role') else UserRole.TENANT.value
            self.user_form_active.value = getattr(user, 'is_active', True)
            self.user_form_password.value = ""
            self.user_form_password.hint_text = "Leave blank to keep current password"
        else:
            self._reset_form_fields()

        self.inline_form_visible = True
        self.inline_form_container.visible = True
        try:
            self.page.update()
        except Exception:
            pass

    def _hide_user_form(self, *_):
        self.inline_form_visible = False
        self.inline_form_container.visible = False
        self._reset_form_fields()
        try:
            self.page.update()
        except Exception:
            pass

    def _submit_user_form(self, _):
        full_name = (self.user_form_full_name.value or "").strip()
        email = (self.user_form_email.value or "").strip()
        role_value = self.user_form_role.value or UserRole.TENANT.value
        phone = (self.user_form_phone.value or "").strip() or None
        is_active = bool(self.user_form_active.value)
        password = (self.user_form_password.value or "").strip()

        # Validate required fields
        if not full_name or not email or not role_value:
            self.page.open(ft.SnackBar(ft.Text("Name, email, and role are required.")))
            return

        # Validate password for new users
        if not self._editing_user and not password:
            self.page.open(ft.SnackBar(ft.Text("Password is required for new users.")))
            return

        # Perform save inline (no modal)
        if self._editing_user:
            user_id = getattr(self._editing_user, 'id', None)
            if not user_id:
                self.page.open(ft.SnackBar(ft.Text("Selected user is invalid.")))
                return
            ok, msg = self.admin_service.update_user_account(user_id, full_name, email, role_value, is_active, phone)
            if ok and password:
                self.admin_service.reset_user_password(user_id, password)
        else:
            ok, msg = self.admin_service.create_user_account(full_name, email, role_value, password, is_active)

        if ok:
            self.page.open(ft.SnackBar(ft.Text(msg)))
            try:
                from services.refresh_service import notify as _notify
                _notify()
            except Exception:
                pass
            self._hide_user_form()
            self._render_table()
            self.page.update()
        else:
            self.page.open(ft.SnackBar(ft.Text(msg)))

    def _build_pagination(self):
        # compute total items according to current filters (use same logic as _render_table)
        role_val = (self.role_filter.value or "All").lower()
        role_enum = None
        if role_val == 'tenants':
            role_enum = UserRole.TENANT
        elif role_val == 'pms':
            role_enum = UserRole.PROPERTY_MANAGER
        elif role_val == 'admins':
            role_enum = UserRole.ADMIN

        status_val = (self.status_filter2.value or "All").lower()
        status_active = None
        if status_val == 'active':
            status_active = 1
        elif status_val == 'deactivated':
            status_active = 0

        df = getattr(self.date_from, 'value', None) or (self.date_from.value if hasattr(self.date_from, 'value') else None)
        dt = getattr(self.date_to, 'value', None) or (self.date_to.value if hasattr(self.date_to, 'value') else None)

        users = self._fetch_users(role=role_enum, active=status_active, date_from=df, date_to=dt, tab=self.active_tab)
        q = (self.search_field.value or "").strip().lower()
        if q:
            users = [u for u in users if (getattr(u, 'full_name', '') or '').lower().find(q) != -1 or (getattr(u, 'email', '') or '').lower().find(q) != -1]
        total_items = len(users)

        # Compute total pages and clamp current page index
        total_pages = max(1, (total_items + self.page_size - 1) // self.page_size)
        if self.page_index >= total_pages:
            self.page_index = max(0, total_pages - 1)

        prev_disabled = self.page_index <= 0
        next_disabled = self.page_index >= (total_pages - 1)

        return ft.Row(controls=[
            ft.ElevatedButton("Prev", disabled=prev_disabled, on_click=lambda e: self._change_page(-1)),
            ft.Text(f"Page {self.page_index + 1} of {total_pages}"),
            ft.ElevatedButton("Next", disabled=next_disabled, on_click=lambda e: self._change_page(1)),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=12)

    def _change_page(self, delta: int):
        self.page_index = max(0, self.page_index + delta)
        self._render_table()
        self.page.update()

    # --------------------
    # Data access helpers
    # --------------------
    def _fetch_users(self, role: Optional[UserRole] = None, active: Optional[int] = None, date_from: Optional[str] = None, date_to: Optional[str] = None, tab: str = 'all'):
        """Query users table with optional filters and return list[User]."""
        conn = get_connection()
        cur = conn.cursor()
        q = "SELECT * FROM users WHERE 1=1"
        params = []
        # Tab-based overrides
        if tab == 'deactivated':
            q += " AND is_active = 0"
        # Role filtering: use flexible LIKE matching so 'Tenant One' or similar values are matched
        if tab == 'tenants':
            q += " AND (lower(role) LIKE '%tenant%')"
        elif tab == 'pms':
            q += " AND (lower(role) LIKE '%pm%' OR lower(role) LIKE '%property%')"
        elif tab == 'admins':
            q += " AND (lower(role) LIKE '%admin%')"
        elif role:
            # role is a UserRole enum; do flexible matching as well
            rv = role.value.lower()
            if rv == 'pm' or rv == 'property_manager':
                q += " AND (lower(role) LIKE '%pm%' OR lower(role) LIKE '%property%')"
            else:
                q += " AND lower(role) LIKE ?"
                params.append(f"%{rv}%")
        if active is not None:
            q += " AND is_active = ?"
            params.append(active)
        if date_from:
            q += " AND date(created_at) >= date(?)"
            if isinstance(date_from, str):
                df_str = date_from.strip()
            elif hasattr(date_from, 'isoformat'):
                df_str = date_from.isoformat()
            else:
                df_str = str(date_from)
            params.append(df_str)
        if date_to:
            q += " AND date(created_at) <= date(?)"
            if isinstance(date_to, str):
                dt_str = date_to.strip()
            elif hasattr(date_to, 'isoformat'):
                dt_str = date_to.isoformat()
            else:
                dt_str = str(date_to)
            params.append(dt_str)

        q += " ORDER BY created_at DESC"
        try:
            cur.execute(q, tuple(params))
            rows = cur.fetchall()
            from models.user import User
            users = [User.from_db_row(r) for r in rows]
            return users
        finally:
            conn.close()

    # --------------------
    # Tabs and charts
    # --------------------
    def _on_tab_change(self, e):
        idx = e.control.selected_index
        mapping = {0: 'all', 1: 'tenants', 2: 'admins', 3: 'pms', 4: 'deactivated'}
        self.active_tab = mapping.get(idx, 'all')

        # Update filters to match the selected tab so state from a
        # previously-selected tab doesn't leak into the next one.
        if self.active_tab == 'tenants':
            self.role_filter.value = 'Tenants'
            self.status_filter2.value = 'All'
        elif self.active_tab == 'admins':
            self.role_filter.value = 'Admins'
            self.status_filter2.value = 'All'
        elif self.active_tab == 'pms':
            self.role_filter.value = 'PMs'
            self.status_filter2.value = 'All'
        elif self.active_tab == 'deactivated':
            # Show deactivated users regardless of role
            self.role_filter.value = 'All'
            self.status_filter2.value = 'Deactivated'
        else:
            self.role_filter.value = 'All'
            self.status_filter2.value = 'All'

        # Reset pagination when switching tabs and re-render
        self.page_index = 0
        self._render_table()
        self.page.update()

        # Users view continues below. Activity-logs table removed from here.

    def _build_registration_chart_container(self):
        # Build a small LineChart with registrations per month (last 6 months)
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as cnt FROM users GROUP BY month ORDER BY month DESC LIMIT 6")
            data = cur.fetchall()
        finally:
            conn.close()

        # If no data, use sample
        if not data:
            sample = [("2025-06", 5), ("2025-07", 8), ("2025-08", 10), ("2025-09", 7), ("2025-10", 12), ("2025-11", 9)]
            data = sample

        data = list(reversed(data))
        points = []
        labels = []
        for i, row in enumerate(data, start=1):
            # row[0] is expected to be a string like 'YYYY-MM' but can be None
            m = row[0] if row and row[0] is not None else ""
            try:
                v = int(row[1] if row and row[1] is not None else 0)
            except Exception:
                v = 0

            # Safe slice: if month string is shorter than expected, fall back to whole string
            lbl = (m[5:] if isinstance(m, str) and len(m) >= 6 else (m or ""))
            labels.append((i, lbl))
            points.append(ft.LineChartDataPoint(x=i, y=v, tooltip=str(v)))

        bottom_axis = ft.ChartAxis(labels=[ft.ChartAxisLabel(value=i, label=ft.Text(lbl, size=10)) for i, lbl in labels], labels_size=10)
        max_y = max([int(r[1]) for r in data]) if data else 1
        chart = ft.LineChart(
            data_series=[ft.LineChartData(data_points=points, curved=True, color="#2196F3", stroke_width=2)],
            left_axis=ft.ChartAxis(labels=[ft.ChartAxisLabel(value=v, label=ft.Text(str(v), size=10)) for v in range(0, max_y + 1, max(1, max_y//4))]),
            bottom_axis=bottom_axis,
            height=160,
            expand=True,
        )

        card = ft.Container(bgcolor="white", padding=12, border_radius=8, expand=True, content=ft.Column(controls=[ft.Text("User Registrations", weight=ft.FontWeight.BOLD), chart]))
        return card

    def _build_active_inactive_card(self):
        # Query active vs inactive counts
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT SUM(CASE WHEN is_active=1 THEN 1 ELSE 0 END) as active, SUM(CASE WHEN is_active=0 THEN 1 ELSE 0 END) as inactive FROM users")
            row = cur.fetchone()
        finally:
            conn.close()

        active = (row[0] or 0) if row else 0
        inactive = (row[1] or 0) if row else 0

        # Simple bar representation using BarChart
        groups = [
            ft.BarChartGroup(x=0, bar_rods=[ft.BarChartRod(to_y=active, width=30, color="#4CAF50")]),
            ft.BarChartGroup(x=1, bar_rods=[ft.BarChartRod(to_y=inactive, width=30, color="#F44336")]),
        ]
        chart = ft.BarChart(bar_groups=groups, groups_space=30, height=140, expand=True, bottom_axis=ft.ChartAxis(labels=[ft.ChartAxisLabel(value=0, label=ft.Text("Active")), ft.ChartAxisLabel(value=1, label=ft.Text("Inactive"))]))
        card = ft.Container(bgcolor="white", padding=12, border_radius=8, width=320, content=ft.Column(controls=[ft.Text("Active vs Inactive Users", weight=ft.FontWeight.BOLD), chart, ft.Text(f"Active: {active}  Inactive: {inactive}")]))
        return card
