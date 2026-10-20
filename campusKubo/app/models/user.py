"""
User data model
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRole(Enum):
    """User role enumeration"""
    TENANT = "tenant"
    PROPERTY_MANAGER = "pm"
    PM = "pm"  # alias for compatibility
    ADMIN = "admin"


@dataclass
class User:
    """User data model"""
    id: int
    email: str
    full_name: Optional[str]
    role: UserRole
    created_at: Optional[datetime] = None
    phone: Optional[str] = None
    is_active: bool = True

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role.value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_db_row(cls, row):
        # Normalize role values that may be stored as human-friendly strings
        # Support different row types (`dict`-like or `sqlite3.Row`)
        try:
            raw_role = row['role']
        except Exception:
            # fallback for dict-like objects or other mappings
            raw_role = row.get('role') if hasattr(row, 'get') else None

        role_str = str(raw_role or '').strip()

        # Try direct enum conversion first (common case: 'tenant','pm','admin')
        try:
            role_enum = UserRole(role_str)
        except Exception:
            rl = role_str.lower()
            if 'admin' in rl:
                role_enum = UserRole.ADMIN
            elif 'pm' in rl or 'property' in rl or 'property manager' in rl or 'manager' in rl:
                role_enum = UserRole.PROPERTY_MANAGER
            elif 'tenant' in rl:
                role_enum = UserRole.TENANT
            else:
                # Fallback: if numeric or unknown, treat as tenant to be safe
                role_enum = UserRole.TENANT

        # full_name may be stored in different row types
        try:
            full_name_val = row['full_name']
        except Exception:
            full_name_val = row.get('full_name') if hasattr(row, 'get') else None

        created_at_val = None
        try:
            if 'created_at' in row.keys() and row['created_at']:
                created_at_val = datetime.fromisoformat(row['created_at'])
        except Exception:
            created_at_val = None

        phone_val = None
        try:
            phone_val = row['phone']
        except Exception:
            phone_val = row.get('phone') if hasattr(row, 'get') else None

        is_active_val = True
        try:
            if 'is_active' in row.keys():
                is_active_val = bool(row['is_active'])
        except Exception:
            is_active_val = True

        return cls(
            id=row['id'],
            email=row['email'],
            full_name=full_name_val if full_name_val is not None else None,
            role=role_enum,
            created_at=created_at_val,
            phone=phone_val,
            is_active=is_active_val
        )

    def is_tenant(self) -> bool:
        """Check if user is a tenant"""
        return self.role == UserRole.TENANT

    def is_property_manager(self) -> bool:
        """Check if user is a property manager"""
        return self.role == UserRole.PROPERTY_MANAGER

    def is_admin(self) -> bool:
        """Check if user is an admin"""
        return self.role == UserRole.ADMIN