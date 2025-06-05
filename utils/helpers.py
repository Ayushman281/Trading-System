"""
Helper functions used across the application.
"""
import os
import json
import csv
import pandas as pd
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)

def ensure_directory_exists(directory_path):
    """
    Create a directory if it doesn't exist.
    
    Args:
        directory_path: Path to the directory
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        logger.info(f"Created directory: {directory_path}")

def read_csv_to_dataframe(file_path):
    """
    Read a CSV file into a pandas DataFrame.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        pandas.DataFrame containing the CSV data
    """
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Error reading CSV file {file_path}: {e}")
        return pd.DataFrame()

def save_dataframe_to_csv(df, file_path):
    """
    Save a pandas DataFrame to a CSV file.
    
    Args:
        df: pandas DataFrame to save
        file_path: Path where to save the CSV file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        ensure_directory_exists(directory)
        
        # Save DataFrame to CSV
        df.to_csv(file_path, index=False)
        logger.info(f"DataFrame saved to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving DataFrame to {file_path}: {e}")
        return False

def date_range(start_date, end_date):
    """
    Generate a range of dates between start and end dates.
    
    Args:
        start_date: Starting date (datetime.date)
        end_date: Ending date (datetime.date)
        
    Yields:
        datetime.date objects in the range
    """
    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)

def format_s3_path(date_obj, base_path="trades"):
    """
    Format S3 path for a given date.
    
    Args:
        date_obj: Date object
        base_path: Base path prefix
        
    Returns:
        S3 path string
    """
    return f"{date_obj.year}/{date_obj.month:02d}/{date_obj.day:02d}/{base_path}.csv"

def parse_date_string(date_str):
    """
    Parse a date string in YYYY-MM-DD format.
    
    Args:
        date_str: Date string
        
    Returns:
        datetime.date object or None if parsing fails
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        logger.error(f"Invalid date format: {date_str}. Expected YYYY-MM-DD.")
        return None
