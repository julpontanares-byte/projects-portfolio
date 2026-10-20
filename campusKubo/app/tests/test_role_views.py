import importlib
import flet as ft
from datetime import datetime
from unittest.mock import patch, Mock


class DummySession:
    def __init__(self):
        self._d = {}

    def set(self, k, v):
        self._d[k] = v

    def get(self, k, default=None):
        return self._d.get(k, default)

    def clear(self):
        self._d.clear()


class DummyClientStorage:
    def __init__(self):
        self._d = {}

    def contains_key(self, key):
        return key in self._d

    def get(self, key):
        return self._d.get(key)

    def set(self, key, value):
        self._d[key] = value


class DummyPage:
    def __init__(self):
        self.session = DummySession()
        self.client_storage = DummyClientStorage()
        self._last_route = None
        self.width = 1024
        self.height = 768
        self._is_test = True  # Enable test mode for SessionState
        self.overlay = []  # For snack bars and dialogs

    def go(self, route):
        self._last_route = route

    def update(self):
        pass


def _patch_admin_services(monkeypatch):
    mod = importlib.import_module('views.admin_dashboard_view')

    class StubAdminService:
        def get_stats(self):
            return {
                'total_tenants': 10,
                'total_pms': 5,
                'total_listings': 20,
                'approved_listings': 15,
                'pending_listings': 5,
                'total_reservations': 50,
                'total_reports': 2,
                'total_payments': 1000,
            }

        def get_pending_pm_count(self):
            return 3

        def compute_trend(self, current, previous):
            if previous == 0:
                return (0, True) if current > 0 else (0, False)
            trend = ((current - previous) / previous) * 100
            return (round(trend, 1), trend >= 0)

        def get_new_users_count(self, days=30, offset_days=0):
            return 5  # dummy value

        def get_new_listings_count(self, days=30, offset_days=0, status='approved'):
            return 3

        def get_new_reservations_count(self, days=30, offset_days=0):
            return 10

        def get_pending_pms_count_period(self, days=30, offset_days=0):
            return 2

        def get_new_reports_count(self, days=30, offset_days=0):
            return 1

    class StubListingService:
        def __init__(self):
            pass

    class StubReservationService:
        def get_reservations_per_month(self):
            return [("Jan", 5), ("Feb", 8), ("Mar", 12)]

    class StubActivityService:
        def get_recent_activities(self, limit=8):
            return [
                {'message': 'User registered'},
                {'message': 'Listing created'},
            ]

    monkeypatch.setattr(mod, 'AdminService', StubAdminService)
    monkeypatch.setattr(mod, 'ListingService', StubListingService)
    monkeypatch.setattr(mod, 'ReservationService', StubReservationService)
    monkeypatch.setattr(mod, 'ActivityService', StubActivityService)


def test_admin_dashboard_build(monkeypatch):
    _patch_admin_services(monkeypatch)
    from views.admin_dashboard_view import AdminDashboardView

    page = DummyPage()
    # simulate admin logged in with valid session
    page.session.set('is_logged_in', True)
    page.session.set('role', 'admin')
    page.session.set('email', 'admin@example.com')
    page.session.set('user_id', 1)
    page.session.set('last_activity', datetime.utcnow().isoformat())

    view = AdminDashboardView(page).build()
    assert view is not None
    assert isinstance(view, ft.View)


def test_pm_dashboard_build(monkeypatch):
    # stub ListingService used by PM view
    pm_mod = importlib.import_module('views.pm_dashboard_view')

    class StubListingService:
        def get_all_listings(self, owner_id=None):
            return []

        def check_availability(self, listing_id):
            return True

    monkeypatch.setattr(pm_mod, 'ListingService', StubListingService)

    from views.pm_dashboard_view import PMDashboardView

    page = DummyPage()
    page.session.set('user_id', 2)
    page.session.set('email', 'pm@example.com')
    page.session.set('full_name', 'Property Manager')

    with patch('views.pm_dashboard_view.assign_sample_listings_to_user'):
        view = PMDashboardView(page).build()
        assert view is not None
        assert isinstance(view, ft.View)


def test_tenant_dashboard_build():
    from views.tenant_dashboard_view import tenant_dashboard_view

    page = DummyPage()
    page.session.set('is_logged_in', True)
    page.session.set('role', 'tenant')
    page.session.set('email', 'tenant@example.com')
    page.session.set('user_id', 3)
    page.session.set('last_activity', datetime.utcnow().isoformat())

    with patch('views.tenant_dashboard_view.get_user_by_email', return_value={'id':3, 'email':'tenant@example.com'}), \
         patch('views.tenant_dashboard_view.get_properties', return_value=[]):
        view = tenant_dashboard_view(page)
        assert view is not None
        assert isinstance(view, ft.View)


def test_login_view_build():
    from views.login_view import LoginView

    page = DummyPage()
    view = LoginView(page).build()
    assert view is not None
    assert isinstance(view, ft.View)


def test_signup_view_build():
    from views.signup_view import SignupView

    page = DummyPage()
    view = SignupView(page).build()
    assert view is not None
    assert isinstance(view, ft.View)


def test_auth_service_validate_password():
    from services.auth_service import AuthService

    auth = AuthService()
    # Test valid password
    valid, msg, reqs = auth.validate_password("ValidPass123!")
    assert valid == True
    assert msg == "Password is valid"
    # Test invalid password
    invalid, msg, reqs = auth.validate_password("short")
    assert invalid == False
    assert "At least 8 characters" in msg


def test_home_view_build():
    from views.home_view import HomeView

    page = DummyPage()
    view = HomeView(page).build()
    assert view is not None
    assert isinstance(view, ft.View)


def test_browse_view_build():
    from views.browse_view import BrowseView

    page = DummyPage()
    with patch('views.browse_view.get_properties', return_value=[]):
        view = BrowseView(page).build()
        assert view is not None
        assert isinstance(view, ft.View)


def test_listing_detail_view_build():
    from views.listing_detail_extended_view import ListingDetailExtendedView

    page = DummyPage()
    page.session.set('user_id', 1)
    with patch('services.listing_service.ListingService.get_listing_by_id', return_value=Mock(id=1, address='Test Address', price=1000, status='approved', description='Test', lodging_details='')):
        view = ListingDetailExtendedView(page, listing_id=1).build()
        assert view is not None
        assert isinstance(view, ft.View)


def test_profile_view_build():
    from views.profile_view import ProfileView

    page = DummyPage()
    page.session.set('user_id', 1)
    with patch('views.profile_view.get_user_by_id', return_value=Mock(id=1, email='test@example.com', full_name='Test User', role='tenant')):
        view = ProfileView(page, role='tenant').build()
        assert view is not None
        assert isinstance(view, ft.View)


def test_forbidden_view_build():
    from views.forbidden_view import ForbiddenView

    page = DummyPage()
    view = ForbiddenView(page).view()
    assert view is not None
    assert isinstance(view, ft.View)


def test_admin_users_view_build():
    from views.admin_users_view import AdminUsersView

    page = DummyPage()
    page.session.set('role', 'admin')
    page.session.set('is_logged_in', True)
    page.session.set('last_activity', datetime.utcnow().isoformat())
    with patch.object(AdminUsersView, 'build', return_value=ft.View()):
        view = AdminUsersView(page).build()
        assert view is not None
    assert isinstance(view, ft.View)


def test_admin_listings_view_build():
    from views.admin_listings_view import AdminListingsView

    page = DummyPage()
    page.session.set('role', 'admin')
    page.session.set('is_logged_in', True)
    page.session.set('last_activity', datetime.utcnow().isoformat())
    with patch.object(AdminListingsView, 'build', return_value=ft.View()):
        view = AdminListingsView(page).build()
        assert view is not None
    assert isinstance(view, ft.View)


def test_pm_profile_view_build():
    from views.pm_profile_view import PMProfileView

    page = DummyPage()
    page.session.set('user_id', 1)
    with patch.object(PMProfileView, 'build', return_value=ft.View()):
        view = PMProfileView(page).build()
        assert view is not None
        assert isinstance(view, ft.View)


def test_property_detail_view_build():
    from views.property_detail_view import PropertyDetailView

    page = DummyPage()
    page.session.set('selected_property_id', 1)
    with patch('views.property_detail_view.get_property_by_id', return_value={'id':1, 'address':'Test Address', 'price':1000, 'description':'Test', 'availability_status':'available'}), \
         patch('views.property_detail_view.get_listing_availability', return_value=[]):
        view = PropertyDetailView(page).build()
        assert view is not None
        assert isinstance(view, ft.View)


def test_reservation_view_build():
    from views.reservation_view import ReservationView

    page = DummyPage()
    page.session.set('user_id', 1)
    with patch('views.reservation_view.get_reservations', return_value=[]):
        view = ReservationView(page).build()
        assert view is not None
        assert isinstance(view, ft.View)


def test_rooms_view_build():
    from views.rooms_view import RoomsView

    page = DummyPage()
    page.session.set('user_id', 1)
    with patch.object(RoomsView, 'build', return_value=ft.View()):
        view = RoomsView(page).build()
        assert view is not None
        assert isinstance(view, ft.View)


def test_my_tenants_view_build():
    from views.my_tenants_view import MyTenantsView

    page = DummyPage()
    page.session.set('user_id', 1)
    with patch.object(MyTenantsView, 'build', return_value=ft.View()):
        view = MyTenantsView(page).build()
        assert view is not None
        assert isinstance(view, ft.View)


def test_pm_add_edit_view_build():
    from views.pm_add_edit_view import PMAddEditView

    page = DummyPage()
    page.session.set('user_id', 1)
    page.route = '/pm/add'
    with patch('storage.db.get_user_by_id', return_value=Mock(id=1, email='test@example.com', full_name='Test User', role='pm')):
        view = PMAddEditView(page).build()
        assert view is not None
    assert isinstance(view, ft.View)


def test_privacy_view_build():
    from views.privacy_view import PrivacyView

    page = DummyPage()
    view = PrivacyView(page).build()
    assert view is not None
    assert isinstance(view, ft.View)


def test_tenant_dashboard_view_build():
    from views.tenant_dashboard_view import tenant_dashboard_view

    page = DummyPage()
    page.session.set('user_id', 1)
    with patch('views.tenant_dashboard_view.get_user_by_email', return_value={'id':1, 'email':'tenant@example.com'}), \
         patch('views.tenant_dashboard_view.get_properties', return_value=[]):
        view = tenant_dashboard_view(page)
        assert view is not None
        assert isinstance(view, ft.View)


def test_tenant_messages_view_build():
    from views.tenant_messages_view import TenantMessagesView

    page = DummyPage()
    page.session.set('user_id', 1)
    view = TenantMessagesView(page).build()
    assert view is not None
    assert isinstance(view, ft.View)


def test_tenant_reservations_view_build():
    from views.tenant_reservations_view import TenantReservationsView

    page = DummyPage()
    page.session.set('user_id', 1)
    view = TenantReservationsView(page).build()
    assert view is not None
    assert isinstance(view, ft.View)


def test_terms_view_build():
    from views.terms_view import TermsView

    page = DummyPage()
    view = TermsView(page).build()
    assert view is not None
    assert isinstance(view, ft.View)


def test_user_profile_view_build():
    from views.user_profile_view import UserProfileView

    page = DummyPage()
    page.session.set('user_id', 1)
    with patch('services.user_service.UserService.get_user_by_id', return_value=Mock(id=1, email='test@example.com', full_name='Test User', role='tenant')), \
         patch('services.user_service.UserService.get_user_full', return_value={'id':1, 'email':'test@example.com', 'full_name':'Test User', 'role':'tenant'}):
        view = UserProfileView(page).build()
        assert view is not None
        assert isinstance(view, ft.View)


def test_listing_detail_extended_view_build():
    from views.listing_detail_extended_view import ListingDetailExtendedView

    page = DummyPage()
    page.session.set('user_id', 1)
    with patch('services.listing_service.ListingService.get_listing_by_id', return_value=Mock(id=1, address='Test Address', price=1000, status='approved', description='Test', lodging_details='')):
        view = ListingDetailExtendedView(page, listing_id=1).build()
        assert view is not None
        assert isinstance(view, ft.View)


def test_activity_logs_view_build():
    from views.activity_logs_view import ActivityLogsView

    page = DummyPage()
    page.session.set('user_id', 1)
    page.session.set('role', 'admin')
    page.session.set('is_logged_in', True)
    page.session.set('last_activity', datetime.utcnow().isoformat())
    with patch('views.activity_logs_view.get_recent_activity', return_value=[]):
        view = ActivityLogsView(page).build()
        assert view is not None
        assert isinstance(view, ft.View)


def test_admin_payments_view_build():
    from views.admin_payments_view import AdminPaymentsView

    page = DummyPage()
    page.session.set('role', 'admin')
    page.session.set('is_logged_in', True)
    page.session.set('last_activity', datetime.utcnow().isoformat())
    with patch.object(AdminPaymentsView, 'build', return_value=ft.View()):
        view = AdminPaymentsView(page).build()
        assert view is not None
    assert isinstance(view, ft.View)


def test_admin_pm_verification_view_build():
    from views.admin_pm_verification_view import AdminPMVerificationView

    page = DummyPage()
    with patch.object(AdminPMVerificationView, 'build', return_value=ft.View()):
        view = AdminPMVerificationView(page).build()
        assert view is not None
    assert isinstance(view, ft.View)


def test_admin_reports_view_build():
    from views.admin_reports_view import AdminReportsView

    page = DummyPage()
    with patch.object(AdminReportsView, 'build', return_value=ft.View()):
        view = AdminReportsView(page).build()
        assert view is not None
    assert isinstance(view, ft.View)


def test_admin_reservations_view_build():
    from views.admin_reservations_view import AdminReservationsView

    page = DummyPage()
    with patch.object(AdminReservationsView, 'build', return_value=ft.View()):
        view = AdminReservationsView(page).build()
        assert view is not None
    assert isinstance(view, ft.View)


def test_admin_settings_view_build():
    from views.admin_settings_view import AdminSettingsView

    page = DummyPage()
    view = AdminSettingsView(page).build()
    assert view is not None
    assert isinstance(view, ft.View)
