"""
Run all AWS integration tests to verify functionality.
"""
import os
import sys
import json
import logging
import importlib
from datetime import datetime, timedelta
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_all_tests():
    """Run all AWS component tests."""
    print("\n===== AWS Integration Testing =====\n")
    
    # Test 1: Create mock trade data
    print("\n1. Creating mock trade data...")
    from cloud.s3_utils import create_mock_trade_data_for_s3
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    mock_data_today = create_mock_trade_data_for_s3(today)
    mock_data_yesterday = create_mock_trade_data_for_s3(yesterday)
    
    print(f"  ✓ Created mock data for {today} with {len(mock_data_today)} records")
    print(f"  ✓ Created mock data for {yesterday} with {len(mock_data_yesterday)} records")
    
    # Test 2: Run Lambda function locally
    print("\n2. Testing Lambda function with mock S3...")
    try:
        from cloud.test_lambda_locally import test_lambda_with_mock_s3
        test_lambda_with_mock_s3()
        print("  ✓ Lambda function test succeeded")
    except Exception as e:
        print(f"  ✗ Lambda function test failed: {e}")
    
    # Test 3: Test API endpoint if app is running
    print("\n3. Testing FastAPI endpoint (requires app to be running)...")
    try:
        import requests
        response = requests.get(f"http://localhost:8000/api/analyze-trades/{today}")
        
        if response.status_code == 200:
            print(f"  ✓ API endpoint test succeeded")
            print(f"  Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"  ✗ API endpoint test failed: {response.status_code}")
            print(f"  Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("  ✗ API endpoint test failed: Could not connect to API server")
        print("    Make sure the API server is running (python app.py)")
    except Exception as e:
        print(f"  ✗ API endpoint test failed: {e}")
    
    print("\n===== AWS Integration Testing Complete =====")

if __name__ == "__main__":
    run_all_tests()
