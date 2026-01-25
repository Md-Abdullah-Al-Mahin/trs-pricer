"""
Futures Model (Project Extension: Hedging Recommendation Module)
Models equity futures contracts for delta hedging.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class FuturesHedge:
    """
    Represents an equity futures hedge position.
    
    Attributes:
        ticker: Underlying stock ticker
        notional: Notional amount to hedge
        current_price: Current stock price
        contract_size: Number of shares per futures contract (default: 100)
        target_hedge_ratio: Target hedge ratio (1.0 = 100% hedge)
        num_contracts: Calculated number of contracts needed
        hedge_notional: Effective notional hedged (num_contracts * contract_size * price)
    """
    
    ticker: str
    notional: float
    current_price: float
    contract_size: int = 100
    target_hedge_ratio: float = 1.0
    num_contracts: int = 0
    hedge_notional: float = 0.0
    
    def __post_init__(self):
        """Calculate number of contracts and hedge notional after initialization."""
        if self.current_price <= 0:
            raise ValueError("current_price must be positive")
        if self.contract_size <= 0:
            raise ValueError("contract_size must be positive")

        # Calculate number of contracts needed
        shares_to_hedge = (self.notional * self.target_hedge_ratio) / self.current_price
        self.num_contracts = int(round(shares_to_hedge / self.contract_size))

        # Effective hedge notional
        self.hedge_notional = self.num_contracts * self.contract_size * self.current_price
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "type": "FUTURES",
            "ticker": self.ticker,
            "notional": self.notional,
            "current_price": self.current_price,
            "contract_size": self.contract_size,
            "target_hedge_ratio": self.target_hedge_ratio,
            "num_contracts": self.num_contracts,
            "hedge_notional": self.hedge_notional,
            "estimated_cost": 0.0,  # Futures typically have minimal upfront cost (margin only)
        }
