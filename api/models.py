"""
Database models for the API.
"""
import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Enum, UUID
from config.database import Base, engine

class TradeSide(enum.Enum):
    """Enumeration for trade sides (buy/sell)."""
    BUY = "buy"
    SELL = "sell"

class Trade(Base):
    """Trade model for storing trade information."""
    __tablename__ = "trades"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), nullable=False, index=True)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    side = Column(Enum(TradeSide), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """Convert Trade object to dictionary."""
        return {
            "id": str(self.id),
            "ticker": self.ticker,
            "price": self.price,
            "quantity": self.quantity,
            "side": self.side.value,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create Trade object from dictionary."""
        return cls(
            ticker=data.get("ticker"),
            price=data.get("price"),
            quantity=data.get("quantity"),
            side=TradeSide(data.get("side")),
            timestamp=data.get("timestamp") or datetime.utcnow(),
        )

# Do NOT create tables automatically here - this should be done in the initialize script
# The Base.metadata.create_all(bind=engine) line that was causing issues has been removed
