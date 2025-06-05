"""
Moving Average Crossover trading strategy implementation.
"""
import pandas as pd
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)

class MovingAverageCrossoverStrategy:
    def __init__(self, short_window=50, long_window=200):
        """
        Initialize the Moving Average Crossover strategy.
        
        Args:
            short_window: Number of periods for short-term moving average
            long_window: Number of periods for long-term moving average
        """
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self, df):
        """
        Generate buy/sell signals based on moving average crossover.
        
        Args:
            df: DataFrame with stock price data (must include 'close' column)
            
        Returns:
            DataFrame with added signal columns
        """
        # Make a copy to avoid modifying the original
        signals = df.copy()
        
        # Check if 'close' column exists
        if 'close' not in signals.columns:
            if 'price' in signals.columns:
                signals['close'] = signals['price']
            else:
                logger.error("No 'close' or 'price' column found in data")
                return signals
        
        # Create short and long moving averages
        signals[f'MA_{self.short_window}'] = signals['close'].rolling(window=self.short_window).mean()
        signals[f'MA_{self.long_window}'] = signals['close'].rolling(window=self.long_window).mean()
        
        # Create signals (1: buy, -1: sell, 0: hold)
        signals['signal'] = 0.0
        
        # Generate buy/sell signals
        signals['signal'] = np.where(
            signals[f'MA_{self.short_window}'] > signals[f'MA_{self.long_window}'], 1.0, 0.0
        )
        
        # Generate trading orders: detect crossovers
        signals['position'] = signals['signal'].diff()
        
        # Drop NaN values resulting from MA calculation
        signals.dropna(inplace=True)
        
        return signals
    
    def backtest(self, df, initial_capital=100000.0):
        """
        Backtest the strategy on historical data.
        
        Args:
            df: DataFrame with price data
            initial_capital: Starting capital for the simulation
            
        Returns:
            DataFrame with portfolio performance metrics
        """
        # Generate trading signals
        signals = self.generate_signals(df)
        
        # Create a new DataFrame for portfolio metrics
        portfolio = signals.copy()
        
        # Add holdings and cash columns
        portfolio['holdings'] = 0.0
        portfolio['cash'] = initial_capital
        portfolio['total'] = initial_capital
        portfolio['returns'] = 0.0
        
        # Iterate through each day
        position = 0
        for i in range(len(portfolio)):
            # Update position based on signal
            if portfolio['position'].iloc[i] == 1.0:  # Buy signal
                # Calculate how many shares to buy with all available cash
                price = portfolio['close'].iloc[i]
                shares_to_buy = portfolio['cash'].iloc[i] // price
                cost = shares_to_buy * price
                
                # Update holdings and cash
                position += shares_to_buy
                portfolio.loc[portfolio.index[i], 'holdings'] = position * price
                portfolio.loc[portfolio.index[i], 'cash'] = portfolio['cash'].iloc[i] - cost
                
            elif portfolio['position'].iloc[i] == -1.0:  # Sell signal
                # Sell all shares
                price = portfolio['close'].iloc[i]
                sale_proceeds = position * price
                
                # Update holdings and cash
                position = 0
                portfolio.loc[portfolio.index[i], 'holdings'] = 0
                portfolio.loc[portfolio.index[i], 'cash'] = portfolio['cash'].iloc[i] + sale_proceeds
            
            else:  # Hold position
                # Update holdings value
                price = portfolio['close'].iloc[i]
                portfolio.loc[portfolio.index[i], 'holdings'] = position * price
                portfolio.loc[portfolio.index[i], 'cash'] = portfolio['cash'].iloc[i-1] if i > 0 else initial_capital
            
            # Calculate total value and returns
            portfolio.loc[portfolio.index[i], 'total'] = portfolio['holdings'].iloc[i] + portfolio['cash'].iloc[i]
            
            if i > 0:
                portfolio.loc[portfolio.index[i], 'returns'] = (
                    portfolio['total'].iloc[i] / portfolio['total'].iloc[i-1] - 1
                )
        
        # Calculate cumulative returns
        portfolio['cumulative_returns'] = (1 + portfolio['returns']).cumprod() - 1
        
        return portfolio
