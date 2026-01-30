import asyncio
from sqlalchemy.orm import Session
from twilio.rest import Client as TwilioClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.config import settings
from app.constants import (
    EMAIL_FROM_ADDRESS,
    EMAIL_SUBJECT_PREFIX,
    AI_MODEL,
)
from app.models.work_order import WorkOrder
from app.models.vendor import Vendor
from app.models.quote import Quote
from app.models.communication_log import CommunicationChannel
from app.services.ai_agent_service import AIAgentService
from app.services.quote_service import QuoteService
from app.services.communication_service import CommunicationService
from uuid import UUID
from sqlalchemy import any_


class VendorContactService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIAgentService()
        self.quote_service = QuoteService(db)
        self.comm_service = CommunicationService(db)

        self.twilio_client = None
        self.sendgrid_client = None

        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                self.twilio_client = TwilioClient(
                    settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
                )
            except Exception as e:
                print(f"⚠️  Twilio initialization failed: {e}")

        if settings.SENDGRID_API_KEY:
            try:
                self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
            except Exception as e:
                print(f"⚠️  SendGrid initialization failed: {e}")

    async def contact_vendor_for_quote(self, quote_id: str):
        quote = self.db.query(Quote).filter(Quote.id == UUID(quote_id)).first()
        if not quote:
            print(f"❌ Quote {quote_id} not found")
            return False

        work_order = quote.work_order
        vendor = quote.vendor

        target_email = (
            settings.DEMO_TEST_EMAIL if settings.DEMO_TEST_EMAIL else vendor.email
        )
        target_phone = (
            settings.DEMO_TEST_PHONE if settings.DEMO_TEST_PHONE else vendor.phone
        )

        is_demo = bool(settings.DEMO_TEST_EMAIL or settings.DEMO_TEST_PHONE)

        print(f"📞 Contacting for quote {quote_id}")
        print(f"   Vendor: {vendor.business_name}")
        print(f"   Mode: {'🎭 DEMO' if is_demo else '🔴 LIVE'}")
        print(f"   Email: {target_email}")
        print(f"   Phone: {target_phone}")

        work_order_data = {
            "trade_type": work_order.trade_type.value,
            "location_address": work_order.location_address,
            "description": work_order.description,
            "urgency": work_order.urgency,
            "preferred_date": str(work_order.preferred_date)
            if work_order.preferred_date
            else "flexible",
        }

        success_count = 0

        if target_email:
            email_success = await self._send_email_unified(
                work_order, vendor, work_order_data, quote.id, target_email, is_demo
            )
            if email_success:
                success_count += 1

        if target_phone:
            sms_success = await self._send_sms_unified(
                work_order, vendor, work_order_data, quote.id, target_phone, is_demo
            )
            if sms_success:
                success_count += 1

        if target_phone and self.twilio_client:
            call_success = await self._make_phone_call_unified(
                work_order, vendor, work_order_data, quote.id, target_phone, is_demo
            )
            if call_success:
                success_count += 1

        print(f"✅ Sent {success_count} communications for quote {quote_id}")
        return success_count > 0

    async def contact_all_vendors_for_work_order(self, work_order: WorkOrder):
        vendors = (
            self.db.query(Vendor)
            .filter(work_order.trade_type.value == any_(Vendor.trade_specialties))
            .order_by(Vendor.composite_score.desc())
            .limit(10)
            .all()
        )

        print(f"📞 Contacting {len(vendors)} vendors for work order {work_order.id}")

        work_order_data = {
            "trade_type": work_order.trade_type.value,
            "location_address": work_order.location_address,
            "description": work_order.description,
            "urgency": work_order.urgency,
            "preferred_date": str(work_order.preferred_date)
            if work_order.preferred_date
            else "flexible",
        }

        tasks = []
        for vendor in vendors:
            task = self._contact_single_vendor(work_order, vendor, work_order_data)
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

        print(f"✅ Finished contacting vendors for work order {work_order.id}")

    async def _contact_single_vendor(
        self, work_order: WorkOrder, vendor: Vendor, work_order_data: dict
    ):
        quote = self.quote_service.create_quote(
            work_order_id=work_order.id, vendor_id=vendor.id
        )

        print(f"  Contacting {vendor.business_name}...")

        if vendor.email:
            success = await self._send_email(
                work_order, vendor, work_order_data, quote.id
            )
            if success:
                return

        if vendor.phone:
            success = await self._send_sms(
                work_order, vendor, work_order_data, quote.id
            )
            if success:
                return

        if vendor.phone and self.twilio_client:
            await self._make_phone_call(work_order, vendor, work_order_data, quote.id)

    async def _send_email(
        self, work_order: WorkOrder, vendor: Vendor, work_order_data: dict, quote_id
    ) -> bool:
        try:
            message = await self.ai_service.generate_vendor_contact_message(
                work_order_data, vendor.business_name, "email"
            )

            # Parse subject and body
            lines = message.split("\n")
            subject = (
                lines[0].replace("Subject:", "").strip()
                if lines[0].startswith("Subject:")
                else f"{EMAIL_SUBJECT_PREFIX} from Tavi"
            )
            body = "\n".join(lines[1:]).strip() if len(lines) > 1 else message

            if self.sendgrid_client:
                mail = Mail(
                    from_email=EMAIL_FROM_ADDRESS,
                    to_emails=vendor.email,
                    subject=subject,
                    html_content=body.replace("\n", "<br>"),
                )

                response = self.sendgrid_client.send(mail)
                success = response.status_code in [200, 201, 202]
            else:
                print(f"    📧 [SIMULATED] Email to {vendor.email}")
                print(f"       Subject: {subject}")
                success = True

            # Log communication
            self.comm_service.log_communication(
                work_order_id=work_order.id,
                vendor_id=vendor.id,
                channel=CommunicationChannel.EMAIL,
                direction="outbound",
                subject=subject,
                message=body,
                sent_successfully=success,
                ai_model_used=AI_MODEL,
            )

            if success:
                print(f"    ✓ Email sent to {vendor.business_name}")

            return success

        except Exception as e:
            print(f"    ✗ Email failed for {vendor.business_name}: {e}")
            return False

    async def _send_sms(
        self, work_order: WorkOrder, vendor: Vendor, work_order_data: dict, quote_id
    ) -> bool:
        try:
            message = await self.ai_service.generate_vendor_contact_message(
                work_order_data, vendor.business_name, "sms"
            )

            if self.twilio_client and settings.TWILIO_PHONE_NUMBER:
                twilio_message = self.twilio_client.messages.create(
                    body=message, from_=settings.TWILIO_PHONE_NUMBER, to=vendor.phone
                )
                success = twilio_message.status != "failed"
                external_id = twilio_message.sid
            else:
                print(f"    💬 [SIMULATED] SMS to {vendor.phone}")
                print(f"       Message: {message}")
                success = True
                external_id = None

            # Log communication
            self.comm_service.log_communication(
                work_order_id=work_order.id,
                vendor_id=vendor.id,
                channel=CommunicationChannel.SMS,
                direction="outbound",
                message=message,
                sent_successfully=success,
                external_id=external_id,
                ai_model_used=AI_MODEL,
            )

            if success:
                print(f"    ✓ SMS sent to {vendor.business_name}")

            return success

        except Exception as e:
            print(f"    ✗ SMS failed for {vendor.business_name}: {e}")
            return False

    async def _make_phone_call(
        self, work_order: WorkOrder, vendor: Vendor, work_order_data: dict, quote_id
    ) -> bool:
        try:
            script = await self.ai_service.generate_vendor_contact_message(
                work_order_data, vendor.business_name, "phone"
            )

            print(f"    📞 [SIMULATED] Phone call to {vendor.phone}")
            print(f"       Script: {script}")

            self.comm_service.log_communication(
                work_order_id=work_order.id,
                vendor_id=vendor.id,
                channel=CommunicationChannel.PHONE,
                direction="outbound",
                message=script,
                sent_successfully=True,
                ai_model_used=AI_MODEL,
            )

            print(f"    ✓ Phone call initiated to {vendor.business_name}")
            return True

        except Exception as e:
            print(f"    ✗ Phone call failed for {vendor.business_name}: {e}")
            return False

    async def process_vendor_response(
        self, vendor_id: str, work_order_id: str, response_text: str, channel: str
    ):
        parsed_response = await self.ai_service.parse_vendor_response(response_text)

        quote = (
            self.db.query(Quote)
            .filter(Quote.work_order_id == work_order_id, Quote.vendor_id == vendor_id)
            .first()
        )

        if quote:
            self.quote_service.update_quote_with_response(
                quote.id,
                price=parsed_response.get("price"),
                availability_date=parsed_response.get("availability_date"),
                quote_text=response_text,
            )

            self.comm_service.log_communication(
                work_order_id=work_order_id,
                vendor_id=vendor_id,
                channel=CommunicationChannel(channel),
                direction="inbound",
                message=response_text,
                response=str(parsed_response),
                sent_successfully=True,
            )

            print(f"✅ Processed vendor response: ${parsed_response.get('price')}")

    async def _send_email_unified(
        self,
        work_order: WorkOrder,
        vendor: Vendor,
        work_order_data: dict,
        quote_id,
        target_email: str,
        is_demo: bool,
    ) -> bool:
        try:
            message = await self.ai_service.generate_vendor_contact_message(
                work_order_data, vendor.business_name, "email"
            )

            # Parse subject and body
            lines = message.split("\n")
            subject = (
                lines[0].replace("Subject:", "").strip()
                if lines[0].startswith("Subject:")
                else f"{EMAIL_SUBJECT_PREFIX} - {vendor.business_name}"
            )
            body = "\n".join(lines[1:]).strip() if len(lines) > 1 else message

            if is_demo:
                demo_notice = f"\n\n---\n🎭 DEMO MODE\nIntended for vendor: {vendor.business_name}\nWould be sent to: {vendor.email or 'No email on file'}"
                body = body + demo_notice
                subject = f"[DEMO] {subject}"

            if self.sendgrid_client:
                mail = Mail(
                    from_email=EMAIL_FROM_ADDRESS,
                    to_emails=target_email,
                    subject=subject,
                    html_content=body.replace("\n", "<br>"),
                )

                response = self.sendgrid_client.send(mail)
                success = response.status_code in [200, 201, 202]
                print(
                    f"    ✅ Email sent via SendGrid (status: {response.status_code})"
                )
            else:
                print(f"    📧 [SIMULATED] Email to {target_email}")
                print(f"       Subject: {subject}")
                success = True

            # Log communication
            self.comm_service.log_communication(
                work_order_id=work_order.id,
                vendor_id=vendor.id,
                channel=CommunicationChannel.EMAIL,
                direction="outbound",
                subject=subject,
                message=body,
                sent_successfully=success,
                ai_model_used=AI_MODEL,
                metadata={
                    "demo_mode": is_demo,
                    "target_email": target_email,
                    "vendor": vendor.business_name,
                },
            )

            return success

        except Exception as e:
            print(f"    ❌ Email failed: {e}")
            return False

    async def _send_sms_unified(
        self,
        work_order: WorkOrder,
        vendor: Vendor,
        work_order_data: dict,
        quote_id,
        target_phone: str,
        is_demo: bool,
    ) -> bool:
        try:
            message = await self.ai_service.generate_vendor_contact_message(
                work_order_data, vendor.business_name, "sms"
            )

            if is_demo:
                message = message + f"\n🎭 DEMO: For {vendor.business_name}"

            if self.twilio_client and settings.TWILIO_PHONE_NUMBER:
                twilio_message = self.twilio_client.messages.create(
                    body=message, from_=settings.TWILIO_PHONE_NUMBER, to=target_phone
                )
                success = twilio_message.status != "failed"
                print(f"    ✅ SMS sent via Twilio (SID: {twilio_message.sid})")
            else:
                print(f"    📱 [SIMULATED] SMS to {target_phone}")
                success = True

            self.comm_service.log_communication(
                work_order_id=work_order.id,
                vendor_id=vendor.id,
                channel=CommunicationChannel.SMS,
                direction="outbound",
                message=message,
                sent_successfully=success,
                ai_model_used=AI_MODEL,
                metadata={
                    "demo_mode": is_demo,
                    "target_phone": target_phone,
                    "vendor": vendor.business_name,
                },
            )

            return success

        except Exception as e:
            print(f"    ❌ SMS failed: {e}")
            return False

    async def _make_phone_call_unified(
        self,
        work_order: WorkOrder,
        vendor: Vendor,
        work_order_data: dict,
        quote_id,
        target_phone: str,
        is_demo: bool,
    ) -> bool:
        try:
            call_script = await self.ai_service.generate_vendor_contact_message(
                work_order_data, vendor.business_name, "phone"
            )

            if self.twilio_client and settings.TWILIO_PHONE_NUMBER:
                base_url = settings.PUBLIC_API_URL or "http://localhost:8000"
                callback_url = (
                    f"{base_url}/api/communications/voice-callback/{quote_id}"
                )

                call = self.twilio_client.calls.create(
                    to=target_phone,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    url=callback_url,
                    method="POST",
                    status_callback=f"{callback_url}/status",
                    record=True,
                )

                success = call.status != "failed"
                print(f"    ✅ Call initiated via Twilio (SID: {call.sid})")

                self.comm_service.log_communication(
                    work_order_id=work_order.id,
                    vendor_id=vendor.id,
                    channel=CommunicationChannel.PHONE,
                    direction="outbound",
                    message=f"AI Voice Call initiated\n\nScript: {call_script}",
                    sent_successfully=success,
                    ai_model_used=AI_MODEL,
                    metadata={
                        "demo_mode": is_demo,
                        "target_phone": target_phone,
                        "vendor": vendor.business_name,
                        "call_sid": call.sid,
                        "call_script": call_script,
                    },
                )
            else:
                print(f"    📞 [SIMULATED] Call to {target_phone}")
                print(f"       Script: {call_script[:150]}...")
                success = True

                self.comm_service.log_communication(
                    work_order_id=work_order.id,
                    vendor_id=vendor.id,
                    channel=CommunicationChannel.PHONE,
                    direction="outbound",
                    message=f"[SIMULATED] AI Voice Call\n\nScript: {call_script}",
                    sent_successfully=True,
                    ai_model_used=AI_MODEL,
                    metadata={
                        "demo_mode": is_demo,
                        "target_phone": target_phone,
                        "vendor": vendor.business_name,
                        "simulated": True,
                    },
                )

            return success

        except Exception as e:
            print(f"    ❌ Call failed: {e}")
            return False
