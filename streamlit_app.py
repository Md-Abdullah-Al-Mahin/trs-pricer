"""
Streamlit UI for TRS Pricing Simulator
Interactive web interface for running Total Return Swap pricing simulations.
"""

import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from trs_pricer import TRSPricer
from trs_pricer.decision import TRSDecisionEngine, TRSDecisionVisualizer, TRSDecisionReport

st.set_page_config(
    page_title="TRS Pricing Simulator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Simple CSS styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
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
        params.update({
            k: v for k, v in {
                "initial_price": initial_price,
                "dividend_yield": dividend_yield,
                "volatility": volatility,
                "benchmark_rate": benchmark_rate,
                "funding_spread": funding_spread,
            }.items() if v is not None
        })

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

# ----- Decision Dashboard -----
st.header("Decision Dashboard")
st.caption("Trade evaluation based on risk-adjusted profitability criteria")

# Evaluate decision
pricer = TRSPricer()
decision_visualizer = TRSDecisionVisualizer()
decision_report = TRSDecisionReport()

decision_results = pricer.evaluate_decision(summary_results)
overall_status = decision_results.get("overall_status", "unknown")
metrics = decision_results.get("metrics", {})
statuses = decision_results.get("statuses", {})
issues = decision_results.get("issues", [])
adjustments = decision_results.get("adjustments", {})

# Store decision results in session state
st.session_state["decision_results"] = decision_results

# Status display
status_info = decision_visualizer.get_status_info(overall_status)
st.subheader("Trade Decision")
status_col1, status_col2 = st.columns([1, 3])
with status_col1:
    st.markdown(f"**Status:**")
    st.markdown(f"<span style='color: {status_info['color']}; font-size: 18px; font-weight: bold;'>{status_info['label']}</span>", unsafe_allow_html=True)
with status_col2:
    st.markdown(f"**Description:** {status_info['description']}")

st.divider()

# Key Metrics
st.subheader("Key Metrics")
# Pass adjusted thresholds from decision_results if available
thresholds = decision_results.get("thresholds")
metric_info = decision_visualizer.get_metric_info(metrics, statuses, thresholds)
metric_col1, metric_col2, metric_col3 = st.columns(3)

for col, metric in zip([metric_col1, metric_col2, metric_col3], metric_info):
    with col:
        threshold_text = f"Green: ≥{metric['green_threshold']:.2f}%" if metric['direction'] == 'higher' else f"Green: ≤{metric['green_threshold']:.2f}%"
        st.metric(
            label=metric['name'],
            value=f"{metric['value']:.2f}{metric['unit']}",
            delta=threshold_text,
            delta_color="off"
        )
        st.caption(f"Status: <span style='color: {metric['status_color']};'>{metric['status'].upper()}</span>", unsafe_allow_html=True)

st.divider()

# Adjustments panel (only for non-Green decisions)
if overall_status != "green":
    st.subheader("Adjustment Recommendations")
    adjustments_info = decision_visualizer.get_adjustments_info(adjustments, issues, summary_results)
    
    if adjustments_info["issues"]:
        st.warning("Issues identified: " + ", ".join([issue.replace('_', ' ').title() for issue in adjustments_info["issues"]]))
    
    if adjustments_info["adjustments"]:
        for adj in adjustments_info["adjustments"]:
            with st.expander(adj["type"]):
                st.write(f"**Current:** {adj['current']}")
                st.write(f"**Change:** {adj['change']}")
                st.write(f"**New:** {adj['new']}")
    else:
        st.info("No adjustments needed")
    
    st.divider()

# Decision Report
st.subheader("Decision Report")
decision_report_text = decision_report.generate_one_page_report(decision_results, summary_results)

with st.expander("View Full Report", expanded=False):
    st.code(decision_report_text, language=None)

st.download_button(
    label="Download Decision Report",
    data=decision_report_text,
    file_name=f"trs_decision_report_{summary_results.get('ticker', 'UNKNOWN')}.txt",
    mime="text/plain",
)

st.divider()

# ----- Results (Existing Section) -----
st.header("Simulation Results")

# Summary report (readable monospace)
report = pricer.generate_summary_report(summary_results)
st.subheader("Simulation Summary Report")
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

st.divider()
if st.button("Clear results and run again"):
    for k in ["summary_results", "figures", "params", "decision_results"]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()
