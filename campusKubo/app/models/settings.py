"""
app/models/settings.py

System Settings Model - Defines all configurable settings for the application.
Supports environment variables, database persistence, and defaults.
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class AppSettings:
    """Core application settings"""
    app_name: str = "CampusKubo"
    app_version: str = "1.0.0"
    theme_mode: str = "LIGHT"  # LIGHT, DARK, AUTO
    language: str = "en"  # en, tl (Tagalog)
    timezone: str = "Asia/Manila"
    debug_mode: bool = False
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSettings':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SecuritySettings:
    """Security-related settings"""
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    password_expiry_days: Optional[int] = None
    session_timeout_minutes: int = 60
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    enable_2fa: bool = False
    require_email_verification: bool = True
    require_pm_document_verification: bool = True
    sql_injection_protection: bool = True
    csrf_protection: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecuritySettings':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PaymentSettings:
    """Payment processing and financial settings"""
    currency_code: str = "PHP"
    currency_symbol: str = "₱"
    payment_methods_enabled: list = field(default_factory=lambda: ["cash", "card", "online_banking"])
    minimum_payment_amount: float = 1000.0
    maximum_payment_amount: float = 1000000.0
    payment_timeout_minutes: int = 30
    enable_refunds: bool = True
    refund_deadline_days: Optional[int] = None  # None = unlimited
    transaction_fee_percentage: float = 0.0
    transaction_fee_fixed: float = 0.0
    enable_payment_notifications: bool = True
    automatic_refund_processing: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaymentSettings':
        # Handle list conversion
        if isinstance(data.get('payment_methods_enabled'), str):
            data['payment_methods_enabled'] = json.loads(data['payment_methods_enabled'])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ListingSettings:
    """Listing and property management settings"""
    listings_per_page: int = 12
    max_images_per_listing: int = 10
    max_image_size_mb: float = 5.0
    require_location_verification: bool = True
    auto_publish_listings: bool = False
    listing_approval_required: bool = True
    enable_featured_listings: bool = True
    featured_listing_cost: float = 500.0
    listing_visibility_radius_km: float = 50.0
    allow_booking_calendar: bool = True
    minimum_lease_duration_days: int = 30
    maximum_lease_duration_days: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ListingSettings':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class NotificationSettings:
    """Notification and communication settings"""
    enable_email_notifications: bool = True
    enable_sms_notifications: bool = False
    enable_in_app_notifications: bool = True
    enable_push_notifications: bool = False
    email_notifications_batch_size: int = 100
    notification_retention_days: int = 90
    enable_weekly_digest: bool = True
    enable_reservation_reminders: bool = True
    reminder_days_before_reservation: int = 1
    enable_payment_notifications: bool = True
    enable_activity_notifications: bool = True
    email_service_provider: str = "smtp"  # smtp, sendgrid, aws_ses

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationSettings':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AdminSettings:
    """Admin dashboard and management settings"""
    items_per_page: int = 10
    enable_activity_logging: bool = True
    activity_log_retention_days: int = 365
    enable_audit_trail: bool = True
    enable_export_data: bool = True
    enable_bulk_operations: bool = True
    require_admin_verification_for_changes: bool = False
    show_system_metrics: bool = True
    enable_performance_monitoring: bool = True
    enable_user_analytics: bool = True
    sensitive_data_masking: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdminSettings':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class FeatureFlags:
    """Feature toggles for gradual rollout and A/B testing"""
    enable_advanced_search: bool = True
    enable_map_view: bool = True
    enable_virtual_tours: bool = False
    enable_instant_booking: bool = False
    enable_reviews_and_ratings: bool = True
    enable_tenant_verification: bool = True
    enable_pm_verification: bool = True
    enable_recommended_listings: bool = True
    enable_bulk_messaging: bool = False
    enable_contract_management: bool = False
    enable_maintenance_requests: bool = False
    enable_payment_plans: bool = False
    enable_referral_program: bool = False
    enable_landlord_insurance: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeatureFlags':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SystemSettings:
    """Master settings container - aggregates all setting categories"""
    # Metadata
    settings_id: str = "default"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    version: int = 1

    # Setting categories
    app: AppSettings = field(default_factory=AppSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    payment: PaymentSettings = field(default_factory=PaymentSettings)
    listing: ListingSettings = field(default_factory=ListingSettings)
    notification: NotificationSettings = field(default_factory=NotificationSettings)
    admin: AdminSettings = field(default_factory=AdminSettings)
    features: FeatureFlags = field(default_factory=FeatureFlags)

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for JSON serialization"""
        return {
            'settings_id': self.settings_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'version': self.version,
            'app': self.app.to_dict(),
            'security': self.security.to_dict(),
            'payment': self.payment.to_dict(),
            'listing': self.listing.to_dict(),
            'notification': self.notification.to_dict(),
            'admin': self.admin.to_dict(),
            'features': self.features.to_dict(),
        }

    def to_json(self) -> str:
        """Convert settings to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemSettings':
        """Reconstruct SystemSettings from dictionary"""
        return cls(
            settings_id=data.get('settings_id', 'default'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            version=data.get('version', 1),
            app=AppSettings.from_dict(data.get('app', {})),
            security=SecuritySettings.from_dict(data.get('security', {})),
            payment=PaymentSettings.from_dict(data.get('payment', {})),
            listing=ListingSettings.from_dict(data.get('listing', {})),
            notification=NotificationSettings.from_dict(data.get('notification', {})),
            admin=AdminSettings.from_dict(data.get('admin', {})),
            features=FeatureFlags.from_dict(data.get('features', {})),
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'SystemSettings':
        """Reconstruct SystemSettings from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def get_setting(self, category: str, key: str, default: Any = None) -> Any:
        """Get a specific setting value using dot notation"""
        if hasattr(self, category):
            category_obj = getattr(self, category)
            if hasattr(category_obj, key):
                return getattr(category_obj, key)
        return default

    def update_setting(self, category: str, key: str, value: Any) -> bool:
        """Update a specific setting value"""
        if hasattr(self, category):
            category_obj = getattr(self, category)
            if hasattr(category_obj, key):
                setattr(category_obj, key, value)
                self.updated_at = datetime.utcnow().isoformat()
                return True
        return False
