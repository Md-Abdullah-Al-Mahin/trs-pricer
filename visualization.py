"""
Visualization Module (Class-based)
Handles plotting of simulation results, NPV distributions, and EPE profiles.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from typing import List, Optional, Tuple
from datetime import datetime


class TRSVisualizer:
    """Plots simulated price paths, NPV distribution, EPE profile, and optional cash flow analysis."""

    @staticmethod
    def _create_figure() -> Tuple[plt.Figure, plt.Axes]:
        """Helper: create a standard figure with grid."""
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.grid(True, alpha=0.3)
        return fig, ax

    @staticmethod
    def _finalize_plot(ax: plt.Axes, xlabel: str, ylabel: str, title: str, show_legend: bool = True):
        """Helper: set labels, title, legend, and tight layout."""
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        if show_legend:
            ax.legend()
        plt.tight_layout()

    def plot_simulated_price_paths(
        self,
        price_paths: np.ndarray,
        num_paths_to_plot: int = 20,
        tenor: Optional[float] = None,
        payment_frequency: Optional[int] = None,
    ) -> plt.Figure:
        """Plot a sample of simulated future stock price paths."""
        num_simulations, num_points = price_paths.shape
        num_paths_to_plot = min(num_paths_to_plot, num_simulations)
        fig, ax = self._create_figure()
        
        time_points = np.linspace(0, tenor, num_points) if (tenor and payment_frequency) else np.arange(num_points)
        xlabel = "Time (years)" if (tenor and payment_frequency) else "Period"
        
        for i in range(num_paths_to_plot):
            ax.plot(time_points, price_paths[i], alpha=0.6, linewidth=0.8)
        
        mean_path = np.mean(price_paths, axis=0)
        ax.plot(time_points, mean_path, 'k-', linewidth=2, label='Mean Path')
        
        self._finalize_plot(ax, xlabel, "Stock Price ($)", 
                          f"Simulated Price Paths (showing {num_paths_to_plot} of {num_simulations})")
        return fig

    def plot_npv_distribution(self, npv_list: List[float]) -> plt.Figure:
        """Plot histogram of desk NPV across all simulations."""
        fig, ax = self._create_figure()
        npv_array = np.array(npv_list)
        mean_npv, std_npv = np.mean(npv_array), np.std(npv_array)
        
        ax.hist(npv_array, bins=50, edgecolor='black', alpha=0.7)
        ax.axvline(mean_npv, color='red', linestyle='--', linewidth=2, label=f'Mean: ${mean_npv:,.0f}')
        ax.axvline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        
        self._finalize_plot(ax, "NPV ($)", "Frequency", 
                          f"NPV Distribution (n={len(npv_list)}, std=${std_npv:,.0f})")
        return fig

    def plot_epe_profile(self, epe_profile: np.ndarray, dates: np.ndarray) -> plt.Figure:
        """Plot Expected Positive Exposure over time."""
        fig, ax = self._create_figure()
        
        if len(epe_profile) == 0 or len(dates) == 0:
            ax.text(0.5, 0.5, 'No EPE data available', transform=ax.transAxes, ha='center', va='center')
            return fig
        
        is_datetime = isinstance(dates[0], datetime) if len(dates) > 0 else False
        x_data = dates if is_datetime else np.arange(1, len(epe_profile) + 1)
        ax.plot(x_data, epe_profile, 'b-', linewidth=2, marker='o', markersize=4)
        
        if is_datetime:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            xlabel = ""
        else:
            xlabel = "Period"
        
        peak_epe = np.max(epe_profile)
        peak_idx = np.argmax(epe_profile)
        ax.axhline(peak_epe, color='red', linestyle='--', alpha=0.5, label=f'Peak EPE: ${peak_epe:,.0f}')
        if is_datetime:
            ax.axvline(dates[peak_idx], color='red', linestyle='--', alpha=0.5)
        
        self._finalize_plot(ax, xlabel, "Expected Positive Exposure ($)", "EPE Profile Over Time")
        return fig

    def plot_cash_flow_analysis(
        self,
        cash_flows_series: List[pd.DataFrame],
        num_simulations_to_plot: int = 10,
    ) -> plt.Figure:
        """Plot net cash flow over periods for a sample of simulations."""
        if not cash_flows_series:
            fig, ax = self._create_figure()
            ax.text(0.5, 0.5, 'No cash flow data available', transform=ax.transAxes, ha='center', va='center')
            return fig
        
        fig, ax = self._create_figure()
        num_simulations_to_plot = min(num_simulations_to_plot, len(cash_flows_series))
        periods = np.arange(1, len(cash_flows_series[0]) + 1)
        
        for i in range(num_simulations_to_plot):
            ax.plot(periods, cash_flows_series[i]["net_cash_flow"].values, alpha=0.5, linewidth=1)
        
        all_flows = np.array([df["net_cash_flow"].values for df in cash_flows_series])
        mean_flows = np.mean(all_flows, axis=0)
        ax.plot(periods, mean_flows, 'k-', linewidth=2, marker='o', markersize=5, label='Mean')
        ax.axhline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        
        self._finalize_plot(ax, "Period", "Net Cash Flow ($)", 
                          f"Net Cash Flow Analysis (showing {num_simulations_to_plot} of {len(cash_flows_series)} paths)")
        return fig
