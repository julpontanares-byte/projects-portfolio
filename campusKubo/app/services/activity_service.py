"""
Activity Service
Delegates to storage.db helpers to log and fetch recent activity.
"""

import os
import sys
# Ensure top-level `storage` package is importable when running from `app.services`
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from storage.db import log_activity, get_recent_activity


class ActivityService:

    @staticmethod
    def log_activity(user_id: int, action: str, description: str = ""):
        """
        Saves an activity entry to the database.
        """
        log_activity(user_id, action, description)

    @staticmethod
    def get_recent_activities(limit: int = 10):
        """
        Returns the most recent activities.
        """
        rows = get_recent_activity(limit)
        activities = []
        for row in rows:
            # sqlite Row supports both index and key access
            def _get(row_obj, key, idx=None):
                if hasattr(row_obj, "keys") and key in row_obj.keys():
                    return row_obj[key]
                if idx is not None and len(row_obj) > idx:
                    return row_obj[idx]
                return None

            activities.append({
                "id": _get(row, "id", 0),
                "user_id": _get(row, "user_id", 1),
                "user_email": _get(row, "user_email", 2),
                "action": _get(row, "action", 3),
                "description": _get(row, "details", 4),
                "timestamp": _get(row, "created_at", 5),
            })
        return activities