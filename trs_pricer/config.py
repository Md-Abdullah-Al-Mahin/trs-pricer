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
# Hedging Configuration (Project Extension: Hedging Recommendation Module)
# -----------------------------------------------------------------------------

class HedgingConfig:
    """Configuration constants for hedging recommendations."""
    
    # Option hedge parameters
    DEFAULT_TARGET_PUT_DELTA = -0.20  # Target delta for protective puts (20% OTM)
    DEFAULT_PUT_STRIKE_PERCENTAGE = 0.90  # Strike as % of spot (90% = 10% OTM)
    DEFAULT_OPTION_CONTRACT_SIZE = 100  # Standard equity option contract size
    
    # Futures hedge parameters
    DEFAULT_FUTURES_CONTRACT_SIZE = 100  # Standard equity futures contract size
    DEFAULT_TARGET_HEDGE_RATIO = 1.0  # Full hedge (1.0 = 100% of notional)
    
    # Interest Rate Swap parameters
    DEFAULT_IRS_FIXED_RATE_BUFFER = 0.0015  # 15 bps buffer above benchmark for fixed leg
    
    # Value-at-Risk parameters for dynamic hedging
    DEFAULT_VAR_CONFIDENCE_LEVEL = 0.95  # 95% VaR
    DEFAULT_PROTECTION_LEVEL = 0.90  # Protect against 90% of downside scenarios
    
    # Hedge cost estimation
    DEFAULT_OPTION_PREMIUM_ESTIMATE = 0.05  # Rough estimate: 5% of notional for puts
    DEFAULT_IRS_BID_ASK_SPREAD = 0.0005  # 5 bps bid-ask spread for IRS
