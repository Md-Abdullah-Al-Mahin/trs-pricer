"""
Decision Report Module
One-page summary report generator for TRS Decision Dashboard.
"""

from typing import Dict
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
from trs_pricer.decision.decision_engine import TRSDecisionEngine


class TRSDecisionReport:
    """
    Report generator for TRS decision dashboard.
    Creates one-page summary reports with trade details, metrics, status, and recommendations.
    """

    @staticmethod
    def _format_status(status: str) -> str:
        """Format status for display."""
        status_map = {
            "green": "✓ APPROVED",
            "yellow": "⚠ REVIEW REQUIRED",
            "red": "✗ NOT APPROVED",
        }
        return status_map.get(status.lower(), status.upper())

    @staticmethod
    def _format_issue(issue: str) -> str:
        """Format issue description for display."""
        issue_map = {
            "npv_too_low": "NPV below acceptable threshold",
            "var_too_high": "VaR exceeds acceptable limit",
            "epe_too_high": "EPE exceeds acceptable limit",
        }
        return issue_map.get(issue, issue.replace("_", " ").title())

    def generate_one_page_report(
        self,
        decision_results: Dict,
        summary_results: Dict,
    ) -> str:
        """
        Generate formatted one-page summary report.
        
        Args:
            decision_results: Dictionary from TRSDecisionEngine.evaluate_trade()
            summary_results: Dictionary from TRSPricer.run_simulation()
        
        Returns:
            Formatted string report with trade details, metrics, status, issues, and adjustments
        """
        lines = []
        
        # Header
        lines.append("=" * 60)
        lines.append("TRS DECISION DASHBOARD - TRADE EVALUATION REPORT")
        lines.append("=" * 60)
        lines.append("")
        
        # Trade Details
        lines.append("TRADE DETAILS")
        lines.append("-" * 60)
        lines.append(f"Reference Asset: {summary_results.get('ticker', 'N/A')}")
        lines.append(f"Notional: ${summary_results.get('notional', 0):,.0f}")
        lines.append(f"Tenor: {summary_results.get('tenor', 0)} years")
        lines.append(f"Payment Frequency: {summary_results.get('payment_frequency', 0)} per year")
        lines.append("")
        
        # Overall Decision
        overall_status = decision_results.get("overall_status", "unknown")
        lines.append("OVERALL DECISION")
        lines.append("-" * 60)
        lines.append(f"Status: {self._format_status(overall_status)}")
        lines.append("")
        
        # Key Metrics
        metrics = decision_results.get("metrics", {})
        statuses = decision_results.get("statuses", {})
        
        lines.append("KEY METRICS (as % of Notional)")
        lines.append("-" * 60)
        
        # NPV
        npv_pct = metrics.get("npv_pct", 0.0)
        npv_status = statuses.get("npv", "unknown")
        npv_green = DECISION_NPV_GREEN_THRESHOLD * 100
        npv_yellow = DECISION_NPV_YELLOW_THRESHOLD * 100
        lines.append(f"NPV / Notional: {npv_pct*100:.2f}%")
        lines.append(f"  Status: {self._format_status(npv_status)}")
        lines.append(f"  Thresholds: Green ≥{npv_green:.2f}% | Yellow ≥{npv_yellow:.2f}%")
        lines.append("")
        
        # VaR - use function-based scaling from decision engine
        var_pct = metrics.get("var_pct", 0.0)
        var_status = statuses.get("var", "unknown")
        volatility = summary_results.get("volatility", DEFAULT_VOLATILITY)
        tenor = summary_results.get("tenor", DEFAULT_TENOR)
        
        var_scale_factor = TRSDecisionEngine.calculate_var_scale_factor(volatility, tenor)
        var_green = DECISION_VAR_GREEN_THRESHOLD * var_scale_factor * 100
        var_yellow = DECISION_VAR_YELLOW_THRESHOLD * var_scale_factor * 100
        lines.append(f"VaR / Notional (95%): {var_pct*100:.2f}%")
        lines.append(f"  Status: {self._format_status(var_status)}")
        lines.append(f"  Thresholds: Green ≤{var_green:.2f}% | Yellow ≤{var_yellow:.2f}%")
        if var_scale_factor != 1.0:
            lines.append(f"  Note: Thresholds adjusted for volatility ({volatility*100:.1f}%) and tenor ({tenor:.2f} years)")
        lines.append("")
        
        # EPE - use function-based scaling from decision engine
        epe_pct = metrics.get("epe_pct", 0.0)
        epe_status = statuses.get("epe", "unknown")
        epe_scale_factor = TRSDecisionEngine.calculate_epe_scale_factor(volatility, tenor)
        epe_green = DECISION_EPE_GREEN_THRESHOLD * epe_scale_factor * 100
        epe_yellow = DECISION_EPE_YELLOW_THRESHOLD * epe_scale_factor * 100
        lines.append(f"Peak EPE / Notional: {epe_pct*100:.2f}%")
        lines.append(f"  Status: {self._format_status(epe_status)}")
        lines.append(f"  Thresholds: Green ≤{epe_green:.2f}% | Yellow ≤{epe_yellow:.2f}%")
        if epe_scale_factor != 1.0:
            lines.append(f"  Note: Thresholds adjusted for volatility ({volatility*100:.1f}%) and tenor ({tenor:.2f} years)")
        lines.append("")
        
        # How thresholds were calculated
        lines.append("THRESHOLD CALCULATION")
        lines.append("-" * 60)
        lines.append("NPV (profitability):")
        lines.append(f"  Base thresholds: Green ≥{DECISION_NPV_GREEN_THRESHOLD*100:.1f}% of notional, Yellow ≥{DECISION_NPV_YELLOW_THRESHOLD*100:.1f}%.")
        lines.append("  No scaling applied; profitability hurdle is fixed.")
        lines.append("")
        lines.append("VaR (tail risk, 5th percentile NPV / notional):")
        lines.append(f"  Base thresholds: Green ≤{DECISION_VAR_GREEN_THRESHOLD*100:.0f}%, Yellow ≤{DECISION_VAR_YELLOW_THRESHOLD*100:.0f}% of notional.")
        lines.append("  Scale factor = (volatility / baseline_vol) × √(tenor / baseline_tenor), clamped [0.5, 4].")
        lines.append(f"  Baselines: σ = {DEFAULT_VOLATILITY*100:.0f}% annualized, T = {DEFAULT_TENOR} year(s).")
        lines.append(f"  For this trade: ({volatility*100:.1f}% / {DEFAULT_VOLATILITY*100:.0f}%) × √({tenor:.2f} / {DEFAULT_TENOR}) = {var_scale_factor:.3f}.")
        lines.append(f"  Scaled thresholds: Green ≤{var_green:.2f}%, Yellow ≤{var_yellow:.2f}%.")
        lines.append("  Rationale: VaR ∝ σ√T under GBM; higher vol or longer tenor allow higher VaR before warning.")
        lines.append("")
        lines.append("EPE (credit risk, peak expected positive exposure / notional):")
        lines.append(f"  Base thresholds: Green ≤{DECISION_EPE_GREEN_THRESHOLD*100:.0f}%, Yellow ≤{DECISION_EPE_YELLOW_THRESHOLD*100:.0f}% of notional.")
        lines.append("  Scale factor = (volatility / baseline_vol) × (tenor / baseline_tenor)^0.7, clamped [0.5, 4].")
        lines.append(f"  For this trade: ({volatility*100:.1f}% / {DEFAULT_VOLATILITY*100:.0f}%) × ({tenor:.2f} / {DEFAULT_TENOR})^0.7 = {epe_scale_factor:.3f}.")
        lines.append(f"  Scaled thresholds: Green ≤{epe_green:.2f}%, Yellow ≤{epe_yellow:.2f}%.")
        lines.append("  Rationale: EPE scales with σ and T^0.7 (path-dependent); thresholds adjusted accordingly.")
        lines.append("")
        
        # Issues
        issues = decision_results.get("issues", [])
        if issues:
            lines.append("ISSUES IDENTIFIED")
            lines.append("-" * 60)
            for issue in issues:
                lines.append(f"  • {self._format_issue(issue)}")
            lines.append("")
        else:
            lines.append("ISSUES IDENTIFIED")
            lines.append("-" * 60)
            lines.append("  None - All metrics within acceptable thresholds")
            lines.append("")
        
        # Adjustments
        adjustments = decision_results.get("adjustments", {})
        if adjustments:
            lines.append("ADJUSTMENT RECOMMENDATIONS")
            lines.append("-" * 60)
            
            # Spread adjustment
            if "spread_adjustment" in adjustments:
                spread_adj = adjustments["spread_adjustment"]
                delta_bps = spread_adj.get("delta_bps", 0.0)
                new_spread = spread_adj.get("new_spread", 0.0)
                current_spread = summary_results.get("funding_spread", 0.0)
                lines.append(f"Spread Adjustment:")
                lines.append(f"  Current Spread: {current_spread*100:.2f}%")
                lines.append(f"  Recommended Increase: {delta_bps:.1f} basis points")
                lines.append(f"  New Spread: {new_spread*100:.2f}%")
                lines.append(f"  Rationale: Increase funding spread to improve NPV profitability")
                lines.append("")
            
            # Notional reduction
            if "notional_reduction" in adjustments:
                notional_adj = adjustments["notional_reduction"]
                reduction_pct = notional_adj.get("reduction_pct", 0.0)
                new_notional = notional_adj.get("new_notional", 0.0)
                current_notional = summary_results.get("notional", 0.0)
                lines.append(f"Notional Reduction:")
                lines.append(f"  Current Notional: ${current_notional:,.0f}")
                lines.append(f"  Recommended Reduction: {reduction_pct:.2f}%")
                lines.append(f"  New Notional: ${new_notional:,.0f}")
                lines.append(f"  Rationale: Reduce notional to lower tail risk (VaR)")
                lines.append("")
            
            # Collateral requirement
            if "collateral_requirement" in adjustments:
                collateral_adj = adjustments["collateral_requirement"]
                collateral_pct = collateral_adj.get("collateral_pct", 0.0)
                collateral_amount = collateral_adj.get("collateral_amount", 0.0)
                lines.append(f"Collateral Requirement:")
                lines.append(f"  Required Collateral: {collateral_pct:.2f}% of notional")
                lines.append(f"  Collateral Amount: ${collateral_amount:,.0f}")
                lines.append(f"  Rationale: Require collateral to mitigate credit exposure (EPE)")
                lines.append("")
        else:
            lines.append("ADJUSTMENT RECOMMENDATIONS")
            lines.append("-" * 60)
            lines.append("  None - Trade meets all thresholds without adjustments")
            lines.append("")
        
        # Rationale
        lines.append("DECISION RATIONALE")
        lines.append("-" * 60)
        
        if overall_status == "green":
            lines.append("All three key metrics (NPV, VaR, EPE) are within acceptable thresholds.")
            lines.append("The trade demonstrates sufficient profitability, acceptable tail risk,")
            lines.append("and manageable credit exposure. No adjustments are required.")
        elif overall_status == "yellow":
            lines.append("One or more metrics are in the warning zone (yellow).")
            lines.append("The trade may be acceptable but requires review and consideration")
            lines.append("of the suggested adjustments to improve risk-adjusted returns.")
        else:  # red
            lines.append("One or more metrics fail acceptable thresholds (red).")
            lines.append("The trade does not meet minimum risk-adjusted profitability criteria.")
            lines.append("Adjustments are strongly recommended before proceeding.")
        
        lines.append("")
        lines.append("=" * 60)
        lines.append("Note: Re-run simulation with adjusted parameters to verify impact of changes.")
        lines.append("=" * 60)
        
        return "\n".join(lines)
