"""
TRS Pricer Module (Class-based)
Main orchestrator for TRS pricing simulation.
"""

from typing import Dict, Tuple, List, Any, Optional, Callable

import matplotlib.pyplot as plt
import numpy as np

from trs_pricer.config import DEFAULT_BENCHMARK_RATE
from trs_pricer.core.market_data import MarketDataFetcher
from trs_pricer.core.simulation import SimulationEngine
from trs_pricer.core.cash_flows import CashFlowEngine
from trs_pricer.core.valuation import ValuationEngine
from trs_pricer.visualization.visualization import TRSVisualizer
from trs_pricer.decision.decision_engine import TRSDecisionEngine


class TRSPricer:
    """Orchestrates market data, simulation, cash flows, valuation, and visualization."""

    def __init__(
        self,
        market_data_fetcher: Optional[MarketDataFetcher] = None,
        simulation_engine: Optional[SimulationEngine] = None,
        cash_flow_engine: Optional[CashFlowEngine] = None,
        valuation_engine: Optional[ValuationEngine] = None,
        visualizer: Optional[TRSVisualizer] = None,
        decision_engine: Optional[TRSDecisionEngine] = None,
    ):
        self._market = market_data_fetcher or MarketDataFetcher(enable_cache=True)
        self._sim = simulation_engine or SimulationEngine()
        self._cf = cash_flow_engine or CashFlowEngine()
        self._val = valuation_engine or ValuationEngine()
        self._viz = visualizer or TRSVisualizer()
        self._decision = decision_engine or TRSDecisionEngine()

    def _validate_positive(self, value: Any, name: str) -> float:
        """Validate and convert to positive float."""
        val = float(value)
        if val <= 0:
            raise ValueError(f"{name} must be positive")
        return val

    def _validate_non_negative(self, value: Any, name: str) -> float:
        """Validate and convert to non-negative float."""
        val = float(value)
        if val < 0:
            raise ValueError(f"{name} must be non-negative")
        return val

    def _get_param_or_fetch(
        self,
        params: Dict[str, Any],
        key: str,
        fetch_func: Callable[[str], float],
        ticker: str,
        validator: Optional[Callable[[Any, str], float]] = None,
    ) -> float:
        """Get parameter from dict or fetch using function. Optionally validate."""
        if key in params:
            value = params[key]
            return validator(value, key) if validator else float(value)
        return fetch_func(ticker)

    def get_user_inputs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user inputs and auto-populate market data where needed.
        Uses MarketDataFetcher for price, dividend yield, volatility, funding spread.
        Benchmark rate: user override or config default.
        
        Args:
            params: Dictionary with user-provided parameters. Required: ticker, notional,
                    tenor, payment_frequency, num_simulations.
                    Optional overrides: initial_price, dividend_yield, volatility, funding_spread, benchmark_rate.
        
        Returns:
            Dictionary with all resolved parameters including auto-fetched market data.
        
        Raises:
            ValueError: If required parameters are missing or invalid.
        """
        # Validate required parameters
        required = ["ticker", "notional", "tenor", "payment_frequency", "num_simulations"]
        missing = [p for p in required if p not in params]
        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")

        ticker = str(params["ticker"]).upper().strip()
        if not ticker:
            raise ValueError("ticker cannot be empty")

        # Validate and convert required parameters
        notional = self._validate_positive(params["notional"], "notional")
        tenor = self._validate_positive(params["tenor"], "tenor")
        payment_frequency = int(self._validate_positive(params["payment_frequency"], "payment_frequency"))
        num_simulations = int(self._validate_positive(params["num_simulations"], "num_simulations"))

        # Auto-fetch market data if not provided
        initial_price = self._get_param_or_fetch(
            params, "initial_price", self._market.fetch_current_price, ticker, self._validate_positive
        )
        dividend_yield = self._get_param_or_fetch(
            params, "dividend_yield", self._market.fetch_dividend_yield, ticker, self._validate_non_negative
        )
        volatility = self._get_param_or_fetch(
            params, "volatility", self._market.fetch_historical_volatility, ticker, self._validate_positive
        )
        funding_spread = self._get_param_or_fetch(
            params, "funding_spread", self._market.estimate_funding_spread, ticker, self._validate_non_negative
        )
        benchmark_rate = self._get_param_or_fetch(
            params, "benchmark_rate", lambda _: DEFAULT_BENCHMARK_RATE, ticker, self._validate_non_negative
        )

        return {
            "ticker": ticker,
            "notional": notional,
            "tenor": tenor,
            "payment_frequency": payment_frequency,
            "num_simulations": num_simulations,
            "initial_price": initial_price,
            "dividend_yield": dividend_yield,
            "volatility": volatility,
            "funding_spread": funding_spread,
            "benchmark_rate": benchmark_rate,
            "effective_funding_rate": benchmark_rate + funding_spread,
        }

    def run_simulation(self, params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[plt.Figure]]:
        """
        Run full pipeline: resolve inputs → simulate paths → cash flows → NPV/EPE → plots.
        Returns (summary_results, figures).
        
        Args:
            params: Dictionary with user-provided parameters (see get_user_inputs for details)
        
        Returns:
            Tuple of (summary_results, figures) where:
                - summary_results: Dictionary with aggregated statistics and metrics
                - figures: List of matplotlib Figure objects for all plots
        """
        # Step 1: Resolve all parameters (auto-fetch market data if needed)
        resolved_params = self.get_user_inputs(params)
        
        # Step 2: Simulate price paths using GBM
        price_paths = self._sim.simulate_price_paths(
            initial_price=resolved_params["initial_price"],
            tenor=resolved_params["tenor"],
            volatility=resolved_params["volatility"],
            payment_frequency=resolved_params["payment_frequency"],
            num_simulations=resolved_params["num_simulations"],
            benchmark_rate=resolved_params["benchmark_rate"],
        )
        
        # Step 3: Calculate cash flows for each simulation path
        cash_flows_list = self._cf.calculate_cash_flows(price_paths, resolved_params)
        
        # Step 4: Calculate NPV for each path
        npv_list = [
            self._val.calculate_npv(
                cash_flows_df["net_cash_flow"],
                resolved_params["benchmark_rate"],
                resolved_params["payment_frequency"],
            )
            for cash_flows_df in cash_flows_list
        ]
        
        # Step 5: Calculate exposure metrics (EPE profile)
        epe_profile, epe_dates = self._val.calculate_exposure_metrics(cash_flows_list, resolved_params)
        
        # Step 6: Aggregate results (summary statistics)
        summary_results = self._val.aggregate_results(cash_flows_list, npv_list)
        
        # Add additional metadata to summary_results
        summary_results.update({
            "ticker": resolved_params["ticker"],
            "notional": resolved_params["notional"],
            "tenor": resolved_params["tenor"],
            "payment_frequency": resolved_params["payment_frequency"],
            "num_simulations": resolved_params["num_simulations"],
            "initial_price": resolved_params["initial_price"],
            "dividend_yield": resolved_params["dividend_yield"],
            "volatility": resolved_params["volatility"],
            "funding_spread": resolved_params["funding_spread"],
            "benchmark_rate": resolved_params["benchmark_rate"],
            "effective_funding_rate": resolved_params["effective_funding_rate"],
            "epe_profile": epe_profile,
            "epe_dates": epe_dates,
            "peak_epe": float(np.max(epe_profile)) if len(epe_profile) > 0 else 0.0,
            "peak_epe_period": int(np.argmax(epe_profile)) + 1 if len(epe_profile) > 0 else 0,
        })
        
        # Step 7: Generate all plots
        figures = []
        
        # Plot simulated price paths
        fig1 = self._viz.plot_simulated_price_paths(
            price_paths,
            num_paths_to_plot=20,
            tenor=resolved_params["tenor"],
            payment_frequency=resolved_params["payment_frequency"],
        )
        figures.append(fig1)
        
        # Plot NPV distribution
        fig2 = self._viz.plot_npv_distribution(npv_list)
        figures.append(fig2)
        
        # Plot EPE profile
        fig3 = self._viz.plot_epe_profile(epe_profile, epe_dates)
        figures.append(fig3)
        
        # Plot cash flow analysis
        fig4 = self._viz.plot_cash_flow_analysis(cash_flows_list, num_simulations_to_plot=10)
        figures.append(fig4)
        
        return summary_results, figures

    def generate_summary_report(self, summary_results: Dict[str, Any]) -> str:
        """
        Format simulation results as a console report.
        
        Args:
            summary_results: Dictionary with simulation results from run_simulation
        
        Returns:
            Formatted string report with trade details, market data, valuation, and risk metrics
        """
        lines = []
        lines.append("=== TRS Pricing Simulation Results ===")
        lines.append(f"Reference Asset: {summary_results['ticker']}")
        lines.append(f"Notional: ${summary_results['notional']:,.0f}")
        lines.append(f"Tenor: {summary_results['tenor']} years")
        lines.append("-" * 40)
        
        # Market Data section
        lines.append("Market Data (Auto-Fetched):")
        lines.append(f"  Initial Price: ${summary_results['initial_price']:.2f} (from yfinance)")
        lines.append(f"  Dividend Yield: {summary_results['dividend_yield']*100:.2f}% (yfinance)")
        lines.append(f"  Historical Volatility: {summary_results['volatility']*100:.1f}% (yfinance)")
        lines.append(f"  Benchmark Rate: {summary_results['benchmark_rate']*100:.2f}% (config default)")
        lines.append(f"  Funding Spread: {summary_results['funding_spread']*100:.2f}% (hybrid model)")
        lines.append(f"  Effective Funding Rate: {summary_results['effective_funding_rate']*100:.2f}%")
        lines.append("-" * 40)
        
        # Valuation section
        lines.append("Valuation (Desk's Perspective):")
        npv_mean = summary_results['npv_mean']
        npv_std = summary_results['npv_std']
        percentiles = summary_results['npv_percentiles']
        
        sign = "+" if npv_mean >= 0 else ""
        lines.append(f"  Expected NPV: {sign}${npv_mean:,.0f}")
        lines.append(f"  Std Dev of NPV: ${npv_std:,.0f}")
        lines.append(f"  5th Percentile NPV: ${percentiles['5th']:,.0f}")
        lines.append(f"  25th Percentile NPV: ${percentiles['25th']:,.0f}")
        lines.append(f"  50th Percentile NPV: ${percentiles['50th']:,.0f}")
        lines.append(f"  75th Percentile NPV: ${percentiles['75th']:,.0f}")
        lines.append(f"  95th Percentile NPV: ${percentiles['95th']:,.0f}")
        lines.append("-" * 40)
        
        # Total Cash Flows section
        lines.append("Total Cash Flows (Undiscounted, Mean Across Simulations):")
        total_return_leg = summary_results.get('total_return_leg_total', 0.0)
        funding_leg = summary_results.get('funding_leg_total', 0.0)
        lines.append(f"  Total Return Leg (Desk → Client): ${total_return_leg:,.0f}")
        lines.append(f"  Funding Leg (Client → Desk): ${funding_leg:,.0f}")
        lines.append(f"  Net Cash Flow (Undiscounted): ${funding_leg - total_return_leg:,.0f}")
        lines.append("-" * 40)
        
        # Risk Metrics section
        lines.append("Risk Metrics:")
        peak_epe = summary_results.get('peak_epe', 0.0)
        peak_epe_period = summary_results.get('peak_epe_period', 0)
        payment_frequency = summary_results.get('payment_frequency', 4)
        
        if peak_epe_period > 0:
            # Calculate time in years when peak EPE occurs
            peak_epe_time_years = peak_epe_period / payment_frequency
            lines.append(f"  Peak EPE (at {peak_epe_time_years:.2f} years): ${peak_epe:,.0f}")
        else:
            lines.append(f"  Peak EPE: ${peak_epe:,.0f}")
        
        # Additional simulation info
        lines.append("-" * 40)
        lines.append(f"Simulation Details:")
        lines.append(f"  Number of Simulations: {summary_results.get('num_simulations', 0):,}")
        lines.append(f"  Payment Frequency: {payment_frequency} per year")
        
        return "\n".join(lines)

    def evaluate_decision(self, summary_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a trade using the decision dashboard engine.
        
        This method provides programmatic access to the decision dashboard functionality.
        It consumes the summary_results from run_simulation() and returns decision
        recommendations with status, metrics, issues, and adjustments.
        
        Args:
            summary_results: Dictionary from TRSPricer.run_simulation() containing:
                - npv_mean: Mean NPV
                - npv_percentiles: Dictionary with percentiles (5th, 25th, 50th, 75th, 95th)
                - peak_epe: Peak Expected Positive Exposure
                - notional: Notional amount
                - tenor: Tenor in years
                - funding_spread: Current funding spread
                - Other simulation metadata
        
        Returns:
            Dictionary with decision results:
                - overall_status: "green", "yellow", or "red"
                - metrics: Dictionary with npv_pct, var_pct, epe_pct (as fractions of notional)
                - statuses: Dictionary with individual metric statuses (npv, var, epe)
                - issues: List of issue descriptions (if any)
                - adjustments: Dictionary with adjustment suggestions (if any):
                    - spread_adjustment: {"delta_bps": float, "new_spread": float}
                    - notional_reduction: {"reduction_pct": float, "new_notional": float}
                    - collateral_requirement: {"collateral_pct": float, "collateral_amount": float}
        
        Example:
            >>> pricer = TRSPricer()
            >>> summary_results, figures = pricer.run_simulation(params)
            >>> decision_results = pricer.evaluate_decision(summary_results)
            >>> print(f"Overall status: {decision_results['overall_status']}")
        """
        return self._decision.evaluate_trade(summary_results)