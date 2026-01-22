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
        if cash_flows_series.empty:
            return 0.0
        n = len(cash_flows_series)
        discount = np.power(1.0 + benchmark_rate / payment_frequency, np.arange(1, n + 1))
        return float(np.sum(cash_flows_series.values / discount))

    def calculate_marked_to_market_value(
        self,
        cash_flows_df: pd.DataFrame,
        benchmark_rate: float,
        payment_frequency: int,
        current_period: int,
    ) -> float:
        """MTM at current_period = PV of future net cash flows from that period onward."""
        if "net_cash_flow" not in cash_flows_df.columns or current_period >= len(cash_flows_df):
            return 0.0
        future = cash_flows_df["net_cash_flow"].iloc[current_period:]
        n = len(future)
        discount = np.power(1.0 + benchmark_rate / payment_frequency, np.arange(1, n + 1))
        return float(np.sum(future.values / discount))

    def calculate_exposure_metrics(
        self,
        cash_flows_list: List[pd.DataFrame],
        params: Dict,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """EPE profile: at each period, average of max(0, MTM) across paths. Returns (epe_profile, dates)."""
        payment_frequency = params["payment_frequency"]
        benchmark_rate = params["benchmark_rate"]
        n_periods = len(cash_flows_list[0]) if cash_flows_list else 0
        mtm = np.zeros((len(cash_flows_list), n_periods + 1))
        for i, df in enumerate(cash_flows_list):
            for t in range(n_periods + 1):
                mtm[i, t] = self.calculate_marked_to_market_value(
                    df, benchmark_rate, payment_frequency, t
                )
        dates = np.arange(n_periods + 1, dtype=float) / payment_frequency
        epe = np.mean(np.maximum(mtm, 0.0), axis=0)
        return epe, dates

    def aggregate_results(
        self,
        all_simulated_cash_flows: List[pd.DataFrame],
        npv_list: List[float],
    ) -> Dict:
        """Summary stats: mean/std NPV, percentiles, mean periodic net cash flows."""
        npv_arr = np.array(npv_list)
        percentiles = [5, 25, 50, 75, 95]
        pct = {p: float(np.percentile(npv_arr, p)) for p in percentiles}
        mean_cf = None
        if all_simulated_cash_flows:
            stacked = np.array([df["net_cash_flow"].values for df in all_simulated_cash_flows])
            mean_cf = np.mean(stacked, axis=0).tolist()
        return {
            "mean_npv": float(np.mean(npv_arr)),
            "std_npv": float(np.std(npv_arr)),
            "percentiles": pct,
            "mean_periodic_cash_flows": mean_cf,
        }
