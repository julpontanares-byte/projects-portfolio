# app/views/admin_dashboard_view.py
"""
Admin Dashboard - Main View
Includes: Header, KPI Cards, Charts, Map Section
"""

import flet as ft
import os
import sys

# Ensure top-level project packages (e.g., `components`, `services`) are importable
# when this module is executed directly (not via the package). This mirrors other
# service modules' approach to robust imports.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components.admin_stats_card import AdminStatsCard
from components.chart_card import ChartCard
from components.navbar import DashboardNavBar
from components.footer import Footer
from services.admin_service import AdminService
from services.listing_service import ListingService
from services.reservation_service import ReservationService
from services.activity_service import ActivityService
from state.session_state import SessionState
from models.user import UserRole

# Import admin subviews
from .admin_users_view import AdminUsersView
from .admin_pm_verification_view import AdminPMVerificationView
from .admin_listings_view import AdminListingsView
from .admin_reservations_view import AdminReservationsView
from .admin_payments_view import AdminPaymentsView
from .admin_reports_view import AdminReportsView
from .admin_profile_view import AdminProfileView
import datetime
import re
import calendar

def _short_label(s: str) -> str:
    """Return a shortened label for chart axes (e.g., month names -> 'Jan').

    Falls back to a truncated version if unknown.
    """
    try:
        if not s:
            return ""
        s = str(s).strip()
        # Map common month names to 3-letter abbreviations
        m = s.lower()
        months = {name.lower(): abbr for name, abbr in zip(calendar.month_name[1:], calendar.month_abbr[1:])}
        if m in months:
            return months[m]
        # If it's already short enough, return it
        if len(s) <= 4:
            return s
        # Otherwise take the first 3 letters
        return s[:3]
    except Exception:
        return str(s)[:3] if s else ""


def _make_left_axis(max_y: int) -> ft.ChartAxis:
    """Create a left chart axis with a few evenly spaced labels up to max_y."""
    try:
        import math

        max_y = int(max(1, max_y))
        steps = 4
        interval = max(1, math.ceil(max_y / steps))
        labels = []
        v = 0
        while v <= max_y:
            labels.append(ft.ChartAxisLabel(value=v, label=ft.Text(str(v))))
            v += interval

        # Ensure the top label equals max_y
        if labels and int(labels[-1].value) != max_y:
            labels.append(ft.ChartAxisLabel(value=max_y, label=ft.Text(str(max_y))))

        return ft.ChartAxis(labels=labels, labels_size=40)
    except Exception:
        return ft.ChartAxis(labels=[ft.ChartAxisLabel(value=0, label=ft.Text("0")), ft.ChartAxisLabel(value=1, label=ft.Text("1"))], labels_size=40)


class AdminDashboardView:
    """Admin dashboard view with KPI cards, charts, and map"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.session = SessionState(page)
        self.admin_service = AdminService()
        self.listing_service = ListingService()
        self.reservation_service = ReservationService()
        self.activity_service = ActivityService()

        # Register for global refresh events
        try:
            from services.refresh_service import register as _register_refresh
            _register_refresh(self._on_global_refresh)
        except Exception:
            pass

    def _on_global_refresh(self):
        """Handle global refresh event - rebuild the view"""
        try:
            # Re-render would require calling build() again
            # For now, just trigger a navigation refresh if on dashboard
            if hasattr(self.page, 'route') and self.page.route == '/admin':
                self.page.go('/admin')
        except Exception:
            pass

    def build(self):
        print("AdminDashboardView.build() called")
        print(f"Session data: logged_in={self.page.session.get('is_logged_in')}, role={self.page.session.get('role')}, email={self.page.session.get('email')}")

        # --- AUTH ---
        if not self.session.require_auth():
            print("Auth check failed - redirecting to login")
            return None
        if not self.session.is_admin():
            print(f"Not admin - user role is: {self.page.session.get('role')}")
            self.page.go("/")
            return None

        print("Auth passed - building admin dashboard")

        # --- FETCH ANALYTICS ---
        stats = self.admin_service.get_stats()
        total_tenants = stats.get('total_tenants', 0) or 0
        total_pms = stats.get('total_pms', 0) or 0
        # include admins in total users
        admins = int(stats.get('total_admins', 0) or 0)
        # Use canonical total_users from the DB counts to avoid classification mismatch
        total_users = int(stats.get('total_users', total_tenants + total_pms + admins) or 0)
        pending_pms = self.admin_service.get_pending_pm_count()
        total_listings = stats.get('total_listings', 0) or 0
        approved_listings = stats.get('approved_listings', 0) or 0
        pending_listings = stats.get('pending_listings', 0) or 0
        total_reservations = stats.get('total_reservations', 0) or 0
        total_reports = stats.get('total_reports', 0) or 0
        total_payments = stats.get('total_payments', 0) or 0

        # Ensure variables used by charts are defined
        tenants = int(total_tenants or 0)
        pms = int(total_pms or 0)
        admins = int(stats.get('total_admins', 0) or 0)

        # --- NAVBAR + FOOTER ---
        navbar = DashboardNavBar(
            page=self.page,
            title="Admin Dashboard",
            user_email=self.session.get_email() or "Admin",
            show_add_button=False,
            on_logout=lambda _: self._logout()
        ).view()

        footer = Footer().view()

        # --- CLICK HANDLERS FOR KPI CARDS ---
        def go_users(e=None):
            self.page.go("/admin_users")

        def go_listings(e=None):
            self.page.go("/admin_listings")

        def go_reservations(e=None):
            self.page.go("/admin_reservations")

        def go_pm_verification(e=None):
            self.page.go("/admin_pm_verification")

        def go_reports(e=None):
            self.page.go("/admin_reports")

        def go_payments(e=None):
            self.page.go("/admin_payments")

        # =====================================================
        # 1. HEADER SECTION
        # =====================================================
        header_section = ft.Container(
            content=ft.Column(
                spacing=5,
                controls=[
                    ft.Text("Overview", size=28, weight=ft.FontWeight.BOLD, color="#1a1a2e"),
                    ft.Text("Summary of platform activity", size=14, color=ft.Colors.BLACK),
                ]
            )
        )

        # =====================================================
        # 2. KPI CLICKABLE CARDS SECTION
        # =====================================================
        card_width = 220
        card_spacing = 16
        container_padding = 16

        kpi_controls = [
            # Total Users: compare new users in last 30 days vs previous 30 days
            AdminStatsCard(
                title="Total Users",
                value=total_users,
                icon=ft.Icon(ft.Icons.PERSON, size=24, color="#2196F3"),
                trend_value=(lambda: (lambda v: v[0])(self.admin_service.compute_trend(
                    self.admin_service.get_new_users_count(days=30, offset_days=0),
                    self.admin_service.get_new_users_count(days=30, offset_days=30)
                )))(),
                trend_up=(lambda: (lambda v: v[1])(self.admin_service.compute_trend(
                    self.admin_service.get_new_users_count(days=30, offset_days=0),
                    self.admin_service.get_new_users_count(days=30, offset_days=30)
                )))(),
                color="#2196F3",
                on_click=go_users
            ).build(),

            # Active Listings: compare new approved listings
            AdminStatsCard(
                title="Active Listings",
                value=approved_listings,
                icon=ft.Icon(ft.Icons.HOME_WORK, size=24, color="#4CAF50"),
                trend_value=(lambda: (lambda v: v[0])(self.admin_service.compute_trend(
                    self.admin_service.get_new_listings_count(days=30, offset_days=0, status='approved'),
                    self.admin_service.get_new_listings_count(days=30, offset_days=30, status='approved')
                )))(),
                trend_up=(lambda: (lambda v: v[1])(self.admin_service.compute_trend(
                    self.admin_service.get_new_listings_count(days=30, offset_days=0, status='approved'),
                    self.admin_service.get_new_listings_count(days=30, offset_days=30, status='approved')
                )))(),
                color="#4CAF50",
                on_click=go_listings
            ).build(),

            # Reservations: compare new reservations
            AdminStatsCard(
                title="Reservations",
                value=total_reservations,
                icon=ft.Icon(ft.Icons.BOOKMARK, size=24, color="#FF9800"),
                trend_value=(lambda: (lambda v: v[0])(self.admin_service.compute_trend(
                    self.admin_service.get_new_reservations_count(days=30, offset_days=0),
                    self.admin_service.get_new_reservations_count(days=30, offset_days=30)
                )))(),
                trend_up=(lambda: (lambda v: v[1])(self.admin_service.compute_trend(
                    self.admin_service.get_new_reservations_count(days=30, offset_days=0),
                    self.admin_service.get_new_reservations_count(days=30, offset_days=30)
                )))(),
                color="#FF9800",
                on_click=go_reservations
            ).build(),

            # Pending PMs: compare pending PM registrations
            AdminStatsCard(
                title="Pending PMs",
                value=pending_pms,
                icon=ft.Icon(ft.Icons.VERIFIED_USER, size=24, color="#9C27B0"),
                trend_value=(lambda: (lambda v: v[0])(self.admin_service.compute_trend(
                    self.admin_service.get_pending_pms_count_period(days=30, offset_days=0),
                    self.admin_service.get_pending_pms_count_period(days=30, offset_days=30)
                )))(),
                trend_up=(lambda: (lambda v: v[1])(self.admin_service.compute_trend(
                    self.admin_service.get_pending_pms_count_period(days=30, offset_days=0),
                    self.admin_service.get_pending_pms_count_period(days=30, offset_days=30)
                )))(),
                color="#9C27B0",
                on_click=go_pm_verification
            ).build(),

            # Reports: compare new reports
            AdminStatsCard(
                title="Reports",
                value=total_reports,
                icon=ft.Icon(ft.Icons.REPORT, size=24, color="#F44336"),
                trend_value=(lambda: (lambda v: v[0])(self.admin_service.compute_trend(
                    self.admin_service.get_new_reports_count(days=30, offset_days=0),
                    self.admin_service.get_new_reports_count(days=30, offset_days=30)
                )))(),
                trend_up=(lambda: (lambda v: v[1])(self.admin_service.compute_trend(
                    self.admin_service.get_new_reports_count(days=30, offset_days=0),
                    self.admin_service.get_new_reports_count(days=30, offset_days=30)
                )))(),
                color="#F44336",
                on_click=go_reports
            ).build(),
        ]

        num_cards = len(kpi_controls)
        kpi_track_width = (num_cards * card_width) + ((num_cards - 1) * card_spacing) + (container_padding * 2)

        kpi_cards = ft.Row(
            wrap=False,
            spacing=card_spacing,
            width=kpi_track_width,
            controls=kpi_controls,
        )

        kpi_scroller = ft.Row(
            controls=[
                ft.Container(
                    width=kpi_track_width,
                    padding=ft.padding.symmetric(horizontal=container_padding),
                    content=kpi_cards,
                    alignment=ft.alignment.center_left,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            vertical_alignment=ft.CrossAxisAlignment.START,
            expand=True,
        )

        kpi_section = ft.Container(
            alignment=ft.alignment.center,
            content=kpi_scroller,
            expand=True,
        )

        # =====================================================
        # 3. CHARTS SECTION
        # =====================================================
        # --- User Distribution Pie Chart ---
        pie_sections = [
            ft.PieChartSection(
                value=tenants if tenants > 0 else 0.1,
                color="#4CAF50",
                title="",
                radius=120,
            ),
            ft.PieChartSection(
                value=pms if pms > 0 else 0.1,
                color="#FF9800",
                title="",
                radius=100,
            ),
            ft.PieChartSection(
                value=admins if admins > 0 else 0.1,
                color="#2196F3",
                title="",
                radius=100,
            ),
        ]

        chart_height = 420
        pie_height = max(180, chart_height - 80)

        user_pie_chart = ft.PieChart(
            sections=pie_sections,
            sections_space=6,
            center_space_radius=0,
            height=pie_height,
            expand=True,
        )

        pie_legend = ft.Container(
            margin=ft.margin.only(top=6, bottom=6),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=15,
                controls=[
                    ft.Row([ft.Container(width=12, height=12, bgcolor="#4CAF50", border_radius=2), ft.Text("Tenants", size=11)]),
                    ft.Row([ft.Container(width=12, height=12, bgcolor="#FF9800", border_radius=2), ft.Text("PMs", size=11)]),
                    ft.Row([ft.Container(width=12, height=12, bgcolor="#2196F3", border_radius=2), ft.Text("Admins", size=11)]),
                ]
            ),
        )

        user_distribution_card = ChartCard(
            title="User Distribution",
            subtitle="Breakdown by user role",
            chart=user_pie_chart,
            footer=pie_legend,
            padding=12,
            width=520,
            height=chart_height,
        ).build()

        # --- Chart 2: Reservation Trend Line Chart (FIXED) ---
        res_monthly = self.reservation_service.get_reservations_per_month() or []
        if not res_monthly:
            res_monthly = [("Jan", 5), ("Feb", 8), ("Mar", 12), ("Apr", 10), ("May", 15), ("Jun", 18)]

        data_points = []
        res_labels = []
        for i, (label, value) in enumerate(res_monthly, start=1):
            lbl = _short_label(label)
            res_labels.append((i, lbl))
            data_points.append(ft.LineChartDataPoint(x=i, y=value or 0, tooltip=str(value or 0)))

        # FIX: Increase labels_size to give more room for x-axis labels
        res_bottom_axis = ft.ChartAxis(
            labels=[ft.ChartAxisLabel(value=i, label=ft.Container(ft.Text(lbl, size=10), margin=ft.margin.only(top=4))) for i, lbl in res_labels],
            labels_size=35,  # Increased from 9 to 35 to show labels
        )

        res_max = max([int(v or 0) for _, v in res_monthly]) if res_monthly else 1
        res_max_y = max(int(res_max * 1.25), 1)

        # FIX: Adjusted chart height to accommodate labels better
        res_chart_height = max(220, chart_height - 180)

        reservation_line_chart = ft.LineChart(
            data_series=[
                ft.LineChartData(
                    data_points=data_points,
                    curved=True,
                    color="#2196F3",
                    stroke_width=3,
                    point=True,
                    stroke_cap_round=True,
                    below_line_gradient=ft.LinearGradient(
                        begin=ft.alignment.top_center,
                        end=ft.alignment.bottom_center,
                        colors=["#2196F340", "#2196F305"],
                    ),
                )
            ],
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)),
            horizontal_grid_lines=ft.ChartGridLines(interval=1, color=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE), width=1),
            left_axis=_make_left_axis(res_max_y),
            bottom_axis=res_bottom_axis,
            height=res_chart_height,
            tooltip_bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.BLUE_GREY),
            min_y=0,
            max_y=res_max_y,
            min_x=0,
            max_x=max(1, len(res_monthly)),
            expand=True,
        )

        reservation_trend_card = ChartCard(
            title="Reservation Trend",
            subtitle="Monthly bookings",
            chart=reservation_line_chart,
            icon=ft.Icon(ft.Icons.SHOW_CHART, size=20, color=ft.Colors.BLACK),
            footer=ft.Row(
                alignment=ft.MainAxisAlignment.END,
                spacing=8,
                controls=[
                    ft.Container(
                        bgcolor="#E3F2FD",
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        border_radius=15,
                        content=ft.Text("Monthly", size=11, color="#1976D2"),
                    )
                ]
            ),
            height=chart_height - 40,
        ).build()

        # =====================================================
        # 5. RECENT ACTIVITY SECTION (FIXED - Made scrollable)
        # =====================================================
        recent_activity = self.activity_service.get_recent_activities(limit=8)

        def _log_text(log):
            try:
                msg = None
                if isinstance(log, dict):
                    msg = log.get('message') or log.get('details') or log.get('action')
                else:
                    for key in ('message', 'details', 'action'):
                        try:
                            v = log[key]
                            if v:
                                msg = v
                                break
                        except Exception:
                            continue
                return str(msg) if msg else ""
            except Exception:
                return str(log) if log else ""

        def _activity_click_handler(msg):
            m = (msg or "").lower()
            if "report" in m:
                route = "/admin_reports"
            elif "pm" in m or "property manager" in m or "pending" in m:
                route = "/admin_pm_verification"
            elif "listing" in m:
                route = "/admin_listings"
            elif "reservation" in m:
                route = "/admin_reservations"
            else:
                # Default to the dedicated Activity Logs view so activity lines
                # navigate to the full logs listing rather than the users list.
                route = "/admin_activity_logs"
            return lambda _: self.page.go(route)

        def _get_activity_icon(msg):
            m = (msg or "").lower()
            if "report" in m:
                return ft.Icons.REPORT, "#F44336"
            elif "pm" in m or "property manager" in m:
                return ft.Icons.VERIFIED_USER, "#9C27B0"
            elif "listing" in m:
                return ft.Icons.HOME_WORK, "#4CAF50"
            elif "reservation" in m:
                return ft.Icons.BOOKMARK, "#FF9800"
            elif "user" in m or "register" in m:
                return ft.Icons.PERSON_ADD, "#2196F3"
            else:
                return ft.Icons.NOTIFICATIONS, "#607D8B"

        activity_controls = []
        for log in recent_activity:
            txt = _log_text(log)
            if not txt:
                continue
            handler = _activity_click_handler(txt)
            icon, color = _get_activity_icon(txt)

            activity_controls.append(
                ft.Container(
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Container(
                                width=32,
                                height=32,
                                bgcolor=f"{color}15",
                                border_radius=16,
                                alignment=ft.alignment.center,
                                content=ft.Icon(icon, size=16, color=color),
                            ),
                            ft.Text(txt, size=13, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, size=16, color=ft.Colors.BLACK),
                        ]
                    ),
                    padding=ft.padding.symmetric(vertical=8, horizontal=12),
                    border_radius=8,
                    on_click=handler,
                )
            )

        if not activity_controls:
            activity_controls.append(
                ft.Container(
                    padding=30,
                    alignment=ft.alignment.center,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Icon(ft.Icons.HISTORY, size=40, color=ft.Colors.BLACK),
                            ft.Text("No recent activity", size=14, color=ft.Colors.BLACK),
                        ]
                    )
                )
            )

        # FIX: Make the activity list scrollable
        activity_section = ft.Container(
            bgcolor="white",
            padding=20,
            border_radius=12,
            height=chart_height,
            shadow=ft.BoxShadow(blur_radius=15, spread_radius=1, color="#00000010"),
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Recent Activity", size=18, weight=ft.FontWeight.BOLD),
                            ft.TextButton("View All", on_click=lambda _: self.page.go("/admin_activity_logs")),
                        ]
                    ),
                    ft.Divider(height=1, color="#E0E0E0"),
                    # FIX: Wrap activity list in scrollable column with fixed height
                    ft.Container(
                        height=chart_height - 120,  # Reserve space for header and divider
                        content=ft.Column(
                            spacing=5,
                            controls=activity_controls,
                            scroll=ft.ScrollMode.AUTO,  # Enable scrolling
                        )
                    ),
                ]
            )
        )

        charts_row = ft.Row(
            wrap=False,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=20,
            controls=[
                ft.Container(
                    content=user_distribution_card,
                    alignment=ft.alignment.center,
                    width=pie_height,
                ),
                ft.Container(expand=True, content=activity_section),
            ]
        )

        # =====================================================
        # 4. MAP SECTION - Lodging Hotspots (FIXED)
        # =====================================================
        sample_locations = [
            {"name": "Manila", "x": 45, "y": 55, "count": 12, "status": "active"},
            {"name": "Quezon City", "x": 48, "y": 50, "count": 8, "status": "active"},
            {"name": "Makati", "x": 46, "y": 58, "count": 15, "status": "active"},
            {"name": "Pasig", "x": 50, "y": 54, "count": 6, "status": "pending"},
            {"name": "Taguig", "x": 48, "y": 60, "count": 10, "status": "active"},
            {"name": "Cebu", "x": 65, "y": 65, "count": 5, "status": "active"},
        ]

        def get_marker_color(status):
            if status == "active":
                return "#2196F3"
            elif status == "pending":
                return "#FF9800"
            else:
                return "#9E9E9E"

        map_markers = []
        for loc in sample_locations:
            color = get_marker_color(loc["status"])
            size = min(40, 15 + loc["count"] * 2)
            map_markers.append(
                ft.Container(
                    left=loc["x"] * 5,
                    top=loc["y"] * 3,
                    width=size,
                    height=size,
                    bgcolor=color,
                    border_radius=size/2,
                    border=ft.border.all(2, "white"),
                    shadow=ft.BoxShadow(blur_radius=5, color="#00000030"),
                    alignment=ft.alignment.center,
                    tooltip=f"{loc['name']}: {loc['count']} listings",
                    content=ft.Text(str(loc["count"]), size=10, color="white", weight=ft.FontWeight.BOLD),
                )
            )

        map_legend = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            spacing=20,
            controls=[
                ft.Row([ft.Container(width=14, height=14, bgcolor="#2196F3", border_radius=7, border=ft.border.all(1, "white")), ft.Text("Active", size=12)]),
                ft.Row([ft.Container(width=14, height=14, bgcolor="#FF9800", border_radius=7, border=ft.border.all(1, "white")), ft.Text("Pending", size=12)]),
                ft.Row([ft.Container(width=14, height=14, bgcolor="#9E9E9E", border_radius=7, border=ft.border.all(1, "white")), ft.Text("Archived", size=12)]),
            ]
        )

        # Modal opener for enlarged map view
        def _open_map_modal(e=None):
            # Build a larger map container reusing the same markers and legend
            # Build a fresh set of marker controls for the modal instead of
            # reusing `map_markers` which are already attached to the dashboard
            # view's Stack. Reusing controls across parents causes Flet to crash.
            modal_markers = []
            try:
                for loc in sample_locations:
                    color = get_marker_color(loc.get("status"))
                    size = min(80, 20 + loc.get("count", 1) * 3)
                    modal_markers.append(
                        ft.Container(
                            left=loc.get("x", 0) * 5,
                            top=loc.get("y", 0) * 3,
                            width=size,
                            height=size,
                            bgcolor=color,
                            border_radius=size/2,
                            border=ft.border.all(2, "white"),
                            shadow=ft.BoxShadow(blur_radius=6, color="#00000030"),
                            alignment=ft.alignment.center,
                            tooltip=f"{loc.get('name')}: {loc.get('count')} listings",
                            content=ft.Text(str(loc.get("count")), size=12, color="white", weight=ft.FontWeight.BOLD),
                        )
                    )
            except Exception:
                modal_markers = []

            large_map = ft.Container(
                height=640,
                width=1000,
                border_radius=8,
                bgcolor="#E8F4FD",
                border=ft.border.all(1, "#B0D4F1"),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                content=ft.Column(spacing=12, controls=[
                    ft.Container(
                        alignment=ft.alignment.center,
                        expand=True,
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_center,
                            end=ft.alignment.bottom_center,
                            colors=["#E3F2FD", "#BBDEFB", "#90CAF9"],
                        ),
                        content=ft.Stack(controls=[
                            ft.Container(
                                alignment=ft.alignment.center,
                                expand=True,
                                content=ft.Column(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Icon(ft.Icons.MAP, size=80, color="#1976D2"),
                                        ft.Text("Philippines Map View", size=18, color="#1976D2"),
                                        ft.Text("Showing listing hotspots across regions", size=13, color=ft.Colors.BLACK),
                                    ]
                                )
                            ),
                            *modal_markers,
                        ])
                    ),
                    map_legend
                ])
            )

            from components.dialog_helper import open_dialog, close_dialog

            dlg = ft.AlertDialog(
                modal=True,
                content=large_map,
                actions=[ft.TextButton("Close", on_click=lambda e, d=None: close_dialog(self.page, dlg))]
            )

            open_dialog(self.page, dlg)

        # FIX: Adjusted spacing and heights to prevent cutoff
        map_section = ft.Container(
            bgcolor="white",
            padding=16,
            border_radius=12,
            height=chart_height - 40,
            shadow=ft.BoxShadow(blur_radius=15, spread_radius=1, color="#00000010"),
            content=ft.Column(
                spacing=12,  # Reduced spacing
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Listings Hotspot Map", size=18, weight=ft.FontWeight.BOLD),
                                    ft.Text("Geographic distribution of listings", size=12, color=ft.Colors.BLACK),
                                ]
                            ),
                            ft.Row([
                                ft.IconButton(icon=ft.Icons.FULLSCREEN, icon_size=20, tooltip="Expand Map", on_click=_open_map_modal),
                                ft.IconButton(icon=ft.Icons.REFRESH, icon_size=20, tooltip="Refresh Data", on_click=lambda e: __import__('services.refresh_service').notify()),
                            ])
                        ]
                    ),
                    ft.Divider(height=1, color="#E0E0E0"),
                    # FIX: Adjusted map container height
                    ft.Container(
                        height=max(140, chart_height - 240),  # Adjusted calculation
                        border_radius=8,
                        bgcolor="#E8F4FD",
                        border=ft.border.all(1, "#B0D4F1"),
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        content=ft.Stack(
                            controls=[
                                ft.Container(
                                    alignment=ft.alignment.center,
                                    expand=True,
                                    gradient=ft.LinearGradient(
                                        begin=ft.alignment.top_center,
                                        end=ft.alignment.bottom_center,
                                        colors=["#E3F2FD", "#BBDEFB", "#90CAF9"],
                                    ),
                                    content=ft.Column(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            ft.Icon(ft.Icons.MAP, size=60, color="#1976D2"),
                                            ft.Text("Philippines Map View", size=14, color="#1976D2"),
                                            ft.Text("Showing listing hotspots across regions", size=11, color=ft.Colors.BLACK),
                                        ]
                                    )
                                ),
                                *map_markers,
                            ]
                        )
                    ),
                    map_legend,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        controls=[
                            ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=2,
                                controls=[
                                    ft.Text(str(approved_listings), size=20, weight=ft.FontWeight.BOLD, color="#2196F3"),
                                    ft.Text("Active", size=11, color=ft.Colors.BLACK),
                                ]
                            ),
                            ft.Container(width=1, height=40, bgcolor="#E0E0E0"),
                            ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=2,
                                controls=[
                                    ft.Text(str(pending_listings), size=20, weight=ft.FontWeight.BOLD, color="#FF9800"),
                                    ft.Text("Pending", size=11, color=ft.Colors.BLACK),
                                ]
                            ),
                            ft.Container(width=1, height=40, bgcolor="#E0E0E0"),
                            ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=2,
                                controls=[
                                    ft.Text("6", size=20, weight=ft.FontWeight.BOLD, color="#4CAF50"),
                                    ft.Text("Regions", size=11, color=ft.Colors.BLACK),
                                ]
                            ),
                        ]
                    ),
                ]
            )
        )

        # =====================================================
        # MAIN VIEW LAYOUT (sidebar removed)
        # =====================================================
        print("Building ft.View for admin dashboard")
        main_column = ft.Column(
            expand=True,
            spacing=0,
            controls=[
                navbar,
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=40, vertical=30),
                    content=ft.Column(
                        spacing=25,
                        controls=[
                            header_section,
                            kpi_section,
                            charts_row,
                            ft.Row(
                                spacing=20,
                                vertical_alignment=ft.CrossAxisAlignment.START,
                                controls=[
                                    ft.Container(expand=1, content=map_section),
                                    ft.Container(expand=1, content=reservation_trend_card),
                                ]
                            ),
                        ]
                    )
                ),
                footer
            ]
        )

        view = ft.View(
            "/admin",
            bgcolor="#F5F7FA",
            scroll=ft.ScrollMode.AUTO,
            controls=[main_column]
        )
        print(f"Admin dashboard view created successfully: {view is not None}")
        return view

    def _logout(self):
        self.session.logout()
        self.page.go("/")