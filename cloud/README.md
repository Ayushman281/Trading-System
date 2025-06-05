# AWS Cloud Integration for Moneyy.ai

This module provides AWS cloud integration for the Moneyy.ai trading system, specifically focusing on:

1. AWS Lambda functions for analyzing trade data
2. S3 storage integration for storing and retrieving trade data
3. API Gateway integration for triggering Lambda functions

## Local Testing

You can test the AWS components locally without actually deploying to AWS:

```bash
# Test the Lambda function locally
python -m cloud.test_lambda_locally

# Use the API endpoint simulation
curl http://localhost:8000/api/analyze-trades/2023-06-06
```

## Folder Structure

- `lambda_function.py`: The main AWS Lambda function
- `s3_utils.py`: Utilities for interacting with S3
- `test_lambda_locally.py`: Script for local testing
- `deploy_to_aws.py`: Script for deploying to real AWS (optional)

## Data Flow

1. Trade data is stored in S3 with the structure: `YEAR/MONTH/DAY/trades.csv`
2. The Lambda function is triggered via API Gateway with a date parameter
3. The function fetches trade data from S3 for the specified date
4. It analyzes the data to calculate total volume and average price for each stock
5. Results are stored back in S3 as `YEAR/MONTH/DAY/analysis_YYYY-MM-DD.csv`

## AWS Deployment (Optional)

If you want to deploy to real AWS resources:

```bash
python -m cloud.deploy_to_aws
```

This will create:
- An S3 bucket for storing trade data
- A Lambda function for analyzing the data
- An API Gateway to trigger the Lambda function

Note: This requires proper AWS credentials and will incur AWS costs.

## API Gateway Usage

Once deployed, you can trigger the Lambda function via:

```
GET https://[api-id].execute-api.[region].amazonaws.com/v1/analyze-trades/[date]
```

Where `[date]` is in the format `YYYY-MM-DD`.

## Local API Simulation

The FastAPI application includes an endpoint that simulates the API Gateway:

```
GET http://localhost:8000/api/analyze-trades/[date]
```

This calls the Lambda function code locally without requiring actual AWS resources.
