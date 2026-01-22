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
        raise NotImplementedError

    def run_simulation(self, params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[plt.Figure]]:
        """
        Run full pipeline: resolve inputs → simulate paths → cash flows → NPV/EPE → plots.
        Returns (summary_results, figures).
        """
        raise NotImplementedError

    def generate_summary_report(self, summary_results: Dict[str, Any]) -> str:
        """Format simulation results as a console report."""
        raise NotImplementedError