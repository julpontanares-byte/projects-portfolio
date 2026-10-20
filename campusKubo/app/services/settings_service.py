"""
app/services/settings_service.py

Settings Service - Manages application configuration and settings.
Provides centralized access to settings from database, environment, and defaults.
"""

import os
import json
import sys
from typing import Optional, Dict, Any
from datetime import datetime

# Handle imports from parent/sibling modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from storage.db import (
    get_settings as db_get_settings,
    save_settings as db_save_settings,
    reset_settings as db_reset_settings,
    get_all_settings_history
)
from models.settings import (
    SystemSettings,
    AppSettings,
    SecuritySettings,
    PaymentSettings,
    ListingSettings,
    NotificationSettings,
    AdminSettings,
    FeatureFlags
)


class SettingsService:
    """Central service for managing application settings"""

    # Cache settings in memory for performance
    _cache: Optional[SystemSettings] = None
    _cache_loaded: bool = False

    @classmethod
    def initialize(cls) -> None:
        """Initialize settings from database or create defaults"""
        cls.reload_from_database()

    @classmethod
    def reload_from_database(cls) -> SystemSettings:
        """Reload settings from database and refresh cache"""
        settings_dict = db_get_settings()

        if settings_dict:
            cls._cache = SystemSettings.from_dict(settings_dict)
        else:
            # Create default settings
            cls._cache = SystemSettings()
            cls._cache.created_at = datetime.utcnow().isoformat()
            cls._cache.updated_at = datetime.utcnow().isoformat()
            # Save defaults to database
            db_save_settings(cls._cache.to_dict())

        cls._cache_loaded = True
        return cls._cache

    @classmethod
    def get_settings(cls) -> SystemSettings:
        """Get current system settings (from cache)"""
        if not cls._cache_loaded:
            cls.initialize()
        return cls._cache or SystemSettings()

    @classmethod
    def get_setting(cls, category: str, key: str, default: Any = None) -> Any:
        """Get a specific setting value"""
        settings = cls.get_settings()
        return settings.get_setting(category, key, default)

    @classmethod
    def update_setting(cls, category: str, key: str, value: Any) -> tuple[bool, str]:
        """Update a specific setting"""
        settings = cls.get_settings()

        # Validate the update
        if not hasattr(settings, category):
            return False, f"Invalid category: {category}"

        category_obj = getattr(settings, category)
        if not hasattr(category_obj, key):
            return False, f"Invalid setting key: {category}.{key}"

        # Update the setting
        old_value = getattr(category_obj, key)
        try:
            setattr(category_obj, key, value)
            settings.updated_at = datetime.utcnow().isoformat()

            # Persist to database
            db_save_settings(settings.to_dict())

            return True, f"Setting {category}.{key} updated from {old_value} to {value}"
        except Exception as e:
            return False, f"Error updating setting: {str(e)}"

    @classmethod
    def update_settings(cls, updates: Dict[str, Dict[str, Any]]) -> tuple[bool, str]:
        """Update multiple settings at once"""
        settings = cls.get_settings()
        errors = []

        for category, category_updates in updates.items():
            if not hasattr(settings, category):
                errors.append(f"Invalid category: {category}")
                continue

            category_obj = getattr(settings, category)
            for key, value in category_updates.items():
                if not hasattr(category_obj, key):
                    errors.append(f"Invalid key in {category}: {key}")
                    continue

                try:
                    setattr(category_obj, key, value)
                except Exception as e:
                    errors.append(f"Error setting {category}.{key}: {str(e)}")

        if errors:
            return False, "; ".join(errors)

        # Persist all changes
        settings.updated_at = datetime.utcnow().isoformat()
        db_save_settings(settings.to_dict())
        return True, "All settings updated successfully"

    @classmethod
    def reset_to_defaults(cls) -> tuple[bool, str]:
        """Reset all settings to defaults"""
        try:
            db_reset_settings()
            cls._cache = SystemSettings()
            cls._cache.created_at = datetime.utcnow().isoformat()
            cls._cache.updated_at = datetime.utcnow().isoformat()
            db_save_settings(cls._cache.to_dict())
            return True, "Settings reset to defaults successfully"
        except Exception as e:
            return False, f"Error resetting settings: {str(e)}"

    @classmethod
    def get_settings_as_dict(cls) -> Dict[str, Any]:
        """Get all settings as dictionary"""
        return cls.get_settings().to_dict()

    @classmethod
    def get_settings_as_json(cls) -> str:
        """Get all settings as JSON string"""
        return cls.get_settings().to_json()

    @classmethod
    def get_category(cls, category: str) -> Optional[Dict[str, Any]]:
        """Get a specific settings category as dictionary"""
        settings = cls.get_settings()
        if hasattr(settings, category):
            category_obj = getattr(settings, category)
            return category_obj.to_dict()
        return None

    @classmethod
    def get_app_settings(cls) -> AppSettings:
        """Get application settings"""
        return cls.get_settings().app

    @classmethod
    def get_security_settings(cls) -> SecuritySettings:
        """Get security settings"""
        return cls.get_settings().security

    @classmethod
    def get_payment_settings(cls) -> PaymentSettings:
        """Get payment settings"""
        return cls.get_settings().payment

    @classmethod
    def get_listing_settings(cls) -> ListingSettings:
        """Get listing settings"""
        return cls.get_settings().listing

    @classmethod
    def get_notification_settings(cls) -> NotificationSettings:
        """Get notification settings"""
        return cls.get_settings().notification

    @classmethod
    def get_admin_settings(cls) -> AdminSettings:
        """Get admin settings"""
        return cls.get_settings().admin

    @classmethod
    def get_feature_flags(cls) -> FeatureFlags:
        """Get feature flags"""
        return cls.get_settings().features

    @classmethod
    def is_feature_enabled(cls, feature_name: str) -> bool:
        """Check if a specific feature is enabled"""
        features = cls.get_feature_flags()
        return getattr(features, feature_name, False)

    @classmethod
    def get_settings_history(cls, limit: int = 10) -> list:
        """Get settings change history"""
        return get_all_settings_history('default', limit)

    @classmethod
    def validate_settings(cls, settings_dict: Dict[str, Any]) -> tuple[bool, str]:
        """Validate settings structure and values"""
        try:
            SystemSettings.from_dict(settings_dict)
            return True, "Settings valid"
        except Exception as e:
            return False, f"Invalid settings: {str(e)}"

    @classmethod
    def export_settings(cls, filepath: str) -> tuple[bool, str]:
        """Export settings to JSON file"""
        try:
            settings_dict = cls.get_settings_as_dict()
            with open(filepath, 'w') as f:
                json.dump(settings_dict, f, indent=2)
            return True, f"Settings exported to {filepath}"
        except Exception as e:
            return False, f"Error exporting settings: {str(e)}"

    @classmethod
    def import_settings(cls, filepath: str) -> tuple[bool, str]:
        """Import settings from JSON file"""
        try:
            with open(filepath, 'r') as f:
                settings_dict = json.load(f)

            # Validate before importing
            valid, msg = cls.validate_settings(settings_dict)
            if not valid:
                return False, msg

            # Import and save
            db_save_settings(settings_dict)
            cls.reload_from_database()
            return True, f"Settings imported from {filepath}"
        except Exception as e:
            return False, f"Error importing settings: {str(e)}"
