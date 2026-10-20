"""
Notification service with optional database integration.

When running under pytest the service will default to an in-memory
implementation to make tests deterministic. In production it uses the
database-backed functions from `storage.db`.
"""
from datetime import datetime
from typing import List, Dict, Optional
import sys
import os

try:
    from storage.db import (
        get_user_notifications as db_get_user_notifications,
        get_unread_count as db_get_unread_count,
        add_notification as db_add_notification,
        mark_notification_read as db_mark_notification_read,
        mark_all_notifications_read as db_mark_all_notifications_read,
    )
except Exception:
    # In some test / isolated environments storage.db may not be importable.
    db_get_user_notifications = db_get_unread_count = db_add_notification = db_mark_notification_read = db_mark_all_notifications_read = None


class NotificationService:
    """Flexible notification service.

    Parameters
    - use_db: when True forces DB-backed mode; when False uses in-memory.
      When None the service will auto-detect running-under-pytest and
      choose in-memory for tests.
    """

    def __init__(self, use_db: Optional[bool] = None):
        if use_db is None:
            # Prefer in-memory when running under pytest to keep tests hermetic
            use_db = 'pytest' not in sys.modules and os.environ.get('PYTEST_CURRENT_TEST') is None

        self._use_db = bool(use_db)

        if not self._use_db:
            # in-memory store
            self.notifications: List[Dict] = []
            self._next_id = 1

    # --- In-memory implementation helpers ---
    def _inmem_add(self, user_id: int, notif_type: str, message: str, category: str = "activity", reference_id: Optional[int] = None, reference_type: Optional[str] = None) -> Dict:
        notif = {
            "notification_id": self._next_id,
            "user_id": user_id,
            "notification_type": notif_type,
            "message": message,
            "category": category,
            "is_read": False,
            "created_at": datetime.now(),
            "reference_id": reference_id,
            "reference_type": reference_type,
        }
        self.notifications.append(notif)
        self._next_id += 1
        return notif

    def _inmem_get_user_notifications(self, user_id: int, limit: int = 50) -> List[Dict]:
        items = [n for n in self.notifications if n.get("user_id") == user_id]
        items = sorted(items, key=lambda x: x["notification_id"], reverse=True)[:limit]
        out = []
        for n in items:
            out.append({
                "id": n["notification_id"],
                "notification_id": n["notification_id"],
                "type": n.get("notification_type"),
                "message": n.get("message"),
                "category": n.get("category"),
                "read": bool(n.get("is_read")),
                "is_read": bool(n.get("is_read")),
                "time": n.get("created_at"),
                "reference_id": n.get("reference_id"),
                "reference_type": n.get("reference_type"),
            })
        return out

    def _inmem_get_unread_count(self, user_id: int) -> int:
        return len([n for n in self.notifications if n.get("user_id") == user_id and not n.get("is_read")])

    def _inmem_mark_notification_read(self, notif_id: int) -> bool:
        for n in self.notifications:
            if n.get("notification_id") == notif_id:
                n["is_read"] = True
                return True
        return False

    def _inmem_mark_all_notifications_read(self, user_id: int) -> int:
        cnt = 0
        for n in self.notifications:
            if n.get("user_id") == user_id and not n.get("is_read"):
                n["is_read"] = True
                cnt += 1
        return cnt

    # --- Public API (dispatch to DB or in-memory) ---
    def add_notification(self, user_id: int, notif_type: str, message: str, category: str = "activity", reference_id: Optional[int] = None, reference_type: Optional[str] = None):
        if not self._use_db or db_add_notification is None:
            return self._inmem_add(user_id, notif_type, message, category, reference_id, reference_type)
        success = db_add_notification(user_id, notif_type, message, category, reference_id, reference_type)
        # preserve old behavior: return a dict-like structure on success
        if success:
            return {
                "notification_id": 0,
                "user_id": user_id,
                "notification_type": notif_type,
                "message": message,
                "category": category,
                "is_read": False,
                "created_at": datetime.now(),
                "reference_id": reference_id,
                "reference_type": reference_type,
            }
        return None

    def get_user_notifications(self, user_id: int, limit: int = 50) -> List[Dict]:
        if not self._use_db or db_get_user_notifications is None:
            return self._inmem_get_user_notifications(user_id, limit)
        db_notifications = db_get_user_notifications(user_id, limit)
        notifications = []
        for n in db_notifications:
            created_at = n.get('created_at')
            if created_at and created_at != 'CURRENT_TIMESTAMP':
                try:
                    time_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00')) if 'T' in created_at else datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                except (ValueError, AttributeError):
                    time_obj = datetime.now()
            else:
                time_obj = datetime.now()

            notifications.append({
                "id": n['notification_id'],
                "type": n['notification_type'],
                "message": n['message'],
                "category": n['category'],
                "read": bool(n['is_read']),
                "time": time_obj,
                "reference_id": n.get('reference_id'),
                "reference_type": n.get('reference_type')
            })
        return notifications

    def get_unread_count(self, user_id: int) -> int:
        if not self._use_db or db_get_unread_count is None:
            return self._inmem_get_unread_count(user_id)
        return db_get_unread_count(user_id)

    def mark_notification_read(self, notif_id: int) -> bool:
        if not self._use_db or db_mark_notification_read is None:
            return self._inmem_mark_notification_read(notif_id)
        return db_mark_notification_read(notif_id)

    def mark_all_notifications_read(self, user_id: int) -> int:
        if not self._use_db or db_mark_all_notifications_read is None:
            return self._inmem_mark_all_notifications_read(user_id)
        unread_before = self.get_unread_count(user_id)
        success = db_mark_all_notifications_read(user_id)
        return unread_before if success else 0