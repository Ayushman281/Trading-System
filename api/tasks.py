"""
Background tasks using Celery.
"""
import logging
import os
from datetime import datetime
from config.settings import Settings

# Load settings
settings = Settings()

# Define a flag to track if Celery is available
CELERY_AVAILABLE = False

# Try to configure Celery but gracefully handle when Redis isn't available
try:
    from celery import Celery
    
    # Check if we should even try to use Redis
    if settings.USE_CELERY and settings.REDIS_URL:
        try:
            celery_app = Celery(
                "moneyy_tasks",
                broker=settings.REDIS_URL,
                backend=settings.REDIS_URL
            )
            
            # Test the connection
            celery_app.broker_connection().ensure_connection(max_retries=1)
            CELERY_AVAILABLE = True
            logging.info("Celery with Redis configured successfully")
        except Exception as e:
            logging.warning(f"Redis connection failed: {e}. Celery tasks will run synchronously.")
            # Create a dummy celery app that won't actually connect
            celery_app = Celery("moneyy_tasks", broker=None)
            celery_app.conf.task_always_eager = True  # Run tasks immediately
    else:
        logging.info("Celery/Redis disabled in configuration. Tasks will run synchronously.")
        celery_app = Celery("moneyy_tasks", broker=None)
        celery_app.conf.task_always_eager = True
except ImportError:
    logging.warning("Celery not installed. Tasks will run synchronously.")
    # Create a dummy class to avoid import errors
    class celery_app:
        @staticmethod
        def task(func):
            return func

# Now define the task
def send_price_alert(ticker, price, change_percent, timestamp):
    """
    Send a price alert notification.
    
    In a real system, this would send an email, SMS, or push notification.
    For this example, we'll just log it.
    
    Args:
        ticker: Stock ticker symbol
        price: Current price
        change_percent: Percentage price change
        timestamp: Timestamp of the alert
    """
    logger = logging.getLogger("price_alerts")
    logger.info(f"[PRICE ALERT] {ticker}: ${price:.2f} ({change_percent:.2f}%) at {timestamp}")
    return {
        "ticker": ticker,
        "price": price,
        "change_percent": change_percent,
        "timestamp": timestamp,
        "status": "sent"
    }

# If Celery is available, wrap the function as a task
if CELERY_AVAILABLE:
    send_price_alert = celery_app.task(send_price_alert)
