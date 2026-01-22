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
    `(effective_funding_rate / payment_frequency) * notional - max(0, period_start - period_end)/period_start * notional`  
    (depreciation netted against funding).  
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

**Module-level API (backward compatibility):**  
`trs_pricer` exposes `get_user_inputs`, `run_simulation`, and `generate_summary_report` as functions that delegate to a default `TRSPricer` instance. `main.py` uses these.

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

### **Module-level API (as in `main.py`)**

```python
from trs_pricer import run_simulation, generate_summary_report
import matplotlib.pyplot as plt

params = {
    "ticker": "MSFT",
    "notional": 5_000_000,
    "tenor": 2,
    "payment_frequency": 4,
    "num_simulations": 5000,
}
summary_results, figs = run_simulation(params)
print(generate_summary_report(summary_results))
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
summary_results, figs = run_simulation(params_manual)
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

❌ **Remaining Implementation Steps:**

### **Phase 1: Foundation & Core (Remaining)**

3. **`simulation.py` → `SimulationEngine`**  
   Implement:
   - `calculate_time_step(tenor, payment_frequency)` - Returns `1 / payment_frequency`
   - `simulate_price_paths(initial_price, tenor, volatility, payment_frequency, num_simulations, benchmark_rate, seed)` - GBM simulation:
     - `dt = 1 / payment_frequency`
     - For each path: `price[t] = price[t-1] * exp((mu - 0.5*vol²)*dt + vol*sqrt(dt)*Z)`
     - `mu = benchmark_rate` (risk-neutral), `Z ~ N(0,1)`
     - Returns `np.ndarray` of shape `(num_simulations, num_periods + 1)`

4. **`cash_flows.py` → `CashFlowEngine`**  
   Implement:
   - `calculate_total_return_leg(period_start_price, period_end_price, dividend_yield, notional, payment_frequency)` - Returns: `(period_end - period_start)/period_start * notional + (dividend_yield / payment_frequency) * notional`
   - `calculate_funding_leg(period_start_price, period_end_price, effective_funding_rate, notional, payment_frequency)` - Returns: `(effective_funding_rate / payment_frequency) * notional - max(0, period_start - period_end)/period_start * notional`
   - `calculate_cash_flows(price_paths, params)` - For each simulation path, compute cash flows per period. Returns `List[pd.DataFrame]` with columns: `period_start_price`, `period_end_price`, `total_return_cash_flow`, `net_funding_cash_flow`, `net_cash_flow`

5. **`trs_pricer.py` → `TRSPricer.get_user_inputs`**  
   Implement:
   - Validate required params (`ticker`, `notional`, `tenor`, `payment_frequency`, `num_simulations`)
   - Use `MarketDataFetcher` to auto-fetch: `initial_price`, `dividend_yield`, `volatility`, `funding_spread`
   - Use user override or `config.DEFAULT_BENCHMARK_RATE` for `benchmark_rate`
   - Calculate `effective_funding_rate = benchmark_rate + funding_spread`
   - Return resolved `Dict[str, Any]` with all parameters

### **Phase 2: Analysis & Visualization**

6. **`valuation.py` → `ValuationEngine`**  
   Implement:
   - `calculate_npv(cash_flows_series, benchmark_rate, payment_frequency)` - Discount net cash flows at `benchmark_rate` per period
   - `calculate_marked_to_market_value(cash_flows_df, benchmark_rate, payment_frequency, current_period)` - PV of future cash flows from `current_period` onward
   - `calculate_exposure_metrics(cash_flows_list, params)` - EPE profile: for each period, average `max(0, MTM)` across all paths. Returns `(epe_profile, dates)` as `Tuple[np.ndarray, np.ndarray]`
   - `aggregate_results(all_simulated_cash_flows, npv_list)` - Summary statistics: mean/std NPV, percentiles (5th, 25th, 50th, 75th, 95th), mean periodic net cash flows. Returns `Dict`

7. **`visualization.py` → `TRSVisualizer`**  
   Implement:
   - `plot_simulated_price_paths(price_paths, num_paths_to_plot, tenor, payment_frequency)` - Plot sample paths over time
   - `plot_npv_distribution(npv_list)` - Histogram of desk NPV across simulations
   - `plot_epe_profile(epe_profile, dates)` - Line plot of Expected Positive Exposure over time
   - `plot_cash_flow_analysis(cash_flows_series, num_simulations_to_plot)` - Net cash flow over periods for sample simulations
   - Each method returns `plt.Figure`

### **Phase 3: Integration**

8. **`trs_pricer.py` → `TRSPricer.run_simulation`**  
   Implement full pipeline:
   - Call `get_user_inputs(params)` to resolve all parameters
   - `SimulationEngine.simulate_price_paths(...)` → price paths
   - `CashFlowEngine.calculate_cash_flows(price_paths, params)` → cash flows per path
   - For each path: `ValuationEngine.calculate_npv(...)` → NPV list
   - `ValuationEngine.calculate_exposure_metrics(...)` → EPE profile
   - `ValuationEngine.aggregate_results(...)` → summary statistics
   - `TRSVisualizer` methods → generate all plots
   - Return `(summary_results: Dict, figures: List[plt.Figure])`

9. **`trs_pricer.py` → `TRSPricer.generate_summary_report`**  
   Format `summary_results` as console report:
   - Trade details (ticker, notional, tenor)
   - Market data (auto-fetched values with sources)
   - Valuation metrics (expected NPV, std dev, percentiles)
   - Risk metrics (peak EPE, timing)
   - Returns formatted `str`

10. **`trs_pricer.py` → Module-level API functions**  
    Implement convenience functions that delegate to default `TRSPricer` instance:
    - `get_user_inputs(params)` → `TRSPricer().get_user_inputs(params)`
    - `run_simulation(params)` → `TRSPricer().run_simulation(params)`
    - `generate_summary_report(summary_results)` → `TRSPricer().generate_summary_report(summary_results)`

11. **`main.py`** (Already structured, will work once above are implemented)  
    Uses module-level API: `run_simulation` and `generate_summary_report`

### **Dependencies flow**

```
config.py ✅
    ↓
MarketDataFetcher (market_data) ✅
    ↓
TRSPricer.get_user_inputs ❌ (Step 5)
    ↓
SimulationEngine (simulation) ❌ (Step 3)
    ↓
CashFlowEngine (cash_flows) ❌ (Step 4)
    ↓
ValuationEngine (valuation) ❌ (Step 6)
    ↓
TRSVisualizer (visualization) ❌ (Step 7)
    ↓
TRSPricer.run_simulation / generate_summary_report ❌ (Steps 8-9)
    ↓
main.py ✅ (structure ready, waiting on implementation)
```

**Legend:** ✅ = Completed, ❌ = Pending implementation

### **Implementation tips**

1. Implement and test each class in isolation before wiring.  
2. Use config defaults and fallbacks for all market data.  
3. Validate inputs (e.g. positive notional, valid tenor).  
4. Handle missing/invalid tickers and empty series gracefully.
