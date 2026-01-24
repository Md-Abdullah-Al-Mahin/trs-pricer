# Financial Calculations Review

**Date:** January 24, 2026  
**Status:** ✅ All calculations verified (with one documentation discrepancy noted)

---

## 1. GBM Simulation (simulation.py)

**Formula:**
```
dt = 1 / payment_frequency
price[t] = price[t-1] * exp((mu - 0.5*vol²)*dt + vol*sqrt(dt)*Z)
mu = benchmark_rate (risk-neutral)
```

**Implementation Check:**
- ✅ `dt = 1.0 / payment_frequency` - Correct
- ✅ `drift_term = (mu - 0.5 * volatility ** 2) * dt` - Correct
- ✅ `diffusion_term = volatility * np.sqrt(dt)` - Correct
- ✅ Risk-neutral drift: `mu = benchmark_rate` - Correct

**Verdict:** ✅ **CORRECT** - Matches standard GBM formula for risk-neutral pricing.

---

## 2. Total Return Leg (cash_flows.py)

**Formula:**
```
Total Return = (period_end - period_start)/period_start * notional 
             + (dividend_yield / payment_frequency) * notional
```

**Implementation Check:**
- ✅ `price_appreciation = (period_end_price - period_start_price) / period_start_price * notional` - Correct
- ✅ `dividend_payment = (dividend_yield / payment_frequency) * notional` - Correct
- ✅ Returns: `price_appreciation + dividend_payment` - Correct

**Verdict:** ✅ **CORRECT** - Matches specification exactly.

---

## 3. Funding Leg (cash_flows.py) ⚠️ **UPDATED**

**Current Implementation (FIXED):**
```python
funding_payment = (effective_funding_rate / payment_frequency) * notional
return funding_payment  # No depreciation offset
```

**Previous Documentation (INCORRECT):**
```
(effective_funding_rate / payment_frequency) * notional 
- max(0, period_start - period_end)/period_start * notional
```

**Analysis:**
- ✅ **Current code is CORRECT** - In standard TRS contracts, the funding leg is a fixed payment regardless of stock movement
- ⚠️ **Documentation needs update** - README.md and FINANCIAL_VERIFICATION.md still reference the old formula with depreciation offset
- The depreciation is already accounted for in the total return leg (which becomes negative when stock depreciates)
- The fix ensures NPVs are positive on average, which is the expected behavior

**Verdict:** ✅ **CODE IS CORRECT** - ⚠️ **Documentation needs updating**

---

## 4. Net Cash Flow (cash_flows.py)

**Formula:**
```
net_cash_flow = funding_flow - total_return_flow
```

**Implementation Check:**
- ✅ `net_flow = funding_flows[i] - total_return_flows[i]` - Correct
- ✅ Sign convention: Positive = desk receives net, Negative = desk pays net - Correct

**Verdict:** ✅ **CORRECT** - Net to desk = funding received - total return paid.

---

## 5. NPV Calculation (valuation.py)

**Formula:**
```
period_rate = benchmark_rate / payment_frequency
discount_factor[t] = (1 + period_rate)^(-t)
NPV = Σ(cash_flow[t] * discount_factor[t])
```

**Implementation Check:**
- ✅ `period_rate = benchmark_rate / payment_frequency` - Correct
- ✅ `periods = np.arange(1, len(cash_flows) + 1)` - Correct (periods start at 1)
- ✅ `discount_factors = (1 + period_rate) ** (-periods)` - Correct
- ✅ Period 1 cash flow discounted by 1 period, Period 2 by 2 periods, etc. - Correct

**Verdict:** ✅ **CORRECT** - Standard discrete compounding discounting.

---

## 6. Marked-to-Market Value (valuation.py)

**Formula:**
```
MTM at period p = PV of future cash flows from period p onward
```

**Implementation Check:**
- ✅ `future_flows = cash_flows_df.iloc[current_period - 1:]` - Correct indexing
  - If current_period=1, gets index 0 (first period) ✓
  - If current_period=2, gets index 1 (second period) ✓
- ✅ Uses `_discount_cash_flows` with `start_period=1` default - Correct
  - Future flows are discounted starting from period 1 (relative to valuation point) ✓

**Example Verification:**
- MTM at START of period 1: future_flows = [CF1, CF2, CF3], discounted by [1, 2, 3] periods ✓
- MTM at START of period 2: future_flows = [CF2, CF3], discounted by [1, 2] periods ✓
- MTM at START of period 3: future_flows = [CF3], discounted by [1] period ✓

**Verdict:** ✅ **CORRECT** - Each cash flow is discounted by the correct number of periods from the valuation point.

---

## 7. EPE Calculation (valuation.py)

**Formula:**
```
EPE[t] = E[max(0, MTM[t])] across all simulation paths
```

**Implementation Check:**
- ✅ Calculates MTM for each path at each period - Correct
- ✅ `np.maximum(0, mtm_matrix)` - Takes max(0, MTM) to get positive exposure only ✓
- ✅ `np.mean(..., axis=0)` - Averages across all paths for each period ✓

**Verdict:** ✅ **CORRECT** - Standard EPE calculation.

---

## 8. Effective Funding Rate (trs_pricer.py)

**Formula:**
```
effective_funding_rate = benchmark_rate + funding_spread
```

**Implementation Check:**
- ✅ `"effective_funding_rate": benchmark_rate + funding_spread` - Correct

**Verdict:** ✅ **CORRECT** - Simple addition.

---

## 9. Cash Flow Timing

**Verification:**
- ✅ Price paths: `(num_simulations, num_periods + 1)` - Includes initial price ✓
- ✅ Period extraction: `start_prices = path[:-1]`, `end_prices = path[1:]` - Correct ✓
- ✅ Period 1 uses prices[0] and prices[1] - Correct ✓
- ✅ Period N uses prices[N-1] and prices[N] - Correct ✓

**Verdict:** ✅ **CORRECT** - Cash flows are calculated for the correct periods.

---

## Summary

### ✅ All Financial Calculations Are Correct

| Component | Status | Notes |
|-----------|--------|-------|
| GBM Simulation | ✅ Correct | Standard risk-neutral GBM |
| Total Return Leg | ✅ Correct | Appreciation + dividends |
| Funding Leg | ✅ Correct | Fixed payment (code fixed, docs need update) |
| Net Cash Flow | ✅ Correct | Funding - Total Return |
| NPV Discounting | ✅ Correct | Discrete compounding |
| MTM Calculation | ✅ Correct | PV of future flows |
| EPE Calculation | ✅ Correct | Average of max(0, MTM) |
| Effective Funding Rate | ✅ Correct | Benchmark + Spread |
| Cash Flow Timing | ✅ Correct | Proper period extraction |

### ⚠️ Documentation Discrepancy

**Issue:** README.md and FINANCIAL_VERIFICATION.md still reference the old funding leg formula with depreciation offset.

**Recommendation:** Update documentation to reflect the corrected implementation:
- Funding leg = `(effective_funding_rate / payment_frequency) * notional` (fixed payment)
- Depreciation is handled in the total return leg, not the funding leg

### ✅ No Financial Logic Errors Found

All calculations are mathematically sound and follow standard TRS pricing conventions.
