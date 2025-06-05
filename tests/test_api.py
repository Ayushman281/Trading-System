"""
Tests for the API module.
"""
import pytest
from fastapi.testclient import TestClient
import json
from app import app
from api.models import Trade, TradeSide

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to Moneyy.ai Trading System" in response.json()["message"]

def test_add_trade():
    """Test adding a trade."""
    trade_data = {
        "ticker": "AAPL",
        "price": 150.75,
        "quantity": 10,
        "side": "buy"
    }
    
    response = client.post("/api/trades", json=trade_data)
    assert response.status_code == 201
    
    # Check response data
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert data["price"] == 150.75
    assert data["quantity"] == 10
    assert data["side"] == "buy"
    assert "id" in data  # ID should be present but as a string UUID
    assert "timestamp" in data

def test_add_trade_validation():
    """Test trade validation."""
    # Invalid trade (negative price)
    invalid_trade = {
        "ticker": "AAPL",
        "price": -10.0,
        "quantity": 5,
        "side": "buy"
    }
    
    response = client.post("/api/trades", json=invalid_trade)
    # FastAPI validates with Pydantic which returns 422 for validation errors
    assert response.status_code == 422 or response.status_code == 400

def test_get_trades():
    """Test fetching trades."""
    # Add a test trade first
    test_trade = {
        "ticker": "TSLA",
        "price": 200.50,
        "quantity": 5,
        "side": "buy"
    }
    client.post("/api/trades", json=test_trade)
    
    # Get all trades
    response = client.get("/api/trades")
    assert response.status_code == 200
    
    # Check if response is a list
    trades = response.json()
    assert isinstance(trades, list)
    
    # Test filtering by ticker
    response = client.get("/api/trades?ticker=TSLA")
    assert response.status_code == 200
    filtered_trades = response.json()
    
    # Check that all returned trades are for TSLA
    if filtered_trades:  # Only check if trades were returned
        for trade in filtered_trades:
            assert trade["ticker"] == "TSLA"
