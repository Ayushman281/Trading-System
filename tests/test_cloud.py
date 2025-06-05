"""
Tests for the cloud integration module.
"""
import pytest
import pandas as pd
import io
from unittest.mock import patch, MagicMock
from cloud.data_analyzer import analyze_daily_trades
from cloud.lambda_function import analyze_trade_data

def test_analyze_daily_trades():
    """Test trade analysis function."""
    # Create test data
    data = {
        'ticker': ['AAPL', 'AAPL', 'MSFT', 'MSFT'],
        'price': [150.0, 152.0, 250.0, 255.0],
        'quantity': [10, 5, 8, 3]
    }
    df = pd.DataFrame(data)
    
    # Analyze the data
    result = analyze_daily_trades(df)
    
    # Check that the result has the expected columns
    expected_columns = ['ticker', 'total_volume', 'average_price', 
                       'min_price', 'max_price', 'price_volatility']
    assert all(col in result.columns for col in expected_columns)
    
    # Check calculations for AAPL
    aapl_row = result[result['ticker'] == 'AAPL'].iloc[0]
    assert aapl_row['total_volume'] == 15  # 10 + 5
    assert aapl_row['average_price'] == 151.0  # (150 + 152) / 2

def test_analyze_trade_data():
    """Test the Lambda analysis function."""
    # Create test data
    data = {
        'ticker': ['AAPL', 'AAPL', 'MSFT', 'GOOGL'],
        'price': [150.0, 155.0, 250.0, 120.0],
        'quantity': [10, 5, 3, 2]
    }
    df = pd.DataFrame(data)
    
    # Run analysis
    result = analyze_trade_data(df)
    
    # Check results
    assert len(result) == 3  # Three unique tickers
    
    # Check AAPL results
    aapl_result = result[result['ticker'] == 'AAPL'].iloc[0]
    assert aapl_result['total_volume'] == 15
    assert round(aapl_result['average_price'], 2) == 152.5

@patch('cloud.s3_operations.get_s3_client')
def test_s3_operations_mock(mock_get_s3_client):
    """Test S3 operations with mocked AWS client."""
    # Create mock S3 client
    mock_s3 = MagicMock()
    mock_get_s3_client.return_value = mock_s3
    
    # Mock S3 get_object response
    mock_s3.get_object.return_value = {
        'Body': io.BytesIO(b"ticker,price,quantity\nAAPL,150.0,10\nMSFT,250.0,5")
    }
    
    # Import after mocking
    from cloud.s3_operations import get_latest_file
    
    # Call function with mocked client
    result = get_latest_file('test-bucket', 'test-path')
    
    # Assert get_object was called with correct parameters
    mock_s3.get_object.assert_called_once_with(
        Bucket='test-bucket',
        Key='test-path'
    )
    
    # Check result is BytesIO object
    assert isinstance(result, io.BytesIO)
