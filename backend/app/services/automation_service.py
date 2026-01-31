"""
Autonomous AI Agent Service for end-to-end work order automation
"""

import asyncio
from typing import Dict, AsyncGenerator, List
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
import random

from app.models.work_order import WorkOrderStatus
from app.models.quote import Quote
from app.services.work_order_service import WorkOrderService
from app.services.quote_service import QuoteService
from app.services.communication_service import CommunicationService
from app.routes.webhooks import (
    process_vendor_sms_response,
    process_vendor_email_response,
)
from app.routes.confirmations import (
    send_facility_manager_confirmation,
    send_vendor_dispatch_confirmation,
)
from app.models.communication_log import CommunicationChannel
from app.constants import get_currency_info


class AutomationService:
    _running_automations = {}
    _lock = asyncio.Lock()

    def __init__(self, db: Session):
        self.db = db
        self.work_order_service = WorkOrderService(db)
        self.quote_service = QuoteService(db)
        self.comm_service = CommunicationService(db)

    async def auto_handle_work_order(
        self, work_order_id: UUID
    ) -> AsyncGenerator[Dict, None]:
        work_order_id_str = str(work_order_id)

        async with self._lock:
            if work_order_id_str in self._running_automations:
                yield {
                    "step": -1,
                    "status": "error",
                    "message": "⚠️ Automation already running for this work order",
                    "timestamp": datetime.utcnow().isoformat(),
                }
                return

            self._running_automations[work_order_id_str] = True

        try:
            self.db.expire_all()

            work_order = self.work_order_service.get_work_order(work_order_id)
            if not work_order:
                yield {
                    "step": -1,
                    "status": "error",
                    "message": f"⚠️ Work order {work_order_id} not found",
                    "timestamp": datetime.utcnow().isoformat(),
                }
                return

            if work_order.status in [
                WorkOrderStatus.DISPATCHED,
                WorkOrderStatus.COMPLETED,
            ]:
                yield {
                    "step": -1,
                    "status": "error",
                    "message": f"⚠️ Work order already {work_order.status.value}",
                    "timestamp": datetime.utcnow().isoformat(),
                }
                return

            yield {
                "step": 1,
                "status": "in_progress",
                "message": "🔍 Discovering vendors...",
                "timestamp": datetime.utcnow().isoformat(),
            }

            vendors_found = await self._discover_vendors(work_order_id)

            yield {
                "step": 1,
                "status": "completed",
                "message": f"✓ Found {vendors_found} vendors",
                "data": {"vendors_count": vendors_found},
                "timestamp": datetime.utcnow().isoformat(),
            }

            yield {
                "step": 2,
                "status": "in_progress",
                "message": f"💬 Requesting quotes from {vendors_found} vendors...",
                "timestamp": datetime.utcnow().isoformat(),
            }

            quotes_requested = await self._request_all_quotes_parallel(work_order_id)

            yield {
                "step": 2,
                "status": "completed",
                "message": f"✓ Requested {quotes_requested} quotes",
                "data": {"quotes_requested": quotes_requested},
                "timestamp": datetime.utcnow().isoformat(),
            }

            yield {
                "step": 3,
                "status": "in_progress",
                "message": "📩 Collecting responses from vendors...",
                "timestamp": datetime.utcnow().isoformat(),
            }

            async for progress in self._simulate_all_responses_parallel(work_order_id):
                yield progress

            yield {
                "step": 4,
                "status": "in_progress",
                "message": "🎯 Evaluating quotes and ranking vendors...",
                "timestamp": datetime.utcnow().isoformat(),
            }

            ranked_vendors = await self._evaluate_and_rank_all(work_order_id)

            if not ranked_vendors:
                yield {
                    "step": 4,
                    "status": "error",
                    "message": "❌ No valid quotes received",
                    "timestamp": datetime.utcnow().isoformat(),
                }
                return

            yield {
                "step": 4,
                "status": "completed",
                "message": f"✓ Ranked {len(ranked_vendors)} vendors by quality and price",
                "data": {"total_vendors": len(ranked_vendors)},
                "timestamp": datetime.utcnow().isoformat(),
            }

            yield {
                "step": 5,
                "status": "in_progress",
                "message": "📋 Seeking confirmations (trying vendors in order)...",
                "timestamp": datetime.utcnow().isoformat(),
            }

            self.db.expire_all()
            work_order = self.work_order_service.get_work_order(work_order_id)
            if not work_order:
                yield {
                    "step": -1,
                    "status": "error",
                    "message": f"⚠️ Work order {work_order_id} not found",
                    "timestamp": datetime.utcnow().isoformat(),
                }
                return

            currency_info = get_currency_info(
                work_order.location_country or "United States"
            )
            currency_symbol = currency_info["symbol"]

            confirmed = False
            for attempt, vendor in enumerate(ranked_vendors, 1):
                yield {
                    "step": 5,
                    "status": "in_progress",
                    "message": f"📋 Attempt #{attempt}: {vendor['name']} ({currency_symbol}{vendor['price']}, {vendor['rating']}/10)...",
                    "timestamp": datetime.utcnow().isoformat(),
                }

                result = await self._try_single_vendor_confirmation(
                    work_order_id=work_order_id, vendor=vendor, attempt_number=attempt
                )

                if result["success"]:
                    yield {
                        "step": 5,
                        "status": "completed",
                        "message": f"✅ Vendor dispatched! {vendor['name']} confirmed.",
                        "data": result,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    confirmed = True
                    break
                else:
                    yield {
                        "step": 5,
                        "status": "in_progress",
                        "message": f"⚠️ {result['reason']} - Trying next vendor...",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    await asyncio.sleep(1)

            if not confirmed:
                yield {
                    "step": 5,
                    "status": "error",
                    "message": "❌ None of the vendors are available at the moment",
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            yield {
                "step": -1,
                "status": "error",
                "message": f"❌ Error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        finally:
            async with self._lock:
                self._running_automations.pop(work_order_id_str, None)

    async def _discover_vendors(self, work_order_id: UUID) -> int:
        existing_quotes = (
            self.db.query(Quote).filter(Quote.work_order_id == work_order_id).all()
        )

        if len(existing_quotes) == 0:
            self.work_order_service.start_vendor_discovery_workflow(work_order_id)
            await asyncio.sleep(2)
            quotes = (
                self.db.query(Quote).filter(Quote.work_order_id == work_order_id).all()
            )
            return len(quotes)
        else:
            return len(existing_quotes)

    async def _request_all_quotes_parallel(self, work_order_id: UUID) -> int:
        quotes = self.db.query(Quote).filter(Quote.work_order_id == work_order_id).all()
        quote_ids = [str(quote.id) for quote in quotes]

        tasks = []
        for quote_id in quote_ids:
            task = self._request_single_quote(UUID(quote_id))
            tasks.append(task)

        await asyncio.gather(*tasks)

        return len(quote_ids)

    async def _request_single_quote(self, quote_id: UUID):
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            return

        quote.status = "requested"
        self.db.commit()

    async def _simulate_all_responses_parallel(
        self, work_order_id: UUID
    ) -> AsyncGenerator[Dict, None]:
        quotes = (
            self.db.query(Quote)
            .filter(Quote.work_order_id == work_order_id, Quote.status == "requested")
            .all()
        )

        total = len(quotes)
        completed = 0
        tasks = []
        for quote in quotes:
            task = self._simulate_single_vendor_response(quote.id)
            tasks.append(task)

        for coro in asyncio.as_completed(tasks):
            await coro
            completed += 1

            progress_pct = int((completed / total) * 100)

            yield {
                "step": 3,
                "status": "in_progress",
                "message": f"📩 Collecting responses... ({completed}/{total})",
                "data": {
                    "completed": completed,
                    "total": total,
                    "progress": progress_pct,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

        yield {
            "step": 3,
            "status": "completed",
            "message": f"✓ Received {total} quotes",
            "data": {"quotes_received": total},
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _simulate_single_vendor_response(self, quote_id: UUID):
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            return

        await asyncio.sleep(random.uniform(0.5, 2.0))

        work_order = quote.work_order
        currency_info = get_currency_info(
            work_order.location_country or "United States"
        )
        currency_symbol = currency_info["symbol"]

        base_price = random.randint(150, 500)
        days_available = random.randint(1, 7)
        duration_hours = random.randint(2, 8)

        vendor_responses = [
            f"Hi! I can help with this. My quote is {currency_symbol}{base_price}. I'm available to start in {days_available} days and estimate {duration_hours} hours to complete. Let me know!",
            f"Hello, thank you for reaching out. Price: {currency_symbol}{base_price}, available in {days_available} days, completion time: ~{duration_hours} hours. Ready to start!",
            f"Yes, I'm interested! {currency_symbol}{base_price} total. Can start {days_available} days from now, should take about {duration_hours} hours. Please confirm.",
            f"I'd be happy to help! Quote: {currency_symbol}{base_price}. Available starting in {days_available} days. Estimated {duration_hours} hour job. Thanks!",
        ]

        inbound_message = random.choice(vendor_responses)
        use_sms = quote_id.int % 2 == 0

        if use_sms:
            await process_vendor_sms_response(
                db=self.db,
                quote_id=quote_id,
                vendor_id=quote.vendor.id,
                message=inbound_message,
            )
        else:
            await process_vendor_email_response(
                db=self.db,
                quote_id=quote_id,
                vendor_id=quote.vendor.id,
                message=inbound_message,
                subject="Re: Service opportunity - Quote request",
            )

    async def _evaluate_and_select_best(self, work_order_id: UUID) -> Dict:
        quotes = (
            self.db.query(Quote)
            .filter(Quote.work_order_id == work_order_id, Quote.price.isnot(None))
            .all()
        )

        best_quote = max(quotes, key=lambda q: q.composite_score or 0)
        await asyncio.sleep(1)

        return {
            "quote_id": str(best_quote.id),
            "vendor_id": str(best_quote.vendor.id),
            "name": best_quote.vendor.business_name,
            "price": best_quote.price,
            "rating": round(best_quote.quality_score, 1)
            if best_quote.quality_score
            else 0,
            "composite_score": round(best_quote.composite_score, 2)
            if best_quote.composite_score
            else 0,
        }

    async def _auto_confirm_and_dispatch(self, work_order_id: UUID, quote_id: UUID):
        self.db.expire_all()
        work_order = self.work_order_service.get_work_order(work_order_id)
        if not work_order:
            return

        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            return

        if not work_order.facility_manager_email:
            work_order.facility_manager_email = "manager@tavi.io"
            work_order.facility_manager_name = "Albert"

        # Update work order with selected vendor
        work_order.selected_vendor_id = quote.vendor_id
        work_order.status = WorkOrderStatus.VENDOR_SELECTED
        quote.status = "accepted"
        self.db.commit()

        await send_facility_manager_confirmation(
            self.db, work_order_id, quote.vendor_id
        )
        await asyncio.sleep(1)

        work_order.facility_confirmed = datetime.utcnow()
        work_order.status = WorkOrderStatus.AWAITING_VENDOR_DISPATCH

        self.comm_service.log_communication(
            work_order_id=work_order.id,
            vendor_id=None,
            channel=CommunicationChannel.EMAIL,
            direction="inbound",
            message=f"APPROVED - Vendor selection looks great! Proceed with {quote.vendor.business_name}. Thanks!",
            sent_successfully=True,
            metadata={
                "type": "facility_confirmation",
                "sender": work_order.facility_manager_email,
                "sender_name": work_order.facility_manager_name,
                "automation": True,
                "simulated": True,
            },
        )

        self.db.commit()
        await asyncio.sleep(1)

        await send_vendor_dispatch_confirmation(self.db, work_order_id, quote.vendor_id)
        await asyncio.sleep(1)

        work_order.vendor_dispatch_confirmed = datetime.utcnow()
        work_order.status = WorkOrderStatus.DISPATCHED

        self.comm_service.log_communication(
            work_order_id=work_order.id,
            vendor_id=quote.vendor_id,
            channel=CommunicationChannel.EMAIL,
            direction="inbound",
            message=f"CONFIRMED - I'll be there on {quote.availability_date.strftime('%Y-%m-%d') if quote.availability_date else 'the scheduled date'}. Looking forward to it! Thanks!",
            sent_successfully=True,
            metadata={
                "type": "vendor_dispatch_confirmation",
                "automation": True,
                "simulated": True,
            },
        )

        self.db.commit()

    async def _evaluate_and_rank_all(self, work_order_id: UUID) -> List[Dict]:
        quotes = (
            self.db.query(Quote)
            .filter(Quote.work_order_id == work_order_id, Quote.price.isnot(None))
            .all()
        )

        sorted_quotes = sorted(
            quotes, key=lambda q: q.composite_score or 0, reverse=True
        )
        await asyncio.sleep(1)

        return [
            {
                "quote_id": str(q.id),
                "vendor_id": str(q.vendor.id),
                "name": q.vendor.business_name,
                "price": q.price,
                "rating": round(q.quality_score, 1) if q.quality_score else 0,
                "composite_score": round(q.composite_score, 2)
                if q.composite_score
                else 0,
            }
            for q in sorted_quotes
        ]

    async def _try_single_vendor_confirmation(
        self, work_order_id: UUID, vendor: Dict, attempt_number: int
    ) -> Dict:
        self.db.expire_all()
        work_order = self.work_order_service.get_work_order(work_order_id)
        if not work_order:
            return {"success": False, "reason": f"Work order {work_order_id} not found"}

        quote_id = UUID(vendor["quote_id"])
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            return {"success": False, "reason": f"Quote {quote_id} not found"}

        if not work_order.facility_manager_email:
            work_order.facility_manager_email = "manager@tavi.io"
            work_order.facility_manager_name = "Albert"

        # Update work order with selected vendor (but DON'T mark quote as accepted yet)
        work_order.selected_vendor_id = quote.vendor_id
        work_order.status = WorkOrderStatus.VENDOR_SELECTED
        # ✅ REMOVED: quote.status = 'accepted' - only set after BOTH confirmations
        self.db.commit()

        await send_facility_manager_confirmation(
            self.db, work_order_id, quote.vendor_id
        )
        await asyncio.sleep(0.5)

        approval_chance = 0.8 - (attempt_number - 1) * 0.15
        facility_approves = random.random() < approval_chance

        if not facility_approves:
            # ✅ Reset work order status and selected vendor
            work_order.selected_vendor_id = None
            work_order.status = WorkOrderStatus.CONTACTING_VENDORS
            self.db.commit()

            comm_service = CommunicationService(self.db)
            comm_service.log_communication(
                work_order_id=work_order.id,
                vendor_id=None,
                channel="EMAIL",
                direction="inbound",
                message=f"I reviewed {quote.vendor.business_name} but would like to see other options. Can we try another vendor?",
                sent_successfully=True,
                metadata={"source": "facility_manager", "decision": "rejected"},
            )
            return {
                "success": False,
                "reason": f"Facility manager declined {vendor['name']}",
            }

        work_order.facility_confirmed = datetime.utcnow()
        work_order.status = WorkOrderStatus.AWAITING_VENDOR_DISPATCH

        comm_service = CommunicationService(self.db)
        comm_service.log_communication(
            work_order_id=work_order.id,
            vendor_id=None,
            channel="EMAIL",
            direction="inbound",
            message="APPROVED - Please proceed with this vendor.",
            sent_successfully=True,
            metadata={"source": "facility_manager", "decision": "approved"},
        )
        self.db.commit()
        await asyncio.sleep(0.5)

        await send_vendor_dispatch_confirmation(self.db, work_order_id, quote.vendor_id)
        await asyncio.sleep(0.5)

        vendor_confirms = random.random() < 0.85

        if not vendor_confirms:
            # ✅ Reset work order status and selected vendor
            work_order.selected_vendor_id = None
            work_order.status = WorkOrderStatus.CONTACTING_VENDORS
            work_order.facility_confirmed = None  # Reset facility confirmation too
            self.db.commit()

            comm_service.log_communication(
                work_order_id=work_order.id,
                vendor_id=quote.vendor_id,
                channel="SMS",
                direction="inbound",
                message="Sorry, something came up and I'm no longer available for this job.",
                sent_successfully=True,
                metadata={"source": "vendor", "decision": "declined"},
            )
            return {
                "success": False,
                "reason": f"{vendor['name']} is no longer available",
            }

        # ✅ BOTH confirmations received - NOW mark as accepted and dispatched
        quote.status = "accepted"
        work_order.vendor_dispatch_confirmed = datetime.utcnow()
        work_order.status = WorkOrderStatus.DISPATCHED

        comm_service.log_communication(
            work_order_id=work_order.id,
            vendor_id=quote.vendor_id,
            channel="SMS",
            direction="inbound",
            message="CONFIRMED - I'll be there as scheduled. Looking forward to it!",
            sent_successfully=True,
            metadata={"source": "vendor", "decision": "confirmed"},
        )

        self.db.commit()

        return {
            "success": True,
            "vendor_name": vendor["name"],
            "price": vendor["price"],
        }
