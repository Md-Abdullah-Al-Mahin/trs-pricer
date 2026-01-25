"""
Hedging Engine Module (Project Extension: Hedging Recommendation Module)
Central orchestrator for hedging recommendations based on desk position and risk exposures.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

from trs_pricer.config import HedgingConfig
from trs_pricer.hedging.instruments import FuturesHedge, InterestRateSwapHedge, OptionsHedge
from trs_pricer.core.valuation import ValuationEngine


class HedgingEngine:
    """
    Analyzes TRS risk exposures and recommends appropriate hedging strategies.
    
    Decision Matrix:
    - Total Return Payer (desk pays asset return): Long Equity Futures
    - Total Return Receiver (desk receives asset return): 
      1. Receive-Floating IRS (hedge floating rate liability)
      2. Long Put Options (protect against depreciation)
    """
    
    def __init__(self, valuation_engine: Optional[ValuationEngine] = None):
        """
        Initialize HedgingEngine.
        
        Args:
            valuation_engine: Optional ValuationEngine instance for exposure calculations
        """
        self._val = valuation_engine or ValuationEngine()
        self._config = HedgingConfig()
    
    def generate_hedging_recommendation(
        self,
        desk_position: str,
        summary_results: Dict[str, Any],
        cash_flows_list: List[pd.DataFrame],
        price_paths: np.ndarray,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate hedging recommendations based on desk position and risk exposures."""
        desk_position = desk_position.lower().strip()
        if desk_position not in ["payer", "receiver"]:
            raise ValueError(f"desk_position must be 'payer' or 'receiver', got '{desk_position}'")

        # Calculate risk exposures
        delta_exposure = self._val.calculate_delta_exposure(cash_flows_list, price_paths, params)
        funding_rate_exposure = self._val.calculate_funding_rate_exposure(cash_flows_list, params)

        # Identify primary risks
        primary_risks = self._identify_primary_risks(
            desk_position, delta_exposure, funding_rate_exposure
        )

        # Generate hedge recommendations based on position
        if desk_position == "payer":
            recommended_strategy = self._recommend_payer_hedge(
                params, price_paths, delta_exposure
            )
        else:  # receiver
            recommended_strategy = self._recommend_receiver_hedge(
                params, price_paths, delta_exposure, funding_rate_exposure, summary_results
            )

        # Calculate combined hedge cost
        combined_hedge_cost = sum(
            hedge.get("estimated_premium", 0.0) or hedge.get("estimated_cost", 0.0)
            for hedge in recommended_strategy
        )

        # Generate net effect description
        net_effect = self._describe_net_effect(
            desk_position, recommended_strategy, combined_hedge_cost
        )

        return {
            "desk_position": desk_position.upper(),
            "primary_risks": primary_risks,
            "delta_exposure": delta_exposure,
            "funding_rate_exposure": funding_rate_exposure,
            "recommended_strategy": recommended_strategy,
            "combined_hedge_cost": combined_hedge_cost,
            "net_effect": net_effect,
        }
    
    def _identify_primary_risks(
        self,
        desk_position: str,
        delta_exposure: float,
        funding_rate_exposure: float,
    ) -> List[str]:
        """Identify primary risks based on desk position and exposures."""
        risks = []

        if desk_position == "payer":
            risks.append("Short Equity (asset appreciation risk)")
        else:  # receiver
            risks.append("Long Equity (asset depreciation risk)")
            if funding_rate_exposure > 0:
                risks.append("Short Floating Rate (rising rate risk)")

        return risks
    
    def _recommend_payer_hedge(
        self,
        params: Dict[str, Any],
        price_paths: np.ndarray,
        delta_exposure: float,
    ) -> List[Dict[str, Any]]:
        """Recommend hedging strategy for Total Return Payer position."""
        ticker = params["ticker"]
        notional = params["notional"]
        current_price = price_paths[0, 0] if price_paths.size > 0 else params.get("initial_price", 1.0)

        # Calculate futures hedge
        futures_hedge = FuturesHedge(
            ticker=ticker,
            notional=notional,
            current_price=current_price,
            contract_size=self._config.DEFAULT_FUTURES_CONTRACT_SIZE,
            target_hedge_ratio=self._config.DEFAULT_TARGET_HEDGE_RATIO,
        )

        return [futures_hedge.to_dict()]
    
    def _recommend_receiver_hedge(
        self,
        params: Dict[str, Any],
        price_paths: np.ndarray,
        delta_exposure: float,
        funding_rate_exposure: float,
        summary_results: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Recommend hedging strategy for Total Return Receiver position."""
        recommendations = []

        # 1. Interest Rate Swap recommendation
        notional = params["notional"]
        tenor = params["tenor"]
        benchmark_rate = params.get("benchmark_rate", 0.05)
        payment_frequency = params.get("payment_frequency", 4)
        fixed_rate = benchmark_rate + self._config.DEFAULT_IRS_FIXED_RATE_BUFFER

        irs_hedge = InterestRateSwapHedge(
            notional=notional,
            tenor=tenor,
            fixed_rate=fixed_rate,
            floating_rate_index="SOFR",
            receive_floating=True,
            payment_frequency=payment_frequency,
        )
        recommendations.append(irs_hedge.to_dict())

        # 2. Put Options recommendation
        ticker = params["ticker"]
        current_price = price_paths[0, 0] if price_paths.size > 0 else params.get("initial_price", 1.0)
        strike_price = self._calculate_protective_put_strike(
            price_paths, current_price, params, summary_results
        )

        put_hedge = OptionsHedge(
            ticker=ticker,
            option_type="PUT",
            strike_price=strike_price,
            current_price=current_price,
            notional=notional,
            contract_size=self._config.DEFAULT_OPTION_CONTRACT_SIZE,
            expiry_years=tenor,
            target_delta=self._config.DEFAULT_TARGET_PUT_DELTA,
        )
        recommendations.append(put_hedge.to_dict())

        return recommendations
    
    def _calculate_protective_put_strike(
        self,
        price_paths: np.ndarray,
        current_price: float,
        params: Dict[str, Any],
        summary_results: Dict[str, Any],
    ) -> float:
        """
        Calculate protective put strike price based on simulation results.

        Uses percentile of final prices or default strike percentage.
        """
        if price_paths.size > 0 and price_paths.shape[1] > 0:
            final_prices = price_paths[:, -1]
            strike = float(np.percentile(final_prices, 10))  # 10th percentile = protect 90% downside
        else:
            strike = current_price * self._config.DEFAULT_PUT_STRIKE_PERCENTAGE  # 90% of spot
        return max(strike, 1e-6)  # Ensure positive
    
    def _describe_net_effect(
        self,
        desk_position: str,
        recommended_strategy: List[Dict[str, Any]],
        combined_hedge_cost: float,
    ) -> str:
        """Generate description of net effect after hedging."""
        if desk_position == "payer":
            return "Offsets short equity exposure via long equity futures."
        # receiver: IRS + puts
        fixed_pct = None
        for h in recommended_strategy:
            if h.get("type") == "IRS" and "fixed_rate" in h:
                fixed_pct = h["fixed_rate"] * 100
                break
        if fixed_pct is not None:
            return f"Converts position to a ~{fixed_pct:.1f}% fixed funding cost with capped downside."
        return "Converts position to a fixed funding cost with capped downside."
