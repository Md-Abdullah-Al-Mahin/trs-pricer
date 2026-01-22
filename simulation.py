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
        """
        if seed is not None:
            np.random.seed(seed)
        dt = self.calculate_time_step(tenor, payment_frequency)
        n_periods = int(tenor * payment_frequency)
        mu = benchmark_rate if benchmark_rate is not None else 0.0
        drift = (mu - 0.5 * volatility ** 2) * dt
        vol_step = volatility * np.sqrt(dt)
        paths = np.empty((num_simulations, n_periods + 1))
        paths[:, 0] = initial_price
        Z = np.random.standard_normal((num_simulations, n_periods))
        for t in range(n_periods):
            paths[:, t + 1] = paths[:, t] * np.exp(drift + vol_step * Z[:, t])
        return paths
