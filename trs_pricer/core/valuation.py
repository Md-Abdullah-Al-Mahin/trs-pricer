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
        # #region agent log
        import json
        with open('/Users/mdabdullahalmahin/Desktop/Projects/trs-pricer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"D","location":"valuation.py:34","message":"NPV calculation inputs","data":{"benchmark_rate":benchmark_rate,"payment_frequency":payment_frequency,"period_rate":period_rate,"num_periods":len(cash_flows_series),"cash_flows":cash_flows_series.values.tolist()},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        npv = ValuationEngine._discount_cash_flows(cash_flows_series.values, period_rate)
        # #region agent log
        with open('/Users/mdabdullahalmahin/Desktop/Projects/trs-pricer/.cursor/debug.log', 'a') as f:
            periods = __import__('numpy').arange(1, len(cash_flows_series) + 1)
            discount_factors = (1 + period_rate) ** (-periods)
            discounted_flows = cash_flows_series.values * discount_factors
            f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"D","location":"valuation.py:40","message":"NPV calculation result","data":{"npv":npv,"discount_factors":discount_factors.tolist(),"discounted_flows":discounted_flows.tolist(),"sum_undiscounted":float(__import__('numpy').sum(cash_flows_series.values))},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        return npv

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
        """Calculate summary statistics: mean/std NPV, percentiles, mean periodic net cash flows, and total cash flows for both legs."""
        npv_array = np.array(npv_list)
        percentiles = [5, 25, 50, 75, 95]
        
        mean_periodic_flows = (
            [float(np.mean([df.iloc[p]["net_cash_flow"] for df in all_simulated_cash_flows]))
             for p in range(len(all_simulated_cash_flows[0]))]
            if all_simulated_cash_flows else []
        )
        
        # Calculate total cash flows for both legs (sum across all periods, mean across simulations)
        if all_simulated_cash_flows:
            total_return_leg_totals = [
                float(df["total_return_cash_flow"].sum()) for df in all_simulated_cash_flows
            ]
            funding_leg_totals = [
                float(df["net_funding_cash_flow"].sum()) for df in all_simulated_cash_flows
            ]
            mean_total_return_leg = float(np.mean(total_return_leg_totals))
            mean_funding_leg = float(np.mean(funding_leg_totals))
        else:
            mean_total_return_leg = 0.0
            mean_funding_leg = 0.0
        
        return {
            "npv_mean": float(np.mean(npv_array)),
            "npv_std": float(np.std(npv_array)),
            "npv_percentiles": {f"{p}th": float(np.percentile(npv_array, p)) for p in percentiles},
            "mean_periodic_net_cash_flows": mean_periodic_flows,
            "total_return_leg_total": mean_total_return_leg,
            "funding_leg_total": mean_funding_leg,
        }
    
    def calculate_delta_exposure(
        self,
        cash_flows_list: List[pd.DataFrame],
        price_paths: np.ndarray,
        params: Dict,
    ) -> float:
        """Calculate approximate delta exposure using finite difference method."""
        if price_paths.size == 0 or not cash_flows_list:
            return 0.0

        initial_price = price_paths[0, 0]
        notional = params.get("notional", 0.0)

        # Simple approximation: Delta ≈ notional / initial_price for a TRS
        return notional / initial_price if initial_price > 0 else 0.0
    
    def calculate_funding_rate_exposure(
        self,
        cash_flows_list: List[pd.DataFrame],
        params: Dict,
    ) -> float:
        """Calculate PV of funding leg to isolate interest rate risk."""
        if not cash_flows_list:
            return 0.0

        benchmark_rate = params.get("benchmark_rate", 0.0)
        payment_frequency = params.get("payment_frequency", 4)
        period_rate = benchmark_rate / payment_frequency

        # Sum up all funding leg cash flows across all paths and periods
        total_funding_pv = 0.0
        for df in cash_flows_list:
            for period_idx, row in df.iterrows():
                period = row["period"]
                funding_flow = row.get("net_funding_cash_flow", 0.0)
                discount_factor = (1 + period_rate) ** (-period)
                total_funding_pv += funding_flow * discount_factor

        # Average across all simulations
        return total_funding_pv / len(cash_flows_list)
