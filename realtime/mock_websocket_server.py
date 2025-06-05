"""
Mock WebSocket server that simulates stock price updates.
"""
import asyncio
import json
import random
import websockets
import logging
from datetime import datetime
import time
import os
import sys

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Configure logging for better debug information
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mock_server")

# List of stocks to generate price data for
STOCKS = {
    "AAPL": {"price": 150.0, "volatility": 0.01},
    "MSFT": {"price": 300.0, "volatility": 0.008},
    "AMZN": {"price": 130.0, "volatility": 0.012},
    "GOOGL": {"price": 120.0, "volatility": 0.009},
    "META": {"price": 250.0, "volatility": 0.011},
    "TSLA": {"price": 200.0, "volatility": 0.02},
    "NVDA": {"price": 400.0, "volatility": 0.015},
}

# To simulate price jumps occasionally
JUMP_PROBABILITY = 0.02  # 2% chance of a significant price jump
JUMP_SIZE_RANGE = (0.01, 0.03)  # 1% to 3% jumps

# Store connected clients with their subscriptions
client_subscriptions = {}


async def handle_client(websocket, path):
    """Handle client connection and message processing."""
    # Track client connection with default subscription to all tickers
    client_id = id(websocket)
    client_subscriptions[client_id] = list(STOCKS.keys())
    logger.info(
        f"Client connected. ID: {client_id}, Total clients: {len(client_subscriptions)}"
    )

    try:
        # Process incoming messages for subscriptions
        subscription_task = asyncio.create_task(
            handle_subscriptions(websocket, client_id)
        )

        # Send price updates to this client
        price_task = asyncio.create_task(send_price_updates(websocket, client_id))

        # Wait for either task to complete
        done, pending = await asyncio.wait(
            [subscription_task, price_task], return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel any pending tasks
        for task in pending:
            task.cancel()

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} connection closed")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        # Remove client tracking
        if client_id in client_subscriptions:
            del client_subscriptions[client_id]
        logger.info(
            f"Client disconnected. ID: {client_id}, Total clients: {len(client_subscriptions)}"
        )


async def handle_subscriptions(websocket, client_id):
    """Handle subscription messages from client."""
    async for message in websocket:
        try:
            data = json.loads(message)
            if data.get("type") == "subscribe":
                tickers = data.get("tickers", [])
                if tickers:  # Only update if tickers provided
                    client_subscriptions[client_id] = tickers
                logger.info(f"Client {client_id} subscribed to: {tickers}")
            else:
                logger.debug(f"Received non-subscription message: {data}")

        except json.JSONDecodeError:
            logger.warning(f"Client {client_id} sent invalid JSON: {message}")
        except Exception as e:
            logger.error(f"Error processing subscription from client {client_id}: {str(e)}")


async def send_price_updates(websocket, client_id):
    """Send periodic price updates to client."""
    try:
        while True:
            # Get subscribed tickers for this client
            subscribed_tickers = client_subscriptions.get(
                client_id, list(STOCKS.keys())
            )

            for ticker in subscribed_tickers:
                if ticker not in STOCKS:
                    continue  # Skip invalid tickers

                details = STOCKS[ticker]

                # Determine price movement
                if random.random() < JUMP_PROBABILITY:
                    # Occasional larger jump
                    jump_size = random.uniform(*JUMP_SIZE_RANGE)
                    direction = random.choice([1, -1])
                    price_change = details["price"] * jump_size * direction
                    logger.debug(f"Generating price jump for {ticker}: {jump_size*100:.2f}%")
                else:
                    # Normal small movement
                    price_change = random.normalvariate(0, details["volatility"]) * details[
                        "price"
                    ]

                # Calculate new price
                new_price = max(0.01, details["price"] + price_change)
                STOCKS[ticker]["price"] = new_price

                # Create price update message
                current_time = datetime.now().isoformat()
                price_data = {
                    "type": "price_update",
                    "ticker": ticker,
                    "price": round(new_price, 2),
                    "timestamp": current_time,
                }

                # Convert to JSON and send
                message = json.dumps(price_data)
                logger.debug(f"Sending {ticker} price: ${round(new_price, 2)}")
                await websocket.send(message)

            # Sleep between updates - randomize to make it realistic
            await asyncio.sleep(random.uniform(0.5, 1.5))
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection to client {client_id} closed during price updates")
    except Exception as e:
        logger.error(f"Error sending updates to client {client_id}: {str(e)}")


async def start_server():
    """Start the WebSocket server."""
    host = "localhost"
    port = 8765

    server = await websockets.serve(handle_client, host, port)
    logger.info(f"Starting mock stock server on {host}:{port}")
    await server.wait_closed()


if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
