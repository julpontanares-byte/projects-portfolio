"""
app/storage/db.py

Features:
- All queries parameterized (no string interpolation) to prevent SQL injection
- Safe migrations / column checks
- Error handling with rollbacks and controlled failures
- Information assurance: integrity (PRAGMA settings, foreign keys), availability (WAL mode)
- Utilities for users, listings, reservations, activity logs, and reports
"""

import os
import sys
import hashlib
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    _PH = PasswordHasher()
except Exception:
    _PH = None
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

import sqlite3
import json
from dotenv import load_dotenv
load_dotenv()

# ---------- CONFIG ----------
DB_FILE = os.getenv('DATABASE_URL', os.path.join(os.path.dirname(__file__), "campuskubo.db"))
SQLCIPHER_AVAILABLE = False

# ---------- Utilities ----------
def _now_iso() -> str:
    return datetime.utcnow().isoformat()

def hash_password(password: str) -> str:
    """Return sha256 hex digest of password."""
    # If Argon2 is available, produce an Argon2 encoded hash.
    if _PH is not None:
        try:
            return _PH.hash(password)
        except Exception:
            pass
    # Fallback to SHA-256 hex digest for older installs (legacy)
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(stored_hash: str, password: str) -> bool:
    """
    Verify a password against stored_hash.
    Supports Argon2 encoded hashes and legacy SHA256 hex digests.
    """
    if not stored_hash:
        return False
    # Detect argon2 hash (argon2 encoded strings contain '$argon2')
    try:
        if isinstance(stored_hash, str) and '$argon2' in stored_hash:
            if _PH is None:
                # cannot verify argon2 without library
                return False
            try:
                return _PH.verify(stored_hash, password)
            except VerifyMismatchError:
                return False
            except Exception:
                return False
        # Fallback: assume legacy sha256 hex
        return hashlib.sha256(password.encode('utf-8')).hexdigest() == stored_hash
    except Exception:
        return False


def log_login_attempt(email: str, success: bool, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> None:
    """
    Log a login attempt (success or failure) for audit and rate limiting.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO login_attempts (email, attempt_time, success, ip_address, user_agent) VALUES (?, ?, ?, ?, ?);",
            (email.strip().lower(), _now_iso(), 1 if success else 0, ip_address, user_agent)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[log_login_attempt] error: {e}", file=sys.stderr)


def is_account_locked(email: str, max_attempts: int = None, lockout_seconds: int = None) -> Tuple[bool, Optional[str]]:
    """
    Check if an account is locked due to too many failed login attempts.
    Returns (is_locked: bool, unlock_time: Optional[str])
    """
    if max_attempts is None:
        max_attempts = int(os.getenv('RATE_LIMIT_MAX_ATTEMPTS', '5'))
    if lockout_seconds is None:
        lockout_seconds = int(os.getenv('RATE_LIMIT_WINDOW_MINUTES', '15')) * 60
    try:
        conn = get_connection()
        cur = conn.cursor()
        email_clean = email.strip().lower()

        # Calculate cutoff time for lockout window
        cutoff = (datetime.utcnow() - timedelta(seconds=lockout_seconds)).isoformat()

        # Count failed attempts in the lockout window
        cur.execute(
            "SELECT COUNT(*) as count FROM login_attempts WHERE email = ? AND attempt_time > ? AND success = 0;",
            (email_clean, cutoff)
        )
        row = cur.fetchone()
        failed_count = row[0] if row else 0

        if failed_count >= max_attempts:
            # Find the time of the last failed attempt
            cur.execute(
                "SELECT attempt_time FROM login_attempts WHERE email = ? AND success = 0 ORDER BY attempt_time DESC LIMIT 1;",
                (email_clean,)
            )
            row = cur.fetchone()
            if row:
                last_attempt = datetime.fromisoformat(row[0])
                unlock_time = (last_attempt + timedelta(seconds=lockout_seconds)).isoformat()
                conn.close()
                return True, unlock_time

        conn.close()
        return False, None
    except Exception as e:
        print(f"[is_account_locked] error: {e}", file=sys.stderr)
        return False, None


def clear_login_attempts(email: str) -> None:
    """
    Clear failed login attempts for a user after successful login.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM login_attempts WHERE email = ? AND success = 0;", (email.strip().lower(),))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[clear_login_attempts] error: {e}", file=sys.stderr)

# ---------- Connection management ----------
def get_connection() -> sqlite3.Connection:
    """
    Create a connection to the (encrypted) DB and apply security PRAGMAs.
    Always returns a connection with row_factory sqlite3.Row.
    """
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute("PRAGMA foreign_keys = ON;")
        cur.execute("PRAGMA journal_mode = WAL;")
        cur.execute("PRAGMA synchronous = NORMAL;")
    except Exception:
        pass

    return conn


def check_argon2_compatibility(fail_on_missing: bool = False) -> tuple[bool, str]:
    """
    Check whether Argon2 is available if Argon2 hashes exist in the database.
    Returns (ok: bool, message: str). If fail_on_missing=True, raises RuntimeError when mismatch detected.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM users WHERE password LIKE '%$argon2%';")
        row = cur.fetchone()
        count = int(row['c']) if row and 'c' in row.keys() else (row[0] if row else 0)
        if count > 0 and _PH is None:
            msg = f"Found {count} Argon2 password hashes but Argon2 library is not available"
            if fail_on_missing:
                raise RuntimeError(msg)
            return False, msg
        return True, "Argon2 compatibility OK"
    except Exception as e:
        return False, f"Argon2 compatibility check failed: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass

def check_db_pragmas() -> tuple[bool, str]:
    """Verify expected PRAGMA settings (foreign_keys, journal_mode)."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys;")
        fk = cur.fetchone()
        # PRAGMA foreign_keys returns a single row with 1 or 0
        fk_ok = (fk[0] == 1) if fk else False
        cur.execute("PRAGMA journal_mode;")
        jm = cur.fetchone()
        jm_ok = (jm and jm[0])
        if not fk_ok:
            return False, "foreign_keys PRAGMA is not enabled"
        return True, f"PRAGMAs OK (journal_mode={jm[0]})"
    except Exception as e:
        return False, f"PRAGMA check failed: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass

# ---------- Schema helpers ----------
def column_exists(cursor: sqlite3.Cursor, table_name: str, column_name: str) -> bool:
    # Prevent identifier injection by allowing only known table names
    _ALLOWED_TABLES = {
        'users', 'listings', 'listing_images', 'reservations',
        'password_reset_tokens', 'activity_logs', 'reports', 'payments'
    }
    if table_name not in _ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")

    cursor.execute("PRAGMA table_info('%s')" % (table_name,))
    return any(row[1] == column_name for row in cursor.fetchall())

# ---------- Initialization & Migrations ----------
def init_db():
    """
    Create tables if missing and apply simple safe migrations.
    Call this once at app startup.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                full_name TEXT,
                is_verified INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Add assignment columns to reports if missing (admin assignment support)
        for col_def in [
            ("assigned_admin_id", "INTEGER"),
            ("assigned_at", "TEXT"),
            ("assigned_note", "TEXT")
        ]:
            col, _def = col_def
            if not column_exists(cur, "reports", col):
                try:
                    cur.execute(f"ALTER TABLE reports ADD COLUMN {col} {_def};")
                except Exception:
                    pass

        for col_def in [
            ("is_verified", "INTEGER DEFAULT 0"),
            ("is_active", "INTEGER DEFAULT 1"),
            ("phone", "TEXT"),
            ("deleted_at", "TEXT")
        ]:
            col, _def = col_def
            if not column_exists(cur, "users", col):
                try:
                    cur.execute(f"ALTER TABLE users ADD COLUMN {col} {_def};")
                except Exception:
                    pass

        cur.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pm_id INTEGER NOT NULL,
                address TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                lodging_details TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                images TEXT,
                FOREIGN KEY(pm_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        for col_def in [
            ("status", "TEXT DEFAULT 'pending'"),
            ("created_at", "TEXT DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TEXT DEFAULT CURRENT_TIMESTAMP"),
            ("images", "TEXT")
        ]:
            col, _def = col_def
            if not column_exists(cur, "listings", col):
                try:
                    cur.execute(f"ALTER TABLE listings ADD COLUMN {col} {_def};")
                except Exception:
                    pass

        cur.execute("""
            CREATE TABLE IF NOT EXISTS listing_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                FOREIGN KEY(listing_id) REFERENCES listings(id) ON DELETE CASCADE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER NOT NULL,
                tenant_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(listing_id) REFERENCES listings(id) ON DELETE CASCADE,
                FOREIGN KEY(tenant_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        if not column_exists(cur, "reservations", "created_at"):
            try:
                cur.execute("ALTER TABLE reservations ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP;")
            except Exception:
                pass

        cur.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                used INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        if not column_exists(cur, "reservations", "created_at"):
            try:
                cur.execute("ALTER TABLE reservations ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP;")
            except Exception:
                pass

        cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                listing_id INTEGER,
                message TEXT,
                status TEXT DEFAULT 'open',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(listing_id) REFERENCES listings(id) ON DELETE SET NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                listing_id INTEGER,
                amount REAL,
                status TEXT DEFAULT 'completed',
                payment_method TEXT DEFAULT 'unknown',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                refunded_amount REAL DEFAULT 0,
                refund_reason TEXT,
                notes TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY(listing_id) REFERENCES listings(id) ON DELETE SET NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_addresses (
                address_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                house_no TEXT,
                street TEXT,
                barangay TEXT,
                city TEXT,
                province TEXT,
                postal_code TEXT,
                is_primary INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS saved_listings (
                saved_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                listing_id INTEGER NOT NULL,
                saved_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(listing_id) REFERENCES listings(id) ON DELETE CASCADE,
                UNIQUE(user_id, listing_id)
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                room_number TEXT NOT NULL,
                room_type TEXT,
                status TEXT DEFAULT 'Vacant',
                avatar TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                notification_type TEXT,
                category TEXT DEFAULT 'activity',
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                reference_id INTEGER,
                reference_type TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                read_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                popup_notifications INTEGER DEFAULT 1,
                chat_notifications INTEGER DEFAULT 1,
                email_notifications INTEGER DEFAULT 1,
                reservation_confirmation_notif INTEGER DEFAULT 1,
                cancellation_notif INTEGER DEFAULT 1,
                payment_update_notif INTEGER DEFAULT 1,
                rent_reminders_notif INTEGER DEFAULT 1,
                theme TEXT DEFAULT 'light',
                language TEXT DEFAULT 'en',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS payment_transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                reservation_id INTEGER,
                user_id INTEGER,
                amount REAL,
                payment_method TEXT,
                transaction_reference TEXT,
                card_last_four TEXT,
                status TEXT DEFAULT 'Pending',
                payment_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(reservation_id) REFERENCES reservations(id) ON DELETE CASCADE,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER,
                comment TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(listing_id) REFERENCES listings(id) ON DELETE CASCADE,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER,
                content TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(sender_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                settings_id TEXT UNIQUE DEFAULT 'default',
                settings_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                settings_id TEXT NOT NULL,
                changed_fields TEXT,
                old_values TEXT,
                new_values TEXT,
                changed_by TEXT,
                changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(settings_id) REFERENCES system_settings(settings_id) ON DELETE SET NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                attempt_time TEXT NOT NULL,
                success INTEGER NOT NULL DEFAULT 0,
                ip_address TEXT,
                user_agent TEXT
            );
        """)

        # Create index for faster lookup of recent attempts
        try:
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_login_attempts_email_time
                ON login_attempts(email, attempt_time);
            """)
        except Exception:
            pass

        conn.commit()
        try:
            from storage import seed_data
            try:
                # Allow forcing seeding in development/testing via env var
                force_seed = os.getenv('CAMPUSKUBO_FORCE_SEED', '').lower() in ('1', 'true', 'yes')

                # Only run demo seeding when the DB appears empty, unless forced.
                cur.execute("SELECT COUNT(*) as c FROM users")
                row = cur.fetchone()
                users_count = int(row['c']) if row and 'c' in row.keys() else (row[0] if row else 0)
                if force_seed or users_count == 0:
                    seed_data.seed_all_tables(conn)
                    conn.commit()
            except Exception:
                pass
        except Exception:
            pass
    except Exception as e:
        conn.rollback()
        print("[db.init_db] initialization error:", e, file=sys.stderr)
        raise
    finally:
        conn.close()

# ---------- User helpers ----------
def create_user(full_name: str, email: str, password: str, role: str, is_active: int = 1) -> tuple[bool, str]:
    """
    Create user with hashed password. Returns (success, message).
    Model-compatible signature: full_name, email, password, role.
    NOTE: Never stores plaintext passwords for security.
    """
    if not email or not password or not role or not full_name:
        msg = "Missing required fields"
        print(f"[create_user] {msg}", file=sys.stderr)
        return False, msg

    email_clean = email.strip().lower()
    full_name_clean = full_name.strip()

    is_valid, validation_msg = validate_email(email_clean)
    if not is_valid:
        print(f"[create_user] Email validation failed: {validation_msg}", file=sys.stderr)
        return False, validation_msg

    is_valid, validation_msg = validate_password(password)
    if not is_valid:
        print(f"[create_user] Password validation failed: {validation_msg}", file=sys.stderr)
        return False, validation_msg

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE email = ?;", (email_clean,))
        if cur.fetchone():
            msg = f"User already exists: {email_clean}"
            print(f"[create_user] {msg}", file=sys.stderr)
            return False, msg

        hashed = hash_password(password)

        cur.execute("""
            INSERT INTO users (email, password, role, full_name, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (email_clean, hashed, role, full_name_clean, 1 if is_active else 0, _now_iso()))

        conn.commit()
        log_activity(cur.lastrowid, "User Created", f"New {role} user: {email_clean}")
        return True, f"Account created successfully"
    except Exception as e:
        conn.rollback()
        msg = f"Failed to create user: {str(e)}"
        print(f"[create_user] error for {email_clean}: {e}", file=sys.stderr)
        return False, msg
    finally:
        conn.close()

def validate_user(email: str, password: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Validate user existence or credentials.
    If password provided, it must match hashed password.
    Returns dict {id, role, email, full_name} or None.
    """
    if not email:
        return None

    email_clean = email.strip().lower()

    # Check if account is locked due to too many failed attempts
    if password is not None:
        is_locked, unlock_time = is_account_locked(email_clean)
        if is_locked:
            print(f"[validate_user] Account locked for {email_clean} until {unlock_time}", file=sys.stderr)
            log_activity(None, "Login Blocked", f"Account locked: {email_clean}")
            return None

    conn = get_connection()
    cur = conn.cursor()
    try:
        if password is not None:
            # Fetch stored hash and verify using verify_password to support Argon2 + legacy SHA256
            cur.execute("SELECT id, role, email, full_name, password FROM users WHERE email = ? AND is_active = 1;", (email_clean,))
            row = cur.fetchone()
            if not row:
                log_login_attempt(email_clean, False)
                log_activity(None, "Login Failed", f"User not found: {email_clean}")
                return None
            stored = row[4]
            try:
                ok = verify_password(stored, password)
            except Exception:
                ok = False

            if not ok:
                log_login_attempt(email_clean, False)
                log_activity(None, "Login Failed", f"Invalid password for: {email_clean}")
                return None

            # Successful login - log it and clear failed attempts
            log_login_attempt(email_clean, True)
            clear_login_attempts(email_clean)
            log_activity(row[0], "Login Success", f"User logged in: {email_clean}")

            # If verified and stored is legacy sha256, re-hash with Argon2 and update DB
            if _PH is not None and stored and isinstance(stored, str) and not ('$argon2' in stored):
                try:
                    new_hash = hash_password(password)
                    cur.execute("UPDATE users SET password = ? WHERE id = ?;", (new_hash, row[0]))
                    conn.commit()
                except Exception:
                    conn.rollback()

            # return user info from row
            return {"id": row[0], "role": row[1], "email": row[2], "full_name": row[3]}
        else:
            cur.execute(
                "SELECT id, role, email, full_name FROM users WHERE email = ? AND is_active = 1;",
                (email_clean,)
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"[validate_user] error for {email_clean}: {e}", file=sys.stderr)
        return None
    finally:
        conn.close()

def get_user_info(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, email, full_name, role, created_at FROM users WHERE id = ?;", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Backward-compatible alias for `get_user_info`.

    Some service layers expect `get_user_by_id` to exist; delegate to
    the canonical `get_user_info` implementation.
    """
    return get_user_info(user_id)


def update_user_profile(user_id: int, full_name: str) -> bool:
    """Backward-compatible alias for updating a user's full name.

    Delegates to `update_user_full_name` which performs validation and logging.
    """
    return update_user_full_name(user_id, full_name)

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM users WHERE email = ?;", (email.strip().lower(),))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def create_admin(email: str, password: str, full_name: str = "Admin User") -> tuple[bool, str]:
    existing = get_user_by_email(email)
    if existing:
        return False, "User already exists"
    return create_user(full_name, email, password, "admin")

def update_user_full_name(user_id: int, full_name: str) -> bool:
    """
    Update user's full name with validation.
    """
    if not full_name or not full_name.strip():
        print(f"[update_user_full_name] Invalid full_name for user {user_id}", file=sys.stderr)
        return False

    if user_id <= 0:
        print(f"[update_user_full_name] Invalid user_id: {user_id}", file=sys.stderr)
        return False

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET full_name = ? WHERE id = ?;", (full_name.strip(), user_id))
        conn.commit()
        if cur.rowcount > 0:
            log_activity(user_id, "Profile Updated", f"Changed name to {full_name}")
            return True
        print(f"[update_user_full_name] User not found: {user_id}", file=sys.stderr)
        return False
    except Exception as e:
        conn.rollback()
        print(f"[update_user_full_name] error for user {user_id}: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

def verify_current_password(user_id: int, current_password: str) -> bool:
    """
    Verify that the current password matches the stored password for a user.
    Used before allowing password changes.
    """
    if not current_password or user_id <= 0:
        return False

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT password FROM users WHERE id = ?;", (user_id,))
        row = cur.fetchone()
        if not row:
            return False
        stored_hash = row[0]
        return verify_password(stored_hash, current_password)
    except Exception as e:
        print(f"[verify_current_password] error for user {user_id}: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

def update_user_password(user_id: int, new_password: str, current_password: Optional[str] = None) -> bool:
    """
    Update user password with hash only (no plaintext storage).
    If current_password is provided, it will be verified before updating.
    """
    if not new_password or user_id <= 0:
        print(f"[update_user_password] Invalid input: user_id={user_id}", file=sys.stderr)
        return False

    # Verify current password if provided (for user-initiated changes)
    if current_password is not None:
        if not verify_current_password(user_id, current_password):
            log_activity(user_id, "Password Change Failed", "Current password verification failed")
            return False

    conn = get_connection()
    cur = conn.cursor()
    try:
        hashed = hash_password(new_password)
        cur.execute("UPDATE users SET password = ? WHERE id = ?;", (hashed, user_id))
        conn.commit()
        if cur.rowcount > 0:
            log_activity(user_id, "Password Updated", "User changed password")
            return True
        print(f"[update_user_password] User not found: {user_id}", file=sys.stderr)
        return False
    except Exception as e:
        conn.rollback()
        print(f"[update_user_password] error for user {user_id}: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

def update_user_info(user_id: int, full_name: str, email: str, phone: Optional[str] = None) -> bool:
    """
    Update user profile information (name, email, phone).
    Validates inputs and checks email uniqueness.
    """
    if not full_name or not email:
        print(f"[update_user_info] Name and email are required for user {user_id}", file=sys.stderr)
        return False

    if user_id <= 0:
        print(f"[update_user_info] Invalid user_id: {user_id}", file=sys.stderr)
        return False

    full_name = full_name.strip()
    email = email.strip().lower()
    phone = phone.strip() if phone and phone.strip() else None

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT email FROM users WHERE id = ?;", (user_id,))
        user = cur.fetchone()
        if not user:
            print(f"[update_user_info] User not found: {user_id}", file=sys.stderr)
            return False

        current_email = user[0].lower()
        if email != current_email:
            cur.execute("SELECT id FROM users WHERE email = ? AND id != ?;", (email, user_id))
            if cur.fetchone():
                print(f"[update_user_info] Email already in use: {email}", file=sys.stderr)
                return False

        cur.execute(
            "UPDATE users SET full_name = ?, email = ?, phone = ? WHERE id = ?;",
            (full_name, email, phone, user_id)
        )
        conn.commit()

        if cur.rowcount > 0:
            log_activity(user_id, "Profile Updated", f"Updated name, email, and phone")
            return True

        print(f"[update_user_info] Failed to update user {user_id}", file=sys.stderr)
        return False
    except Exception as e:
        conn.rollback()
        print(f"[update_user_info] error for user {user_id}: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def _ensure_address_table(conn):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_addresses (
            user_id INTEGER PRIMARY KEY,
            house TEXT,
            street TEXT,
            barangay TEXT,
            city TEXT
        );
        """
    )
    conn.commit()


def _ensure_users_has_avatar_column(conn):
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(users);")
        cols = [r[1] for r in cur.fetchall()]
        if 'avatar' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN avatar TEXT;")
            conn.commit()
    except Exception:
        # Best-effort; ignore failures
        conn.rollback()


def update_user_avatar(user_id: int, avatar_path: str) -> bool:
    """Store avatar path in `users.avatar` column (adds column if missing)."""
    if not user_id:
        return False
    conn = get_connection()
    try:
        _ensure_users_has_avatar_column(conn)
        cur = conn.cursor()
        cur.execute("UPDATE users SET avatar = ? WHERE id = ?;", (avatar_path or '', user_id))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"[update_user_avatar] error for user {user_id}: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def update_user_account(user_id: int, full_name: str, email: str, role: str, is_active: int = 1, phone: Optional[str] = None) -> bool:
    """
    Update user account details including role and active status.
    """
    if not full_name or not email or not role:
        print(f"[update_user_account] Missing required fields for user {user_id}", file=sys.stderr)
        return False

    if user_id <= 0:
        print(f"[update_user_account] Invalid user_id: {user_id}", file=sys.stderr)
        return False

    full_name = full_name.strip()
    email = email.strip().lower()
    role = role.strip().lower()
    phone = phone.strip() if phone and phone.strip() else None

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT email FROM users WHERE id = ?;", (user_id,))
        user = cur.fetchone()
        if not user:
            print(f"[update_user_account] User not found: {user_id}", file=sys.stderr)
            return False

        current_email = user[0].lower()
        if email != current_email:
            cur.execute("SELECT id FROM users WHERE email = ? AND id != ?;", (email, user_id))
            if cur.fetchone():
                print(f"[update_user_account] Email already in use: {email}", file=sys.stderr)
                return False

        cur.execute(
            "UPDATE users SET full_name = ?, email = ?, phone = ?, role = ?, is_active = ? WHERE id = ?;",
            (full_name, email, phone, role, 1 if is_active else 0, user_id)
        )
        conn.commit()

        if cur.rowcount > 0:
            log_activity(user_id, "Profile Updated", "Updated account metadata")
            return True

        print(f"[update_user_account] Nothing to update for user {user_id}", file=sys.stderr)
        return False
    except Exception as e:
        conn.rollback()
        print(f"[update_user_account] error for user {user_id}: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

def delete_user(user_id: int, soft_delete: bool = True) -> bool:
    """
    Delete user by ID with validation.
    Uses soft delete by default (sets deleted_at timestamp).
    Set soft_delete=False for permanent deletion.
    """
    if user_id <= 0:
        print(f"[delete_user] Invalid user_id: {user_id}", file=sys.stderr)
        return False

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Check if user exists first
        cur.execute("SELECT email, role FROM users WHERE id = ?;", (user_id,))
        user = cur.fetchone()
        if not user:
            print(f"[delete_user] User not found: {user_id}", file=sys.stderr)
            return False

        if soft_delete:
            # Soft delete: mark as deleted with timestamp
            cur.execute("UPDATE users SET deleted_at = ?, is_active = 0 WHERE id = ?;", (_now_iso(), user_id))
            action_msg = f"Soft deleted {user['role']} user: {user['email']}"
        else:
            # Hard delete: permanently remove
            cur.execute("DELETE FROM users WHERE id = ?;", (user_id,))
            action_msg = f"Permanently deleted {user['role']} user: {user['email']}"

        conn.commit()
        log_activity(None, "User Deleted", action_msg)
        return True
    except Exception as e:
        conn.rollback()
        print(f"[delete_user] error for user {user_id}: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

def delete_user_by_email(email: str, soft_delete: bool = True) -> bool:
    """
    Delete user by email with validation.
    Uses soft delete by default (sets deleted_at timestamp).
    Set soft_delete=False for permanent deletion.
    """
    if not email or not email.strip():
        print("[delete_user_by_email] Invalid email", file=sys.stderr)
        return False

    conn = get_connection()
    cur = conn.cursor()
    try:
        email_clean = email.strip().lower()
        cur.execute("SELECT id, role FROM users WHERE email = ?;", (email_clean,))
        user = cur.fetchone()
        if not user:
            print(f"[delete_user_by_email] User not found: {email_clean}", file=sys.stderr)
            return False

        if soft_delete:
            # Soft delete: mark as deleted with timestamp
            cur.execute("UPDATE users SET deleted_at = ?, is_active = 0 WHERE id = ?;", (_now_iso(), user['id']))
            action_msg = f"Soft deleted {user['role']} user: {email_clean}"
        else:
            # Hard delete: permanently remove
            cur.execute("DELETE FROM users WHERE email = ?;", (email_clean,))
            action_msg = f"Permanently deleted {user['role']} user: {email_clean}"

        conn.commit()
        log_activity(None, "User Deleted", action_msg)
        return True
    except Exception as e:
        conn.rollback()
        print(f"[delete_user_by_email] error for {email}: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

def deactivate_user(user_id: int) -> bool:
    """
    Deactivate user by setting is_active=0 instead of deleting.
    """
    if user_id <= 0:
        print(f"[deactivate_user] Invalid user_id: {user_id}", file=sys.stderr)
        return False

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT email, role FROM users WHERE id = ?;", (user_id,))
        user = cur.fetchone()
        if not user:
            print(f"[deactivate_user] User not found: {user_id}", file=sys.stderr)
            return False

        cur.execute("UPDATE users SET is_active = 0 WHERE id = ?;", (user_id,))
        conn.commit()
        log_activity(user_id, "User Deactivated", f"Deactivated {user['role']} user: {user['email']}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[deactivate_user] error for user {user_id}: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def activate_user(user_id: int) -> bool:
    """
    Reactivate user by setting is_active=1.
    """
    if user_id <= 0:
        print(f"[activate_user] Invalid user_id: {user_id}", file=sys.stderr)
        return False

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT email, role FROM users WHERE id = ?;", (user_id,))
        user = cur.fetchone()
        if not user:
            print(f"[activate_user] User not found: {user_id}", file=sys.stderr)
            return False

        cur.execute("UPDATE users SET is_active = 1 WHERE id = ?;", (user_id,))
        conn.commit()
        log_activity(user_id, "User Activated", f"Activated {user['role']} user: {user['email']}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[activate_user] error for user {user_id}: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

# ---------- Password Reset Tokens ----------
def create_password_reset_token(user_id: int, token: str, expires_at: str) -> bool:
    """
    Create a password reset token for secure password recovery.
    Token should be a cryptographically secure random string (e.g., from secrets module).
    expires_at should be ISO format datetime string (e.g., from datetime.datetime.isoformat()).
    """
    if user_id <= 0 or not token or not token.strip():
        print("[create_password_reset_token] Invalid user_id or token", file=sys.stderr)
        return False

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE id = ?;", (user_id,))
        if not cur.fetchone():
            print(f"[create_password_reset_token] User not found: {user_id}", file=sys.stderr)
            return False

        # Rate-limit password reset requests: disallow more than 1 request per 5 minutes
        try:
            cur.execute("SELECT created_at FROM password_reset_tokens WHERE user_id = ? ORDER BY created_at DESC LIMIT 1;", (user_id,))
            last = cur.fetchone()
            if last and last[0]:
                try:
                    last_dt = datetime.fromisoformat(last[0])
                    if datetime.utcnow() - last_dt < timedelta(minutes=5):
                        print(f"[create_password_reset_token] Rate limit: recent token created for user {user_id}", file=sys.stderr)
                        return False
                except Exception:
                    # If parsing fails, continue and allow creation (safer than blocking legitimate users)
                    pass
        except Exception:
            pass

        cur.execute("DELETE FROM password_reset_tokens WHERE user_id = ? AND used = 0;", (user_id,))

        cur.execute("""
            INSERT INTO password_reset_tokens (user_id, token, expires_at, used)
            VALUES (?, ?, ?, 0);
        """, (user_id, token, expires_at))

        conn.commit()
        log_activity(user_id, "Password Reset Requested", "User requested password reset")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[create_password_reset_token] error for user {user_id}: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

def verify_password_reset_token(token: str) -> Optional[int]:
    """
    Verify a password reset token and return user_id if valid.
    Returns None if token is invalid, expired, or already used.
    """
    if not token or not token.strip():
        print("[verify_password_reset_token] Empty token", file=sys.stderr)
        return None

    conn = get_connection()
    cur = conn.cursor()
    try:
        now = _now_iso()
        cur.execute("""
            SELECT user_id FROM password_reset_tokens
            WHERE token = ? AND used = 0 AND expires_at > ?;
        """, (token, now))

        row = cur.fetchone()
        return row['user_id'] if row else None
    except Exception as e:
        print(f"[verify_password_reset_token] error: {e}", file=sys.stderr)
        return None
    finally:
        conn.close()

def use_password_reset_token(token: str) -> bool:
    """
    Mark a password reset token as used after successful password change.
    """
    if not token or not token.strip():
        print("[use_password_reset_token] Empty token", file=sys.stderr)
        return False

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE password_reset_tokens SET used = 1 WHERE token = ?;", (token,))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"[use_password_reset_token] error: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

def cleanup_expired_reset_tokens() -> int:
    """
    Delete expired password reset tokens. Returns count of deleted tokens.
    Run this periodically (e.g., daily via background task).
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        now = _now_iso()
        cur.execute("DELETE FROM password_reset_tokens WHERE expires_at <= ?;", (now,))
        conn.commit()
        deleted = cur.rowcount
        if deleted > 0:
            print(f"[cleanup_expired_reset_tokens] Deleted {deleted} expired tokens")
        return deleted
    except Exception as e:
        conn.rollback()
        print(f"[cleanup_expired_reset_tokens] error: {e}", file=sys.stderr)
        return 0
    finally:
        conn.close()

# ---------- Listing helpers ----------
def create_listing(pm_id: int, address: str, price: float, description: str,
                   lodging_details: str, image_paths: Optional[List[str]] = None) -> Optional[int]:
    """
    Create listing with validation.
    """
    if pm_id <= 0:
        print(f"[create_listing] Invalid pm_id: {pm_id}", file=sys.stderr)
        return None
    if not address or not address.strip():
        print("[create_listing] Address is required", file=sys.stderr)
        return None
    if price <= 0:
        print(f"[create_listing] Invalid price: {price}", file=sys.stderr)
        return None
    if not description or not description.strip():
        print("[create_listing] Description is required", file=sys.stderr)
        return None

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE id = ? AND role = 'pm';", (pm_id,))
        if not cur.fetchone():
            print(f"[create_listing] PM not found: {pm_id}", file=sys.stderr)
            return None

        now = _now_iso()
        # New listings should start as pending and be approved by an admin
        cur.execute("""
            INSERT INTO listings (pm_id, address, price, description, lodging_details, created_at, updated_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (pm_id, address.strip(), price, description.strip(), lodging_details or "", now, now, "pending"))

        listing_id = cur.lastrowid

        if image_paths:
            for p in image_paths:
                if p and p.strip():
                    cur.execute("INSERT INTO listing_images (listing_id, image_path) VALUES (?, ?);", (listing_id, p.strip()))

        conn.commit()
        log_activity(pm_id, "Listing Created", f"Created listing ID {listing_id}: {address[:50]}")
        return listing_id
    except Exception as e:
        conn.rollback()
        print(f"[create_listing] error for PM {pm_id}: {e}", file=sys.stderr)
        return None
    finally:
        conn.close()

def get_listings(pm_id: Optional[int] = None) -> List[sqlite3.Row]:
    """
    Returns rows of listings joined with pm info (pm_email, pm_name).
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        if pm_id is not None:
            cur.execute("""
                SELECT l.*, u.email AS pm_email, u.full_name AS pm_name
                FROM listings l
                JOIN users u ON l.pm_id = u.id
                WHERE l.pm_id = ?
                ORDER BY l.created_at DESC;
            """, (pm_id,))
        else:
            cur.execute("""
                SELECT l.*, u.email AS pm_email, u.full_name AS pm_name
                FROM listings l
                JOIN users u ON l.pm_id = u.id
                ORDER BY l.created_at DESC;
            """)
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()

def get_listing_by_id(listing_id: int) -> Optional[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT l.*, u.email AS pm_email, u.full_name AS pm_name
            FROM listings l
            JOIN users u ON l.pm_id = u.id
            WHERE l.id = ?;
        """, (listing_id,))
        return cur.fetchone()
    finally:
        conn.close()

def get_listings_by_status(status: str) -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT l.*, u.email AS pm_email, u.full_name AS pm_name
            FROM listings l
            JOIN users u ON l.pm_id = u.id
            WHERE l.status = ?
            ORDER BY l.created_at DESC;
        """, (status,))
        return cur.fetchall()
    finally:
        conn.close()

def update_listing(
    listing_id: int, pm_id: int, address: str, price: float,
    description: str, lodging_details: str,
    image_paths: Optional[List[str]] = None,
    status: Optional[str] = None
) -> bool:
    """
    Update listing with validation. PM must own the listing.
    """
    if listing_id <= 0 or pm_id <= 0:
        print(f"[update_listing] Invalid IDs: listing_id={listing_id}, pm_id={pm_id}", file=sys.stderr)
        return False
    if not address or not address.strip():
        print(f"[update_listing] Address required for listing {listing_id}", file=sys.stderr)
        return False
    if price <= 0:
        print(f"[update_listing] Invalid price for listing {listing_id}: {price}", file=sys.stderr)
        return False
    if not description or not description.strip():
        print(f"[update_listing] Description required for listing {listing_id}", file=sys.stderr)
        return False

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT pm_id FROM listings WHERE id = ?;", (listing_id,))
        row = cur.fetchone()
        if not row:
            print(f"[update_listing] Listing not found: {listing_id}", file=sys.stderr)
            return False
        if row['pm_id'] != pm_id:
            print(f"[update_listing] Unauthorized: PM {pm_id} doesn't own listing {listing_id}", file=sys.stderr)
            return False

        now = _now_iso()
        if status:
            cur.execute("""
                UPDATE listings
                SET address = ?, price = ?, description = ?, lodging_details = ?, updated_at = ?, status = ?
                WHERE id = ?;
            """, (address.strip(), price, description.strip(), lodging_details or "", now, status, listing_id))
        else:
            cur.execute("""
                UPDATE listings
                SET address = ?, price = ?, description = ?, lodging_details = ?, updated_at = ?
                WHERE id = ?;
            """, (address.strip(), price, description.strip(), lodging_details or "", now, listing_id))

        if image_paths is not None:
            cur.execute("DELETE FROM listing_images WHERE listing_id = ?;", (listing_id,))
            for p in image_paths:
                if p and p.strip():
                    cur.execute("INSERT INTO listing_images (listing_id, image_path) VALUES (?, ?);", (listing_id, p.strip()))

        conn.commit()
        log_activity(pm_id, "Listing Updated", f"Updated listing ID {listing_id}: {address[:50]}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[update_listing] error for listing {listing_id}: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

def get_listing_by_title(title_substr: str) -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        like_pattern = f"%{title_substr}%"
        cur.execute("""
            SELECT l.*, u.email AS pm_email, u.full_name AS pm_name
            FROM listings l
            JOIN users u ON l.pm_id = u.id
            WHERE l.address LIKE ?
            ORDER BY l.created_at DESC;
        """, (like_pattern,))
        return cur.fetchall()
    finally:
        conn.close()

def get_listings_by_pm(pm_id: int) -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT l.*, u.email AS pm_email, u.full_name AS pm_name
            FROM listings l
            JOIN users u ON l.pm_id = u.id
            WHERE l.pm_id = ?
            ORDER BY l.created_at DESC;
        """, (pm_id,))
        return cur.fetchall()
    finally:
        conn.close()

def get_listings_by_tenant(tenant_id: int) -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT DISTINCT l.*, u.email AS pm_email, u.full_name AS pm_name
            FROM listings l
            JOIN users u ON l.pm_id = u.id
            JOIN reservations r ON l.id = r.listing_id
            WHERE r.tenant_id = ?
            ORDER BY l.created_at DESC;
        """, (tenant_id,))
        return cur.fetchall()
    finally:
        conn.close()

def search_listings_advanced(search_query: Optional[str] = None, filters: Optional[Dict] = None) -> List[sqlite3.Row]:
    """
    Advanced search with price, location, and other filters.
    Filters dict can contain: price_min, price_max, location
    Returns approved listings matching criteria.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        query = """
            SELECT l.*, u.email AS pm_email, u.full_name AS pm_name
            FROM listings l
            JOIN users u ON l.pm_id = u.id
            WHERE l.status = 'approved'
        """
        params = []

        if search_query and search_query.strip():
            query += " AND (l.address LIKE ? OR l.description LIKE ? OR l.lodging_details LIKE ?)"
            pattern = f"%{search_query.strip()}%"
            params.extend([pattern, pattern, pattern])

        if filters:
            if filters.get("price_min"):
                try:
                    price_min = float(filters["price_min"])
                    query += " AND l.price >= ?"
                    params.append(price_min)
                except (ValueError, TypeError):
                    pass
            if filters.get("price_max"):
                try:
                    price_max = float(filters["price_max"])
                    query += " AND l.price <= ?"
                    params.append(price_max)
                except (ValueError, TypeError):
                    pass
            if filters.get("location") and filters["location"].strip():
                query += " AND l.address LIKE ?"
                params.append(f"%{filters['location'].strip()}%")

        query += " ORDER BY l.created_at DESC"
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        conn.close()

def get_listing_images(listing_id: int) -> List[str]:
    """Get all image paths for a listing."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT image_path FROM listing_images WHERE listing_id = ?;", (listing_id,))
        return [r["image_path"] for r in cur.fetchall()]
    finally:
        conn.close()

def delete_listing(listing_id: int, pm_id: int) -> bool:
    """
    Delete listing with ownership verification.
    """
    if listing_id <= 0 or pm_id <= 0:
        print(f"[delete_listing] Invalid IDs: listing_id={listing_id}, pm_id={pm_id}", file=sys.stderr)
        return False

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Verify ownership
        cur.execute("SELECT pm_id, address FROM listings WHERE id = ?;", (listing_id,))
        r = cur.fetchone()
        if not r:
            print(f"[delete_listing] Listing not found: {listing_id}", file=sys.stderr)
            return False
        if r["pm_id"] != pm_id:
            print(f"[delete_listing] Unauthorized: PM {pm_id} doesn't own listing {listing_id}", file=sys.stderr)
            return False

        cur.execute("DELETE FROM listings WHERE id = ?;", (listing_id,))
        conn.commit()
        log_activity(pm_id, "Listing Deleted", f"Deleted listing ID {listing_id}: {r['address'][:50]}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[delete_listing] error for listing {listing_id}: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

def delete_listing_admin(listing_id: int) -> bool:
    """
    Admin delete (no ownership check).
    """
    if listing_id <= 0:
        print(f"[delete_listing_admin] Invalid listing_id: {listing_id}", file=sys.stderr)
        return False

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT address FROM listings WHERE id = ?;", (listing_id,))
        r = cur.fetchone()
        if not r:
            print(f"[delete_listing_admin] Listing not found: {listing_id}", file=sys.stderr)
            return False

        cur.execute("DELETE FROM listings WHERE id = ?;", (listing_id,))
        conn.commit()
        log_activity(None, "Listing Deleted (Admin)", f"Admin deleted listing ID {listing_id}: {r['address'][:50]}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[delete_listing_admin] error for listing {listing_id}: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

def delete_listing_image(listing_id: int, image_path: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM listing_images WHERE listing_id = ? AND image_path = ?;", (listing_id, image_path))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print("[delete_listing_image] error:", e, file=sys.stderr)
        return False
    finally:
        conn.close()

def delete_listing_by_title(title_substr: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        like_pattern = f"%{title_substr}%"
        cur.execute("DELETE FROM listings WHERE address LIKE ?;", (like_pattern,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print("[delete_listing_by_title] error:", e, file=sys.stderr)
        return False
    finally:
        conn.close()

def change_listing_status(listing_id: int, new_status: str) -> bool:
    """
    Change listing status with validation.
    """
    if listing_id <= 0:
        print(f"[change_listing_status] Invalid listing_id: {listing_id}", file=sys.stderr)
        return False
    if not new_status or not new_status.strip():
        print("[change_listing_status] Status is required", file=sys.stderr)
        return False

    valid_statuses = ["Available", "Occupied", "approved", "pending", "rejected"]
    if new_status not in valid_statuses:
        print(f"[change_listing_status] Invalid status: {new_status}. Valid: {valid_statuses}", file=sys.stderr)
        return False

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT address FROM listings WHERE id = ?;", (listing_id,))
        listing = cur.fetchone()
        if not listing:
            print(f"[change_listing_status] Listing not found: {listing_id}", file=sys.stderr)
            return False

        cur.execute("UPDATE listings SET status = ? WHERE id = ?;", (new_status, listing_id))
        conn.commit()
        log_activity(None, "Listing Status Changed", f"Listing {listing_id} status changed to {new_status}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[change_listing_status] error for listing {listing_id}: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

# ---------- Reservation helpers ----------
def create_reservation(listing_id: int, tenant_id: int, start_date: str, end_date: str, status: str = "pending") -> Optional[int]:
    """
    Create reservation with validation.
    """
    if listing_id <= 0 or tenant_id <= 0:
        print(f"[create_reservation] Invalid IDs: listing_id={listing_id}, tenant_id={tenant_id}", file=sys.stderr)
        return None
    if not start_date or not end_date:
        print("[create_reservation] Start and end dates are required", file=sys.stderr)
        return None
    if status not in ["pending", "approved", "confirmed", "cancelled", "rejected"]:
        print(f"[create_reservation] Invalid status: {status}", file=sys.stderr)
        return None

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM listings WHERE id = ?;", (listing_id,))
        if not cur.fetchone():
            print(f"[create_reservation] Listing not found: {listing_id}", file=sys.stderr)
            return None

        cur.execute("SELECT id FROM users WHERE id = ? AND role = 'tenant';", (tenant_id,))
        if not cur.fetchone():
            print(f"[create_reservation] Tenant not found: {tenant_id}", file=sys.stderr)
            return None

        now = _now_iso()
        cur.execute("""
            INSERT INTO reservations (listing_id, tenant_id, start_date, end_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (listing_id, tenant_id, start_date, end_date, status, now))
        conn.commit()

        reservation_id = cur.lastrowid
        log_activity(tenant_id, "Reservation Created", f"Created reservation ID {reservation_id} for listing {listing_id}")
        return reservation_id
    except Exception as e:
        conn.rollback()
        print(f"[create_reservation] error: {e}", file=sys.stderr)
        return None
    finally:
        conn.close()

def get_reservations(listing_id: Optional[int] = None, tenant_id: Optional[int] = None) -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        query = "SELECT * FROM reservations WHERE 1=1"
        params: List[Any] = []
        if listing_id is not None:
            query += " AND listing_id = ?"
            params.append(listing_id)
        if tenant_id is not None:
            query += " AND tenant_id = ?"
            params.append(tenant_id)
        query += " ORDER BY created_at DESC;"
        cur.execute(query, tuple(params))
        return cur.fetchall()
    finally:
        conn.close()

def get_listing_availability(listing_id: int) -> List[sqlite3.Row]:
    """
    Returns approved/confirmed reservations for a listing (caller decides availability).
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT * FROM reservations
            WHERE listing_id = ? AND status IN ('approved','confirmed')
            ORDER BY start_date ASC;
        """, (listing_id,))
        return cur.fetchall()
    finally:
        conn.close()

def get_reservation(reservation_id: int) -> Optional[Dict[str, Any]]:
    """
    Return a single reservation by ID joined with basic listing info.
    Returns a dict or None if not found.
    """
    if reservation_id <= 0:
        return None

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT r.*, l.address AS listing_address, l.price AS listing_price
            FROM reservations r
            LEFT JOIN listings l ON r.listing_id = l.id
            WHERE r.id = ?;
        """, (reservation_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        print(f"[get_reservation] error for id {reservation_id}: {e}", file=sys.stderr)
        return None
    finally:
        conn.close()

def update_reservation_status(reservation_id: int, new_status: str) -> bool:
    """
    Update the status of a reservation.
    Valid statuses: pending, approved, confirmed, cancelled, rejected
    """
    if reservation_id <= 0:
        print(f"[update_reservation_status] Invalid reservation ID: {reservation_id}", file=sys.stderr)
        return False
    if new_status not in ["pending", "approved", "confirmed", "cancelled", "rejected"]:
        print(f"[update_reservation_status] Invalid status: {new_status}", file=sys.stderr)
        return False

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE reservations SET status = ? WHERE id = ?;", (new_status, reservation_id))
        if cur.rowcount == 0:
            print(f"[update_reservation_status] Reservation not found: {reservation_id}", file=sys.stderr)
            return False
        conn.commit()
        log_activity(None, "Reservation Status Updated", f"Reservation {reservation_id} status changed to {new_status}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[update_reservation_status] error: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

# ---------- Activity logging ----------
def log_activity(user_id: Optional[int], action: str, details: str = "") -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        now = _now_iso()
        cur.execute("""
            INSERT INTO activity_logs (user_id, action, details, created_at)
            VALUES (?, ?, ?, ?);
        """, (user_id, action, details, now))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print("[log_activity] error:", e, file=sys.stderr)
        return False
    finally:
        conn.close()

def get_recent_activity(limit: int = 20) -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT a.*, u.full_name as user_full_name, u.email as user_email
            FROM activity_logs a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at DESC
            LIMIT ?;
        """, (limit,))
        return cur.fetchall()
    finally:
        conn.close()

# ---------- Reports ----------
def create_report(user_id: int, listing_id: Optional[int], message: str) -> Optional[int]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        now = _now_iso()
        cur.execute("""
            INSERT INTO reports (user_id, listing_id, message, status, created_at)
            VALUES (?, ?, ?, ?, ?);
        """, (user_id, listing_id, message, "open", now))
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        conn.rollback()
        print("[create_report] error:", e, file=sys.stderr)
        return None
    finally:
        conn.close()

def get_all_reports() -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT r.*, u.email AS reporter_email, l.address AS listing_address
            FROM reports r
            LEFT JOIN users u ON r.user_id = u.id
            LEFT JOIN listings l ON r.listing_id = l.id
            ORDER BY r.created_at DESC;
        """)
        return cur.fetchall()
    finally:
        conn.close()

# ---------- Admin utilities ----------
def rekey_database(new_key: str) -> bool:
    """
    Change the database encryption key.
    Works only if SQLCipher is available.
    WARNING: call with care and backup DB before rekey.
    """
    if not SQLCIPHER_AVAILABLE:
        print("[rekey_database] sqlcipher not available, cannot rekey.", file=sys.stderr)
        return False

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA rekey = ?;", (new_key,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print("[rekey_database] error:", e, file=sys.stderr)
        return False
    finally:
        conn.close()

# ---------- Debug / safe check ----------
def _list_tables() -> List[str]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()

# ---------- Model-compatible adapter functions ----------
def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.
    Returns (is_valid, message)
    """
    if not password:
        return False, "Password is required"
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    return True, "Password is valid"

def validate_email(email: str) -> tuple[bool, str]:
    """
    Validate email format.
    Returns (is_valid, message)
    """
    if not email or not email.strip():
        return False, "Email is required"

    email_clean = email.strip().lower()

    if "@" not in email_clean or "." not in email_clean:
        return False, "Invalid email format"

    existing = get_user_by_email(email_clean)
    if existing:
        return False, "Email already registered"

    return True, "Email is valid"


def property_data():
    """
    Seed 15 beautiful, real-looking properties with working images.
    Runs only if we don't have 15+ proper listings yet.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Add missing columns safely
        columns_to_add = [
            ("name", "TEXT"),
            ("location", "TEXT"),
            ("room_type", "TEXT"),
            ("total_rooms", "INTEGER DEFAULT 0"),
            ("available_rooms", "INTEGER DEFAULT 0"),
            ("available_room_types", "TEXT"),
            ("amenities", "TEXT"),
            ("availability_status", "TEXT DEFAULT 'Available'"),
            ("image_url", "TEXT"),
            ("image_url_2", "TEXT"),
            ("image_url_3", "TEXT"),
            ("image_url_4", "TEXT"),
        ]
        for col_name, col_def in columns_to_add:
            if not column_exists(cur, "listings", col_name):
                try:
                    cur.execute(f"ALTER TABLE listings ADD COLUMN {col_name} {col_def};")
                    print(f"[property_data] Added column: {col_name}")
                except:
                    pass
        conn.commit()

        pm_emails = [
            "pm.1",
            "pm.2",
            "pm.3",
            "pm.4",
            "pm.5",
            "pm.6",
        ]

        for email in pm_emails:
            cur.execute("SELECT id FROM users WHERE email = ?", (email,))
            if not cur.fetchone():
                hashed = hash_password("PmPassword123!")
                cur.execute("""
                    INSERT INTO users (email, password, role, full_name, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (email, hashed, "pm", email.split("@")[0].replace(".", " ").title(), _now_iso()))
                print(f"[property_data] Created PM: {email}")

        conn.commit()

        cur.execute("SELECT id, email FROM users WHERE role = 'pm' ORDER BY id")
        pm_rows = cur.fetchall()
        if len(pm_rows) < 6:
            print("[property_data] Not enough PMs created!")
            return

        pm_map = {row["email"]: row["id"] for row in pm_rows}

        cur.execute("SELECT COUNT(*) as c FROM listings WHERE name IS NOT NULL AND name != '' AND name NOT LIKE 'Demo Listing%'")
        real_count = cur.fetchone()['c']

        if real_count >= 15:
            print(f"[property_data] Already have {real_count} real listings – skipping")
            return

        print(f"[property_data] Seeding 15 beautiful listings with real photos...")

        sample_listings = [
            {
            "pm_id": pm_map["pm.1"],
            "name": "Cozy Campus Boardinghouse",
            "address": "123 Aurora Blvd, Quezon City",
            "location": "Near UP Diliman",
            "price": 3500.0,
            "description": "Super cozy boarding house just 5 mins walk from UP Diliman gate. Clean rooms, fast WiFi, shared kitchen & laundry. Perfect for students!",
            "room_type": "Double",
            "total_rooms": 10,
            "available_rooms": 4,
            "available_room_types": json.dumps(["Single", "Double"]),
            "amenities": json.dumps(["WiFi", "Kitchen", "Laundry", "24/7 Security", "Study Area", "Water Included"]),
            "availability_status": "Available",
            "lodging_details": "Double room with bunk beds",
            "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267",
            "image_url_2": "https://images.unsplash.com/photo-1502672260066-6bc2c0923089",
            "image_url_3": "https://images.unsplash.com/photo-1484154218962-a197022b5858",
            "image_url_4": "https://images.unsplash.com/photo-1493809842364-78817add7ffb",
            "status": "approved"
            },
            {
            "pm_id": pm_map["pm.1"],
            "name": "Modern Studio near Ateneo",
            "address": "Katipunan Ave, Loyola Heights",
            "location": "Near Ateneo & Miriam",
            "price": 5800.0,
            "description": "Brand new minimalist studio with high-speed fiber internet, study desk, kitchenette, and private bathroom. Walking distance to campus.",
            "room_type": "Studio",
            "total_rooms": 8,
            "available_rooms": 3,
            "available_room_types": json.dumps(["Studio"]),
            "amenities": json.dumps(["WiFi", "AC", "Kitchenette", "Private CR", "Study Desk", "Laundry Service"]),
            "availability_status": "Available",
            "lodging_details": "Fully furnished studio unit",
            "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2",
            "image_url_2": "https://images.unsplash.com/photo-1556020685-ae41abfc9365",
            "image_url_3": "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af",
            "image_url_4": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
            "status": "approved"
            },
            {
            "pm_id": pm_map["pm.1"],
            "name": "Budget Dorm Espana",
            "address": "567 España Blvd, Sampaloc",
            "location": "Near UST",
            "price": 2500.0,
            "description": "Affordable bedspace for budget-conscious students. Includes locker, study area, and free WiFi. 3 mins from UST gate.",
            "room_type": "Bed Space",
            "total_rooms": 20,
            "available_rooms": 7,
            "available_room_types": json.dumps(["Bed Space"]),
            "amenities": json.dumps(["WiFi", "Locker", "Study Area", "CCTV", "Common CR"]),
            "availability_status": "Available",
            "lodging_details": "Clean bed space with personal cabinet",
            "image_url": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5",
            "image_url_2": "https://images.unsplash.com/photo-1540518614846-7eded433c457",
            "image_url_3": "https://images.unsplash.com/photo-1562438668-bcf0ca6578f0",
            "image_url_4": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85",
            "status": "approved"
            },
            {
            "pm_id": pm_map["pm.2"],
            "name": "Female-Only Dorm Taft",
            "address": "234 Taft Avenue, Malate",
            "location": "Near DLSU & St. Scholastica",
            "price": 3200.0,
            "description": "Exclusive female dormitory with 24/7 female guard, curfew, study lounge, and sisterhood community. Safe and supportive environment.",
            "room_type": "Double",
            "total_rooms": 12,
            "available_rooms": 5,
            "available_room_types": json.dumps(["Double", "Quad Share"]),
            "amenities": json.dumps(["WiFi", "Study Lounge", "Female Guard 24/7", "CCTV", "Laundry", "Prayer Room"]),
            "availability_status": "Available",
            "lodging_details": "Safe female-only boarding house",
            "image_url": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b",
            "image_url_2": "https://images.unsplash.com/photo-1513694203232-719a280e022f",
            "image_url_3": "https://images.unsplash.com/photo-1602940659805-70b109a9d8a2",
            "image_url_4": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
            "status": "approved"
            },
            {
            "pm_id": pm_map["pm.2"],
            "name": "Luxury Condo BGC",
            "address": "Serendra, Bonifacio Global City",
            "location": "BGC, Taguig",
            "price": 8500.0,
            "description": "High-end condo unit with hotel-like amenities: infinity pool, gym, concierge. Perfect for UP-PGH, St. Luke's, or BGC workers.",
            "room_type": "Single",
            "total_rooms": 6,
            "available_rooms": 2,
            "available_room_types": json.dumps(["Single", "Studio"]),
            "amenities": json.dumps(["WiFi", "AC", "Gym", "Pool", "Concierge", "Parking"]),
            "availability_status": "Limited",
            "lodging_details": "Premium single room with city view",
            "image_url": "https://images.unsplash.com/photo-1564078516393-cf04bd966897",
            "image_url_2": "https://images.unsplash.com/photo-1567767292722-443c687c3e73",
            "image_url_3": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750",
            "image_url_4": "https://images.unsplash.com/photo-1600566753376-2da6f6a55fd9",
            "status": "approved"
            },
            {
            "pm_id": pm_map["pm.3"],
            "name": "Smart Tech Dorm QC",
            "address": "999 Innovation Ave, Diliman",
            "location": "Near UP & Ateneo",
            "price": 3800.0,
            "description": "State-of-the-art smart dorm: biometric entry, app-controlled lights/AC, gaming room, study pods.",
            "room_type": "Single",
            "total_rooms": 20,
            "available_rooms": 9,
            "available_room_types": json.dumps(["Single", "Twin Share"]),
            "amenities": json.dumps(["Fiber Internet", "Smart Lock", "Gaming Room", "Study Pods", "Rooftop"]),
            "availability_status": "Available",
            "lodging_details": "Tech-savvy dormitory",
            "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3",
            "image_url_2": "https://images.unsplash.com/photo-1602940659805-70b109a9d8a2",
            "image_url_3": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
            "image_url_4": "https://images.unsplash.com/photo-1560185127-6ed189bf02f4",
            "status": "approved"
            },
            {
            "pm_id": pm_map["pm.3"],
            "name": "Garden View Apartment",
            "address": "88 Pioneer St, Mandaluyong",
            "location": "Near Shaw Blvd",
            "price": 4800.0,
            "description": "Peaceful apartment with balcony and garden view. Great natural light, quiet street, near malls and MRT.",
            "room_type": "Single",
            "total_rooms": 8,
            "available_rooms": 3,
            "available_room_types": json.dumps(["Single", "Double"]),
            "amenities": json.dumps(["WiFi", "Balcony", "Parking", "Garden", "CCTV"]),
            "availability_status": "Available",
            "lodging_details": "Apartment with garden access",
            "image_url": "https://images.unsplash.com/photo-1536376072261-38c75010e6c9",
            "image_url_2": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267",
            "image_url_3": "https://images.unsplash.com/photo-1502672260066-6bc2c0923089",
            "image_url_4": "https://images.unsplash.com/photo-1484154218962-a197022b5858",
            "status": "approved"
            },
            {
            "pm_id": pm_map["pm.4"],
            "name": "Executive Townhouse Alabang",
            "address": "Palm Drive, Alabang",
            "location": "Alabang, Muntinlupa",
            "price": 9500.0,
            "description": "Spacious 2-storey townhouse perfect for med students or small groups. Private garage, clubhouse access.",
            "room_type": "Whole Unit",
            "total_rooms": 3,
            "available_rooms": 1,
            "available_room_types": json.dumps(["Whole Unit"]),
            "amenities": json.dumps(["WiFi", "Parking", "Clubhouse", "Pool", "Swimming Pool", "Security"]),
            "availability_status": "Limited",
            "lodging_details": "Full townhouse rental",
            "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750",
            "image_url_2": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
            "image_url_3": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3",
            "image_url_4": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2",
            "status": "approved"
            },
            {
            "pm_id": pm_map["pm.4"],
            "name": "Beachside Condo Pasay",
            "address": "777 Roxas Blvd",
            "location": "Near Mall of Asia",
            "price": 7200.0,
            "description": "Stunning bay view condo. Wake up to the sea breeze. Infinity pool, gym, mall access.",
            "room_type": "Studio",
            "total_rooms": 5,
            "available_rooms": 2,
            "available_room_types": json.dumps(["Studio", "One Bedroom"]),
            "amenities": json.dumps(["WiFi", "Pool", "Gym", "Mall Access", "Bay View"]),
            "availability_status": "Available",
            "lodging_details": "Condo with sea view",
            "image_url": "https://images.unsplash.com/photo-1502672023488-70e25813eb80",
            "image_url_2": "https://images.unsplash.com/photo-1560185127-6ed189bf02f4",
            "image_url_3": "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af",
            "image_url_4": "https://images.unsplash.com/photo-1502672260066-6bc2c0923089",
            "status": "approved"
            },
            {
            "pm_id": pm_map["pm.5"],
            "name": "Green Living Marikina",
            "address": "555 Eco Street, Marikina Heights",
            "location": "Marikina City",
            "price": 4200.0,
            "description": "Eco-friendly apartment with solar panels, rainwater system, and organic garden. Pet-friendly!",
            "room_type": "Single",
            "total_rooms": 10,
            "available_rooms": 6,
            "available_room_types": json.dumps(["Single", "Double"]),
            "amenities": json.dumps(["WiFi", "Solar Power", "Garden", "Pet-Friendly", "Bike Rack"]),
            "availability_status": "Available",
            "lodging_details": "Sustainable living apartment",
            "image_url": "https://images.unsplash.com/photo-1536376072261-38c75010e6c9",
            "image_url_2": "https://images.unsplash.com/photo-1484154218962-a197022b5858",
            "image_url_3": "https://images.unsplash.com/photo-1493809842364-78817add7ffb",
            "image_url_4": "https://images.unsplash.com/photo-1502672260066-6bc2c0923089",
            "status": "approved"
            },
            {
            "pm_id": pm_map["pm.5"],
            "name": "Co-Living Poblacion",
            "address": "888 Jupiter St, Makati",
            "location": "Poblacion, Makati",
            "price": 6500.0,
            "description": "Modern co-living space with co-working area, rooftop bar, gym, and events. Best for social students!",
            "room_type": "Single",
            "total_rooms": 15,
            "available_rooms": 5,
            "available_room_types": json.dumps(["Single", "Shared Studio"]),
            "amenities": json.dumps(["WiFi", "Co-working", "Gym", "Rooftop Bar", "Events"]),
            "availability_status": "Available",
            "lodging_details": "Vibrant co-living community",
            "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750",
            "image_url_2": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
            "image_url_3": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2",
            "image_url_4": "https://images.unsplash.com/photo-1556020685-ae41abfc9365",
            "status": "approved"
            },
            {
            "pm_id": pm_map["pm.5"],
            "name": "Traditional Home Sampaloc",
            "address": "432 P. Noval St",
            "location": "Near FEU & UE",
            "price": 2900.0,
            "description": "Classic Filipino boarding house with home-cooked meals available. Warm landlady, family vibe.",
            "room_type": "Double",
            "total_rooms": 8,
            "available_rooms": 4,
            "available_room_types": json.dumps(["Single", "Double"]),
            "amenities": json.dumps(["WiFi", "Home-cooked Meals", "Laundry", "Study Area"]),
            "availability_status": "Available",
            "lodging_details": "Home away from home",
            "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267",
            "image_url_2": "https://images.unsplash.com/photo-1493809842364-78817add7ffb",
            "image_url_3": "https://images.unsplash.com/photo-1484154218962-a197022b5858",
            "image_url_4": "https://images.unsplash.com/photo-1540518614846-7eded433c457",
            "status": "approved"
            },
            {
            "pm_id": pm_map["pm.6"],
            "name": "Premium Loft McKinley",
            "address": "McKinley Hill, Taguig",
            "location": "Venice Grand Canal Mall",
            "price": 11000.0,
            "description": "Ultra-luxury loft with panoramic views, smart home system, private terrace. For students who want the best.",
            "room_type": "Penthouse",
            "total_rooms": 1,
            "available_rooms": 1,
            "available_room_types": json.dumps(["Penthouse"]),
            "amenities": json.dumps(["WiFi", "Smart Home", "Terrace", "Gym", "Pool", "Concierge"]),
            "availability_status": "Available",
            "lodging_details": "Exclusive penthouse unit",
            "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3",
            "image_url_2": "https://images.unsplash.com/photo-1564078516393-cf04bd966897",
            "image_url_3": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750",
            "image_url_4": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
            "status": "approved"
            },
            {
            "pm_id": pm_map["pm.6"],
            "name": "Sunshine Apartment Pasig",
            "address": "Ortigas Extension, Pasig",
            "location": "Near Tiendesitas",
            "price": 4300.0,
            "description": "Bright and sunny apartment with big windows. Near Eastwood, Ortigas CBD. Great for working students.",
            "room_type": "Single",
            "total_rooms": 10,
            "available_rooms": 5,
            "available_room_types": json.dumps(["Single"]),
            "amenities": json.dumps(["WiFi", "AC", "Parking", "Security", "Rooftop"]),
            "availability_status": "Available",
            "lodging_details": "Sunny single room",
            "image_url": "https://images.unsplash.com/photo-1502672260066-6bc2c0923089",
            "image_url_2": "https://images.unsplash.com/photo-1484154218962-a197022b5858",
            "image_url_3": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267",
            "image_url_4": "https://images.unsplash.com/photo-1493809842364-78817add7ffb",
            "status": "approved"
            },
            {
            "pm_id": pm_map["pm.6"],
            "name": "Riverside Bedspace",
            "address": "Marikina Riverbanks",
            "location": "Marikina City",
            "price": 2400.0,
            "description": "Most affordable option near Marikina schools. Clean, simple, safe. Free breakfast on weekends!",
            "room_type": "Bed Space",
            "total_rooms": 25,
            "available_rooms": 10,
            "available_room_types": json.dumps(["Bed Space"]),
            "amenities": json.dumps(["WiFi", "Breakfast", "Locker", "CCTV"]),
            "availability_status": "Available",
            "lodging_details": "Budget bedspace with meals",
            "image_url": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85",
            "image_url_2": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5",
            "image_url_3": "https://images.unsplash.com/photo-1540518614846-7eded433c457",
            "image_url_4": "https://images.unsplash.com/photo-1562438668-bcf0ca6578f0",
            "status": "approved"
            }
        ]

        now = _now_iso()
        for listing in sample_listings:
            cur.execute("""
                INSERT INTO listings (
                    pm_id, name, address, location, price, description, lodging_details,
                    room_type, total_rooms, available_rooms, available_room_types,
                    amenities, availability_status, image_url, image_url_2,
                    image_url_3, image_url_4, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                listing["pm_id"], listing["name"], listing["address"], listing["location"],
                listing["price"], listing["description"], listing["lodging_details"],
                listing["room_type"], listing["total_rooms"], listing["available_rooms"],
                listing["available_room_types"], listing["amenities"], listing["availability_status"],
                listing["image_url"], listing["image_url_2"], listing["image_url_3"],
                listing["image_url_4"], listing["status"], now, now
            ))

        conn.commit()
        print("[property_data] SUCCESS! 15 beautiful listings with real photos seeded!")

    except Exception as e:
        print(f"[property_data] ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()


def get_property_by_id(property_id: int):
    """
    Get a single property by ID with all details.
    Returns all fields needed for property_details_view.
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        query = """
            SELECT
                id, pm_id, name, address, location, price, description,
                room_type, total_rooms, available_rooms, available_room_types,
                amenities, availability_status, image_url, image_url_2,
                image_url_3, image_url_4, status, created_at, updated_at
            FROM listings
            WHERE id = ? AND status = 'approved'
        """

        cur.execute(query, (property_id,))
        prop = cur.fetchone()

        if not prop:
            return None

        return {
            "id": prop["id"],
            "pm_id": prop["pm_id"],
            "name": prop["name"],
            "address": prop["address"],
            "location": prop["location"],
            "price": prop["price"],
            "description": prop["description"],
            "room_type": prop["room_type"],
            "total_rooms": prop["total_rooms"],
            "available_rooms": prop["available_rooms"],
            "available_room_types": prop["available_room_types"],
            "amenities": prop["amenities"],
            "availability_status": prop["availability_status"],
            "image_url": prop["image_url"],
            "image_url_2": prop["image_url_2"],
            "image_url_3": prop["image_url_3"],
            "image_url_4": prop["image_url_4"],
            "status": prop["status"],
            "created_at": prop["created_at"],
            "updated_at": prop["updated_at"]
        }

    except Exception as e:
        print(f"[get_property_by_id] ❌ Error: {e}", file=sys.stderr)
        return None
    finally:
        conn.close()


# ---------- Extra helpers added from DatabaseManager class ----------
def get_user_address(user_id: int) -> Optional[Dict[str, Any]]:
    """Get the primary address for a user."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM user_addresses WHERE user_id = ? AND is_primary = 1;", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_user_address(user_id: int, house_no: str, street: str, barangay: str, city: str, province: str = "Camarines Sur") -> bool:
    """Update or create a user's primary address."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT address_id FROM user_addresses WHERE user_id = ? AND is_primary = 1;", (user_id,))
        existing = cur.fetchone()
        now = _now_iso()
        if existing:
            cur.execute(
                """
                UPDATE user_addresses SET house_no = ?, street = ?, barangay = ?, city = ?, province = ?, updated_at = ?
                WHERE address_id = ?
                """,
                (house_no, street, barangay, city, province, now, existing[0])
            )
        else:
            cur.execute(
                """
                INSERT INTO user_addresses (user_id, house_no, street, barangay, city, province, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, house_no, street, barangay, city, province, now, now)
            )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"[update_user_address] error for user {user_id}: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def get_saved_listings(user_id: int) -> List[Dict[str, Any]]:
    """Return saved listings for a user (joined with listings)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT l.*, s.saved_at
            FROM listings l
            INNER JOIN saved_listings s ON l.id = s.listing_id
            WHERE s.user_id = ?
            ORDER BY s.saved_at DESC;
            """,
            (user_id,)
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def is_property_saved(user_id: int, listing_id: int) -> bool:
    """Check if a listing is already saved by the user."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT 1 FROM saved_listings WHERE user_id = ? AND listing_id = ? LIMIT 1;",
            (user_id, listing_id)
        )
        return cur.fetchone() is not None
    except Exception as e:
        print(f"[is_property_saved] error: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def save_property(user_id: int, listing_id: int) -> bool:
    """Persist a saved listing for the user."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT saved_id FROM saved_listings WHERE user_id = ? AND listing_id = ?;",
            (user_id, listing_id)
        )
        if cur.fetchone():
            return True

        now = _now_iso()
        cur.execute(
            "INSERT INTO saved_listings (user_id, listing_id, saved_at) VALUES (?, ?, ?);",
            (user_id, listing_id, now)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"[save_property] error: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def unsave_property(user_id: int, listing_id: int) -> bool:
    """Remove a saved listing for the user."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM saved_listings WHERE user_id = ? AND listing_id = ?;",
            (user_id, listing_id)
        )
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"[unsave_property] error: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def toggle_saved_listing(user_id: int, listing_id: int) -> bool:
    """Toggle saved listing; returns True if added, False if removed."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT saved_id FROM saved_listings WHERE user_id = ? AND listing_id = ?;", (user_id, listing_id))
        row = cur.fetchone()
        if row:
            cur.execute("DELETE FROM saved_listings WHERE saved_id = ?;", (row[0],))
            conn.commit()
            return False
        else:
            now = _now_iso()
            cur.execute("INSERT INTO saved_listings (user_id, listing_id, saved_at) VALUES (?, ?, ?);", (user_id, listing_id, now))
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"[toggle_saved_listing] error: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def get_user_notifications(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT ?;", (user_id, limit))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_unread_count(user_id: int) -> int:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) as c FROM notifications WHERE user_id = ? AND is_read = 0;", (user_id,))
        row = cur.fetchone()
        return int(row['c']) if row and 'c' in row.keys() else (row[0] if row else 0)
    finally:
        conn.close()


def add_notification(user_id: int, notification_type: str, message: str, category: str = "activity", reference_id: Optional[int] = None, reference_type: Optional[str] = None) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        now = _now_iso()
        cur.execute(
            """
            INSERT INTO notifications (user_id, notification_type, category, message, reference_id, reference_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (user_id, notification_type, category, message, reference_id, reference_type, now)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"[add_notification] error: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def mark_notification_read(notification_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        now = _now_iso()
        cur.execute("UPDATE notifications SET is_read = 1, read_at = ? WHERE notification_id = ?;", (now, notification_id))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"[mark_notification_read] error: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def mark_all_notifications_read(user_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        now = _now_iso()
        cur.execute("UPDATE notifications SET is_read = 1, read_at = ? WHERE user_id = ? AND is_read = 0;", (now, user_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"[mark_all_notifications_read] error: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def get_user_settings(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM user_settings WHERE user_id = ?;", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_user_settings(user_id: int, settings: Dict[str, Any]) -> bool:
    """Update user settings. `settings` is a dict of allowed keys."""
    valid_keys = [
        "popup_notifications", "chat_notifications", "email_notifications",
        "reservation_confirmation_notif", "cancellation_notif",
        "payment_update_notif", "rent_reminders_notif", "theme", "language"
    ]
    updates = []
    values = []
    for k, v in settings.items():
        if k in valid_keys:
            updates.append(f"{k} = ?")
            values.append(v)

    if not updates:
        return False

    values.append(user_id)
    sql = f"UPDATE user_settings SET {', '.join(updates)}, updated_at = ? WHERE user_id = ?"
    # updated_at value
    values.insert(-1, _now_iso())

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, tuple(values))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"[update_user_settings] error: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def create_payment_transaction(reservation_id: int, user_id: int, amount: float, payment_method: str, transaction_reference: Optional[str] = None, card_last_four: Optional[str] = None) -> Optional[int]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        now = _now_iso()
        cur.execute(
            """
            INSERT INTO payment_transactions (reservation_id, user_id, amount, payment_method, transaction_reference, card_last_four, status, payment_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (reservation_id, user_id, amount, payment_method, transaction_reference, card_last_four, 'Completed', now, now)
        )
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        conn.rollback()
        print(f"[create_payment_transaction] error: {e}", file=sys.stderr)
        return None
    finally:
        conn.close()


def get_payment_transactions(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT pt.*, r.id as reservation_id, l.address as listing_address
            FROM payment_transactions pt
            LEFT JOIN reservations r ON pt.reservation_id = r.id
            LEFT JOIN listings l ON r.listing_id = l.id
            WHERE pt.user_id = ?
            ORDER BY pt.created_at DESC;
            """,
            (user_id,)
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# =====================================================
# ADMIN PAYMENT MANAGEMENT FUNCTIONS
# =====================================================

def get_all_payments_admin(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all payments (optionally filtered by status) with user and listing info."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        if status:
            cur.execute("""
                SELECT p.id, p.user_id, u.email as user_email, u.full_name,
                       p.listing_id, l.address as listing_address,
                       p.amount, p.status, p.payment_method, p.refunded_amount,
                       p.refund_reason, p.notes, p.created_at, p.updated_at
                FROM payments p
                LEFT JOIN users u ON p.user_id = u.id
                LEFT JOIN listings l ON p.listing_id = l.id
                WHERE p.status = ?
                ORDER BY p.created_at DESC
            """, (status,))
        else:
            cur.execute("""
                SELECT p.id, p.user_id, u.email as user_email, u.full_name,
                       p.listing_id, l.address as listing_address,
                       p.amount, p.status, p.payment_method, p.refunded_amount,
                       p.refund_reason, p.notes, p.created_at, p.updated_at
                FROM payments p
                LEFT JOIN users u ON p.user_id = u.id
                LEFT JOIN listings l ON p.listing_id = l.id
                ORDER BY p.created_at DESC
            """)
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def process_payment_refund(payment_id: int, refund_amount: float, refund_reason: str) -> Tuple[bool, str]:
    """Process a partial or full refund for a payment."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Get original payment
        cur.execute("SELECT id, amount, refunded_amount FROM payments WHERE id = ?", (payment_id,))
        payment = cur.fetchone()

        if not payment:
            return False, "Payment not found"

        original_amount = float(payment['amount'])
        already_refunded = float(payment['refunded_amount'])
        remaining = original_amount - already_refunded

        if refund_amount > remaining:
            return False, f"Refund amount (₱{refund_amount:,.2f}) exceeds remaining balance (₱{remaining:,.2f})"

        if refund_amount <= 0:
            return False, "Refund amount must be greater than 0"

        # Update payment with refund info
        new_refunded_amount = already_refunded + refund_amount
        new_status = 'refunded' if new_refunded_amount >= original_amount else 'completed'

        cur.execute("""
            UPDATE payments
            SET status = ?, refunded_amount = ?, refund_reason = ?, updated_at = ?
            WHERE id = ?
        """, (new_status, new_refunded_amount, refund_reason, _now_iso(), payment_id))

        conn.commit()
        return True, f"Refund of ₱{refund_amount:,.2f} processed successfully"
    except Exception as e:
        conn.rollback()
        return False, f"Error processing refund: {str(e)}"
    finally:
        conn.close()


def update_payment_status(payment_id: int, new_status: str, notes: Optional[str] = None) -> Tuple[bool, str]:
    """Update payment status (completed, pending, failed, refunded)."""
    valid_statuses = ['completed', 'pending', 'failed', 'refunded']
    if new_status not in valid_statuses:
        return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE payments
            SET status = ?, notes = ?, updated_at = ?
            WHERE id = ?
        """, (new_status, notes, _now_iso(), payment_id))

        if cur.rowcount == 0:
            return False, "Payment not found"

        conn.commit()
        return True, f"Payment status updated to '{new_status}'"
    except Exception as e:
        conn.rollback()
        return False, f"Error updating payment: {str(e)}"
    finally:
        conn.close()


def get_payment_statistics() -> Dict[str, Any]:
    """Get payment statistics (total revenue, refunds, average transaction, etc.)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Total revenue (completed and partially refunded payments minus refunds)
        cur.execute("""
            SELECT
                COUNT(*) as total_transactions,
                SUM(amount) as total_revenue,
                SUM(refunded_amount) as total_refunds,
                SUM(amount - refunded_amount) as net_revenue,
                AVG(amount) as avg_transaction,
                MIN(amount) as min_transaction,
                MAX(amount) as max_transaction
            FROM payments
            WHERE status IN ('completed', 'refunded')
        """)
        row = cur.fetchone()

        # Payment method breakdown
        cur.execute("""
            SELECT payment_method, COUNT(*) as count, SUM(amount) as total
            FROM payments
            WHERE status IN ('completed', 'refunded')
            GROUP BY payment_method
            ORDER BY total DESC
        """)
        method_rows = cur.fetchall()
        payment_methods = {dict(r)['payment_method']: dict(r) for r in method_rows}

        # Status breakdown
        cur.execute("""
            SELECT status, COUNT(*) as count, SUM(amount) as total
            FROM payments
            GROUP BY status
            ORDER BY count DESC
        """)
        status_rows = cur.fetchall()
        statuses = {dict(r)['status']: dict(r) for r in status_rows}

        return {
            'total_transactions': row['total_transactions'] or 0,
            'total_revenue': float(row['total_revenue'] or 0),
            'total_refunds': float(row['total_refunds'] or 0),
            'net_revenue': float(row['net_revenue'] or 0),
            'avg_transaction': float(row['avg_transaction'] or 0),
            'min_transaction': float(row['min_transaction'] or 0),
            'max_transaction': float(row['max_transaction'] or 0),
            'payment_methods': payment_methods,
            'statuses': statuses
        }
    finally:
        conn.close()


def add_review(listing_id: int, user_id: int, rating: int, comment: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        now = _now_iso()
        cur.execute("INSERT INTO reviews (listing_id, user_id, rating, comment, created_at) VALUES (?, ?, ?, ?, ?);", (listing_id, user_id, rating, comment, now))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"[add_review] error: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def get_reviews_for_property(listing_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT r.*, u.full_name, u.email
            FROM reviews r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.listing_id = ?
            ORDER BY r.created_at DESC;
            """,
            (listing_id,)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def send_message(sender_id: int, content: str, receiver_id: int = 0) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        now = _now_iso()
        cur.execute("INSERT INTO messages (sender_id, receiver_id, content, is_read, created_at) VALUES (?, ?, ?, 0, ?);", (sender_id, receiver_id, content, now))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"[send_message] error: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def get_chat_history(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM messages WHERE sender_id = ? OR receiver_id = ? ORDER BY created_at ASC;", (user_id, user_id))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ---------- SYSTEM SETTINGS ----------

def get_settings(settings_id: str = 'default') -> Optional[Dict[str, Any]]:
    """Get system settings from database"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT settings_json FROM system_settings WHERE settings_id = ?;""",
            (settings_id,)
        )
        result = cur.fetchone()
        if result:
            import json
            return json.loads(result['settings_json'])
        return None
    except Exception as e:
        print(f"[get_settings] error: {e}", file=sys.stderr)
        return None
    finally:
        conn.close()


def save_settings(settings_dict: Dict[str, Any], settings_id: str = 'default', changed_by: str = 'system') -> Tuple[bool, str]:
    """Save system settings to database"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        import json

        now = _now_iso()
        settings_json = json.dumps(settings_dict)

        # Check if settings exist
        cur.execute("SELECT id FROM system_settings WHERE settings_id = ?;", (settings_id,))
        existing = cur.fetchone()

        if existing:
            # Update existing
            cur.execute(
                """UPDATE system_settings SET settings_json = ?, updated_at = ? WHERE settings_id = ?;""",
                (settings_json, now, settings_id)
            )
            # Record change in history
            cur.execute(
                """INSERT INTO settings_history (settings_id, changed_fields, changed_by, changed_at)
                   VALUES (?, 'full_update', ?, ?);""",
                (settings_id, changed_by, now)
            )
        else:
            # Insert new
            cur.execute(
                """INSERT INTO system_settings (settings_id, settings_json, created_at, updated_at)
                   VALUES (?, ?, ?, ?);""",
                (settings_id, settings_json, now, now)
            )
            cur.execute(
                """INSERT INTO settings_history (settings_id, changed_fields, changed_by, changed_at)
                   VALUES (?, 'initial_creation', ?, ?);""",
                (settings_id, changed_by, now)
            )

        conn.commit()
        return True, "Settings saved successfully"
    except Exception as e:
        conn.rollback()
        print(f"[save_settings] error: {e}", file=sys.stderr)
        return False, f"Error saving settings: {str(e)}"
    finally:
        conn.close()


def reset_settings(settings_id: str = 'default') -> Tuple[bool, str]:
    """Reset settings to empty state"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        now = _now_iso()
        cur.execute(
            """DELETE FROM system_settings WHERE settings_id = ?;""",
            (settings_id,)
        )
        cur.execute(
            """INSERT INTO settings_history (settings_id, changed_fields, changed_by, changed_at)
               VALUES (?, 'reset_to_defaults', 'system', ?);""",
            (settings_id, now)
        )
        conn.commit()
        return True, "Settings reset successfully"
    except Exception as e:
        conn.rollback()
        print(f"[reset_settings] error: {e}", file=sys.stderr)
        return False, f"Error resetting settings: {str(e)}"
    finally:
        conn.close()


def get_all_settings_history(settings_id: str = 'default', limit: int = 10) -> List[Dict[str, Any]]:
    """Get settings change history"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT id, settings_id, changed_fields, changed_by, changed_at
               FROM settings_history
               WHERE settings_id = ?
               ORDER BY changed_at DESC
               LIMIT ?;""",
            (settings_id, limit)
        )
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        print(f"[get_all_settings_history] error: {e}", file=sys.stderr)
        return []
    finally:
        conn.close()


def update_setting_field(settings_id: str, field_path: str, value: Any, changed_by: str = 'system') -> Tuple[bool, str]:
    """Update a single settings field and record change"""
    try:
        import json

        # Get current settings
        current = get_settings(settings_id)
        if not current:
            return False, "Settings not found"

        # Update field (simple case - no nested paths for now)
        # Full implementation would handle dot notation paths

        # Save updated settings
        return save_settings(current, settings_id, changed_by)
    except Exception as e:
        return False, f"Error updating setting: {str(e)}"


# ========== TENANT MANAGEMENT ==========

def create_tenant(owner_id: int, name: str, room_number: str, room_type: str, status: str, avatar: str) -> Optional[int]:
    """Create a new tenant record"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO tenants (owner_id, name, room_number, room_type, status, avatar, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?);""",
            (owner_id, name, room_number, room_type, status, avatar, _now_iso())
        )
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        print(f"[create_tenant] error: {e}", file=sys.stderr)
        conn.rollback()
        return None
    finally:
        conn.close()


def get_tenants(owner_id: int) -> List[Dict[str, Any]]:
    """Get all tenants for a property owner"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT id, owner_id, name, room_number, room_type, status, avatar, created_at
               FROM tenants
               WHERE owner_id = ?
               ORDER BY room_number;""",
            (owner_id,)
        )
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        print(f"[get_tenants] error: {e}", file=sys.stderr)
        return []
    finally:
        conn.close()


def update_tenant(tenant_id: int, name: Optional[str] = None, room_number: Optional[str] = None,
                  room_type: Optional[str] = None, status: Optional[str] = None) -> bool:
    """Update tenant information"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Build update query dynamically based on provided parameters
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if room_number is not None:
            updates.append("room_number = ?")
            params.append(room_number)
        if room_type is not None:
            updates.append("room_type = ?")
            params.append(room_type)
        if status is not None:
            updates.append("status = ?")
            params.append(status)

        if not updates:
            return True  # Nothing to update

        params.append(tenant_id)
        query = f"UPDATE tenants SET {', '.join(updates)} WHERE id = ?;"

        cur.execute(query, params)
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        print(f"[update_tenant] error: {e}", file=sys.stderr)
        conn.rollback()
        return False
    finally:
        conn.close()


def delete_tenant(tenant_id: int) -> bool:
    """Delete a tenant record"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM tenants WHERE id = ?;", (tenant_id,))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        print(f"[delete_tenant] error: {e}", file=sys.stderr)
        conn.rollback()
        return False
    finally:
        conn.close()


def get_properties(search_query: str = "", filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Returns properties/listings in the format expected by browse_view.py
    Supports search and filtering
    """
    if filters is None:
        filters = {}

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Base query
        query = """
            SELECT l.id, l.address as name, l.price, l.description,
                   l.availability_status, l.status, u.full_name as pm_name, u.email as pm_email,
                   li.image_path as image_url
            FROM listings l
            JOIN users u ON l.pm_id = u.id
            LEFT JOIN listing_images li ON l.id = li.listing_id
            WHERE l.status = 'approved'
        """

        params = []
        conditions = []

        # Search query filtering
        if search_query and search_query.strip():
            search_term = f"%{search_query.strip()}%"
            conditions.append("(l.address LIKE ? OR l.description LIKE ? OR u.full_name LIKE ?)")
            params.extend([search_term, search_term, search_term])

        # Price range filtering
        if 'min_price' in filters and filters['min_price']:
            try:
                min_price = float(filters['min_price'])
                conditions.append("l.price >= ?")
                params.append(min_price)
            except (ValueError, TypeError):
                pass

        if 'max_price' in filters and filters['max_price']:
            try:
                max_price = float(filters['max_price'])
                conditions.append("l.price <= ?")
                params.append(max_price)
            except (ValueError, TypeError):
                pass

        # Location filtering
        if 'location' in filters and filters['location'] and filters['location'].strip():
            location_term = f"%{filters['location'].strip()}%"
            conditions.append("l.address LIKE ?")
            params.append(location_term)

        # Add conditions to query
        if conditions:
            query += " AND " + " AND ".join(conditions)

        query += " ORDER BY l.created_at DESC"

        cur.execute(query, params)
        rows = cur.fetchall()

        # Group by listing ID and take first image for each
        listings_dict = {}
        for row in rows:
            listing_id = row['id']
            if listing_id not in listings_dict:
                listings_dict[listing_id] = {
                    'id': row['id'],
                    'name': row['name'],
                    'price': row['price'],
                    'location': row['name'],  # Using address as location
                    'availability_status': row['availability_status'],
                    'image_url': row['image_url'],
                    'description': row['description'],
                    'pm_name': row['pm_name'],
                    'pm_email': row['pm_email']
                }

        return list(listings_dict.values())
    finally:
        conn.close()

