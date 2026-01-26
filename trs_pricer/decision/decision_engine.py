"""
Decision Engine Module
Core decision logic for TRS Decision Dashboard.
Evaluates trades based on three key metrics and generates adjustment recommendations.
"""

import math
from typing import Dict, List
from trs_pricer.config import (
    DECISION_NPV_GREEN_THRESHOLD,
    DECISION_NPV_YELLOW_THRESHOLD,
    DECISION_VAR_GREEN_THRESHOLD,
    DECISION_VAR_YELLOW_THRESHOLD,
    DECISION_EPE_GREEN_THRESHOLD,
    DECISION_EPE_YELLOW_THRESHOLD,
    DEFAULT_VOLATILITY,
    DEFAULT_TENOR,
)


class TRSDecisionEngine:
    """
    Decision engine for TRS trade evaluation.
    Transforms quantitative simulation outputs into actionable recommendations.
    """

    @staticmethod
    def calculate_var_scale_factor(
        volatility: float,
        tenor: float,
        baseline_volatility: float = DEFAULT_VOLATILITY,
        baseline_tenor: float = DEFAULT_TENOR,
        min_scale: float = 0.5,
        max_scale: float = 4.0,
    ) -> float:
        """
        Calculate VaR threshold scale factor based on volatility and tenor.
        
        VaR scales with volatility and the square root of tenor (from GBM theory).
        For a risk-neutral GBM: VaR ∝ σ * √T * |Z_α|
        where σ is volatility, T is tenor, and Z_α is the percentile (e.g., -1.645 for 5th percentile).
        
        Args:
            volatility: Current stock volatility (annualized)
            tenor: Trade tenor in years
            baseline_volatility: Baseline volatility for normalization (default 25%)
            baseline_tenor: Baseline tenor for normalization (default 1 year)
            min_scale: Minimum scale factor (default 0.5x)
            max_scale: Maximum scale factor (default 4.0x)
        
        Returns:
            Scale factor to multiply base VaR threshold
        """
        # VaR scales with volatility and sqrt(tenor)
        vol_ratio = volatility / baseline_volatility if baseline_volatility > 0 else 1.0
        tenor_ratio = math.sqrt(tenor / baseline_tenor) if baseline_tenor > 0 else 1.0
        
        scale_factor = vol_ratio * tenor_ratio
        return max(min_scale, min(max_scale, scale_factor))

    @staticmethod
    def calculate_epe_scale_factor(
        volatility: float,
        tenor: float,
        baseline_volatility: float = DEFAULT_VOLATILITY,
        baseline_tenor: float = DEFAULT_TENOR,
        min_scale: float = 0.5,
        max_scale: float = 4.0,
    ) -> float:
        """
        Calculate EPE threshold scale factor based on volatility and tenor.
        
        EPE (Expected Positive Exposure) also scales with volatility and tenor,
        though the relationship is more complex due to path dependency.
        We use a similar but slightly adjusted formula: EPE ∝ σ * T^α
        where α is between 0.5 and 1.0 (we use 0.7 as a practical middle ground).
        
        Args:
            volatility: Current stock volatility (annualized)
            tenor: Trade tenor in years
            baseline_volatility: Baseline volatility for normalization (default 25%)
            baseline_tenor: Baseline tenor for normalization (default 1 year)
            min_scale: Minimum scale factor (default 0.5x)
            max_scale: Maximum scale factor (default 4.0x)
        
        Returns:
            Scale factor to multiply base EPE threshold
        """
        # EPE scales with volatility and tenor^0.7 (between sqrt and linear)
        vol_ratio = volatility / baseline_volatility if baseline_volatility > 0 else 1.0
        tenor_ratio = (tenor / baseline_tenor) ** 0.7 if baseline_tenor > 0 else 1.0
        
        scale_factor = vol_ratio * tenor_ratio
        return max(min_scale, min(max_scale, scale_factor))

    def extract_key_metrics(self, summary_results: Dict) -> Dict[str, float]:
        """
        Extract three key percentages from simulation results.
        
        Args:
            summary_results: Dictionary from TRSPricer.run_simulation()
        
        Returns:
            Dictionary with:
                - npv_pct: NPV/notional (profitability)
                - var_pct: 95% VaR/notional (tail risk, using 5th percentile)
                - epe_pct: Peak EPE/notional (credit risk)
        """
        notional = summary_results.get("notional", 1.0)
        
        # NPV percentage: mean NPV divided by notional
        npv_mean = summary_results.get("npv_mean", 0.0)
        npv_pct = npv_mean / notional if notional > 0 else 0.0
        
        # VaR percentage: absolute value of 5th percentile (negative tail) divided by notional
        npv_percentiles = summary_results.get("npv_percentiles", {})
        var_5th = npv_percentiles.get("5th", 0.0)
        var_pct = abs(var_5th) / notional if notional > 0 else 0.0
        
        # EPE percentage: peak EPE divided by notional
        peak_epe = summary_results.get("peak_epe", 0.0)
        epe_pct = peak_epe / notional if notional > 0 else 0.0
        
        return {
            "npv_pct": npv_pct,
            "var_pct": var_pct,
            "epe_pct": epe_pct,
        }

    def evaluate_metric(
        self,
        value: float,
        threshold_green: float,
        threshold_yellow: float,
    ) -> str:
        """
        Evaluate a metric against thresholds and return traffic light status.
        
        For NPV: higher is better (green if >= green_threshold)
        For VaR and EPE: lower is better (green if <= green_threshold)
        
        Args:
            value: Metric value to evaluate
            threshold_green: Green threshold (upper bound for NPV, lower bound for VaR/EPE)
            threshold_yellow: Yellow threshold (lower bound for NPV, upper bound for VaR/EPE)
        
        Returns:
            "green", "yellow", or "red"
        """
        # For NPV: green if value >= green_threshold, yellow if >= yellow_threshold, else red
        # For VaR/EPE: green if value <= green_threshold, yellow if <= yellow_threshold, else red
        # We determine which direction by checking if green_threshold > yellow_threshold
        # (NPV: green > yellow, VaR/EPE: green < yellow)
        
        if threshold_green > threshold_yellow:
            # NPV case: higher is better
            if value >= threshold_green:
                return "green"
            elif value >= threshold_yellow:
                return "yellow"
            else:
                return "red"
        else:
            # VaR/EPE case: lower is better
            if value <= threshold_green:
                return "green"
            elif value <= threshold_yellow:
                return "yellow"
            else:
                return "red"

    def calculate_adjustments(
        self,
        summary_results: Dict,
        issues: List[str],
    ) -> Dict[str, Dict[str, float]]:
        """
        Generate adjustment suggestions based on identified issues.
        
        Args:
            summary_results: Dictionary from TRSPricer.run_simulation()
            issues: List of issue descriptions (e.g., ["npv_too_low", "var_too_high"])
        
        Returns:
            Dictionary with adjustment suggestions:
                - spread_adjustment: {"delta_bps": float, "new_spread": float}
                - notional_reduction: {"reduction_pct": float, "new_notional": float}
                - collateral_requirement: {"collateral_pct": float, "collateral_amount": float}
        """
        notional = summary_results.get("notional", 1.0)
        tenor = summary_results.get("tenor", DEFAULT_TENOR)
        funding_spread = summary_results.get("funding_spread", 0.0)
        npv_mean = summary_results.get("npv_mean", 0.0)
        
        # Calculate volatility and tenor-adjusted thresholds (same logic as evaluate_trade)
        volatility = summary_results.get("volatility", DEFAULT_VOLATILITY)
        
        var_scale_factor = self.calculate_var_scale_factor(volatility, tenor)
        epe_scale_factor = self.calculate_epe_scale_factor(volatility, tenor)
        
        var_green_threshold = DECISION_VAR_GREEN_THRESHOLD * var_scale_factor
        epe_green_threshold = DECISION_EPE_GREEN_THRESHOLD * epe_scale_factor
        
        # Extract key metrics
        metrics = self.extract_key_metrics(summary_results)
        npv_pct = metrics["npv_pct"]
        var_pct = metrics["var_pct"]
        epe_pct = metrics["epe_pct"]
        
        adjustments = {}
        
        # Spread adjustment: increase spread to improve NPV
        if "npv_too_low" in issues:
            target_npv_pct = DECISION_NPV_GREEN_THRESHOLD
            target_npv = target_npv_pct * notional
            current_npv = npv_mean
            
            # Formula: delta_spread_bps = (target_npv - current_npv) / (notional * tenor) * 10000
            # This scales inversely with tenor (longer terms require smaller basis point changes)
            if notional > 0 and tenor > 0:
                delta_npv = target_npv - current_npv
                delta_spread_bps = (delta_npv / (notional * tenor)) * 10000
                new_spread = funding_spread + (delta_spread_bps / 10000)
                
                adjustments["spread_adjustment"] = {
                    "delta_bps": delta_spread_bps,
                    "new_spread": max(0.0, new_spread),  # Ensure non-negative
                }
        
        # Notional reduction: reduce notional to lower VaR
        if "var_too_high" in issues:
            target_var_pct = var_green_threshold  # Use volatility-adjusted threshold
            current_var = var_pct * notional
            
            # Formula: reduction_pct = (current_var - target_var) / current_var * 100
            # Maintains proportional risk relationships
            if current_var > 0:
                target_var = target_var_pct * notional
                reduction_pct = ((current_var - target_var) / current_var) * 100
                new_notional = notional * (1 - reduction_pct / 100)
                
                adjustments["notional_reduction"] = {
                    "reduction_pct": max(0.0, min(100.0, reduction_pct)),  # Clamp 0-100%
                    "new_notional": max(0.0, new_notional),
                }
        
        # Collateral requirement: require collateral to mitigate EPE
        if "epe_too_high" in issues:
            target_epe_pct = epe_green_threshold  # Use volatility-adjusted threshold
            current_epe = epe_pct * notional
            
            # Formula: collateral_pct = (current_epe - target_epe) / notional * 100
            # Assumes partial risk mitigation
            if notional > 0:
                target_epe = target_epe_pct * notional
                collateral_pct = ((current_epe - target_epe) / notional) * 100
                collateral_amount = notional * (collateral_pct / 100)
                
                adjustments["collateral_requirement"] = {
                    "collateral_pct": max(0.0, collateral_pct),
                    "collateral_amount": max(0.0, collateral_amount),
                }
        
        return adjustments

    def evaluate_trade(self, summary_results: Dict) -> Dict:
        """
        Main entry point: evaluate a trade and generate decision recommendations.
        
        Args:
            summary_results: Dictionary from TRSPricer.run_simulation()
        
        Returns:
            Dictionary with:
                - overall_status: "green", "yellow", or "red"
                - metrics: extracted key metrics (npv_pct, var_pct, epe_pct)
                - statuses: individual metric statuses
                - issues: list of identified issues (if any)
                - adjustments: adjustment suggestions (if any)
        """
        # Step 1: Extract key metrics
        metrics = self.extract_key_metrics(summary_results)
        
        # Step 2: Calculate volatility and tenor-adjusted thresholds for VaR and EPE
        # Higher volatility and longer tenor naturally lead to higher VaR and EPE,
        # so thresholds should scale accordingly to remain fair
        volatility = summary_results.get("volatility", DEFAULT_VOLATILITY)
        tenor = summary_results.get("tenor", DEFAULT_TENOR)
        
        # Use function-based scaling that accounts for both volatility and tenor
        var_scale_factor = self.calculate_var_scale_factor(volatility, tenor)
        epe_scale_factor = self.calculate_epe_scale_factor(volatility, tenor)
        
        # Scale VaR and EPE thresholds by their respective scale factors
        var_green_threshold = DECISION_VAR_GREEN_THRESHOLD * var_scale_factor
        var_yellow_threshold = DECISION_VAR_YELLOW_THRESHOLD * var_scale_factor
        epe_green_threshold = DECISION_EPE_GREEN_THRESHOLD * epe_scale_factor
        epe_yellow_threshold = DECISION_EPE_YELLOW_THRESHOLD * epe_scale_factor
        
        # Step 3: Evaluate each metric
        npv_status = self.evaluate_metric(
            metrics["npv_pct"],
            DECISION_NPV_GREEN_THRESHOLD,
            DECISION_NPV_YELLOW_THRESHOLD,
        )
        
        var_status = self.evaluate_metric(
            metrics["var_pct"],
            var_green_threshold,
            var_yellow_threshold,
        )
        
        epe_status = self.evaluate_metric(
            metrics["epe_pct"],
            epe_green_threshold,
            epe_yellow_threshold,
        )
        
        statuses = {
            "npv": npv_status,
            "var": var_status,
            "epe": epe_status,
        }
        
        # Step 3: Determine overall status (worst case)
        status_priority = {"red": 3, "yellow": 2, "green": 1}
        overall_status = max(
            [npv_status, var_status, epe_status],
            key=lambda s: status_priority[s]
        )
        
        # Step 4: Identify issues
        issues = []
        if npv_status != "green":
            issues.append("npv_too_low")
        if var_status != "green":
            issues.append("var_too_high")
        if epe_status != "green":
            issues.append("epe_too_high")
        
        # Step 5: Calculate adjustments if needed
        adjustments = {}
        if issues:
            adjustments = self.calculate_adjustments(summary_results, issues)
        
        return {
            "overall_status": overall_status,
            "metrics": metrics,
            "statuses": statuses,
            "issues": issues,
            "adjustments": adjustments,
            # Store adjusted thresholds for UI display
            "thresholds": {
                "npv": {
                    "green": DECISION_NPV_GREEN_THRESHOLD,
                    "yellow": DECISION_NPV_YELLOW_THRESHOLD,
                },
                "var": {
                    "green": var_green_threshold,
                    "yellow": var_yellow_threshold,
                },
                "epe": {
                    "green": epe_green_threshold,
                    "yellow": epe_yellow_threshold,
                },
            },
            "volatility_info": {
                "volatility": volatility,
                "tenor": tenor,
                "baseline_volatility": DEFAULT_VOLATILITY,
                "baseline_tenor": DEFAULT_TENOR,
                "var_scale_factor": var_scale_factor,
                "epe_scale_factor": epe_scale_factor,
            },
        }
