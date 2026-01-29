from sqlalchemy.orm import Session
from typing import List, Tuple, Optional
from uuid import UUID

from app.models.vendor import Vendor


class VendorService:
    """Service for managing vendors"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_vendor(self, vendor_id: UUID) -> Optional[Vendor]:
        """Get a vendor by ID"""
        return self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
    
    def list_vendors(
        self,
        skip: int = 0,
        limit: int = 100,
        trade_type: Optional[str] = None
    ) -> Tuple[List[Vendor], int]:
        """List vendors with optional trade type filter"""
        query = self.db.query(Vendor)
        
        if trade_type:
            query = query.filter(Vendor.trade_specialties.contains([trade_type]))
        
        total = query.count()
        vendors = query.offset(skip).limit(limit).all()
        
        return vendors, total
    
    def create_or_update_vendor(self, vendor_data: dict) -> Vendor:
        """Create a new vendor or update existing one"""
        # Check if vendor exists by phone or email
        existing = None
        if vendor_data.get("phone"):
            existing = self.db.query(Vendor).filter(
                Vendor.phone == vendor_data["phone"]
            ).first()
        
        if existing:
            # Update existing vendor
            for key, value in vendor_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            vendor = existing
        else:
            # Create new vendor
            vendor = Vendor(**vendor_data)
            self.db.add(vendor)
        
        self.db.commit()
        self.db.refresh(vendor)
        return vendor
