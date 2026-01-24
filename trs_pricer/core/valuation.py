"""
Valuation Module (Class-based)
Handles NPV calculation and risk metrics (EPE, exposure profiles).
See README Section 2.2.C.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


class ValuationEngine:
    """NPV discounting, marked-to-market, EPE, and summary statistics."""

    @staticmethod
    def _discount_cash_flows(cash_flows: np.ndarray, period_rate: float, start_period: int = 1) -> float:
        """Helper: discount cash flows starting from start_period."""
        if len(cash_flows) == 0:
            return 0.0
        periods = np.arange(start_period, start_period + len(cash_flows))
        discount_factors = (1 + period_rate) ** (-periods)
        return float(np.sum(cash_flows * discount_factors))

    @staticmethod
    def calculate_npv(
        cash_flows_series: pd.Series,
        benchmark_rate: float,
        payment_frequency: int,
    ) -> float:
        """Calculate NPV by discounting net cash flows at benchmark_rate per period."""
        if len(cash_flows_series) == 0:
            return 0.0
        period_rate = benchmark_rate / payment_frequency
        return ValuationEngine._discount_cash_flows(cash_flows_series.values, period_rate)

    def calculate_marked_to_market_value(
        self,
        cash_flows_df: pd.DataFrame,
        benchmark_rate: float,
        payment_frequency: int,
        current_period: int,
    ) -> float:
        """Calculate MTM at current_period = PV of future net cash flows from that period onward."""
        if current_period > len(cash_flows_df):
            return 0.0
        future_flows = cash_flows_df.iloc[current_period - 1:]["net_cash_flow"].values
        if len(future_flows) == 0:
            return 0.0
        period_rate = benchmark_rate / payment_frequency
        return self._discount_cash_flows(future_flows, period_rate)

    def calculate_exposure_metrics(
        self,
        cash_flows_list: List[pd.DataFrame],
        params: Dict,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate EPE profile: at each period, average of max(0, MTM) across paths."""
        if not cash_flows_list:
            return np.array([]), np.array([])
        
        benchmark_rate = params["benchmark_rate"]
        payment_frequency = params["payment_frequency"]
        num_periods = len(cash_flows_list[0])
        
        # Calculate MTM for each path at each period
        mtm_matrix = np.array([
            [self.calculate_marked_to_market_value(df, benchmark_rate, payment_frequency, p + 1)
             for p in range(num_periods)]
            for df in cash_flows_list
        ])
        
        # EPE = average of max(0, MTM) across paths for each period
        epe_profile = np.mean(np.maximum(0, mtm_matrix), axis=0)
        
        # Generate dates for each period
        start_date = datetime.now()
        period_days = int(365 / payment_frequency)
        dates = np.array([start_date + timedelta(days=period_days * p) for p in range(1, num_periods + 1)])
        
        return epe_profile, dates

    def aggregate_results(
        self,
        all_simulated_cash_flows: List[pd.DataFrame],
        npv_list: List[float],
    ) -> Dict:
        """Calculate summary statistics: mean/std NPV, percentiles, mean periodic net cash flows."""
        npv_array = np.array(npv_list)
        percentiles = [5, 25, 50, 75, 95]
        
        mean_periodic_flows = (
            [float(np.mean([df.iloc[p]["net_cash_flow"] for df in all_simulated_cash_flows]))
             for p in range(len(all_simulated_cash_flows[0]))]
            if all_simulated_cash_flows else []
        )
        
        return {
            "npv_mean": float(np.mean(npv_array)),
            "npv_std": float(np.std(npv_array)),
            "npv_percentiles": {f"{p}th": float(np.percentile(npv_array, p)) for p in percentiles},
            "mean_periodic_net_cash_flows": mean_periodic_flows,
        }
    
    def calculate_delta_exposure(
        self,
        cash_flows_list: List[pd.DataFrame],
        price_paths: np.ndarray,
        params: Dict,
    ) -> float:
        """
        Calculate approximate delta exposure: sensitivity of TRS NPV to changes in underlying stock price.
        
        Uses finite difference approximation: delta ≈ (NPV_up - NPV_down) / (2 * price_shock)
        where NPV_up/down are NPVs calculated with shocked prices.
        
        Args:
            cash_flows_list: List of cash flow DataFrames (from original simulation)
            price_paths: Original simulated price paths
            params: Dictionary with benchmark_rate, payment_frequency, notional, etc.
        
        Returns:
            Estimated delta exposure (dNPV/dPrice)
        """
        # TODO: Implement delta calculation using finite difference or analytical approximation
        raise NotImplementedError
    
    def calculate_funding_rate_exposure(
        self,
        cash_flows_list: List[pd.DataFrame],
        params: Dict,
    ) -> float:
        """
        Calculate funding rate exposure: present value of the floating funding leg.
        
        This isolates the interest rate risk component of the TRS.
        
        Args:
            cash_flows_list: List of cash flow DataFrames
            params: Dictionary with benchmark_rate, payment_frequency, notional, effective_funding_rate
        
        Returns:
            Present value of funding leg (positive = liability, negative = asset)
        """
        # TODO: Implement funding rate exposure calculation
        raise NotImplementedError
