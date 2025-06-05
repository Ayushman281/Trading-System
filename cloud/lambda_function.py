"""
AWS Lambda function for analyzing trade data stored in S3.
"""
import os
import io
import csv
import json
import logging
import datetime
import boto3
import pandas as pd
from collections import defaultdict
from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

# Set up logging
logger = Logger(service="trade-analyzer")

def parse_date_from_event(event):
    """
    Extract date from event object, either from path parameters or query string.
    
    Args:
        event: Lambda event object
        
    Returns:
        datetime.date: The parsed date
    """
    try:
        # Check for API Gateway event format
        if 'pathParameters' in event and event['pathParameters'] and 'date' in event['pathParameters']:
            date_str = event['pathParameters']['date']
        elif 'queryStringParameters' in event and event['queryStringParameters'] and 'date' in event['queryStringParameters']:
            date_str = event['queryStringParameters']['date']
        else:
            # Default to today if no date provided
            logger.warning("No date parameter found in event, using today's date")
            return datetime.datetime.now().date()
        
        # Parse the date (expected format: YYYY-MM-DD)
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception as e:
        logger.error(f"Error parsing date from event: {e}")
        # Default to today if there's an error
        return datetime.datetime.now().date()

def get_s3_path(date_obj):
    """
    Generate the S3 path for trade data based on date.
    
    Args:
        date_obj: Date object
        
    Returns:
        str: S3 path in YEAR/MONTH/DAY/trades.csv format
    """
    return f"{date_obj.year}/{date_obj.month:02d}/{date_obj.day:02d}/trades.csv"

def get_analysis_path(date_obj):
    """
    Generate the S3 path for analysis results.
    
    Args:
        date_obj: Date object
        
    Returns:
        str: S3 path for analysis results
    """
    return f"{date_obj.year}/{date_obj.month:02d}/{date_obj.day:02d}/analysis_{date_obj.strftime('%Y-%m-%d')}.csv"

def analyze_trade_data(data):
    """
    Analyze trade data to calculate total volume and average price per stock.
    
    Args:
        data: CSV data as a string or DataFrame
    
    Returns:
        pandas.DataFrame: Analysis results
    """
    # If input is a string, parse it as CSV
    if isinstance(data, str):
        try:
            df = pd.read_csv(io.StringIO(data))
        except Exception as e:
            logger.error(f"Error parsing CSV data: {e}")
            return pd.DataFrame()
    else:
        df = data
    
    # Check if DataFrame is empty or missing required columns
    if df.empty or not all(col in df.columns for col in ['ticker', 'price', 'quantity']):
        logger.warning("DataFrame is empty or missing required columns")
        return pd.DataFrame()
    
    # Group by ticker and calculate metrics
    results = df.groupby('ticker').agg(
        total_volume=pd.NamedAgg(column='quantity', aggfunc='sum'),
        average_price=pd.NamedAgg(column='price', aggfunc='mean'),
        trade_count=pd.NamedAgg(column='ticker', aggfunc='count')
    ).reset_index()
    
    # Add timestamp
    results['analysis_date'] = datetime.datetime.now().strftime('%Y-%m-%d')
    
    return results

def save_analysis_to_s3(bucket, analysis_path, analysis_df):
    """
    Save analysis results to S3.
    
    Args:
        bucket: S3 bucket name
        analysis_path: Path in the bucket to save the results
        analysis_df: DataFrame with analysis results
        
    Returns:
        bool: True if successful, False otherwise
    """
    s3_client = boto3.client('s3')
    
    # Convert DataFrame to CSV
    csv_buffer = io.StringIO()
    analysis_df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()
    
    # Upload to S3
    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=analysis_path,
            Body=csv_content,
            ContentType='text/csv'
        )
        logger.info(f"Analysis results saved to s3://{bucket}/{analysis_path}")
        return True
    except ClientError as e:
        logger.error(f"Error saving analysis results to S3: {e}")
        return False

def fetch_trade_data(bucket, s3_path):
    """
    Fetch trade data from S3.
    
    Args:
        bucket: S3 bucket name
        s3_path: Path in the bucket to the trade data
        
    Returns:
        str: CSV data as a string, or None if failed
    """
    s3_client = boto3.client('s3')
    
    try:
        # Get object from S3
        response = s3_client.get_object(Bucket=bucket, Key=s3_path)
        
        # Read the content
        csv_content = response['Body'].read().decode('utf-8')
        logger.info(f"Successfully fetched trade data from s3://{bucket}/{s3_path}")
        return csv_content
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.warning(f"No trade data found at s3://{bucket}/{s3_path}")
        else:
            logger.error(f"Error fetching trade data from S3: {e}")
        return None

@logger.inject_lambda_context(clear_state=True)
def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        dict: Response object
    """
    # Set log level based on whether we're in local testing mode
    if context is None:
        logger.setLevel(logging.INFO)
        logger.info("Running in local testing mode")
    
    try:
        # Get S3 bucket name from environment variable or use default for testing
        bucket_name = os.environ.get('S3_BUCKET', 'moneyy-trading-data')
        
        # Parse date from event
        date_obj = parse_date_from_event(event)
        logger.info(f"Processing trade data for date: {date_obj}")
        
        # Generate S3 paths
        trade_path = get_s3_path(date_obj)
        analysis_path = get_analysis_path(date_obj)
        
        # Fetch trade data from S3
        trade_data = fetch_trade_data(bucket_name, trade_path)
        
        if not trade_data:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'message': f"No trade data found for {date_obj}"
                })
            }
        
        # Analyze the data
        analysis_results = analyze_trade_data(trade_data)
        
        if analysis_results.empty:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': f"Failed to analyze trade data for {date_obj}"
                })
            }
        
        # Save analysis results to S3
        if save_analysis_to_s3(bucket_name, analysis_path, analysis_results):
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f"Trade analysis completed for {date_obj}",
                    'analysis_path': f"s3://{bucket_name}/{analysis_path}",
                    'record_count': len(analysis_results),
                    'tickers_analyzed': analysis_results['ticker'].tolist()
                })
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': f"Failed to save analysis results for {date_obj}"
                })
            }
            
    except Exception as e:
        logger.exception("Unhandled exception in lambda_handler")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f"Error processing trade data: {str(e)}"
            })
        }

# For local testing
if __name__ == "__main__":
    # Create a test event
    test_event = {
        'queryStringParameters': {
            'date': datetime.datetime.now().strftime('%Y-%m-%d')
        }
    }
    
    # Call the handler with the test event
    response = lambda_handler(test_event, None)
    print(json.dumps(response, indent=2))
