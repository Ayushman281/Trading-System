"""
AWS Lambda function for analyzing trade data.
"""
import json
import pandas as pd
from datetime import datetime
from .s3_operations import get_latest_file, save_analysis_results

def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        Dict with execution status and results
    """
    try:
        # Get the date from the event or use current date
        if event.get('queryStringParameters') and 'date' in event['queryStringParameters']:
            date_str = event['queryStringParameters']['date']
            # Parse date string (format: YYYY-MM-DD)
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            date_obj = datetime.now()
        
        # Format date components for S3 path
        year = date_obj.strftime("%Y")
        month = date_obj.strftime("%m")
        day = date_obj.strftime("%d")
        
        # Fetch the latest trades file from S3
        bucket_name = 'moneyy-ai-trades'  # Set your bucket name
        file_path = f"{year}/{month}/{day}/trades.csv"
        
        # Get the latest file
        latest_file = get_latest_file(bucket_name, file_path)
        
        if latest_file is None:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'message': f"No trades file found for {year}-{month}-{day}"
                })
            }
        
        # Read CSV data into a pandas DataFrame
        df = pd.read_csv(latest_file)
        
        # Perform analysis
        analysis_results = analyze_trade_data(df)
        
        # Save analysis results
        output_path = f"{year}/{month}/{day}/analysis_{day}.csv"
        save_analysis_results(bucket_name, output_path, analysis_results)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Analysis completed successfully',
                'date': f"{year}-{month}-{day}",
                'output_path': output_path
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f"Error: {str(e)}"
            })
        }

def analyze_trade_data(df):
    """
    Analyze trade data to calculate volume and average price by ticker.
    
    Args:
        df: Pandas DataFrame containing trade data
        
    Returns:
        DataFrame with analysis results
    """
    # Ensure the DataFrame has the expected columns
    required_columns = ['ticker', 'price', 'quantity']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in trade data")
    
    # Calculate total volume and average price by ticker
    analysis = df.groupby('ticker').agg({
        'quantity': 'sum',  # Total traded volume
        'price': 'mean'     # Average price
    }).reset_index()
    
    # Rename columns for clarity
    analysis.columns = ['ticker', 'total_volume', 'average_price']
    
    # Round average price to 2 decimal places
    analysis['average_price'] = analysis['average_price'].round(2)
    
    return analysis
