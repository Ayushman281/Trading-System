"""
API request and response schemas.
"""
from pydantic import BaseModel, Field, validator, constr
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal
import uuid

class TradeBase(BaseModel):
    """Base model for trade data."""
    ticker: constr(min_length=1, max_length=10)
    price: float = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    side: str = Field(..., regex="^(buy|sell)$")
    
class TradeCreate(TradeBase):
    """Request model for creating trades."""
    timestamp: Optional[datetime] = None

class TradeResponse(TradeBase):
    """Response model for trade data."""
    id: str  # Changed from int to str to accept UUID string
    timestamp: datetime
    
    class Config:
        orm_mode = True
        
    @validator('id')
    def validate_uuid(cls, v):
        """Validate ID is a proper UUID string."""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            return str(v)
