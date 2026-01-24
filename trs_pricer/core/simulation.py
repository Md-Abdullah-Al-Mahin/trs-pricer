"""
Simulation Module (Class-based)
Handles price path simulation using Geometric Brownian Motion (GBM).
See README Section 2.2.A.
"""

import numpy as np
from typing import Optional


class SimulationEngine:
    """Generates future stock price paths via GBM."""

    @staticmethod
    def calculate_time_step(tenor: float, payment_frequency: int) -> float:
        """Time step per period in years: 1 / payment_frequency."""
        return 1.0 / payment_frequency

    def simulate_price_paths(
        self,
        initial_price: float,
        tenor: float,
        volatility: float,
        payment_frequency: int,
        num_simulations: int,
        benchmark_rate: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> np.ndarray:
        """
        GBM paths: P[t] = P[t-1] * exp((mu - 0.5*vol²)*dt + vol*sqrt(dt)*Z).
        mu = benchmark_rate for risk-neutral valuation; uses 0 if not provided.
        
        Returns:
            np.ndarray of shape (num_simulations, num_periods + 1) where
            num_periods = int(tenor * payment_frequency)
        """
        # Set random seed if provided
        if seed is not None:
            np.random.seed(seed)
        
        # Calculate time step and number of periods
        dt = self.calculate_time_step(tenor, payment_frequency)
        num_periods = int(tenor * payment_frequency)
        
        # Risk-neutral drift (mu = benchmark_rate, default to 0 if not provided)
        mu = benchmark_rate if benchmark_rate is not None else 0.0
        
        # Initialize price paths array: (num_simulations, num_periods + 1)
        # First column is initial_price, remaining columns are simulated prices
        price_paths = np.zeros((num_simulations, num_periods + 1))
        price_paths[:, 0] = initial_price
        
        # Generate random shocks for all paths and periods at once
        # Z ~ N(0, 1) for each path and period
        random_shocks = np.random.standard_normal((num_simulations, num_periods))
        
        # GBM formula: P[t] = P[t-1] * exp((mu - 0.5*vol²)*dt + vol*sqrt(dt)*Z)
        drift_term = (mu - 0.5 * volatility ** 2) * dt
        diffusion_term = volatility * np.sqrt(dt)
        
        # Simulate each period
        for t in range(1, num_periods + 1):
            price_paths[:, t] = price_paths[:, t - 1] * np.exp(
                drift_term + diffusion_term * random_shocks[:, t - 1]
            )
        
        return price_paths
