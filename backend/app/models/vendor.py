from sqlalchemy import Column, String, Float, JSON, DateTime, ARRAY, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    business_name = Column(String(255), nullable=False)
    contact_name = Column(String(200))
    phone = Column(String(50))
    email = Column(String(200))
    website = Column(String(500))

    address = Column(String(500))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    latitude = Column(Float)
    longitude = Column(Float)
    service_radius_miles = Column(Float, default=30.0)
    trade_specialties = Column(ARRAY(String), default=[])

    google_rating = Column(Float)
    google_review_count = Column(Integer, default=0)
    yelp_rating = Column(Float)
    yelp_review_count = Column(Integer, default=0)
    bbb_rating = Column(String(10))
    composite_score = Column(Float)

    google_place_id = Column(String(200))
    yelp_business_id = Column(String(200))
    bbb_business_id = Column(String(200))

    source_data = Column(JSON)
    last_contacted = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    quotes = relationship(
        "Quote", back_populates="vendor", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Vendor {self.business_name}>"
