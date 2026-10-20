# app/views/admin_reports_view.py

import flet as ft
from services.report_service import ReportService
from services.refresh_service import register as register_refresh, notify as notify_refresh
from services.activity_service import ActivityService
from services.settings_service import SettingsService
from state.session_state import SessionState
from components.navbar import DashboardNavBar

class AdminReportsView:

    def __init__(self, page):
        self.page = page
        self.session = SessionState(page)
        self.report_service = ReportService()
        self.status_filter = None
        self.reporter_filter = None
        self.start_date = None
        self.end_date = None
        # register refresh hook
        try:
            register_refresh(self._on_global_refresh)
        except Exception:
            pass

    def build(self):
        if not self.session.require_auth(): return None
        if not self.session.is_admin(): self.page.go("/"); return None

        reports = self.report_service.get_reports(status=self.status_filter, start_date=self.start_date, end_date=self.end_date, reporter_email=self.reporter_filter)

        report_cards = []
        for r in reports:
            rid = r.get('id') if isinstance(r, dict) else getattr(r, 'id', None)
            reporter = r.get('reporter_email') if isinstance(r, dict) else getattr(r, 'reporter_email', None)
            message = r.get('message') if isinstance(r, dict) else getattr(r, 'message', None)
            addr = r.get('listing_address') if isinstance(r, dict) else getattr(r, 'listing_address', None)
            resolve_btn = ft.ElevatedButton("Resolve", on_click=lambda e, _id=rid: self._resolve_report(_id) if _id else None)
            escalate_btn = ft.ElevatedButton("Escalate", bgcolor="#FF9800", on_click=lambda e, _id=rid: self._open_escalate_dialog(_id))
            assign_btn = ft.ElevatedButton("Assign to Me", bgcolor="#2196F3", on_click=lambda e, _id=rid: self._assign_to_current_admin(_id))
            report_cards.append(
                ft.Container(
                    padding=20,
                    bgcolor="white",
                    border_radius=12,
                    margin=ft.margin.only(bottom=12),
                    content=ft.Column([
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                            ft.Text(f"Report #{rid}", size=18, weight=ft.FontWeight.BOLD),
                            ft.Text(addr or "", size=12, color=ft.Colors.BLACK)
                        ]),
                        ft.Text(f"Submitted by: {reporter}"),
                        ft.Text(f"Message: {message}"),
                        ft.Row(controls=[resolve_btn, escalate_btn, assign_btn], alignment=ft.MainAxisAlignment.END)
                    ])
                )
            )

        return ft.View(
            "/admin_reports",
            scroll=ft.ScrollMode.AUTO,
            controls=[
                DashboardNavBar(self.page, "Report Management", self.session.get_email() or "").view(),
                ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Row(controls=[
                            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.page.go('/admin')),
                            ft.Text("Reports", size=26, weight=ft.FontWeight.BOLD)
                        ], alignment=ft.MainAxisAlignment.START),
                        ft.Divider(),
                        # Filters
                        ft.Row([
                            ft.Dropdown(width=180, options=[ft.dropdown.Option(""), ft.dropdown.Option("open"), ft.dropdown.Option("assigned"), ft.dropdown.Option("escalated"), ft.dropdown.Option("resolved")], hint_text="Status", on_change=self._on_status_change),
                            ft.TextField(label="Reporter email", on_change=self._on_reporter_change),
                            ft.TextField(label="Start date (YYYY-MM-DD)", on_change=self._on_start_date_change),
                            ft.TextField(label="End date (YYYY-MM-DD)", on_change=self._on_end_date_change),
                            ft.ElevatedButton("Apply Filters", on_click=self._apply_filters),
                            ft.ElevatedButton("Clear Filters", on_click=self._clear_filters)
                        ], spacing=12),
                        ft.Divider(),
                        ft.Column(report_cards)
                    ])
                )
            ]
        )

    def _resolve_report(self, report_id: int):
        from services.report_service import ReportService
        ok = ReportService.update_report_status(report_id, 'resolved')
        if ok:
            snack = ft.SnackBar(ft.Text('Report marked resolved'))
            try:
                # Use page.open to show the snack in a consistent way
                self.page.open(snack)
            except Exception:
                try:
                    self.page.overlay.append(snack)
                    snack.open = True
                except Exception:
                    pass
            # Notify views to refresh
            try:
                from services.refresh_service import notify as _notify
                _notify()
            except Exception:
                pass
            self.page.update()
        else:
            snack = ft.SnackBar(ft.Text('Failed to update report'))
            try:
                self.page.open(snack)
            except Exception:
                try:
                    self.page.overlay.append(snack)
                    snack.open = True
                except Exception:
                    pass
            self.page.update()
            self.page.go('/admin_reports')

    def _on_status_change(self, e):
        try:
            self.status_filter = e.control.value
        except Exception:
            self.status_filter = None

    def _on_reporter_change(self, e):
        self.reporter_filter = e.control.value

    def _on_start_date_change(self, e):
        self.start_date = e.control.value

    def _on_end_date_change(self, e):
        self.end_date = e.control.value

    def _apply_filters(self, e):
        self.page.go('/admin_reports')
        try:
            notify_refresh()
        except Exception:
            pass

    def _clear_filters(self, e):
        self.status_filter = None
        self.reporter_filter = None
        self.start_date = None
        self.end_date = None
        try:
            notify_refresh()
        except Exception:
            pass

    def _on_global_refresh(self):
        # Rebuild view when global refresh is triggered
        try:
            self.page.update()
        except Exception:
            pass

    def _open_escalate_dialog(self, report_id: int):
        from components.dialog_helper import open_dialog, close_dialog

        d = ft.AlertDialog(
            title=ft.Text("Escalate Report"),
            content=ft.Column([
                ft.Text("Provide reason for escalation (optional):"),
                ft.TextField(key="escalate_reason", multiline=True)
            ]),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e, dlg=d: close_dialog(self.page, dlg)),
                ft.TextButton("Escalate", on_click=lambda e, dlg=d: (self._do_escalate(report_id, dlg), close_dialog(self.page, dlg)))
            ]
        )
        open_dialog(self.page, d)

    def _do_escalate(self, report_id: int, dialog):
        try:
            reason = dialog.content.controls[1].value if dialog and dialog.content and len(dialog.content.controls) > 1 else None
        except Exception:
            reason = None
        admin_id = self.session.get_user_id()
        ok = ReportService.escalate_report(report_id, reason, admin_id)
        if ok:
            ActivityService.log_activity(admin_id, "Escalated Report", f"Report {report_id} escalated. Reason: {reason or ''}")
            try:
                notify_refresh()
            except Exception:
                pass
            self._show_snack("Report escalated")
        else:
            self._show_snack("Failed to escalate report", error=True)

    def _assign_to_current_admin(self, report_id: int):
        admin_id = self.session.get_user_id()
        ok = ReportService.assign_report(report_id, admin_id, note="Assigned via UI")
        if ok:
            ActivityService.log_activity(admin_id, "Assigned Report", f"Assigned report {report_id} to admin {admin_id}")
            try:
                notify_refresh()
            except Exception:
                pass
            self._show_snack("Report assigned to you")
        else:
            self._show_snack("Failed to assign report", error=True)

    def _show_snack(self, message: str, error: bool = False):
        sb = ft.SnackBar(ft.Text(message), bgcolor="#F44336" if error else "#4CAF50")
        self.page.open(sb)
        self.page.update()
