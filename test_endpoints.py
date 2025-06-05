"""
Test script to verify all API endpoints are working.
"""
import requests
import json
import os
import sys
import time
import uuid
from datetime import datetime, timedelta

# Base URL for API
BASE_URL = "http://localhost:8000"

def test_root_endpoint():
    """Test the root API endpoint."""
    print("\n1. Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✓ Root endpoint working!")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Root endpoint failed! Status code: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing root endpoint: {e}")

def test_add_trade():
    """Test adding a trade through the API."""
    print("\n2. Testing adding a trade...")
    try:
        # Create test trade data
        trade_data = {
            "ticker": "AAPL",
            "price": 150.25,
            "quantity": 10,
            "side": "buy" 
        }
        
        # Send POST request
        response = requests.post(
            f"{BASE_URL}/api/trades", 
            json=trade_data
        )
        
        if response.status_code == 201:
            print("✓ Add trade endpoint working!")
            print(f"  Trade ID: {response.json().get('id')}")
            return response.json().get('id')  # Return ID for further testing
        else:
            print(f"✗ Add trade endpoint failed! Status code: {response.status_code}")
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Error testing add trade endpoint: {e}")
    
    return None

def test_get_trades(trade_id=None):
    """Test retrieving trades."""
    print("\n3. Testing get trades endpoint...")
    try:
        # Get all trades
        response = requests.get(f"{BASE_URL}/api/trades")
        
        if response.status_code == 200:
            trades = response.json()
            print(f"✓ Get trades endpoint working! Found {len(trades)} trades.")
            
            # If we have a specific trade ID, check if it's in the response
            if trade_id:
                trade_found = any(trade.get('id') == trade_id for trade in trades)
                if trade_found:
                    print(f"  ✓ Recently added trade (ID: {trade_id}) was found in the response")
                else:
                    print(f"  ✗ Recently added trade (ID: {trade_id}) was NOT found in the response")
            
            # Test filtering by ticker
            ticker_response = requests.get(f"{BASE_URL}/api/trades?ticker=AAPL")
            if ticker_response.status_code == 200:
                ticker_trades = ticker_response.json()
                print(f"  ✓ Filter by ticker working! Found {len(ticker_trades)} AAPL trades.")
            else:
                print(f"  ✗ Filter by ticker failed! Status code: {ticker_response.status_code}")
            
            # Test filtering by date range
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            date_response = requests.get(
                f"{BASE_URL}/api/trades?start_date={yesterday}&end_date={today}"
            )
            
            if date_response.status_code == 200:
                date_trades = date_response.json()
                print(f"  ✓ Filter by date range working! Found {len(date_trades)} trades.")
            else:
                print(f"  ✗ Filter by date range failed! Status code: {date_response.status_code}")
                
        else:
            print(f"✗ Get trades endpoint failed! Status code: {response.status_code}")
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Error testing get trades endpoint: {e}")

def test_trade_simulation():
    """Test the trading simulation endpoint."""
    print("\n4. Testing trading simulation endpoint...")
    try:
        # Basic simulation
        response = requests.get(f"{BASE_URL}/simulate?ticker=AAPL")
        
        if response.status_code == 200:
            print("✓ Trading simulation endpoint working!")
            print(f"  Report path: {response.json().get('report_path')}")
            
            # Test with parameters
            params_response = requests.get(
                f"{BASE_URL}/simulate?ticker=MSFT&short_window=20&long_window=100"
            )
            
            if params_response.status_code == 200:
                print("  ✓ Trading simulation with parameters working!")
            else:
                print(f"  ✗ Trading simulation with parameters failed! Status: {params_response.status_code}")
                
        else:
            print(f"✗ Trading simulation endpoint failed! Status code: {response.status_code}")
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Error testing trading simulation endpoint: {e}")

def test_api_docs():
    """Test that the API documentation is accessible."""
    print("\n5. Testing API documentation...")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        
        if response.status_code == 200:
            print("✓ API documentation (Swagger UI) is accessible!")
        else:
            print(f"✗ API documentation not accessible! Status code: {response.status_code}")
    except Exception as e:
        print(f"✗ Error accessing API documentation: {e}")

def run_all_tests():
    """Run all endpoint tests."""
    print("===== TESTING MONEYY.AI API ENDPOINTS =====")
    
    # Check if the server is running
    try:
        requests.get(f"{BASE_URL}/")
    except requests.exceptions.ConnectionError:
        print("✗ ERROR: API server is not running!")
        print("  Please start the server with 'python app.py' before running tests.")
        return
    
    # Run all tests
    test_root_endpoint()
    trade_id = test_add_trade()
    test_get_trades(trade_id)
    test_trade_simulation()
    test_api_docs()
    
    print("\n===== ENDPOINT TESTING COMPLETE =====")

if __name__ == "__main__":
    run_all_tests()
