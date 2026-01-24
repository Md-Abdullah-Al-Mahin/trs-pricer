"""
Options Model (Project Extension: Hedging Recommendation Module)
Models equity options (puts/calls) for protective hedging strategies.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class OptionsHedge:
    """
    Represents an equity options hedge position.
    
    Attributes:
        ticker: Underlying stock ticker
        option_type: "PUT" or "CALL"
        strike_price: Strike price of the option
        current_price: Current stock price (spot)
        notional: Notional amount to protect
        contract_size: Number of shares per option contract (default: 100)
        num_contracts: Number of option contracts
        estimated_premium: Estimated option premium cost
        expiry_years: Time to expiry in years
        target_delta: Target option delta (for dynamic hedging)
    """
    
    ticker: str
    option_type: str  # "PUT" or "CALL"
    strike_price: float
    current_price: float
    notional: float
    contract_size: int = 100
    num_contracts: int = 0
    estimated_premium: float = 0.0
    expiry_years: Optional[float] = None
    target_delta: Optional[float] = None
    
    def __post_init__(self):
        """Calculate number of contracts and validate after initialization."""
        if self.current_price <= 0:
            raise ValueError("current_price must be positive")
        if self.strike_price <= 0:
            raise ValueError("strike_price must be positive")
        if self.contract_size <= 0:
            raise ValueError("contract_size must be positive")

        # Calculate number of contracts needed to hedge notional
        shares_to_hedge = self.notional / self.current_price
        self.num_contracts = int(round(shares_to_hedge / self.contract_size))

        # Estimate premium if not provided (rough approximation based on moneyness)
        if self.estimated_premium == 0.0:
            moneyness = self.strike_price / self.current_price

            # Base premium rate: 5% of notional (rough estimate for ATM options)
            base_premium_rate = 0.05

            # Adjust premium based on moneyness and option type
            if self.option_type.upper() == "PUT":
                # For puts: OTM (moneyness < 1.0) = lower premium, ITM (moneyness > 1.0) = higher premium
                if moneyness < 0.9:  # Deep OTM
                    premium_multiplier = 0.6
                elif moneyness < 0.95:  # OTM
                    premium_multiplier = 0.75
                elif moneyness < 1.0:  # Slightly OTM
                    premium_multiplier = 0.9
                elif moneyness < 1.05:  # Slightly ITM
                    premium_multiplier = 1.1
                elif moneyness < 1.1:  # ITM
                    premium_multiplier = 1.3
                else:  # Deep ITM
                    premium_multiplier = 1.5
            else:  # CALL
                # For calls: OTM (moneyness > 1.0) = lower premium, ITM (moneyness < 1.0) = higher premium
                if moneyness > 1.1:  # Deep OTM
                    premium_multiplier = 0.6
                elif moneyness > 1.05:  # OTM
                    premium_multiplier = 0.75
                elif moneyness > 1.0:  # Slightly OTM
                    premium_multiplier = 0.9
                elif moneyness > 0.95:  # Slightly ITM
                    premium_multiplier = 1.1
                elif moneyness > 0.9:  # ITM
                    premium_multiplier = 1.3
                else:  # Deep ITM
                    premium_multiplier = 1.5

            premium_rate = base_premium_rate * premium_multiplier
            self.estimated_premium = self.notional * premium_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        # TODO: Implement dictionary conversion
        raise NotImplementedError
