from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
import json

from app.database import get_db
from app.models.quote import Quote
from app.models.communication_log import CommunicationChannel
from app.services.communication_service import CommunicationService
from app.services.ai_agent_service import AIAgentService
from app.constants import AI_MODEL

router = APIRouter()


@router.post("/voice-callback/{quote_id}")
async def voice_callback(
    quote_id: UUID,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Twilio Voice webhook - generates TwiML for AI voice interaction
    """
    form_data = await request.form()
    
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        return Response(content=generate_error_twiml(), media_type="application/xml")
    
    work_order = quote.work_order
    vendor = quote.vendor
    
    ai_service = AIAgentService()
    work_order_data = {
        "trade_type": work_order.trade_type.value,
        "location_address": work_order.location_address,
        "description": work_order.description,
        "urgency": work_order.urgency,
        "preferred_date": str(work_order.preferred_date) if work_order.preferred_date else "flexible"
    }
    
    call_script = await ai_service.generate_vendor_contact_message(
        work_order_data,
        vendor.business_name,
        "phone"
    )
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">{call_script}</Say>
    <Pause length="1"/>
    <Say voice="alice">Please provide your quote and availability after the beep.</Say>
    <Record 
        maxLength="120" 
        transcribe="true"
        transcribeCallback="/api/communications/voice-transcript/{quote_id}"
        playBeep="true"
        finishOnKey="#"
    />
    <Say voice="alice">Thank you for your response. We will review your quote shortly. Goodbye!</Say>
</Response>"""
    
    return Response(content=twiml, media_type="application/xml")


@router.post("/voice-transcript/{quote_id}")
async def voice_transcript_callback(
    quote_id: UUID,
    TranscriptionText: str = Form(None),
    RecordingUrl: str = Form(None),
    CallSid: str = Form(None),
    RecordingSid: str = Form(None),
    TranscriptionStatus: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Twilio callback for call transcription
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        return {"error": "Quote not found"}
    
    work_order = quote.work_order
    vendor = quote.vendor
    
    comm_service = CommunicationService(db)
    
    transcript_message = f"""📞 CALL TRANSCRIPT

Vendor: {vendor.business_name}
Phone: {vendor.phone or 'N/A'}

--- VENDOR RESPONSE ---
{TranscriptionText or '[Transcription failed or in progress]'}

--- CALL DETAILS ---
Call SID: {CallSid}
Recording URL: {RecordingUrl}
Recording SID: {RecordingSid}
Status: {TranscriptionStatus}
"""
    
    comm_service.log_communication(
        work_order_id=work_order.id,
        vendor_id=vendor.id,
        channel=CommunicationChannel.PHONE,
        direction="inbound",
        message=transcript_message,
        sent_successfully=True,
        metadata={
            "call_sid": CallSid,
            "recording_url": RecordingUrl,
            "recording_sid": RecordingSid,
            "transcription_status": TranscriptionStatus,
            "transcript": TranscriptionText
        }
    )
    
    if TranscriptionText:
        ai_service = AIAgentService()
        parsed_response = await ai_service.parse_vendor_response(TranscriptionText)
        
        if parsed_response.get('price'):
            from app.services.quote_service import QuoteService
            quote_service = QuoteService(db)
            quote_service.update_quote_with_response(
                quote.id,
                price=parsed_response.get('price'),
                availability_date=parsed_response.get('availability_date'),
                quote_text=TranscriptionText
            )
    
    print(f"✅ Call transcript received for quote {quote_id}")
    return {"status": "success"}


@router.post("/voice-callback/{quote_id}/status")
async def voice_status_callback(
    quote_id: UUID,
    CallStatus: str = Form(None),
    CallDuration: str = Form(None),
    CallSid: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Twilio callback for call status updates
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        return {"error": "Quote not found"}
    
    comm_service = CommunicationService(db)
    
    status_message = f"""📞 CALL STATUS UPDATE

Status: {CallStatus}
Duration: {CallDuration} seconds
Call SID: {CallSid}
"""
    
    comm_service.log_communication(
        work_order_id=quote.work_order_id,
        vendor_id=quote.vendor_id,
        channel=CommunicationChannel.PHONE,
        direction="outbound",
        message=status_message,
        sent_successfully=(CallStatus == "completed"),
        metadata={
            "call_sid": CallSid,
            "call_status": CallStatus,
            "call_duration": CallDuration,
            "status_update": True
        }
    )
    
    print(f"✅ Call status: {CallStatus} (duration: {CallDuration}s)")
    return {"status": "success"}


def generate_error_twiml():
    """Generate error TwiML response"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">We're sorry, but we encountered an error processing this call. Please try again later. Goodbye.</Say>
</Response>"""
