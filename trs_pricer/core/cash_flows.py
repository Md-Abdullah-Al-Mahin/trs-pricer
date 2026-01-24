"""
Cash Flow Module (Class-based)
Handles calculation of periodic cash flows for TRS.
See README Section 2.2.B.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any


class CashFlowEngine:
    """Computes total return leg, funding leg, and net cash flows per path and period."""

    @staticmethod
    def calculate_total_return_leg(
        period_start_price: float,
        period_end_price: float,
        dividend_yield: float,
        notional: float,
        payment_frequency: int,
    ) -> float:
        """
        Total return leg (desk pays client): appreciation + dividends.
        
        Formula: (period_end - period_start)/period_start * notional 
                 + (dividend_yield / payment_frequency) * notional
        
        Returns:
            Cash flow amount (positive = desk pays client)
        """
        # #region agent log
        import json
        with open('/Users/mdabdullahalmahin/Desktop/Projects/trs-pricer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"A","location":"cash_flows.py:32","message":"Total return leg inputs","data":{"period_start_price":period_start_price,"period_end_price":period_end_price,"dividend_yield":dividend_yield,"notional":notional,"payment_frequency":payment_frequency},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        price_appreciation = (period_end_price - period_start_price) / period_start_price * notional
        dividend_payment = (dividend_yield / payment_frequency) * notional
        result = price_appreciation + dividend_payment
        # #region agent log
        with open('/Users/mdabdullahalmahin/Desktop/Projects/trs-pricer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"A","location":"cash_flows.py:36","message":"Total return leg result","data":{"price_appreciation":price_appreciation,"dividend_payment":dividend_payment,"total_return_leg":result},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        return result

    @staticmethod
    def calculate_funding_leg(
        period_start_price: float,
        period_end_price: float,
        effective_funding_rate: float,
        notional: float,
        payment_frequency: int,
    ) -> float:
        """
        Funding leg (client pays desk): funding amount.
        
        Formula: (effective_funding_rate / payment_frequency) * notional
        
        Note: Depreciation is already accounted for in the total return leg.
        The funding leg should be a fixed payment regardless of stock movement.
        
        Returns:
            Funding cash flow (positive = client pays desk)
        """
        # #region agent log
        import json
        with open('/Users/mdabdullahalmahin/Desktop/Projects/trs-pricer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"B","location":"cash_flows.py:53","message":"Funding leg inputs","data":{"period_start_price":period_start_price,"period_end_price":period_end_price,"effective_funding_rate":effective_funding_rate,"notional":notional,"payment_frequency":payment_frequency},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        funding_payment = (effective_funding_rate / payment_frequency) * notional
        # #region agent log
        with open('/Users/mdabdullahalmahin/Desktop/Projects/trs-pricer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"B","location":"cash_flows.py:68","message":"Funding leg result (FIXED)","data":{"funding_payment":funding_payment,"net_funding_leg":funding_payment},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        return funding_payment

    def calculate_cash_flows(
        self, price_paths: np.ndarray, params: Dict[str, Any]
    ) -> List[pd.DataFrame]:
        """
        Calculate cash flows for each simulation path.
        
        Args:
            price_paths: Array of shape (num_simulations, num_periods + 1) from SimulationEngine
            params: Dictionary containing:
                - notional: Principal amount
                - dividend_yield: Annual dividend yield (default: 0.0)
                - effective_funding_rate: Annual funding rate (benchmark + spread)
                - payment_frequency: Payments per year
        
        Returns:
            List of DataFrames (one per simulation), each with columns:
                - period: Period number (1, 2, 3, ...)
                - period_start_price: Stock price at period start
                - period_end_price: Stock price at period end
                - total_return_cash_flow: Desk → Client (appreciation + dividends)
                - net_funding_cash_flow: Client → Desk (funding payment)
                - net_cash_flow: Net to desk (funding - total return)
        """
        # Extract parameters
        notional = params["notional"]
        dividend_yield = params.get("dividend_yield", 0.0)
        effective_funding_rate = params["effective_funding_rate"]
        payment_frequency = params["payment_frequency"]
        
        num_simulations, num_periods = price_paths.shape[0], price_paths.shape[1] - 1
        
        all_cash_flows = []
        for path in price_paths:
            # Extract prices for each period
            start_prices = path[:-1]  # All prices except last
            end_prices = path[1:]     # All prices except first
            
            # Calculate cash flows for each period
            total_return_flows = [
                self.calculate_total_return_leg(
                    start_prices[i], end_prices[i], dividend_yield, notional, payment_frequency
                )
                for i in range(num_periods)
            ]
            
            funding_flows = [
                self.calculate_funding_leg(
                    start_prices[i], end_prices[i], effective_funding_rate, notional, payment_frequency
                )
                for i in range(num_periods)
            ]
            
            # Net cash flow = funding received - total return paid
            net_flows = []
            for i in range(num_periods):
                net_flow = funding_flows[i] - total_return_flows[i]
                # #region agent log
                import json
                with open('/Users/mdabdullahalmahin/Desktop/Projects/trs-pricer/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"post-fix","hypothesisId":"C","location":"cash_flows.py:112","message":"Net cash flow calculation","data":{"period":i+1,"funding_flow":funding_flows[i],"total_return_flow":total_return_flows[i],"net_cash_flow":net_flow},"timestamp":int(__import__('time').time()*1000)})+'\n')
                # #endregion
                net_flows.append(net_flow)
            
            # Create DataFrame for this simulation
            all_cash_flows.append(pd.DataFrame({
                "period": list(range(1, num_periods + 1)),
                "period_start_price": start_prices.tolist(),
                "period_end_price": end_prices.tolist(),
                "total_return_cash_flow": total_return_flows,
                "net_funding_cash_flow": funding_flows,
                "net_cash_flow": net_flows,
            }))
        
        return all_cash_flows
