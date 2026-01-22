"""
TRS Pricer Module (Class-based)
Main orchestrator for TRS pricing simulation.
"""

from typing import Dict, Tuple, List, Any, Optional

import numpy as np
import matplotlib.pyplot as plt

from config import (
    DEFAULT_BENCHMARK_RATE,
    DEFAULT_LOOKBACK_DAYS,
)
from market_data import MarketDataFetcher
from simulation import SimulationEngine
from cash_flows import CashFlowEngine
from valuation import ValuationEngine
from visualization import TRSVisualizer


class TRSPricer:
    """Orchestrates market data, simulation, cash flows, valuation, and visualization."""

    def __init__(
        self,
        market_data_fetcher: Optional[MarketDataFetcher] = None,
        simulation_engine: Optional[SimulationEngine] = None,
        cash_flow_engine: Optional[CashFlowEngine] = None,
        valuation_engine: Optional[ValuationEngine] = None,
        visualizer: Optional[TRSVisualizer] = None,
    ):
        self._market = market_data_fetcher or MarketDataFetcher(enable_cache=True)
        self._sim = simulation_engine or SimulationEngine()
        self._cf = cash_flow_engine or CashFlowEngine()
        self._val = valuation_engine or ValuationEngine()
        self._viz = visualizer or TRSVisualizer()

    def get_user_inputs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user inputs and auto-populate market data where needed.
        Uses MarketDataFetcher for price, dividend yield, volatility, funding spread.
        Benchmark rate: user override or config default.
        """
        ticker = params["ticker"]
        if "initial_price" not in params or params["initial_price"] is None:
            params["initial_price"] = self._market.fetch_current_price(ticker)
        if "dividend_yield" not in params or params["dividend_yield"] is None:
            params["dividend_yield"] = self._market.fetch_dividend_yield(ticker)
        if "benchmark_rate" not in params or params["benchmark_rate"] is None:
            params["benchmark_rate"] = DEFAULT_BENCHMARK_RATE
        if "funding_spread" not in params or params["funding_spread"] is None:
            params["funding_spread"] = self._market.estimate_funding_spread(ticker)
        params["effective_funding_rate"] = params["benchmark_rate"] + params["funding_spread"]
        if "volatility" not in params or params["volatility"] is None:
            params["volatility"] = self._market.fetch_historical_volatility(
                ticker, lookback_days=DEFAULT_LOOKBACK_DAYS
            )
        return params

    def run_simulation(self, params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[plt.Figure]]:
        """
        Run full pipeline: resolve inputs → simulate paths → cash flows → NPV/EPE → plots.
        Returns (summary_results, figures).
        """
        params = self.get_user_inputs(params)
        paths = self._sim.simulate_price_paths(
            params["initial_price"],
            params["tenor"],
            params["volatility"],
            params["payment_frequency"],
            params["num_simulations"],
            benchmark_rate=params["benchmark_rate"],
        )
        cash_flows = self._cf.calculate_cash_flows(paths, params)
        npv_list = [
            self._val.calculate_npv(
                df["net_cash_flow"],
                params["benchmark_rate"],
                params["payment_frequency"],
            )
            for df in cash_flows
        ]
        epe_profile, epe_dates = self._val.calculate_exposure_metrics(cash_flows, params)
        aggregated = self._val.aggregate_results(cash_flows, npv_list)

        figs = [
            self._viz.plot_simulated_price_paths(
                paths,
                num_paths_to_plot=20,
                tenor=params["tenor"],
                payment_frequency=params["payment_frequency"],
            ),
            self._viz.plot_npv_distribution(npv_list),
            self._viz.plot_epe_profile(epe_profile, epe_dates),
        ]

        summary = {
            "params": params,
            "price_paths": paths,
            "cash_flows": cash_flows,
            "npv_list": npv_list,
            "epe_profile": epe_profile,
            "epe_dates": epe_dates,
            "aggregated": aggregated,
        }
        return summary, figs

    def generate_summary_report(self, summary_results: Dict[str, Any]) -> str:
        """Format simulation results as a console report."""
        p = summary_results["params"]
        agg = summary_results["aggregated"]
        epe = summary_results["epe_profile"]
        epe_dates = summary_results["epe_dates"]

        peak_idx = int(np.argmax(epe))
        peak_epe = epe[peak_idx]
        peak_year = epe_dates[peak_idx]

        lines = [
            "=== TRS Pricing Simulation Results ===",
            f"Reference Asset: {p['ticker']}",
            f"Notional: ${p['notional']:,.0f}",
            f"Tenor: {p['tenor']} years",
            "----------------------------------------",
            "Market Data (Auto-Fetched):",
            f"  Initial Price: ${p['initial_price']:.2f} (from yfinance)",
            f"  Dividend Yield: {p['dividend_yield']*100:.2f}% (yfinance)",
            f"  Historical Volatility: {p['volatility']*100:.1f}% (yfinance)",
            f"  Benchmark Rate: {p['benchmark_rate']*100:.2f}% (config default)",
            f"  Funding Spread: {p['funding_spread']*100:.2f}% (hybrid model)",
            f"  Effective Funding Rate: {p['effective_funding_rate']*100:.2f}%",
            "----------------------------------------",
            "Valuation (Desk's Perspective):",
            f"  Expected NPV: ${agg['mean_npv']:+,.0f}",
            f"  Std Dev of NPV: ${agg['std_npv']:,.0f}",
            f"  5th Percentile NPV: ${agg['percentiles'][5]:+,.0f}",
            f"  95th Percentile NPV: ${agg['percentiles'][95]:+,.0f}",
            "----------------------------------------",
            "Risk Metrics:",
            f"  Peak EPE (at {peak_year:.2f} years): ${peak_epe:,.0f}",
        ]
        return "\n".join(lines)


_default_pricer = TRSPricer()


def get_user_inputs(params: Dict[str, Any]) -> Dict[str, Any]:
    """Process and resolve parameters (delegates to default TRSPricer)."""
    return _default_pricer.get_user_inputs(params)


def run_simulation(params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[plt.Figure]]:
    """Run simulation (delegates to default TRSPricer)."""
    return _default_pricer.run_simulation(params)


def generate_summary_report(summary_results: Dict[str, Any]) -> str:
    """Generate console report (delegates to default TRSPricer)."""
    return _default_pricer.generate_summary_report(summary_results)
