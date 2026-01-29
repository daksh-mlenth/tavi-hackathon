from sqlalchemy import Column, String, Float, DateTime, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class QuoteStatus(str, enum.Enum):
    PENDING = "pending"  # Vendor discovered, not yet contacted
    REQUESTED = "requested"  # Quote request sent to vendor
    RECEIVED = "received"  # Vendor responded with quote
    ACCEPTED = "accepted"  # Customer accepted quote
    REJECTED = "rejected"  # Quote rejected
    EXPIRED = "expired"  # Quote expired


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    work_order_id = Column(UUID(as_uuid=True), ForeignKey("work_orders.id"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    
    # Quote Details
    price = Column(Float)
    currency = Column(String(10), default="USD")
    availability_date = Column(DateTime)
    estimated_duration_hours = Column(Float)
    
    # Status
    status = Column(SQLEnum(QuoteStatus), default=QuoteStatus.PENDING)
    
    # Communication
    quote_text = Column(Text)  # Raw quote text from vendor
    notes = Column(Text)  # Internal notes
    
    # Scoring (for ranking quotes)
    price_score = Column(Float)  # Normalized price score
    quality_score = Column(Float)  # Based on vendor rating
    availability_score = Column(Float)  # Based on availability
    composite_score = Column(Float)  # Overall score
    
    # Metadata
    requested_at = Column(DateTime, default=datetime.utcnow)
    received_at = Column(DateTime)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    work_order = relationship("WorkOrder", back_populates="quotes")
    vendor = relationship("Vendor", back_populates="quotes")
    
    def __repr__(self):
        return f"<Quote {self.id} - ${self.price}>"
