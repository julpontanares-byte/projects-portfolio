import pytest
from datetime import datetime
from models.user import User, UserRole
from models.listing import Listing
from models.reservation import Reservation, ReservationStatus
from models.payment import Payment
from models.notification import Notification, NotificationType
from models.settings import AppSettings


def test_user_model():
    user = User(
        id=1,
        email="test@example.com",
        full_name="Test User",
        role=UserRole.TENANT,
        created_at=datetime.utcnow(),
        phone="1234567890",
        is_active=True
    )
    assert user.email == "test@example.com"
    assert user.role == UserRole.TENANT


def test_listing_model():
    listing = Listing(
        id=1,
        pm_id=1,
        address="123 Test St",
        price=1000.0,
        description="A test listing",
        lodging_details="Details",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        images=[],
        status="pending"
    )
    assert listing.address == "123 Test St"
    assert listing.price == 1000.0


def test_reservation_model():
    reservation = Reservation(
        id=1,
        listing_id=1,
        tenant_id=1,
        start_date="2023-01-01",
        end_date="2023-01-02",
        status=ReservationStatus.PENDING,
        created_at=datetime.utcnow()
    )
    assert reservation.status == ReservationStatus.PENDING
    assert reservation.start_date == "2023-01-01"


def test_payment_model():
    payment = Payment(
        id=1,
        user_id=1,
        listing_id=1,
        amount=1000.0,
        status="completed",
        payment_method="card",
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    assert payment.amount == 1000.0
    assert payment.status == "completed"


def test_notification_model():
    notification = Notification(
        id=1,
        user_id=1,
        type=NotificationType.INFO,
        title="Test Title",
        message="Test message",
        is_read=False,
        created_at=datetime.utcnow()
    )
    assert notification.message == "Test message"
    assert not notification.is_read


def test_settings_model():
    settings = AppSettings(
        app_name="TestApp",
        theme_mode="DARK",
        debug_mode=True
    )
    assert settings.app_name == "TestApp"
    assert settings.theme_mode == "DARK"