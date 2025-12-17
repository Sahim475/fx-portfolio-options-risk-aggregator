"""
Domain models for FX Options trading system.
Defines data structures at different stages of the pipeline.
"""
from datetime import date
from enum import Enum
from typing import List
from pydantic import BaseModel, Field, model_validator


class OptionType(str, Enum):
    """Type of option: Call or Put"""
    CALL = "CALL"
    PUT = "PUT"


class CurrencyPair(str, Enum):
    """Supported currency pairs"""
    EURUSD = "EURUSD"
    GBPUSD = "GBPUSD"
    USDJPY = "USDJPY"
    AUDUSD = "AUDUSD"
    USDCAD = "USDCAD"
    USDCHF = "USDCHF"


class RawTrade(BaseModel):
    """
    Raw trade data as loaded from Excel.
    Minimal validation - accepts various formats.
    """
    TradeID: str
    Underlying: str  #"EUR/USD"
    Notional: float
    NotionalCurrency: str  # "USD" or "JPY"
    Spot: float
    Strike: float
    Vol: float
    RateDomestic: float
    RateForeign: float
    Expiry: float  # Time to expiry in years
    OptionType: str  # "Call" or "Put"
    
    class Config:
        str_strip_whitespace = True


class ValidatedTrade(BaseModel):
    """
    Validated trade with proper types and business logic validation.
    """
    trade_id: str = Field(..., description="Unique trade identifier")
    currency_pair: CurrencyPair
    option_type: OptionType
    strike: float = Field(gt=0, description="Strike price (must be positive)")
    notional: float = Field(gt=0, description="Notional amount (must be positive)")
    notional_currency: str = Field(..., description="Currency of notional (USD or JPY)")
    time_to_expiry: float = Field(gt=0, le=10.0, description="Time to expiry in years")
    spot: float = Field(gt=0, description="Current spot rate")
    volatility: float = Field(gt=0, le=5.0, description="Implied volatility (0-500%)")
    domestic_rate: float = Field(ge=-0.1, le=1.0, description="Domestic risk-free rate")
    foreign_rate: float = Field(ge=-0.1, le=1.0, description="Foreign risk-free rate")
    
    @model_validator(mode='after')
    def validate_business_rules(self) -> 'ValidatedTrade':
        """Apply cross-field business logic validation."""
        # Reasonable parameter ranges
        if self.volatility > 1.0:  # 100% vol
            raise ValueError(f"Volatility {self.volatility:.2%} seems unreasonably high")
        
        # Ensure notional currency matches currency pair
        if self.notional_currency not in ['USD', 'JPY']:
            raise ValueError(f"NotionalCurrency must be USD or JPY, got {self.notional_currency}")
        
        return self


class PricedTrade(BaseModel):
    """
    Trade with computed risk metrics.
    Output of the pricing engine.
    """
    trade_id: str
    currency_pair: str
    option_type: str
    strike: float
    notional: float
    notional_currency: str
    spot: float
    time_to_expiry: float
    volatility: float
    pv: float = Field(..., description="Present Value in notional currency")
    delta: float = Field(..., description="Delta: sensitivity to spot rate")
    vega: float = Field(..., description="Vega: sensitivity to volatility")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }


class PortfolioSummary(BaseModel):
    """
    Aggregated portfolio-level risk metrics.
    """
    total_trades: int
    total_pv: float
    total_delta: float
    total_vega: float
    valuation_date: date
    reporting_currency: str
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }


class ValidationResult(BaseModel):
    """
    Result of trade validation process.
    Contains both valid trades and any errors encountered.
    """
    valid_trades: List[ValidatedTrade]
    errors: List[str]
    
    @property
    def is_valid(self) -> bool:
        """Returns True if no validation errors."""
        return len(self.errors) == 0
