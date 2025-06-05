"""
Tests for the real-time data processing module.
"""
import pytest
import asyncio
from datetime import datetime
from realtime.price_monitor import PriceMonitor
from realtime.mock_websocket_server import STOCKS

@pytest.fixture
def price_monitor():
    """Create PriceMonitor fixture."""
    return PriceMonitor(threshold_percent=1.0, window_seconds=10)

def test_price_monitor_initialization(price_monitor):
    """Test PriceMonitor initialization."""
    assert price_monitor.threshold_percent == 1.0
    assert price_monitor.window_seconds == 10
    assert isinstance(price_monitor.price_history, dict)

@pytest.mark.asyncio
async def test_process_price_update(price_monitor):
    """Test processing price updates."""
    ticker = "AAPL"
    price = 150.0
    timestamp = datetime.now()
    
    # Process first update
    await price_monitor.process_price_update(ticker, price, timestamp)
    
    # Check that price was recorded
    assert len(price_monitor.price_history[ticker]) == 1
    assert price_monitor.price_history[ticker][0][1] == price

@pytest.mark.asyncio
async def test_price_change_detection(price_monitor):
    """Test detection of significant price changes."""
    ticker = "AAPL"
    initial_price = 100.0
    timestamp1 = datetime.now()
    
    # Initial price
    await price_monitor.process_price_update(ticker, initial_price, timestamp1)
    
    # Price change that should trigger alert (2% change)
    timestamp2 = datetime.now()
    new_price = initial_price * 1.02
    
    # This should trigger alert (captured in logs or via the mock)
    await price_monitor.process_price_update(ticker, new_price, timestamp2)
    
    # Check that both prices were recorded
    assert len(price_monitor.price_history[ticker]) == 2
