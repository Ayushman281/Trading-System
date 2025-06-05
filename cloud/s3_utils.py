"""
Utility functions for interacting with AWS S3.
"""
import os
import io
import boto3
import pandas as pd
from datetime import datetime
from botocore.exceptions import ClientError
from utils.logger import get_logger

logger = get_logger(__name__)

def get_s3_client(local_mode=False):
    """
    Get an S3 client, optionally configured for local testing.
    
    Args:
        local_mode: If True, configure for local testing
        
    Returns:
        boto3.client: S3 client
    """
    if local_mode:
        # For local testing with moto or localstack
        return boto3.client(
            's3',
            aws_access_key_id='test',
            aws_secret_access_key='test',
            endpoint_url='http://localhost:4566'  # LocalStack default endpoint
        )
    else:
        # Use standard AWS credentials
        return boto3.client('s3')

def upload_dataframe_to_s3(df, bucket, key, local_mode=False):
    """
    Upload a pandas DataFrame to S3 as a CSV.
    
    Args:
        df: pandas DataFrame to upload
        bucket: S3 bucket name
        key: Object key (path in bucket)
        local_mode: If True, use local testing configuration
        
    Returns:
        bool: True if successful, False otherwise
    """
    s3_client = get_s3_client(local_mode)
    
    try:
        # Convert DataFrame to CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        # Upload to S3
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=csv_content,
            ContentType='text/csv'
        )
        
        logger.info(f"Uploaded DataFrame to s3://{bucket}/{key}")
        return True
    
    except Exception as e:
        logger.error(f"Error uploading DataFrame to S3: {e}")
        return False

def download_csv_from_s3(bucket, key, local_mode=False):
    """
    Download a CSV file from S3 as a pandas DataFrame.
    
    Args:
        bucket: S3 bucket name
        key: Object key (path in bucket)
        local_mode: If True, use local testing configuration
        
    Returns:
        pandas.DataFrame: The downloaded data, or None if failed
    """
    s3_client = get_s3_client(local_mode)
    
    try:
        # Get the object from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        
        # Read the CSV content
        csv_content = response['Body'].read().decode('utf-8')
        
        # Parse as DataFrame
        df = pd.read_csv(io.StringIO(csv_content))
        
        logger.info(f"Downloaded s3://{bucket}/{key} (rows: {len(df)})")
        return df
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.warning(f"File s3://{bucket}/{key} does not exist")
        else:
            logger.error(f"Error downloading from S3: {e}")
        return None

def list_objects_in_path(bucket, prefix, local_mode=False):
    """
    List objects in an S3 path.
    
    Args:
        bucket: S3 bucket name
        prefix: Path prefix to list
        local_mode: If True, use local testing configuration
        
    Returns:
        list: Object keys in the path
    """
    s3_client = get_s3_client(local_mode)
    
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
        )
        
        if 'Contents' in response:
            return [item['Key'] for item in response['Contents']]
        else:
            return []
    
    except Exception as e:
        logger.error(f"Error listing objects in S3: {e}")
        return []

def generate_s3_path_for_date(date_obj=None, file_type='trades'):
    """
    Generate S3 path based on date in the format YEAR/MONTH/DAY/filename.csv.
    
    Args:
        date_obj: Date to use, defaults to today
        file_type: Type of file ('trades' or 'analysis')
        
    Returns:
        str: S3 path
    """
    # Use today's date if none provided
    if date_obj is None:
        date_obj = datetime.now().date()
    
    # Generate base path
    base_path = f"{date_obj.year}/{date_obj.month:02d}/{date_obj.day:02d}"
    
    # Add filename based on type
    if file_type == 'analysis':
        return f"{base_path}/analysis_{date_obj.strftime('%Y-%m-%d')}.csv"
    else:
        return f"{base_path}/trades.csv"

def create_mock_trade_data_for_s3(date_str=None):
    """
    Create mock trade data for testing S3 integration.
    
    Args:
        date_str: Date string in YYYY-MM-DD format, defaults to today
        
    Returns:
        pandas.DataFrame: Mock trade data
    """
    # Use today if no date provided
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Parse date
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    
    # Prepare data
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
    records = []
    
    # Generate mock trades
    for ticker in tickers:
        # Generate 5-10 trades per ticker
        for i in range(5, 10):
            records.append({
                'ticker': ticker,
                'price': round(100 + i * 2.5, 2),
                'quantity': i * 10,
                'side': 'buy' if i % 2 == 0 else 'sell',
                'timestamp': f"{date_str}T{10 + i:02d}:00:00"
            })
    
    return pd.DataFrame(records)
