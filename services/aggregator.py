"""
Aggregation service for computing portfolio-level metrics.
"""
from typing import List
from datetime import date

from models import PricedTrade, PortfolioSummary


class AggregationService:
    """
    Service responsible for aggregating trade-level results 
    into portfolio-level risk metrics.
    """
    
    def aggregate_portfolio(
        self, 
        priced_trades: List[PricedTrade],
        valuation_date: date = None,
        reporting_currency: str = "USD"
    ) -> PortfolioSummary:
        """
        Aggregate priced trades into portfolio summary.
        
        Args:
            priced_trades: List of priced trades
            valuation_date: Valuation date for the portfolio
            reporting_currency: Currency to aggregate results into
            
        Returns:
            PortfolioSummary with aggregated metrics
        """
        if valuation_date is None:
            valuation_date = date.today()
        
        # Portfolio total sums
        total_pv = 0.0
        total_delta = 0.0
        total_vega = 0.0
        
        for trade in priced_trades:
            total_pv += self._to_reporting_currency(trade.pv, trade, reporting_currency)
            total_delta += self._to_reporting_currency(trade.delta, trade, reporting_currency)
            total_vega += self._to_reporting_currency(trade.vega, trade, reporting_currency)
        
        return PortfolioSummary(
            total_trades=len(priced_trades),
            total_pv=total_pv,
            total_delta=total_delta,
            total_vega=total_vega,
            valuation_date=valuation_date,
            reporting_currency=reporting_currency
        )

    def _to_reporting_currency(
        self,
        amount: float,
        trade: PricedTrade,
        reporting_currency: str
    ) -> float:
        """
        Convert a trade amount into the reporting currency.
        USD and JPY for USDJPY pairs; other pairs assumed USD notionals.
        """
        trade_ccy = trade.notional_currency.upper()
        reporting_currency = reporting_currency.upper()
        
        # Reporting Currency
        if trade_ccy == reporting_currency:
            return amount
        
        # USD/JPY conversion using spot
        if trade.currency_pair == "USDJPY":
            if trade_ccy == "JPY" and reporting_currency == "USD":
                return amount / trade.spot
            if trade_ccy == "USD" and reporting_currency == "JPY":
                return amount * trade.spot
        
        raise ValueError(
            f"Unsupported conversion {trade_ccy}->{reporting_currency} for {trade.currency_pair}"
        )
