# Moneyy.ai Trading System

A comprehensive trading system that processes real-time stock data, manages trades through a REST API, integrates cloud functionality, and includes an algorithmic trading simulation.

## Features

### REST API

- FastAPI-based REST endpoints for trade management
- PostgreSQL database for persistent storage
- Input validation and error handling
- Trade filtering by date and ticker

### Real-Time Processing

- WebSocket implementation for live stock price updates
- Price spike detection (2%+ changes within a minute)
- 5-minute average price calculations

### AWS Cloud Integration

- Lambda function for trade data analysis
- S3 storage with YEAR/MONTH/DAY structure
- Volume and average price calculations
- API Gateway integration

### Algorithmic Trading

- Moving Average Crossover Strategy (50/200 day)
- Historical data processing
- Performance reporting
- Visualization of signals and returns

## Setup and Installation

### Prerequisites

- Python 3.9+
- PostgreSQL database
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/moneyy-ai.git
cd moneyy-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
python initialize.py
```

## Running the Application

```bash
# Start the main API server
python app.py

# In a separate terminal, start real-time processing
python -m realtime.run_realtime

# Run a trading simulation
curl http://localhost:8000/simulate?ticker=AAPL
```

## Comprehensive Testing Guide

### 1. API Endpoint Testing

**Run the Test:**
```bash
python test_endpoints.py
```

**What This Tests:**
- REST API endpoints for trade operations (Task 1)
- Database connectivity with PostgreSQL
- Input validation for trade data
- Filtering trades by ticker and date

**Sample Output:**
```
===== TESTING MONEYY.AI API ENDPOINTS =====

1. Testing root endpoint...
✓ Root endpoint working!
  Response: {'message': 'Welcome to Moneyy.ai Trading System', 'documentation': '/docs'}

2. Testing adding a trade...
✓ Add trade endpoint working!
  Trade ID: a020f89d-b7e4-4ba6-a2ce-146edfa7db07

3. Testing get trades endpoint...
✓ Get trades endpoint working! Found 8 trades.
  ✓ Recently added trade (ID: a020f89d-b7e4-4ba6-a2ce-146edfa7db07) was found in the response
  ✓ Filter by ticker working! Found 6 AAPL trades.
  ✓ Filter by date range working! Found 8 trades.

4. Testing trading simulation endpoint...
✓ Trading simulation endpoint working!
  Report path: outputs\AAPL_ma_50_200_report.html
  ✓ Trading simulation with parameters working!

5. Testing API documentation...
✓ API documentation (Swagger UI) is accessible!

===== ENDPOINT TESTING COMPLETE =====
```

### 2. Real-Time Data Processing Testing

**Run the Test:**
```bash
# First make sure the app.py is running
python app.py

# Then in a separate terminal:
python test_realtime.py
```

**What This Tests:**
- WebSocket data streaming (Task 2)
- Price spike detection algorithm (>2% change in 1 minute)
- 5-minute average price calculations 
- Price alerts functionality

**Sample Output:**
```
===== TESTING REAL-TIME COMPONENTS =====

Testing start-monitoring endpoint...
✓ Successfully called start-monitoring endpoint
  Response: {'status': 'success', 'message': 'Real-time monitoring started in background'}

Waiting 3 seconds for monitoring system to start...

1. Testing WebSocket server connection...
✓ Connected to WebSocket server
  Waiting for price updates (5 seconds)...
  ✓ Received update: AAPL $161.09
  ✓ Received update: MSFT $296.8
  ✓ Received update: AMZN $126.57
✓ Successfully received 3 price updates

2. Waiting for price spike detection (up to 30 seconds)...
✓ Price spike detected! New trade recorded: NVDA at $428.83

3. Testing price averages calculation...
  Checking if price averages are being stored...
✓ Found 5 price average records!
  Most recent: AAPL avg: $148.22 (5 min)

===== REAL-TIME TESTING COMPLETE =====
```

**Alternative Method: Run Real-Time Components Individually**
```bash
# In terminal 1 - Start WebSocket server
python -m realtime.mock_websocket_server

# In terminal 2 - Start WebSocket client 
python -m realtime.websocket_client

# Watch for price alerts like:
WARNING - PRICE ALERT: TSLA decreased by 8.64% in 58.6 seconds
WARNING - TSLA: $190.73 -> $174.26
```

### 3. AWS Cloud Integration Testing

**Run the Test:**
```bash
python run_aws_tests.py
```

**What This Tests:**
- AWS Lambda functionality (Task 3)
- S3 storage with YEAR/MONTH/DAY file structure
- Trade data analysis (volume & average price calculation)
- API Gateway integration for triggering Lambda

**Sample Output:**
```
===== AWS Integration Testing =====

1. Creating mock trade data...
  ✓ Created mock data for 2025-06-06 with 25 records
  ✓ Created mock data for 2025-06-05 with 25 records

2. Testing Lambda function with mock S3...
INFO:cloud.test_lambda_locally:Using temporary directory as mock S3: C:\Users\...\Temp\tmpnbs8w7yp
INFO:cloud.test_lambda_locally:Saved mock S3 file: s3://moneyy-trading-data/2025/06/06/trades.csv
Lambda response:
{
  "statusCode": 200,
  "body": "{\"message\": \"Trade analysis completed for 2025-06-06\", 
            \"analysis_path\": \"s3://moneyy-trading-data/2025/06/06/analysis_2025-06-06.csv\", 
            \"record_count\": 5, 
            \"tickers_analyzed\": [\"AAPL\", \"AMZN\", \"GOOGL\", \"META\", \"MSFT\"]}"
}

Analysis file content:
ticker,total_volume,average_price,trade_count,analysis_date
AAPL,350,117.5,5,2025-06-06
AMZN,350,117.5,5,2025-06-06
GOOGL,350,117.5,5,2025-06-06
META,350,117.5,5,2025-06-06
MSFT,350,117.5,5,2025-06-06

  ✓ Lambda function test succeeded

3. Testing FastAPI endpoint (requires app to be running)...
  ✓ API endpoint test succeeded
  Response: {
  "message": "Trade analysis completed for 2025-06-06",
  "analysis_path": "s3://moneyy-trading-data/2025/06/06/analysis_2025-06-06.csv",
  "record_count": 5,
  "tickers_analyzed": ["AAPL", "AMZN", "GOOGL", "META", "MSFT"]
}

===== AWS Integration Testing Complete =====
```

**Test API Gateway Integration:**
```bash
# With app.py running, visit:
http://localhost:8000/api/analyze-trades/2023-06-06
```

### 4. Algorithmic Trading Simulation Testing

**Run the Test:**
```bash
# Via API endpoint
curl http://localhost:8000/simulate?ticker=AAPL

# With custom parameters
curl http://localhost:8000/simulate?ticker=TSLA&short_window=20&long_window=100&initial_capital=50000
```

**What This Tests:**
- Moving Average Crossover Strategy (Task 4)
- Historical data processing
- Buy/sell signal generation
- Performance metrics calculation

**Sample Output:**
```json
{
  "message": "Trading simulation completed successfully",
  "ticker": "AAPL",
  "strategy": "Moving Average Crossover (50/200)",
  "report_path": "outputs/AAPL_ma_50_200_report.html",
  "view_report": "/static/AAPL_ma_50_200_report.html",
  "metrics": {
    "final_portfolio_value": 156489.32,
    "total_returns_pct": 56.49,
    "max_drawdown_pct": 18.72,
    "trades_executed": 8,
    "win_rate": 0.75
  }
}
```

**HTML Report:**
The HTML report in the `outputs` directory will show:
- Price chart with moving averages
- Buy/sell signals marked on the chart
- Portfolio value over time
- Performance metrics table
- Trade journal with entry/exit points

### 5. Unit Tests

**Run Unit Tests:**
```bash
pytest tests/test_api.py -v
```

**What This Tests:**
- Individual components' correctness
- API request validation
- Error handling
- Database operations

**Sample Output:**
```
====================================================== test session starts =======================================================
platform win32 -- Python 3.11.9, pytest-7.3.1, pluggy-1.6.0 -- D:\College\Projects\Moneyy.ai\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\College\Projects\Moneyy.ai
plugins: anyio-4.9.0
collected 4 items                                                                                                                

tests/test_api.py::test_root_endpoint PASSED                                                                                [ 25%]
tests/test_api.py::test_add_trade PASSED                                                                                    [ 50%]
tests/test_api.py::test_add_trade_validation PASSED                                                                         [ 75%]
tests/test_api.py::test_get_trades PASSED                                                                                   [100%]

================================================== 4 passed in 2.29s ==================================================
```

### 6. Database Setup Testing

**Run Database Setup:**
```bash
python initialize.py
```

**What This Tests:**
- PostgreSQL connection configuration
- Database schema creation
- Table initialization

**Sample Output:**
```
Testing database connection...
✓ Database connection successful!
Initializing database...
Creating database tables...
Database tables: trades, stock_price_averages
Database initialization complete
```

## API Documentation

API documentation is available at http://localhost:8000/docs once the server is running. The documentation includes:

- All available endpoints with detailed descriptions
- Request/response schemas
- Try-it-out feature for testing endpoints directly
- Sample requests and responses

## Project Structure

- `api/`: REST API implementation and route handlers
- `cloud/`: AWS Lambda and S3 integration components
- `realtime/`: WebSocket server, client, and real-time processors
- `trading/`: Algorithmic trading strategy implementation
- `config/`: Database and application configuration
- `utils/`: Shared utility functions and logging
- `tests/`: Test scripts and fixtures
- `data/`: Data storage directory for stock data
- `outputs/`: Generated trading reports and visualizations

## Assumptions and Design Decisions

- **FastAPI Framework:** Chosen over Django for better performance and modern typing support
- **PostgreSQL Database:** Used for robust data storage with transaction support
- **WebSocket Implementation:** Implemented real-time data processing over WebSockets instead of polling for better efficiency
- **AWS Integration Testing:** Designed a mock implementation for testing AWS features without incurring costs
- **Moving Average Strategy:** Implemented as a practical demonstration of algorithmic trading
- **Local Testing:** All components are testable locally without external services

## Project Limitations and Future Work

- Currently uses simulated stock data; could integrate with real market data APIs
- WebSocket implementation could be enhanced with reconnection strategies
- Trading strategy could be expanded with more technical indicators
- Could add user authentication and multi-tenancy support

## License

MIT
