from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum, ForeignKey, Boolean, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class CommunicationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    SYSTEM = "system"


class CommunicationLog(Base):
    __tablename__ = "communication_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    work_order_id = Column(UUID(as_uuid=True), ForeignKey("work_orders.id"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=True)
    
    # Communication Details
    channel = Column(SQLEnum(CommunicationChannel), nullable=False)
    direction = Column(String(20))  # 'outbound' or 'inbound'
    
    # Content
    subject = Column(String(500))
    message = Column(Text)
    response = Column(Text)
    
    # Status
    sent_successfully = Column(Boolean, default=False)
    error_message = Column(Text)
    
    # Phone-specific
    call_duration_seconds = Column(Float)
    call_recording_url = Column(String(500))
    call_transcript = Column(Text)
    
    # AI Processing
    ai_model_used = Column(String(100))
    ai_prompt = Column(Text)
    ai_response = Column(Text)
    ai_metadata = Column(JSON)  # Additional AI processing info
    
    # Metadata
    external_id = Column(String(200))  # ID from external service (Twilio, SendGrid, etc.)
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    work_order = relationship("WorkOrder", back_populates="communication_logs")
    
    def __repr__(self):
        return f"<CommunicationLog {self.channel} - {self.direction}>"
