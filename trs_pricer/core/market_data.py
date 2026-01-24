"""
Market Data Module (Class-based)
Handles fetching of market data from various sources (yfinance)
See README Section 2.1.1 for data sources and fallback logic.
"""
import warnings
from typing import Optional, Dict

import numpy as np
import pandas as pd
import yfinance as yf

from trs_pricer.config import (
    DEFAULT_DIVIDEND_YIELD,
    DEFAULT_FUNDING_SPREAD,
    DEFAULT_LOOKBACK_DAYS,
    DEFAULT_VOLATILITY,
    TRADING_DAYS_PER_YEAR,
)


class MarketDataFetcher:
    """Fetches market data from yfinance (prices, dividends, vol, funding spread). Caches tickers."""

    def __init__(self, enable_cache: bool = True):
        self.enable_cache = enable_cache
        self._ticker_cache: Dict[str, yf.Ticker] = {}
    
    def _get_ticker(self, ticker: str) -> yf.Ticker:
        """Get or create a cached yfinance Ticker."""
        if self.enable_cache and ticker in self._ticker_cache:
            return self._ticker_cache[ticker]
        stock = yf.Ticker(ticker)
        if self.enable_cache:
            self._ticker_cache[ticker] = stock
        return stock

    def _first_float(self, info: dict, keys: tuple, min_val: Optional[float] = None) -> Optional[float]:
        """Return first valid float from info keys; skip if min_val is set and v <= min_val."""
        for key in keys:
            val = info.get(key)
            if val is None:
                continue
            try:
                v = float(val)
                if min_val is not None and v <= min_val:
                    continue
                return v
            except (TypeError, ValueError):
                pass
        return None
    
    def fetch_current_price(self, ticker: str) -> float:
        """Get current stock price via yfinance. Raises ValueError if unavailable."""
        try:
            stock = self._get_ticker(ticker)
            info = stock.info
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            if price is not None:
                return float(price)
            hist = stock.history(period="1d")
            if hist.empty:
                raise ValueError(f"Unable to fetch price for {ticker}")
            return float(hist["Close"].iloc[-1])
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Error fetching current price for {ticker}: {str(e)}")
    
    def fetch_dividend_yield(self, ticker: str) -> float:
        """Get dividend yield from yfinance; TTM fallback if needed. Uses default on error."""
        try:
            stock = self._get_ticker(ticker)
            info = stock.info
            y = self._first_float(info, ("dividendYield", "trailingAnnualDividendYield", "yield"))
            if y is not None and y >= 0:
                return y
            dividends = stock.dividends
            if dividends.empty:
                warnings.warn(f"No dividend data for {ticker}, using default yield")
                return DEFAULT_DIVIDEND_YIELD
            one_year_ago = pd.Timestamp.now() - pd.DateOffset(years=1)
            ttm = dividends[dividends.index >= one_year_ago].sum()
            if ttm == 0:
                return DEFAULT_DIVIDEND_YIELD
            return float(ttm / self.fetch_current_price(ticker))
        except Exception as e:
            warnings.warn(f"Error fetching dividend yield for {ticker}: {str(e)}, using default")
            return DEFAULT_DIVIDEND_YIELD
    
    def _volatility_from_option_chain(self, ticker: str, stock: yf.Ticker) -> Optional[float]:
        """ATM implied vol from nearest expiry option chain, or None."""
        try:
            expiries = getattr(stock, "options", None) or []
            if not expiries:
                return None
            chain = stock.option_chain(expiries[0])
            current = self.fetch_current_price(ticker)
            parts = []
            for df in (chain.calls, chain.puts):
                if df is None or df.empty or "impliedVolatility" not in df.columns:
                    continue
                part = df[["strike", "impliedVolatility"]].copy()
                part["moneyness"] = np.abs(part["strike"] - current)
                parts.append(part)
            if not parts:
                return None
            combined = pd.concat(parts, ignore_index=True).dropna(subset=["impliedVolatility"])
            iv = combined.sort_values("moneyness").head(10)["impliedVolatility"].replace(0, np.nan).dropna()
            return None if iv.empty else float(iv.mean())
        except Exception:
            return None
    
    def fetch_historical_volatility(
        self, ticker: str, lookback_days: int = DEFAULT_LOOKBACK_DAYS
    ) -> float:
        """Vol from info, option-chain ATM IV, or historical returns. Default on error."""
        try:
            stock = self._get_ticker(ticker)
            info = stock.info
            v = self._first_float(info, ("impliedVolatility", "volatility", "52WeekVolatility"), min_val=0)
            if v is not None:
                return v / 100.0 if v > 1 else v
            iv = self._volatility_from_option_chain(ticker, stock)
            if iv is not None and iv > 0:
                return iv
            period_days = int(lookback_days * 1.5)
            hist = stock.history(period=f"{period_days}d")
            if hist.empty or len(hist) < 2:
                warnings.warn(f"Insufficient price data for {ticker}, using default volatility")
                return DEFAULT_VOLATILITY
            closes = hist["Close"]
            log_returns = np.log(closes / closes.shift(1)).dropna().tail(lookback_days)
            if len(log_returns) < 10:
                warnings.warn(f"Insufficient return data for {ticker}, using default volatility")
                return DEFAULT_VOLATILITY
            return float(log_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR))
        except Exception as e:
            warnings.warn(f"Error fetching volatility for {ticker}: {str(e)}, using default")
            return DEFAULT_VOLATILITY
    
    def _calculate_beta_adjustment(self, beta: Optional[float]) -> float:
        """Additive spread adjustment from beta; beta=1 → 0, clamped to [0.3, 3]."""
        if beta is None:
            return 0.0
        c = max(0.3, min(3.0, float(beta)))
        return (c - 1.0) * 0.3

    def _calculate_volatility_adjustment(self, ticker: str) -> float:
        """Additive spread adjustment from vol (vs 20% baseline); clamped to [-0.5, 1.0]."""
        try:
            vol = self.fetch_historical_volatility(ticker, lookback_days=252)
            return max(-0.5, min(1.0, (vol - 0.20) * 1.5))
        except Exception:
            return 0.0

    def _compute_additive_risk_term(self, beta_adj: float, vol_adj: float) -> float:
        """(1 + beta_adj + vol_adj) clamped to [0.5, 2.0]."""
        return max(0.5, min(2.0, 1.0 + beta_adj + vol_adj))

    def _calculate_market_cap_factor(self, market_cap: Optional[float]) -> float:
        """Spread multiplier by size: >200B 0.8, >50B 0.9, >10B 1.0, else 1.2."""
        if market_cap is None:
            return 1.0
        try:
            b = float(market_cap) / 1e9
            for thresh, fac in [(200, 0.8), (50, 0.9), (10, 1.0)]:
                if b > thresh:
                    return fac
            return 1.2
        except (TypeError, ValueError):
            return 1.0

    def _calculate_sector_factor(
        self, sector: Optional[str], industry: Optional[str]
    ) -> float:
        """Spread multiplier by sector: defensive 0.85, commodity 1.15, tech 1.10, else 1.0."""
        s, i = ((sector or "").upper(), (industry or "").upper())
        if any(x in s for x in ("UTILITIES", "CONSUMER STAPLES")):
            return 0.85
        if any(x in s for x in ("ENERGY", "MATERIALS")):
            return 1.15
        if "TECHNOLOGY" in s or "BIOTECH" in i:
            return 1.10
        return 1.0

    def _calculate_leverage_factor(self, debt_to_equity: Optional[float]) -> float:
        """Spread multiplier by D/E: <0.5 → 0.95, <1 → 1.0, <2 → 1.10, else 1.20."""
        if debt_to_equity is None:
            return 1.0
        try:
            d = float(debt_to_equity)
            for thresh, fac in [(0.5, 0.95), (1.0, 1.0), (2.0, 1.10)]:
                if d < thresh:
                    return fac
            return 1.20
        except (TypeError, ValueError):
            return 1.0

    def _apply_spread_bounds(
        self, spread: float, min_spread: float = 0.005, max_spread: float = 0.05
    ) -> float:
        """Clamp spread to [min_spread, max_spread]."""
        return max(min_spread, min(max_spread, spread))
    
    def estimate_funding_spread(self, ticker: str) -> float:
        """Hybrid multi-factor funding spread: base × (1 + beta_adj + vol_adj) × cap × sector × leverage."""
        try:
            stock = self._get_ticker(ticker)
            info = stock.info
            beta_adj = self._calculate_beta_adjustment(info.get("beta"))
            vol_adj = self._calculate_volatility_adjustment(ticker)
            term = self._compute_additive_risk_term(beta_adj, vol_adj)
            spread = (
                DEFAULT_FUNDING_SPREAD
                * term
                * self._calculate_market_cap_factor(info.get("marketCap"))
                * self._calculate_sector_factor(info.get("sector"), info.get("industry"))
                * self._calculate_leverage_factor(info.get("debtToEquity"))
            )
            return float(self._apply_spread_bounds(spread))
        except Exception as e:
            warnings.warn(f"Error estimating spread for {ticker}: {str(e)}, using default")
        return DEFAULT_FUNDING_SPREAD

    def clear_cache(self) -> None:
        """Clear the ticker cache."""
        self._ticker_cache.clear()
