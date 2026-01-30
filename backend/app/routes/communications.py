from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.schemas.communication import CommunicationLogResponse
from app.services.communication_service import CommunicationService

router = APIRouter()


@router.get(
    "/work-order/{work_order_id}", response_model=List[CommunicationLogResponse]
)
def get_communications_for_work_order(
    work_order_id: UUID, db: Session = Depends(get_db)
):
    """Get all communications for a specific work order (unified stream)"""
    service = CommunicationService(db)
    communications = service.get_communications_for_work_order(work_order_id)
    return communications


@router.get("/vendor/{vendor_id}", response_model=List[CommunicationLogResponse])
def get_communications_for_vendor(vendor_id: UUID, db: Session = Depends(get_db)):
    """Get all communications with a specific vendor"""
    service = CommunicationService(db)
    communications = service.get_communications_for_vendor(vendor_id)
    return communications
