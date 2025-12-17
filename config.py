"""
Configuration settings for the FX Options Risk Aggregator.
"""
from dataclasses import dataclass
from datetime import date


@dataclass
class Config:
    """
    Application configuration settings.
    
    Centralizes all configurable parameters including:
    - Market conventions
    - Calculation parameters
    - Validation thresholds
    """
    
    # Valuation settings
    valuation_date: date = None
    reporting_currency: str = "USD"
    
    # Day count convention (for reference - not used since expiry is already in years)
    day_count_convention: str = "ACT/365"
    
    # Numerical precision
    price_decimal_places: int = 2
    greek_decimal_places: int = 2
    
    # Validation thresholds
    max_volatility: float = 1.0  # 100%
    min_time_to_expiry_years: float = 0.01
    
    # Output settings
    output_sheet_trades: str = "Trade_Results"
    output_sheet_summary: str = "Portfolio_Summary"
    
    def __post_init__(self):
        """Set default valuation date if not provided."""
        if self.valuation_date is None:
            self.valuation_date = date.today()
