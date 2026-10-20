import flet as ft
from typing import Optional
from services.admin_service import AdminService
from components.admin_utils import format_id, format_name, format_datetime
from components.navbar import DashboardNavBar
from components.table_card import TableCard
from state.session_state import SessionState
from services.refresh_service import register as _register_refresh


class AdminPaymentsView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.session = SessionState(page)
        self.admin_service = AdminService()
        self.page_index = 0
        self.page_size = 8
        self.table_container = ft.Container()
        self.stats_container = ft.Container()

        # Filter state
        self.status_filter = ft.Dropdown(
            label="Status Filter",
            options=[
                ft.dropdown.Option("All"),
                ft.dropdown.Option("Completed", "completed"),
                ft.dropdown.Option("Refunded", "refunded"),
                ft.dropdown.Option("Pending", "pending"),
                ft.dropdown.Option("Failed", "failed")
            ],
            value="All",
            on_change=self._on_filter_change
        )

        # Refund dialog state
        self._refund_dialog = None
        self._refunding_payment_id = None
        self.refund_amount_field = ft.TextField(label="Refund Amount (₱)", width=200)
        self.refund_reason_field = ft.TextField(label="Reason", width=350, min_lines=2, max_lines=4)

        try:
            _register_refresh(self._on_global_refresh)
        except Exception:
            pass

    def _on_global_refresh(self):
        try:
            self._render_table()
            self._render_statistics()
            self.page.update()
        except Exception:
            pass

    def _on_filter_change(self, e):
        """Handle status filter change."""
        self.page_index = 0
        self._render_table()
        self.page.update()

    def build(self):
        if not self.session.require_auth():
            return None
        if not self.session.is_admin():
            self.page.go("/")
            return None

        # initial render
        self._render_table()
        self._render_statistics()

        navbar = DashboardNavBar(self.page, "Payments", self.session.get_email() or "").view()

        return ft.View(
            "/admin_payments",
            scroll=ft.ScrollMode.AUTO,
            controls=[
                navbar,
                ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Row(controls=[
                            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.page.go('/admin')),
                            ft.Text("Payments Management", size=26, weight=ft.FontWeight.BOLD)
                        ], alignment=ft.MainAxisAlignment.START),
                        ft.Divider(),

                        # Statistics section
                        ft.ExpansionTile(
                            title=ft.Text("Payment Statistics", weight=ft.FontWeight.BOLD),
                            controls=[
                                ft.Container(
                                    height=200,
                                    content=self.stats_container,
                                    expand=True
                                )
                            ]
                        ),

                        ft.Divider(),

                        # Filter row
                        ft.Row(
                            controls=[
                                self.status_filter,
                                ft.Container(expand=True)
                            ],
                            spacing=10
                        ),

                        # Table
                        ft.Container(height=440, content=self.table_container),
                        ft.Divider(),
                        self._build_pagination()
                    ])
                )
            ]
        )

    def _render_statistics(self):
        """Render payment statistics."""
        try:
            stats = self.admin_service.get_payment_statistics()

            stat_cards = ft.Row(
                spacing=15,
                wrap=True,
                controls=[
                    self._build_stat_card(
                        "Total Revenue",
                        f"₱{stats.get('total_revenue', 0):,.2f}",
                        ft.Icons.ATTACH_MONEY,
                        ft.Colors.GREEN
                    ),
                    self._build_stat_card(
                        "Total Refunds",
                        f"₱{stats.get('total_refunds', 0):,.2f}",
                        ft.Icons.UNDO,
                        ft.Colors.ORANGE
                    ),
                    self._build_stat_card(
                        "Net Revenue",
                        f"₱{stats.get('net_revenue', 0):,.2f}",
                        ft.Icons.TRENDING_UP,
                        ft.Colors.BLUE
                    ),
                    self._build_stat_card(
                        "Transactions",
                        str(stats.get('total_transactions', 0)),
                        ft.Icons.RECEIPT,
                        ft.Colors.PURPLE
                    ),
                    self._build_stat_card(
                        "Avg Transaction",
                        f"₱{stats.get('avg_transaction', 0):,.2f}",
                        ft.Icons.SHOW_CHART,
                        ft.Colors.INDIGO
                    ),
                ]
            )

            self.stats_container.content = stat_cards
        except Exception as e:
            print(f"[AdminPaymentsView] Error rendering statistics: {e}")
            self.stats_container.content = ft.Text(f"Error loading statistics: {str(e)}", color=ft.Colors.RED)

    def _build_stat_card(self, title: str, value: str, icon, color) -> ft.Container:
        """Build a statistics card."""
        return ft.Container(
            width=150,
            padding=12,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, color),
            content=ft.Column(
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, size=28, color=color),
                    ft.Text(value, size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(title, size=11, color=ft.Colors.GREY)
                ]
            )
        )

    def _render_table(self):
        """Render payment table with refund actions."""
        # Get status filter value
        status_filter = None if self.status_filter.value == "All" else self.status_filter.value

        # Fetch payments
        payments = self.admin_service.get_all_payments_admin(status_filter)

        total = len(payments)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self.page_index >= total_pages:
            self.page_index = max(0, total_pages - 1)
        start = self.page_index * self.page_size
        end = start + self.page_size
        page_items = payments[start:end]

        rows = []
        for p in page_items:
            pid_raw = p.get('id')
            try:
                pid = int(pid_raw) if pid_raw is not None else 0
            except (TypeError, ValueError):
                pid = 0

            user_email = p.get('user_email') or '—'
            listing_addr = p.get('listing_address') or '—'
            amount_raw = p.get('amount') or 0
            refunded_raw = p.get('refunded_amount') or 0
            status = p.get('status') or 'unknown'
            payment_method = p.get('payment_method') or '—'

            try:
                amount_val = float(amount_raw)
                refunded_val = float(refunded_raw)
            except Exception:
                print(f"[admin_payments_view] Non-numeric amount for payment id={pid_raw}: {amount_raw}")
                amount_val = 0.0
                refunded_val = 0.0

            # Status color
            status_color = ft.Colors.GREEN if status == 'completed' else (
                ft.Colors.ORANGE if status == 'pending' else (
                ft.Colors.RED if status == 'failed' else ft.Colors.GREY
            ))

            # Refund button (only for completed/refunded payments)
            refund_btn = None
            if status in ['completed', 'refunded'] and amount_val > refunded_val:
                refund_btn = ft.ElevatedButton(
                    "Refund",
                    width=70,
                    height=36,
                    bgcolor=ft.Colors.ORANGE,
                    color=ft.Colors.WHITE,
                    on_click=lambda e, payment_id=pid: self._open_refund_dialog(payment_id)
                )

            # Action buttons
            actions = []
            if refund_btn:
                actions.append(refund_btn)

            actions.append(
                ft.IconButton(
                    ft.Icons.INFO,
                    icon_size=18,
                    tooltip="Payment details",
                    on_click=lambda e, payment_id=pid: self._show_payment_details(payment_id, p)
                )
            )

            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(format_id('PMT', pid))),
                ft.DataCell(ft.Text(user_email, size=11)),
                ft.DataCell(ft.Text(format_name(listing_addr), size=11)),
                ft.DataCell(ft.Text(f"₱{amount_val:,.2f}", size=11)),
                ft.DataCell(ft.Text(f"₱{refunded_val:,.2f}", color=ft.Colors.ORANGE if refunded_val > 0 else ft.Colors.GREY, size=11)),
                ft.DataCell(ft.Chip(label=ft.Text(status, size=10), color=status_color)),
                ft.DataCell(ft.Text(payment_method, size=10)),
                ft.DataCell(ft.Text(format_datetime(p.get('created_at')), size=10)),
                ft.DataCell(ft.Row(actions, spacing=4)) if actions else ft.DataCell(ft.Text("—"))
            ]))

        if not page_items:
            self.table_container.content = ft.Container(
                content=ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Icon(ft.Icons.INBOX, size=48, color=ft.Colors.GREY),
                    ft.Text("No Data Yet", size=14, color=ft.Colors.GREY),
                    ft.Text("No payments available.", size=12, color=ft.Colors.GREY_600),
                ]),
                padding=ft.padding.symmetric(vertical=24, horizontal=8),
                alignment=ft.alignment.center,
                expand=True,
            )
            return

        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("User")),
                ft.DataColumn(ft.Text("Listing")),
                ft.DataColumn(ft.Text("Amount")),
                ft.DataColumn(ft.Text("Refunded")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Method")),
                ft.DataColumn(ft.Text("Date")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=rows,
            column_spacing=12,
            expand=True,
            border=ft.border.all(1, "#E0E0E0"),
            heading_row_color="#F9F9F9",
            heading_row_height=48,
        )

        self.table_container.content = ft.Container(content=table, expand=True, padding=ft.padding.only(top=6, bottom=6))

    def _open_refund_dialog(self, payment_id: int):
        """Open refund dialog for a payment."""
        self._refunding_payment_id = payment_id
        self.refund_amount_field.value = ""
        self.refund_reason_field.value = ""

        self._refund_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Process Refund", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=450,
                content=ft.Column([
                    ft.Text(f"Payment ID: {format_id('PMT', payment_id)}", weight=ft.FontWeight.BOLD, size=14),
                    ft.Divider(height=1, color=ft.Colors.GREY_400),
                    ft.Container(height=10),
                    self.refund_amount_field,
                    self.refund_reason_field,
                ], spacing=10, tight=True)
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_refund_dialog()),
                ft.ElevatedButton(
                    "Process Refund",
                    bgcolor=ft.Colors.ORANGE,
                    color=ft.Colors.WHITE,
                    on_click=lambda e: self._confirm_refund()
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.dialog = self._refund_dialog
        self._refund_dialog.open = True
        self.page.update()

    def _close_refund_dialog(self):
        """Close refund dialog."""
        if self._refund_dialog:
            self._refund_dialog.open = False
            self._refund_dialog = None
        self._refunding_payment_id = None
        self.page.update()

    def _confirm_refund(self):
        """Validate inputs and show confirmation before processing refund."""
        if not self._refunding_payment_id:
            return

        # Validate amount
        try:
            refund_amount = float(self.refund_amount_field.value)
            if refund_amount <= 0:
                self.page.open(ft.SnackBar(ft.Text("Refund amount must be greater than 0")))
                return
        except (ValueError, TypeError):
            self.page.open(ft.SnackBar(ft.Text("Enter a valid refund amount")))
            return

        # Validate reason
        reason = self.refund_reason_field.value.strip()
        if not reason:
            self.page.open(ft.SnackBar(ft.Text("Please provide a refund reason")))
            return

        # Show confirmation dialog
        confirm_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Refund", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Amount: ₱{refund_amount:,.2f}", size=14),
                    ft.Text(f"Reason: {reason}", size=14),
                    ft.Container(height=10),
                    ft.Text("Are you sure you want to process this refund?", size=14, weight=ft.FontWeight.W_500)
                ], tight=True, spacing=5),
                width=400
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_confirm_dialog(confirm_dlg)),
                ft.ElevatedButton(
                    "Process Refund",
                    bgcolor=ft.Colors.ORANGE,
                    color=ft.Colors.WHITE,
                    on_click=lambda e: self._submit_refund(confirm_dlg, refund_amount, reason)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.dialog = confirm_dlg
        confirm_dlg.open = True
        self.page.update()

    def _close_confirm_dialog(self, dlg):
        """Close confirmation dialog and return to refund dialog."""
        dlg.open = False
        self.page.dialog = self._refund_dialog
        self.page.update()

    def _submit_refund(self, confirm_dlg, refund_amount, reason):
        """Submit refund request after confirmation."""
        # Close confirmation dialog
        confirm_dlg.open = False
        self.page.update()

        # Process refund
        success, message = self.admin_service.process_refund(
            self._refunding_payment_id,
            refund_amount,
            reason
        )

        self.page.open(ft.SnackBar(ft.Text(message)))

        if success:
            # Notify global refresh service
            try:
                from services.refresh_service import notify as _notify
                _notify()
            except Exception:
                pass

            self._close_refund_dialog()
            self._render_table()
            self._render_statistics()
            self.page.update()

    def _show_payment_details(self, payment_id: int, payment: dict):
        """Show detailed payment information."""
        detail_rows = [
            ft.Row([
                ft.Text("User:", weight=ft.FontWeight.BOLD, width=100),
                ft.Text(payment.get('user_email', '—'))
            ]),
            ft.Row([
                ft.Text("Listing:", weight=ft.FontWeight.BOLD, width=100),
                ft.Text(payment.get('listing_address', '—'))
            ]),
            ft.Row([
                ft.Text("Amount:", weight=ft.FontWeight.BOLD, width=100),
                ft.Text(f"₱{float(payment.get('amount', 0)):,.2f}")
            ]),
            ft.Row([
                ft.Text("Refunded:", weight=ft.FontWeight.BOLD, width=100),
                ft.Text(f"₱{float(payment.get('refunded_amount', 0)):,.2f}", color=ft.Colors.ORANGE)
            ]),
            ft.Row([
                ft.Text("Status:", weight=ft.FontWeight.BOLD, width=100),
                ft.Text(payment.get('status', '—').title())
            ]),
            ft.Row([
                ft.Text("Method:", weight=ft.FontWeight.BOLD, width=100),
                ft.Text(payment.get('payment_method', '—'))
            ]),
            ft.Row([
                ft.Text("Date:", weight=ft.FontWeight.BOLD, width=100),
                ft.Text(format_datetime(payment.get('created_at', '')))
            ]),
        ]

        if payment.get('refund_reason'):
            detail_rows.append(
                ft.Row([
                    ft.Text("Refund Reason:", weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(payment.get('refund_reason', '—'))
                ])
            )

        if payment.get('notes'):
            detail_rows.append(
                ft.Row([
                    ft.Text("Notes:", weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(payment.get('notes', '—'))
                ])
            )

        details = ft.AlertDialog(
            title=ft.Text(f"Payment Details - {format_id('PMT', payment_id)}"),
            content=ft.Container(
                width=500,
                content=ft.Column(detail_rows, spacing=10)
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self._close_details_dialog(details))
            ]
        )

        self.page.dialog = details
        details.open = True
        self.page.update()

    def _close_details_dialog(self, dialog):
        """Close details dialog."""
        dialog.open = False
        self.page.update()

    def _build_pagination(self):
        # Get current status filter
        status_filter = None if self.status_filter.value == "All" else self.status_filter.value
        payments = self.admin_service.get_all_payments_admin(status_filter)

        total_items = len(payments)
        total_pages = max(1, (total_items + self.page_size - 1) // self.page_size)
        prev_disabled = self.page_index <= 0
        next_disabled = (self.page_index + 1) * self.page_size >= max(1, total_items)

        return ft.Row(controls=[
            ft.ElevatedButton("Prev", disabled=prev_disabled, on_click=lambda e: self._change_page(-1)),
            ft.Text(f"Page {self.page_index + 1} of {total_pages}"),
            ft.ElevatedButton("Next", disabled=next_disabled, on_click=lambda e: self._change_page(1)),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=12)

    def _change_page(self, delta: int):
        self.page_index = max(0, self.page_index + delta)
        self._render_table()
        self.page.update()
