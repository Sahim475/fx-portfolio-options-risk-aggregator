"""
FX Options Portfolio Risk Aggregator
Main orchestration module
"""
from pathlib import Path
from typing import Optional
import sys

from services.data_loader import DataLoaderService
from services.validator import ValidationService
from services.pricing_engine import PricingEngineService
from services.aggregator import AggregationService
from services.output_writer import OutputWriterService
from config import Config


class FXOptionsRiskAggregator:
    """
    Main orchestrator for FX options portfolio risk aggregation.
    Coordinates all services to process trades from input to output.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.data_loader = DataLoaderService()
        self.validator = ValidationService()
        self.pricing_engine = PricingEngineService()
        self.aggregator = AggregationService()
        self.output_writer = OutputWriterService()
    
    def run(self, input_file: Path, output_file: Optional[Path] = None) -> None:
        """
        Executing full risk aggregation pipeline.
        
        Args:
            input_file: Path to input Excel file with trade data
            output_file: Optional path for output file. If None, generates default name.
        """
        print(f"Starting FX Options Risk Aggregation...")
        print(f"Input file: {input_file}")
        
        # Step 1: Load data
        print("\n[1/5] Loading trade data...")
        raw_trades = self.data_loader.load_from_excel(input_file)
        print(f"Loaded {len(raw_trades)} trades")
        
        # Step 2: Validate data
        print("\n[2/5] Validating trades...")
        validation_result = self.validator.validate_trades(raw_trades)
        
        if not validation_result.is_valid:
            print(f"\n Validation failed with {len(validation_result.errors)} errors:")
            for error in validation_result.errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(validation_result.errors) > 10:
                print(f"  ... and {len(validation_result.errors) - 10} more errors")
            sys.exit(1)
        
        validated_trades = validation_result.valid_trades
        print(f" All {len(validated_trades)} trades validated successfully")
        
        # Step 3: Price trades
        print("\n[3/5] Pricing trades...")
        priced_trades = self.pricing_engine.price_portfolio(validated_trades)
        print(f"✓ Priced {len(priced_trades)} trades")
        
        # Step 4: Aggregate results
        print("\n[4/5] Aggregating portfolio metrics..")
        portfolio_summary = self.aggregator.aggregate_portfolio(
            priced_trades=priced_trades,
            valuation_date=self.config.valuation_date,
            reporting_currency=self.config.reporting_currency
        )
        
        # Step 5: Write output
        print("\n[5/5] Writing results..")
        if output_file is None:
            output_file = input_file.parent / f"{input_file.stem}_results.xlsx"
        
        self.output_writer.write_results(
            priced_trades=priced_trades,
            portfolio_summary=portfolio_summary,
            output_file=output_file
        )
        
        print(f"\n Results written to: {output_file}")
        
        # Display summary
        print("\n" + "="*60)
        print("PORTFOLIO SUMMARY")
        print("="*60)
        print(f"Total Trades:        {portfolio_summary.total_trades}")
        print(f"Total PV ({portfolio_summary.reporting_currency}):    {portfolio_summary.total_pv:,.2f}")
        print(f"Total Delta ({portfolio_summary.reporting_currency}): {portfolio_summary.total_delta:,.2f}")
        print(f"Total Vega ({portfolio_summary.reporting_currency}):  {portfolio_summary.total_vega:,.2f}")
        print("="*60)


def main():
    """Main entry point for the application."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="FX Options Portfolio Risk Aggregator"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to input Excel file containing trade data"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Path to output Excel file (default: input_file_results.xlsx)"
    )
    
    args = parser.parse_args()
    
    if not args.input_file.exists():
        print(f"Error: Input file not found: {args.input_file}")
        sys.exit(1)
    
    config = Config()
    aggregator = FXOptionsRiskAggregator(config)
    
    try:
        aggregator.run(args.input_file, args.output)
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
