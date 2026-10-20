"""
Reservation data model
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class ReservationStatus(Enum):
    """Reservation status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


@dataclass
class Reservation:
    """Reservation data model"""
    id: int
    listing_id: int
    tenant_id: int
    start_date: str
    end_date: str
    status: ReservationStatus
    created_at: datetime

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'listing_id': self.listing_id,
            'tenant_id': self.tenant_id,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'status': self.status.value,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_db_row(cls, row):
        """Create Reservation from database row"""
        return cls(
            id=row['id'],
            listing_id=row['listing_id'],
            tenant_id=row['tenant_id'],
            start_date=row['start_date'],
            end_date=row['end_date'],
            status=ReservationStatus(row['status']),
            created_at=datetime.fromisoformat(row['created_at'])
        )

    def is_active(self) -> bool:
        """Check if reservation is active"""
        return self.status == ReservationStatus.CONFIRMED

    def is_pending(self) -> bool:
        """Check if reservation is pending"""
        return self.status == ReservationStatus.PENDING