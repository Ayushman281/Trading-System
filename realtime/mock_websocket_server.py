"""
Mock WebSocket server for simulating stock market data feed.
"""
import asyncio
import json
import random
import websockets
from datetime import datetime

# Stock tickers with initial prices
STOCKS = {
    "AAPL": 175.50,
    "MSFT": 320.75,
    "AMZN": 130.25,
    "GOOGL": 125.80,
    "META": 280.15,
    "TSLA": 180.40,
    "NVDA": 420.60,
    "JPM": 150.30,
    "V": 240.50,
    "PG": 160.20,
}

class MockStockServer:
    def __init__(self, host="localhost", port=8765):
        """
        Initialize the mock stock server.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
        """
        self.host = host
        self.port = port
        self.clients = set()
        self.subscriptions = {}  # client -> list of tickers
    
    async def register(self, websocket):
        """Register a new client."""
        self.clients.add(websocket)
        self.subscriptions[websocket] = []
        print(f"New client connected. Total clients: {len(self.clients)}")
    
    async def unregister(self, websocket):
        """Unregister a client."""
        self.clients.remove(websocket)
        del self.subscriptions[websocket]
        print(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def handle_message(self, websocket, message):
        """Handle incoming messages from clients."""
        data = json.loads(message)
        message_type = data.get("type")
        
        if message_type == "subscribe":
            symbols = data.get("symbols", [])
            self.subscriptions[websocket] = symbols
            print(f"Client subscribed to: {symbols}")
            
            # Send confirmation
            await websocket.send(json.dumps({
                "type": "subscription_result",
                "status": "success",
                "symbols": symbols
            }))
    
    async def generate_prices(self):
        """Generate random price updates for stocks."""
        while True:
            # For each stock, randomly decide whether to update its price
            for ticker, price in STOCKS.items():
                # 20% chance of updating each stock on each iteration
                if random.random() < 0.2:
                    # Generate a small random price change (-2% to +2%)
                    change_percent = random.uniform(-2.0, 2.0)
                    new_price = price * (1 + change_percent / 100)
                    STOCKS[ticker] = round(new_price, 2)
                    
                    # Create price update message
                    message = {
                        "type": "price_update",
                        "symbol": ticker,
                        "price": STOCKS[ticker],
                        "change_percent": change_percent,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Send to subscribed clients
                    for client, symbols in self.subscriptions.items():
                        if not symbols or ticker in symbols:
                            try:
                                await client.send(json.dumps(message))
                            except websockets.ConnectionClosed:
                                pass  # Client will be removed on next connection attempt
            
            # Wait before next update (100-500ms)
            await asyncio.sleep(random.uniform(0.1, 0.5))
    
    async def handle_client(self, websocket, path):
        """Handle a client connection."""
        await self.register(websocket)
        try:
            # Start price generation if this is the first client
            if len(self.clients) == 1:
                asyncio.create_task(self.generate_prices())
            
            # Handle messages from this client
            async for message in websocket:
                await self.handle_message(websocket, message)
        finally:
            await self.unregister(websocket)
    
    async def start(self):
        """Start the WebSocket server."""
        print(f"Starting mock stock server on {self.host}:{self.port}")
        server = await websockets.serve(
            self.handle_client, 
            self.host, 
            self.port
        )
        await server.wait_closed()

def run_server():
    """Run the mock WebSocket server."""
    server = MockStockServer()
    asyncio.run(server.start())

if __name__ == "__main__":
    run_server()
