"""
Notification data model
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class NotificationType(Enum):
    """Notification type enumeration"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    RESERVATION = "reservation"
    PAYMENT = "payment"


@dataclass
class Notification:
    """Notification data model"""
    id: Optional[int]
    user_id: int
    type: NotificationType
    title: str
    message: str
    is_read: bool = False
    created_at: Optional[datetime] = None

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type.value,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True