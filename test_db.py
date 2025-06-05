"""
Test database connection.
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment
database_url = os.getenv("DATABASE_URL")
print(f"Attempting to connect to: {database_url}")

try:
    # Create engine and connect
    engine = create_engine(database_url)
    
    # Test connection
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("Database connection successful!")
        
        # Display PostgreSQL version
        version = connection.execute(text("SHOW server_version")).scalar()
        print(f"PostgreSQL version: {version}")
        
except Exception as e:
    print(f"Error connecting to database: {e}")
