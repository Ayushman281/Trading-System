"""
Deploy the Lambda function to AWS.

Note: This requires real AWS credentials and will incur costs.
Only use this if you have AWS credits or are willing to pay for AWS services.
"""
import os
import sys
import boto3
import logging
import tempfile
import zipfile
import subprocess
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - change these as needed
LAMBDA_FUNCTION_NAME = "moneyy-trade-analyzer"
LAMBDA_ROLE_NAME = "moneyy-lambda-role"
S3_BUCKET_NAME = "moneyy-trading-data"
API_GATEWAY_NAME = "moneyy-api"
REGION = "us-east-1"

def create_lambda_deployment_package():
    """
    Create a deployment package for Lambda.
    
    Returns:
        str: Path to the ZIP file containing the deployment package
    """
    logger.info("Creating Lambda deployment package...")
    
    # Create a temporary directory for the package
    temp_dir = tempfile.mkdtemp()
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    
    # Install requirements to the temporary directory
    requirements_path = os.path.join(project_root, "requirements.txt")
    if os.path.exists(requirements_path):
        logger.info("Installing dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "-r", requirements_path,
            "-t", temp_dir
        ])
    
    # Copy lambda function code
    lambda_path = os.path.join(project_root, "cloud", "lambda_function.py")
    lambda_dest = os.path.join(temp_dir, "lambda_function.py")
    with open(lambda_path, "r") as src, open(lambda_dest, "w") as dest:
        dest.write(src.read())
    
    # Create ZIP file
    zip_path = os.path.join(tempfile.gettempdir(), "lambda_deployment.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(
                    file_path, 
                    os.path.relpath(file_path, temp_dir)
                )
    
    logger.info(f"Created deployment package: {zip_path}")
    return zip_path

def deploy_lambda_function(zip_path):
    """
    Deploy the Lambda function to AWS.
    
    Args:
        zip_path: Path to the ZIP deployment package
        
    Returns:
        str: ARN of the deployed Lambda function
    """
    logger.info(f"Deploying Lambda function {LAMBDA_FUNCTION_NAME}...")
    
    # Read the ZIP file
    with open(zip_path, "rb") as f:
        zip_content = f.read()
    
    # Create IAM client
    iam_client = boto3.client("iam", region_name=REGION)
    
    # Check if role exists
    try:
        role = iam_client.get_role(RoleName=LAMBDA_ROLE_NAME)
        role_arn = role["Role"]["Arn"]
        logger.info(f"Using existing role: {role_arn}")
    except iam_client.exceptions.NoSuchEntityException:
        logger.info(f"Creating new role: {LAMBDA_ROLE_NAME}")
        
        # Create trust policy for Lambda
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Create the role
        role = iam_client.create_role(
            RoleName=LAMBDA_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        role_arn = role["Role"]["Arn"]
        
        # Attach policies for S3 access and CloudWatch Logs
        iam_client.attach_role_policy(
            RoleName=LAMBDA_ROLE_NAME,
            PolicyArn="arn:aws:iam::aws:policy/AmazonS3FullAccess"
        )
        
        iam_client.attach_role_policy(
            RoleName=LAMBDA_ROLE_NAME,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        
        # Wait for role to propagate
        logger.info("Waiting for role to propagate...")
        time.sleep(10)
    
    # Create Lambda client
    lambda_client = boto3.client("lambda", region_name=REGION)
    
    # Check if function exists
    try:
        lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
        logger.info(f"Updating existing function: {LAMBDA_FUNCTION_NAME}")
        
        # Update function code
        response = lambda_client.update_function_code(
            FunctionName=LAMBDA_FUNCTION_NAME,
            ZipFile=zip_content
        )
        
    except lambda_client.exceptions.ResourceNotFoundException:
        logger.info(f"Creating new function: {LAMBDA_FUNCTION_NAME}")
        
        # Create function
        response = lambda_client.create_function(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Runtime="python3.9",
            Role=role_arn,
            Handler="lambda_function.lambda_handler",
            Code={
                "ZipFile": zip_content
            },
            Timeout=30,
            MemorySize=256,
            Environment={
                "Variables": {
                    "S3_BUCKET": S3_BUCKET_NAME
                }
            }
        )
    
    function_arn = response["FunctionArn"]
    logger.info(f"Lambda function deployed: {function_arn}")
    
    return function_arn

def create_api_gateway(lambda_arn):
    """
    Create an API Gateway to trigger the Lambda function.
    
    Args:
        lambda_arn: ARN of the Lambda function
        
    Returns:
        str: URL of the API Gateway endpoint
    """
    logger.info(f"Setting up API Gateway: {API_GATEWAY_NAME}...")
    
    # Create API Gateway client
    apigw_client = boto3.client("apigateway", region_name=REGION)
    
    # Check if API exists
    apis = apigw_client.get_rest_apis()
    existing_api = None
    
    for api in apis.get("items", []):
        if api["name"] == API_GATEWAY_NAME:
            existing_api = api
            break
    
    if existing_api:
        api_id = existing_api["id"]
        logger.info(f"Using existing API Gateway: {api_id}")
    else:
        # Create new API
        response = apigw_client.create_rest_api(
            name=API_GATEWAY_NAME,
            description="API for Moneyy.ai Trading System"
        )
        api_id = response["id"]
        logger.info(f"Created new API Gateway: {api_id}")
    
    # Get root resource ID
    resources = apigw_client.get_resources(restApiId=api_id)
    root_id = None
    
    for resource in resources["items"]:
        if resource["path"] == "/":
            root_id = resource["id"]
            break
    
    # Create resource for /analyze-trades
    analyze_resource = apigw_client.create_resource(
        restApiId=api_id,
        parentId=root_id,
        pathPart="analyze-trades"
    )
    
    # Create resource for /analyze-trades/{date}
    date_resource = apigw_client.create_resource(
        restApiId=api_id,
        parentId=analyze_resource["id"],
        pathPart="{date}"
    )
    
    # Create GET method
    apigw_client.put_method(
        restApiId=api_id,
        resourceId=date_resource["id"],
        httpMethod="GET",
        authorizationType="NONE",
        requestParameters={
            "method.request.path.date": True
        }
    )
    
    # Set up Lambda integration
    apigw_client.put_integration(
        restApiId=api_id,
        resourceId=date_resource["id"],
        httpMethod="GET",
        type="AWS_PROXY",
        integrationHttpMethod="POST",  # Lambda always requires POST
        uri=f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
    )
    
    # Deploy the API
    apigw_client.create_deployment(
        restApiId=api_id,
        stageName="v1"
    )
    
    # Grant API Gateway permission to invoke Lambda
    lambda_client = boto3.client("lambda", region_name=REGION)
    lambda_client.add_permission(
        FunctionName=LAMBDA_FUNCTION_NAME,
        StatementId=f"apigateway-invoke-{int(time.time())}",
        Action="lambda:InvokeFunction",
        Principal="apigateway.amazonaws.com",
        SourceArn=f"arn:aws:execute-api:{REGION}:{boto3.client('sts').get_caller_identity()['Account']}:{api_id}/*/*"
    )
    
    # Get the API URL
    api_url = f"https://{api_id}.execute-api.{REGION}.amazonaws.com/v1/analyze-trades/{{date}}"
    logger.info(f"API Gateway endpoint: {api_url}")
    
    return api_url

def check_s3_bucket():
    """
    Check if S3 bucket exists, create if needed.
    """
    logger.info(f"Checking S3 bucket: {S3_BUCKET_NAME}...")
    
    s3_client = boto3.client("s3", region_name=REGION)
    
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        logger.info(f"Bucket {S3_BUCKET_NAME} exists")
    except Exception:
        logger.info(f"Creating bucket {S3_BUCKET_NAME}")
        
        # Create the bucket
        if REGION == "us-east-1":
            s3_client.create_bucket(Bucket=S3_BUCKET_NAME)
        else:
            s3_client.create_bucket(
                Bucket=S3_BUCKET_NAME,
                CreateBucketConfiguration={
                    "LocationConstraint": REGION
                }
            )
    
    return True

def main():
    """Main deployment function."""
    print("\nAWS Lambda Deployment Script")
    print("==========================")
    print("\nWARNING: This script will deploy resources to AWS that may incur costs.")
    
    # Ask for confirmation
    confirm = input("\nDo you want to proceed? (yes/no): ")
    if confirm.lower() != "yes":
        print("Deployment cancelled.")
        return
    
    try:
        import json
        import time
        
        # Check/create S3 bucket
        check_s3_bucket()
        
        # Create deployment package
        zip_path = create_lambda_deployment_package()
        
        # Deploy Lambda
        lambda_arn = deploy_lambda_function(zip_path)
        
        # Create API Gateway
        api_url = create_api_gateway(lambda_arn)
        
        print("\nDeployment Summary:")
        print(f"Lambda Function: {LAMBDA_FUNCTION_NAME}")
        print(f"S3 Bucket: {S3_BUCKET_NAME}")
        print(f"API Endpoint: {api_url}")
        print("\nDeployment completed successfully!")
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
