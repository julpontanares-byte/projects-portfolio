"""
Session state management with timeout enforcement
"""
from typing import Optional
from datetime import datetime, timedelta
import os
from models.user import User, UserRole


class SessionState:
    """Manages user session state with timeout enforcement"""

    # Session timeout in minutes (configurable via env)
    SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', '60'))

    def __init__(self, page):
        """Initialize session state"""
        self.page = page

    def login(self, user_id: int, email: str, role: str, full_name: str = None or ""):
        """Store user login information and initialize session timeout"""
        self.page.session.set("user_id", user_id)
        self.page.session.set("email", email)
        self.page.session.set("role", role)
        self.page.session.set("full_name", full_name)
        self.page.session.set("is_logged_in", True)
        self._update_last_activity()

    def logout(self):
        """Clear session data"""
        self.page.session.clear()

    def _update_last_activity(self):
        """Update last activity timestamp"""
        self.page.session.set("last_activity", datetime.utcnow().isoformat())

    def _is_session_expired(self) -> bool:
        """Check if session has expired due to inactivity"""
        last_activity_str = self.page.session.get("last_activity")
        if not last_activity_str:
            return True

        try:
            last_activity = datetime.fromisoformat(last_activity_str)
            timeout_delta = timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)
            return datetime.utcnow() > (last_activity + timeout_delta)
        except (ValueError, TypeError):
            return True

    def is_logged_in(self) -> bool:
        """Check if user is logged in and session is not expired"""
        if self.page.session.get("is_logged_in") != True:
            return False

        # Check session timeout
        if self._is_session_expired():
            self.logout()
            return False

        # Update activity on successful check
        self._update_last_activity()
        return True

    def get_user_id(self) -> Optional[int]:
        """Get current user ID"""
        return self.page.session.get("user_id")

    def get_email(self) -> Optional[str]:
        """Get current user email"""
        return self.page.session.get("email")

    def get_role(self) -> Optional[str]:
        """Get current user role"""
        return self.page.session.get("role")

    def get_full_name(self) -> Optional[str]:
        """Get current user full name"""
        return self.page.session.get("full_name")

    def is_tenant(self) -> bool:
        """Check if current user is tenant"""
        return self.get_role() == "tenant"

    def is_property_manager(self) -> bool:
        """Check if current user is property manager"""
        return self.get_role() == "pm"

    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return self.get_role() == "admin"

    def refresh_session(self):
        """Explicitly refresh session activity (call on user interactions)"""
        if self.is_logged_in():
            self._update_last_activity()

    def get_session_time_remaining(self) -> Optional[int]:
        """Get minutes remaining before session timeout"""
        last_activity_str = self.page.session.get("last_activity")
        if not last_activity_str:
            return None

        try:
            last_activity = datetime.fromisoformat(last_activity_str)
            timeout_delta = timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)
            expire_time = last_activity + timeout_delta
            remaining = (expire_time - datetime.utcnow()).total_seconds() / 60
            return max(0, int(remaining))
        except (ValueError, TypeError):
            return None

    def require_auth(self) -> bool:
        """Redirect to login if not authenticated"""
        if not self.is_logged_in():
            self.page.go("/login")
            return False
        return True