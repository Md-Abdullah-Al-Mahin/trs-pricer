# **Project Outline: Total Return Swap (TRS) Pricing Simulator**

## **1. Project Overview & Objective**
Build a Python-based simulation engine for a single-stock Total Return Swap (TRS), the foundational instrument in synthetic prime brokerage. This tool will model the periodic cash flows between a prime brokerage desk and a hedge fund client, calculating the net economics and key risk metrics. The goal is to create a practical, educational model that demonstrates how synthetics provide leveraged exposure and how the desk manages the associated funding and market risks.

## **2. Core Technical Requirements & Specifications**

### **2.1. Input Parameters (User-Defined Variables)**
Your script should initialize with the following configurable parameters:

*   **Reference Asset**: `ticker` (e.g., "AAPL")
*   **Trade Terms**:
    *   `notional`: Principal amount of the swap (e.g., 10,000,000)
    *   `initial_price`: Stock price at trade inception (fetched automatically if not provided)
    *   `dividend_yield`: **Fetched automatically** - Retrieved from market data using the stock's trailing twelve-month dividends divided by current price. Falls back to user-provided value if data unavailable.
*   **Funding & Rates**:
    *   `benchmark_rate`: Annual risk-free rate (e.g., SOFR at 0.05 for 5%). Can be fetched from FRED (Federal Reserve Economic Data) for current rates.
    *   `funding_spread`: **Estimated automatically** - Derived from publicly available data using one of these methods:
        *   **Primary**: Fetch corporate bond spreads (investment-grade vs high-yield indices) from FRED
        *   **Secondary**: Estimate based on stock's beta and market volatility as a credit quality proxy
        *   **Fallback**: Use sector-specific average spreads or user-provided value
    *   `effective_funding_rate`: `benchmark_rate + funding_spread`
*   **Simulation Settings**:
    *   `tenor`: Swap duration in years (e.g., 1)
    *   `payment_frequency`: Number of coupon periods per year (e.g., 4 for quarterly)
    *   `num_simulations`: Number of random future price path scenarios to generate (e.g., 1000)
*   **Market Assumptions**:
    *   `volatility`: **Fetched automatically** - Calculated from historical price data:
        *   Fetch daily closing prices for the past 1 year (252 trading days)
        *   Calculate daily log returns: `ln(P_t / P_{t-1})`
        *   Compute standard deviation of daily returns
        *   Annualize: `volatility = daily_std * sqrt(252)`
        *   Falls back to user-provided value or sector average if data unavailable

### **2.1.1. Market Data Sources & Fetching Logic**

The following public data sources are used to automatically populate parameters:

| Parameter | Data Source | API/Library | Fallback |
|-----------|-------------|-------------|----------|
| `initial_price` | Current stock price | `yfinance` | User input |
| `dividend_yield` | TTM dividends / current price | `yfinance` (dividends history) | User input or 0% |
| `benchmark_rate` | SOFR or Fed Funds Rate | FRED API (`fredapi`) | User input or 5% default |
| `funding_spread` | Corporate bond spread indices | FRED API (ICE BofA indices) | Beta-based estimate or 1.5% default |
| `volatility` | Historical price returns | `yfinance` (1-year daily prices) | User input or 25% default |

**FRED Series IDs for Spread Estimation:**
*   `BAMLC0A0CM` - ICE BofA US Corporate Index Option-Adjusted Spread
*   `BAMLH0A0HYM2` - ICE BofA US High Yield Index Option-Adjusted Spread
*   `SOFR` - Secured Overnight Financing Rate

### **2.2. Mathematical & Financial Modeling Logic**

The core of the model involves calculating cash flows for each simulation path at each payment date.

**A. Simulate Future Stock Price Paths**
Use Geometric Brownian Motion (GBM) to generate plausible future price scenarios.
*   `dt = tenor / (payment_frequency * tenor)` (time step per period)
*   For each simulation `i` and period `t`:
    *   `random_shock = np.random.normal(0, 1)`
    *   `price_path[i, t] = price_path[i, t-1] * exp( (mu - 0.5*volatility²) * dt + volatility * sqrt(dt) * random_shock )`
    *   Where `mu` can be approximated by the `benchmark_rate` for risk-neutral valuation.

**B. Calculate Periodic Cash Flows (For each path and period)**
*   **Total Return Leg (Desk Pays to Client)**:
    *   Price Appreciation: `(period_end_price - period_start_price) / period_start_price * notional`
    *   Dividend Payment: `dividend_yield / payment_frequency * notional`
    *   `total_return_cash_flow = Price Appreciation + Dividend Payment`
*   **Funding Leg (Client Pays to Desk)**:
    *   Funding Amount: `effective_funding_rate / payment_frequency * notional`
    *   Price Depreciation (if any): If `period_end_price < period_start_price`, the client pays the depreciation amount (this is typically *netted* against the funding amount in practice).
    *   `net_funding_cash_flow = Funding Amount - max(0, period_start_price - period_end_price)/period_start_price * notional`
*   **Net Periodic Cash Flow (To Desk)**:
    *   `net_cash_flow = net_funding_cash_flow - total_return_cash_flow`
    *   A positive value represents a net inflow to the desk.

**C. Valuation & Risk Metrics**
*   **Net Present Value (NPV) for the Desk**: For each simulated path, discount all future `net_cash_flows` back to inception using the `benchmark_rate`. Calculate the average NPV across all simulations.
*   **Expected Positive Exposure (EPE)**: For each future date, calculate the average of *positive* net exposures (marked-to-market value of the swap from the desk's perspective) across all paths. This measures potential future credit risk to the desk.
*   **Key Outputs per Simulation**:
    *   Array of stock prices over time.
    *   Array of detailed cash flows (Total Return Leg, Funding Leg, Net).
    *   Final NPV of the swap for the desk.

## **3. Step-by-Step Implementation Plan**

### **Phase 1: Project Setup & Core Calculation Functions**
1.  **Environment Setup**: Create a new Python file (e.g., `trs_pricer.py`). Import necessary libraries: `numpy`, `pandas`, `matplotlib.pyplot`, `yfinance`, `fredapi`.
2.  **Market Data Module**: Write a `market_data.py` module with the following functions:
    *   `fetch_current_price(ticker)` - Get current stock price via yfinance
    *   `fetch_dividend_yield(ticker)` - Calculate TTM dividend yield from dividend history
    *   `fetch_historical_volatility(ticker, lookback_days=252)` - Calculate annualized volatility from historical returns
    *   `fetch_benchmark_rate(fred_api_key=None)` - Fetch SOFR or Fed Funds rate from FRED
    *   `estimate_funding_spread(ticker, fred_api_key=None)` - Estimate spread using corporate bond indices or beta-based proxy
3.  **Input Module**: Write a function `get_user_inputs()` that defines and returns all parameters from Section 2.1. This function should call the market data module to auto-populate dividend yield, volatility, and funding spread, with fallback to user-provided values.
4.  **Path Simulation**: Write a function `simulate_price_paths(initial_price, tenor, volatility, payment_frequency, num_simulations)` that implements the GBM model and returns a 2D NumPy array of shape (`num_simulations`, `periods`).
5.  **Cash Flow Engine**: Write the core function `calculate_cash_flows(price_paths, params)`. This function should iterate through each simulation and time period to compute the three cash flow legs using the logic in Section 2.2.B. It should return structured data (e.g., a list of DataFrames).

### **Phase 2: Analysis, Aggregation & Visualization**
6.  **Valuation & Risk Analysis**:
    *   Write a function `calculate_npv(cash_flows_series, benchmark_rate, payment_frequency)` that discounts cash flows.
    *   Write a function `calculate_exposure_metrics(cash_flows_series, params)` that computes the EPE profile.
7.  **Results Aggregation**: Create a function `aggregate_results(all_simulated_cash_flows, npv_list)` that calculates summary statistics (mean, standard deviation, key percentiles) for final NPV and critical periodic cash flows.
8.  **Visualization**:
    *   `plot_simulated_price_paths(price_paths, num_paths_to_plot=20)`: Plot a sample of the simulated future stock price paths.
    *   `plot_npv_distribution(npv_list)`: Plot a histogram of the desk's NPV across all simulations.
    *   `plot_epe_profile(epe_profile, dates)`: Plot the Expected Positive Exposure over time.

### **Phase 3: CLI & Presentation**
9.  **Main Execution Routine**: Create a `main()` or `run_simulation()` function that orchestrates the flow: fetch market data, get inputs, simulate paths, calculate cash flows, perform analysis, generate visualizations, and print a clear summary report to the console.
10. **Console Report**: The summary should print:
    *   Input parameters used.
    *   Key results: Mean Desk NPV, Std Dev of NPV, EPE at key dates.
    *   Interpretation (e.g., "Based on 1000 simulations, the swap has an expected value of $X for the desk with a standard deviation of $Y").

## **4. Sample Usage & Expected Output**

```python
# Example instantiation and run
if __name__ == "__main__":
    # Minimal params - dividend_yield, volatility, and funding_spread auto-fetched
    params = {
        'ticker': 'MSFT',
        'notional': 5_000_000,
        'tenor': 2,
        'payment_frequency': 4,
        'num_simulations': 5000,
        # Optional: provide FRED API key for benchmark rate and spread fetching
        # 'fred_api_key': 'your_api_key_here'
    }
    
    # Run the simulation - market data is fetched automatically
    summary_results, figs = run_simulation(params)
    
    # Display summary in console
    print(summary_results)
    
    # Show plots
    for fig in figs:
        plt.show()

# Example with manual overrides (skip auto-fetch for specific params)
params_manual = {
    'ticker': 'MSFT',
    'notional': 5_000_000,
    'initial_price': 420.0,          # Override: use specific price
    'dividend_yield': 0.008,          # Override: use manual yield
    'benchmark_rate': 0.05,           # Override: use manual rate
    'funding_spread': 0.02,           # Override: use manual spread
    'tenor': 2,
    'payment_frequency': 4,
    'volatility': 0.25,               # Override: use manual volatility
    'num_simulations': 5000
}
```

**Expected Console Output Snippet:**
```
=== TRS Pricing Simulation Results ===
Reference Asset: MSFT
Notional: $5,000,000
Tenor: 2.0 years
----------------------------------------
Market Data (Auto-Fetched):
  Initial Price: $420.35 (from yfinance)
  Dividend Yield: 0.82% (TTM from yfinance)
  Historical Volatility: 24.3% (1-year daily returns)
  Benchmark Rate: 5.25% (SOFR from FRED)
  Funding Spread: 1.85% (ICE BofA Corporate Index)
  Effective Funding Rate: 7.10%
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
This outline provides the complete structure, logic, and specifications needed for an AI assistant to generate the functional code for a meaningful TRS pricing tool.