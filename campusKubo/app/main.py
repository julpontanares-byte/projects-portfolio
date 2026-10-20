"""
CampusKubo - Main Application (Model Version)
Single-file application matching the provided model.
Uses existing modular components and database infrastructure.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import flet as ft

# Generate or load secret key
from config.secrets import get_or_create_secret_key
get_or_create_secret_key()

# Import database functions (matching model's import style)
from storage.db import (
    init_db,
    property_data
)
from services.auth_service import AuthService

# Import modular components
from views.admin_dashboard_view import AdminDashboardView
from views.admin_users_view import AdminUsersView
from views.admin_pm_verification_view import AdminPMVerificationView
from views.admin_listings_view import AdminListingsView
from views.admin_reservations_view import AdminReservationsView
from views.admin_payments_view import AdminPaymentsView
from views.admin_reports_view import AdminReportsView
from views.admin_profile_view import AdminProfileView
from views.activity_logs_view import ActivityLogsView
from views.home_view import HomeView
from views.browse_view import BrowseView
from views.login_view import LoginView
from views.signup_view import SignupView
from views.tenant_dashboard_view import tenant_dashboard_view
from views.pm_dashboard_view import PMDashboardView
from views.pm_analytics_view import PMAnalyticsView
from views.pm_add_edit_view import PMAddEditView
from views.pm_profile_view import PMProfileView
from views.property_detail_view import PropertyDetailView
from views.rooms_view import RoomsView
from views.rooms_view import RoomsView
from views.my_tenants_view import MyTenantsView
from views.user_profile_view import UserProfileView
from views.tenant_reservations_view import TenantReservationsView
from views.tenant_messages_view import TenantMessagesView
from views.forbidden_view import ForbiddenView
from views.terms_view import TermsView
from views.privacy_view import PrivacyView
from views.reservation_view import ReservationView
from state.session_state import SessionState

def main(page: ft.Page):
    """Main application entry point - modular version"""

    page.title = "CampusKubo"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.frameless = False
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Initialize database
    # Run startup health checks before initializing DB
#   try:
#       run_startup_checks(fail_on_error=False)
#   except Exception as e:
#       print(f"[main] Startup health check warning: {e}")
    init_db()
    AuthService.ensure_admin_exists()
    property_data()

    # ========== ROUTING SYSTEM ==========

    def route_change(e):
        """Centralized routing with RBAC and navigation history"""
        # Extract route from event
        route = e.route if hasattr(e, 'route') else page.route

        # Navigation history management
        prev_route = getattr(page, "_current_route", None)
        is_back = getattr(page, "_nav_back_navigation", False)

        # Routes that shouldn't be added to history (detail pages, modals, etc.)
        # These pages are "dead ends" - you view them and go back, no forward navigation
        non_history_routes = ["/property-details", "/403"]

        # Only add to history if:
        # 1. Not a back navigation
        # 2. Previous route exists and is different from current
        # 3. Previous route is not a "non-history" route (detail pages)
        if not is_back and prev_route and prev_route != route:
            if prev_route not in non_history_routes:
                history = getattr(page, "_nav_history", [])
                # Avoid duplicates - if the route is already last in history, don't add again
                if not history or history[-1] != prev_route:
                    history.append(prev_route)
                    setattr(page, "_nav_history", history)

        setattr(page, "_nav_back_navigation", False)
        setattr(page, "_current_route", route)
        page.views.clear()

        # Session manager
        session = SessionState(page)

        # ========== ROUTE PERMISSION MAP ==========
        ROUTE_PERMISSIONS = {
            "/admin": ["admin"],
            "/pm": ["pm"],
            "/tenant": ["tenant"],
            "/rooms": ["pm"],
            "/my-tenants": ["pm"],
        }

        # ========== RBAC CHECK ==========
        for route_prefix, allowed_roles in ROUTE_PERMISSIONS.items():
            if page.route.startswith(route_prefix):
                if not session.require_role(allowed_roles, redirect_to_403=True):
                    return

        # ========== ROUTE HANDLERS ==========
        view = None

        # --- PUBLIC ROUTES ---
        if route == "/":
            view = HomeView(page).build()

        elif route == "/login":
            view = LoginView(page).build()

        elif route == "/signup":
            view = SignupView(page).build()

        elif route == "/terms":
            view = TermsView(page).build()

        elif route == "/privacy":
            view = PrivacyView(page).build()

        elif route == "/browse":
            view = BrowseView(page).build()

        elif route == "/property-details":
            view = PropertyDetailView(page).build()

        elif route == "/403":
            view = ForbiddenView(page).view()

        elif route == "/logout":
            session.logout()
            page.go("/login")
            return

        # --- TENANT ROUTES ---
        elif route == "/tenant":
            view = tenant_dashboard_view(page)

        elif route == "/tenant/reservations":
            view = TenantReservationsView(page).build()

        elif route == "/reservations":
            view = ReservationView(page).build()

        elif route == "/tenant/messages":
            view = TenantMessagesView(page).build()

        elif route == "/tenant/profile":
            view = UserProfileView(page).build()

        # --- PROPERTY MANAGER ROUTES ---
        elif route == "/pm":
            view = PMDashboardView(page).build()

        elif route == "/pm/add":
            view = PMAddEditView(page).build()

        elif route.startswith("/pm/edit/"):
            view = PMAddEditView(page).build()

        elif route == "/pm/profile":
            view = PMProfileView(page).build()

        elif route == "/pm/profile/edit":
            view = PMAddEditView(page).build()

        elif route == "/pm/analytics":
            view = PMAnalyticsView(page).build()

        elif route == "/rooms":
            view = RoomsView(page).build()

        elif route.startswith("/rooms/"):
            try:
                property_id = int(route.split("/")[-1])
                view = RoomsView(page, property_id=property_id).build()
            except (ValueError, IndexError):
                page.go("/rooms")
                return

        elif route == "/my-tenants":
            view = MyTenantsView(page).build()

        elif route.startswith("/my-tenants/"):
            try:
                property_id = int(route.split("/")[-1])
                view = MyTenantsView(page, property_id=property_id).build()
            except (ValueError, IndexError):
                page.go("/my-tenants")
                return

        # --- ADMIN ROUTES ---
        elif route == "/admin":
            view = AdminDashboardView(page).build()

        elif route == "/admin_users":
            view = AdminUsersView(page).build()

        elif route == "/admin_pm_verification":
            view = AdminPMVerificationView(page).build()

        elif route == "/admin_listings":
            view = AdminListingsView(page).build()

        elif route == "/admin_reservations":
            view = AdminReservationsView(page).build()

        elif route == "/admin_payments":
            view = AdminPaymentsView(page).build()

        elif route == "/admin_reports":
            view = AdminReportsView(page).build()

        elif route == "/admin_activity_logs":
            view = ActivityLogsView(page).build()

        elif route == "/admin_profile":
            view = AdminProfileView(page).build()

        # --- 404 NOT FOUND ---
        else:
            view = ft.View(
                route,
                controls=[
                    ft.Container(
                        padding=50,
                        alignment=ft.alignment.center,
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=20,
                            controls=[
                                ft.Icon(ft.Icons.ERROR_OUTLINE, size=100, color="#FF6B6B"),
                                ft.Text("404 - Page Not Found", size=32, weight=ft.FontWeight.BOLD),
                                ft.Text(f"The page '{route}' does not exist.", size=16, color="#666"),
                                ft.ElevatedButton(
                                    "Go Home",
                                    icon=ft.Icons.HOME,
                                    on_click=lambda _: page.go("/"),
                                    bgcolor="#0078FF",
                                    color = ft.Colors.WHITE
                                )
                            ]
                        )
                    )
                ]
            )

        # Append view to page
        if view:
            page.views.append(view)

        page.update()

    def view_pop(view):
        """Handle browser back button - properly navigate to previous page"""
        if page.views:
            page.views.pop()
        history = getattr(page, "_nav_history", [])
        if history:
            target_route = history.pop()
        else:
            target_route = "/"
        setattr(page, "_nav_history", history)
        setattr(page, "_nav_back_navigation", True)
        page.go(target_route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")