from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Enum as SQLEnum, JSON
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
    VENDOR_SELECTED = "vendor_selected"  # Vendor chosen, awaiting confirmations
    AWAITING_FACILITY_CONFIRMATION = "awaiting_facility_confirmation"  # Waiting for facility manager approval
    AWAITING_VENDOR_DISPATCH = "awaiting_vendor_dispatch"  # Waiting for vendor to confirm dispatch
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
    
    # Basic Information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    trade_type = Column(SQLEnum(TradeType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    
    # Location
    location_address = Column(String(500), nullable=False)
    location_city = Column(String(100))
    location_state = Column(String(50))
    location_zip = Column(String(20))
    location_country = Column(String(100), default="United States")  # For currency localization
    location_latitude = Column(Float)
    location_longitude = Column(Float)
    
    # Asset Information
    asset_name = Column(String(255), nullable=True)  # e.g., "HVAC Unit", "Roof Section A"
    asset_type = Column(String(100), nullable=True)  # e.g., "HVAC", "Plumbing", "Electrical"
    
    # Status and Priority
    status = Column(SQLEnum(WorkOrderStatus, values_callable=lambda x: [e.value for e in x]), default=WorkOrderStatus.SUBMITTED)
    urgency = Column(String(50))  # low, medium, high, emergency
    priority = Column(SQLEnum(Priority, values_callable=lambda x: [e.value for e in x]), default=Priority.MEDIUM)
    
    # Work Classification
    work_type = Column(SQLEnum(WorkType, values_callable=lambda x: [e.value for e in x]), default=WorkType.REACTIVE)
    category = Column(SQLEnum(Category, values_callable=lambda x: [e.value for e in x]), nullable=True)
    recurrence = Column(SQLEnum(Recurrence, values_callable=lambda x: [e.value for e in x]), default=Recurrence.NONE)
    
    # Scheduling
    preferred_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    scheduled_date = Column(DateTime, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    
    # Parts and Requirements
    parts_needed = Column(ARRAY(String), nullable=True)  # Array of parts/materials
    special_requirements = Column(Text, nullable=True)
    
    # Customer Information
    customer_name = Column(String(200))
    customer_email = Column(String(200))
    customer_phone = Column(String(50))
    
    # Facility Manager (for dispatch confirmation)
    facility_manager_name = Column(String(200))
    facility_manager_email = Column(String(200))
    facility_manager_phone = Column(String(50))
    facility_confirmed = Column(DateTime, nullable=True)  # When facility manager confirmed
    vendor_dispatch_confirmed = Column(DateTime, nullable=True)  # When vendor confirmed dispatch
    
    # Selected Vendor (for confirmation phase)
    selected_vendor_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Metadata
    raw_input = Column(Text)  # Original user input (voice/chat)
    ai_processing_log = Column(JSON)  # Log of AI processing steps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    quotes = relationship("Quote", back_populates="work_order", cascade="all, delete-orphan")
    communication_logs = relationship("CommunicationLog", back_populates="work_order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<WorkOrder {self.id} - {self.title}>"
