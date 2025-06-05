"""
Main application entry point for the Moneyy.ai Trading System.
"""
import os
from fastapi import FastAPI, Query, HTTPException
from api.routes import router as api_router
from config.settings import Settings
from trading.run_simulation import run_simulation
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, API_KEY

# Load settings
settings = Settings()

# Initialize FastAPI app
app = FastAPI(
    title="Moneyy.ai Trading System",
    description="A comprehensive trading system for managing trades, monitoring stocks, and analyzing market data.",
    version="0.1.0",
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Moneyy.ai Trading System",
        "documentation": "/docs",
    }

# Trading simulation endpoint
@app.get("/simulate")
async def simulate_trading(
    ticker: str = Query("AAPL", description="Stock ticker to simulate"),
    short_window: int = Query(50, description="Short moving average window"),
    long_window: int = Query(200, description="Long moving average window"),
    initial_capital: float = Query(100000.0, description="Initial capital")
):
    try:
        output_file = run_simulation(
            ticker=ticker,
            short_window=short_window,
            long_window=long_window,
            initial_capital=initial_capital
        )
        
        # Get relative path for response
        relative_path = os.path.relpath(output_file, os.path.dirname(os.path.abspath(__file__)))
        
        return {
            "message": "Trading simulation completed successfully",
            "ticker": ticker,
            "strategy": f"Moving Average Crossover ({short_window}/{long_window})",
            "report_path": relative_path,
            "view_report": f"/static/{os.path.basename(output_file)}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Example of using environment variables for database connection
# db_connection = connect_to_db(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    
    # Update the host to "localhost" instead of "0.0.0.0"
    print(f"\nStarting server - API will be available at http://localhost:{port}")
    print(f"API documentation: http://localhost:{port}/docs")
    print(f"Trading simulation: http://localhost:{port}/simulate?ticker=AAPL")
    print("\nPress Ctrl+C to quit\n")
    
    uvicorn.run(
        "app:app", 
        host="localhost",  # Changed from "0.0.0.0" to "localhost"
        port=port, 
        reload=True
    )
