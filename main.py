"""
Main Entry Point
Example usage and execution of TRS pricing simulator
"""

from trs_pricer import TRSPricer
import matplotlib.pyplot as plt


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
    main()
