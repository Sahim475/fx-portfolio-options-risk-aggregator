
# FX Options Portfolio Risk Aggregator

A small Python application for pricing and aggregating FX options portfolios using the Black-Scholes model. This system integrates quantitative modelling, software engineering and data validation along with multi currncy handling
---

## Overview

The FX Options Portfolio Risk Aggregator:

* Reads FX options portfolios from Excel files
* Validates trade data using **Pydantic models** with business-logic checks
* Prices each option using the **Black–Scholes FX model**
* Computes key risk metrics:

  * Present Value (PV)
  * Delta
  * Vega
* Converts all metrics into a **unified reporting currency**
* Aggregates results at the portfolio level
* Exports detailed trade level and portfolio level results to Excel

---

## Architecture

The application follows a **Service-Oriented Architecture**, ensuring a clear separation of concerns.

![System architecture](architecture.png)

### Key Components

#### 1. Domain Models (`models.py`)

* **RawTrade**: Accepts loosely typed input data
* **ValidatedTrade**: Strongly typed, validated trade ready for pricing
* **PricedTrade**: Trade with computed risk metrics in notional currency
* **PortfolioSummary**: Aggregated portfolio-level metrics in reporting currency

#### 2. Services

* **DataLoaderService**: Reads Excel files and parses raw trade data
* **ValidationService**: Applies structural and business-logic validation
* **PricingEngineService**: Implements FX Black–Scholes pricing
* **AggregationService**: Performs currency conversion and aggregation
* **OutputWriterService**: Writes formatted Excel outputs

#### 3. Configuration (`config.py`)

* Centralised valuation parameters
* Market conventions and assumptions
* Reporting currency (default: USD)

---

## Quantitative Model

### Black–Scholes for FX Options

The pricing engine implements the **Garman Kohlhagen** model.

#### Call Option Present Value

```math
C = S \cdot e^{-r_f T} \cdot N(d_1) - K \cdot e^{-r_d T} \cdot N(d_2)
```

#### Put Option Present Value

```math
P = K \cdot e^{-r_d T} \cdot N(-d_2) - S \cdot e^{-r_f T} \cdot N(-d_1)
```

#### Where

* `S`:    Spot FX rate
* `K`:    Strike price
* `T`:    Time to expiry (in years)
* `r_d`:  Domestic risk-free rate
* `r_f`:  Foreign risk-free rate
* `σ`:    Implied volatility
* `N(·)`: Cumulative standard normal distribution

The auxiliary terms are defined as:

* $d_1 = \frac{\ln(S/K) + (r_d - r_f + \sigma^2 / 2), T}{\sigma \sqrt{T}}$
* $d_2 = d_1 - \sigma \sqrt{T}$

---

## Greeks Computation

### Delta (Δ)

Sensitivity of option value to changes in the spot FX rate.

```math
\text{Call Delta} = e^{-r_f T} \cdot N(d_1) \cdot \text{Notional}
```

```math
\text{Put Delta} = e^{-r_f T} \cdot \bigl[N(d_1) - 1\bigr] \cdot \text{Notional}
```

---

### Vega (ν)

Sensitivity of option value to a **1% change in volatility**.

```math
\text{Vega}
= \frac{S \cdot e^{-r_f T} \cdot n(d_1) \cdot \sqrt{T} \cdot \text{Notional}}{100}
```

where `n(·)` is the **standard normal probability density function**.

---

## Multi Currency Handling

The system supports portfolios containing trades with different **notional currencies** (e.g. USD, JPY).

### Currency Conversion Logic

* Trades are priced in their **notional currency**
* Before aggregation, all PVs, Deltas, and Vegas are converted into the **reporting currency**

**Conversion factors:**

* USD → USD: factor = 1
* JPY → USD: factor = 1 / spot
* USD → JPY: factor = spot

All portfolio totals are reported in the configured reporting currency.

---

## Installation

### Requirements

* Python 3.9+
* Dependencies:

  * `pandas`
  * `openpyxl`
  * `pydantic`
  * `numpy`
  * `scipy`
  * `python-dateutil`

### Setup

```bash
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
```

---

## Usage

### Run the Aggregator

```bash
python main.py fx_trades__1_.xlsx
```

Or specify a custom output file:

```bash
python main.py fx_trades__1_.xlsx -o trade_results.xlsx
```

---

## Output

The generated Excel file contains two sheets:

### Trade_Results

* TradeID
* CurrencyPair
* OptionType
* Strike
* Notional
* NotionalCurrency
* Spot
* TimeToExpiry
* Volatility
* PV
* Delta
* Vega

### Portfolio_Summary

* Total Trades
* Total PV (reporting currency)
* Total Delta (reporting currency)
* Total Vega (reporting currency)
* Valuation Date

---

## Input File Format

The input Excel file should contain:

* TradeID
* Underlying
* Notional
* NotionalCurrency
* Spot
* Strike
* Vol
* RateDomestic
* RateForeign
* Expiry
* OptionType

---

## Testing

Unit tests cover:

* Black–Scholes pricing accuracy 
* Put–call parity
* Delta and Vega correctness
* Trade validation rules
* Portfolio aggregation logic
* Error handling and edge cases

Tests are designed to validate both **quantitative correctness** and **system robustness**.

---

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
---

## Assumptions

### Market Assumptions
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

### Currency Conversion

- Spot rates are used for currency conversion (no forward adjustment)
- Conversion assumes mid market rates with no spreads
- For USD/JPY trades:
  - JPY notional → USD: divide by spot
  - USD notional → JPY: multiply by spot
- All portfolio aggregations are in reporting currency

### Data Assumptions

* Market data is observable and reliable
* No counterparty or credit risk

## Key Implementation Details

### Currency Conversion in AggregationService
The `AggregationService.aggregate_portfolio()` method performs the following steps:
1. **Iterate through priced trades** (each in its own notional currency)
2. **Apply conversion factor** based on currency pair and reporting currency
3. **Convert PV, Delta, and Vega** to reporting currency
4. **Sum converted values** across all trades


