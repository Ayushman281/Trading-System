"""
AWS S3 operations for reading and writing files.
"""
import os
import io
import boto3
import pandas as pd
from utils.logger import get_logger
from botocore.exceptions import ClientError

logger = get_logger(__name__)

def get_s3_client():
    """
    Get an AWS S3 client.
    
    Returns:
        boto3.client: Configured S3 client
    """
    return boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )

def get_latest_file(bucket_name, file_path):
    """
    Get the latest file from S3.
    
    Args:
        bucket_name: S3 bucket name
        file_path: Path to the file in the bucket
        
    Returns:
        BytesIO object containing the file content or None if the file doesn't exist
    """
    s3 = get_s3_client()
    
    try:
        # Get the object from S3
        response = s3.get_object(Bucket=bucket_name, Key=file_path)
        
        # Read the content into a BytesIO object
        content = io.BytesIO(response['Body'].read())
        return content
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.warning(f"File not found: {file_path}")
            return None
        else:
            logger.error(f"Error retrieving file from S3: {e}")
            raise

def save_analysis_results(bucket_name, file_path, analysis_df):
    """
    Save analysis results to S3.
    
    Args:
        bucket_name: S3 bucket name
        file_path: Path to save the file in the bucket
        analysis_df: Pandas DataFrame containing analysis results
        
    Returns:
        bool: True if save was successful
    """
    s3 = get_s3_client()
    
    try:
        # Convert DataFrame to CSV
        csv_buffer = io.StringIO()
        analysis_df.to_csv(csv_buffer, index=False)
        
        # Upload to S3
        s3.put_object(
            Bucket=bucket_name,
            Key=file_path,
            Body=csv_buffer.getvalue(),
            ContentType='text/csv'
        )
        
        logger.info(f"Analysis results saved to s3://{bucket_name}/{file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving analysis results to S3: {e}")
        raise
