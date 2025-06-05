"""
Process and store market data from the WebSocket feed.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from collections import defaultdict
from utils.logger import get_logger
from config.database import get_db_session
from api.models import Trade, TradeSide

logger = get_logger(__name__)

class DataProcessor:
    def __init__(self):
        """
        Initialize the data processor for market data.
        """
        self.ticker_stats = defaultdict(lambda: {
            "last_price": None,
            "high_price": 0.0,
            "low_price": float('inf'),
            "volume": 0,
            "price_sum": 0.0,  # For calculating average
            "update_count": 0,  # For calculating average
            "last_calc_time": datetime.now()
        })
    
    async def process_stock_data(self, ticker, price, timestamp):
        """
        Process stock price data and store statistics.
        
        Args:
            ticker: Stock ticker symbol
            price: Current price
            timestamp: Time of the update
        """
        stats = self.ticker_stats[ticker]
        
        # Update statistics
        if stats["last_price"] is None:
            stats["last_price"] = price
        
        stats["high_price"] = max(stats["high_price"], price)
        stats["low_price"] = min(stats["low_price"], price)
        stats["volume"] += 1  # In a real system this would be actual trade volume
        stats["price_sum"] += price
        stats["update_count"] += 1
        
        # Check if it's time to calculate and store 5-minute average
        if timestamp - stats["last_calc_time"] >= timedelta(minutes=5):
            await self._store_average_price(ticker, timestamp)
            
    async def _store_average_price(self, ticker, timestamp):
        """
        Calculate and store the 5-minute average price.
        
        Args:
            ticker: Stock ticker symbol
            timestamp: Current timestamp
        """
        stats = self.ticker_stats[ticker]
        
        if stats["update_count"] > 0:
            avg_price = stats["price_sum"] / stats["update_count"]
            
            logger.info(f"Storing 5-minute average for {ticker}: ${avg_price:.2f}")
            
            # Get a database session
            with get_db_session() as db:
                # Save the average price as a database record
                # In a real system, you might have a separate table for this
                # For now, we'll create a "meta" trade record
                db_record = Trade(
                    ticker=ticker,
                    price=avg_price,
                    quantity=stats["volume"],
                    side=TradeSide.BUY,  # Placeholder for a statistical record
                    timestamp=timestamp
                )
                
                db.add(db_record)
                db.commit()
            
            # Reset statistics for the next period
            stats["price_sum"] = 0.0
            stats["update_count"] = 0
            stats["volume"] = 0
            stats["last_calc_time"] = timestamp
