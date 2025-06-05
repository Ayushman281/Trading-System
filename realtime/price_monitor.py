"""
Monitor stock prices for significant changes.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import os
import sys

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from utils.logger import get_logger
from api.models import Trade, TradeSide
from config.database import SessionLocal

# Try to import the task, improve error handling
try:
    from api.tasks import send_price_alert, CELERY_AVAILABLE
except ImportError:
    send_price_alert = None
    CELERY_AVAILABLE = False
    logging.warning("Tasks module not available. Price alerts will be logged only.")

logger = get_logger(__name__)

class PriceMonitor:
    """
    Monitor stock prices for significant changes.
    """
    def __init__(self, threshold_percent=2.0, window_seconds=60):
        """
        Initialize the price monitor.
        
        Args:
            threshold_percent: Percentage change that triggers an alert
            window_seconds: Time window in seconds to consider for price changes
        """
        self.threshold_percent = threshold_percent
        self.window_seconds = window_seconds
        self.price_history = defaultdict(list)  # {ticker: [(timestamp, price), ...]}
        self.last_average_calc = {}  # For calculation timing
        self.last_alert_time = {}  # To prevent alert spam
        logger.info(f"Price monitor initialized with {threshold_percent}% threshold over {window_seconds} seconds")
    
    async def process_price_update(self, ticker, price, timestamp):
        """
        Process a price update and check for significant changes.
        
        Args:
            ticker: Stock ticker symbol
            price: Current price
            timestamp: Timestamp of the update
        """
        # Validate inputs
        if ticker is None or not isinstance(ticker, str):
            logger.warning(f"Invalid ticker: {ticker}")
            return
        
        if price is None or not isinstance(price, (int, float)) or price <= 0:
            logger.warning(f"Invalid price for {ticker}: {price}")
            return
            
        # Add the new price to history
        self.price_history[ticker].append((timestamp, price))
        
        # Check for significant price changes
        await self._check_price_change(ticker, price, timestamp)
        
        # Clean up old price data
        self._clean_price_history(ticker, timestamp)
    
    async def _check_price_change(self, ticker, current_price, current_time):
        """
        Check if there's a significant price change within the time window.
        
        Args:
            ticker: Stock ticker symbol
            current_price: Current price
            current_time: Current timestamp
        """
        # Get price history for the ticker within the time window
        cutoff_time = current_time - timedelta(seconds=self.window_seconds)
        window_prices = [(t, p) for t, p in self.price_history[ticker] 
                       if t >= cutoff_time]
        
        # Need at least 2 prices to calculate change
        if len(window_prices) < 2:
            return
        
        # Find the earliest price in the window
        earliest_time, earliest_price = min(window_prices, key=lambda x: x[0])
        
        # Calculate percentage change
        price_change_percent = (current_price - earliest_price) / earliest_price * 100
        
        # Check if change exceeds threshold
        if abs(price_change_percent) >= self.threshold_percent:
            await self._trigger_price_alert(ticker, earliest_price, current_price, 
                              earliest_time, current_time, price_change_percent)
    
    async def _trigger_price_alert(self, ticker, start_price, current_price, 
                    start_time, current_time, change_percent):
        """
        Trigger an alert for a significant price change.
        
        Args:
            ticker: Stock ticker symbol
            start_price: Price at start of window
            current_price: Current price
            start_time: Timestamp at start of window
            current_time: Current timestamp
            change_percent: Percentage price change
        """
        # Skip if ticker is None
        if ticker is None:
            logger.warning("Price alert triggered with None ticker, skipping")
            return
        
        time_diff = (current_time - start_time).total_seconds()
        logger.warning(f"PRICE ALERT: {ticker} {'increased' if change_percent > 0 else 'decreased'} by {abs(change_percent):.2f}% in {time_diff:.1f} seconds")
        logger.warning(f"{ticker}: ${start_price:.2f} -> ${current_price:.2f}")
        
        # Send alert via Celery if available
        if CELERY_AVAILABLE and send_price_alert:
            try:
                # Don't use .delay() which requires Redis, call directly
                send_price_alert(
                    ticker, 
                    current_price, 
                    change_percent, 
                    current_time.isoformat()
                )
            except Exception as e:
                logger.error(f"Failed to send price alert task: {e}")
        
        # Store alert in database regardless
        try:
            db = SessionLocal()
            # Record a simulated trade based on the alert (for demonstration)
            alert_trade = Trade(
                ticker=ticker,
                price=current_price,
                quantity=100,  # Example quantity
                side=TradeSide.BUY if change_percent > 0 else TradeSide.SELL,  # Buy on price increase, sell on decrease
                timestamp=current_time
            )
            db.add(alert_trade)
            db.commit()
            logger.info(f"Recorded alert trade for {ticker}")
        except Exception as e:
            logger.error(f"Failed to record alert trade: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    def _clean_price_history(self, ticker, current_time):
        """
        Remove price data older than the time window.
        
        Args:
            ticker: Stock ticker symbol
            current_time: Current timestamp
        """
        # Define cutoff time (double the window to keep some history)
        cutoff_time = current_time - timedelta(seconds=self.window_seconds * 2)
        
        # Remove old entries
        self.price_history[ticker] = [
            (t, p) for t, p in self.price_history[ticker] 
            if t >= cutoff_time
        ]
    
    def calculate_averages(self, current_time, interval_minutes=5):
        """
        Check if it's time to calculate averages for each ticker.
        
        Args:
            current_time: Current timestamp
            interval_minutes: Interval for average calculations in minutes
            
        Returns:
            Dictionary of tickers with their average prices if calculated
        """
        results = {}
        
        for ticker, history in self.price_history.items():
            # Check if we should calculate for this ticker
            last_calc_time = self.last_average_calc.get(ticker)
            if (not last_calc_time or 
                    current_time - last_calc_time >= timedelta(minutes=interval_minutes)):
                
                # Define interval
                interval_start = current_time - timedelta(minutes=interval_minutes)
                
                # Get prices in interval
                interval_prices = [p for t, p in history if t >= interval_start]
                
                # Calculate average if we have data
                if interval_prices:
                    avg_price = sum(interval_prices) / len(interval_prices)
                    results[ticker] = avg_price
                    self.last_average_calc[ticker] = current_time
                    
        return results
