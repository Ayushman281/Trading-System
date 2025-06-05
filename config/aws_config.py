"""
AWS credentials and settings.
"""
import os
import boto3
from botocore.exceptions import NoCredentialsError
from utils.logger import get_logger

logger = get_logger(__name__)

# AWS credentials from environment variables
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

def get_aws_session():
    """
    Create and return an AWS session.
    
    Returns:
        boto3.session.Session: Configured AWS session
    """
    return boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

def get_s3_client():
    """
    Get an S3 client from AWS session.
    
    Returns:
        boto3.client: S3 client
    """
    session = get_aws_session()
    return session.client('s3')

def get_lambda_client():
    """
    Get a Lambda client from AWS session.
    
    Returns:
        boto3.client: Lambda client
    """
    session = get_aws_session()
    return session.client('lambda')

def validate_aws_credentials():
    """
    Validate AWS credentials by making a simple S3 listing call.
    
    Returns:
        bool: True if credentials are valid
    """
    try:
        s3 = get_s3_client()
        # Try to list buckets (will fail if credentials are invalid)
        s3.list_buckets()
        logger.info("AWS credentials are valid")
        return True
    except NoCredentialsError:
        logger.error("AWS credentials not found or invalid")
        return False
    except Exception as e:
        logger.error(f"Error validating AWS credentials: {e}")
        return False
