"""
Valuation Module (Class-based)
Handles NPV calculation and risk metrics (EPE, exposure profiles).
See README Section 2.2.C.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple


class ValuationEngine:
    """NPV discounting, marked-to-market, EPE, and summary statistics."""

    @staticmethod
    def calculate_npv(
        cash_flows_series: pd.Series,
        benchmark_rate: float,
        payment_frequency: int,
    ) -> float:
        """NPV by discounting net cash flows at benchmark_rate."""
        raise NotImplementedError

    def calculate_marked_to_market_value(
        self,
        cash_flows_df: pd.DataFrame,
        benchmark_rate: float,
        payment_frequency: int,
        current_period: int,
    ) -> float:
        """MTM at current_period = PV of future net cash flows from that period onward."""
        raise NotImplementedError

    def calculate_exposure_metrics(
        self,
        cash_flows_list: List[pd.DataFrame],
        params: Dict,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """EPE profile: at each period, average of max(0, MTM) across paths. Returns (epe_profile, dates)."""
        raise NotImplementedError

    def aggregate_results(
        self,
        all_simulated_cash_flows: List[pd.DataFrame],
        npv_list: List[float],
    ) -> Dict:
        """Summary stats: mean/std NPV, percentiles, mean periodic net cash flows."""
        raise NotImplementedError
