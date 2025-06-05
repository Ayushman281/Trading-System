"""
Script to run the real-time monitoring system.
"""
import asyncio
import subprocess
import sys
import os
import time
import signal
import logging
from websockets.exceptions import ConnectionClosedError

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realtime.websocket_client import WebSocketClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_realtime")

async def start_client():
    """Start the WebSocket client."""
    client = WebSocketClient()
    await client.connect()

def start_server_process():
    """Start the WebSocket server in a separate process."""
    script_path = os.path.join(os.path.dirname(__file__), "mock_websocket_server.py")
    process = subprocess.Popen([sys.executable, script_path])
    return process

def main():
    """Run the real-time monitoring system."""
    logger.info("Starting real-time monitoring system...")
    
    # Start the server process
    server_process = start_server_process()
    logger.info("WebSocket server started")
    
    # Wait for server to initialize
    time.sleep(2)
    
    try:
        # Start the client in the main event loop
        logger.info("Starting WebSocket client...")
        asyncio.run(start_client())
    except KeyboardInterrupt:
        logger.info("Interrupted by user, shutting down...")
    except ConnectionClosedError:
        logger.error("WebSocket connection closed unexpectedly")
    except Exception as e:
        logger.error(f"Error in real-time system: {e}")
    finally:
        # Terminate the server process
        if server_process:
            server_process.terminate()
            logger.info("WebSocket server terminated")

if __name__ == "__main__":
    main()