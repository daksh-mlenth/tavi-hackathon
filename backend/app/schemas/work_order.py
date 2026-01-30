from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.work_order import (
    WorkOrderStatus, 
    TradeType, 
    WorkType, 
    Priority, 
    Category, 
    Recurrence
)
from app.constants import get_currency_info


class WorkOrderCreate(BaseModel):
    raw_input: str = Field(..., description="Natural language input from user")
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None


class WorkOrderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    trade_type: Optional[TradeType] = None
    location_address: Optional[str] = None
    status: Optional[WorkOrderStatus] = None
    urgency: Optional[str] = None
    preferred_date: Optional[datetime] = None


class WorkOrderResponse(BaseModel):
    id: UUID
    title: str
    description: str
    trade_type: TradeType
    
    location_address: str
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_zip: Optional[str] = None
    location_country: Optional[str] = "United States"
    currency: Optional[str] = "USD"
    currency_symbol: Optional[str] = "$"
    
    asset_name: Optional[str] = None
    asset_type: Optional[str] = None
    
    status: WorkOrderStatus
    urgency: Optional[str] = None
    priority: Optional[Priority] = None
    work_type: Optional[WorkType] = None
    category: Optional[Category] = None
    recurrence: Optional[Recurrence] = None
    
    preferred_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    scheduled_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    parts_needed: Optional[List[str]] = None
    special_requirements: Optional[str] = None
    
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    
    @model_validator(mode='after')
    def compute_currency(self):
        if self.location_country:
            currency_info = get_currency_info(self.location_country)
            self.currency = currency_info['code']
            self.currency_symbol = currency_info['symbol']
        return self
    
    class Config:
        from_attributes = True


class WorkOrderList(BaseModel):
    work_orders: List[WorkOrderResponse]
    total: int
