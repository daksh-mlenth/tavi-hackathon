"""
Webhook endpoints for inbound vendor communications (SMS, Email replies)
"""

from fastapi import APIRouter, Request, Form, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.models.vendor import Vendor
from app.models.quote import Quote, QuoteStatus
from app.models.communication_log import CommunicationChannel, CommunicationLog
from app.services.communication_service import CommunicationService
from app.services.ai_agent_service import AIAgentService
from app.services.quote_service import QuoteService
from app.constants import AI_MODEL

router = APIRouter()


@router.post("/sms/inbound")
async def handle_inbound_sms(
    request: Request,
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(None),
    db: Session = Depends(get_db),
):
    """
    Twilio webhook for inbound SMS messages from vendors
    """
    print(f"📱 Inbound SMS from {From}: {Body}")

    vendor = db.query(Vendor).filter(Vendor.phone == From).first()
    if not vendor:
        print(f"⚠️  Unknown vendor phone: {From}")
        return {"status": "ignored", "reason": "unknown vendor"}

    active_quotes = (
        db.query(Quote)
        .filter(
            Quote.vendor_id == vendor.id,
            Quote.status.in_([QuoteStatus.PENDING, QuoteStatus.REQUESTED]),
        )
        .order_by(Quote.created_at.desc())
        .all()
    )

    if not active_quotes:
        print(f"⚠️  No active quotes for vendor {vendor.business_name}")
        return {"status": "ignored", "reason": "no active quotes"}

    quote = active_quotes[0]
    work_order = quote.work_order

    comm_service = CommunicationService(db)
    comm_service.log_communication(
        work_order_id=work_order.id,
        vendor_id=vendor.id,
        channel=CommunicationChannel.SMS,
        direction="inbound",
        message=Body,
        sent_successfully=True,
        metadata={"message_sid": MessageSid, "from_number": From},
    )

    background_tasks.add_task(
        process_vendor_sms_response, db, quote.id, vendor.id, Body
    )

    return {"status": "received"}


@router.post("/email/inbound")
async def handle_inbound_email(
    request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """
    SendGrid webhook for inbound email replies from vendors
    """
    data = await request.json()

    from_email = data.get("from")
    subject = data.get("subject", "")
    body = data.get("text", "") or data.get("html", "")

    print(f"📧 Inbound email from {from_email}")

    vendor = db.query(Vendor).filter(Vendor.email == from_email).first()
    if not vendor:
        print(f"⚠️  Unknown vendor email: {from_email}")
        return {"status": "ignored", "reason": "unknown vendor"}

    active_quotes = (
        db.query(Quote)
        .filter(
            Quote.vendor_id == vendor.id,
            Quote.status.in_([QuoteStatus.PENDING, QuoteStatus.REQUESTED]),
        )
        .order_by(Quote.created_at.desc())
        .all()
    )

    if not active_quotes:
        return {"status": "ignored", "reason": "no active quotes"}

    quote = active_quotes[0]
    work_order = quote.work_order

    comm_service = CommunicationService(db)
    comm_service.log_communication(
        work_order_id=work_order.id,
        vendor_id=vendor.id,
        channel=CommunicationChannel.EMAIL,
        direction="inbound",
        subject=subject,
        message=body,
        sent_successfully=True,
        metadata={"from_email": from_email},
    )

    background_tasks.add_task(
        process_vendor_email_response, db, quote.id, vendor.id, body, subject
    )

    return {"status": "received"}


async def process_vendor_sms_response(db: Session, quote_id, vendor_id, message: str):
    """
    Process vendor SMS response with AI, extract quote info, decide if human needed.
    Limits: Max 2 SMS exchanges, then close conversation.
    """
    print(f"🤖 Processing SMS response for quote {quote_id}")

    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        return

    work_order = quote.work_order
    vendor = quote.vendor

    comm_service = CommunicationService(db)
    all_comms = (
        db.query(CommunicationLog)
        .filter(
            CommunicationLog.work_order_id == work_order.id,
            CommunicationLog.vendor_id == vendor.id,
            CommunicationLog.channel == CommunicationChannel.SMS,
        )
        .all()
    )
    turn_count = len([c for c in all_comms if c.direction == "outbound"])

    if turn_count >= 2:
        print(f"⚠️  Max SMS turns reached ({turn_count}), closing conversation")
        comm_service.log_communication(
            work_order_id=work_order.id,
            vendor_id=vendor.id,
            channel=CommunicationChannel.SMS,
            direction="outbound",
            message="Thank you! We have all the info we need. We'll contact you if selected.",
            sent_successfully=True,
            metadata={"conversation_closed": True, "reason": "max_turns"},
        )
        return

    history = comm_service.get_conversation_history(work_order.id, vendor.id)

    ai_service = AIAgentService()

    comm_service.log_communication(
        work_order_id=work_order.id,
        vendor_id=vendor.id,
        channel=CommunicationChannel.SMS,
        direction="inbound",
        message=message,
        sent_successfully=True,
        metadata={"turn": turn_count, "source": "vendor_reply"},
    )

    parsed = await ai_service.parse_vendor_sms_response(
        message=message,
        conversation_history=history,
        work_order_data={
            "description": work_order.description,
            "trade_type": work_order.trade_type.value,
            "location": work_order.location_address,
            "turn_count": turn_count,
        },
    )

    if parsed.get("extracted_info"):
        info = parsed["extracted_info"]
        quote_service = QuoteService(db)

        availability_date = None
        if info.get("availability_days"):
            days = int(info["availability_days"])
            availability_date = datetime.utcnow() + timedelta(days=days)

        if info.get("price"):
            quote_service.update_quote_with_response(
                quote.id,
                price=info["price"],
                availability_date=availability_date,
                quote_text=message,
            )
            quote.status = QuoteStatus.RECEIVED

        db.commit()

    if parsed.get("conversation_complete"):
        print("✅ SMS conversation complete (all info collected)")
        return

    if not parsed.get("needs_human"):
        comm_service.log_communication(
            work_order_id=work_order.id,
            vendor_id=vendor.id,
            channel=CommunicationChannel.SMS,
            direction="outbound",
            message=parsed["response"],
            sent_successfully=True,
            ai_model_used=AI_MODEL,
            metadata={"automated_reply": True, "turn": turn_count + 1},
        )
    else:
        comm_service.log_communication(
            work_order_id=work_order.id,
            vendor_id=vendor.id,
            channel=CommunicationChannel.SMS,
            direction="outbound",
            message=f"🚨 NEEDS HUMAN REVIEW\n\nReason: {parsed.get('reason')}\n\nSuggested response:\n{parsed.get('draft_response')}",
            sent_successfully=False,
            metadata={"needs_human": True, "reason": parsed.get("reason")},
        )

    print("✅ SMS response processed")


async def process_vendor_email_response(
    db: Session, quote_id, vendor_id, message: str, subject: str
):
    """
    Process vendor email response with AI, extract quote info, decide if human needed.
    Limits: Max 3 email exchanges, then close conversation.
    """
    print(f"🤖 Processing email response for quote {quote_id}")

    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        return

    work_order = quote.work_order
    vendor = quote.vendor

    comm_service = CommunicationService(db)
    all_comms = (
        db.query(CommunicationLog)
        .filter(
            CommunicationLog.work_order_id == work_order.id,
            CommunicationLog.vendor_id == vendor.id,
            CommunicationLog.channel == CommunicationChannel.EMAIL,
        )
        .all()
    )
    turn_count = len([c for c in all_comms if c.direction == "outbound"])

    if turn_count >= 3:
        print(f"⚠️  Max email turns reached ({turn_count}), closing conversation")
        comm_service.log_communication(
            work_order_id=work_order.id,
            vendor_id=vendor.id,
            channel=CommunicationChannel.EMAIL,
            direction="outbound",
            subject=f"Re: {subject}",
            message="Thank you for the information. We have what we need and will contact you if you're selected.",
            sent_successfully=True,
            metadata={"conversation_closed": True, "reason": "max_turns"},
        )
        return

    history = comm_service.get_conversation_history(work_order.id, vendor.id)

    comm_service.log_communication(
        work_order_id=work_order.id,
        vendor_id=vendor.id,
        channel=CommunicationChannel.EMAIL,
        direction="inbound",
        message=message,
        sent_successfully=True,
        metadata={"turn": turn_count, "source": "vendor_reply", "subject": subject},
    )

    ai_service = AIAgentService()

    parsed = await ai_service.parse_vendor_email_response(
        message=message,
        conversation_history=history,
        work_order_data={
            "description": work_order.description,
            "trade_type": work_order.trade_type.value,
            "location": work_order.location_address,
            "urgency": work_order.urgency,
            "turn_count": turn_count,
        },
    )

    if parsed.get("extracted_info"):
        info = parsed["extracted_info"]
        quote_service = QuoteService(db)

        availability_date = None
        if info.get("availability_days"):
            days = int(info["availability_days"])
            availability_date = datetime.utcnow() + timedelta(days=days)

        if info.get("price"):
            quote_service.update_quote_with_response(
                quote.id,
                price=info["price"],
                availability_date=availability_date,
                quote_text=message,
            )
            quote.status = QuoteStatus.RECEIVED

        db.commit()

    if parsed.get("conversation_complete"):
        print("✅ Email conversation complete (all info collected)")
        return

    if not parsed.get("needs_human"):
        comm_service.log_communication(
            work_order_id=work_order.id,
            vendor_id=vendor.id,
            channel=CommunicationChannel.EMAIL,
            direction="outbound",
            subject=f"Re: {subject}",
            message=parsed["response"],
            sent_successfully=True,
            ai_model_used=AI_MODEL,
            metadata={"automated_reply": True, "turn": turn_count + 1},
        )
    else:
        comm_service.log_communication(
            work_order_id=work_order.id,
            vendor_id=vendor.id,
            channel=CommunicationChannel.EMAIL,
            direction="outbound",
            subject="⚠️ Human review needed",
            message=f"🚨 NEEDS HUMAN REVIEW\n\nReason: {parsed.get('reason')}\n\nSuggested response:\n{parsed.get('draft_response')}",
            sent_successfully=False,
            metadata={"needs_human": True, "reason": parsed.get("reason")},
        )

    print("✅ Email response processed")
