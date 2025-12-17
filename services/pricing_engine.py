"""
Pricing engine service for FX options using Black-Scholes model.
Computes PV, Delta, and Vega for validated trades.
"""
from typing import List
import numpy as np
from scipy.stats import norm

from models import ValidatedTrade, PricedTrade, OptionType


class PricingEngineService:
    """
    Pricing FX options using the Black-Scholes model.
    
    The Garman-Kohlhagen model (Black-Scholes for FX) is used:
    - Call: S * exp(-r_f * T) * N(d1) - K * exp(-r_d * T) * N(d2)
    - Put:  K * exp(-r_d * T) * N(-d2) - S * exp(-r_f * T) * N(-d1)
    
    Where:
    - S: Spot rate
    - K: Strike price
    - T: Time to expiry
    - r_d: Domestic risk-free rate
    - r_f: Foreign risk-free rate
    - σ: Implied volatility
    - d1 = [ln(S/K) + (r_d - r_f + σ²/2) * T] / (σ * sqrt(T))
    - d2 = d1 - σ * sqrt(T)
    """
    
    def price_portfolio(self, trades: List[ValidatedTrade]) -> List[PricedTrade]:
        """
        Price a portfolio of validated trades.
        
        Args:
            trades: List of validated trades
            
        Returns:
            List of priced trades with PV, Delta, and Vega
        """
        priced_trades = []
        
        for trade in trades:
            pv = self._calculate_pv(trade)
            delta = self._calculate_delta(trade)
            vega = self._calculate_vega(trade)
            
            priced_trade = PricedTrade(
                trade_id=trade.trade_id,
                currency_pair=trade.currency_pair.value,
                option_type=trade.option_type.value,
                strike=trade.strike,
                notional=trade.notional,
                notional_currency=trade.notional_currency,
                spot=trade.spot,
                time_to_expiry=trade.time_to_expiry,
                volatility=trade.volatility,
                pv=pv,
                delta=delta,
                vega=vega
            )
            priced_trades.append(priced_trade)
        
        return priced_trades
    
    def _calculate_d1_d2(self, trade: ValidatedTrade) -> tuple[float, float]:
        """
        Calculate d1 and d2 parameters for Black-Scholes formula.
        
        Args:
            trade: Validated trade
            
        Returns:
            Tuple of (d1, d2)
        """
        S = trade.spot
        K = trade.strike
        T = trade.time_to_expiry
        r_d = trade.domestic_rate
        r_f = trade.foreign_rate
        sigma = trade.volatility
        
        d1 = (np.log(S / K) + (r_d - r_f + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        return d1, d2
    
    def _calculate_pv(self, trade: ValidatedTrade) -> float:
        """
        Calculate present value of the option.
        
        Args:
            trade: Validated trade
            
        Returns:
            Present value in notional currency
        """
        S = trade.spot
        K = trade.strike
        T = trade.time_to_expiry
        r_d = trade.domestic_rate
        r_f = trade.foreign_rate
        N = trade.notional
        
        d1, d2 = self._calculate_d1_d2(trade)
        
        # Discount factors
        df_domestic = np.exp(-r_d * T)
        df_foreign = np.exp(-r_f * T)
        
        if trade.option_type == OptionType.CALL:
            # Call option: S * exp(-r_f * T) * N(d1) - K * exp(-r_d * T) * N(d2)
            pv_per_unit = S * df_foreign * norm.cdf(d1) - K * df_domestic * norm.cdf(d2)
        else:  # PUT
            # Put option: K * exp(-r_d * T) * N(-d2) - S * exp(-r_f * T) * N(-d1)
            pv_per_unit = K * df_domestic * norm.cdf(-d2) - S * df_foreign * norm.cdf(-d1)
        
        # Multiplying by notional
        pv = pv_per_unit * N
        
        return pv
    
    def _calculate_delta(self, trade: ValidatedTrade) -> float:
        """
        Calculate Delta: sensitivity of PV to changes in spot rate.
        
        Delta = ∂PV/∂S
        
        Args:
            trade: Validated trade
            
        Returns:
            Delta in notional currency per unit move in spot
        """
        T = trade.time_to_expiry
        r_f = trade.foreign_rate
        N = trade.notional
        
        d1, _ = self._calculate_d1_d2(trade)
        
        # Discount factor for foreign currency
        df_foreign = np.exp(-r_f * T)
        
        if trade.option_type == OptionType.CALL:
            # Call delta: exp(-r_f * T) * N(d1)
            delta_per_unit = df_foreign * norm.cdf(d1)
        else:  # PUT
            # Put delta: -exp(-r_f * T) * N(-d1) = exp(-r_f * T) * (N(d1) - 1)
            delta_per_unit = df_foreign * (norm.cdf(d1) - 1)
        
        # Multiply by notional
        delta = delta_per_unit * N
        
        return delta
    
    def _calculate_vega(self, trade: ValidatedTrade) -> float:
        """
        Calculate Vega: sensitivity of PV to changes in volatility.
        
        Vega = ∂PV/∂σ
        
        Note: Vega is typically quoted per 1% change in volatility.
        
        Args:
            trade: Validated trade
            
        Returns:
            Vega in notional currency per 1% change in volatility
        """
        S = trade.spot
        T = trade.time_to_expiry
        r_f = trade.foreign_rate
        N = trade.notional
        
        d1, _ = self._calculate_d1_d2(trade)
        
        # Discount factor for foreign currency
        df_foreign = np.exp(-r_f * T)
        
        # Vega is the same for calls and puts
        # Vega = S * exp(-r_f * T) * n(d1) * sqrt(T)
        # where n(d1) is the standard normal PDF
        vega_per_unit = S * df_foreign * norm.pdf(d1) * np.sqrt(T)
        
        # Multiply by notional and dividing by 100 to express per 1% change in volatility
        vega = vega_per_unit * N / 100
        
        return vega