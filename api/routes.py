"""
API routes for trade operations.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Path, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import json
import sys
from unittest import mock

from .schemas import TradeCreate, TradeResponse
from .models import Trade, TradeSide
from config.database import get_db_session
from utils.logger import get_logger
from cloud.lambda_function import lambda_handler

logger = get_logger(__name__)

router = APIRouter()

@router.get("/", tags=["info"])
async def api_root():
    """Root API endpoint."""
    return {
        "message": "Moneyy.ai Trading API",
        "version": "1.0.0"
    }

@router.post("/trades", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def add_trade(trade: TradeCreate, session: Session = Depends(get_db_session)):
    """
    Add a new trade.
    """
    try:
        # Convert side string to enum
        side = TradeSide(trade.side)
        
        # Create new trade
        db_trade = Trade(
            ticker=trade.ticker,
            price=trade.price,
            quantity=trade.quantity,
            side=side,
            timestamp=trade.timestamp or datetime.utcnow()
        )
        
        # Save to database
        session.add(db_trade)
        session.commit()
        session.refresh(db_trade)
        
        logger.info(f"Added trade: {trade.ticker} {trade.side} {trade.quantity} shares at ${trade.price}")
        
        # Convert to response format
        response_data = db_trade.to_dict()
        return TradeResponse(**response_data)
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid trade data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error adding trade: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add trade"
        )

@router.get("/trades", response_model=List[TradeResponse])
async def get_trades(
    ticker: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_db_session)
):
    """
    Retrieve trades with optional filtering.
    """
    try:
        query = session.query(Trade)
        
        # Apply filters if provided
        if ticker:
            query = query.filter(Trade.ticker == ticker)
        
        if start_date:
            query = query.filter(Trade.timestamp >= start_date)
        
        if end_date:
            # Include the entire end_date
            next_day = datetime.combine(end_date, datetime.max.time())
            query = query.filter(Trade.timestamp <= next_day)
        
        # Apply pagination
        query = query.order_by(Trade.timestamp.desc()).offset(offset).limit(limit)
        
        # Execute query
        trades = query.all()
        
        # Convert to response format
        return [TradeResponse(**trade.to_dict()) for trade in trades]
    
    except Exception as e:
        logger.error(f"Error retrieving trades: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trades"
        )

# Add new endpoint for price averages
@router.get("/price-averages", response_model=List[dict])
async def get_price_averages(
    ticker: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    session: Session = Depends(get_db_session)
):
    """
    Retrieve 5-minute price averages with optional filtering.
    """
    try:
        # Import the model from the correct location
        from realtime.data_processor import StockPriceAverage
        
        query = session.query(StockPriceAverage)
        
        # Apply filters if provided
        if ticker:
            query = query.filter(StockPriceAverage.ticker == ticker)
        
        if start_date:
            query = query.filter(StockPriceAverage.start_time >= start_date)
        
        if end_date:
            # Include the entire end_date
            next_day = datetime.combine(end_date, datetime.max.time())
            query = query.filter(StockPriceAverage.end_time <= next_day)
        
        # Execute query with ordering and limit
        averages = query.order_by(StockPriceAverage.end_time.desc()).limit(100).all()
        
        # Convert to dictionary format
        return [avg.to_dict() for avg in averages]
    
    except Exception as e:
        logger.error(f"Error retrieving price averages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve price averages"
        )

@router.post("/start-monitoring")
async def start_monitoring():
    """
    Start the real-time price monitoring system.
    """
    try:
        script_path = os.path.join(os.path.dirname(__file__), "..", "realtime", "run_realtime.py")
        
        # Start the monitoring script in a separate process
        subprocess.Popen([sys.executable, script_path])
        
        return {
            "status": "success",
            "message": "Real-time monitoring started in background"
        }
    except Exception as e:
        logger.error(f"Error starting monitoring: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start monitoring"
        )

from datetime import date as date_type

# Add endpoint to simulate API Gateway triggering Lambda
@router.get("/analyze-trades/{date}")
async def analyze_trades(date: str = Path(..., description="Date in YYYY-MM-DD format")):
    """
    Analyze trades for a specific date using AWS Lambda functionality.
    
    This endpoint simulates AWS API Gateway triggering a Lambda function.
    """
    try:
        from cloud.lambda_function import lambda_handler
        from datetime import datetime
        
        # Validate date format
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        # Import mocking tools
        from cloud.test_lambda_locally import MockLambdaContext, MockS3Client
        
        # Create event object like API Gateway would
        event = {
            'pathParameters': {
                'date': date
            }
        }
        
        # Create mock S3 client and data
        mock_s3 = MockS3Client()
        
        # Generate mock trade data
        from cloud.s3_utils import create_mock_trade_data_for_s3
        mock_trades = create_mock_trade_data_for_s3(date)
        
        # Convert to CSV string
        import io
        import pandas as pd
        csv_buffer = io.StringIO()
        mock_trades.to_csv(csv_buffer, index=False)
        mock_csv = csv_buffer.getvalue()
        
        # Get S3 paths
        bucket = 'moneyy-trading-data'
        trade_path = f"{date_obj.year}/{date_obj.month:02d}/{date_obj.day:02d}/trades.csv"
        
        # Store mock trade data in our mock S3
        mock_s3.put_object(Bucket=bucket, Key=trade_path, Body=mock_csv)
        
        # Create mock Lambda context
        mock_context = MockLambdaContext()
        
        # Call Lambda handler with mocks
        with mock.patch('boto3.client', return_value=mock_s3):
            response = lambda_handler(event, mock_context)
        
        # Return response if successful
        if response['statusCode'] == 200:
            return json.loads(response['body'])
        else:
            raise HTTPException(
                status_code=response['statusCode'],
                detail=json.loads(response['body']).get('message', 'Unknown error')
            )
    
    except Exception as e:
        logger.error(f"Error running trade analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze trades: {str(e)}"
        )
