"""
Visualization Module (Class-based)
Handles plotting of simulation results, NPV distributions, and EPE profiles.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List, Optional


class TRSVisualizer:
    """Plots simulated price paths, NPV distribution, EPE profile, and optional cash flow analysis."""

    def plot_simulated_price_paths(
        self,
        price_paths: np.ndarray,
        num_paths_to_plot: int = 20,
        tenor: Optional[float] = None,
        payment_frequency: Optional[int] = None,
    ) -> plt.Figure:
        """Plot a sample of simulated future stock price paths."""
        raise NotImplementedError

    def plot_npv_distribution(self, npv_list: List[float]) -> plt.Figure:
        """Plot histogram of desk NPV across all simulations."""
        raise NotImplementedError

    def plot_epe_profile(self, epe_profile: np.ndarray, dates: np.ndarray) -> plt.Figure:
        """Plot Expected Positive Exposure over time."""
        raise NotImplementedError

    def plot_cash_flow_analysis(
        self,
        cash_flows_series: List[pd.DataFrame],
        num_simulations_to_plot: int = 10,
    ) -> plt.Figure:
        """Plot net cash flow over periods for a sample of simulations."""
        raise NotImplementedError
