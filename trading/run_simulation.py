"""
Run a trading strategy simulation using historical data.
"""
import os
import pandas as pd
import argparse
from .strategy import MovingAverageCrossoverStrategy
from .backtester import Backtester
from .report_generator import ReportGenerator
from utils.logger import get_logger
from utils.helpers import ensure_directory_exists

logger = get_logger(__name__)

def run_simulation(ticker="AAPL", data_file=None, short_window=50, long_window=200, 
                  initial_capital=100000.0, output_dir=None):
    """
    Run a trading strategy simulation.
    
    Args:
        ticker: Stock ticker symbol to analyze
        data_file: Path to CSV file with historical data
        short_window: Short moving average window
        long_window: Long moving average window
        initial_capital: Initial capital for simulation
        output_dir: Directory to save output report
        
    Returns:
        Path to the generated report file
    """
    # Use default data file if not provided
    if data_file is None:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
        data_file = os.path.join(data_dir, "stock_data.csv")
    
    # Check if file exists
    if not os.path.exists(data_file):
        logger.error(f"Data file not found: {data_file}")
        raise FileNotFoundError(f"Data file not found: {data_file}")
    
    # Load and prepare data
    logger.info(f"Loading data from {data_file}")
    df = pd.read_csv(data_file)
    
    # Filter by ticker
    if 'ticker' in df.columns:
        df = df[df['ticker'] == ticker]
    
    # Check if we have data
    if df.empty:
        logger.error(f"No data found for ticker {ticker}")
        raise ValueError(f"No data found for ticker {ticker}")
    
    # Prepare data for backtesting
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    if 'close' not in df.columns and 'price' in df.columns:
        df['close'] = df['price']
    
    # Create strategy and backtester
    logger.info(f"Creating {short_window}/{long_window} MA strategy for {ticker}")
    strategy = MovingAverageCrossoverStrategy(short_window=short_window, long_window=long_window)
    backtester = Backtester(strategy, df, initial_capital=initial_capital)
    
    # Run backtest
    logger.info("Running backtest...")
    results = backtester.run()
    
    # Generate report
    logger.info("Generating report...")
    report_gen = ReportGenerator(results)
    
    # Create output directory
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'outputs')
    
    ensure_directory_exists(output_dir)
    output_file = os.path.join(output_dir, f"{ticker}_ma_{short_window}_{long_window}_report.html")
    
    # Save report
    report_gen.save_report_to_file(output_file)
    logger.info(f"Report saved to {output_file}")
    
    # Print summary
    print(backtester.get_results_summary())
    
    return output_file

def main():
    """Main entry point for the simulation script."""
    parser = argparse.ArgumentParser(description='Run trading strategy simulation')
    parser.add_argument('--ticker', type=str, default='AAPL', help='Stock ticker symbol')
    parser.add_argument('--data-file', type=str, help='Path to CSV file with historical data')
    parser.add_argument('--short-window', type=int, default=50, help='Short MA window')
    parser.add_argument('--long-window', type=int, default=200, help='Long MA window')
    parser.add_argument('--capital', type=float, default=100000.0, help='Initial capital')
    parser.add_argument('--output-dir', type=str, help='Output directory for report')
    
    args = parser.parse_args()
    
    run_simulation(
        ticker=args.ticker,
        data_file=args.data_file,
        short_window=args.short_window,
        long_window=args.long_window,
        initial_capital=args.capital,
        output_dir=args.output_dir
    )

if __name__ == '__main__':
    main()
