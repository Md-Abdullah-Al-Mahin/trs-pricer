# **Project Outline: Total Return Swap (TRS) Pricing Simulator**

## **1. Project Overview & Objective**
Build a Python-based simulation engine for a single-stock Total Return Swap (TRS), the foundational instrument in synthetic prime brokerage. This tool models the periodic cash flows between a prime brokerage desk and a hedge fund client, calculating the net economics and key risk metrics. The goal is a practical, educational model that demonstrates how synthetics provide leveraged exposure and how the desk manages funding and market risks.

The codebase uses a **class-based architecture**: each domain (market data, simulation, cash flows, valuation, visualization, orchestration) is implemented as a dedicated class with clear interfaces.

---

## **2. Core Technical Requirements & Specifications**

### **2.1. Input Parameters (User-Defined Variables)**
Configurable parameters:

*   **Reference Asset**: `ticker` (e.g. `"AAPL"`)
*   **Trade Terms**:
    *   `notional`: Principal amount of the swap (e.g. `10_000_000`)
    *   `initial_price`: Stock price at trade inception (**auto-fetched** if not provided)
    *   `dividend_yield`: **Auto-fetched** via yfinance (TTM dividends / price). Fallback: user input or config default.
*   **Funding & Rates**:
    *   `benchmark_rate`: Annual risk-free rate (e.g. `0.05` for 5%). **User-provided or config default** (`config.DEFAULT_BENCHMARK_RATE`). No FRED integration in current implementation.
    *   `funding_spread`: **Estimated automatically** via a hybrid multi-factor model (beta, volatility, market cap, sector, leverage) using yfinance. Fallback: config default.
    *   `effective_funding_rate`: `benchmark_rate + funding_spread` (computed internally).
*   **Simulation Settings**:
    *   `tenor`: Swap duration in years (e.g. `1`)
    *   `payment_frequency`: Coupon periods per year (e.g. `4` for quarterly)
    *   `num_simulations`: Number of GBM price-path scenarios (e.g. `1000`)
*   **Market Assumptions**:
    *   `volatility`: **Auto-fetched** from yfinance (info, option-chain ATM IV, or historical log-return vol). Fallback: user input or config default.

### **2.1.1. Market Data Sources & Fetching Logic (Current Implementation)**

All market data is provided by **yfinance**. There is no FRED or other external API in the current implementation.

| Parameter | Data Source | Implementation | Fallback |
|-----------|-------------|----------------|----------|
| `initial_price` | Current stock price | `MarketDataFetcher.fetch_current_price(ticker)` | User input |
| `dividend_yield` | TTM dividends / price | `MarketDataFetcher.fetch_dividend_yield(ticker)` | User input or `config.DEFAULT_DIVIDEND_YIELD` |
| `benchmark_rate` | — | Not fetched | User input or `config.DEFAULT_BENCHMARK_RATE` |
| `funding_spread` | Hybrid model (beta, vol, cap, sector, leverage) | `MarketDataFetcher.estimate_funding_spread(ticker)` | User input or `config.DEFAULT_FUNDING_SPREAD` |
| `volatility` | yfinance (info, options IV, or historical returns) | `MarketDataFetcher.fetch_historical_volatility(ticker)` | User input or `config.DEFAULT_VOLATILITY` |

**Funding spread (hybrid model):**  
Base spread is adjusted by (1) additive terms: beta and volatility vs baseline, (2) multiplicative factors: market cap, sector/industry, and debt-to-equity. See `market_data.MarketDataFetcher` for details.

**Config** (`config.py`) defines `DEFAULT_BENCHMARK_RATE`, `DEFAULT_FUNDING_SPREAD`, `DEFAULT_VOLATILITY`, `DEFAULT_DIVIDEND_YIELD`, and related constants. FRED series IDs are present in config for possible future use but are not used by the current market data implementation.

### **2.2. Mathematical & Financial Modeling Logic**

**A. Simulate Future Stock Price Paths (GBM)**  
*   `dt = 1 / payment_frequency` (time step per period).
*   For each simulation `i` and period `t`:  
    `price_path[i, t] = price_path[i, t-1] * exp((mu - 0.5*volatility²)*dt + volatility*sqrt(dt)*Z)`  
    with `mu = benchmark_rate` for risk-neutral valuation, `Z` standard normal.

**B. Periodic Cash Flows (per path and period)**  
*   **Total Return Leg (Desk → Client):**  
    Appreciation + dividends:  
    `(period_end - period_start)/period_start * notional + (dividend_yield / payment_frequency) * notional`  
*   **Funding Leg (Client → Desk):**  
    `(effective_funding_rate / payment_frequency) * notional`  
    (fixed payment regardless of stock movement; depreciation is handled in the total return leg).  
*   **Net (to Desk):**  
    `net_cash_flow = net_funding_cash_flow - total_return_cash_flow`

**C. Valuation & Risk**  
*   **NPV:** Discount each path’s `net_cash_flow` at `benchmark_rate`; report mean, std, percentiles.  
*   **EPE:** At each future date, average of `max(0, MTM)` across paths (MTM = PV of remaining cash flows from desk’s perspective).

---

## **3. Class-Based Architecture**

The project is structured around the following classes:

| Module | Class | Role |
|--------|-------|------|
| `market_data` | `MarketDataFetcher` | Fetch price, dividend yield, volatility, funding spread (yfinance + hybrid model). Optional ticker caching. |
| `simulation` | `SimulationEngine` | GBM price path simulation. `calculate_time_step`, `simulate_price_paths`. |
| `cash_flows` | `CashFlowEngine` | Total return leg, funding leg, net flows. `calculate_total_return_leg`, `calculate_funding_leg`, `calculate_cash_flows`. |
| `valuation` | `ValuationEngine` | NPV, MTM, EPE, aggregation. `calculate_npv`, `calculate_marked_to_market_value`, `calculate_exposure_metrics`, `aggregate_results`. |
| `visualization` | `TRSVisualizer` | Plots. `plot_simulated_price_paths`, `plot_npv_distribution`, `plot_epe_profile`, `plot_cash_flow_analysis`. |
| `trs_pricer` | `TRSPricer` | Orchestrator. `get_user_inputs`, `run_simulation`, `generate_summary_report`. Uses the above classes (or injected equivalents). |

---

## **4. Sample Usage & Expected Output**

### **Class-based usage**

```python
from market_data import MarketDataFetcher
from simulation import SimulationEngine
from cash_flows import CashFlowEngine
from valuation import ValuationEngine
from visualization import TRSVisualizer
from trs_pricer import TRSPricer, run_simulation, generate_summary_report
import matplotlib.pyplot as plt

# Optional: custom components
fetcher = MarketDataFetcher(enable_cache=True)
pricer = TRSPricer(market_data_fetcher=fetcher)

# Minimal params – dividend_yield, volatility, funding_spread auto-fetched
params = {
    "ticker": "MSFT",
    "notional": 5_000_000,
    "tenor": 2,
    "payment_frequency": 4,
    "num_simulations": 5000,
}

# Run simulation
summary_results, figs = pricer.run_simulation(params)
report = pricer.generate_summary_report(summary_results)
print(report)
for fig in figs:
    plt.show()
```

### **Manual overrides**

```python
params_manual = {
    "ticker": "MSFT",
    "notional": 5_000_000,
    "initial_price": 420.0,
    "dividend_yield": 0.008,
    "benchmark_rate": 0.05,
    "funding_spread": 0.02,
    "tenor": 2,
    "payment_frequency": 4,
    "volatility": 0.25,
    "num_simulations": 5000,
}
pricer = TRSPricer()
summary_results, figs = pricer.run_simulation(params_manual)
report = pricer.generate_summary_report(summary_results)
print(report)
for fig in figs:
    plt.show()
```

### **Expected console output (snippet)**

```
=== TRS Pricing Simulation Results ===
Reference Asset: MSFT
Notional: $5,000,000
Tenor: 2 years
----------------------------------------
Market Data (Auto-Fetched):
  Initial Price: $420.35 (from yfinance)
  Dividend Yield: 0.82% (yfinance)
  Historical Volatility: 24.3% (yfinance)
  Benchmark Rate: 5.00% (config default)
  Funding Spread: 1.85% (hybrid model)
  Effective Funding Rate: 6.85%
----------------------------------------
Valuation (Desk's Perspective):
  Expected NPV: +$42,150
  Std Dev of NPV: $185,250
  5th Percentile NPV: -$225,400
  95th Percentile NPV: +$310,800
----------------------------------------
Risk Metrics:
  Peak EPE (at 1.25 years): $155,200
```

Exact numbers depend on market data and simulation seed. Benchmark and spread lines reflect **config default** and **hybrid model** as in the current implementation.

---

## **5. Implementation Order & Dependencies**

### **Current Implementation Status**

✅ **Completed:**
- **`config.py`** - Constants, defaults, and FRED series IDs (for future use)
- **`market_data.py` → `MarketDataFetcher`** - Fully implemented with:
  - `fetch_current_price` - Gets current stock price from yfinance
  - `fetch_dividend_yield` - Calculates TTM dividend yield
  - `fetch_historical_volatility` - Multi-source volatility (info, options IV, historical returns)
  - `estimate_funding_spread` - Hybrid multi-factor model (beta, vol, market cap, sector, leverage)
  - Ticker caching for performance

- **`simulation.py` → `SimulationEngine`** - Fully implemented with:
  - `calculate_time_step(tenor, payment_frequency)` - Returns `1 / payment_frequency`
  - `simulate_price_paths(...)` - GBM simulation using risk-neutral drift:
    - `dt = 1 / payment_frequency`
    - For each path: `price[t] = price[t-1] * exp((mu - 0.5*vol²)*dt + vol*sqrt(dt)*Z)`
    - `mu = benchmark_rate` (risk-neutral), `Z ~ N(0,1)`
    - Returns `np.ndarray` of shape `(num_simulations, num_periods + 1)`

- **`cash_flows.py` → `CashFlowEngine`** - Fully implemented with:
  - `calculate_total_return_leg(...)` - Calculates appreciation + dividends (desk → client)
  - `calculate_funding_leg(...)` - Calculates fixed funding payment (client → desk)
  - `calculate_cash_flows(price_paths, params)` - Computes cash flows for all paths and periods
  - Returns `List[pd.DataFrame]` with columns: `period`, `period_start_price`, `period_end_price`, `total_return_cash_flow`, `net_funding_cash_flow`, `net_cash_flow`

- **`trs_pricer.py` → `TRSPricer.get_user_inputs`** - Fully implemented with:
  - Validates required params (`ticker`, `notional`, `tenor`, `payment_frequency`, `num_simulations`)
  - Uses `MarketDataFetcher` to auto-fetch: `initial_price`, `dividend_yield`, `volatility`, `funding_spread`
  - Uses user override or `config.DEFAULT_BENCHMARK_RATE` for `benchmark_rate`
  - Calculates `effective_funding_rate = benchmark_rate + funding_spread`
  - Returns resolved `Dict[str, Any]` with all parameters
  - Includes helper methods for validation and parameter resolution

- **`valuation.py` → `ValuationEngine`** - Fully implemented with:
  - `calculate_npv(cash_flows_series, benchmark_rate, payment_frequency)` - Discounts net cash flows at `benchmark_rate` per period
  - `calculate_marked_to_market_value(...)` - Calculates PV of future cash flows from `current_period` onward
  - `calculate_exposure_metrics(cash_flows_list, params)` - Computes EPE profile: for each period, averages `max(0, MTM)` across all paths
  - `aggregate_results(all_simulated_cash_flows, npv_list)` - Summary statistics: mean/std NPV, percentiles (5th, 25th, 50th, 75th, 95th), mean periodic net cash flows
  - Includes helper method `_discount_cash_flows` for common discounting logic

- **`visualization.py` → `TRSVisualizer`** - Fully implemented with:
  - `plot_simulated_price_paths(...)` - Plots sample price paths over time with mean path overlay
  - `plot_npv_distribution(npv_list)` - Histogram of desk NPV across simulations with mean indicator
  - `plot_epe_profile(epe_profile, dates)` - Line plot of Expected Positive Exposure over time with peak EPE markers
  - `plot_cash_flow_analysis(cash_flows_series, num_simulations_to_plot)` - Net cash flow over periods for sample simulations with mean overlay
  - Each method returns `plt.Figure`
  - Includes helper methods `_create_figure` and `_finalize_plot` for consistent styling

- **`trs_pricer.py` → `TRSPricer.run_simulation`** - Fully implemented with:
  - Complete pipeline orchestration: resolve inputs → simulate paths → cash flows → NPV/EPE → plots
  - Calls `get_user_inputs(params)` to resolve all parameters
  - Uses `SimulationEngine.simulate_price_paths(...)` to generate price paths
  - Uses `CashFlowEngine.calculate_cash_flows(...)` to compute cash flows per path
  - Calculates NPV for each path using `ValuationEngine.calculate_npv(...)`
  - Computes EPE profile using `ValuationEngine.calculate_exposure_metrics(...)`
  - Aggregates results using `ValuationEngine.aggregate_results(...)`
  - Generates all plots using `TRSVisualizer` methods
  - Returns `(summary_results: Dict, figures: List[plt.Figure])`

- **`trs_pricer.py` → `TRSPricer.generate_summary_report`** - Fully implemented with:
  - Formats `summary_results` as console report
  - Includes trade details (ticker, notional, tenor)
  - Displays market data (auto-fetched values with sources)
  - Shows valuation metrics (expected NPV, std dev, percentiles)
  - Reports risk metrics (peak EPE, timing)
  - Returns formatted `str`

- **`main.py`** - Fully implemented with:
  - Main execution function demonstrating minimal parameter usage
  - Manual override example function
  - Error handling for robust execution
  - Uses class-based API: `TRSPricer` instance methods

✅ **All implementation steps completed!**

---

### **Dependencies flow**

```
config.py ✅
    ↓
MarketDataFetcher (market_data) ✅
    ↓
TRSPricer.get_user_inputs ✅
    ↓
SimulationEngine (simulation) ✅
    ↓
CashFlowEngine (cash_flows) ✅
    ↓
ValuationEngine (valuation) ✅
    ↓
TRSVisualizer (visualization) ✅
    ↓
TRSPricer.run_simulation / generate_summary_report ✅
    ↓
main.py ✅
```

**Legend:** ✅ = Completed

---

## **6. Installation & Setup**

### **Prerequisites**
- Python 3.8 or higher
- pip (Python package manager)

### **Installation Steps**

1. **Clone or download the project** to your local machine

2. **Navigate to the project directory:**
   ```bash
   cd trs-pricer
   ```

3. **Create a virtual environment (recommended):**
   
   **On macOS/Linux:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
   
   **On Windows:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
   
   You should see `(venv)` in your terminal prompt, indicating the virtual environment is active.

4. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   This will install:
   - `numpy>=1.24.0` - Numerical computations
   - `pandas>=2.0.0` - Data manipulation
   - `matplotlib>=3.7.0` - Plotting and visualization
   - `yfinance>=0.2.0` - Market data fetching
   - `streamlit>=1.28.0` - Web UI framework (for Streamlit app)

5. **Verify installation:**
   ```bash
   python -c "import numpy, pandas, matplotlib, yfinance, streamlit; print('All dependencies installed successfully!')"
   ```

### **Virtual Environment Notes**

- **Activating the venv**: Always activate the virtual environment before running the project:
  - macOS/Linux: `source venv/bin/activate`
  - Windows: `venv\Scripts\activate`

- **Deactivating the venv**: When you're done, deactivate with:
  ```bash
  deactivate
  ```

- **The `venv/` directory is already in `.gitignore`** and won't be committed to version control.

---

## **7. Running the Project**

### **Option 1: Streamlit Web UI (Recommended)**

The easiest way to run the simulator is through the interactive Streamlit web interface:

1. **Launch the Streamlit app**:
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Open your browser** - Streamlit will automatically open a browser window, or navigate to `http://localhost:8501`

3. **Use the interface**:
   - Enter parameters in the sidebar (ticker, notional, tenor, etc.)
   - Optionally enable manual overrides for market data
   - Click "Run Simulation"
   - View results, metrics, and visualizations in the main area

The Streamlit UI provides:
- ✅ Interactive parameter input with validation
- ✅ Real-time simulation execution with progress indicators
- ✅ Visual display of all results and plots in organized tabs
- ✅ Key metrics dashboard
- ✅ Easy parameter customization
- ✅ Manual override options for market data

### **Option 2: Command Line Interface**

Run the main script with default parameters:

```bash
python main.py
```

This will:
1. Fetch market data for MSFT (Microsoft) automatically
2. Run 5000 Monte Carlo simulations
3. Generate a summary report in the console
4. Display 4 visualization plots (price paths, NPV distribution, EPE profile, cash flow analysis)

### **Customizing Parameters**

Edit `main.py` to customize the simulation parameters:

```python
params = {
    'ticker': 'AAPL',              # Change ticker symbol
    'notional': 10_000_000,        # Change notional amount
    'tenor': 1,                    # Change swap duration (years)
    'payment_frequency': 4,        # Change payment frequency (4 = quarterly)
    'num_simulations': 10000,      # Change number of simulations
}
```

### **Using Manual Overrides**

To use manual parameters instead of auto-fetched market data, modify `main.py` to call `main_manual()`:

```python
if __name__ == "__main__":
    main_manual()  # Use manual parameters
```

Or create your own function with custom parameters:

```python
from trs_pricer import TRSPricer
import matplotlib.pyplot as plt

pricer = TRSPricer()
params = {
    'ticker': 'TSLA',
    'notional': 1_000_000,
    'tenor': 1,
    'payment_frequency': 12,  # Monthly payments
    'num_simulations': 1000,
    'volatility': 0.40,        # Manual override
    'benchmark_rate': 0.04,   # Manual override
}

summary_results, figs = pricer.run_simulation(params)
report = pricer.generate_summary_report(summary_results)
print(report)

for fig in figs:
    plt.show()
```

### **Expected Runtime**

- **Market data fetching**: 2-5 seconds (first run, cached on subsequent runs)
- **Simulation (1000 paths)**: 1-3 seconds
- **Simulation (5000 paths)**: 5-15 seconds
- **Simulation (10000 paths)**: 15-30 seconds
- **Plot generation**: 1-2 seconds

*Note: Runtime depends on network speed for market data and system performance for simulations.*

### **Troubleshooting**

**Issue: Market data fetch fails**
- Check internet connection
- Verify ticker symbol is valid (e.g., 'MSFT', 'AAPL', 'GOOGL')
- Some tickers may have limited data availability

**Issue: Import errors**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version is 3.8 or higher: `python --version`

**Issue: Plots not displaying**
- Ensure matplotlib backend is properly configured
- On headless servers, plots may need to be saved instead of displayed

**Issue: Memory errors with large simulations**
- Reduce `num_simulations` parameter
- Close other applications to free up memory

---
Here is a project extension outline detailing the plan to add hedging recommendation logic to your TRS Pricing Simulator, structured for your README.md.

---

## **Project Extension: Hedging Recommendation Module**

### **1. Extension Overview**
This module adds intelligent hedging recommendations to the TRS simulator. It analyzes the simulated risk exposures from the desk's perspective (whether it is the **Total Return Payer** or **Receiver**) and recommends appropriate financial instruments to mitigate market risk.

trs-pricer/
├── hedging_engine.py          # NEW: Advanced hedging logic
├── instruments/               # NEW: Instrument models
│   ├── futures_model.py
│   ├── swap_model.py
│   └── options_model.py
├── config.py                  # Updated with hedging parameters
└── Existing files (unchanged)

**Core Objective**: Transform the simulator from a pricing/risk engine into a decision-support tool that answers: "Given this TRS trade, how should the desk hedge its market exposure?"

---

### **2. Implementation Plan: Phases & Steps**

#### **Phase 1: Foundation & Parameter Expansion**
*Goal: Extend the core system to support hedging decisions.*

1.  **Define the Desk's Position Parameter**: Add a mandatory `desk_position` parameter (values: `"payer"` or `"receiver"`) to determine the hedge direction.
2.  **Enhance Risk Exposure Metrics**: Modify the `ValuationEngine` to calculate additional metrics crucial for hedging:
    *   **Delta Exposure**: Approximate sensitivity of the TRS NPV to changes in the underlying stock price.
    *   **Funding Rate Exposure**: Isolate the present value of the floating funding leg for interest rate risk.
3.  **Extend Configuration**: Add a new `HedgingConfig` class within `config.py` to store constants (e.g., target option deltas, futures contract sizes, default hedge ratios).

#### **Phase 2: Core Hedging Logic & Instrument Selection**
*Goal: Implement the decision engine that maps desk positions to hedging strategies.*

1.  **Create the `HedgingEngine` Class**: This will be the central orchestrator for all hedging logic.
2.  **Implement the Primary Decision Matrix**:
    | Desk Position | Economic Risk | Recommended Hedge Action |
    | :--- | :--- | :--- |
    | **Total Return Payer**<br>(Pays asset return) | **Short the Asset** | **Long Equity Futures**<br>Directly offsets delta exposure from being short the stock's performance. |
    | **Total Return Receiver**<br>(Receives asset return) | **Long the Asset**<br>**Short the Floating Rate** | **1. Receive-Floating IRS**<br>Hedges the liability of paying the floating funding rate (e.g., SOFR + spread).<br>**2. Long Put Options**<br>Protects against depreciation of the long asset position while retaining upside. |
3.  **Develop Hedge Calculation Methods**:
    *   `_calculate_futures_hedge()`: Calculates the optimal number of futures contracts based on notional, price, and target hedge ratio.
    *   `_calculate_irs_hedge()`: Specifies an IRS to receive floating/pay fixed, matching the TRS tenor and notional.
    *   `_calculate_put_hedge()`: Determines put option specifications (strike, expiry, quantity) based on desired protection level (e.g., 95% Value-at-Risk).

#### **Phase 3: Advanced Features & Integration**
*Goal: Refine recommendations and connect them to the existing simulator workflow.*

1.  **Incorporate Simulation Insights**: Use the Monte Carlo results (e.g., distribution of final prices, path volatility) to calibrate hedge sizes and strike prices dynamically, moving beyond static rules.
2.  **Integrate with `TRSPricer.run_simulation`**: Modify the main orchestration method to:
    a. Pass all simulated data (price paths, cash flows, NPV list) to the `HedgingEngine`.
    b. Append the hedging recommendation dictionary to the `summary_results`.
3.  **Extend Reporting & Visualization**:
    *   Update `TRSPricer.generate_summary_report()` to display the hedge recommendation clearly.
    *   Add a new plotting method in `TRSVisualizer` (e.g., `plot_hedge_strategy`) to visualize the payoff of the hedged portfolio versus the unhedged TRS.

#### **Phase 4: Validation & Documentation**
*Goal: Ensure correctness and update project guides.*

1.  **Create Validation Tests**: Develop unit tests for the `HedgingEngine` logic using known scenarios (e.g., "For a payer position with a 10M notional on AAPL, expect a long futures recommendation of X contracts").
2.  **Update `main.py` Examples**: Include clear examples in the main script demonstrating both `desk_position="payer"` and `desk_position="receiver"` scenarios.
3.  **Update README.md**: Integrate this plan and the new module's API into the main project documentation.

---

### **3. Expected Output Enhancement**

After implementation, the console output from `generate_summary_report` will include a new section:

```
----------------------------------------
Hedging Recommendation (Desk's Perspective):
  Desk Role: Total Return RECEIVER
  Primary Risk: Long Equity, Short Floating Rate
  Recommended Strategy:
    1. INTEREST RATE SWAP: Receive SOFR, Pay Fixed @ 5.15%
       • Notional: $5,000,000 | Tenor: 2 Years
       • Objective: Hedge floating rate payment liability.
    2. EQUITY PUT OPTIONS: Long Put, Strike @ $380.00 (90% of spot)
       • Quantity: 132 Contracts | Estimated Premium: $42,000
       • Objective: Protect against underlying depreciation below $380.
  Combined Hedge Cost (Premium): ~$42,000
  Net Effect: Converts position to a ~5% fixed funding cost with capped downside.
```

This extension adds significant practical value by closing the loop between risk measurement and risk management, making your simulator a comprehensive tool for understanding TRS economics.

---

## **Step-by-Step Implementation Guide: Hedging Recommendation Module**

This section provides detailed implementation instructions for the hedging module skeleton code. Follow these steps in order to complete the implementation.

### **Step 1: Implement Instrument Models**

#### **1.1 Futures Model** (`trs_pricer/hedging/instruments/futures_model.py`)

**Implement `__post_init__()`:**
```python
def __post_init__(self):
    """Calculate number of contracts and hedge notional after initialization."""
    if self.current_price <= 0:
        raise ValueError("current_price must be positive")
    if self.contract_size <= 0:
        raise ValueError("contract_size must be positive")
    
    # Calculate number of contracts needed
    # Formula: num_contracts = (notional * target_hedge_ratio) / (contract_size * current_price)
    shares_to_hedge = (self.notional * self.target_hedge_ratio) / self.current_price
    self.num_contracts = int(round(shares_to_hedge / self.contract_size))
    
    # Effective hedge notional
    self.hedge_notional = self.num_contracts * self.contract_size * self.current_price
```

**Implement `to_dict()`:**
```python
def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary for reporting."""
    return {
        "type": "EQUITY FUTURES",
        "ticker": self.ticker,
        "position": "LONG",
        "num_contracts": self.num_contracts,
        "contract_size": self.contract_size,
        "current_price": self.current_price,
        "hedge_notional": self.hedge_notional,
        "target_hedge_ratio": self.target_hedge_ratio,
        "objective": f"Hedge {self.target_hedge_ratio*100:.0f}% of delta exposure from short equity position",
    }
```

#### **1.2 Interest Rate Swap Model** (`trs_pricer/hedging/instruments/swap_model.py`)

**Implement `__post_init__()`:**
```python
def __post_init__(self):
    """Validate parameters after initialization."""
    if self.notional <= 0:
        raise ValueError("notional must be positive")
    if self.tenor <= 0:
        raise ValueError("tenor must be positive")
    if self.payment_frequency <= 0:
        raise ValueError("payment_frequency must be positive")
```

**Implement `calculate_annual_payment()`:**
```python
def calculate_annual_payment(self) -> float:
    """Calculate annual fixed payment amount."""
    return self.notional * self.fixed_rate
```

**Implement `calculate_periodic_payment()`:**
```python
def calculate_periodic_payment(self) -> float:
    """Calculate periodic (e.g., quarterly) fixed payment amount."""
    return self.calculate_annual_payment() / self.payment_frequency
```

**Implement `to_dict()`:**
```python
def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary for reporting."""
    position = "RECEIVE FLOATING, PAY FIXED" if self.receive_floating else "PAY FLOATING, RECEIVE FIXED"
    return {
        "type": "INTEREST RATE SWAP",
        "notional": self.notional,
        "tenor": self.tenor,
        "position": position,
        "fixed_rate": self.fixed_rate,
        "floating_rate_index": self.floating_rate_index,
        "payment_frequency": self.payment_frequency,
        "annual_payment": self.calculate_annual_payment(),
        "periodic_payment": self.calculate_periodic_payment(),
        "objective": f"Hedge floating rate payment liability by receiving {self.floating_rate_index} and paying fixed @ {self.fixed_rate*100:.2f}%",
    }
```

#### **1.3 Options Model** (`trs_pricer/hedging/instruments/options_model.py`)

**Implement `__post_init__()`:**
```python
def __post_init__(self):
    """Calculate number of contracts and validate after initialization."""
    if self.current_price <= 0:
        raise ValueError("current_price must be positive")
    if self.strike_price <= 0:
        raise ValueError("strike_price must be positive")
    if self.contract_size <= 0:
        raise ValueError("contract_size must be positive")
    if self.option_type.upper() not in ["PUT", "CALL"]:
        raise ValueError("option_type must be 'PUT' or 'CALL'")
    
    # Calculate number of contracts needed to hedge notional
    shares_to_hedge = self.notional / self.current_price
    self.num_contracts = int(round(shares_to_hedge / self.contract_size))
    
    # Estimate premium if not provided (rough approximation based on moneyness)
    if self.estimated_premium == 0.0:
        moneyness = self.strike_price / self.current_price
        if self.option_type.upper() == "PUT":
            if moneyness < 0.95:  # Deep OTM
                premium_rate = 0.02
            elif moneyness < 1.0:  # OTM
                premium_rate = 0.05
            else:  # ITM or ATM
                premium_rate = 0.08
        else:  # CALL
            if moneyness > 1.05:  # Deep OTM
                premium_rate = 0.02
            elif moneyness > 1.0:  # OTM
                premium_rate = 0.05
            else:  # ITM or ATM
                premium_rate = 0.08
        self.estimated_premium = self.notional * premium_rate
```

**Implement `to_dict()`:**
```python
def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary for reporting."""
    moneyness_pct = (self.strike_price / self.current_price - 1) * 100
    return {
        "type": f"EQUITY {self.option_type.upper()} OPTIONS",
        "ticker": self.ticker,
        "position": f"LONG {self.option_type.upper()}",
        "strike_price": self.strike_price,
        "current_price": self.current_price,
        "moneyness": f"{moneyness_pct:+.1f}%",
        "num_contracts": self.num_contracts,
        "contract_size": self.contract_size,
        "estimated_premium": self.estimated_premium,
        "expiry_years": self.expiry_years,
        "target_delta": self.target_delta,
        "objective": f"Protect against underlying {'depreciation' if self.option_type.upper() == 'PUT' else 'appreciation'} below/above ${self.strike_price:.2f}",
    }
```

---

### **Step 2: Implement Valuation Engine Exposure Methods**

#### **2.1 Delta Exposure** (`trs_pricer/core/valuation.py`)

**Implement `calculate_delta_exposure()`:**
```python
def calculate_delta_exposure(
    self,
    cash_flows_list: List[pd.DataFrame],
    price_paths: np.ndarray,
    params: Dict,
) -> float:
    """
    Calculate approximate delta exposure using finite difference method.
    """
    if price_paths.size == 0 or not cash_flows_list:
        return 0.0
    
    initial_price = price_paths[0, 0]
    price_shock = initial_price * 0.01  # 1% shock
    
    # For simplicity, use analytical approximation:
    # Delta ≈ notional / initial_price for a TRS
    notional = params.get("notional", 0.0)
    
    # More sophisticated: could recalculate NPV with shocked prices
    # For now, use simple approximation
    return notional / initial_price if initial_price > 0 else 0.0
```

#### **2.2 Funding Rate Exposure** (`trs_pricer/core/valuation.py`)

**Implement `calculate_funding_rate_exposure()`:**
```python
def calculate_funding_rate_exposure(
    self,
    cash_flows_list: List[pd.DataFrame],
    params: Dict,
) -> float:
    """
    Calculate PV of funding leg to isolate interest rate risk.
    """
    if not cash_flows_list:
        return 0.0
    
    benchmark_rate = params.get("benchmark_rate", 0.0)
    payment_frequency = params.get("payment_frequency", 4)
    period_rate = benchmark_rate / payment_frequency
    
    # Sum up all funding leg cash flows across all paths and periods
    total_funding_pv = 0.0
    for df in cash_flows_list:
        for period_idx, row in df.iterrows():
            period = row["period"]
            funding_flow = row.get("net_funding_cash_flow", 0.0)
            discount_factor = (1 + period_rate) ** (-period)
            total_funding_pv += funding_flow * discount_factor
    
    # Average across all simulations
    num_simulations = len(cash_flows_list)
    return total_funding_pv / num_simulations
```

---

### **Step 3: Implement Hedging Engine Core Methods**

#### **3.1 Risk Identification** (`trs_pricer/hedging/hedging_engine.py`)

**Implement `_identify_primary_risks()`:**
```python
def _identify_primary_risks(
    self,
    desk_position: str,
    delta_exposure: float,
    funding_rate_exposure: float,
) -> List[str]:
    """Identify primary risks based on desk position and exposures."""
    risks = []
    
    if desk_position == "payer":
        # Desk pays total return → short the asset → risk if asset appreciates
        risks.append("Short Equity (asset appreciation risk)")
    else:  # receiver
        # Desk receives total return → long the asset → risk if asset depreciates
        risks.append("Long Equity (asset depreciation risk)")
        # Also short floating rate (pays funding) → risk if rates rise
        if funding_rate_exposure > 0:
            risks.append("Short Floating Rate (rising rate risk)")
    
    return risks
```

#### **3.2 Payer Hedge Recommendation** (`trs_pricer/hedging/hedging_engine.py`)

**Implement `_recommend_payer_hedge()`:**
```python
def _recommend_payer_hedge(
    self,
    params: Dict[str, Any],
    price_paths: np.ndarray,
    delta_exposure: float,
) -> List[Dict[str, Any]]:
    """Recommend hedging strategy for Total Return Payer position."""
    ticker = params["ticker"]
    notional = params["notional"]
    current_price = price_paths[0, 0] if price_paths.size > 0 else params.get("initial_price", 1.0)
    
    # Calculate futures hedge
    futures_hedge = FuturesHedge(
        ticker=ticker,
        notional=notional,
        current_price=current_price,
        contract_size=self._config.DEFAULT_FUTURES_CONTRACT_SIZE,
        target_hedge_ratio=self._config.DEFAULT_TARGET_HEDGE_RATIO,
    )
    
    return [futures_hedge.to_dict()]
```

#### **3.3 Receiver Hedge Recommendation** (`trs_pricer/hedging/hedging_engine.py`)

**Implement `_recommend_receiver_hedge()`:**
```python
def _recommend_receiver_hedge(
    self,
    params: Dict[str, Any],
    price_paths: np.ndarray,
    delta_exposure: float,
    funding_rate_exposure: float,
    summary_results: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Recommend hedging strategy for Total Return Receiver position."""
    recommendations = []
    
    # 1. Interest Rate Swap recommendation
    notional = params["notional"]
    tenor = params["tenor"]
    benchmark_rate = params.get("benchmark_rate", 0.05)
    payment_frequency = params.get("payment_frequency", 4)
    
    # Fixed rate = benchmark + buffer
    fixed_rate = benchmark_rate + self._config.DEFAULT_IRS_FIXED_RATE_BUFFER
    
    irs_hedge = InterestRateSwapHedge(
        notional=notional,
        tenor=tenor,
        fixed_rate=fixed_rate,
        floating_rate_index="SOFR",
        receive_floating=True,
        payment_frequency=payment_frequency,
    )
    recommendations.append(irs_hedge.to_dict())
    
    # 2. Put Options recommendation
    ticker = params["ticker"]
    current_price = price_paths[0, 0] if price_paths.size > 0 else params.get("initial_price", 1.0)
    
    # Calculate strike price based on protection level
    strike_price = self._calculate_protective_put_strike(
        price_paths, current_price, params, summary_results
    )
    
    put_hedge = OptionsHedge(
        ticker=ticker,
        option_type="PUT",
        strike_price=strike_price,
        current_price=current_price,
        notional=notional,
        contract_size=self._config.DEFAULT_OPTION_CONTRACT_SIZE,
        expiry_years=tenor,
        target_delta=self._config.DEFAULT_TARGET_PUT_DELTA,
    )
    recommendations.append(put_hedge.to_dict())
    
    return recommendations
```

#### **3.4 Protective Put Strike Calculation** (`trs_pricer/hedging/hedging_engine.py`)

**Implement `_calculate_protective_put_strike()`:**
```python
def _calculate_protective_put_strike(
    self,
    price_paths: np.ndarray,
    current_price: float,
    params: Dict[str, Any],
    summary_results: Dict[str, Any],
) -> float:
    """Calculate protective put strike price based on simulation results."""
    if price_paths.size > 0:
        final_prices = price_paths[:, -1]  # Last period prices
        protection_level = self._config.DEFAULT_PROTECTION_LEVEL
        percentile_price = np.percentile(final_prices, (1 - protection_level) * 100)
        
        # Use the lower of percentile-based or percentage-based strike
        percentage_strike = current_price * self._config.DEFAULT_PUT_STRIKE_PERCENTAGE
        return min(percentile_price, percentage_strike)
    
    # Fallback: Use default percentage
    return current_price * self._config.DEFAULT_PUT_STRIKE_PERCENTAGE
```

#### **3.5 Net Effect Description** (`trs_pricer/hedging/hedging_engine.py`)

**Implement `_describe_net_effect()`:**
```python
def _describe_net_effect(
    self,
    desk_position: str,
    recommended_strategy: List[Dict[str, Any]],
    combined_hedge_cost: float,
) -> str:
    """Generate description of net effect after hedging."""
    if desk_position == "payer":
        return (
            f"Long futures position offsets short equity exposure. "
            f"Net effect: Neutralized delta risk with minimal cost (futures margin only)."
        )
    else:  # receiver
        irs_present = any(h.get("type") == "INTEREST RATE SWAP" for h in recommended_strategy)
        puts_present = any("PUT" in h.get("type", "") for h in recommended_strategy)
        
        effects = []
        if irs_present:
            effects.append("converts floating rate liability to fixed rate")
        if puts_present:
            effects.append("caps downside risk while retaining upside")
        
        net_effect = "Net effect: " + " and ".join(effects) if effects else "Net effect: Risk mitigated"
        if combined_hedge_cost > 0:
            net_effect += f" with estimated hedge cost of ${combined_hedge_cost:,.0f}"
        
        return net_effect
```

#### **3.6 Main Recommendation Generator** (`trs_pricer/hedging/hedging_engine.py`)

**Implement `generate_hedging_recommendation()`:**
```python
def generate_hedging_recommendation(
    self,
    desk_position: str,
    summary_results: Dict[str, Any],
    cash_flows_list: List[pd.DataFrame],
    price_paths: np.ndarray,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate hedging recommendations based on desk position and risk exposures."""
    desk_position = desk_position.lower().strip()
    if desk_position not in ["payer", "receiver"]:
        raise ValueError(f"desk_position must be 'payer' or 'receiver', got '{desk_position}'")
    
    # Calculate risk exposures
    delta_exposure = self._val.calculate_delta_exposure(cash_flows_list, price_paths, params)
    funding_rate_exposure = self._val.calculate_funding_rate_exposure(cash_flows_list, params)
    
    # Identify primary risks
    primary_risks = self._identify_primary_risks(desk_position, delta_exposure, funding_rate_exposure)
    
    # Generate hedge recommendations based on position
    if desk_position == "payer":
        recommended_strategy = self._recommend_payer_hedge(params, price_paths, delta_exposure)
    else:  # receiver
        recommended_strategy = self._recommend_receiver_hedge(
        params, price_paths, delta_exposure, funding_rate_exposure, summary_results
    )
    
    # Calculate combined hedge cost
    combined_hedge_cost = sum(
        hedge.get("estimated_premium", 0.0) or hedge.get("estimated_cost", 0.0)
        for hedge in recommended_strategy
    )
    
    # Generate net effect description
    net_effect = self._describe_net_effect(desk_position, recommended_strategy, combined_hedge_cost)
    
    return {
        "desk_position": desk_position.upper(),
        "primary_risks": primary_risks,
        "delta_exposure": delta_exposure,
        "funding_rate_exposure": funding_rate_exposure,
        "recommended_strategy": recommended_strategy,
        "combined_hedge_cost": combined_hedge_cost,
        "net_effect": net_effect,
    }
```

---

### **Step 4: Integrate Hedging into TRSPricer**

#### **4.1 Update `run_simulation()`** (`trs_pricer/core/trs_pricer.py`)

**Replace the TODO in `run_simulation()`:**
```python
# Step 7: Generate hedging recommendations (if desk_position is provided)
hedging_recommendation = None
if "desk_position" in resolved_params:
    try:
        hedging_recommendation = self._hedge.generate_hedging_recommendation(
            desk_position=resolved_params["desk_position"],
            summary_results=summary_results,
            cash_flows_list=cash_flows_list,
            price_paths=price_paths,
            params=resolved_params,
        )
        summary_results["hedging_recommendation"] = hedging_recommendation
    except Exception as e:
        # Log error but don't fail the simulation
        print(f"Warning: Could not generate hedging recommendations: {e}")
```

#### **4.2 Update `generate_summary_report()`** (`trs_pricer/core/trs_pricer.py`)

**Replace the TODO in `generate_summary_report()`:**
```python
# Hedging Recommendation section (if available)
if "hedging_recommendation" in summary_results:
    hedging = summary_results["hedging_recommendation"]
    lines.append("-" * 40)
    lines.append("Hedging Recommendation (Desk's Perspective):")
    lines.append(f"  Desk Role: Total Return {hedging['desk_position']}")
    lines.append(f"  Primary Risk: {', '.join(hedging['primary_risks'])}")
    lines.append("  Recommended Strategy:")
    
    for idx, strategy in enumerate(hedging["recommended_strategy"], 1):
        strategy_type = strategy.get("type", "UNKNOWN")
        if strategy_type == "INTEREST RATE SWAP":
            lines.append(f"    {idx}. {strategy_type}: {strategy.get('position', '')}")
            lines.append(f"       • Notional: ${strategy.get('notional', 0):,.0f} | Tenor: {strategy.get('tenor', 0)} Years")
            lines.append(f"       • Fixed Rate: {strategy.get('fixed_rate', 0)*100:.2f}% | Floating: {strategy.get('floating_rate_index', 'N/A')}")
            lines.append(f"       • Objective: {strategy.get('objective', 'N/A')}")
        elif "OPTIONS" in strategy_type:
            lines.append(f"    {idx}. {strategy_type}: {strategy.get('position', '')}")
            lines.append(f"       • Strike: ${strategy.get('strike_price', 0):.2f} ({strategy.get('moneyness', 'N/A')})")
            lines.append(f"       • Quantity: {strategy.get('num_contracts', 0)} Contracts | Estimated Premium: ${strategy.get('estimated_premium', 0):,.0f}")
            lines.append(f"       • Objective: {strategy.get('objective', 'N/A')}")
        elif "FUTURES" in strategy_type:
            lines.append(f"    {idx}. {strategy_type}: {strategy.get('position', '')}")
            lines.append(f"       • Quantity: {strategy.get('num_contracts', 0)} Contracts | Hedge Notional: ${strategy.get('hedge_notional', 0):,.0f}")
            lines.append(f"       • Objective: {strategy.get('objective', 'N/A')}")
    
    combined_cost = hedging.get("combined_hedge_cost", 0.0)
    if combined_cost > 0:
        lines.append(f"  Combined Hedge Cost (Premium): ~${combined_cost:,.0f}")
    lines.append(f"  Net Effect: {hedging.get('net_effect', 'N/A')}")
```

---

### **Step 5: Implement Visualization**

#### **5.1 Hedge Strategy Plot** (`trs_pricer/visualization/visualization.py`)

**Implement `plot_hedge_strategy()`:**
```python
def plot_hedge_strategy(
    self,
    hedging_recommendation: Dict,
    price_paths: np.ndarray,
    params: Dict,
) -> plt.Figure:
    """Plot hedge strategy visualization showing hedged vs unhedged portfolio payoff."""
    fig, ax = self._create_figure()
    
    # Extract key information
    desk_position = hedging_recommendation.get("desk_position", "RECEIVER")
    strategies = hedging_recommendation.get("recommended_strategy", [])
    
    if not strategies or price_paths.size == 0:
        ax.text(0.5, 0.5, 'No hedge strategy data available', 
                transform=ax.transAxes, ha='center', va='center')
        return fig
    
    # Plot final price distribution
    final_prices = price_paths[:, -1]
    initial_price = price_paths[0, 0]
    
    # Create histogram of final prices
    ax.hist(final_prices, bins=50, alpha=0.5, label='Final Price Distribution', 
            color='blue', edgecolor='black')
    ax.axvline(initial_price, color='green', linestyle='--', linewidth=2, 
               label=f'Initial Price: ${initial_price:.2f}')
    
    # Mark hedge strikes if puts are present
    for strategy in strategies:
        if "PUT" in strategy.get("type", ""):
            strike = strategy.get("strike_price", initial_price)
            ax.axvline(strike, color='red', linestyle='--', linewidth=2, 
                     label=f'Put Strike: ${strike:.2f}')
    
    ax.set_xlabel("Final Stock Price ($)")
    ax.set_ylabel("Frequency")
    ax.set_title(f"Hedge Strategy Visualization\nDesk Position: {desk_position}")
    ax.legend()
    plt.tight_layout()
    
    return fig
```

**Update `run_simulation()` to include the plot:**
```python
# Plot hedge strategy (if hedging recommendation available)
if hedging_recommendation:
    try:
        fig5 = self._viz.plot_hedge_strategy(
            hedging_recommendation, price_paths, resolved_params
        )
        figures.append(fig5)
    except Exception as e:
        print(f"Warning: Could not generate hedge strategy plot: {e}")
```

---

### **Step 6: Testing**

#### **6.1 Test Payer Position**

Create a test script:
```python
from trs_pricer import TRSPricer

params = {
    "ticker": "AAPL",
    "notional": 10_000_000,
    "tenor": 1,
    "payment_frequency": 4,
    "num_simulations": 1000,
    "desk_position": "payer",  # Test payer hedge
}

pricer = TRSPricer()
summary_results, figs = pricer.run_simulation(params)
report = pricer.generate_summary_report(summary_results)
print(report)
```

#### **6.2 Test Receiver Position**

```python
params = {
    "ticker": "MSFT",
    "notional": 5_000_000,
    "tenor": 2,
    "payment_frequency": 4,
    "num_simulations": 5000,
    "desk_position": "receiver",  # Test receiver hedge
}

pricer = TRSPricer()
summary_results, figs = pricer.run_simulation(params)
report = pricer.generate_summary_report(summary_results)
print(report)
```

---

### **Step 7: Verification Checklist**

- [ ] All instrument models (`FuturesHedge`, `InterestRateSwapHedge`, `OptionsHedge`) implement `__post_init__()` and `to_dict()`
- [ ] `ValuationEngine` implements `calculate_delta_exposure()` and `calculate_funding_rate_exposure()`
- [ ] `HedgingEngine` implements all helper methods and `generate_hedging_recommendation()`
- [ ] `TRSPricer.run_simulation()` integrates hedging recommendations
- [ ] `TRSPricer.generate_summary_report()` displays hedging recommendations
- [ ] `TRSVisualizer.plot_hedge_strategy()` creates visualization
- [ ] Test with both `desk_position="payer"` and `desk_position="receiver"`
- [ ] Verify output matches expected format from Section 3

---

**Implementation Order Recommendation:**
1. Start with instrument models (Step 1) - they're independent and testable
2. Implement valuation exposure methods (Step 2) - needed by hedging engine
3. Build hedging engine methods incrementally (Step 3) - test each method as you go
4. Integrate into TRSPricer (Step 4) - connects everything together
5. Add visualization (Step 5) - final polish
6. Test thoroughly (Step 6) - verify end-to-end functionality