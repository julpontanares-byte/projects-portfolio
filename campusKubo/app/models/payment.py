# app/models/payment.py

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Payment:
    """Payment model representing a transaction in the system."""

    id: Optional[int]
    user_id: Optional[int]
    listing_id: Optional[int]
    amount: float
    status: str = "completed"  # completed, refunded, pending, failed
    payment_method: str = "unknown"  # cash, card, online_banking, check
    created_at: Optional[str] = None or datetime.utcnow().isoformat()
    updated_at: Optional[str] = None or datetime.utcnow().isoformat()
    refunded_amount: float = 0.0
    refund_reason: Optional[str] = None
    notes: Optional[str] = None

    @staticmethod
    def from_db_row(row):
        """Convert database row to Payment object."""
        if not row:
            return None

        # Handle both dict and tuple row types
        if isinstance(row, dict):
            return Payment(
                id=row.get('id'),
                user_id=row.get('user_id'),
                listing_id=row.get('listing_id'),
                amount=float(row.get('amount', 0)),
                status=row.get('status', 'completed'),
                payment_method=row.get('payment_method', 'unknown'),
                created_at=row.get('created_at'),
                updated_at=row.get('updated_at'),
                refunded_amount=float(row.get('refunded_amount', 0)),
                refund_reason=row.get('refund_reason'),
                notes=row.get('notes')
            )
        else:
            # Tuple-like row object
            return Payment(
                id=row['id'],
                user_id=row['user_id'],
                listing_id=row['listing_id'],
                amount=float(row['amount']),
                status=row.get('status', 'completed') if hasattr(row, 'get') else 'completed',
                payment_method=row.get('payment_method', 'unknown') if hasattr(row, 'get') else 'unknown',
                created_at=row.get('created_at') if hasattr(row, 'get') else None,
                updated_at=row.get('updated_at') if hasattr(row, 'get') else None,
                refunded_amount=float(row.get('refunded_amount', 0)) if hasattr(row, 'get') else 0.0,
                refund_reason=row.get('refund_reason') if hasattr(row, 'get') else None,
                notes=row.get('notes') if hasattr(row, 'get') else None
            )

    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'listing_id': self.listing_id,
            'amount': self.amount,
            'status': self.status,
            'payment_method': self.payment_method,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'refunded_amount': self.refunded_amount,
            'refund_reason': self.refund_reason,
            'notes': self.notes
        }
