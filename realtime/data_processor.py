"""
Process and store market data from the WebSocket feed.
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Float, DateTime, Integer
from collections import defaultdict
from utils.logger import get_logger
from config.database import get_db_session, Base, engine
from api.models import Trade, TradeSide

logger = get_logger(__name__)

# Define the model for storing stock price averages
class StockPriceAverage(Base):
    """Model for storing average stock prices over time intervals."""
    __tablename__ = "stock_price_averages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    interval_minutes = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    average_price = Column(Float, nullable=False)
    min_price = Column(Float, nullable=False)
    max_price = Column(Float, nullable=False)
    data_points = Column(Integer, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "ticker": self.ticker,
            "interval_minutes": self.interval_minutes,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "average_price": self.average_price,
            "min_price": self.min_price,
            "max_price": self.max_price,
            "data_points": self.data_points
        }

# Create the table if it doesn't exist
Base.metadata.create_all(bind=engine)

class DataProcessor:
    """
    Process and store time-based statistics from price data.
    """
    def __init__(self, interval_minutes=5):
        """
        Initialize the data processor.
        
        Args:
            interval_minutes: Time interval in minutes for calculating averages
        """
        self.interval_minutes = interval_minutes
        self.price_buffer = defaultdict(list)  # {ticker: [(timestamp, price), ...]}
        self.last_processed = {}  # {ticker: timestamp}
        logger.info(f"Data processor initialized with {interval_minutes}-minute intervals")
    
    async def process_price_update(self, ticker, price, timestamp):
        """
        Process a price update and store time-based statistics.
        
        Args:
            ticker: Stock ticker symbol
            price: Current price
            timestamp: Timestamp of the update
        """
        # Skip if ticker is None
        if ticker is None:
            logger.warning("Received price update with None ticker, skipping")
            return
            
        # Add the price to buffer
        self.price_buffer[ticker].append((timestamp, price))
        
        # Check if it's time to calculate average
        await self._calculate_averages_if_needed(ticker, timestamp)
    
    async def _calculate_averages_if_needed(self, ticker, timestamp):
        """
        Calculate and store averages if the time interval has passed.
        
        Args:
            ticker: Stock ticker symbol
            timestamp: Current timestamp
        """
        # Get the last processed time for the ticker
        last_time = self.last_processed.get(ticker)
        
        # If there's no record or the interval has passed, calculate averages
        if last_time is None or timestamp - last_time >= timedelta(minutes=self.interval_minutes):
            await self._store_average_price(ticker, timestamp)
    
    async def _store_average_price(self, ticker, timestamp):
        """
        Calculate and store the average price for the ticker.
        
        Args:
            ticker: Stock ticker symbol
            timestamp: Current timestamp
        """
        prices = self.price_buffer[ticker]
        
        if prices:
            # Extract just the price values and timestamps
            price_values = [price for _, price in prices]
            timestamps = [ts for ts, _ in prices]
            
            # Calculate statistics
            avg_price = sum(price_values) / len(price_values)
            min_price = min(price_values)
            max_price = max(price_values)
            start_time = min(timestamps)
            
            logger.info(f"Storing {self.interval_minutes}-minute average for {ticker}: ${avg_price:.2f}")
            
            try:
                # Create a database session without using context manager
                session = next(get_db_session())
                
                # Create a new price average record
                average_record = StockPriceAverage(
                    ticker=ticker,
                    interval_minutes=self.interval_minutes,
                    start_time=start_time,
                    end_time=timestamp,
                    average_price=round(avg_price, 2),
                    min_price=round(min_price, 2),
                    max_price=round(max_price, 2),
                    data_points=len(prices)
                )
                
                # Add and commit
                session.add(average_record)
                session.commit()
                
                # Update the last processed time
                self.last_processed[ticker] = timestamp
                
                # Clear the buffer for the next interval
                self.price_buffer[ticker] = []
                
            except Exception as e:
                logger.error(f"Error storing price average for {ticker}: {str(e)}")
                if 'session' in locals():
                    session.rollback()
            finally:
                if 'session' in locals():
                    session.close()
