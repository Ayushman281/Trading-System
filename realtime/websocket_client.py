"""
WebSocket client for connecting to the mock stock data feed.
"""
import asyncio
import json
import websockets
from datetime import datetime
from .price_monitor import PriceMonitor
from utils.logger import get_logger

logger = get_logger(__name__)

class WebSocketClient:
    def __init__(self, uri="ws://localhost:8765"):
        """
        Initialize the WebSocket client.
        
        Args:
            uri: WebSocket server URI
        """
        self.uri = uri
        self.price_monitor = PriceMonitor()
        self.connected = False
        
    async def connect(self):
        """
        Connect to the WebSocket server and process incoming messages.
        """
        try:
            async with websockets.connect(self.uri) as websocket:
                logger.info(f"Connected to {self.uri}")
                self.connected = True
                
                # Send subscription message
                await websocket.send(json.dumps({
                    "type": "subscribe",
                    "symbols": ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]
                }))
                
                # Process incoming messages
                while True:
                    message = await websocket.recv()
                    await self.process_message(json.loads(message))
                    
        except websockets.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.connected = False
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.connected = False
        
    async def process_message(self, message):
        """
        Process incoming WebSocket messages.
        
        Args:
            message: JSON message from the WebSocket server
        """
        if message.get("type") == "price_update":
            # Extract price data
            ticker = message.get("symbol")
            price = message.get("price")
            timestamp = datetime.fromisoformat(message.get("timestamp"))
            
            # Process price update
            await self.price_monitor.process_price_update(ticker, price, timestamp)
            
        elif message.get("type") == "error":
            logger.error(f"Error from WebSocket server: {message.get('message')}")
            
        else:
            logger.debug(f"Unhandled message type: {message.get('type')}")
    
    def start(self):
        """
        Start the WebSocket client in a separate thread.
        """
        asyncio.run(self.connect())
