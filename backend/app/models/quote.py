from sqlalchemy import Column, String, Float, DateTime, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class QuoteStatus(str, enum.Enum):
    PENDING = "pending"
    REQUESTED = "requested"
    RECEIVED = "received"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_order_id = Column(UUID(as_uuid=True), ForeignKey("work_orders.id"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    
    price = Column(Float)
    currency = Column(String(10), default="USD")
    availability_date = Column(DateTime)
    estimated_duration_hours = Column(Float)
    status = Column(SQLEnum(QuoteStatus), default=QuoteStatus.PENDING)
    
    quote_text = Column(Text)
    notes = Column(Text)
    
    price_score = Column(Float)
    quality_score = Column(Float)
    availability_score = Column(Float)
    composite_score = Column(Float)
    
    requested_at = Column(DateTime, default=datetime.utcnow)
    received_at = Column(DateTime)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    work_order = relationship("WorkOrder", back_populates="quotes")
    vendor = relationship("Vendor", back_populates="quotes")
    
    def __repr__(self):
        return f"<Quote {self.id} - ${self.price}>"
