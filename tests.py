"""
Unit tests for FX Options Risk Aggregator.
Tests pricing, validation, and aggregation logic.
"""
import unittest
from datetime import date
import numpy as np
from scipy.stats import norm

from models import (
    ValidatedTrade, OptionType, CurrencyPair, 
    RawTrade, PortfolioSummary
)
from services.validator import ValidationService
from services.pricing_engine import PricingEngineService
from services.aggregator import AggregationService


class TestBlackScholesPricing(unittest.TestCase):
    """Test Black-Scholes pricing calculations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pricing_engine = PricingEngineService()
    
    def test_atm_call_option(self):
        """Test pricing of at-the-money call option."""
        trade = ValidatedTrade(
            trade_id="TEST001",
            currency_pair=CurrencyPair.EURUSD,
            option_type=OptionType.CALL,
            strike=1.1000,
            notional=1_000_000,
            notional_currency="USD",
            time_to_expiry=0.5,  # 6 months
            spot=1.1000,  # ATM
            volatility=0.10,  # 10% vol
            domestic_rate=0.05,
            foreign_rate=0.03
        )
        
        pv = self.pricing_engine._calculate_pv(trade)
        
        # ATM call should have positive value
        self.assertGreater(pv, 0)
        # should be a few thousand for 1M notional
        self.assertGreater(pv, 10_000)
        self.assertLess(pv, 100_000)
    
    def test_deep_itm_call_option(self):
        """Test pricing of deep in-the-money call option."""
        trade = ValidatedTrade(
            trade_id="TEST002",
            currency_pair=CurrencyPair.EURUSD,
            option_type=OptionType.CALL,
            strike=1.0000,
            notional=1_000_000,
            notional_currency="USD",
            time_to_expiry=0.5,  # 6 months
            spot=1.1000,  # 10% ITM
            volatility=0.10,
            domestic_rate=0.05,
            foreign_rate=0.03
        )
        
        pv = self.pricing_engine._calculate_pv(trade)
        
        # ITM call should be worth approximately intrinsic value, just a guardrail test to catch any model regresions
        # Intrinsic = (Spot - Strike) * Notional = 0.10 * 1M = 100k
        # With discounting and foreign rate, should be close
        self.assertGreater(pv, 90_000)
        self.assertAlmostEqual(pv, 110_500, delta=5_000)
    
    def test_otm_put_option(self):
        """Test pricing of out-of-the-money put option."""
        trade = ValidatedTrade(
            trade_id="TEST003",
            currency_pair=CurrencyPair.EURUSD,
            option_type=OptionType.PUT,
            strike=1.0000,
            notional=1_000_000,
            notional_currency="USD",
            time_to_expiry=0.5,  # 6 months
            spot=1.1000,  # 10% OTM
            volatility=0.10,
            domestic_rate=0.05,
            foreign_rate=0.03
        )
        
        pv = self.pricing_engine._calculate_pv(trade)
        
        # OTM put should have positive time value but less than ATM
        self.assertGreater(pv, 0)
        self.assertLess(pv, 10_000)
    
    def test_call_delta_positive(self):
        """Test that call options have positive delta."""
        trade = ValidatedTrade(
            trade_id="TEST004",
            currency_pair=CurrencyPair.EURUSD,
            option_type=OptionType.CALL,
            strike=1.1000,
            notional=1_000_000,
            notional_currency="USD",
            time_to_expiry=0.5,
            spot=1.1000,
            volatility=0.10,
            domestic_rate=0.05,
            foreign_rate=0.03
        )
        
        delta = self.pricing_engine._calculate_delta(trade)
        
        # Call delta should be positive
        self.assertGreater(delta, 0)
        # ATM call delta should be around 0.5 * notional
        self.assertGreater(delta, 400_000)
        self.assertLess(delta, 600_000)
    
    def test_put_delta_negative(self):
        """Test that put options have negative delta."""
        trade = ValidatedTrade(
            trade_id="TEST005",
            currency_pair=CurrencyPair.EURUSD,
            option_type=OptionType.PUT,
            strike=1.1000,
            notional=1_000_000,
            notional_currency="USD",
            time_to_expiry=0.5,
            spot=1.1000,
            volatility=0.10,
            domestic_rate=0.05,
            foreign_rate=0.03
        )
        
        delta = self.pricing_engine._calculate_delta(trade)
        
        # Put delta should be negative
        self.assertLess(delta, 0)
        # ATM put delta should be around -0.5 * notional
        self.assertGreater(delta, -600_000)
        self.assertLess(delta, -400_000)
    
    def test_vega_positive(self):
        """Test that vega is always positive for both calls and puts."""
        for option_type in [OptionType.CALL, OptionType.PUT]:
            trade = ValidatedTrade(
                trade_id="TEST006",
                currency_pair=CurrencyPair.EURUSD,
                option_type=option_type,
                strike=1.1000,
                notional=1_000_000,
                notional_currency="USD",
                time_to_expiry=0.5,
                spot=1.1000,
                volatility=0.10,
                domestic_rate=0.05,
                foreign_rate=0.03
            )
            
            vega = self.pricing_engine._calculate_vega(trade)
            
            # Vega should always be positive
            self.assertGreater(vega, 0)
    
    def test_put_call_parity(self):
        """Test put-call parity relationship."""
        # Put-Call Parity for FX options:
        # C - P = S * exp(-r_f * T) - K * exp(-r_d * T)
        
        strike = 1.1000
        spot = 1.1000
        T = 0.5
        r_d = 0.05
        r_f = 0.03
        
        call_trade = ValidatedTrade(
            trade_id="CALL",
            currency_pair=CurrencyPair.EURUSD,
            option_type=OptionType.CALL,
            strike=strike,
            notional=1_000_000,
            notional_currency="USD",
            time_to_expiry=T,
            spot=spot,
            volatility=0.10,
            domestic_rate=r_d,
            foreign_rate=r_f
        )
        
        put_trade = ValidatedTrade(
            trade_id="PUT",
            currency_pair=CurrencyPair.EURUSD,
            option_type=OptionType.PUT,
            strike=strike,
            notional=1_000_000,
            notional_currency="USD",
            time_to_expiry=T,
            spot=spot,
            volatility=0.10,
            domestic_rate=r_d,
            foreign_rate=r_f
        )
        
        call_pv = self.pricing_engine._calculate_pv(call_trade)
        put_pv = self.pricing_engine._calculate_pv(put_trade)
        
        # Calculate theoretical difference
        expected_diff = (
            spot * np.exp(-r_f * T) - strike * np.exp(-r_d * T)
        ) * 1_000_000
        
        actual_diff = call_pv - put_pv
        
        # Should match within small tolerance
        self.assertAlmostEqual(actual_diff, expected_diff, places=0)
    
    def test_zero_volatility_edge_case(self):
        """Test behavior with very low volatility."""
        trade = ValidatedTrade(
            trade_id="TEST007",
            currency_pair=CurrencyPair.EURUSD,
            option_type=OptionType.CALL,
            strike=1.1000,
            notional=1_000_000,
            notional_currency="USD",
            time_to_expiry=0.5,
            spot=1.1000,
            volatility=0.001,  # Very low vol
            domestic_rate=0.05,
            foreign_rate=0.03
        )
        
        pv = self.pricing_engine._calculate_pv(trade)
        
        # Should still produce a valid price
        self.assertGreater(pv, 0)
        self.assertIsInstance(pv, float)
        self.assertFalse(np.isnan(pv))
        self.assertFalse(np.isinf(pv))


class TestValidation(unittest.TestCase):
    """Test trade validation logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = ValidationService()
    
    def test_valid_trade(self):
        """Test validation of a valid trade."""
        raw_trade = RawTrade(
            TradeID="T001",
            Underlying="EUR/USD",
            Notional=1000000.000,
            NotionalCurrency="USD",
            Spot=1.1,
            Strike=1.1,
            Vol=0.01,
            RateDomestic=0.01,
            RateForeign=0.01,
            Expiry=0.25,
            OptionType="Call"
        )
        
        result = self.validator.validate_trades([raw_trade])
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.valid_trades), 1)
        self.assertEqual(len(result.errors), 0)
    
    def test_invalid_option_type(self):
        """Test validation fails for invalid option type."""
        raw_trade = RawTrade(
            TradeID="T002",
            Underlying="EUR/USD",
            Notional=1000000.000,
            NotionalCurrency="USD",
            Spot=1.1,
            Strike=1.1,
            Vol=0.01,
            RateDomestic=0.01,
            RateForeign=0.01,
            Expiry=0.25,
            OptionType="INVALID"
        )
        
        result = self.validator.validate_trades([raw_trade])
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.valid_trades), 0)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Invalid OptionType", result.errors[0])
    
    def test_invalid_currency_pair(self):
        """Test validation fails for invalid currency pair."""
        raw_trade = RawTrade(
            TradeID="T003",
            Underlying="EUR/CHF",  # Not supported
            Notional=1000000.000,
            NotionalCurrency="USD",
            Spot=1.1,
            Strike=1.1,
            Vol=0.01,
            RateDomestic=0.01,
            RateForeign=0.01,
            Expiry=0.25,
            OptionType="Call"
        )
        
        result = self.validator.validate_trades([raw_trade])
        
        self.assertFalse(result.is_valid)
        self.assertIn("Invalid Underlying", result.errors[0])
    
    def test_negative_expiry(self):
        """Test validation fails for negative expiry."""
        raw_trade = RawTrade(
            TradeID="T004",
            Underlying="EUR/USD",
            Notional=1000000.000,
            NotionalCurrency="USD",
            Spot=1.1,
            Strike=1.1,
            Vol=0.01,
            RateDomestic=0.01,
            RateForeign=0.01,
            Expiry=-0.25,  # Negative
            OptionType="Call"
        )
        
        result = self.validator.validate_trades([raw_trade])
        
        self.assertFalse(result.is_valid)
        self.assertIn("must be positive", result.errors[0])
    
    def test_negative_strike(self):
        """Test validation fails for negative strike."""
        raw_trade = RawTrade(
            TradeID="T005",
            Underlying="EUR/USD",
            Notional=1000000.000,
            NotionalCurrency="USD",
            Spot=1.1,
            Strike=-1.1,
            Vol=0.01,
            RateDomestic=0.01,
            RateForeign=0.01,
            Expiry=0.25,
            OptionType="Call"
        )
        
        result = self.validator.validate_trades([raw_trade])
        
        self.assertFalse(result.is_valid)
    
    def test_case_insensitive_option_type(self):
        """Test that option type is case-insensitive."""
        for option_type_input in ["call", "Call", "CALL", "put", "Put", "PUT"]:
            raw_trade = RawTrade(
                TradeID=f"T_{option_type_input}",
                Underlying="EUR/USD",
                Notional=1000000.000,
                NotionalCurrency="USD",
                Spot=1.1,
                Strike=1.1,
                Vol=0.01,
                RateDomestic=0.01,
                RateForeign=0.01,
                Expiry=0.25,
                OptionType=option_type_input
            )
            
            result = self.validator.validate_trades([raw_trade])
            self.assertTrue(result.is_valid, f"Failed for option type: {option_type_input}")
    
    def test_currency_pair_normalization(self):
        """Test that currency pairs with slashes are normalized."""
        raw_trade = RawTrade(
            TradeID="T006",
            Underlying="EUR / USD",  # With spaces
            Notional=1000000.000,
            NotionalCurrency="USD",
            Spot=1.1,
            Strike=1.1,
            Vol=0.01,
            RateDomestic=0.01,
            RateForeign=0.01,
            Expiry=0.25,
            OptionType="Call"
        )
        
        result = self.validator.validate_trades([raw_trade])
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.valid_trades[0].currency_pair, CurrencyPair.EURUSD)
    
    def test_multiple_trades_with_errors(self):
        """Test validation of multiple trades with some errors."""
        raw_trades = [
            RawTrade(
                TradeID="T_VALID",
                Underlying="EUR/USD",
                Notional=1000000.000,
                NotionalCurrency="USD",
                Spot=1.1,
                Strike=1.1,
                Vol=0.01,
                RateDomestic=0.01,
                RateForeign=0.01,
                Expiry=0.25,
                OptionType="Call"
            ),
            RawTrade(
                TradeID="T_INVALID",
                Underlying="EUR/USD",
                Notional=1000000.000,
                NotionalCurrency="USD",
                Spot=1.1,
                Strike=-1.1,  # Invalid
                Vol=0.01,
                RateDomestic=0.01,
                RateForeign=0.01,
                Expiry=0.25,
                OptionType="Call"
            )
        ]
        
        result = self.validator.validate_trades(raw_trades)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.valid_trades), 1)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("T_INVALID", result.errors[0])


class TestAggregation(unittest.TestCase):
    """Test portfolio aggregation logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.aggregator = AggregationService()
    
    def test_portfolio_aggregation(self):
        """Test aggregation of multiple trades."""
        from models import PricedTrade
        
        trades = [
            PricedTrade(
                trade_id="T1",
                currency_pair="EURUSD",
                option_type="CALL",
                strike=1.10,
                notional=1000000,
                notional_currency="USD",
                spot=1.08,
                time_to_expiry=0.5,
                volatility=0.12,
                pv=25000,
                delta=500000,
                vega=3000
            ),
            PricedTrade(
                trade_id="T2",
                currency_pair="GBPUSD",
                option_type="PUT",
                strike=1.25,
                notional=500000,
                notional_currency="USD",
                spot=1.27,
                time_to_expiry=0.25,
                volatility=0.15,
                pv=-5000,
                delta=-250000,
                vega=1500
            )
        ]
        
        summary = self.aggregator.aggregate_portfolio(trades)
        
        self.assertEqual(summary.total_trades, 2)
        self.assertEqual(summary.total_pv, 20000)
        self.assertEqual(summary.total_delta, 250000)
        self.assertEqual(summary.total_vega, 4500)
    
    def test_empty_portfolio(self):
        """Test aggregation of empty portfolio."""
        trades = []
        
        summary = self.aggregator.aggregate_portfolio(trades)
        
        self.assertEqual(summary.total_trades, 0)
        self.assertEqual(summary.total_pv, 0)
        self.assertEqual(summary.total_delta, 0)
        self.assertEqual(summary.total_vega, 0)
    
    def test_single_trade_aggregation(self):
        """Test aggregation of single trade."""
        from models import PricedTrade
        
        trades = [
            PricedTrade(
                trade_id="T1",
                currency_pair="EURUSD",
                option_type="CALL",
                strike=1.10,
                notional=1000000,
                notional_currency="USD",
                spot=1.08,
                time_to_expiry=0.5,
                volatility=0.12,
                pv=25000,
                delta=500000,
                vega=3000
            )
        ]
        
        summary = self.aggregator.aggregate_portfolio(trades)
        
        self.assertEqual(summary.total_trades, 1)
        self.assertEqual(summary.total_pv, 25000)
        self.assertEqual(summary.total_delta, 500000)
        self.assertEqual(summary.total_vega, 3000)


if __name__ == '__main__':
    unittest.main()
