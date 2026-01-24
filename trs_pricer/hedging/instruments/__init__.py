"""
Instruments Module (Project Extension: Hedging Recommendation Module)
Contains models for financial instruments used in hedging strategies.
"""

from .futures_model import FuturesHedge
from .swap_model import InterestRateSwapHedge
from .options_model import OptionsHedge

__all__ = ["FuturesHedge", "InterestRateSwapHedge", "OptionsHedge"]
