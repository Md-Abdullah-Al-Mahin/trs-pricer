"""
Configuration Module
Contains constants and default values for TRS pricing
"""

# FRED Series IDs for Spread Estimation
FRED_SERIES_IDS = {
    'corporate_index': 'BAMLC0A0CM',  # ICE BofA US Corporate Index Option-Adjusted Spread
    'high_yield_index': 'BAMLH0A0HYM2',  # ICE BofA US High Yield Index Option-Adjusted Spread
    'sofr': 'SOFR'  # Secured Overnight Financing Rate
}

# Default values (fallbacks)
DEFAULT_BENCHMARK_RATE = 0.05  # 5%
DEFAULT_FUNDING_SPREAD = 0.015  # 1.5%
DEFAULT_VOLATILITY = 0.25  # 25%
DEFAULT_DIVIDEND_YIELD = 0.0  # 0%

# Simulation defaults
DEFAULT_LOOKBACK_DAYS = 252  # 1 year of trading days
DEFAULT_NUM_SIMULATIONS = 1000

# Trading days per year
TRADING_DAYS_PER_YEAR = 252
