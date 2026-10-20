import pytest
from unittest.mock import Mock, patch
from services.auth_service import AuthService
from services.user_service import UserService
from services.listing_service import ListingService
from services.reservation_service import ReservationService
from services.notification_service import NotificationService
from services.admin_service import AdminService
from services.settings_service import SettingsService
from services.activity_service import ActivityService
from services.report_service import ReportService
from models.listing import Listing
from models.user import User, UserRole
from datetime import datetime


def test_auth_service_validate_email():
    assert AuthService.validate_email("test@example.com") == (True, "Valid")
    assert AuthService.validate_email("invalid") == (False, "Please enter a valid email address")


def test_auth_service_validate_password():
    valid, msg, _ = AuthService().validate_password("ValidPass123!")
    assert valid
    assert msg == "Password is valid"

    invalid, msg, _ = AuthService().validate_password("short")
    assert not invalid
    assert "At least 8 characters" in msg


@patch('services.user_service.db_get_user_by_id')
def test_user_service_get_user(mock_get):
    mock_get.return_value = {'id': 1, 'email': 'test@example.com'}
    user = UserService.get_user_full(1)
    assert user['email'] == 'test@example.com'


# Listing Service Tests
@patch('services.listing_service.get_listings')
@patch('services.listing_service.get_listing_images')
def test_listing_service_get_all_listings(mock_images, mock_listings):
    mock_listings.return_value = [{'id': 1, 'address': 'Test Address', 'price': 1000}]
    mock_images.return_value = ['image1.jpg']

    listings = ListingService.get_all_listings()
    assert len(listings) == 1
    assert listings[0].address == 'Test Address'


@patch('services.listing_service.get_listing_by_id')
@patch('services.listing_service.get_listing_images')
def test_listing_service_get_listing_by_id(mock_images, mock_listing):
    mock_listing.return_value = {'id': 1, 'address': 'Test Address', 'price': 1000}
    mock_images.return_value = ['image1.jpg']

    listing = ListingService.get_listing_by_id(1)
    assert listing is not None
    assert listing.id == 1


@patch('services.listing_service.get_listing_availability')
def test_listing_service_check_availability(mock_availability):
    mock_availability.return_value = []
    result = ListingService.check_availability(1)
    assert result is True


# Reservation Service Tests
@patch('services.reservation_service.create_reservation')
def test_reservation_service_create_new_reservation(mock_create):
    mock_create.return_value = 1
    success, message = ReservationService.create_new_reservation(1, 1, '2024-01-01', '2024-01-02')
    assert success
    assert 'created successfully' in message


def test_reservation_service_create_new_reservation_invalid_dates():
    success, message = ReservationService.create_new_reservation(1, 1, '', '2024-01-02')
    assert not success
    assert 'dates are required' in message


# Notification Service Tests
def test_notification_service_add_notification():
    service = NotificationService()
    notif = service.add_notification(1, 'info', 'Test message')
    assert notif['user_id'] == 1
    assert notif['message'] == 'Test message'
    assert notif['is_read'] is False


def test_notification_service_get_user_notifications():
    service = NotificationService()
    service.add_notification(1, 'info', 'Test message')
    service.add_notification(2, 'warning', 'Other message')

    notifications = service.get_user_notifications(1)
    assert len(notifications) == 1
    assert notifications[0]['message'] == 'Test message'


def test_notification_service_get_unread_count():
    service = NotificationService()
    service.add_notification(1, 'info', 'Test message')
    service.add_notification(1, 'warning', 'Another message')

    count = service.get_unread_count(1)
    assert count == 2


def test_notification_service_mark_notification_read():
    service = NotificationService()
    notif = service.add_notification(1, 'info', 'Test message')
    result = service.mark_notification_read(notif['notification_id'])
    assert result is True

    count = service.get_unread_count(1)
    assert count == 0


def test_notification_service_mark_all_notifications_read():
    service = NotificationService()
    service.add_notification(1, 'info', 'Test message 1')
    service.add_notification(1, 'warning', 'Test message 2')

    count = service.mark_all_notifications_read(1)
    assert count == 2

    unread_count = service.get_unread_count(1)
    assert unread_count == 0


# Admin Service Tests
@patch('services.admin_service.get_connection')
def test_admin_service_get_all_users(mock_conn):
    mock_cursor = Mock()
    mock_conn.return_value.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [{'id': 1, 'email': 'test@example.com', 'role': 'admin'}]

    service = AdminService()
    users = service.get_all_users()
    assert len(users) == 1
    assert users[0].email == 'test@example.com'


@patch('services.admin_service.get_connection')
def test_admin_service_get_user_by_id(mock_conn):
    mock_cursor = Mock()
    mock_conn.return_value.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'id': 1, 'email': 'test@example.com', 'role': 'admin'}

    service = AdminService()
    user = service.get_user_by_id(1)
    assert user is not None
    assert user.id == 1


# Settings Service Tests
# Settings Service Tests
@patch('services.settings_service.db_get_settings')
def test_settings_service_get_settings(mock_get):
    mock_get.return_value = {'theme': 'dark', 'notifications': True}
    # Assuming SettingsService has a get_settings method
    # This needs to be implemented based on actual service


# Activity Service Tests
@patch('services.activity_service.log_activity')
def test_activity_service_log_activity(mock_log):
    ActivityService.log_activity(1, 'login', 'User logged in')
    mock_log.assert_called_once_with(1, 'login', 'User logged in')


@patch('services.activity_service.get_recent_activity')
def test_activity_service_get_recent_activities(mock_get):
    # Create a mock row that supports both key access and index access
    class MockRow:
        def __init__(self, data):
            self.data = data

        def __getitem__(self, key):
            if isinstance(key, int):
                return list(self.data.values())[key]
            return self.data[key]

        def __contains__(self, key):
            return key in self.data

        def keys(self):
            return self.data.keys()

    mock_row = MockRow({
        'id': 1,
        'user_id': 1,
        'user_email': 'test@example.com',
        'action': 'login',
        'details': 'User logged in',
        'created_at': '2024-01-01 12:00:00'
    })

    mock_get.return_value = [mock_row]
    activities = ActivityService.get_recent_activities(10)
    assert len(activities) == 1
    assert activities[0]['action'] == 'login'


# Report Service Tests
@patch('services.report_service.get_connection')
def test_report_service_get_reports(mock_conn):
    # Create a mock row that supports both key access and index access
    class MockRow:
        def __init__(self, data):
            self.data = data

        def __getitem__(self, key):
            if isinstance(key, int):
                return list(self.data.values())[key]
            return self.data[key]

        def __contains__(self, key):
            return key in self.data

        def keys(self):
            return self.data.keys()

    mock_cursor = Mock()
    mock_conn.return_value.cursor.return_value = mock_cursor
    mock_row = MockRow({
        'id': 1,
        'message': 'Test report',
        'status': 'pending',
        'created_at': '2024-01-01',
        'user_id': 1,
        'reporter_email': 'reporter@example.com',
        'listing_address': '123 Test St',
        'assigned_admin_id': None,
        'assigned_at': None,
        'assigned_note': None
    })
    mock_cursor.fetchall.return_value = [mock_row]

    reports = ReportService.get_reports()
    assert len(reports) == 1
    assert reports[0]['message'] == 'Test report'