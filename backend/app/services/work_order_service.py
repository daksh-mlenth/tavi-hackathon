from sqlalchemy.orm import Session
from typing import List, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime

from app.constants import DEFAULT_TRADE_TYPE, DEFAULT_URGENCY
from app.models.work_order import (
    WorkOrder, 
    WorkOrderStatus, 
    TradeType, 
    WorkType, 
    Priority, 
    Category, 
    Recurrence
)
from app.schemas.work_order import WorkOrderCreate, WorkOrderResponse
from app.services.vendor_discovery_service import VendorDiscoveryService
from app.services.vendor_contact_service import VendorContactService
from app.utils import safe_enum


class WorkOrderService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_work_order(
        self,
        work_order_data: WorkOrderCreate,
        parsed_data: Dict[str, Any]
    ) -> WorkOrder:
        trade_type = safe_enum(TradeType, parsed_data.get("trade_type"), TradeType(DEFAULT_TRADE_TYPE))
        work_type = safe_enum(WorkType, parsed_data.get("work_type"), WorkType.REACTIVE)
        priority = safe_enum(Priority, parsed_data.get("priority"), Priority.MEDIUM)
        category = safe_enum(Category, parsed_data.get("category"), None)
        recurrence = safe_enum(Recurrence, parsed_data.get("recurrence"), Recurrence.NONE)
        
        preferred_date = parsed_data.get("preferred_date")
        if preferred_date and isinstance(preferred_date, str):
            try:
                preferred_date = datetime.fromisoformat(preferred_date)
            except ValueError:
                preferred_date = None
        
        due_date = parsed_data.get("due_date")
        if due_date and isinstance(due_date, str):
            try:
                due_date = datetime.fromisoformat(due_date)
            except ValueError:
                due_date = None
        
        work_order = WorkOrder(
            title=parsed_data.get("title", "Work Order"),
            description=parsed_data.get("description", work_order_data.raw_input),
            trade_type=trade_type,
            location_address=parsed_data.get("location_address") or parsed_data.get("location_city", "Address to be specified"),
            location_city=parsed_data.get("location_city"),
            location_state=parsed_data.get("location_state"),
            location_zip=parsed_data.get("location_zip"),
            location_country=parsed_data.get("location_country", "United States"),
            asset_name=parsed_data.get("asset_name"),
            asset_type=parsed_data.get("asset_type"),
            status=WorkOrderStatus.SUBMITTED,
            urgency=parsed_data.get("urgency", DEFAULT_URGENCY),
            priority=priority,
            work_type=work_type,
            category=category,
            recurrence=recurrence,
            preferred_date=preferred_date,
            due_date=due_date,
            estimated_hours=parsed_data.get("estimated_hours"),
            parts_needed=parsed_data.get("parts_needed", []),
            special_requirements=parsed_data.get("special_requirements"),
            customer_name=work_order_data.customer_name,
            customer_email=work_order_data.customer_email,
            customer_phone=work_order_data.customer_phone,
            raw_input=work_order_data.raw_input,
            ai_processing_log=parsed_data
        )
        
        self.db.add(work_order)
        self.db.commit()
        self.db.refresh(work_order)
        
        return work_order
    
    def get_work_order(self, work_order_id: UUID) -> WorkOrder:
        """Get a work order by ID"""
        return self.db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    
    def list_work_orders(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[WorkOrder], int]:
        """List all work orders with pagination"""
        total = self.db.query(WorkOrder).count()
        work_orders = (
            self.db.query(WorkOrder)
            .order_by(WorkOrder.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return work_orders, total
    
    def update_status(self, work_order_id: UUID, status: WorkOrderStatus) -> WorkOrder:
        """Update work order status"""
        work_order = self.get_work_order(work_order_id)
        if work_order:
            work_order.status = status
            work_order.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(work_order)
        return work_order
    
    async def start_vendor_discovery_workflow(self, work_order_id: UUID):
        """Start the vendor discovery process (runs in background)"""
        work_order = self.get_work_order(work_order_id)
        if not work_order:
            return
        
        self.update_status(work_order_id, WorkOrderStatus.DISCOVERING_VENDORS)
        
        discovery_service = VendorDiscoveryService(self.db)
        vendors = await discovery_service.discover_vendors_for_work_order(work_order)
        
        print(f"✅ Discovered {len(vendors)} vendors for work order {work_order_id}")
        
        if vendors:
            self.update_status(work_order_id, WorkOrderStatus.AWAITING_APPROVAL)
    
    async def start_vendor_contact_workflow(self, work_order_id: UUID):
        work_order = self.get_work_order(work_order_id)
        if not work_order:
            return
        
        self.update_status(work_order_id, WorkOrderStatus.CONTACTING_VENDORS)
        
        contact_service = VendorContactService(self.db)
        await contact_service.contact_all_vendors_for_work_order(work_order)
        
        # Move to evaluation status
        self.update_status(work_order_id, WorkOrderStatus.EVALUATING_QUOTES)
