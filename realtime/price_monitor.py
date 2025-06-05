"""
Monitor stock price changes and detect significant movements.
"""
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from utils.logger import get_logger
from api.tasks import send_price_alert

logger = get_logger(__name__)

class PriceMonitor:
    def __init__(self, threshold_percent=2.0, window_seconds=60):
        """
        Initialize the price monitor.
        
        Args:
            threshold_percent: Price change percentage to trigger an alert
            window_seconds: Time window to consider for price changes (in seconds)
        """
        self.threshold_percent = threshold_percent
        self.window_seconds = window_seconds
        # Store price history for each ticker
        self.price_history = defaultdict(list)
        # Last average calculation time
        self.last_average_calc = datetime.now()
        # Average calculation interval (5 minutes)
        self.avg_calc_interval = timedelta(minutes=5)
    
    async def process_price_update(self, ticker, price, timestamp):
        """
        Process a price update and check for significant changes.
        
        Args:
            ticker: Stock ticker symbol
            price: Updated price
            timestamp: Time of the update
        """
        # Add to price history
        self.price_history[ticker].append((timestamp, price))
        
        # Clean up old data
        self._clean_price_history(ticker, timestamp)
        
        # Check for significant price change
        await self._check_price_change(ticker, price, timestamp)
        
        # Calculate average price if needed
        await self._calculate_average_prices(timestamp)
        
    async def _check_price_change(self, ticker, current_price, current_time):
        """
        Check if the price change exceeds the threshold.
        
        Args:
            ticker: Stock ticker symbol
            current_price: Current price
            current_time: Current timestamp
        """
        history = self.price_history[ticker]
        if not history or len(history) < 2:
            return
        
        # Find price from one minute ago
        cutoff_time = current_time - timedelta(seconds=self.window_seconds)
        old_prices = [(t, p) for (t, p) in history if t <= cutoff_time]
        
        if not old_prices:
            return
            
        # Get the most recent price before the cutoff
        old_time, old_price = max(old_prices, key=lambda x: x[0])
        
        # Calculate percentage change
        if old_price > 0:  # Avoid division by zero
            percent_change = ((current_price - old_price) / old_price) * 100
            
            # Check against threshold
            if abs(percent_change) >= self.threshold_percent:
                logger.info(f"Significant price movement detected for {ticker}: {percent_change:.2f}%")
                # Send alert as a background task
                send_price_alert.delay(ticker, current_price, percent_change)
    
    async def _calculate_average_prices(self, current_time):
        """
        Calculate average prices for all tickers every 5 minutes.
        
        Args:
            current_time: Current timestamp
        """
        # Check if it's time to calculate averages
        if current_time - self.last_average_calc < self.avg_calc_interval:
            return
            
        self.last_average_calc = current_time
        logger.debug("Calculating 5-minute average prices")
        
        # Calculate average for each ticker
        for ticker, history in self.price_history.items():
            # Get data from the last 5 minutes
            cutoff_time = current_time - self.avg_calc_interval
            recent_prices = [p for (t, p) in history if t >= cutoff_time]
            
            if recent_prices:
                avg_price = sum(recent_prices) / len(recent_prices)
                logger.info(f"5-minute average price for {ticker}: ${avg_price:.2f}")
                
                # TODO: Save this data to the database
                # In a real implementation, this would store the average in the database
                
    def _clean_price_history(self, ticker, current_time):
        """
        Remove price data older than the monitoring window.
        
        Args:
            ticker: Stock ticker symbol
            current_time: Current timestamp
        """
        # Keep only data within twice the window size (for calculating averages)
        retention_period = timedelta(seconds=self.window_seconds * 2)
        cutoff_time = current_time - retention_period
        
        self.price_history[ticker] = [
            (t, p) for (t, p) in self.price_history[ticker] 
            if t >= cutoff_time
        ]
