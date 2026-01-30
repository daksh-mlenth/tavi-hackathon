"""
Autonomous AI Agent API endpoints
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
import json

from app.database import get_db
from app.services.automation_service import AutomationService


router = APIRouter()


@router.get("/auto-handle/{work_order_id}")
async def auto_handle_work_order_stream(
    work_order_id: str, db: Session = Depends(get_db)
):
    """
    Autonomous AI agent that handles entire work order lifecycle
    Returns Server-Sent Events (SSE) for real-time progress updates
    """

    async def event_generator():
        automation_service = AutomationService(db)

        try:
            async for progress in automation_service.auto_handle_work_order(
                UUID(work_order_id)
            ):
                # Format as SSE
                yield f"data: {json.dumps(progress)}\n\n"
        except Exception as e:
            error_event = {
                "step": -1,
                "status": "error",
                "message": f"❌ Error: {str(e)}",
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
