# Financial Calculations Verification

## 1. GBM Simulation (simulation.py)

**Specification:**
```
dt = 1 / payment_frequency
price[t] = price[t-1] * exp((mu - 0.5*vol²)*dt + vol*sqrt(dt)*Z)
mu = benchmark_rate (risk-neutral)
```

**Implementation:**
```python
dt = 1.0 / payment_frequency
drift_term = (mu - 0.5 * volatility ** 2) * dt
diffusion_term = volatility * np.sqrt(dt)
price_paths[:, t] = price_paths[:, t - 1] * np.exp(drift_term + diffusion_term * random_shocks[:, t - 1])
```

✅ **VERIFIED CORRECT** - Matches standard GBM formula exactly.

---

## 2. Total Return Leg (cash_flows.py)

**Specification:**
```
(period_end - period_start)/period_start * notional + (dividend_yield / payment_frequency) * notional
```

**Implementation:**
```python
price_appreciation = (period_end_price - period_start_price) / period_start_price * notional
dividend_payment = (dividend_yield / payment_frequency) * notional
return price_appreciation + dividend_payment
```

✅ **VERIFIED CORRECT** - Matches specification exactly.

---

## 3. Funding Leg (cash_flows.py)

**Specification (UPDATED):**
```
(effective_funding_rate / payment_frequency) * notional
```

**Note:** In standard TRS contracts, the funding leg is a fixed payment regardless of stock movement. Depreciation is already accounted for in the total return leg (which becomes negative when stock depreciates).

**Implementation:**
```python
funding_payment = (effective_funding_rate / payment_frequency) * notional
return funding_payment  # No depreciation offset
```

✅ **VERIFIED CORRECT** - Fixed payment matches standard TRS convention.

---

## 4. Net Cash Flow (cash_flows.py)

**Specification:**
```
net_cash_flow = net_funding_cash_flow - total_return_cash_flow
```

**Implementation:**
```python
net_flows = [funding_flows[i] - total_return_flows[i] for i in range(num_periods)]
```

✅ **VERIFIED CORRECT** - Net to desk = funding received - total return paid.

---

## 5. NPV Calculation (valuation.py)

**Specification:**
Discount each path's net_cash_flow at benchmark_rate per period.

**Implementation:**
```python
period_rate = benchmark_rate / payment_frequency
periods = np.arange(1, len(cash_flows) + 1)
discount_factors = (1 + period_rate) ** (-periods)
NPV = sum(cash_flows * discount_factors)
```

**Verification:**
- Period 1 cash flow (occurs at end of period 1): discounted by 1 period ✓
- Period 2 cash flow (occurs at end of period 2): discounted by 2 periods ✓
- Period rate = annual_rate / payment_frequency ✓

✅ **VERIFIED CORRECT** - Standard discrete compounding discounting.

---

## 6. Marked-to-Market Value (valuation.py)

**Specification:**
MTM at current_period = PV of future net cash flows from that period onward.

**Implementation:**
```python
future_flows = cash_flows_df.iloc[current_period - 1:]["net_cash_flow"].values
period_rate = benchmark_rate / payment_frequency
return self._discount_cash_flows(future_flows, period_rate)  # start_period=1 default
```

**Example Verification:**
- MTM at START of period 1: future_flows = [CF1, CF2, CF3], discounted by [1, 2, 3] periods ✓
- MTM at START of period 2: future_flows = [CF2, CF3], discounted by [1, 2] periods ✓
- MTM at START of period 3: future_flows = [CF3], discounted by [1] period ✓

✅ **VERIFIED CORRECT** - Each cash flow is discounted by the correct number of periods from the valuation point.

---

## 7. EPE Calculation (valuation.py)

**Specification:**
At each future date, average of max(0, MTM) across paths.

**Implementation:**
```python
# Calculate MTM for each path at each period
mtm_matrix = np.array([
    [self.calculate_marked_to_market_value(df, benchmark_rate, payment_frequency, p + 1)
     for p in range(num_periods)]
    for df in cash_flows_list
])

# EPE = average of max(0, MTM) across paths for each period
epe_profile = np.mean(np.maximum(0, mtm_matrix), axis=0)
```

**Verification:**
- For each period p, calculate MTM at start of period p for all paths ✓
- Take max(0, MTM) to get positive exposure only ✓
- Average across all paths ✓

✅ **VERIFIED CORRECT** - Standard EPE calculation.

---

## 8. Effective Funding Rate (trs_pricer.py)

**Specification:**
```
effective_funding_rate = benchmark_rate + funding_spread
```

**Implementation:**
```python
"effective_funding_rate": benchmark_rate + funding_spread
```

✅ **VERIFIED CORRECT** - Simple addition.

---

## Summary

All financial calculations are **CORRECT** and match the specifications:
- ✅ GBM simulation formula
- ✅ Total return leg calculation
- ✅ Funding leg calculation
- ✅ Net cash flow calculation
- ✅ NPV discounting
- ✅ MTM calculation
- ✅ EPE calculation
- ✅ Effective funding rate

No financial logic errors found.
