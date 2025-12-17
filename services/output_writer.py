"""
Output writer service for exporting results to Excel.
"""
from pathlib import Path
from typing import List
import pandas as pd

from models import PricedTrade, PortfolioSummary


class OutputWriterService:
    """
    Service responsible for writing results to output files.
    """
    
    def write_results(
        self,
        priced_trades: List[PricedTrade],
        portfolio_summary: PortfolioSummary,
        output_file: Path
    ) -> None:
        """
        Write priced trades and portfolio summary to Excel file.
        
        Args:
            priced_trades: List of priced trades
            portfolio_summary: Portfolio aggregated metrics
            output_file: Path to output Excel file
        """
        # Convert priced trades to DataFrame
        trades_data = []
        for trade in priced_trades:
            trades_data.append({
                'TradeID': trade.trade_id,
                'CurrencyPair': trade.currency_pair,
                'OptionType': trade.option_type,
                'Strike': trade.strike,
                'Notional': trade.notional,
                'NotionalCurrency': trade.notional_currency,
                'Spot': trade.spot,
                'TimeToExpiry': trade.time_to_expiry,
                'Volatility': trade.volatility,
                'PV': round(trade.pv, 2),
                'Delta': round(trade.delta, 2),
                'Vega': round(trade.vega, 2)
            })
        
        df_trades = pd.DataFrame(trades_data)
        
        # Portfolio summary DataFrame
        summary_data = {
            'Metric': [
                'Total Trades',
                f"Total PV ({portfolio_summary.reporting_currency})",
                f"Total Delta ({portfolio_summary.reporting_currency})",
                f"Total Vega ({portfolio_summary.reporting_currency})",
                'Valuation Date'
            ],
            'Value': [
                portfolio_summary.total_trades,
                round(portfolio_summary.total_pv, 2),
                round(portfolio_summary.total_delta, 2),
                round(portfolio_summary.total_vega, 2),
                portfolio_summary.valuation_date.isoformat()
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        
        # Write to Excel 
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df_trades.to_excel(writer, sheet_name='Trade_Results', index=False)
            df_summary.to_excel(writer, sheet_name='Portfolio_Summary', index=False)
            
            # Column width adjustments
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
