# services/auth_service.py
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from storage.db import (
    validate_user,
    create_user,
    get_user_info,
    create_admin,
    get_user_by_email,
    hash_password,
    create_password_reset_token,
    verify_password_reset_token,
    use_password_reset_token,
    update_user_password
)

class AuthService:
    """Handles user authentication for CampusKubo"""

    # Only these roles can self-register
    ALLOWED_ROLES = ["tenant", "pm"]
    # Validation constants
    PASSWORD_MIN_LENGTH = int(os.getenv('MIN_LENGTH_PASSWORD', '8'))
    PASSWORD_REQUIREMENTS = [
        ("length", lambda p, min_len=PASSWORD_MIN_LENGTH: len(p) >= min_len, f"At least {PASSWORD_MIN_LENGTH} characters"),
        ("digit", lambda p: any(c.isdigit() for c in p), "One number"),
        ("uppercase", lambda p: any(c.isupper() for c in p), "One uppercase letter"),
        ("special", lambda p: any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in p), "One special character"),
    ]

    # Email validation regex
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # -------- VALIDATION METHODS --------
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email format"""
        if not email or not email.strip():
            return False, "Email is required"

        if not re.match(AuthService.EMAIL_PATTERN, email.strip()):
            return False, "Please enter a valid email address"

        return True, "Valid"

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str, list]:
        """
        Validate password meets security requirements.
        Returns (is_valid, message, requirements_status_list)
        """
        if not password:
            return False, "Password is required", []

        status = []
        for req_name, req_func, req_label in AuthService.PASSWORD_REQUIREMENTS:
            is_met = req_func(password)
            status.append({
                "name": req_name,
                "label": req_label,
                "met": is_met
            })

        all_met = all(s["met"] for s in status)
        if not all_met:
            failed = [s["label"] for s in status if not s["met"]]
            return False, f"Password must have: {', '.join(failed)}", status

        return True, "Password is valid", status

    @staticmethod
    def validate_full_name(full_name: str) -> Tuple[bool, str]:
        """Validate full name contains only letters and spaces"""
        if not full_name or not full_name.strip():
            return False, "Full name is required"

        name_pattern = r'^[A-Za-z\s]+$'
        if not re.match(name_pattern, full_name.strip()):
            return False, "Full name can only contain letters and spaces"

        return True, "Valid"

    # -------- AUTH METHODS --------
    # LOGIN
    # -----------------------------
    @staticmethod
    def login(email: str, password: str) -> Optional[dict]:
        """
        Authenticate user (all roles)
        Returns dict: {"id": int, "role": string, "email": string, "full_name": string}
        or None if authentication fails
        """
        if not email or not password:
            return None

        email_clean = email.strip().lower()

        # Use hashed password validation only (secure)
        user = validate_user(email_clean, password)

        if user:
            return {
                "id": user["id"],
                "role": user["role"],
                "email": user.get("email", email_clean),
                "full_name": user.get("full_name", "")
            }

        return None

    # -----------------------------
    # REGISTER
    # -----------------------------
    @staticmethod
    def register(email: str, password: str, role: str, full_name: str = "") -> Tuple[bool, str]:
        """
        Register new user (tenant or pm only)
        Returns (success: bool, message: str)
        """
        # Validate email
        is_valid_email, email_msg = AuthService.validate_email(email)
        if not is_valid_email:
            return False, email_msg

        email_clean = email.strip().lower()

        # Validate password
        is_valid_pwd, pwd_msg, _ = AuthService.validate_password(password)
        if not is_valid_pwd:
            return False, pwd_msg

        # Validate role
        if role not in AuthService.ALLOWED_ROLES:
            return False, f"Cannot register with role '{role}'. Allowed roles: {', '.join(AuthService.ALLOWED_ROLES)}"

        # Validate full name if provided
        if full_name:
            is_valid_name, name_msg = AuthService.validate_full_name(full_name)
            if not is_valid_name:
                return False, name_msg

        # Create user (storage.db.create_user expects full_name, email, password, role)
        success, msg = create_user(
            full_name.strip() if full_name else "",
            email_clean,
            password,
            role,
        )

        if success:
            return True, "Account created successfully"
        return False, msg or "Email already exists or registration failed"

    # -----------------------------
    # GET USER INFO
    # -----------------------------
    @staticmethod
    def get_user_info(user_id: int) -> Optional[dict]:
        return get_user_info(user_id)

    # -----------------------------
    # ADMIN CREATION
    # -----------------------------
    @staticmethod
    def create_admin(email: str, password: str, full_name: str = "Admin User") -> bool:
        email_clean = email.strip().lower()
        existing = get_user_by_email(email_clean)
        if existing:
            return False
        # storage.db.create_admin returns (success: bool, message: str)
        success, _msg = create_admin(email_clean, password, full_name)
        return bool(success)

    @staticmethod
    def ensure_admin_exists(email=None, password=None, full_name="Super Admin"):
        if email is None:
            email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@campuskubo.local')
        if password is None:
            password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'Admin123!')
        from storage.db import get_connection

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE role='admin' LIMIT 1")
        admin_exists = cur.fetchone()
        conn.close()

        if not admin_exists:
            AuthService.create_admin(email, password, full_name)

    # -----------------------------
    # RESET PASSWORD
    # -----------------------------
    @staticmethod
    def reset_password(email: str, new_password: str) -> Tuple[bool, str]:
        """
        Reset user password with validation.
        Returns (success: bool, message: str)
        """
        if not email or not new_password:
            return False, "Email and new password are required"

        # Validate new password
        is_valid, msg, _ = AuthService.validate_password(new_password)
        if not is_valid:
            return False, msg

        email_clean = email.strip().lower()
        user = get_user_by_email(email_clean)

        if not user:
            return False, "User not found"

        # Use the db function which now only stores hashed password
        success = update_user_password(user["id"], new_password)

        if success:
            return True, "Password reset successfully"
        return False, "Failed to reset password"

    # -------- SECURE PASSWORD RECOVERY (Token-Based) --------
    @staticmethod
    def request_password_reset(email: str) -> Tuple[bool, str, Optional[str]]:
        """
        Generate a secure password reset token for the user.

        Returns:
            (success: bool, message: str, token: str or None)

        Usage:
            - User requests "Forgot Password"
            - Call this method to generate token
            - Send token to user via email (e.g., reset link with token as query param)
            - User clicks link and submits new password along with token
            - Call reset_password_with_token() to complete the reset
        """
        if not email or not email.strip():
            return False, "Email is required", None

        email_clean = email.strip().lower()
        user = get_user_by_email(email_clean)

        if not user:
            # For security: don't reveal if user exists
            print(f"[request_password_reset] User not found: {email_clean}")
            return False, "If email exists, a reset link will be sent", None

        try:
            # Generate cryptographically secure token (32 bytes = 256 bits of entropy)
            token = secrets.token_urlsafe(32)

            # Token expires in configured minutes
            expires_at = (datetime.utcnow() + timedelta(minutes=int(os.getenv('PASSWORD_RESET_EXPIRY_MINUTES', '1')))).isoformat()

            # Store token in database
            success = create_password_reset_token(user["id"], token, expires_at)

            if success:
                # Return token so caller can embed in email reset link
                return True, "Password reset request created", token
            else:
                return False, "Failed to create reset token", None

        except Exception as e:
            print(f"[request_password_reset] error for {email_clean}: {e}")
            return False, "An error occurred. Please try again later", None

    @staticmethod
    def reset_password_with_token(token: str, new_password: str) -> Tuple[bool, str]:
        """
        Reset password using a valid reset token.

        Args:
            token: The reset token from user's email link
            new_password: The new password to set

        Returns:
            (success: bool, message: str)

        Usage:
            - User submits password reset form with token and new password
            - Validate token and new password
            - If valid, update password and mark token as used
        """
        if not token or not token.strip():
            return False, "Reset token is required"

        if not new_password:
            return False, "New password is required"

        # Validate new password meets security requirements
        is_valid, msg, _ = AuthService.validate_password(new_password)
        if not is_valid:
            return False, msg

        try:
            # Verify token is valid and get user_id
            user_id = verify_password_reset_token(token)

            if user_id is None:
                return False, "Invalid or expired reset link. Please request a new one"

            # Update password
            success = update_user_password(user_id, new_password)

            if success:
                # Mark token as used so it can't be reused
                use_password_reset_token(token)
                return True, "Password reset successfully. You can now log in."
            else:
                return False, "Failed to update password. Please try again"

        except Exception as e:
            print(f"[reset_password_with_token] error: {e}")
            return False, "An error occurred. Please try again later"
