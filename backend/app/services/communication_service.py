from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models.communication_log import CommunicationLog, CommunicationChannel


class CommunicationService:
    """Service for managing communication logs"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_communication(
        self,
        work_order_id: UUID,
        channel: CommunicationChannel,
        direction: str,
        message: str,
        vendor_id: Optional[UUID] = None,
        **kwargs
    ) -> CommunicationLog:
        """Log a communication event"""
        comm_log = CommunicationLog(
            work_order_id=work_order_id,
            vendor_id=vendor_id,
            channel=channel,
            direction=direction,
            message=message,
            **kwargs
        )
        
        self.db.add(comm_log)
        self.db.commit()
        self.db.refresh(comm_log)
        
        return comm_log
    
    def get_communications_for_work_order(
        self,
        work_order_id: UUID
    ) -> List[dict]:
        """Get all communications for a work order (unified stream) with vendor names"""
        from app.models.vendor import Vendor
        from sqlalchemy.orm import joinedload
        
        comms = (
            self.db.query(CommunicationLog)
            .filter(CommunicationLog.work_order_id == work_order_id)
            .order_by(CommunicationLog.timestamp.asc())
            .all()
        )
        
        # Enrich with vendor names
        result = []
        for comm in comms:
            comm_dict = {
                "id": comm.id,
                "work_order_id": comm.work_order_id,
                "vendor_id": comm.vendor_id,
                "vendor_name": None,
                "channel": comm.channel,
                "direction": comm.direction,
                "subject": comm.subject,
                "message": comm.message,
                "response": comm.response,
                "sent_successfully": comm.sent_successfully,
                "timestamp": comm.timestamp
            }
            
            # Get vendor name if vendor_id exists
            if comm.vendor_id:
                vendor = self.db.query(Vendor).filter(Vendor.id == comm.vendor_id).first()
                if vendor:
                    comm_dict["vendor_name"] = vendor.business_name
            
            result.append(comm_dict)
        
        return result
    
    def get_communications_for_vendor(
        self,
        vendor_id: UUID
    ) -> List[CommunicationLog]:
        """Get all communications with a specific vendor"""
        return (
            self.db.query(CommunicationLog)
            .filter(CommunicationLog.vendor_id == vendor_id)
            .order_by(CommunicationLog.timestamp.desc())
            .all()
        )
    
    def get_conversation_history(
        self,
        work_order_id: UUID,
        vendor_id: UUID,
        limit: int = 10
    ) -> str:
        """
        Get formatted conversation history for AI context.
        Returns a string with all messages formatted for readability.
        """
        communications = (
            self.db.query(CommunicationLog)
            .filter(
                CommunicationLog.work_order_id == work_order_id,
                CommunicationLog.vendor_id == vendor_id
            )
            .order_by(CommunicationLog.timestamp.asc())
            .limit(limit)
            .all()
        )
        
        if not communications:
            return "No previous conversation"
        
        history = []
        for comm in communications:
            direction_label = "You (Tavi)" if comm.direction == "outbound" else "Vendor"
            channel_label = comm.channel.value.upper()
            
            entry = f"[{direction_label} via {channel_label}]\n"
            if comm.subject:
                entry += f"Subject: {comm.subject}\n"
            entry += f"{comm.message}\n"
            
            history.append(entry)
        
        return "\n---\n".join(history)
