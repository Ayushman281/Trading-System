"""
Celery tasks for background processing.
"""
from celery import Celery
from config.settings import Settings

settings = Settings()
celery_app = Celery(
    "tasks",
    broker=settings.redis_url,
    backend=settings.redis_url
)

@celery_app.task
def send_price_alert(ticker, price, change_percent):
    """
    Send price alert notification when a stock price changes significantly.
    
    Args:
        ticker: Stock ticker symbol
        price: Current price
        change_percent: Percentage change that triggered the alert
    """
    # In a real system, this could send an email, SMS, or push notification
    print(f"ALERT: {ticker} price changed by {change_percent:.2f}% to ${price:.2f}")
    
    # Here you would integrate with a notification service
    # For example:
    # notification_service.send_notification(
    #     user_id=user_id,
    #     message=f"{ticker} price changed by {change_percent:.2f}% to ${price:.2f}",
    #     notification_type="price_alert"
    # )
    
    return True
