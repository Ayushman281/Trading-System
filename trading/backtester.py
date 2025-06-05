"""
Backtesting engine for trading strategies.
"""
import pandas as pd
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)

class Backtester:
    def __init__(self, strategy, data, initial_capital=100000.0):
        """
        Initialize the backtester.
        
        Args:
            strategy: Trading strategy object
            data: DataFrame with historical price data
            initial_capital: Starting capital for the simulation
        """
        self.strategy = strategy
        self.data = data
        self.initial_capital = initial_capital
        self.results = None
        
    def run(self):
        """
        Run the backtest.
        
        Returns:
            Dictionary with backtest results
        """
        logger.info("Starting backtest...")
        
        # Generate signals using the strategy
        signals = self.strategy.generate_signals(self.data)
        
        # Initialize portfolio metrics
        portfolio = self._initialize_portfolio(signals)
        
        # Simulate trading based on signals
        portfolio = self._simulate_trades(portfolio)
        
        # Calculate performance metrics
        metrics = self._calculate_metrics(portfolio)
        
        self.results = {
            'portfolio': portfolio,
            'metrics': metrics
        }
        
        logger.info(f"Backtest completed. Final portfolio value: ${metrics['final_value']:.2f}")
        
        return self.results
        
    def _initialize_portfolio(self, signals):
        """Initialize portfolio metrics DataFrame."""
        portfolio = signals.copy()
        portfolio['holdings'] = 0.0
        portfolio['cash'] = self.initial_capital
        portfolio['total'] = self.initial_capital
        portfolio['returns'] = 0.0
        return portfolio
        
    def _simulate_trades(self, portfolio):
        """Simulate trades based on signals."""
        position = 0  # Number of shares held
        
        for i in range(len(portfolio)):
            price = portfolio['close'].iloc[i]
            
            # Buy signal (crossover happened)
            if portfolio['position'].iloc[i] == 1.0:
                # Calculate number of shares to buy with all available cash
                shares_to_buy = int(portfolio['cash'].iloc[i-1] / price) if i > 0 else int(self.initial_capital / price)
                cost = shares_to_buy * price
                
                position += shares_to_buy
                portfolio.loc[portfolio.index[i], 'holdings'] = position * price
                portfolio.loc[portfolio.index[i], 'cash'] = portfolio['cash'].iloc[i-1] - cost if i > 0 else self.initial_capital - cost
                
                logger.debug(f"BUY: {shares_to_buy} shares at ${price:.2f}")
                
            # Sell signal (crossover happened)
            elif portfolio['position'].iloc[i] == -1.0 and position > 0:
                # Sell all shares
                proceeds = position * price
                
                logger.debug(f"SELL: {position} shares at ${price:.2f}")
                
                position = 0
                portfolio.loc[portfolio.index[i], 'holdings'] = 0
                portfolio.loc[portfolio.index[i], 'cash'] = portfolio['cash'].iloc[i-1] + proceeds if i > 0 else self.initial_capital + proceeds
                
            # Hold position
            else:
                portfolio.loc[portfolio.index[i], 'holdings'] = position * price
                portfolio.loc[portfolio.index[i], 'cash'] = portfolio['cash'].iloc[i-1] if i > 0 else self.initial_capital
            
            # Update total value and calculate returns
            portfolio.loc[portfolio.index[i], 'total'] = portfolio['holdings'].iloc[i] + portfolio['cash'].iloc[i]
            
            if i > 0:
                daily_return = portfolio['total'].iloc[i] / portfolio['total'].iloc[i-1] - 1
                portfolio.loc[portfolio.index[i], 'returns'] = daily_return
        
        # Calculate cumulative returns
        portfolio['cumulative_returns'] = (1 + portfolio['returns']).cumprod() - 1
        
        return portfolio
    
    def _calculate_metrics(self, portfolio):
        """Calculate performance metrics for the portfolio."""
        # Basic metrics
        start_date = portfolio.index[0]
        end_date = portfolio.index[-1]
        trading_days = len(portfolio)
        
        # Performance metrics
        total_return = portfolio['cumulative_returns'].iloc[-1]
        annual_return = (1 + total_return) ** (252 / trading_days) - 1
        
        # Risk metrics
        daily_returns = portfolio['returns'].dropna()
        volatility = daily_returns.std() * np.sqrt(252)  # Annualized volatility
        
        # Sharpe ratio (using 0% risk-free rate for simplicity)
        sharpe_ratio = annual_return / volatility if volatility != 0 else 0
        
        # Maximum drawdown
        cum_returns = (1 + portfolio['returns']).cumprod()
        running_max = cum_returns.cummax()
        drawdowns = (cum_returns / running_max - 1)
        max_drawdown = drawdowns.min()
        
        # Count trades
        buy_signals = (portfolio['position'] == 1.0).sum()
        sell_signals = (portfolio['position'] == -1.0).sum()
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'initial_value': self.initial_capital,
            'final_value': portfolio['total'].iloc[-1],
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'num_trades': buy_signals + sell_signals,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals
        }

    def get_results_summary(self):
        """
        Get a text summary of backtest results.
        
        Returns:
            String containing backtest results summary
        """
        if not self.results:
            return "Backtest has not been run yet."
        
        metrics = self.results['metrics']
        
        summary = [
            "=== BACKTEST RESULTS ===",
            f"Period: {metrics['start_date']} to {metrics['end_date']}",
            f"Initial Capital: ${metrics['initial_value']:.2f}",
            f"Final Portfolio Value: ${metrics['final_value']:.2f}",
            f"Total Return: {metrics['total_return']:.2%}",
            f"Annual Return: {metrics['annual_return']:.2%}",
            f"Volatility (Annual): {metrics['volatility']:.2%}",
            f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}",
            f"Maximum Drawdown: {metrics['max_drawdown']:.2%}",
            f"Number of Trades: {metrics['num_trades']}",
            f"Buy Signals: {metrics['buy_signals']}",
            f"Sell Signals: {metrics['sell_signals']}",
        ]
        
        return "\n".join(summary)
