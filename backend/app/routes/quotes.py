from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime
import asyncio

from app.database import get_db
from app.schemas.quote import QuoteResponse, QuoteList
from app.services.quote_service import QuoteService
from app.services.ai_agent_service import AIAgentService

router = APIRouter()


class VendorResponseCreate(BaseModel):
    """Schema for simulating vendor response"""
    response_text: str


@router.get("/work-order/{work_order_id}", response_model=QuoteList)
def list_quotes_for_work_order(
    work_order_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all quotes for a specific work order"""
    service = QuoteService(db)
    quotes = service.get_quotes_for_work_order(work_order_id)
    return QuoteList(quotes=quotes, total=len(quotes))


@router.get("/{quote_id}", response_model=QuoteResponse)
def get_quote(
    quote_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific quote by ID"""
    service = QuoteService(db)
    quote = service.get_quote(quote_id)
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    return quote


@router.post("/{quote_id}/respond")
async def simulate_vendor_response(
    quote_id: UUID,
    response_data: VendorResponseCreate,
    db: Session = Depends(get_db)
):
    """
    Simulate a vendor response to a quote request.
    This endpoint is for demo purposes to show how the system handles vendor responses.
    
    Example response text:
    "Yes, I can do it for $350. Available tomorrow afternoon."
    """
    service = QuoteService(db)
    ai_service = AIAgentService()
    
    # Check if quote exists
    quote = service.get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Parse vendor response using AI
    parsed_response = await ai_service.parse_vendor_response(response_data.response_text)
    
    # Convert availability_date string to datetime if present
    availability_date = None
    if parsed_response.get('availability_date'):
        try:
            availability_date = datetime.fromisoformat(parsed_response['availability_date'])
        except (ValueError, TypeError):
            availability_date = None
    
    # Update quote with parsed data
    updated_quote = service.update_quote_with_response(
        quote_id=quote_id,
        price=parsed_response.get('price'),
        availability_date=availability_date,
        quote_text=response_data.response_text
    )
    
    return {
        "message": "Vendor response processed successfully!",
        "quote_id": str(updated_quote.id),
        "parsed_data": {
            "price": updated_quote.price,
            "availability_date": updated_quote.availability_date.isoformat() if updated_quote.availability_date else None,
            "quote_text": updated_quote.quote_text
        },
        "scores": {
            "price_score": updated_quote.price_score,
            "quality_score": updated_quote.quality_score,
            "availability_score": updated_quote.availability_score,
            "composite_score": updated_quote.composite_score
        },
        "status": updated_quote.status
    }


@router.post("/{quote_id}/request")
async def request_quote(
    quote_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Request a quote from a vendor.
    Changes quote status from 'pending' to 'requested', updates work order status,
    and sends multi-modal communications (email + SMS) to demo test addresses.
    """
    from app.models.quote import Quote, QuoteStatus
    from app.models.work_order import WorkOrder, WorkOrderStatus
    from app.services.vendor_contact_service import VendorContactService
    
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Update quote status to requested
    quote.status = QuoteStatus.REQUESTED
    
    # Update work order status to contacting_vendors if not already
    work_order = db.query(WorkOrder).filter(WorkOrder.id == quote.work_order_id).first()
    if work_order and work_order.status == WorkOrderStatus.AWAITING_APPROVAL:
        work_order.status = WorkOrderStatus.CONTACTING_VENDORS
    
    db.commit()
    db.refresh(quote)
    
    # Actually contact the vendor (in demo mode - sends to test email/phone)
    contact_service = VendorContactService(db)
    await contact_service.contact_vendor_for_quote(str(quote_id))
    
    return {
        "message": "Quote requested successfully! Multi-modal communications sent.",
        "quote_id": str(quote.id),
        "vendor_id": str(quote.vendor_id),
        "vendor_name": quote.vendor.business_name,
        "status": quote.status,
        "communications_sent": ["email", "sms"]
    }


@router.post("/request-multiple")
async def request_multiple_quotes(
    quote_ids: List[UUID],
    db: Session = Depends(get_db)
):
    """
    Request quotes from multiple vendors at once.
    Sends multi-modal communications to all selected vendors.
    """
    from app.models.quote import Quote, QuoteStatus
    from app.models.work_order import WorkOrder, WorkOrderStatus
    from app.services.vendor_contact_service import VendorContactService
    
    if not quote_ids:
        raise HTTPException(status_code=400, detail="No quote IDs provided")
    
    quotes = db.query(Quote).filter(Quote.id.in_(quote_ids)).all()
    if not quotes:
        raise HTTPException(status_code=404, detail="No quotes found")
    
    # Update all quote statuses to requested
    for quote in quotes:
        quote.status = QuoteStatus.REQUESTED
    
    # Update work order status
    work_order_id = quotes[0].work_order_id
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if work_order and work_order.status == WorkOrderStatus.AWAITING_APPROVAL:
        work_order.status = WorkOrderStatus.CONTACTING_VENDORS
    
    db.commit()
    
    # Contact all vendors in parallel (demo mode)
    contact_service = VendorContactService(db)
    tasks = [contact_service.contact_vendor_for_quote(str(q.id)) for q in quotes]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    vendor_names = [q.vendor.business_name for q in quotes]
    
    return {
        "message": f"Quote requests sent to {len(quotes)} vendors!",
        "quote_ids": [str(q.id) for q in quotes],
        "vendor_count": len(quotes),
        "vendors": vendor_names,
        "communications_sent": ["email", "sms"]
    }


@router.post("/{quote_id}/accept")
def accept_quote(
    quote_id: UUID,
    db: Session = Depends(get_db)
):
    """Accept a quote and dispatch the vendor"""
    service = QuoteService(db)
    quote = service.accept_quote(quote_id)
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    return {
        "message": "Quote accepted",
        "quote_id": str(quote.id),
        "vendor_id": str(quote.vendor_id)
    }
