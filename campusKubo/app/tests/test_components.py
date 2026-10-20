import pytest
import flet as ft
from unittest.mock import Mock
from components.login_form import LoginForm
from components.signup_form import SignupForm
from components.navbar import NavBar
from components.footer import Footer
from components.logo import Logo
from components.searchbar import SearchBar
from components.listing_card import ListingCard
from components.table_card import TableCard
from components.chart_card import ChartCard
from components.admin_stats_card import AdminStatsCard
from components.admin_user_table import AdminUserTable
from components.notification_banner import NotificationBanner
from components.password_requirements import PasswordRequirements
from components.profile_section import ProfileSection
from components.reservation_form import ReservationForm
from components.search_filter import SearchFilter
from components.signup_banner import SignupBanner
from components.advanced_filters import AdvancedFilters


class DummyPage:
    def __init__(self):
        self.session = {'user_id': 1, 'role': 'tenant'}
        self.width = 1024
        self.height = 768

    def go(self, route):
        pass

    def update(self):
        pass


def test_login_form_build():
    page = DummyPage()
    form = LoginForm(page)
    component = form.build()
    assert component is not None
    assert isinstance(component, ft.Container)


def test_signup_form_build():
    page = DummyPage()
    form = SignupForm(page)
    component = form.build()
    assert component is not None
    assert isinstance(component, ft.Container)


def test_navbar_build():
    page = DummyPage()
    navbar = NavBar(page)
    component = navbar.view()
    assert component is not None
    assert isinstance(component, ft.Container)


def test_footer_build():
    page = DummyPage()
    footer = Footer(page)
    component = footer.build()
    assert component is not None
    assert isinstance(component, ft.Container)


def test_logo_build():
    page = DummyPage()
    logo = Logo(page)
    component = logo.build()
    assert component is not None
    assert isinstance(component, ft.Container)


def test_searchbar_build():
    page = DummyPage()
    searchbar = SearchBar(page)
    component = searchbar.build()
    assert component is not None
    assert isinstance(component, ft.Container)


def test_listing_card_build():
    page = DummyPage()
    # Mock listing data
    listing = Mock()
    listing.id = 1
    listing.address = "Test Address"
    listing.price = 1000
    listing.description = "Test description"
    listing.images = ["image1.jpg"]

    card = ListingCard(page, listing)
    component = card.build()
    assert component is not None
    assert isinstance(component, ft.Container)


def test_table_card_build():
    page = DummyPage()
    data = [
        {"id": 1, "name": "Test", "status": "Active"},
        {"id": 2, "name": "Test2", "status": "Inactive"}
    ]
    columns = ["id", "name", "status"]

    card = TableCard(page, data, columns, "Test Table")
    component = card.build()
    assert component is not None
    assert isinstance(component, ft.Container)


def test_chart_card_build():
    page = DummyPage()
    data = {"labels": ["Jan", "Feb"], "values": [10, 20]}

    card = ChartCard(page, data, "Test Chart")
    component = card.build()
    assert component is not None
    assert isinstance(component, ft.Container)


def test_admin_stats_card_build():
    page = DummyPage()
    stats = {"total_users": 100, "active_listings": 50}

    card = AdminStatsCard(page, stats)
    component = card.build()
    assert component is not None
    assert isinstance(component, ft.Container)


def test_admin_user_table_build():
    page = DummyPage()
    users = [
        Mock(id=1, email="test@example.com", full_name="Test User", role="tenant", is_active=True),
        Mock(id=2, email="test2@example.com", full_name="Test User 2", role="pm", is_active=False)
    ]

    table = AdminUserTable(page, users)
    component = table.build()
    assert component is not None
    assert isinstance(component, ft.Container)


def test_notification_banner_build():
    page = DummyPage()
    banner = NotificationBanner(page, "Test message", "info")
    component = banner.build()
    assert component is not None
    assert isinstance(component, ft.Container)


def test_password_requirements_build():
    page = DummyPage()
    reqs = PasswordRequirements(page, "TestPass123!")
    component = reqs.build()
    assert component is not None
    assert isinstance(component, ft.Container)


def test_profile_section_build():
    from unittest.mock import patch
    page = DummyPage()
    with patch('services.user_service.UserService.get_user_full', return_value={'full_name': 'Test User', 'email': 'test@example.com', 'phone': '1234567890'}):
        section = ProfileSection(page)
        component = section.get_profile_info()
        assert component is not None
    component = section.build()
    assert component is not None
    assert isinstance(component, ft.Container)


def test_reservation_form_build():
    page = DummyPage()
    form = ReservationForm(page, listing_id=1)
    component = form.build()
    assert component is not None
    assert isinstance(component, ft.Container)


def test_search_filter_build():
    page = DummyPage()
    filter_comp = SearchFilter(page)
    component = filter_comp.build()
    assert component is not None
    assert isinstance(component, ft.Container)


def test_signup_banner_build():
    page = DummyPage()
    banner = SignupBanner(page)
    component = banner.build()
    assert component is not None
    assert isinstance(component, ft.Container)


def test_advanced_filters_build():
    page = DummyPage()
    filters = AdvancedFilters(page)
    component = filters.build()
    assert component is not None
    assert isinstance(component, ft.Container)

