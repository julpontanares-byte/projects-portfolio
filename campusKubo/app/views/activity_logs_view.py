import flet as ft
from state.session_state import SessionState
from components.navbar import DashboardNavBar
from components.footer import Footer
from components.admin_utils import format_datetime
from storage.db import get_recent_activity, get_connection
from datetime import datetime, timedelta


class ActivityLogsView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.session = SessionState(page)

        # Controls
        self.search_field = ft.TextField(hint_text="Search actions, user, details, id", expand=True, on_change=self._on_filters_changed)
        self.role_filter = ft.Dropdown(label="Role", options=[ft.dropdown.Option("All"), ft.dropdown.Option("Admin"), ft.dropdown.Option("PM"), ft.dropdown.Option("Tenant")], value="All", width=160, on_change=self._on_filters_changed)
        self.action_filter = ft.Dropdown(label="Action", options=[ft.dropdown.Option("All"), ft.dropdown.Option("Login"), ft.dropdown.Option("Logout"), ft.dropdown.Option("Created"), ft.dropdown.Option("Updated"), ft.dropdown.Option("Deleted"), ft.dropdown.Option("Approved"), ft.dropdown.Option("Rejected"), ft.dropdown.Option("Payment"), ft.dropdown.Option("Reservation")], value="All", width=180, on_change=self._on_filters_changed)
        self.sort_filter = ft.Dropdown(label="Sort", options=[ft.dropdown.Option("Newest first"), ft.dropdown.Option("Oldest first")], value="Newest first", width=160, on_change=self._on_filters_changed)

        self.date_from = ft.TextField(hint_text="From (YYYY-MM-DD)", width=140)
        self.date_to = ft.TextField(hint_text="To (YYYY-MM-DD)", width=140)

        # Quick chips
        self.chips_row = ft.Row(controls=[], spacing=8)

        # Table + pagination
        self.table_container = ft.Container()
        self.pagination_container = ft.Container()
        self.page_index = 0
        self.page_size = 50

        # cache logs fetched from DB
        self._all_logs = []
        try:
            from services.refresh_service import register as _register_refresh
            _register_refresh(self._on_global_refresh)
        except Exception:
            pass

    def _on_global_refresh(self):
        try:
            self._fetch_logs()
            self._render_table()
            self.page.update()
        except Exception:
            pass

    def build(self):
        if not self.session.require_auth(): return None
        if not self.session.is_admin(): self.page.go('/'); return None

        self._fetch_logs()

        navbar = DashboardNavBar(page=self.page, title="Activity Logs", user_email=self.session.get_email() or "").view()

        header = ft.Column([ft.Text("Activity Logs", size=26, weight=ft.FontWeight.BOLD), ft.Text("Track all system actions and events.")])

        # Quick chips
        chips = ft.Row([ft.ElevatedButton("Today", on_click=lambda e: self._apply_quick_range('today')), ft.ElevatedButton("Last 7 days", on_click=lambda e: self._apply_quick_range('7d')), ft.ElevatedButton("Last 30 days", on_click=lambda e: self._apply_quick_range('30d')), ft.ElevatedButton("Custom range", on_click=lambda e: self._apply_quick_range('custom'))], spacing=8)

        filters_row = ft.Row(controls=[self.search_field, self.role_filter, self.action_filter, self.sort_filter, self.date_from, self.date_to], spacing=12)

        # initial render
        self._render_table()

        return ft.View(
            "/admin_activity_logs",
            scroll=ft.ScrollMode.AUTO,
            controls=[
                navbar,
                ft.Container(padding=20, content=ft.Column([
                    ft.Row(controls=[ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self.page.go('/admin')), header], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(),
                    chips,
                    filters_row,
                    ft.Divider(),
                    ft.Container(height=560, content=ft.ListView(expand=True, spacing=8, padding=ft.padding.all(0), controls=[self.table_container])),
                    ft.Divider(),
                    self.pagination_container
                ]))
            ]
        )

    def _fetch_logs(self):
        # Fetch a reasonable number of recent logs and cache them
        rows = get_recent_activity(1000)
        logs = []
        for r in rows:
            logs.append({
                'id': r['id'],
                'user_id': r['user_id'],
                'user_full_name': r['user_full_name'] or r['user_email'] or 'System',
                'action': r['action'] or '',
                'details': r['details'] or '',
                'created_at': r['created_at']
            })
        self._all_logs = logs

    def _apply_quick_range(self, which: str):
        today = datetime.utcnow().date()
        if which == 'today':
            self.date_from.value = today.isoformat()
            self.date_to.value = today.isoformat()
        elif which == '7d':
            self.date_from.value = (today - timedelta(days=7)).isoformat()
            self.date_to.value = today.isoformat()
        elif which == '30d':
            self.date_from.value = (today - timedelta(days=30)).isoformat()
            self.date_to.value = today.isoformat()
        else:
            # custom - let user edit date fields
            self.date_from.value = ''
            self.date_to.value = ''
        self.page_index = 0
        self._render_table()
        self.page.update()

    def _on_filters_changed(self, e=None):
        self.page_index = 0
        self._render_table()
        self.page.update()

    def _filter_logs(self):
        logs = list(self._all_logs)
        q = (self.search_field.value or '').strip().lower()
        if q:
            logs = [l for l in logs if q in (l['action'] or '').lower() or q in (l['details'] or '').lower() or q in (l['user_full_name'] or '').lower() or q in str(l['id'])]

        # role filter: we have limited role info, attempt to derive from user table if needed
        role_val = (self.role_filter.value or 'All').lower()
        if role_val != 'all':
            # naive mapping: check for role words in details (seeded data is limited)
            logs = [l for l in logs if role_val in (l.get('details') or '').lower() or role_val in (l.get('action') or '').lower()]

        # action filter
        action_val = (self.action_filter.value or 'All').lower()
        if action_val != 'all':
            logs = [l for l in logs if action_val in (l.get('action') or '').lower()]

        # date filter
        df = (self.date_from.value or '').strip()
        dt = (self.date_to.value or '').strip()
        if df:
            try:
                df_dt = datetime.fromisoformat(df)
                logs = [l for l in logs if l.get('created_at') and datetime.fromisoformat(l['created_at']) >= df_dt]
            except Exception:
                pass
        if dt:
            try:
                dt_dt = datetime.fromisoformat(dt)
                logs = [l for l in logs if l.get('created_at') and datetime.fromisoformat(l['created_at']) <= dt_dt]
            except Exception:
                pass

        # sort
        if (self.sort_filter.value or 'Newest first') == 'Oldest first':
            logs = list(reversed(logs))

        return logs

    def _render_table(self):
        logs = self._filter_logs()
        total = len(logs)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self.page_index >= total_pages:
            self.page_index = max(0, total_pages - 1)
        start = self.page_index * self.page_size
        end = start + self.page_size
        page_items = logs[start:end]

        if not page_items:
            self.table_container.content = ft.Container(content=ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Icon(ft.Icons.INBOX, size=48, color=ft.Colors.GREY), ft.Text("No logs found", size=14, color=ft.Colors.GREY), ft.Text("Try widening your filters or date range.", size=12, color=ft.Colors.GREY_600)]), padding=ft.padding.symmetric(vertical=24, horizontal=8), alignment=ft.alignment.center, expand=True)
            # update pagination
            self.pagination_container.content = self._build_pagination(total, total_pages)
            return

        rows = []
        for l in page_items:
            ts = format_datetime(l.get('created_at')) if l.get('created_at') else ''
            user = l.get('user_full_name')
            action = l.get('action')
            details = (l.get('details') or '')[:80]
            view_btn = ft.ElevatedButton("View", on_click=lambda e, log=l: self._open_detail_dialog(log))
            rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(ts)), ft.DataCell(ft.Text(user)), ft.DataCell(ft.Text(action)), ft.DataCell(ft.Text(details)), ft.DataCell(view_btn)]))

        table = ft.DataTable(columns=[ft.DataColumn(ft.Text("Timestamp")), ft.DataColumn(ft.Text("User")), ft.DataColumn(ft.Text("Action")), ft.DataColumn(ft.Text("Details")), ft.DataColumn(ft.Text("View"))], rows=rows, column_spacing=12, expand=True)
        self.table_container.content = ft.Container(content=table, expand=True)
        self.pagination_container.content = self._build_pagination(total, total_pages)

    def _build_pagination(self, total_items, total_pages):
        prev_disabled = self.page_index <= 0
        next_disabled = self.page_index >= (total_pages - 1)
        return ft.Row(controls=[ft.ElevatedButton("Prev", disabled=prev_disabled, on_click=lambda e: self._change_page(-1)), ft.Text(f"Page {self.page_index + 1} of {total_pages} (Total: {total_items})"), ft.ElevatedButton("Next", disabled=next_disabled, on_click=lambda e: self._change_page(1))], alignment=ft.MainAxisAlignment.CENTER, spacing=12)

    def _change_page(self, delta: int):
        self.page_index = max(0, self.page_index + delta)
        self._render_table()
        self.page.update()

    def _open_detail_dialog(self, log: dict):
        dlg = ft.AlertDialog(title=ft.Text(f"Log #{log.get('id')}: {log.get('action')}"), content=ft.Column([ft.Row([ft.Text("When:"), ft.Text(format_datetime(log.get('created_at')) or '')]), ft.Row([ft.Text("User:"), ft.Text(log.get('user_full_name') or '')]), ft.Divider(), ft.Text("Details:"), ft.Text(log.get('details') or '')]), actions=[ft.TextButton("Close", on_click=lambda e: self._close_dialog(dlg))], actions_alignment=ft.MainAxisAlignment.END)
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _close_dialog(self, dlg: ft.AlertDialog):
        dlg.open = False
        self.page.update()
