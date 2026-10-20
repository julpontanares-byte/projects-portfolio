# app/state/profile_state.py
"""
Profile State Management
Manages user profile data state
"""
from typing import Optional
from dataclasses import dataclass


@dataclass
class ProfileState:
    """State container for user profile information"""
    user_id: int
    first_name: str = ""
    last_name: str = ""
    gender: str = ""
    email: str = ""
    contact_number: str = ""
    phone: str = ""
    role: str = ""
    avatar_url: str = ""
    house_no: str = ""
    street: str = ""
    barangay: str = ""
    city: str = ""
    actual_password: Optional[str] = None
    password_visible: bool = False

    @property
    def full_name(self) -> str:
        """Get full name from first and last name"""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def full_address(self) -> str:
        """Get formatted full address"""
        parts = [
            self.house_no,
            self.street,
            self.barangay,
            self.city
        ]
        return ", ".join(p for p in parts if p)

    def update_from_dict(self, data: dict):
        """Update state from dictionary"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    def to_dict(self) -> dict:
        """Convert state to dictionary"""
        return {
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'gender': self.gender,
            'email': self.email,
            'contact_number': self.contact_number,
            'phone': self.phone,
            'role': self.role,
            'avatar_url': self.avatar_url,
            'house_no': self.house_no,
            'street': self.street,
            'barangay': self.barangay,
            'city': self.city,
        }
