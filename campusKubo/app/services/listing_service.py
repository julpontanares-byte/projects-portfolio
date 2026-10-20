"""
Listing service - business logic for listings
"""
from storage.db import (
    get_connection, get_listings, get_listing_by_id, get_listing_images,
    create_listing, update_listing, delete_listing, delete_listing_admin,
    get_listing_availability, change_listing_status
)
from models.listing import Listing
from typing import List, Optional, Tuple
from datetime import datetime
from services.refresh_service import notify as _notify_refresh


class ListingService:
    """Handles listing operations"""

    @staticmethod
    def get_all_listings(owner_id: Optional[int] = None) -> List[Listing]:
        """Get all listings, optionally filtered by owner"""
        db_listings = get_listings(owner_id)
        listings = []

        for row in db_listings:
            images = get_listing_images(row['id'])
            # Construct Listing model with owner info if your model supports it.
            # We'll pass owner_email and owner_name via the row to the model
            listing = Listing.from_db_row(row, images)
            # attach owner info if model doesn't already keep it
            if hasattr(listing, "owner_email") is False and "owner_email" in row.keys():
                setattr(listing, "owner_email", row["owner_email"])
            if hasattr(listing, "owner_name") is False and "owner_name" in row.keys():
                setattr(listing, "owner_name", row["owner_name"])
            listings.append(listing)

        return listings

    @staticmethod
    def get_listing_by_id(listing_id: int) -> Optional[Listing]:
        """Get single listing by ID"""
        row = get_listing_by_id(listing_id)
        if not row:
            return None
        images = get_listing_images(listing_id)
        return Listing.from_db_row(row, images)

    @staticmethod
    def check_availability(listing_id: int) -> bool:
        """A listing is considered available if it has no approved/confirmed reservations"""
        reservations = get_listing_availability(listing_id)
        return len(reservations) == 0

    @staticmethod
    def create_new_listing(
        owner_id: int,
        address: str,
        price: float,
        description: str,
        lodging_details: str,
        image_paths: List[str]
    ) -> Tuple[bool, str, Optional[int]]:
        """Create new listing and return (success, message, id)"""

        if not address or not address.strip():
            return False, "Address is required", None
        if price <= 0:
            return False, "Price must be greater than 0", None
        if not description or not description.strip():
            return False, "Description is required", None
        if not image_paths:
            return False, "At least one image is required", None

        listing_id = create_listing(
            owner_id, address, price, description,
            lodging_details, image_paths
        )

        if listing_id:
            try:
                _notify_refresh()
            except Exception:
                pass
            return True, "Listing created successfully", listing_id
        else:
            return False, "Failed to create listing", None

    @staticmethod
    def update_existing_listing(
        listing_id: int,
        owner_id: int,
        address: str,
        price: float,
        description: str,
        lodging_details: str,
        image_paths: List[str],
        status: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Update listing including optional status"""
        if not address or not address.strip():
            return False, "Address is required"

        if price <= 0:
            return False, "Price must be greater than 0"

        if not description or not description.strip():
            return False, "Description is required"

        if image_paths is None or not isinstance(image_paths, list):
            return False, "Image paths must be provided as a list"

        success = update_listing(
            listing_id, owner_id, address, price,
            description, lodging_details, image_paths, status
        )

        if success:
            try:
                _notify_refresh()
            except Exception:
                pass
            return True, "Listing updated successfully"
        else:
            return False, "Failed to update listing or unauthorized"

    @staticmethod
    def delete_listing_by_id(listing_id: int, owner_id: int) -> Tuple[bool, str]:
        """
        Owner-level deletion (used by PMs/owners). Requires owner_id match.
        """
        success = delete_listing(listing_id, owner_id)
        if success:
            try:
                _notify_refresh()
            except Exception:
                pass
            return True, "Listing deleted successfully"
        else:
            return False, "Failed to delete listing or unauthorized"

    @staticmethod
    def delete_listing_by_admin(listing_id: int) -> Tuple[bool, str]:
        """
        Admin-level deletion (no owner check).
        """
        success = delete_listing_admin(listing_id)
        if success:
            try:
                _notify_refresh()
            except Exception:
                pass
            return True, "Listing deleted by admin"
        else:
            return False, "Failed to delete listing (admin)"

    @staticmethod
    def search_listings(query: str, all_listings: List[Listing]) -> List[Listing]:
        """Search listings by address or description"""
        if not query:
            return all_listings

        q = query.lower()
        return [
            listing for listing in all_listings
            if q in getattr(listing, "address", "").lower()
            or q in getattr(listing, "description", "").lower()
        ]

    @staticmethod
    def update_existing_listing_admin(
        listing_id: int,
        address: str,
        price: float,
        description: str,
        lodging_details: str,
        status: str,
        pm_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Admin-level listing update (can change owner, status, etc.)"""
        if not address or not address.strip():
            return False, "Address is required"
        if price <= 0:
            return False, "Price must be greater than 0"
        if not description or not description.strip():
            return False, "Description is required"

        conn = get_connection()
        cur = conn.cursor()
        try:
            if pm_id is not None:
                cur.execute(
                    """UPDATE listings SET address = ?, price = ?, description = ?,
                       lodging_details = ?, status = ?, pm_id = ?, updated_at = ?
                       WHERE id = ?""",
                    (address, price, description, lodging_details, status, pm_id, datetime.utcnow().isoformat(), listing_id)
                )
            else:
                cur.execute(
                    """UPDATE listings SET address = ?, price = ?, description = ?,
                       lodging_details = ?, status = ?, updated_at = ? WHERE id = ?""",
                    (address, price, description, lodging_details, status, datetime.utcnow().isoformat(), listing_id)
                )
            conn.commit()
            if cur.rowcount > 0:
                try:
                    _notify_refresh()
                except Exception:
                    pass
                return True, "Listing updated successfully"
            return False, "Listing not found"
        except Exception as e:
            conn.rollback()
            return False, f"Error updating listing: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def filter_by_price(
        listings: List[Listing],
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[Listing]:
        if min_price is None and max_price is None:
            return listings

        filtered = []
        for L in listings:
            if min_price is not None and getattr(L, "price", 0) < min_price:
                continue
            if max_price is not None and getattr(L, "price", 0) > max_price:
                continue
            filtered.append(L)

        return filtered

    def get_all_listings_count(self) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM listings")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_occupancy_counts(self) -> tuple[int, int]:
        """
        Return (occupied_count, available_count) using the 'status' column added to listings.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM listings WHERE lower(status) = 'occupied'")
        occupied = cursor.fetchone()[0]
        # Count only available/approved as available; exclude pending from availability to reflect approval workflow.
        cursor.execute("SELECT COUNT(*) FROM listings WHERE lower(status) IN ('available','approved')")
        available = cursor.fetchone()[0]
        conn.close()
        return occupied, available
