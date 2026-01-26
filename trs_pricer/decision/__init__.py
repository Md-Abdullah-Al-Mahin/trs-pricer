"""
Decision Dashboard Module
Decision support layer for TRS pricing simulator.
Transforms quantitative simulation outputs into actionable recommendations.
"""

# Decision dashboard components will be imported here as they are implemented
from trs_pricer.decision.decision_engine import TRSDecisionEngine
from trs_pricer.decision.decision_visualizer import TRSDecisionVisualizer
from trs_pricer.decision.decision_report import TRSDecisionReport

__all__ = [
    "TRSDecisionEngine",
    "TRSDecisionVisualizer",
    "TRSDecisionReport",
]
