"""
Client for connecting to the WebSocket server and processing price updates.
"""
import asyncio
import json
import websockets
import logging
from datetime import datetime
import os
import sys

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from utils.logger import get_logger
from realtime.price_monitor import PriceMonitor
from realtime.data_processor import DataProcessor

logger = get_logger("websocket_client")

class WebSocketClient:
    """
    Client for connecting to the WebSocket server and processing price updates.
    """
    def __init__(self, uri="ws://localhost:8765", reconnect_interval=5):
        """
        Initialize the WebSocket client.
        
        Args:
            uri: WebSocket server URI
            reconnect_interval: Seconds to wait before reconnection attempts
        """
        self.uri = uri
        self.reconnect_interval = reconnect_interval
        self.connected = False
        self.price_monitor = PriceMonitor(threshold_percent=2.0)
        self.data_processor = DataProcessor()
        
        # Subscribe to specific tickers
        self.subscriptions = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA"]
    
    async def connect(self):
        """Connect to the WebSocket server and handle messages."""
        while True:
            try:
                async with websockets.connect(self.uri) as websocket:
                    self.connected = True
                    logger.info(f"Connected to {self.uri}")
                    
                    # Send subscription message
                    if self.subscriptions:
                        subscription_msg = {
                            "type": "subscribe",
                            "tickers": self.subscriptions
                        }
                        await websocket.send(json.dumps(subscription_msg))
                    
                    # Process incoming messages
                    await self._process_messages(websocket)
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                self.connected = False
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.connected = False
            
            # Wait before reconnecting
            logger.info(f"Attempting to reconnect in {self.reconnect_interval} seconds...")
            await asyncio.sleep(self.reconnect_interval)
    
    async def _process_messages(self, websocket):
        """
        Process incoming WebSocket messages.
        
        Args:
            websocket: WebSocket connection
        """
        async for message in websocket:
            try:
                data = json.loads(message)
                
                # Check message type
                if data.get("type") == "price_update":
                    ticker = data.get("ticker")
                    price = data.get("price")
                    timestamp_str = data.get("timestamp")
                    
                    # Skip invalid messages
                    if ticker is None or price is None or timestamp_str is None:
                        logger.warning("Received invalid price update, missing required fields")
                        continue
                    
                    # Parse timestamp
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                    except ValueError:
                        logger.warning(f"Invalid timestamp format: {timestamp_str}")
                        timestamp = datetime.now()
                    
                    # Log price update
                    logger.debug(f"Price update: {ticker} ${price:.2f}")
                    
                    # Process price update
                    await self.price_monitor.process_price_update(ticker, price, timestamp)
                    await self.data_processor.process_price_update(ticker, price, timestamp)
                    
                elif data.get("type") == "error":
                    logger.error(f"Server error: {data.get('message')}")
                else:
                    logger.debug(f"Received message: {data}")
                    
            except json.JSONDecodeError:
                logger.error(f"Failed to parse message: {message[:100]}...")
            except Exception as e:
                logger.error(f"Error processing message: {e}")

async def main():
    """Main function to run the WebSocket client."""
    client = WebSocketClient()
    try:
        await client.connect()
    except KeyboardInterrupt:
        logger.info("Client stopped by user")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Client stopped by user")
