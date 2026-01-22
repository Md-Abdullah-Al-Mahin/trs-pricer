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
        fig, ax = plt.subplots(figsize=(10, 5))
        n_sims, n_cols = price_paths.shape
        n_plot = min(num_paths_to_plot, n_sims)
        x = np.arange(n_cols)
        if tenor is not None and payment_frequency is not None:
            x = x / payment_frequency
        for i in range(n_plot):
            ax.plot(x, price_paths[i], alpha=0.6, linewidth=0.8)
        ax.set_xlabel("Time (years)" if (tenor is not None and payment_frequency is not None) else "Period")
        ax.set_ylabel("Stock price")
        ax.set_title("Simulated price paths")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return fig

    def plot_npv_distribution(self, npv_list: List[float]) -> plt.Figure:
        """Plot histogram of desk NPV across all simulations."""
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(npv_list, bins=50, edgecolor="black", alpha=0.7)
        ax.axvline(np.mean(npv_list), color="red", linestyle="--", label=f"Mean: ${np.mean(npv_list):,.0f}")
        ax.set_xlabel("Desk NPV ($)")
        ax.set_ylabel("Count")
        ax.set_title("NPV distribution")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return fig

    def plot_epe_profile(self, epe_profile: np.ndarray, dates: np.ndarray) -> plt.Figure:
        """Plot Expected Positive Exposure over time."""
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(dates, epe_profile, "b-", linewidth=2)
        ax.fill_between(dates, 0, epe_profile, alpha=0.3)
        ax.set_xlabel("Time (years)")
        ax.set_ylabel("EPE ($)")
        ax.set_title("Expected Positive Exposure")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return fig

    def plot_cash_flow_analysis(
        self,
        cash_flows_series: List[pd.DataFrame],
        num_simulations_to_plot: int = 10,
    ) -> plt.Figure:
        """Plot net cash flow over periods for a sample of simulations."""
        fig, ax = plt.subplots(figsize=(10, 5))
        n_plot = min(num_simulations_to_plot, len(cash_flows_series))
        for i in range(n_plot):
            df = cash_flows_series[i]
            ax.plot(df["net_cash_flow"].values, alpha=0.5, linewidth=1)
        ax.axhline(0, color="black", linestyle="-", linewidth=0.5)
        ax.set_xlabel("Period")
        ax.set_ylabel("Net cash flow ($)")
        ax.set_title("Net cash flow by period (sample paths)")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return fig
