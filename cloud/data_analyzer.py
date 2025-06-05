"""
Trade data analysis functions.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)

def analyze_daily_trades(df):
    """
    Perform daily analysis on trade data.
    
    Args:
        df: Pandas DataFrame containing trade data
        
    Returns:
        DataFrame with analysis results
    """
    # Check if dataframe is empty
    if df.empty:
        logger.warning("Empty dataframe provided for analysis")
        return pd.DataFrame(columns=['ticker', 'total_volume', 'average_price', 
                                    'min_price', 'max_price', 'price_volatility'])
    
    # Group by ticker
    grouped = df.groupby('ticker')
    
    # Calculate metrics
    analysis = grouped.agg({
        'quantity': 'sum',             # Total volume
        'price': ['mean', 'min', 'max', 'std']  # Price statistics
    })
    
    # Flatten the column hierarchy and rename
    analysis.columns = ['total_volume', 'average_price', 'min_price', 'max_price', 'price_volatility']
    
    # Reset index to make ticker a column
    analysis = analysis.reset_index()
    
    # Calculate volatility as percentage of average price
    analysis['price_volatility'] = (analysis['price_volatility'] / analysis['average_price'] * 100).round(2)
    
    # Round price columns to 2 decimal places
    for col in ['average_price', 'min_price', 'max_price']:
        analysis[col] = analysis[col].round(2)
    
    return analysis

def analyze_trade_by_timeframe(df, period='1H'):
    """
    Analyze trade data aggregated by time periods.
    
    Args:
        df: DataFrame with trade data including timestamp
        period: Time period for grouping ('1H'=hourly, '1D'=daily)
        
    Returns:
        DataFrame with time-based analysis
    """
    # Ensure timestamp is datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    else:
        logger.error("Timestamp column missing from trade data")
        return pd.DataFrame()
    
    # Group by ticker and time period
    df['time_group'] = df['timestamp'].dt.floor(period)
    grouped = df.groupby(['ticker', 'time_group'])
    
    # Calculate metrics
    analysis = grouped.agg({
        'quantity': 'sum',     # Volume in period
        'price': 'mean',       # Average price in period
    }).reset_index()
    
    # Calculate volume-weighted average price (VWAP)
    vwap_df = df.copy()
    vwap_df['price_volume'] = vwap_df['price'] * vwap_df['quantity']
    vwap = vwap_df.groupby(['ticker', 'time_group']).agg({
        'price_volume': 'sum',
        'quantity': 'sum'
    })
    vwap['vwap'] = vwap['price_volume'] / vwap['quantity']
    vwap = vwap[['vwap']].reset_index()
    
    # Merge VWAP with main analysis
    analysis = analysis.merge(vwap, on=['ticker', 'time_group'])
    
    # Round price columns
    analysis['price'] = analysis['price'].round(2)
    analysis['vwap'] = analysis['vwap'].round(2)
    
    return analysis
