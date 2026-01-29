from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.constants import (
    QUOTE_PRICE_WEIGHT,
    QUOTE_QUALITY_WEIGHT,
    QUOTE_AVAILABILITY_WEIGHT,
    DEFAULT_VENDOR_SCORE,
)
from app.models.quote import Quote, QuoteStatus
from app.models.work_order import WorkOrderStatus


class QuoteService:
    """Service for managing quotes"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_quote(self, quote_id: UUID) -> Optional[Quote]:
        """Get a quote by ID"""
        return self.db.query(Quote).filter(Quote.id == quote_id).first()
    
    def get_quotes_for_work_order(self, work_order_id: UUID) -> List[Quote]:
        """Get all quotes for a work order, sorted by composite score"""
        return (
            self.db.query(Quote)
            .options(joinedload(Quote.vendor))  # Eagerly load vendor details
            .filter(Quote.work_order_id == work_order_id)
            .order_by(Quote.composite_score.desc().nullslast())
            .all()
        )
    
    def create_quote(
        self,
        work_order_id: UUID,
        vendor_id: UUID,
        **quote_data
    ) -> Quote:
        """Create a new quote"""
        quote = Quote(
            work_order_id=work_order_id,
            vendor_id=vendor_id,
            **quote_data
        )
        
        self.db.add(quote)
        self.db.commit()
        self.db.refresh(quote)
        
        return quote
    
    def update_quote_with_response(
        self,
        quote_id: UUID,
        price: Optional[float],
        availability_date: Optional[datetime],
        quote_text: str
    ) -> Quote:
        """Update a quote when vendor responds"""
        quote = self.get_quote(quote_id)
        if quote:
            quote.price = price
            quote.availability_date = availability_date
            quote.quote_text = quote_text
            quote.status = QuoteStatus.RECEIVED
            quote.received_at = datetime.utcnow()
            
            # Calculate scores (simplified)
            if price:
                # Lower price = higher score (normalize to 0-100)
                quote.price_score = max(0, 100 - (price / 10))
            
            # Get vendor quality score from vendor table
            if quote.vendor:
                quote.quality_score = quote.vendor.composite_score or DEFAULT_VENDOR_SCORE
            
            # Availability score (sooner = better)
            if availability_date and isinstance(availability_date, datetime):
                days_until_available = (availability_date - datetime.utcnow()).days
                quote.availability_score = max(0, 100 - (days_until_available * 5))
            
            # Composite score (weighted average)
            scores = []
            if quote.price_score:
                scores.append(quote.price_score * QUOTE_PRICE_WEIGHT)
            if quote.quality_score:
                scores.append(quote.quality_score * QUOTE_QUALITY_WEIGHT)
            if quote.availability_score:
                scores.append(quote.availability_score * QUOTE_AVAILABILITY_WEIGHT)
            
            if scores:
                quote.composite_score = sum(scores) / len(scores)
            
            self.db.commit()
            self.db.refresh(quote)
        
        return quote
    
    def accept_quote(self, quote_id: UUID) -> Quote:
        """Accept a quote and update work order status"""
        quote = self.get_quote(quote_id)
        if quote:
            quote.status = QuoteStatus.ACCEPTED
            
            # Update work order status
            quote.work_order.status = WorkOrderStatus.DISPATCHED
            
            # Reject other quotes
            other_quotes = (
                self.db.query(Quote)
                .filter(
                    Quote.work_order_id == quote.work_order_id,
                    Quote.id != quote_id
                )
                .all()
            )
            for other_quote in other_quotes:
                other_quote.status = QuoteStatus.REJECTED
            
            self.db.commit()
            self.db.refresh(quote)
        
        return quote
