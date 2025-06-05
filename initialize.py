"""
Initialize the Moneyy.ai application database.
"""
import os
import sys
from sqlalchemy import inspect, text
from config.database import engine, Base
from dotenv import load_dotenv
import importlib

# Load environment variables
load_dotenv()

def check_database_connection():
    """Test the database connection."""
    print("Testing database connection...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection successful")
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def initialize_database():
    """Create database tables if they don't exist."""
    print("Initializing database...")
    
    # Import models here to avoid circular imports
    # This also ensures we're using the same Base as in the models
    from api.models import Trade, TradeSide
    
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Check created tables
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    
    print(f"Database tables: {', '.join(table_names)}")
    
    return True

if __name__ == "__main__":
    if check_database_connection():
        initialize_database()
        print("Database initialization complete")
        sys.exit(0)
    else:
        print("Database connection failed, check your configuration")
        sys.exit(1)
