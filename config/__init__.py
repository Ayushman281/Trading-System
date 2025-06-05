"""
Configuration package initialization.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Export database config variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "gunimithu")
DB_NAME = os.getenv("DB_NAME", "moneyy_trading")
DB_PORT = os.getenv("DB_PORT", "5432")

# API configurations
API_KEY = os.getenv("API_KEY", "your-default-api-key")  # Add a default API key or generate one

# Debug mode
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Other configurations
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
