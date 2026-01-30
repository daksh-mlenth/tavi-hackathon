from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.models.quote import QuoteStatus


class VendorDetails(BaseModel):
    id: UUID
    business_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    google_rating: Optional[float] = None
    google_review_count: Optional[int] = None
    yelp_rating: Optional[float] = None
    yelp_review_count: Optional[int] = None
    composite_score: Optional[float] = None
    trade_specialties: Optional[List[str]] = None
    price_level: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to extract price_level from source_data"""
        vendor_dict = {
            "id": obj.id,
            "business_name": obj.business_name,
            "phone": obj.phone,
            "email": obj.email,
            "address": obj.address,
            "city": obj.city,
            "state": obj.state,
            "google_rating": obj.google_rating,
            "google_review_count": obj.google_review_count,
            "yelp_rating": obj.yelp_rating,
            "yelp_review_count": obj.yelp_review_count,
            "composite_score": obj.composite_score,
            "trade_specialties": obj.trade_specialties,
            "price_level": obj.source_data.get("price_display")
            if obj.source_data
            else None,
        }
        return cls(**vendor_dict)


class QuoteResponse(BaseModel):
    id: UUID
    work_order_id: UUID
    vendor_id: UUID
    vendor: Optional[VendorDetails] = None
    price: Optional[float] = None
    availability_date: Optional[datetime] = None
    estimated_duration_hours: Optional[float] = None
    status: QuoteStatus
    quote_text: Optional[str] = None
    composite_score: Optional[float] = None
    requested_at: datetime
    received_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuoteList(BaseModel):
    quotes: List[QuoteResponse]
    total: int
