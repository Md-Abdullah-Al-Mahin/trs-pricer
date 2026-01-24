"""
Main Entry Point
Example usage and execution of TRS pricing simulator.

By default, running this script launches the Streamlit UI.
Use --cli to run the console simulation instead.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from trs_pricer import TRSPricer
import matplotlib.pyplot as plt


def run_ui():
    """Launch the Streamlit web UI."""
    app_path = Path(__file__).resolve().parent / "streamlit_app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])


def main():
    """
    Main execution function - demonstrates minimal parameter usage with auto-fetched market data.
    """
    # Example 1: Minimal params - dividend_yield, volatility, and funding_spread auto-fetched
    params = {
        'ticker': 'MSFT',
        'notional': 5_000_000,
        'tenor': 2,
        'payment_frequency': 4,
        'num_simulations': 5000,
    }
    
    try:
        # Create TRSPricer instance and run the simulation - market data is fetched automatically
        pricer = TRSPricer()
        summary_results, figs = pricer.run_simulation(params)
        
        # Display summary in console
        report = pricer.generate_summary_report(summary_results)
        print(report)
        
        # Show plots
        for fig in figs:
            plt.show()
    except Exception as e:
        print(f"Error running simulation: {e}")
        raise


def main_manual():
    """
    Example with manual overrides (skip auto-fetch for specific params).
    Useful for testing with fixed parameters or when market data is unavailable.
    """
    params_manual = {
        'ticker': 'MSFT',
        'notional': 5_000_000,
        'initial_price': 420.0,          # Override: use specific price
        'dividend_yield': 0.008,          # Override: use manual yield
        'benchmark_rate': 0.05,           # Override: use manual rate
        'funding_spread': 0.02,           # Override: use manual spread
        'tenor': 2,
        'payment_frequency': 4,
        'volatility': 0.25,               # Override: use manual volatility
        'num_simulations': 5000
    }
    
    try:
        pricer = TRSPricer()
        summary_results, figs = pricer.run_simulation(params_manual)
        report = pricer.generate_summary_report(summary_results)
        print(report)
        
        for fig in figs:
            plt.show()
    except Exception as e:
        print(f"Error running simulation: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TRS Pricing Simulator")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run console simulation instead of launching the Streamlit UI",
    )
    args = parser.parse_args()

    if args.cli:
        main()
    else:
        run_ui()
