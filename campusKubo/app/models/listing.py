"""
Listing data model
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class Listing:
    """Property listing data model"""
    id: int
    pm_id: int
    address: str
    price: float
    description: str
    lodging_details: Optional[str]
    created_at: datetime
    updated_at: datetime
    images: list = field(default_factory=list)
    status: str = "pending"

    def __post_init__(self):
        """Initialize images list if None"""
        if self.images is None:
            self.images = []

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'pm_id': self.pm_id,
            'address': self.address,
            'price': self.price,
            'description': self.description,
            'lodging_details': self.lodging_details,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'images': self.images
        }

    @classmethod
    def from_db_row(cls, row, images: List[str] = None or []):
        """Create Listing from database row with defensive parsing.

        Ensures `price` is a float when possible. If parsing fails, falls back
        to 0.0 and leaves a diagnostic on stderr so bad DB rows can be fixed.
        Also handles created_at/updated_at parsing more robustly.
        """
        # Defensive price parsing
        raw_price = row['price'] if 'price' in row.keys() else None

        price_val = 0.0
        if raw_price is None:
            price_val = 0.0
        else:
            try:
                price_val = float(raw_price)
            except (TypeError, ValueError):
                try:
                    # attempt to clean common formatting like commas and currency symbols
                    s = str(raw_price).replace(',', '').replace('\u20b1', '').strip()
                    price_val = float(s)
                except Exception:
                    import sys
                    lid = (row['id'] if 'id' in row.keys() else None)
                    print(f"[Listing.from_db_row] invalid price for listing id={lid}: {raw_price}", file=sys.stderr)
                    price_val = 0.0

        # Defensive datetime parsing
        def _parse_dt(val):
            if not val:
                return datetime.utcnow()
            try:
                return datetime.fromisoformat(val)
            except Exception:
                try:
                    # sometimes stored with space separator
                    return datetime.fromisoformat(val.replace(' ', 'T'))
                except Exception:
                    return datetime.utcnow()

        created = _parse_dt(row['created_at'] if 'created_at' in row.keys() else None)
        updated = _parse_dt(row['updated_at'] if 'updated_at' in row.keys() else None)

        return cls(
            id=(row['id'] if 'id' in row.keys() else 0),
            pm_id=(row['pm_id'] if 'pm_id' in row.keys() else 0),
            address=(row['address'] if 'address' in row.keys() else ""),
            price=price_val,
            description=(row['description'] if 'description' in row.keys() else ""),
            lodging_details=(row['lodging_details'] if 'lodging_details' in row.keys() else None),
            created_at=created,
            updated_at=updated,
            images=images or [],
            status=(row['status'] if 'status' in row.keys() else 'pending')
        )