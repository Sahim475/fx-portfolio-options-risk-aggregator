"""
Validation service for trade data.
Transforms and validates raw trades into validated trades.
"""
from typing import List

from models import RawTrade, ValidatedTrade, ValidationResult, OptionType, CurrencyPair


class ValidationService:
    """
    Service responsible for validating and transforming raw trade data.
    Performs field-level and business logic validation.
    """
    
    def __init__(self):
        pass
    
    def validate_trades(self, raw_trades: List[RawTrade]) -> ValidationResult:
        """
        Validate a list of raw trades.
        
        Args:
            raw_trades: List of raw trade data from input
            
        Returns:
            ValidationResult containing valid trades and any errors
        """
        valid_trades = []
        errors = []
        
        for raw_trade in raw_trades:
            try:
                validated_trade = self._validate_single_trade(raw_trade)
                valid_trades.append(validated_trade)
            except Exception as e:
                error_msg = f"Trade {raw_trade.TradeID}: {str(e)}"
                errors.append(error_msg)
        
        return ValidationResult(valid_trades=valid_trades, errors=errors)
    
    def _validate_single_trade(self, raw_trade: RawTrade) -> ValidatedTrade:
        """
        Validate and transform a single raw trade.
        
        Args:
            raw_trade: Raw trade data
            
        Returns:
            ValidatedTrade object
            
        Raises:
            ValueError: If validation fails
        """
        # Parse and validate option type 
        option_type_str = raw_trade.OptionType.upper()
        try:
            option_type = OptionType(option_type_str)
        except ValueError:
            raise ValueError(
                f"Invalid OptionType '{raw_trade.OptionType}'. "
                f"Must be one of: {[t.value for t in OptionType]}"
            )
        
        # Parse and validate currency pair
        currency_pair_normalized = raw_trade.Underlying.replace("/", "").replace(" ", "").upper()
        try:
            currency_pair = CurrencyPair(currency_pair_normalized)
        except ValueError:
            raise ValueError(
                f"Invalid Underlying '{raw_trade.Underlying}'. "
                f"Must be one of: EUR/USD, GBP/USD, or USD/JPY"
            )
        
        # Validate time to expiry
        if raw_trade.Expiry <= 0:
            raise ValueError(f"Expiry must be positive, got {raw_trade.Expiry}")
        
        # Create validated trade
        try:
            validated_trade = ValidatedTrade(
                trade_id=raw_trade.TradeID,
                currency_pair=currency_pair,
                option_type=option_type,
                strike=raw_trade.Strike,
                notional=raw_trade.Notional,
                notional_currency=raw_trade.NotionalCurrency,
                time_to_expiry=raw_trade.Expiry,
                spot=raw_trade.Spot,
                volatility=raw_trade.Vol,
                domestic_rate=raw_trade.RateDomestic,
                foreign_rate=raw_trade.RateForeign
            )
        except Exception as e:
            raise ValueError(f"Validation error: {str(e)}")
        
        return validated_trade