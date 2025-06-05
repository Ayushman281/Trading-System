"""
Validation functions for API inputs.
"""
from .schemas import TradeCreate

def validate_trade_input(trade: TradeCreate) -> list:
    """
    Validate trade input data beyond Pydantic validation.
    
    Args:
        trade: The trade data to validate
        
    Returns:
        A list of validation errors, empty if no errors found
    """
    errors = []
    
    # Further validation beyond Pydantic
    if trade.price <= 0:
        errors.append("Price must be positive")
    
    if trade.quantity <= 0:
        errors.append("Quantity must be positive")
    
    # You could add more complex validation rules here
    # For example, checking if the ticker exists in an allowed list
    
    return errors
