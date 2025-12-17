"""
Data loading service for reading trade data from Excel files.
"""
from pathlib import Path
from typing import List
import pandas as pd

from models import RawTrade


class DataLoaderService:
    """
    Service responsible for loading trade data from external sources.
    Currently supports Excel files with specific schema.
    """
    
    REQUIRED_COLUMNS = [
        'TradeID', 'Underlying', 'Notional', 'NotionalCurrency',
        'Spot', 'Strike', 'Vol', 'RateDomestic', 'RateForeign',
        'Expiry', 'OptionType'
    ]
    
    def load_from_excel(self, file_path: Path) -> List[RawTrade]:
        """
        Load trades from an Excel file.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            List of RawTrade objects
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If required columns are missing
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read Excel file
        df = pd.read_excel(file_path, sheet_name=0)
        
        # Validate required columns
        missing_columns = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_columns:
            raise ValueError(
                f"Missing required columns: {missing_columns}. "
                f"Required columns are: {self.REQUIRED_COLUMNS}"
            )
        
        # Convert DataFrame rows to RawTrade objects
        raw_trades = []
        for idx, row in df.iterrows():
            try:
                trade = RawTrade(
                    TradeID=str(row['TradeID']),
                    Underlying=str(row['Underlying']).strip(),
                    Notional=float(row['Notional']),
                    NotionalCurrency=str(row['NotionalCurrency']).strip().upper(),
                    Spot=float(row['Spot']),
                    Strike=float(row['Strike']),
                    Vol=float(row['Vol']),
                    RateDomestic=float(row['RateDomestic']),
                    RateForeign=float(row['RateForeign']),
                    Expiry=float(row['Expiry']),
                    OptionType=str(row['OptionType']).strip().upper()
                )
                raw_trades.append(trade)
            except Exception as e:
                raise ValueError(f"Error parsing row {idx + 2}: {e}")
        
        return raw_trades