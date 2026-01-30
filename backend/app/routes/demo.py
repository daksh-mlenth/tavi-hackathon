"""
Demo endpoints for testing bidirectional conversations without external webhooks
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import get_db
from app.models.quote import Quote
from app.models.vendor import Vendor

router = APIRouter()


class SimulateVendorReplyRequest(BaseModel):
    quote_id: str
    reply_message: str
    channel: str


@router.post("/simulate-vendor-reply")
async def simulate_vendor_reply(
    request: SimulateVendorReplyRequest,
    db: Session = Depends(get_db)
):
    """
    Simulate a vendor replying to our message.
    Useful for testing without configuring Twilio/SendGrid webhooks.
    """
    quote = db.query(Quote).filter(Quote.id == UUID(request.quote_id)).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    vendor = quote.vendor
    
    if request.channel == 'sms':
        from app.routes.webhooks import process_vendor_sms_response
        await process_vendor_sms_response(
            db=db,
            quote_id=quote.id,
            vendor_id=vendor.id,
            message=request.reply_message
        )
    elif request.channel == 'email':
        from app.routes.webhooks import process_vendor_email_response
        await process_vendor_email_response(
            db=db,
            quote_id=quote.id,
            vendor_id=vendor.id,
            message=request.reply_message,
            subject="Re: Service opportunity"
        )
    elif request.channel == 'phone':
        from app.services.ai_agent_service import AIAgentService
        from app.services.quote_service import QuoteService
        from datetime import datetime, timedelta
        
        ai_service = AIAgentService()
        
        parsed = await ai_service.parse_vendor_phone_response(
            transcript=request.reply_message,
            work_order_data={
                'description': quote.work_order.description if quote.work_order else '',
                'trade_type': quote.work_order.trade_type.value if quote.work_order else ''
            }
        )
        
        from app.services.communication_service import CommunicationService
        from app.models.communication_log import CommunicationChannel
        
        comm_service = CommunicationService(db)
        info = parsed.get('extracted_info', {})
        
        from app.constants import get_currency_info
        currency_info = get_currency_info(quote.work_order.location_country if quote.work_order else "United States")
        currency_symbol = currency_info['symbol']
        
        summary_parts = []
        if info.get('price'):
            summary_parts.append(f"Price: {currency_symbol}{info['price']}")
        if info.get('availability_days'):
            summary_parts.append(f"Available in {info['availability_days']} days")
        if info.get('duration_hours'):
            summary_parts.append(f"Duration: ~{info['duration_hours']}h")
        
        summary = f"📞 Call Summary: {' | '.join(summary_parts) if summary_parts else 'Call completed - no quote provided'}"
        
        comm_service.log_communication(
            work_order_id=quote.work_order.id,
            vendor_id=quote.vendor.id,
            channel=CommunicationChannel.PHONE,
            direction="inbound",
            message=summary,
            sent_successfully=True,
            metadata={
                "full_transcript": request.reply_message,
                "extracted_info": info,
                "source": "simulation"
            }
        )
        
        if parsed.get('extracted_info'):
            info = parsed['extracted_info']
            quote_service = QuoteService(db)
            
            availability_date = None
            if info.get('availability_days'):
                days = int(info['availability_days'])
                availability_date = datetime.utcnow() + timedelta(days=days)
            
            if info.get('price'):
                quote_service.update_quote_with_response(
                    quote.id,
                    price=info['price'],
                    availability_date=availability_date,
                    quote_text=request.reply_message
                )
        
        db.commit()
    else:
        raise HTTPException(status_code=400, detail="Invalid channel. Must be 'sms', 'email', or 'phone'")
    
    return {
        "status": "success",
        "message": f"Simulated {request.channel} reply from {vendor.business_name}",
        "vendor": vendor.business_name,
        "quote_id": str(quote.id)
    }


@router.post("/simulate-multiple-quotes")
async def simulate_multiple_vendor_quotes(
    work_order_id: str,
    db: Session = Depends(get_db)
):
    """
    Quickly simulate multiple vendors responding with quotes.
    Perfect for testing the comparison dashboard!
    """
    from app.models.work_order import WorkOrder
    from app.models.quote import QuoteStatus
    import random
    
    work_order = db.query(WorkOrder).filter(WorkOrder.id == UUID(work_order_id)).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    quotes = db.query(Quote).filter(Quote.work_order_id == work_order.id).all()
    
    from app.constants import get_currency_info
    currency_info = get_currency_info(work_order.location_country or "United States")
    currency_symbol = currency_info['symbol']
    
    responses = []
    for quote in quotes[:5]:
        base_price = random.randint(150, 500)
        days = random.randint(1, 5)
        
        vendor_message = f"Hi, I can do this job for {currency_symbol}{base_price}. Available to start in {days} days. Quality work guaranteed!"
        
        from app.routes.webhooks import process_vendor_sms_response
        await process_vendor_sms_response(
            db=db,
            quote_id=quote.id,
            vendor_id=quote.vendor_id,
            message=vendor_message
        )
        
        responses.append({
            "vendor": quote.vendor.business_name,
            "price": base_price,
            "message": vendor_message
        })
    
    return {
        "status": "success",
        "message": f"Simulated {len(responses)} vendor responses",
        "responses": responses
    }


class SimulateFacilityConfirmationRequest(BaseModel):
    work_order_id: str
    approved: bool

@router.post("/simulate-facility-confirmation")
async def simulate_facility_manager_confirmation(
    request: SimulateFacilityConfirmationRequest,
    db: Session = Depends(get_db)
):
    """Simulate facility manager approving/rejecting vendor selection"""
    from app.models.work_order import WorkOrder, WorkOrderStatus
    
    work_order = db.query(WorkOrder).filter(WorkOrder.id == UUID(request.work_order_id)).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    response_text = "APPROVED - Vendor selection looks good!" if request.approved else "REJECTED - Please select another vendor"
    
    from app.services.communication_service import CommunicationService
    from app.models.communication_log import CommunicationChannel
    
    comm_service = CommunicationService(db)
    comm_service.log_communication(
        work_order_id=work_order.id,
        vendor_id=None,
        channel=CommunicationChannel.EMAIL,
        direction="inbound",
        message=response_text,
        sent_successfully=True,
        metadata={
            "type": "facility_confirmation",
            "approved": request.approved,
            "recipient_name": work_order.facility_manager_name
        }
    )
    
    if request.approved:
        work_order.facility_confirmed = datetime.utcnow()
        
        if work_order.vendor_dispatch_confirmed:
            work_order.status = WorkOrderStatus.DISPATCHED
        
        db.commit()
        return {"status": "approved", "message": "Facility manager approved"}
    else:
        work_order.status = WorkOrderStatus.EVALUATING_QUOTES
        db.commit()
        return {"status": "rejected", "message": "Facility manager rejected"}


class SimulateVendorDispatchRequest(BaseModel):
    work_order_id: str
    confirmed: bool

@router.post("/simulate-vendor-dispatch-confirmation")
async def simulate_vendor_dispatch_confirmation(
    request: SimulateVendorDispatchRequest,
    db: Session = Depends(get_db)
):
    """Simulate vendor confirming/declining dispatch"""
    from app.models.work_order import WorkOrder, WorkOrderStatus
    
    work_order = db.query(WorkOrder).filter(WorkOrder.id == UUID(request.work_order_id)).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    response_text = "CONFIRMED - I will be there on the scheduled date!" if request.confirmed else "Sorry, I cannot make it on that date. Can we reschedule?"
    
    from app.services.communication_service import CommunicationService
    from app.models.communication_log import CommunicationChannel
    
    comm_service = CommunicationService(db)
    comm_service.log_communication(
        work_order_id=work_order.id,
        vendor_id=work_order.selected_vendor_id,
        channel=CommunicationChannel.SMS,
        direction="inbound",
        message=response_text,
        sent_successfully=True,
        metadata={
            "type": "vendor_dispatch_confirmation",
            "confirmed": request.confirmed
        }
    )
    
    if request.confirmed:
        work_order.vendor_dispatch_confirmed = datetime.utcnow()
        
        if work_order.facility_confirmed:
            work_order.status = WorkOrderStatus.DISPATCHED
        
        db.commit()
        return {"status": "confirmed", "message": "Vendor confirmed dispatch"}
    else:
        db.commit()
        return {"status": "declined", "message": "Vendor cannot confirm dispatch"}
