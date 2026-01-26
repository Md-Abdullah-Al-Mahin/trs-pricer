"""
Decision Visualizer Module
Simple visualization components for TRS Decision Dashboard.
"""

from typing import Dict, List, Optional


class TRSDecisionVisualizer:
    """
    Simple visualizer for TRS decision dashboard.
    Provides data formatting for Streamlit native components.
    """

    @staticmethod
    def _get_status_color(status: str) -> str:
        """Get color for status."""
        color_map = {
            "green": "#10b981",
            "yellow": "#f59e0b",
            "red": "#ef4444",
        }
        return color_map.get(status.lower(), "#6b7280")
    
    @staticmethod
    def _get_status_label(status: str) -> str:
        """Get label for status."""
        label_map = {
            "green": "APPROVED",
            "yellow": "REVIEW REQUIRED",
            "red": "NOT APPROVED",
        }
        return label_map.get(status.lower(), "UNKNOWN")
    
    @staticmethod
    def _get_status_description(status: str) -> str:
        """Get description for status."""
        desc_map = {
            "green": "Trade meets all risk-adjusted profitability criteria",
            "yellow": "Trade requires review - some metrics in warning zone",
            "red": "Trade does not meet minimum risk-adjusted criteria",
        }
        return desc_map.get(status.lower(), "")

    def get_status_info(self, overall_status: str) -> Dict:
        """
        Get status information for display.
        
        Args:
            overall_status: "green", "yellow", or "red"
        
        Returns:
            Dictionary with status information
        """
        return {
            "status": overall_status,
            "label": self._get_status_label(overall_status),
            "description": self._get_status_description(overall_status),
            "color": self._get_status_color(overall_status),
        }

    def get_metric_info(
        self,
        metrics: Dict[str, float],
        statuses: Dict[str, str],
        thresholds: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Get metric information for display.
        
        Args:
            metrics: Dictionary with npv_pct, var_pct, epe_pct
            statuses: Dictionary with npv, var, epe statuses
            thresholds: Optional dictionary with adjusted thresholds from decision_results
        
        Returns:
            List of dictionaries with metric information
        """
        from trs_pricer.config import (
            DECISION_NPV_GREEN_THRESHOLD,
            DECISION_NPV_YELLOW_THRESHOLD,
            DECISION_VAR_GREEN_THRESHOLD,
            DECISION_VAR_YELLOW_THRESHOLD,
            DECISION_EPE_GREEN_THRESHOLD,
            DECISION_EPE_YELLOW_THRESHOLD,
        )
        
        # Use adjusted thresholds if provided, otherwise fall back to base thresholds
        if thresholds:
            npv_green = thresholds.get("npv", {}).get("green", DECISION_NPV_GREEN_THRESHOLD)
            npv_yellow = thresholds.get("npv", {}).get("yellow", DECISION_NPV_YELLOW_THRESHOLD)
            var_green = thresholds.get("var", {}).get("green", DECISION_VAR_GREEN_THRESHOLD)
            var_yellow = thresholds.get("var", {}).get("yellow", DECISION_VAR_YELLOW_THRESHOLD)
            epe_green = thresholds.get("epe", {}).get("green", DECISION_EPE_GREEN_THRESHOLD)
            epe_yellow = thresholds.get("epe", {}).get("yellow", DECISION_EPE_YELLOW_THRESHOLD)
        else:
            npv_green = DECISION_NPV_GREEN_THRESHOLD
            npv_yellow = DECISION_NPV_YELLOW_THRESHOLD
            var_green = DECISION_VAR_GREEN_THRESHOLD
            var_yellow = DECISION_VAR_YELLOW_THRESHOLD
            epe_green = DECISION_EPE_GREEN_THRESHOLD
            epe_yellow = DECISION_EPE_YELLOW_THRESHOLD
        
        metric_configs = [
            {
                "key": "npv",
                "name": "NPV / Notional",
                "value": metrics.get("npv_pct", 0.0),
                "status": statuses.get("npv", "green"),
                "green_threshold": npv_green,
                "yellow_threshold": npv_yellow,
                "unit": "%",
                "direction": "higher",
            },
            {
                "key": "var",
                "name": "VaR / Notional",
                "value": metrics.get("var_pct", 0.0),
                "status": statuses.get("var", "green"),
                "green_threshold": var_green,
                "yellow_threshold": var_yellow,
                "unit": "%",
                "direction": "lower",
            },
            {
                "key": "epe",
                "name": "EPE / Notional",
                "value": metrics.get("epe_pct", 0.0),
                "status": statuses.get("epe", "green"),
                "green_threshold": epe_green,
                "yellow_threshold": epe_yellow,
                "unit": "%",
                "direction": "lower",
            },
        ]
        
        result = []
        for config in metric_configs:
            result.append({
                "name": config["name"],
                "value": config["value"] * 100,
                "unit": config["unit"],
                "status": config["status"],
                "status_color": self._get_status_color(config["status"]),
                "green_threshold": config["green_threshold"] * 100,
                "yellow_threshold": config["yellow_threshold"] * 100,
                "direction": config["direction"],
            })
        
        return result

    def get_adjustments_info(
        self,
        adjustments: Dict[str, Dict[str, float]],
        issues: List[str],
        summary_results: Optional[Dict] = None,
    ) -> Dict:
        """
        Get adjustments information for display.
        
        Args:
            adjustments: Dictionary with adjustment suggestions
            issues: List of issue descriptions
            summary_results: Optional summary results for context
        
        Returns:
            Dictionary with adjustments information
        """
        adjustment_list = []
        
        if "spread_adjustment" in adjustments:
            spread_adj = adjustments["spread_adjustment"]
            current_spread = summary_results.get("funding_spread", 0.0) if summary_results else 0.0
            adjustment_list.append({
                "type": "Spread Adjustment",
                "current": f"{current_spread*100:.2f}%",
                "change": f"+{spread_adj.get('delta_bps', 0.0):.1f} bps",
                "new": f"{spread_adj.get('new_spread', 0.0)*100:.2f}%",
            })
        
        if "notional_reduction" in adjustments:
            notional_adj = adjustments["notional_reduction"]
            current_notional = summary_results.get("notional", 0.0) if summary_results else 0.0
            adjustment_list.append({
                "type": "Notional Reduction",
                "current": f"${current_notional:,.0f}",
                "change": f"-{notional_adj.get('reduction_pct', 0.0):.2f}%",
                "new": f"${notional_adj.get('new_notional', 0.0):,.0f}",
            })
        
        if "collateral_requirement" in adjustments:
            collateral_adj = adjustments["collateral_requirement"]
            adjustment_list.append({
                "type": "Collateral Requirement",
                "current": "N/A",
                "change": f"{collateral_adj.get('collateral_pct', 0.0):.2f}% of notional",
                "new": f"${collateral_adj.get('collateral_amount', 0.0):,.0f}",
            })
        
        return {
            "issues": issues,
            "adjustments": adjustment_list,
        }
