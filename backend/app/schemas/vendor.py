from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class VendorResponse(BaseModel):
    id: UUID
    business_name: str
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    trade_specialties: List[str] = []
    google_rating: Optional[float] = None
    google_review_count: Optional[int] = None
    yelp_rating: Optional[float] = None
    yelp_review_count: Optional[int] = None
    composite_score: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class VendorList(BaseModel):
    vendors: List[VendorResponse]
    total: int
