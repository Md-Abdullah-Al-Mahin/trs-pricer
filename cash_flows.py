"""
Cash Flow Module (Class-based)
Handles calculation of periodic cash flows for TRS.
See README Section 2.2.B.
"""

import numpy as np
import pandas as pd
from typing import Dict, List


class CashFlowEngine:
    """Computes total return leg, funding leg, and net cash flows per path and period."""

    @staticmethod
    def calculate_total_return_leg(
        period_start_price: float,
        period_end_price: float,
        dividend_yield: float,
        notional: float,
        payment_frequency: int,
    ) -> float:
        """Total return leg (desk pays client): appreciation + dividends."""
        raise NotImplementedError

    @staticmethod
    def calculate_funding_leg(
        period_start_price: float,
        period_end_price: float,
        effective_funding_rate: float,
        notional: float,
        payment_frequency: int,
    ) -> float:
        """Funding leg (client pays desk): funding amount minus depreciation (netted)."""
        raise NotImplementedError

    def calculate_cash_flows(self, price_paths: np.ndarray, params: Dict) -> List[pd.DataFrame]:
        """
        Cash flows for each simulation. Each DataFrame has period_start_price, period_end_price,
        total_return_cash_flow, net_funding_cash_flow, net_cash_flow.
        """
        raise NotImplementedError
