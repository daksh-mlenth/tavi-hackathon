from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.models.quote import Quote
from app.models.communication_log import CommunicationChannel
from app.services.communication_service import CommunicationService
from app.services.ai_agent_service import AIAgentService
from app.constants import AI_MODEL

router = APIRouter()


class ConfirmVendorRequest(BaseModel):
    quote_id: str
    facility_manager_email: str
    facility_manager_name: str = "Facility Manager"


@router.post("/confirm-vendor")
async def confirm_vendor_selection(
    request: ConfirmVendorRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Initiate vendor confirmation process:
    1. Send confirmation email to facility manager
    2. Send dispatch confirmation to vendor
    Both need approval before final dispatch
    """
    quote = db.query(Quote).filter(Quote.id == UUID(request.quote_id)).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    work_order = quote.work_order
    vendor = quote.vendor
    
    # Update work order with selected vendor and facility manager info
    work_order.selected_vendor_id = vendor.id
    work_order.facility_manager_email = request.facility_manager_email
    work_order.facility_manager_name = request.facility_manager_name
    work_order.status = WorkOrderStatus.VENDOR_SELECTED
    
    # Mark quote as accepted
    quote.status = 'accepted'
    
    db.commit()
    
    # Send facility manager confirmation email
    background_tasks.add_task(
        send_facility_manager_confirmation,
        db, work_order.id, vendor.id
    )
    
    # Send vendor dispatch confirmation
    background_tasks.add_task(
        send_vendor_dispatch_confirmation,
        db, work_order.id, vendor.id
    )
    
    return {
        "status": "confirmations_sent",
        "work_order_id": str(work_order.id),
        "message": "Confirmation requests sent to facility manager and vendor"
    }


async def send_facility_manager_confirmation(db: Session, work_order_id: UUID, vendor_id: UUID):
    """Send confirmation email to facility manager"""
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    vendor = db.query(Quote).filter(Quote.work_order_id == work_order_id, Quote.vendor_id == vendor_id).first().vendor
    
    if not work_order or not vendor:
        return
    
    comm_service = CommunicationService(db)
    ai_service = AIAgentService()
    
    # Get quote details
    quote = db.query(Quote).filter(Quote.work_order_id == work_order_id, Quote.vendor_id == vendor_id).first()
    
    # Generate confirmation email (simple version without currency symbol)
    email_content = f"""Dear {work_order.facility_manager_name},

We have selected a vendor for the following work order:

Work Order: {work_order.title}
Vendor: {vendor.business_name}
Price: ${quote.price if quote else 'N/A'}
Availability: {quote.availability_date if quote else 'TBD'}

Please reply with "APPROVED" to confirm this selection, or "REJECT" with reasons if you have concerns.

Best regards,
Tavi Team"""
    
    # Log the outbound confirmation request
    comm_service.log_communication(
        work_order_id=work_order.id,
        vendor_id=None,  # This is to facility manager, not vendor
        channel=CommunicationChannel.EMAIL,
        direction="outbound",
        message=email_content,
        sent_successfully=True,
        metadata={
            "recipient": work_order.facility_manager_email,
            "recipient_name": work_order.facility_manager_name,
            "type": "facility_confirmation",
            "awaiting_response": True
        }
    )
    
    # Update status
    work_order.status = WorkOrderStatus.AWAITING_FACILITY_CONFIRMATION
    db.commit()
    
    print(f"📧 Sent facility manager confirmation to {work_order.facility_manager_email}")


async def send_vendor_dispatch_confirmation(db: Session, work_order_id: UUID, vendor_id: UUID):
    """Send dispatch confirmation to vendor"""
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    quote = db.query(Quote).filter(Quote.work_order_id == work_order_id, Quote.vendor_id == vendor_id).first()
    vendor = quote.vendor
    
    if not work_order or not vendor:
        return
    
    comm_service = CommunicationService(db)
    
    # Generate dispatch confirmation message
    message = f"""Hi {vendor.business_name},

Great news! You have been selected for this job:

{work_order.description}
Location: {work_order.location_address}
Start Date: {quote.availability_date}

Please reply "CONFIRMED" to confirm you can start on the agreed date, or contact us if there are any issues.

Thank you,
Tavi Team"""
    
    # Log the outbound dispatch confirmation
    comm_service.log_communication(
        work_order_id=work_order.id,
        vendor_id=vendor.id,
        channel=CommunicationChannel.EMAIL,
        direction="outbound",
        message=message,
        sent_successfully=True,
        metadata={
            "type": "vendor_dispatch_confirmation",
            "awaiting_response": True
        }
    )
    
    print(f"📧 Sent dispatch confirmation to {vendor.business_name}")


@router.post("/facility-confirm/{work_order_id}")
async def facility_manager_confirms(
    work_order_id: UUID,
    confirmation: dict,
    db: Session = Depends(get_db)
):
    """Handle facility manager confirmation (APPROVED/REJECT)"""
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    response = confirmation.get('response', '').upper()
    
    if 'APPROVED' in response or 'APPROVE' in response or 'YES' in response:
        work_order.facility_confirmed = datetime.utcnow()
        
        # Check if vendor also confirmed
        if work_order.vendor_dispatch_confirmed:
            work_order.status = WorkOrderStatus.DISPATCHED
        
        db.commit()
        
        return {"status": "approved", "message": "Facility manager approved vendor selection"}
    else:
        work_order.status = WorkOrderStatus.EVALUATING_QUOTES  # Go back to evaluation
        db.commit()
        return {"status": "rejected", "message": "Vendor selection rejected by facility manager"}


@router.post("/vendor-dispatch-confirm/{work_order_id}")
async def vendor_confirms_dispatch(
    work_order_id: UUID,
    confirmation: dict,
    db: Session = Depends(get_db)
):
    """Handle vendor dispatch confirmation"""
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    response = confirmation.get('response', '').upper()
    
    if 'CONFIRMED' in response or 'YES' in response or 'CONFIRM' in response:
        work_order.vendor_dispatch_confirmed = datetime.utcnow()
        work_order.status = WorkOrderStatus.AWAITING_VENDOR_DISPATCH
        
        # Check if facility manager also confirmed
        if work_order.facility_confirmed:
            work_order.status = WorkOrderStatus.DISPATCHED
        
        db.commit()
        
        return {"status": "confirmed", "message": "Vendor confirmed dispatch"}
    else:
        return {"status": "pending", "message": "Vendor has not confirmed yet"}
