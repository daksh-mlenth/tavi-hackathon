from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.schemas.work_order import WorkOrderCreate, WorkOrderResponse, WorkOrderList
from app.services.work_order_service import WorkOrderService
from app.services.ai_agent_service import AIAgentService
from app.models.work_order import WorkOrderStatus

router = APIRouter()


@router.post("", response_model=WorkOrderResponse, status_code=201)
async def create_work_order(
    work_order_data: WorkOrderCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    service = WorkOrderService(db)
    ai_service = AIAgentService()

    parsed_data = await ai_service.parse_work_order_input(work_order_data.raw_input)
    work_order = service.create_work_order(work_order_data, parsed_data)

    background_tasks.add_task(service.start_vendor_discovery_workflow, work_order.id)

    return work_order


@router.get("", response_model=WorkOrderList)
def list_work_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    service = WorkOrderService(db)
    work_orders, total = service.list_work_orders(skip, limit)
    return WorkOrderList(work_orders=work_orders, total=total)


@router.get("/{work_order_id}", response_model=WorkOrderResponse)
def get_work_order(work_order_id: UUID, db: Session = Depends(get_db)):
    service = WorkOrderService(db)
    work_order = service.get_work_order(work_order_id)

    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")

    return work_order


@router.patch("/{work_order_id}/status", response_model=WorkOrderResponse)
def update_work_order_status(
    work_order_id: UUID, status_update: dict, db: Session = Depends(get_db)
):
    service = WorkOrderService(db)
    work_order = service.get_work_order(work_order_id)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")

    new_status = status_update.get("status")
    if new_status:
        try:
            work_order.status = WorkOrderStatus(new_status)
            db.commit()
            db.refresh(work_order)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")

    return work_order


@router.post("/{work_order_id}/discover-vendors")
async def discover_vendors(
    work_order_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    service = WorkOrderService(db)

    work_order = service.get_work_order(work_order_id)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")

    background_tasks.add_task(service.start_vendor_discovery_workflow, work_order_id)

    return {"message": "Vendor discovery started", "work_order_id": str(work_order_id)}


@router.post("/{work_order_id}/contact-vendors")
async def contact_vendors(
    work_order_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    service = WorkOrderService(db)

    work_order = service.get_work_order(work_order_id)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")

    background_tasks.add_task(service.start_vendor_contact_workflow, work_order_id)

    return {
        "message": "Vendor contact process started",
        "work_order_id": str(work_order_id),
    }
