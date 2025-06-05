"""
Generate synthetic historical stock price data for trading simulation.
"""
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import random
from utils.logger import get_logger
from utils.helpers import ensure_directory_exists

logger = get_logger(__name__)

class HistoricalDataGenerator:
    def __init__(self, start_date=None, end_date=None, tickers=None):
        """
        Initialize the historical data generator.
        
        Args:
            start_date: Start date for the data (defaults to 2 years ago)
            end_date: End date for the data (defaults to today)
            tickers: List of stock tickers (defaults to popular tech stocks)
        """
        self.start_date = start_date or (datetime.now() - timedelta(days=365*2))
        self.end_date = end_date or datetime.now()
        self.tickers = tickers or ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA"]
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
        ensure_directory_exists(self.data_dir)
        
    def generate_price_series(self, ticker, days, initial_price=None, volatility=None):
        """
        Generate a synthetic price series for a stock.
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to generate
            initial_price: Starting price (if None, a default is chosen)
            volatility: Daily volatility factor (if None, a default is chosen)
            
        Returns:
            DataFrame with date and OHLCV data
        """
        # Set initial price based on ticker if not provided
        if initial_price is None:
            ticker_defaults = {
                "AAPL": 150.0, "MSFT": 300.0, "AMZN": 130.0,
                "GOOGL": 120.0, "META": 250.0, "TSLA": 200.0, "NVDA": 400.0
            }
            initial_price = ticker_defaults.get(ticker, 100.0)
        
        # Set volatility based on ticker if not provided
        if volatility is None:
            ticker_volatility = {
                "AAPL": 0.015, "MSFT": 0.015, "AMZN": 0.02,
                "GOOGL": 0.018, "META": 0.025, "TSLA": 0.035, "NVDA": 0.03
            }
            volatility = ticker_volatility.get(ticker, 0.02)
        
        # Generate dates
        date_range = [self.end_date - timedelta(days=i) for i in range(days)]
        date_range.reverse()  # Oldest to newest
        
        # Generate returns with some autocorrelation for price momentum
        returns = np.random.normal(0, volatility, days)
        
        # Add some trend patterns
        # Bull market (uptrend)
        if random.random() < 0.6:  # 60% chance of uptrend
            trend_days = random.randint(20, 100)
            trend_start = random.randint(0, days - trend_days)
            trend_end = trend_start + trend_days
            returns[trend_start:trend_end] += np.linspace(0, 0.001, trend_days)
        
        # Bear market (downtrend)
        if random.random() < 0.4:  # 40% chance of downtrend
            trend_days = random.randint(15, 60)
            trend_start = random.randint(0, days - trend_days)
            trend_end = trend_start + trend_days
            returns[trend_start:trend_end] -= np.linspace(0, 0.002, trend_days)
        
        # Convert returns to prices
        prices = [initial_price]
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))
        prices = prices[1:]  # Remove the initial seed
        
        # Generate OHLCV data
        data = []
        for i, date in enumerate(date_range):
            price = prices[i]
            
            # Generate open, high, low, close for the day
            daily_volatility = price * volatility * 0.5
            
            open_price = price * (1 + np.random.normal(0, 0.003))
            high_price = max(open_price, price) * (1 + abs(np.random.normal(0, 0.005)))
            low_price = min(open_price, price) * (1 - abs(np.random.normal(0, 0.005)))
            close_price = price
            
            # Generate volume
            base_volume = ticker_defaults.get(ticker, 100) * 100000  # Base volume proportional to price
            volume = int(base_volume * (1 + np.random.normal(0, 0.3)))
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
        
        return pd.DataFrame(data)
    
    def generate_all_data(self):
        """
        Generate historical price data for all tickers.
        
        Returns:
            Dictionary mapping ticker symbols to DataFrames with price data
        """
        days = (self.end_date - self.start_date).days
        all_data = {}
        
        for ticker in self.tickers:
            logger.info(f"Generating historical data for {ticker}")
            all_data[ticker] = self.generate_price_series(ticker, days)
        
        return all_data
    
    def save_to_csv(self, data=None, directory=None):
        """
        Save generated data to CSV files.
        
        Args:
            data: Dictionary of DataFrames (if None, generates new data)
            directory: Directory to save files (if None, uses default)
            
        Returns:
            Dictionary mapping ticker symbols to file paths
        """
        if data is None:
            data = self.generate_all_data()
        
        directory = directory or self.data_dir
        ensure_directory_exists(directory)
        
        file_paths = {}
        for ticker, df in data.items():
            file_path = os.path.join(directory, f"{ticker}_historical.csv")
            df.to_csv(file_path, index=False)
            file_paths[ticker] = file_path
            logger.info(f"Saved historical data for {ticker} to {file_path}")
        
        return file_paths
    
    def generate_merged_file(self, data=None, filename="stock_data.csv"):
        """
        Generate a merged CSV file containing data for multiple stocks.
        
        Args:
            data: Dictionary of DataFrames (if None, generates new data)
            filename: Name of the output file
            
        Returns:
            Path to the merged CSV file
        """
        if data is None:
            data = self.generate_all_data()
        
        # Add ticker column to each DataFrame
        merged_data = []
        for ticker, df in data.items():
            df_copy = df.copy()
            df_copy['ticker'] = ticker
            merged_data.append(df_copy)
        
        # Combine all DataFrames
        merged_df = pd.concat(merged_data)
        
        # Sort by date and ticker
        merged_df = merged_df.sort_values(['date', 'ticker'])
        
        # Save to CSV
        filepath = os.path.join(self.data_dir, filename)
        merged_df.to_csv(filepath, index=False)
        logger.info(f"Saved merged historical data to {filepath}")
        
        return filepath

def generate_sample_data():
    """
    Generate sample historical data for the application.
    
    Returns:
        Path to the generated CSV file
    """
    generator = HistoricalDataGenerator()
    filepath = generator.generate_merged_file(filename="stock_data.csv")
    logger.info(f"Sample data generated at {filepath}")
    return filepath

if __name__ == "__main__":
    generate_sample_data()
