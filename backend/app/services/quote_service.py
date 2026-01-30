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
    def __init__(self, db: Session):
        self.db = db
    
    def get_quote(self, quote_id: UUID) -> Optional[Quote]:
        return self.db.query(Quote).filter(Quote.id == quote_id).first()
    
    def get_quotes_for_work_order(self, work_order_id: UUID) -> List[Quote]:
        return (
            self.db.query(Quote)
            .options(joinedload(Quote.vendor))
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
        quote = self.get_quote(quote_id)
        if quote:
            quote.price = price
            quote.availability_date = availability_date
            quote.quote_text = quote_text
            quote.status = QuoteStatus.RECEIVED
            quote.received_at = datetime.utcnow()
            
            if price:
                quote.price_score = max(0, 100 - (price / 10))
            
            if quote.vendor:
                quote.quality_score = quote.vendor.composite_score or DEFAULT_VENDOR_SCORE
            
            if availability_date and isinstance(availability_date, datetime):
                days_until_available = (availability_date - datetime.utcnow()).days
                quote.availability_score = max(0, 100 - (days_until_available * 5))
            
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
            quote.work_order.status = WorkOrderStatus.DISPATCHED
            
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
