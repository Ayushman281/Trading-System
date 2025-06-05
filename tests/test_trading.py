"""
Tests for the trading module.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from trading.strategy import MovingAverageCrossoverStrategy
from trading.backtester import Backtester

@pytest.fixture
def sample_price_data():
    """Create sample price data for testing."""
    # Create date range
    dates = [datetime.now() - timedelta(days=i) for i in range(300, 0, -1)]
    
    # Create price series with a known pattern for testing
    prices = [100.0]
    for i in range(1, 300):
        # Add some randomness but with a general trend
        if i < 100:
            # Downward trend
            change = np.random.normal(-0.1, 0.5)
        elif i < 200:
            # Upward trend
            change = np.random.normal(0.2, 0.5)
        else:
            # Sideways with slight upward bias
            change = np.random.normal(0.05, 0.5)
        
        prices.append(max(0.1, prices[-1] * (1 + change/100)))
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'close': prices
    })
    
    df.set_index('date', inplace=True)
    return df

def test_moving_average_strategy(sample_price_data):
    """Test Moving Average Crossover strategy."""
    # Create strategy with shorter windows for testing
    strategy = MovingAverageCrossoverStrategy(short_window=10, long_window=30)
    
    # Generate signals
    signals = strategy.generate_signals(sample_price_data)
    
    # Check that signals DataFrame has the expected columns
    assert 'MA_10' in signals.columns
    assert 'MA_30' in signals.columns
    assert 'signal' in signals.columns
    assert 'position' in signals.columns
    
    # Check that there are some buy/sell signals
    assert signals['position'].abs().sum() > 0

def test_backtester(sample_price_data):
    """Test backtesting functionality."""
    # Create strategy and backtester
    strategy = MovingAverageCrossoverStrategy(short_window=10, long_window=30)
    backtester = Backtester(strategy, sample_price_data)
    
    # Run backtest
    results = backtester.run()
    
    # Check that results contain expected keys
    assert 'portfolio' in results
    assert 'metrics' in results
    
    # Check metrics
    metrics = results['metrics']
    assert 'initial_value' in metrics
    assert 'final_value' in metrics
    assert 'total_return' in metrics
    assert 'sharpe_ratio' in metrics
    
    # Initial value should match what we set
    assert metrics['initial_value'] == 100000.0
    
    # Check portfolio DataFrame
    portfolio = results['portfolio']
    assert 'holdings' in portfolio.columns
    assert 'cash' in portfolio.columns
    assert 'total' in portfolio.columns
    assert 'returns' in portfolio.columns
