# Moneyy.ai Trading System

A comprehensive trading system that processes real-time stock data, manages trades through a REST API, and integrates cloud functionality for data analysis.

## Features

- REST API for trade management using FastAPI
- Real-time stock data processing with WebSocket
- Cloud integration with AWS (S3, Lambda)
- Algorithmic trading simulation

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- PostgreSQL or MongoDB
- AWS account (for cloud integration)
- Redis (optional, for Celery background tasks)

### Installation

1. Clone the repository
   ```
   git clone <repository-url>
   cd Moneyy.ai
   ```

2. Create and activate virtual environment
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Unix/MacOS
   source venv/bin/activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Configure environment variables (create a .env file based on .env.example)

5. Run the application
   ```
   python app.py
   ```

## API Endpoints

- `POST /api/trades` - Add a new trade
- `GET /api/trades` - Fetch trades with optional filtering

## Project Structure

- `api/` - REST API implementation
- `realtime/` - Real-time data processing
- `cloud/` - AWS integration
- `trading/` - Algorithmic trading simulation
- `config/` - Configuration files
- `utils/` - Shared utilities
- `tests/` - Unit and integration tests

## License

[MIT License](LICENSE)
