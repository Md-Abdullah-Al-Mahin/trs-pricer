"""
Configuration Module (Phase 1, Step 1)
Contains all FRED series IDs, default values, and constants used throughout
the TRS pricing simulator. See README Section 2.1 and 2.1.1.
"""

# -----------------------------------------------------------------------------
# FRED Series IDs (Section 2.1.1)
# -----------------------------------------------------------------------------
FRED_SERIES_IDS = {
    "sofr": "SOFR",  # Secured Overnight Financing Rate (primary benchmark)
    "fed_funds": "FEDFUNDS",  # Fed Funds Rate (benchmark fallback)
    "corporate_oas": "BAMLC0A0CM",  # ICE BofA US Corporate Index OAS
    "high_yield_oas": "BAMLH0A0HYM2",  # ICE BofA US High Yield Index OAS
}

# -----------------------------------------------------------------------------
# Default Values (Section 2.1 – fallbacks when market data unavailable)
# -----------------------------------------------------------------------------
DEFAULT_BENCHMARK_RATE = 0.05  # 5% (e.g. SOFR)
DEFAULT_FUNDING_SPREAD = 0.015  # 1.5%
DEFAULT_VOLATILITY = 0.25  # 25% annualized
DEFAULT_DIVIDEND_YIELD = 0.0  # 0%

# Trade / simulation defaults (Section 2.1)
DEFAULT_TENOR = 1  # years
DEFAULT_PAYMENT_FREQUENCY = 4  # e.g. 4 = quarterly
DEFAULT_NUM_SIMULATIONS = 1000
DEFAULT_NOTIONAL = 10_000_000  # for examples only; typically user-provided

# -----------------------------------------------------------------------------
# Market Data & Volatility (Section 2.1.1)
# -----------------------------------------------------------------------------
DEFAULT_LOOKBACK_DAYS = 252  # 1 year of trading days for volatility
TRADING_DAYS_PER_YEAR = 252  # for annualization (e.g. sqrt(252) in vol)

# -----------------------------------------------------------------------------
# Environment / API
# -----------------------------------------------------------------------------
FRED_API_KEY_ENV = "FRED_API_KEY"  # optional; also passable via params

# -----------------------------------------------------------------------------
# Decision Dashboard Thresholds
# -----------------------------------------------------------------------------
# Thresholds for TRS Decision Dashboard traffic light system
# All thresholds are expressed as fractions of notional (e.g., 0.01 = 1% of notional)

# NPV (Net Present Value) thresholds - profitability metric
DECISION_NPV_GREEN_THRESHOLD = 0.01  # 1% of notional - Green: trade is sufficiently profitable
DECISION_NPV_YELLOW_THRESHOLD = 0.005  # 0.5% of notional - Yellow: marginal profitability

# VaR (Value at Risk) thresholds - tail risk metric (using 5th percentile)
# Note: VaR is measured as absolute value of negative tail (5th percentile NPV).
# Full-life TRS VaR (5th %ile NPV / notional) is often 35-55% for typical vol/tenor;
# previous 15%/25% were too tight and caused VaR to never be green.
DECISION_VAR_GREEN_THRESHOLD = 0.40  # 40% of notional - Green: acceptable tail risk
DECISION_VAR_YELLOW_THRESHOLD = 0.55  # 55% of notional - Yellow: elevated tail risk

# EPE (Expected Positive Exposure) thresholds - credit risk metric
# Updated to more realistic levels for TRS trades (especially volatile stocks)
DECISION_EPE_GREEN_THRESHOLD = 0.10  # 10% of notional - Green: acceptable credit exposure
DECISION_EPE_YELLOW_THRESHOLD = 0.20  # 20% of notional - Yellow: elevated credit exposure
