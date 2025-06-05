"""
Test script to verify the real-time data processing components.
"""
import asyncio
import json
import websockets
import time
import sys
import requests
from datetime import datetime

async def test_websocket_server():
    """Test connecting to the WebSocket server and receiving messages."""
    print("\n1. Testing WebSocket server connection...")
    uri = "ws://localhost:8765"
    try:
        async with websockets.connect(uri, timeout=5) as websocket:
            print("✓ Connected to WebSocket server")
            
            # Wait for some messages
            print("  Waiting for price updates (5 seconds)...")
            
            # Get first 3 messages
            messages_received = 0
            start_time = time.time()
            
            while time.time() - start_time < 5 and messages_received < 3:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    try:
                        data = json.loads(message)
                        messages_received += 1
                        
                        # Check if the message has the required fields
                        if all(key in data for key in ['ticker', 'price', 'timestamp']):
                            print(f"  ✓ Received update: {data['ticker']} ${data['price']}")
                        else:
                            print(f"  ✗ Received malformed message: {data}")
                    except json.JSONDecodeError:
                        print(f"  ✗ Received invalid JSON: {message[:50]}...")
                except asyncio.TimeoutError:
                    continue
            
            if messages_received > 0:
                print(f"✓ Successfully received {messages_received} price updates")
                return True
            else:
                print("✗ No price updates received within timeout period")
                return False
                
    except (websockets.exceptions.WebSocketException, ConnectionRefusedError) as e:
        print(f"✗ WebSocket connection failed: {e}")
        print("  Make sure the WebSocket server is running (python -m realtime.mock_websocket_server)")
        return False

async def simulate_price_spike():
    """Connect to WebSocket server and wait for a price spike alert."""
    print("\n2. Waiting for price spike detection (up to 30 seconds)...")
    uri = "ws://localhost:8765"
    spike_detected = False
    
    try:
        start_time = time.time()
        # Let's watch for a maximum of 30 seconds for a spike
        while time.time() - start_time < 30 and not spike_detected:
            # Check the PostgreSQL database for any trades created due to alerts
            try:
                response = requests.get("http://localhost:8000/api/trades")
                if response.status_code == 200:
                    trades = response.json()
                    # Filter trades created in the last 30 seconds
                    recent_trades = [
                        t for t in trades 
                        if datetime.fromisoformat(t['timestamp'].replace('Z', '')) > 
                           datetime.fromisoformat(datetime.now().isoformat()[:-3])
                    ]
                    if recent_trades:
                        print(f"✓ Price spike detected! New trade recorded: {recent_trades[0]['ticker']} at ${recent_trades[0]['price']}")
                        spike_detected = True
                        break
            except Exception as e:
                print(f"  API check error: {e}")
            
            # Sleep for a bit before checking again
            await asyncio.sleep(3)
        
        if not spike_detected:
            print("  No price spike detected within the timeout period.")
            print("  This is normal as spikes are randomly generated.")
    
    except Exception as e:
        print(f"✗ Error monitoring for price spikes: {e}")
    
    return spike_detected

async def test_price_averages():
    """Test the 5-minute price average calculations."""
    print("\n3. Testing price averages calculation...")
    
    # Give some time for averages to be calculated (if the system has been running)
    print("  Checking if price averages are being stored...")
    
    try:
        response = requests.get("http://localhost:8000/api/price-averages")
        if response.status_code == 200:
            averages = response.json()
            if averages:
                print(f"✓ Found {len(averages)} price average records!")
                print(f"  Most recent: {averages[0]['ticker']} avg: ${averages[0]['average_price']} ({averages[0]['interval_minutes']} min)")
                return True
            else:
                print("  No price averages found yet.")
                print("  This is normal if the real-time system hasn't been running for at least 5 minutes.")
                return False
        else:
            print(f"✗ Failed to retrieve price averages: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error checking price averages: {e}")
        return False

async def main():
    """Run all real-time tests."""
    print("===== TESTING REAL-TIME COMPONENTS =====")
    
    # Test the WebSocket API endpoint that starts monitoring
    print("\nTesting start-monitoring endpoint...")
    try:
        response = requests.post("http://localhost:8000/api/start-monitoring")
        if response.status_code == 200:
            print("✓ Successfully called start-monitoring endpoint")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ start-monitoring endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Error calling start-monitoring endpoint: {e}")
    
    # Give the monitoring system time to start
    print("\nWaiting 3 seconds for monitoring system to start...")
    await asyncio.sleep(3)
    
    # Test the WebSocket server
    await test_websocket_server()
    
    # Test price spike detection
    await simulate_price_spike()
    
    # Test price averages
    await test_price_averages()
    
    print("\n===== REAL-TIME TESTING COMPLETE =====")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTesting interrupted by user.")
        sys.exit(0)
