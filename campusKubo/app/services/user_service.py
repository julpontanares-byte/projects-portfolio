"""
User service - business logic for user operations
"""
from storage.db import (
    get_connection,
    update_user_profile as db_update_user_profile,
    update_user_password as db_update_user_password,
    update_user_info as db_update_user_info,
    get_user_address as db_get_user_address,
    update_user_address as db_update_user_address,
    update_user_avatar as db_update_user_avatar,
)
from storage.db import get_user_by_id as db_get_user_by_id
from storage.file_storage import save_user_avatar
from models.user import User, UserRole
from typing import Optional, List, Dict, Any
from services.refresh_service import notify as _notify_refresh


class UserService:
    """Handles user-related operations"""

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID"""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, email, full_name, role FROM users WHERE id = ?",
            (user_id,)
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return User.from_db_row(row)

        return None

    @staticmethod
    def get_user_full(user_id: int) -> Optional[Dict[str, Any]]:
        """Return the full DB row for a user as a dict (includes phone and other columns)."""
        return db_get_user_by_id(user_id)

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email"""
        conn = get_connection()
        cursor = conn.cursor()

        email_clean = email.strip().lower()
        cursor.execute(
            "SELECT id, email, full_name, role FROM users WHERE email = ?",
            (email_clean,)
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return User.from_db_row(row)

        return None

    @staticmethod
    def get_all_users(role: Optional[str] = None) -> List[User]:
        """Get all users, optionally filtered by role"""
        conn = get_connection()
        cursor = conn.cursor()

        if role:
            cursor.execute(
                "SELECT id, email, full_name, role FROM users WHERE role = ?",
                (role,)
            )
        else:
            cursor.execute("SELECT id, email, full_name, role FROM users")

        rows = cursor.fetchall()
        conn.close()

        return [User.from_db_row(row) for row in rows]

    @staticmethod
    def update_user_profile(user_id: int, full_name: str) -> bool:
        """Update user profile information"""
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE users SET full_name = ? WHERE id = ?",
                (full_name, user_id)
            )
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                try:
                    _notify_refresh()
                except Exception:
                    pass
        except Exception as e:
            print(f"Error updating user profile: {e}")
            success = False
        finally:
            conn.close()

        return success

    # ------------------------------------------------------------------
    # Adapter-style helpers to align with richer profile flows
    # ------------------------------------------------------------------
    @staticmethod
    def update_user_profile_full(user_id: int, first: str, last: str, gender: str, email: str, phone: str, avatar: str) -> tuple[bool, str]:
        """
        Update user profile with extended signature; gender/avatar are not persisted in current schema.
        """
        full_name = f"{first} {last}".strip()
        # Use the richer update_user_info adapter which updates name, email and phone
        import io
        import contextlib
        buf = io.StringIO()
        try:
            with contextlib.redirect_stderr(buf):
                ok = db_update_user_info(user_id, full_name, email, phone)
        except Exception as e:
            # Fallback and return message
            try:
                fallback_ok = db_update_user_profile(user_id, full_name)
                return fallback_ok, str(e)
            except Exception:
                return False, str(e)

        stderr_out = buf.getvalue().strip()
        if ok:
            return True, "User updated successfully"
        return False, (stderr_out or "Failed to update user")

    @staticmethod
    def get_user_address(user_id: int):
        """Return stored address for a user (or None)."""
        try:
            return db_get_user_address(user_id)
        except Exception:
            return None

    @staticmethod
    def update_user_address(user_id: int, house: str, street: str, brgy: str, city: str) -> bool:
        """Persist user address via DB adapter."""
        try:
            return db_update_user_address(user_id, house, street, brgy, city)
        except Exception:
            return False

    @staticmethod
    def update_user_avatar(user_id: int, avatar_path: str) -> bool:
        """Persist avatar path for user (adds column if necessary)."""
        try:
            # If the provided avatar_path is a local file or data URL, copy/encode it
            stored = save_user_avatar(user_id, avatar_path)
            if stored:
                success = db_update_user_avatar(user_id, stored)
                return stored if success else False
            # fallback: attempt to persist the raw value
            success = db_update_user_avatar(user_id, avatar_path)
            return avatar_path if success else False
        except Exception:
            return False

    @staticmethod
    def update_user_password(user_id: int, new_password: str) -> bool:
        """Update password through db adapter."""
        return db_update_user_password(user_id, new_password)
    # Note: address/avatar adapters and other helpers are provided above