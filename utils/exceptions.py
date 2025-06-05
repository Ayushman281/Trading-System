"""
Custom exceptions for the application.
"""

class TradeValidationError(Exception):
    """Exception raised when trade validation fails."""
    pass

class WebSocketConnectionError(Exception):
    """Exception raised when WebSocket connection fails."""
    pass

class DatabaseError(Exception):
    """Exception raised for database errors."""
    pass

class AWSConnectionError(Exception):
    """Exception raised for AWS connection failures."""
    pass

class TradeStrategyError(Exception):
    """Exception raised for errors in trading strategies."""
    pass

class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass

class AnalysisError(Exception):
    """Exception raised for data analysis errors."""
    pass

class ReportGenerationError(Exception):
    """Exception raised when report generation fails."""
    pass
