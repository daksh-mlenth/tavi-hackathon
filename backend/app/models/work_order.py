from sqlalchemy import Column, String, Text, DateTime, Float, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class WorkOrderStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    DISCOVERING_VENDORS = "discovering_vendors"
    CONTACTING_VENDORS = "contacting_vendors"
    EVALUATING_QUOTES = "evaluating_quotes"
    AWAITING_APPROVAL = "awaiting_approval"
    VENDOR_SELECTED = "vendor_selected"
    AWAITING_FACILITY_CONFIRMATION = "awaiting_facility_confirmation"
    AWAITING_VENDOR_DISPATCH = "awaiting_vendor_dispatch"
    DISPATCHED = "dispatched"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TradeType(str, enum.Enum):
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    HVAC = "hvac"
    LANDSCAPING = "landscaping"
    ROOFING = "roofing"
    PAINTING = "painting"
    CARPENTRY = "carpentry"
    CLEANING = "cleaning"
    PEST_CONTROL = "pest_control"
    GENERAL_MAINTENANCE = "general_maintenance"


class WorkType(str, enum.Enum):
    REACTIVE = "reactive"
    PREVENTIVE = "preventive"
    OTHER = "other"


class Priority(str, enum.Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Category(str, enum.Enum):
    DAMAGE = "damage"
    ELECTRICAL = "electrical"
    INSPECTION = "inspection"
    MECHANICAL = "mechanical"
    PREVENTIVE = "preventive"
    PROJECT = "project"
    REFRIGERATION = "refrigeration"
    SAFETY = "safety"
    STANDARD_OPERATING_PROCEDURE = "standard_operating_procedure"


class Recurrence(str, enum.Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    trade_type = Column(
        SQLEnum(TradeType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    location_address = Column(String(500), nullable=False)
    location_city = Column(String(100))
    location_state = Column(String(50))
    location_zip = Column(String(20))
    location_country = Column(String(100), default="United States")
    location_latitude = Column(Float)
    location_longitude = Column(Float)

    asset_name = Column(String(255), nullable=True)
    asset_type = Column(String(100), nullable=True)

    status = Column(
        SQLEnum(WorkOrderStatus, values_callable=lambda x: [e.value for e in x]),
        default=WorkOrderStatus.SUBMITTED,
    )
    urgency = Column(String(50))
    priority = Column(
        SQLEnum(Priority, values_callable=lambda x: [e.value for e in x]),
        default=Priority.MEDIUM,
    )

    work_type = Column(
        SQLEnum(WorkType, values_callable=lambda x: [e.value for e in x]),
        default=WorkType.REACTIVE,
    )
    category = Column(
        SQLEnum(Category, values_callable=lambda x: [e.value for e in x]), nullable=True
    )
    recurrence = Column(
        SQLEnum(Recurrence, values_callable=lambda x: [e.value for e in x]),
        default=Recurrence.NONE,
    )

    preferred_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    scheduled_date = Column(DateTime, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    parts_needed = Column(ARRAY(String), nullable=True)
    special_requirements = Column(Text, nullable=True)

    customer_name = Column(String(200))
    customer_email = Column(String(200))
    customer_phone = Column(String(50))

    facility_manager_name = Column(String(200))
    facility_manager_email = Column(String(200))
    facility_manager_phone = Column(String(50))
    facility_confirmed = Column(DateTime, nullable=True)
    vendor_dispatch_confirmed = Column(DateTime, nullable=True)
    selected_vendor_id = Column(UUID(as_uuid=True), nullable=True)

    raw_input = Column(Text)
    ai_processing_log = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    quotes = relationship(
        "Quote", back_populates="work_order", cascade="all, delete-orphan"
    )
    communication_logs = relationship(
        "CommunicationLog", back_populates="work_order", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<WorkOrder {self.id} - {self.title}>"
