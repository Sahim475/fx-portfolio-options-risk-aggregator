# FX Options Portfolio Risk Aggregator
A small Python application for pricing and aggregating FX options portfolios using the Black-Scholes model. This system integrates quantitative modelling, software engineering and data validation along with multi currncy handling

# Overview
The FX Options Portfolio Risk Aggregator:
- Reads a portfolio of FX options from Excel files
- Validates trade data using Pydantic models with comprehensive business logic checks
- Prices each option using the Black-Scholes for FX model
- Computes risk metrics: Present Value (PV), Delta, and Vega
-  **Converts all metrics to a unified reporting currency**
-  Aggregates results at the portfolio level in the reporting currency
-  Exports detailed results to Excel

## Architecture
The application follows a **Service Oriented Architecture** with clear separation of concerns:

![System architecture](architecture.png)

### Key Components

### 1. ##Domain Models## ('models.py')
- `RawTrade`: Accepts loosely-typed input data
- `ValidatedTrade`: Strongly-typed, validated trade ready for pricing
- `PricedTrade`: Trade with computed risk metrics in original currency
- `PortfolioSummary`: Aggregated portfolio-level results in reporting currency

#### 2. **Services**
- **DataLoaderService**: Reads Excel files and parses trade data
- **ValidationService**: Transforms raw data into validated trades with business logic checks
- **PricingEngineService**: Implements Black-Scholes pricing for FX options
- **AggregationService**: Converts multi-currency metrics to reporting currency and computes portfolio level totals
- **OutputWriterService**: Exports results to Excel with currency labels

#### 3. **Configuration** (`config.py`)
- Centralised settings for valuation date, conventions, and parameters
- **Reporting currency specification** (default: USD)

## Quantitative Model

### Black Scholes for FX Options

The pricing engine implements the Garman Kohlhagen model:

**Call Option PV:**
$$
C = S \cdot e^{-r_f T} \cdot N(d_1) - K \cdot e^{-r_d T} \cdot N(d_2)
$$

**Put Option PV:**
$$
P = K \cdot e^{-r_d T} \cdot N(-d_2) - S \cdot e^{-r_f T} \cdot N(-d_1)
$$

Where:
- `S`: Spot rate
- `K`: Strike price
- `T`: Time to expiry (years)
- `r_d`: Domestic risk-free rate
- `r_f`: Foreign risk-free rate
- `σ`: Implied volatility
- `d1`: $\frac{\ln(S/K) + (r_d - r_f + \sigma^2 / 2)\, T}{\sigma \sqrt{T}}$
- `d2 = d1 - σ·√T`
- `N(·)`: Cumulative standard normal distribution

### Greeks Computation

**Delta (Δ):** Sensitivity to spot rate changes
$$
\text{Call Delta} = e^{-r_f T} \cdot N(d_1) \cdot \text{Notional}
$$

$$
\text{Put Delta} = e^{-r_f T} \cdot \bigl[N(d_1) - 1\bigr] \cdot \text{Notional}
$$

**Vega (ν):** Sensitivity to volatility changes (per 1%)
$$
\text{Vega}
= \frac{S \cdot e^{-r_f T} \cdot n(d_1) \cdot \sqrt{T} \cdot \text{Notional}}{100}
$$
where `n(·)` is the standard normal probability density function.

### Multi-Currency Handling
The aggregator properly handles portfolios with trades in different notional currencies (USD, JPY, etc.).

**Currency Conversion Logic:**
- Each trade is priced in its notional currency (USD or JPY)
- Before aggregation, all PVs, Deltas, and Vegas are converted to the reporting currency
**Conversion factors:**
  - USD → USD: factor = 1
  - JPY → USD: factor = 1 / spot rate 
  - USD → JPY: factor = spot rate

## Installation

### Requirements
- Python 3.9+
- Dependencies:
  - `pandas` (Excel I/O)
  - `openpyxl` (Excel engine)
  - `pydantic` (data validation)
  - `numpy` (numerical computing)
  - `scipy` (statistical functions)
  - `python-dateutil` (date parsing)

### Setup
```bash
# Create virtual environment
python -m venv venv
# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/MacOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```
## Usage

### 2. Run the Aggregator

Process a portfolio of trades:
```bash
python main.py fx_trades__1_.xlsx 
```
Or specify a custom output file:
```bash
python main.py fx_trades__1_.xlsx -o trade_results.xlsx
```
### 3. Review Results

The output Excel file contains two sheets:

**Trade_Results:**
This has the following columns
- TradeID
- CurrencyPair
- OptionType
- Strike
- Notional
- NotionalCurrency
- Spot
- TimeToExpiry
- Volatility
- PV
- Delta
- Vega

**Portfolio_Summary**:
This has the following metrics
- Total Trades
- Total PV (USD)
- Total Delta (USD)
- Total Vega (USD)
- Valuation Date

All portfolio totals are expressed in the reporting currency. 

## Input File Format

The input Excel file should contain the following
- TradeID
- Underlying
- Notional
- NotionalCurrency
- Spot
- Strike
- Vol
- RateDomestic
- RateForeign
- Expiry
- OptionType

## Input File Location

Place the file in the same directory as main.py and then run:

```bash
python main.py fx_trades__1_.xlsx
```

or place elsewhere and specify full path

The application will automatically create an output file in the same directory as the input file, with `_results` appended to the filename.

## Testing

Tests cover:
- Black-Scholes pricing accuracy (ATM, ITM, OTM options)
- Put-call parity validation
- Delta and Vega calculations
- Data validation logic
- Portfolio aggregation
- Edge cases and error handling

### Test Coverage

- ATM call/put option pricing
- Deep ITM option pricing (intrinsic value validation)
- OTM option pricing
- Call delta (positive) and put delta (negative)
- Vega computation (always positive)
- Put-call parity relationship
- Trade validation (valid and invalid cases)
- Business logic validation (expired options, negative strikes)
- Portfolio aggregation with currency conversion

## Design Principles

### 1. **Separation of Concerns**
Each service has a single, defined responsibility:
- Data loading is isolated from validation
- Pricing logic is independent of I/O
- Currency conversion is handled in aggregation layer

### 2. **Type Safety**
- Full type hints throughout
- Pydantic models ensure integrity of data at each pipeline stage
- Catches errors at validation time

### 3. **Fail Fast Validation**
- Comprehensive validation with clear error messages
- Business logic checks
- Range validation

### 4. **Multi-Currency Awareness**
- FX conversion at aggregation stage
- Prevents mixing currencies in portfolio totals
- Clear labelling of reporting currency in outputs
- Accurate representation of cross currency portfolios

### 5. **Testability**
- Pure functions for pricing calculations
- Services accept dependency injection
- Comprehensive unit test coverage

### 6. **Data Transformations**
```
RawTrade → ValidatedTrade → PricedTrade → Converted → Output
```
Each stage represents a clear transformation with explicit types.

### 7. **Output**
- Multi sheet Excel files with formatted results
- Auto adjusted column widths
- Currency-labeled portfolio summaries

## Assumptions

### Market
- **Time to Expiry:** Specified directly in years 
- **Rates:** Continuously compounded risk-free rates (decimal format)
- **Volatility:** Implied volatility (decimal format)
- **Notional Currency:** Either USD or JPY depending on the currency pair
- **Reporting Currency:** Default is USD (can configure in config.py)

### Pricing Assumptions
- European style options
- No transaction costs
- No bid spreads
- Continuous trading and no arbitrage opportunities
- Log normal distribution of spot rates
- Constant volatility and interest rates

### Currency Conversion Assumptions
- Spot rates are used for currency conversion (no forward adjustment)
- Conversion assumes mid market rates with no spreads
- For USD/JPY trades:
  - JPY notional → USD: divide by spot
  - USD notional → JPY: multiply by spot
- All portfolio aggregations are in reporting currency

### Data Assumptions
- All trades are valid and settled
- Market data (spot, rates, vol) is observable and reliable
- No credit risk or counterparty default

## Key Implementation Details

### Currency Conversion in AggregationService
The `AggregationService.aggregate_portfolio()` method performs the following steps:
1. **Iterate through priced trades** (each in its own notional currency)
2. **Apply conversion factor** based on currency pair and reporting currency
3. **Convert PV, Delta, and Vega** to reporting currency
4. **Sum converted values** across all trades
