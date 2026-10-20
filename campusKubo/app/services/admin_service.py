# app/services/admin_service.py
from typing import List, Optional, Dict, Tuple
import os
import sys
# Ensure top-level `storage` package is importable when importing from `app.services`
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from storage.db import (
    get_connection,
    deactivate_user as db_deactivate_user,
    activate_user as db_activate_user,
    delete_user as db_delete_user,
    change_listing_status,
    create_user,
    update_user_account,
    update_user_password as db_update_user_password,
)
from models.user import User, UserRole
from models.listing import Listing
from services.refresh_service import notify as _notify_refresh
from services.activity_service import ActivityService

class AdminService:
    """Service for admin-related operations"""

    # ------------------ USER MANAGEMENT ------------------
    def get_all_users(self, role: Optional[UserRole] = None) -> List[User]:
        conn = get_connection()
        cursor = conn.cursor()
        if role:
            cursor.execute("SELECT * FROM users WHERE role=? ORDER BY created_at DESC", (role.value,))
        else:
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [User.from_db_row(row) for row in rows]

    def get_all_users_by_role(self, role_string: str) -> List[User]:
        """Get all users by role (string). Convenience method for UI."""
        try:
            role_enum = UserRole(role_string)
            return self.get_all_users(role_enum)
        except (ValueError, KeyError):
            return []

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return User.from_db_row(row) if row else None

    def deactivate_user(self, admin_id: int, user_id: int) -> bool:
        ok = db_deactivate_user(user_id)
        if ok:
            ActivityService.log_activity(admin_id, "User Deactivated", f"Deactivated user ID {user_id}")
            try:
                _notify_refresh()
            except Exception:
                pass
        return ok

    def activate_user(self, admin_id: int, user_id: int) -> bool:
        ok = db_activate_user(user_id)
        if ok:
            ActivityService.log_activity(admin_id, "User Activated", f"Activated user ID {user_id}")
            try:
                _notify_refresh()
            except Exception:
                pass
        return ok

    def delete_user(self, admin_id: int, user_id: int) -> bool:
        """Permanently remove a user from the database (admin action)."""
        ok = db_delete_user(user_id)
        if ok:
            ActivityService.log_activity(admin_id, "User Deleted", f"Deleted user ID {user_id}")
            try:
                _notify_refresh()
            except Exception:
                pass
        return ok

    def create_user_account(self, admin_id: int, full_name: str, email: str, role: str, password: str, is_active: bool = True) -> tuple[bool, str]:
        """Create a user account as an admin."""
        if not full_name or not email or not role or not password:
            return False, "All fields are required"

        success, msg = create_user(full_name, email, password, role, 1 if is_active else 0)
        if success:
            ActivityService.log_activity(admin_id, "User Created", f"Created user {email} with role {role}")
            try:
                _notify_refresh()
            except Exception:
                pass
        return success, msg

    def update_user_account(self, admin_id: int, user_id: int, full_name: str, email: str, role: str, is_active: bool = True, phone: Optional[str] = None) -> tuple[bool, str]:
        """Update user metadata as an admin."""
        # Capture any stderr output from the DB adapter so we can return a
        # helpful message to the UI instead of a generic failure string.
        import io
        import contextlib
        buf = io.StringIO()
        try:
            with contextlib.redirect_stderr(buf):
                ok = update_user_account(user_id, full_name, email, role, 1 if is_active else 0, phone)
        except Exception as e:
            # If the adapter raised, capture message and return
            msg = str(e)
            return False, msg

        stderr_out = buf.getvalue().strip()
        if ok:
            ActivityService.log_activity(admin_id, "User Updated", f"Updated user ID {user_id}: {full_name}, {email}, role {role}")
            try:
                _notify_refresh()
            except Exception:
                pass
            return True, "User updated successfully"

        # Prefer the adapter's stderr message if present
        if stderr_out:
            return False, stderr_out

        return False, "Failed to update user"

    def reset_user_password(self, admin_id: int, user_id: int, new_password: str) -> tuple[bool, str]:
        """Reset password for a user."""
        if not new_password:
            return False, "Password cannot be empty"
        ok = db_update_user_password(user_id, new_password)
        if ok:
            ActivityService.log_activity(admin_id, "Password Reset", f"Reset password for user ID {user_id}")
            try:
                _notify_refresh()
            except Exception:
                pass
            return True, "Password updated"
        return False, "Failed to update password"

    def approve_pm(self, admin_id: int, user_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_verified=1 WHERE id=? AND role='pm'", (user_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        ok = affected > 0
        if ok:
            ActivityService.log_activity(admin_id, "PM Approved", f"Approved property manager user ID {user_id}")
            try:
                _notify_refresh()
            except Exception:
                pass
        return ok

    def reject_pm(self, admin_id: int, user_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_verified=0 WHERE id=? AND role='pm'", (user_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        ok = affected > 0
        if ok:
            ActivityService.log_activity(admin_id, "PM Rejected", f"Rejected property manager user ID {user_id}")
            try:
                _notify_refresh()
            except Exception:
                pass
        return ok

    # ------------------ LISTING MANAGEMENT ------------------
    def get_all_listings(self, status: Optional[str] = None) -> List[Listing]:
        """Fetch all listings, optionally filtered by status (pending/approved/rejected)"""
        conn = get_connection()
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM listings WHERE status=? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM listings ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [Listing.from_db_row(row) for row in rows]

    def approve_listing(self, listing_id: int) -> bool:
        ok = change_listing_status(listing_id, "approved")
        if ok:
            try:
                _notify_refresh()
            except Exception:
                pass
        return ok

    def reject_listing(self, listing_id: int) -> bool:
        ok = change_listing_status(listing_id, "rejected")
        if ok:
            try:
                _notify_refresh()
            except Exception:
                pass
        return ok

    # ------------------ DASHBOARD ANALYTICS ------------------
    def get_stats(self) -> Dict[str, int]:
        """Return counts of users, listings, reservations, payments"""
        conn = get_connection()
        cursor = conn.cursor()

        stats = {}
        cursor.execute("SELECT COUNT(*) as count FROM users")

        stats['total_users'] = cursor.fetchone()['count']

        # Role matching: DB may store human-friendly role strings like 'PM One' or 'Tenant Two'
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE lower(role) LIKE '%pm%' OR lower(role) LIKE '%property%'")
        stats['total_pms'] = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM users WHERE lower(role) LIKE '%tenant%'")
        stats['total_tenants'] = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM listings")
        stats['total_listings'] = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM listings WHERE status='approved'")
        stats['approved_listings'] = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM listings WHERE status='pending'")
        stats['pending_listings'] = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM reservations")
        stats['total_reservations'] = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM payments")
        stats['total_payments'] = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM reports")
        stats['total_reports'] = cursor.fetchone()['count']

        # Count admin users explicitly so UI can display admins separately
        try:
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE lower(role) LIKE '%admin%'")
            stats['total_admins'] = cursor.fetchone()['count']
        except Exception:
            # Fallback: derive admins by subtracting known roles from total_users
            try:
                stats['total_admins'] = int(stats.get('total_users', 0)) - int(stats.get('total_pms', 0)) - int(stats.get('total_tenants', 0))
            except Exception:
                stats['total_admins'] = 0

        conn.close()
        return stats

    #
    def get_pending_pm_accounts(self) -> List[User]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE (lower(role) LIKE '%pm%' OR lower(role) LIKE '%property%' OR lower(role) LIKE '%manager%') AND is_verified=0 ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [User.from_db_row(row) for row in rows]

    # ------------------ ADDITIONAL HELPERS ------------------
    def get_pending_pm_count(self) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE (lower(role) LIKE '%pm%' OR lower(role) LIKE '%property%' OR lower(role) LIKE '%manager%') AND is_verified=0")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_pending_pm_counts_per_month(self) -> list[tuple[str, int]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT strftime('%Y-%m', created_at) AS month, COUNT(*)
            FROM users
            WHERE (lower(role) LIKE '%pm%' OR lower(role) LIKE '%property%' OR lower(role) LIKE '%manager%') AND is_verified=0
            GROUP BY month ORDER BY month
        """)
        data = cursor.fetchall()
        conn.close()
        return [(row[0], row[1]) for row in data]

    def get_all_users_count(self) -> int:
        return len(self.get_all_users())

    def get_users_count_by_role(self, role: str) -> int:
        # Role can be 'tenant' or 'pm' — perform a DB count using flexible matching
        conn = get_connection()
        cursor = conn.cursor()
        rl = (role or '').lower()
        try:
            if rl == 'pm' or rl == 'property_manager' or rl == 'property':
                cursor.execute("SELECT COUNT(*) FROM users WHERE lower(role) LIKE '%pm%' OR lower(role) LIKE '%property%' OR lower(role) LIKE '%manager%'")
            elif rl == 'tenant':
                cursor.execute("SELECT COUNT(*) FROM users WHERE lower(role) LIKE '%tenant%'")
            else:
                cursor.execute("SELECT COUNT(*) FROM users")
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_all_payments(self):
        """Return recent payments with joined user and listing info."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT p.id, p.user_id, u.email as user_email, p.listing_id, l.address as listing_address,
                       p.amount, p.created_at
                FROM payments p
                LEFT JOIN users u ON p.user_id = u.id
                LEFT JOIN listings l ON p.listing_id = l.id
                ORDER BY p.created_at DESC
            """)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # --------- LISTING MANAGEMENT (Admin) ---------
    def create_listing_admin(self, pm_id: int, address: str, price: float, description: str, lodging_details: str, status: str = "pending") -> Tuple[bool, str, Optional[int]]:
        """Admin can create listings for any PM and set initial status."""
        if not address or not description or price <= 0:
            return False, "Address, description, and price are required", None

        from services.listing_service import ListingService
        success, msg, listing_id = ListingService.create_new_listing(
            pm_id, address, price, description, lodging_details, []
        )
        if success and listing_id and status != "pending":
            ok = change_listing_status(listing_id, status)
            if not ok:
                return False, "Listing created but status update failed", listing_id
        return success, msg, listing_id if success else None

    def update_listing_admin(self, listing_id: int, address: str, price: float, description: str, lodging_details: str, status: str, pm_id: Optional[int] = None) -> Tuple[bool, str]:
        """Admin can update all listing fields including owner and status."""
        from services.listing_service import ListingService
        return ListingService.update_existing_listing_admin(listing_id, address, price, description, lodging_details, status, pm_id)

    # --------- RESERVATION MANAGEMENT (Admin) ---------
    def create_reservation_admin(self, listing_id: int, tenant_id: int, start_date: str, end_date: str, status: str = "pending") -> Tuple[bool, str, Optional[int]]:
        """Admin can create reservations and set status directly."""
        from services.reservation_service import ReservationService
        success, msg, res_id = ReservationService().create_reservation_admin(listing_id, tenant_id, start_date, end_date, status)
        return success, msg, res_id

    def update_reservation_admin(self, reservation_id: int, listing_id: int, tenant_id: int, start_date: str, end_date: str, status: str) -> Tuple[bool, str]:
        """Admin can update all reservation fields."""
        from services.reservation_service import ReservationService
        return ReservationService().update_reservation_admin(reservation_id, listing_id, tenant_id, start_date, end_date, status)

    # --------- PAYMENT MANAGEMENT (Admin) ---------
    def get_all_payments_admin(self, status: Optional[str] = None) -> List[Dict]:
        """Get all payments with optional status filter."""
        from storage.db import get_all_payments_admin
        return get_all_payments_admin(status)

    def process_refund(self, payment_id: int, refund_amount: float, refund_reason: str) -> Tuple[bool, str]:
        """Process a refund for a payment."""
        from storage.db import process_payment_refund
        success, msg = process_payment_refund(payment_id, refund_amount, refund_reason)
        if success:
            try:
                _notify_refresh()
            except Exception:
                pass
        return success, msg

    def update_payment_status(self, payment_id: int, new_status: str, notes: Optional[str] = None) -> Tuple[bool, str]:
        """Update payment status."""
        from storage.db import update_payment_status
        success, msg = update_payment_status(payment_id, new_status, notes)
        if success:
            try:
                _notify_refresh()
            except Exception:
                pass
        return success, msg

    def get_payment_statistics(self) -> Dict:
        """Get payment statistics and insights."""
        from storage.db import get_payment_statistics
        return get_payment_statistics()

    # ------------------ TREND / PERIOD HELPERS ------------------
    def _count_rows_in_period(self, table: str, days: int = 30, offset_days: int = 0, date_column: str = 'created_at', where: str = None) -> int:
        """Count rows in a given table for a period defined by days and optional offset.

        Example: days=30, offset_days=0 => last 30 days; offset_days=30 => 30-60 days ago.
        """
        conn = get_connection()
        cursor = conn.cursor()
        try:
            if offset_days <= 0:
                # current period: from date('now', '-{days} days') to now
                q = f"SELECT COUNT(*) as count FROM {table} WHERE {date_column} >= date('now', '-{days} days')"
            else:
                # previous window: between date('now', '-{offset_days + days} days') and date('now','-{offset_days} days')
                q = f"SELECT COUNT(*) as count FROM {table} WHERE {date_column} >= date('now', '-{offset_days + days} days') AND {date_column} < date('now', '-{offset_days} days')"
            if where:
                q += f" AND ({where})"
            cursor.execute(q)
            row = cursor.fetchone()
            return int(row['count'] if isinstance(row, dict) and 'count' in row else (row[0] if row else 0))
        finally:
            conn.close()

    def get_new_users_count(self, days: int = 30, offset_days: int = 0) -> int:
        return self._count_rows_in_period('users', days=days, offset_days=offset_days, date_column='created_at')

    def get_new_listings_count(self, days: int = 30, offset_days: int = 0, status: str = None) -> int:
        where = None
        if status:
            where = f"status='{status}'"
        return self._count_rows_in_period('listings', days=days, offset_days=offset_days, date_column='created_at', where=where)

    def get_new_reservations_count(self, days: int = 30, offset_days: int = 0) -> int:
        return self._count_rows_in_period('reservations', days=days, offset_days=offset_days, date_column='created_at')

    def get_new_reports_count(self, days: int = 30, offset_days: int = 0) -> int:
        return self._count_rows_in_period('reports', days=days, offset_days=offset_days, date_column='created_at')

    def get_pending_pms_count_period(self, days: int = 30, offset_days: int = 0) -> int:
        # Count pending PM verifications created within the period
        where = "(lower(role) LIKE '%pm%' OR lower(role) LIKE '%property%' OR lower(role) LIKE '%manager%') AND is_verified=0"
        return self._count_rows_in_period('users', days=days, offset_days=offset_days, date_column='created_at', where=where)

    @staticmethod
    def compute_trend(current: int, previous: int, precision: int = 0) -> tuple[int, bool]:
        """Compute an absolute percent change and direction.

        Returns (trend_value, trend_up) where trend_value is an int percent (absolute),
        and trend_up is True when current >= previous.
        When previous == 0 and current > 0, returns 100 (semantic choice).
        """
        try:
            cur = int(current or 0)
            prev = int(previous or 0)
        except Exception:
            return 0, False

        if prev == 0:
            if cur == 0:
                return 0, False
            return 100, True

        delta = cur - prev
        pct = (delta / prev) * 100.0
        rounded = int(round(abs(pct), precision))
        return rounded, (pct >= 0)
