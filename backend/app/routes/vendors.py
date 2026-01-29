from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.schemas.vendor import VendorResponse, VendorList
from app.services.vendor_service import VendorService

router = APIRouter()


@router.get("", response_model=VendorList)
def list_vendors(
    skip: int = 0,
    limit: int = 100,
    trade_type: str = None,
    db: Session = Depends(get_db)
):
    """List all vendors, optionally filtered by trade type"""
    service = VendorService(db)
    vendors, total = service.list_vendors(skip, limit, trade_type)
    return VendorList(vendors=vendors, total=total)


@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(
    vendor_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific vendor by ID"""
    service = VendorService(db)
    vendor = service.get_vendor(vendor_id)
    
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return vendor


@router.get("/{vendor_id}/score")
def get_vendor_score(
    vendor_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed scoring breakdown for a vendor"""
    service = VendorService(db)
    vendor = service.get_vendor(vendor_id)
    
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return {
        "vendor_id": str(vendor.id),
        "business_name": vendor.business_name,
        "google_rating": vendor.google_rating,
        "google_review_count": vendor.google_review_count,
        "yelp_rating": vendor.yelp_rating,
        "yelp_review_count": vendor.yelp_review_count,
        "bbb_rating": vendor.bbb_rating,
        "composite_score": vendor.composite_score
    }
