"""
Test the AWS Lambda function locally without actual AWS services.
"""
import os
import io
import json
import logging
import tempfile
from unittest import mock
from datetime import datetime, timedelta
import pandas as pd
from cloud.lambda_function import lambda_handler
from cloud.s3_utils import create_mock_trade_data_for_s3, upload_dataframe_to_s3

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockS3Client:
    """Mock S3 client for local testing."""
    
    def __init__(self):
        # Use a temporary directory to store "S3" files
        self.temp_dir = tempfile.mkdtemp()
        logger.info(f"Using temporary directory as mock S3: {self.temp_dir}")
        self.files = {}  # Dictionary to store mock S3 files
    
    def put_object(self, Bucket, Key, Body, ContentType=None):
        """Mock S3 put_object method."""
        # Store the file content
        self.files[(Bucket, Key)] = Body
        
        # Also save to temp directory for inspection
        path = os.path.join(self.temp_dir, Bucket, Key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(Body)
        
        logger.info(f"Saved mock S3 file: s3://{Bucket}/{Key}")
        return {}
    
    def get_object(self, Bucket, Key):
        """Mock S3 get_object method."""
        key = (Bucket, Key)
        if key in self.files:
            return {'Body': MockS3Body(self.files[key])}
        else:
            # Simulate NoSuchKey error
            import botocore
            error = {'Error': {'Code': 'NoSuchKey', 'Message': 'The specified key does not exist.'}}
            raise botocore.exceptions.ClientError(error, 'GetObject')

class MockS3Body:
    """Mock S3 object body."""
    
    def __init__(self, content):
        self.content = content
    
    def read(self):
        """Return content as bytes."""
        return self.content.encode('utf-8')

class MockLambdaContext:
    """Mock Lambda context for local testing."""
    
    def __init__(self):
        self.function_name = "mock-lambda-function"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:mock-lambda-function"
        self.aws_request_id = "mock-request-id"
        self.log_group_name = "/aws/lambda/mock-lambda-function"
        self.log_stream_name = "2023/06/06/[$LATEST]mock-stream"
        self.identity = None
        self.client_context = None
        self.function_version = "$LATEST"
        self.remaining_time_in_millis = 3000

def test_lambda_with_mock_s3():
    """Test the Lambda function with mock S3."""
    # Create a mock S3 client
    mock_s3 = MockS3Client()
    
    # Choose a date for testing
    test_date = datetime.now().date()
    test_date_str = test_date.strftime('%Y-%m-%d')
    
    # Create test event
    test_event = {
        'queryStringParameters': {
            'date': test_date_str
        }
    }
    
    # Generate mock trade data
    mock_trades = create_mock_trade_data_for_s3(test_date_str)
    
    # Convert to CSV string
    csv_buffer = io.StringIO()
    mock_trades.to_csv(csv_buffer, index=False)
    mock_csv = csv_buffer.getvalue()
    
    # Get S3 paths
    bucket = 'moneyy-trading-data'
    trade_path = f"{test_date.year}/{test_date.month:02d}/{test_date.day:02d}/trades.csv"
    
    # Store mock trade data in our mock S3
    mock_s3.put_object(Bucket=bucket, Key=trade_path, Body=mock_csv)
    
    # Create a mock Lambda context
    mock_context = MockLambdaContext()
    
    # Patch boto3.client to use our mock
    with mock.patch('boto3.client', return_value=mock_s3):
        # Run the Lambda handler with the mock context
        response = lambda_handler(test_event, mock_context)
        
        # Print the response
        print("Lambda response:")
        print(json.dumps(response, indent=2))
        
        # Check if analysis file was created
        analysis_path = f"{test_date.year}/{test_date.month:02d}/{test_date.day:02d}/analysis_{test_date_str}.csv"
        analysis_key = (bucket, analysis_path)
        
        if analysis_key in mock_s3.files:
            print("\nAnalysis file content:")
            print(mock_s3.files[analysis_key])
        else:
            print("\nAnalysis file was not created")

if __name__ == "__main__":
    import botocore
    test_lambda_with_mock_s3()
