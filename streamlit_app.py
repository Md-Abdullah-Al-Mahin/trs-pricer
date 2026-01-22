"""
Streamlit UI for TRS Pricing Simulator
Interactive web interface for running Total Return Swap pricing simulations.
"""

import streamlit as st
import matplotlib.pyplot as plt
from trs_pricer import TRSPricer

# Page configuration
st.set_page_config(
    page_title="TRS Pricing Simulator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">📊 TRS Pricing Simulator</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Total Return Swap Pricing with Monte Carlo Simulation</p>', unsafe_allow_html=True)

# Sidebar for inputs
with st.sidebar:
    st.header("⚙️ Simulation Parameters")
    
    # Required parameters
    st.subheader("Required Parameters")
    ticker = st.text_input(
        "Ticker Symbol",
        value="MSFT",
        help="Stock ticker symbol (e.g., MSFT, AAPL, GOOGL)"
    ).upper().strip()
    
    notional = st.number_input(
        "Notional Amount ($)",
        min_value=100_000,
        max_value=100_000_000,
        value=5_000_000,
        step=100_000,
        help="Principal amount of the swap"
    )
    
    tenor = st.number_input(
        "Tenor (years)",
        min_value=0.25,
        max_value=10.0,
        value=2.0,
        step=0.25,
        help="Swap duration in years"
    )
    
    payment_frequency = st.selectbox(
        "Payment Frequency",
        options=[1, 2, 4, 12, 52],
        index=2,
        format_func=lambda x: {1: "Annual", 2: "Semi-annual", 4: "Quarterly", 12: "Monthly", 52: "Weekly"}[x],
        help="Number of payments per year"
    )
    
    num_simulations = st.number_input(
        "Number of Simulations",
        min_value=100,
        max_value=50000,
        value=5000,
        step=500,
        help="Number of Monte Carlo simulation paths"
    )
    
    # Optional parameters (manual overrides)
    st.subheader("Manual Overrides (Optional)")
    st.caption("Leave empty to auto-fetch from market data")
    
    use_manual = st.checkbox("Use Manual Parameters", value=False)
    
    if use_manual:
        initial_price = st.number_input(
            "Initial Price ($)",
            min_value=0.01,
            value=420.0,
            step=1.0,
            help="Stock price at trade inception"
        )
        
        dividend_yield = st.number_input(
            "Dividend Yield (%)",
            min_value=0.0,
            max_value=20.0,
            value=0.8,
            step=0.1,
            help="Annual dividend yield as percentage"
        ) / 100
        
        volatility = st.number_input(
            "Volatility (%)",
            min_value=0.01,
            max_value=200.0,
            value=25.0,
            step=1.0,
            help="Annual volatility as percentage"
        ) / 100
        
        benchmark_rate = st.number_input(
            "Benchmark Rate (%)",
            min_value=0.0,
            max_value=20.0,
            value=5.0,
            step=0.1,
            help="Annual risk-free rate as percentage"
        ) / 100
        
        funding_spread = st.number_input(
            "Funding Spread (%)",
            min_value=0.0,
            max_value=10.0,
            value=1.5,
            step=0.1,
            help="Funding spread as percentage"
        ) / 100
    else:
        initial_price = None
        dividend_yield = None
        volatility = None
        benchmark_rate = None
        funding_spread = None

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🚀 Run Simulation")
    
    if st.button("▶️ Run Simulation", type="primary", use_container_width=True):
        if not ticker:
            st.error("❌ Please enter a ticker symbol")
        else:
            # Prepare parameters
            params = {
                "ticker": ticker,
                "notional": notional,
                "tenor": tenor,
                "payment_frequency": payment_frequency,
                "num_simulations": int(num_simulations),
            }
            
            # Add manual overrides if provided
            if use_manual:
                if initial_price:
                    params["initial_price"] = initial_price
                if dividend_yield is not None:
                    params["dividend_yield"] = dividend_yield
                if volatility is not None:
                    params["volatility"] = volatility
                if benchmark_rate is not None:
                    params["benchmark_rate"] = benchmark_rate
                if funding_spread is not None:
                    params["funding_spread"] = funding_spread
            
            # Run simulation with progress
            with st.spinner("🔄 Running simulation... This may take a few moments."):
                try:
                    pricer = TRSPricer()
                    summary_results, figures = pricer.run_simulation(params)
                    
                    # Store results in session state
                    st.session_state['summary_results'] = summary_results
                    st.session_state['figures'] = figures
                    st.session_state['params'] = params
                    
                    st.success("✅ Simulation completed successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error running simulation: {str(e)}")
                    st.exception(e)

with col2:
    st.header("ℹ️ Information")
    st.info("""
    **How to use:**
    1. Enter required parameters in the sidebar
    2. Optionally enable manual overrides
    3. Click "Run Simulation"
    4. View results below
    
    **Auto-fetching:**
    - Market data is automatically fetched from yfinance
    - Manual overrides skip auto-fetch for specific parameters
    """)

# Display results if available
if 'summary_results' in st.session_state and 'figures' in st.session_state:
    st.divider()
    st.header("📈 Simulation Results")
    
    summary_results = st.session_state['summary_results']
    figures = st.session_state['figures']
    
    # Summary Report
    st.subheader("📊 Summary Report")
    pricer = TRSPricer()
    report = pricer.generate_summary_report(summary_results)
    st.text(report)
    
    # Key Metrics
    st.subheader("📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Expected NPV",
            f"${summary_results['npv_mean']:,.0f}",
            delta=f"${summary_results['npv_std']:,.0f} std dev"
        )
    
    with col2:
        st.metric(
            "Peak EPE",
            f"${summary_results.get('peak_epe', 0):,.0f}",
            help="Expected Positive Exposure"
        )
    
    with col3:
        st.metric(
            "Volatility",
            f"{summary_results['volatility']*100:.1f}%"
        )
    
    with col4:
        st.metric(
            "Effective Funding Rate",
            f"{summary_results['effective_funding_rate']*100:.2f}%"
        )
    
    # NPV Percentiles
    st.subheader("📊 NPV Distribution Percentiles")
    percentiles = summary_results['npv_percentiles']
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("5th", f"${percentiles['5th']:,.0f}")
    with col2:
        st.metric("25th", f"${percentiles['25th']:,.0f}")
    with col3:
        st.metric("50th (Median)", f"${percentiles['50th']:,.0f}")
    with col4:
        st.metric("75th", f"${percentiles['75th']:,.0f}")
    with col5:
        st.metric("95th", f"${percentiles['95th']:,.0f}")
    
    # Visualizations
    st.subheader("📈 Visualizations")
    
    # Display plots in tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Price Paths", 
        "NPV Distribution", 
        "EPE Profile", 
        "Cash Flow Analysis"
    ])
    
    with tab1:
        st.pyplot(figures[0], use_container_width=True)
        st.caption("Simulated stock price paths over time with mean path overlay")
    
    with tab2:
        st.pyplot(figures[1], use_container_width=True)
        st.caption("Distribution of Net Present Value across all simulations")
    
    with tab3:
        st.pyplot(figures[2], use_container_width=True)
        st.caption("Expected Positive Exposure profile over time")
    
    with tab4:
        st.pyplot(figures[3], use_container_width=True)
        st.caption("Net cash flow analysis across sample simulation paths")
    
    # Download results button
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col2:
        if st.button("🔄 Run New Simulation", use_container_width=True):
            # Clear session state
            if 'summary_results' in st.session_state:
                del st.session_state['summary_results']
            if 'figures' in st.session_state:
                del st.session_state['figures']
            if 'params' in st.session_state:
                del st.session_state['params']
            st.rerun()

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>TRS Pricing Simulator | Built with Streamlit</p>
    </div>
""", unsafe_allow_html=True)
