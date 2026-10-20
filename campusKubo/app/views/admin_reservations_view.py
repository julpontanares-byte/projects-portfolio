# app/views/admin_reservations_view.py

import flet as ft
from services.reservation_service import ReservationService
from services.admin_service import AdminService
from components.navbar import DashboardNavBar
from components.admin_utils import format_id, format_name, format_datetime
from components.table_card import TableCard
from state.session_state import SessionState
from services.refresh_service import register as _register_refresh
from typing import Optional, Any
from models.reservation import Reservation

class AdminReservationsView:

    def __init__(self, page):
        self.page = page
        self.session = SessionState(page)
        self.reservation_service = ReservationService()
        self.admin_service = AdminService()
        # pagination state
        self.page_index = 0
        self.page_size = 8
        self.table_container = ft.Container()

        # Create/edit reservation form fields
        self.reservation_form_listing = ft.Dropdown(label="Listing", width=280)
        self.reservation_form_tenant = ft.Dropdown(label="Tenant", width=280)
        self.reservation_form_start_date = ft.TextField(label="Start Date (YYYY-MM-DD)", width=280)
        self.reservation_form_end_date = ft.TextField(label="End Date (YYYY-MM-DD)", width=280)
        self.reservation_form_status = ft.Dropdown(
            label="Status",
            options=[
                ft.dropdown.Option("Pending", "pending"),
                ft.dropdown.Option("Approved", "approved"),
                ft.dropdown.Option("Active", "active"),
                ft.dropdown.Option("Completed", "completed"),
                ft.dropdown.Option("Cancelled", "cancelled")
            ],
            value="pending",
            width=220
        )
        self._editing_reservation = None
        self.reservation_form_title = ft.Text("Add Reservation", size=18, weight=ft.FontWeight.BOLD)
        self.is_reservation_form_visible = False
        self.reservation_form_container = ft.Container(visible=False)

        try:
            _register_refresh(self._on_global_refresh)
        except Exception:
            pass

        self._build_reservation_form_container()

    def _on_global_refresh(self):
        try:
            self._render_table()
            self.page.update()
        except Exception:
            pass

    def build(self):
        if not self.session.require_auth(): return None
        if not self.session.is_admin(): self.page.go("/"); return None

        # initial render
        self._render_table()

        return ft.View(
            "/admin_reservations",
            scroll=ft.ScrollMode.AUTO,
            controls=[
                DashboardNavBar(self.page, "Reservation Oversight", self.session.get_email() or "").view(),
                ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Row(controls=[
                            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.page.go('/admin')),
                            ft.Text("All Reservations", size=26, weight= ft.FontWeight.BOLD)
                        ], alignment=ft.MainAxisAlignment.START),
                        ft.Row(
                            spacing=12,
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Container(expand=True),
                                ft.ElevatedButton(
                                    "Add Reservation",
                                    icon=ft.Icons.ADD,
                                    on_click=lambda e: self._show_reservation_form()
                                )
                            ]
                        ),
                        self.reservation_form_container,
                        ft.Divider(),
                        ft.Container(height=440, content=self.table_container),
                        ft.Divider(),
                        self._build_pagination()
                    ])
                )
            ]
        )

    def _confirm_reservation_action(self, reservation_id: int, new_status: str):
        """Show confirmation dialog before updating reservation status."""
        action_text = "approve" if new_status == 'approved' else "cancel"

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"{action_text.capitalize()} Reservation", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Text(
                    f"Are you sure you want to {action_text} this reservation?",
                    size=14
                ),
                width=400
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_confirmation_dialog(dlg)),
                ft.ElevatedButton(
                    action_text.capitalize(),
                    bgcolor=ft.Colors.GREEN if new_status == 'approved' else ft.Colors.ORANGE,
                    color=ft.Colors.WHITE,
                    on_click=lambda e, rid=reservation_id, status=new_status: self._perform_reservation_update(rid, status, dlg)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def _close_confirmation_dialog(self, dlg):
        """Close the confirmation dialog."""
        dlg.open = False
        self.page.update()

    def _perform_reservation_update(self, reservation_id: int, new_status: str, dlg: ft.AlertDialog):
        """Perform the actual update after confirmation."""
        self._close_confirmation_dialog(dlg)
        self._update_reservation(reservation_id, new_status)

    def _update_reservation(self, reservation_id: int, new_status: str):
        ok = self.reservation_service.update_reservation_status(reservation_id, new_status)
        if ok:
            self.page.open(ft.SnackBar(ft.Text(f"Reservation {new_status}")))
        else:
            self.page.open(ft.SnackBar(ft.Text("Failed to update reservation")))

        # Notify global refresh service
        try:
            from services.refresh_service import notify as _notify
            _notify()
        except Exception:
            pass

        # refresh current page
        self._render_table()
        self.page.update()

    def _render_table(self):
        reservations = self.reservation_service.get_all_reservations()

        # pagination slice: clamp the page_index to valid range to avoid empty pages
        total = len(reservations)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self.page_index >= total_pages:
            self.page_index = max(0, total_pages - 1)
        start = self.page_index * self.page_size
        end = start + self.page_size
        page_items = reservations[start:end]

        data_rows = []
        for r in page_items:
            rid = r.get('id') if isinstance(r, dict) else r['id']
            listing_id = r.get('listing_id') if isinstance(r, dict) else r['listing_id']
            tenant_id = r.get('tenant_id') if isinstance(r, dict) else r['tenant_id']
            start_date = r.get('start_date') if isinstance(r, dict) else r['start_date']
            end_date = r.get('end_date') if isinstance(r, dict) else r['end_date']
            status = r.get('status') if isinstance(r, dict) else r['status']

            rid_int = int(rid) if rid is not None else 0
            start_display = format_datetime(start_date) if start_date else "-"
            end_display = format_datetime(end_date) if end_date else "-"

            approve_btn = ft.ElevatedButton(
                "Approve",
                bgcolor=ft.Colors.GREEN,
                color=ft.Colors.WHITE,
                on_click=lambda e, _id=rid_int: self._confirm_reservation_action(_id, 'approved')
            )
            cancel_btn = ft.OutlinedButton(
                "Cancel",
                on_click=lambda e, _id=rid_int: self._confirm_reservation_action(_id, 'cancelled')
            )

            data_rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(format_id('R', rid_int))),
                    ft.DataCell(ft.Text(format_id('L', listing_id))),
                    ft.DataCell(ft.Text(format_id('U', tenant_id))),
                    ft.DataCell(ft.Text(start_display)),
                    ft.DataCell(ft.Text(end_display)),
                    ft.DataCell(ft.Text(str(status).title())),
                    ft.DataCell(ft.Row([
                        ft.IconButton(ft.Icons.EDIT, icon_size=18, on_click=lambda e, res=r: self._show_reservation_form(res)),
                        approve_btn,
                        cancel_btn
                    ], spacing=4))
                ])
            )

        if not page_items:
            self.table_container.content = ft.Container(
                content=ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Icon(ft.Icons.INBOX, size=48, color=ft.Colors.GREY),
                    ft.Text("No Data Yet", size=14, color=ft.Colors.GREY),
                    ft.Text("No reservations match the selected filters.", size=12, color=ft.Colors.GREY_600),
                ]),
                padding=ft.padding.symmetric(vertical=24, horizontal=8),
                alignment=ft.alignment.center,
                expand=True,
            )
            return

        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Listing ID")),
                ft.DataColumn(ft.Text("Tenant ID")),
                ft.DataColumn(ft.Text("Start")),
                ft.DataColumn(ft.Text("End")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=data_rows,
            column_spacing=14,
            expand=True,
            border=ft.border.all(1, "#E0E0E0"),
            heading_row_color="#F9F9F9",
            heading_row_height=48,
        )

        # Show the table directly for a minimal appearance (no TableCard)
        self.table_container.content = ft.Container(content=table, expand=True, padding=ft.padding.only(top=6, bottom=6))

    def _build_pagination(self):
        reservations = self.reservation_service.get_all_reservations()
        total_items = len(reservations)

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

    # ----------------------------------------------------
    # Inline reservation form methods
    # ----------------------------------------------------
    def _build_reservation_form_container(self):
        form_fields = ft.Column(
            [
                ft.Row([
                    self.reservation_form_listing,
                    self.reservation_form_tenant
                ], spacing=12, wrap=True),
                ft.Row([
                    self.reservation_form_start_date,
                    self.reservation_form_end_date,
                    self.reservation_form_status
                ], spacing=12, wrap=True),
            ],
            spacing=12,
            tight=True,
        )

        action_row = ft.Row(
            [
                ft.TextButton("Cancel", on_click=lambda e: self._hide_reservation_form()),
                ft.ElevatedButton(
                    "Save",
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                    on_click=lambda e: self._submit_reservation_form()
                )
            ],
            alignment=ft.MainAxisAlignment.END,
            spacing=10
        )

        self.reservation_form_container.content = ft.Container(
            bgcolor="#F5F7FB",
            border_radius=10,
            border=ft.border.all(1, "#E2E8F0"),
            padding=16,
            content=ft.Column([
                self.reservation_form_title,
                form_fields,
                action_row
            ], spacing=12),
        )

    def _reset_reservation_form_fields(self):
        self.reservation_form_listing.value = None
        self.reservation_form_tenant.value = None
        self.reservation_form_start_date.value = ""
        self.reservation_form_end_date.value = ""
        self.reservation_form_status.value = "pending"

    def _get_reservation_value(self, reservation: Optional[Any], key: str, default: Any = ""):
        if reservation is None:
            return default
        if isinstance(reservation, dict):
            return reservation.get(key, default)
        return getattr(reservation, key, default)

    def _populate_reservation_dropdowns(self):
        try:
            listings = self.admin_service.get_all_listings()
            listing_options = [ft.dropdown.Option(f"{getattr(lst, 'address', '')[:30]}", str(lst.id)) for lst in listings]
            self.reservation_form_listing.options = listing_options
        except Exception:
            self.reservation_form_listing.options = []

        try:
            tenants = self.admin_service.get_all_users_by_role('tenant')
            tenant_options = [ft.dropdown.Option(f"{getattr(t, 'full_name', '')} ({getattr(t, 'email', '')})", str(t.id)) for t in tenants]
            self.reservation_form_tenant.options = tenant_options
        except Exception:
            self.reservation_form_tenant.options = []

    def _show_reservation_form(self, reservation: Optional[Any] = None):
        self._editing_reservation = reservation
        self._populate_reservation_dropdowns()
        self._reset_reservation_form_fields()

        if reservation:
            self.reservation_form_title.value = "Edit Reservation"
            self.reservation_form_listing.value = str(self._get_reservation_value(reservation, 'listing_id', ""))
            self.reservation_form_tenant.value = str(self._get_reservation_value(reservation, 'tenant_id', ""))
            self.reservation_form_start_date.value = str(self._get_reservation_value(reservation, 'start_date', ""))
            self.reservation_form_end_date.value = str(self._get_reservation_value(reservation, 'end_date', ""))
            self.reservation_form_status.value = self._get_reservation_value(reservation, 'status', 'pending') or 'pending'
        else:
            self.reservation_form_title.value = "Add Reservation"

        self.is_reservation_form_visible = True
        self.reservation_form_container.visible = True
        self.page.update()

    def _hide_reservation_form(self):
        self._reset_reservation_form_fields()
        self._editing_reservation = None
        self.is_reservation_form_visible = False
        self.reservation_form_container.visible = False
        self.page.update()

    def _submit_reservation_form(self):
        """Validate and submit the reservation form."""
        # Validate required fields
        listing_id_str = self.reservation_form_listing.value
        tenant_id_str = self.reservation_form_tenant.value
        start_date = (self.reservation_form_start_date.value or "").strip()
        end_date = (self.reservation_form_end_date.value or "").strip()
        status = self.reservation_form_status.value or 'pending'

        # Validate listing
        if not listing_id_str:
            self.page.open(ft.SnackBar(ft.Text("Please select a listing")))
            return

        try:
            listing_id = int(listing_id_str)
        except (ValueError, TypeError):
            self.page.open(ft.SnackBar(ft.Text("Invalid listing")))
            return

        # Validate tenant
        if not tenant_id_str:
            self.page.open(ft.SnackBar(ft.Text("Please select a tenant")))
            return

        try:
            tenant_id = int(tenant_id_str)
        except (ValueError, TypeError):
            self.page.open(ft.SnackBar(ft.Text("Invalid tenant")))
            return

        # Validate dates
        if not start_date or not end_date:
            self.page.open(ft.SnackBar(ft.Text("Both start and end dates are required")))
            return

        # Basic date format validation (YYYY-MM-DD)
        import re
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(date_pattern, start_date) or not re.match(date_pattern, end_date):
            self.page.open(ft.SnackBar(ft.Text("Use date format: YYYY-MM-DD")))
            return

        # Call service
        if self._editing_reservation:
            # Update existing reservation
            success, message = self.admin_service.update_reservation_admin(
                reservation_id=self._editing_reservation.id,
                listing_id=listing_id,
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date,
                status=status
            )
        else:
            # Create new reservation
            success, message, res_id = self.admin_service.create_reservation_admin(
                listing_id=listing_id,
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date,
                status=status
            )

        # Show feedback
        self.page.open(ft.SnackBar(ft.Text(message)))

        # Close form and refresh if successful
        if success:
            # Notify global refresh service
            try:
                from services.refresh_service import notify as _notify
                _notify()
            except Exception:
                pass

            self._hide_reservation_form()
            self._render_table()
            self.page.update()

