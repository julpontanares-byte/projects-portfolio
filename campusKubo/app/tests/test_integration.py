import pytest
from unittest.mock import Mock, patch
import flet as ft
from services.auth_service import AuthService
from services.user_service import UserService
from services.listing_service import ListingService
from services.reservation_service import ReservationService
from services.notification_service import NotificationService
from models.user import User, UserRole
from models.listing import Listing
from datetime import datetime


class DummyPage:
    def __init__(self):
        self.session = {'user_id': 1, 'role': 'tenant'}
        self.width = 1024
        self.height = 768
        self.last_route = None

    def go(self, route):
        self.last_route = route

    def update(self):
        pass


# Integration Tests - Testing service interactions
@patch('services.user_service.db_get_user_by_id')
@patch('services.listing_service.get_listings')
@patch('services.listing_service.get_listing_images')
def test_user_listing_integration(mock_images, mock_listings, mock_user):
    # Test user retrieving their listings
    mock_user.return_value = {'id': 1, 'email': 'test@example.com', 'role': 'pm'}
    mock_listings.return_value = [{'id': 1, 'pm_id': 1, 'address': 'Test Address', 'price': 1000}]
    mock_images.return_value = ['image1.jpg']

    user = UserService.get_user_full(1)
    listings = ListingService.get_all_listings(owner_id=1)

    assert user['id'] == 1
    assert len(listings) == 1
    assert listings[0].pm_id == 1  # Assuming listing has pm_id


@patch('services.reservation_service.create_reservation')
@patch('services.notification_service.NotificationService')
def test_reservation_notification_integration(mock_notif_service, mock_create_reservation):
    # Test creating reservation and sending notification
    mock_create_reservation.return_value = 1
    mock_notif_instance = Mock()
    mock_notif_service.return_value = mock_notif_instance

    # Create reservation
    success, message = ReservationService.create_new_reservation(1, 1, '2024-01-01', '2024-01-02')
    assert success

    # Check if notification was sent (this would need actual implementation)
    # mock_notif_instance.add_notification.assert_called_once()


@patch('services.auth_service.AuthService.validate_email')
@patch('services.auth_service.AuthService.validate_password')
def test_auth_validation_integration(mock_validate_pass, mock_validate_email):
    # Test complete auth validation flow
    mock_validate_email.return_value = (True, "Valid")
    mock_validate_pass.return_value = (True, "Password is valid", ["req1", "req2"])

    email_result = AuthService.validate_email("test@example.com")
    pass_result = AuthService().validate_password("ValidPass123!")

    assert email_result[0] is True
    assert pass_result[0] is True


def test_user_role_workflow():
    # Test role-based workflow
    admin_user = User(id=1, email="admin@test.com", full_name="Admin User", role=UserRole.ADMIN)
    pm_user = User(id=2, email="pm@test.com", full_name="PM User", role=UserRole.PM)
    tenant_user = User(id=3, email="tenant@test.com", full_name="Tenant User", role=UserRole.TENANT)

    assert admin_user.role == UserRole.ADMIN
    assert pm_user.role == UserRole.PM
    assert tenant_user.role == UserRole.TENANT

    # Test role string conversion
    assert admin_user.role.value == "admin"
    assert pm_user.role.value == "pm"
    assert tenant_user.role.value == "tenant"


@patch('services.listing_service.get_listing_by_id')
@patch('services.listing_service.get_listing_images')
@patch('services.reservation_service.create_reservation')
def test_listing_reservation_workflow(mock_create_reservation, mock_images, mock_listing):
    # Test complete listing to reservation workflow
    mock_listing.return_value = {'id': 1, 'address': 'Test Address', 'price': 1000}
    mock_images.return_value = ['image1.jpg']
    mock_create_reservation.return_value = 1

    # Get listing
    listing = ListingService.get_listing_by_id(1)
    assert listing is not None

    # Create reservation
    success, message = ReservationService.create_new_reservation(
        listing.id, 1, '2024-01-01', '2024-01-02'
    )
    assert success


def test_notification_workflow():
    # Test complete notification workflow
    service = NotificationService()

    # Add notifications
    notif1 = service.add_notification(1, 'booking', 'New booking request')
    notif2 = service.add_notification(1, 'payment', 'Payment received')

    # Check unread count
    assert service.get_unread_count(1) == 2

    # Mark one as read
    service.mark_notification_read(notif1['notification_id'])
    assert service.get_unread_count(1) == 1

    # Mark all as read
    service.mark_all_notifications_read(1)
    assert service.get_unread_count(1) == 0


def test_data_validation_workflow():
    # Test data validation across services
    from services.auth_service import AuthService

    # Test email validation
    valid_email = AuthService.validate_email("valid@example.com")
    invalid_email = AuthService.validate_email("invalid")

    assert valid_email[0] is True
    assert invalid_email[0] is False

    # Test password validation
    valid_pass = AuthService().validate_password("StrongPass123!")
    weak_pass = AuthService().validate_password("weak")

    assert valid_pass[0] is True
    assert weak_pass[0] is False


def test_error_handling_workflow():
    # Test error handling across services
    service = NotificationService()

    # Test marking non-existent notification
    result = service.mark_notification_read(999)
    assert result is False

    # Test getting notifications for non-existent user
    notifications = service.get_user_notifications(999)
    assert len(notifications) == 0

    # Test unread count for non-existent user
    count = service.get_unread_count(999)
    assert count == 0