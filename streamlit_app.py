"""
Streamlit UI for TRS Pricing Simulator
Interactive web interface for running Total Return Swap pricing simulations.
"""

import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from trs_pricer import TRSPricer

st.set_page_config(
    page_title="TRS Pricing Simulator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Minimal CSS: ensure readable text (works with dark theme from config.toml)
st.markdown("""
<style>
    /* Light text on dark background */
    .stMarkdown, .stMarkdown p, label, .stMetric label { color: #eaeaea !important; }
    h1, h2, h3, .stCaption { color: #eaeaea !important; }
    .main .block-container { background-color: #0e1117; }
    [data-testid="stSidebar"] { background-color: #1a1d24; }
</style>
""", unsafe_allow_html=True)

st.title("TRS Pricing Simulator")
st.caption("Total Return Swap pricing with Monte Carlo simulation")

# ----- Sidebar: inputs -----
with st.sidebar:
    st.header("Parameters")

    ticker = st.text_input("Ticker", value="MSFT", help="e.g. MSFT, AAPL").upper().strip()
    notional = st.number_input("Notional ($)", min_value=100_000, max_value=100_000_000, value=5_000_000, step=100_000)
    tenor = st.number_input("Tenor (years)", min_value=0.25, max_value=10.0, value=2.0, step=0.25)
    payment_frequency = st.selectbox(
        "Payment frequency",
        options=[1, 2, 4, 12, 52],
        index=2,
        format_func=lambda x: {1: "Annual", 2: "Semi-annual", 4: "Quarterly", 12: "Monthly", 52: "Weekly"}[x],
    )
    num_simulations = st.number_input("Simulations", min_value=100, max_value=50_000, value=5000, step=500)

    st.divider()
    st.subheader("Manual overrides")
    use_manual = st.checkbox("Use manual parameters", value=False)

    if use_manual:
        initial_price = st.number_input("Initial price ($)", min_value=0.01, value=420.0, step=1.0)
        dividend_yield = st.number_input("Dividend yield (%)", min_value=0.0, max_value=20.0, value=0.8, step=0.1) / 100
        volatility = st.number_input("Volatility (%)", min_value=0.01, max_value=200.0, value=25.0, step=1.0) / 100
        benchmark_rate = st.number_input("Benchmark rate (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.1) / 100
        funding_spread = st.number_input("Funding spread (%)", min_value=0.0, max_value=10.0, value=1.5, step=0.1) / 100
    else:
        initial_price = dividend_yield = volatility = benchmark_rate = funding_spread = None

# ----- Main: run simulation -----
st.header("Run simulation")

if not ticker:
    st.error("Enter a ticker symbol.")
else:
    params = {
        "ticker": ticker,
        "notional": notional,
        "tenor": tenor,
        "payment_frequency": payment_frequency,
        "num_simulations": int(num_simulations),
    }
    if use_manual:
        if initial_price is not None:
            params["initial_price"] = initial_price
        if dividend_yield is not None:
            params["dividend_yield"] = dividend_yield
        if volatility is not None:
            params["volatility"] = volatility
        if benchmark_rate is not None:
            params["benchmark_rate"] = benchmark_rate
        if funding_spread is not None:
            params["funding_spread"] = funding_spread

    if st.button("Run simulation", type="primary"):
        with st.spinner("Running simulation…"):
            try:
                pricer = TRSPricer()
                summary_results, figures = pricer.run_simulation(params)
                st.session_state["summary_results"] = summary_results
                st.session_state["figures"] = figures
                st.session_state["params"] = params
                st.success("Done.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
                st.exception(e)

st.divider()
st.caption("1. Set parameters in sidebar → 2. Click Run simulation → 3. View results below. Leave manual overrides off to auto-fetch market data.")

# ----- Results -----
if "summary_results" not in st.session_state or "figures" not in st.session_state:
    st.stop()

summary_results = st.session_state["summary_results"]
figures = st.session_state["figures"]

st.header("Results")

# Summary report (readable monospace)
pricer = TRSPricer()
report = pricer.generate_summary_report(summary_results)
st.subheader("Summary report")
st.code(report, language=None)

# Key metrics
st.subheader("Key metrics")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Expected NPV", f"${summary_results['npv_mean']:,.0f}", delta=f"± ${summary_results['npv_std']:,.0f} std")
with c2:
    st.metric("Peak EPE", f"${summary_results.get('peak_epe', 0):,.0f}")
with c3:
    st.metric("Volatility", f"{summary_results['volatility']*100:.1f}%")
with c4:
    st.metric("Effective funding", f"{summary_results['effective_funding_rate']*100:.2f}%")

# Total Cash Flows
st.subheader("Total Cash Flows (Undiscounted, Mean Across Simulations)")
cf1, cf2, cf3 = st.columns(3)
total_return_leg = summary_results.get('total_return_leg_total', 0.0)
funding_leg = summary_results.get('funding_leg_total', 0.0)
with cf1:
    st.metric("Total Return Leg", f"${total_return_leg:,.0f}", help="Desk → Client (appreciation + dividends)")
with cf2:
    st.metric("Funding Leg", f"${funding_leg:,.0f}", help="Client → Desk (funding payments)")
with cf3:
    net_undiscounted = funding_leg - total_return_leg
    st.metric("Net Cash Flow", f"${net_undiscounted:,.0f}", help="Undiscounted net to desk")

# NPV percentiles
st.subheader("NPV percentiles")
pct = summary_results["npv_percentiles"]
pc1, pc2, pc3, pc4, pc5 = st.columns(5)
for col, (k, lbl) in zip([pc1, pc2, pc3, pc4, pc5], [("5th", "5th"), ("25th", "25th"), ("50th", "Median"), ("75th", "75th"), ("95th", "95th")]):
    with col:
        st.metric(lbl, f"${pct[k]:,.0f}")

# Plots in tabs
st.subheader("Charts")
tab1, tab2, tab3, tab4 = st.tabs(["Price paths", "NPV distribution", "EPE profile", "Cash flows"])

with tab1:
    st.pyplot(figures[0], use_container_width=True)
with tab2:
    st.pyplot(figures[1], use_container_width=True)
with tab3:
    st.pyplot(figures[2], use_container_width=True)
with tab4:
    st.pyplot(figures[3], use_container_width=True)

# Hedge strategy plot if present
if "hedging_recommendation" in summary_results and len(figures) > 4:
    st.subheader("Hedge strategy")
    st.pyplot(figures[4], use_container_width=True)

st.divider()
if st.button("Clear results and run again"):
    for k in ["summary_results", "figures", "params"]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()
