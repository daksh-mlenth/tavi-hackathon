from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.communication_log import CommunicationChannel


class CommunicationLogResponse(BaseModel):
    id: UUID
    work_order_id: UUID
    vendor_id: Optional[UUID] = None
    vendor_name: Optional[str] = None  # Added vendor name
    channel: CommunicationChannel
    direction: str
    subject: Optional[str] = None
    message: Optional[str] = None
    response: Optional[str] = None
    sent_successfully: bool
    timestamp: datetime
    
    class Config:
        from_attributes = True
