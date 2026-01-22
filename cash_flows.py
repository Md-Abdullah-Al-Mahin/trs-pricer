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
        appreciation = (period_end_price - period_start_price) / period_start_price * notional
        dividends = (dividend_yield / payment_frequency) * notional
        return appreciation + dividends

    @staticmethod
    def calculate_funding_leg(
        period_start_price: float,
        period_end_price: float,
        effective_funding_rate: float,
        notional: float,
        payment_frequency: int,
    ) -> float:
        """Funding leg (client pays desk): funding amount minus depreciation (netted)."""
        funding_amount = (effective_funding_rate / payment_frequency) * notional
        depreciation = max(0.0, period_start_price - period_end_price) / period_start_price * notional
        return funding_amount - depreciation

    def calculate_cash_flows(self, price_paths: np.ndarray, params: Dict) -> List[pd.DataFrame]:
        """
        Cash flows for each simulation. Each DataFrame has period_start_price, period_end_price,
        total_return_cash_flow, net_funding_cash_flow, net_cash_flow.
        """
        notional = params["notional"]
        dividend_yield = params["dividend_yield"]
        effective_funding_rate = params["effective_funding_rate"]
        payment_frequency = params["payment_frequency"]
        n_sims, n_cols = price_paths.shape
        n_periods = n_cols - 1
        out: List[pd.DataFrame] = []
        for i in range(n_sims):
            rows = []
            for t in range(n_periods):
                p_start = price_paths[i, t]
                p_end = price_paths[i, t + 1]
                total_return = self.calculate_total_return_leg(
                    p_start, p_end, dividend_yield, notional, payment_frequency
                )
                net_funding = self.calculate_funding_leg(
                    p_start, p_end, effective_funding_rate, notional, payment_frequency
                )
                net_cf = net_funding - total_return
                rows.append({
                    "period_start_price": p_start,
                    "period_end_price": p_end,
                    "total_return_cash_flow": total_return,
                    "net_funding_cash_flow": net_funding,
                    "net_cash_flow": net_cf,
                })
            out.append(pd.DataFrame(rows))
        return out
