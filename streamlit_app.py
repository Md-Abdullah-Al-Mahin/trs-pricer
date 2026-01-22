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

# Enhanced Custom CSS for modern, beautiful styling
st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Main Container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header Styles */
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .sub-header {
        font-size: 1.3rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 3rem;
        font-weight: 400;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    [data-testid="stSidebar"] .css-1d391kg {
        background: transparent;
    }
    
    /* Sidebar Headers */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #1e293b;
        font-weight: 700;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* Primary Button */
    button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #5568d3 0%, #6a3f8f 100%);
    }
    
    /* Secondary Button */
    button[kind="secondary"] {
        background: white;
        color: #667eea;
        border: 2px solid #667eea;
    }
    
    button[kind="secondary"]:hover {
        background: #f8fafc;
        border-color: #5568d3;
        color: #5568d3;
    }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e293b;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    [data-testid="stMetricDelta"] {
        font-weight: 600;
    }
    
    /* Info Boxes */
    .stInfo {
        background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
        border-left: 4px solid #667eea;
        border-radius: 8px;
        padding: 1.5rem;
    }
    
    /* Success Messages */
    .stSuccess {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border-left: 4px solid #10b981;
        border-radius: 8px;
    }
    
    /* Error Messages */
    .stError {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left: 4px solid #ef4444;
        border-radius: 8px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Dividers */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
        margin: 2rem 0;
    }
    
    /* Section Headers */
    h2 {
        color: #1e293b;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
        font-size: 1.75rem;
    }
    
    h3 {
        color: #334155;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        font-size: 1.4rem;
    }
    
    /* Captions */
    .stCaption {
        color: #64748b;
        font-size: 0.85rem;
        font-style: italic;
    }
    
    /* Checkbox */
    .stCheckbox label {
        font-weight: 500;
        color: #334155;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #94a3b8;
        padding: 2rem 1rem;
        font-size: 0.9rem;
        margin-top: 3rem;
    }
    
    /* Card-like containers */
    .metric-container {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .metric-container:hover {
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #667eea;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Header with enhanced styling
st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 class="main-header">📊 TRS Pricing Simulator</h1>
        <p class="sub-header">Total Return Swap Pricing with Monte Carlo Simulation</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar for inputs
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding: 1rem 0 2rem 0;">
            <h1 style="font-size: 1.8rem; font-weight: 800; color: #1e293b; margin-bottom: 0.5rem;">
                ⚙️ Simulation Parameters
            </h1>
            <p style="color: #64748b; font-size: 0.9rem;">Configure your TRS pricing simulation</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Required parameters
    st.markdown("### 📋 Required Parameters")
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
    
    st.divider()
    
    # Optional parameters (manual overrides)
    st.markdown("### 🔧 Manual Overrides (Optional)")
    st.caption("💡 Leave empty to auto-fetch from market data")
    
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
    st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); 
                    padding: 2rem; border-radius: 12px; margin-bottom: 2rem;">
            <h2 style="color: #1e293b; font-weight: 700; margin-bottom: 1rem;">
                🚀 Run Simulation
            </h2>
            <p style="color: #64748b; margin-bottom: 0;">
                Execute Monte Carlo simulation with your configured parameters
            </p>
        </div>
    """, unsafe_allow_html=True)
    
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
    st.markdown("""
        <div style="background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%); 
                    padding: 1.5rem; border-radius: 12px; border-left: 4px solid #667eea;">
            <h3 style="color: #1e293b; font-weight: 700; margin-bottom: 1rem;">
                ℹ️ Quick Guide
            </h3>
        </div>
    """, unsafe_allow_html=True)
    st.info("""
    **📝 How to use:**
    1. Enter required parameters in the sidebar
    2. Optionally enable manual overrides
    3. Click "Run Simulation"
    4. View results below
    
    **🔄 Auto-fetching:**
    - Market data is automatically fetched from yfinance
    - Manual overrides skip auto-fetch for specific parameters
    """)

# Display results if available
if 'summary_results' in st.session_state and 'figures' in st.session_state:
    st.divider()
    
    # Results Header
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="font-size: 2.5rem; font-weight: 800; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        margin-bottom: 0.5rem;">
                📈 Simulation Results
            </h1>
            <p style="color: #64748b; font-size: 1.1rem;">Comprehensive analysis of your TRS pricing simulation</p>
        </div>
    """, unsafe_allow_html=True)
    
    summary_results = st.session_state['summary_results']
    figures = st.session_state['figures']
    
    # Summary Report
    st.markdown("### 📊 Summary Report")
    pricer = TRSPricer()
    report = pricer.generate_summary_report(summary_results)
    st.markdown(f"""
        <div style="background: #f8fafc; padding: 1.5rem; border-radius: 8px; 
                     border-left: 4px solid #667eea; font-family: 'Courier New', monospace;
                     font-size: 0.9rem; line-height: 1.8; color: #334155;">
            <pre style="margin: 0; white-space: pre-wrap;">{report}</pre>
        </div>
    """, unsafe_allow_html=True)
    
    # Key Metrics with enhanced styling
    st.markdown("### 📊 Key Metrics")
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            "Expected NPV",
            f"${summary_results['npv_mean']:,.0f}",
            delta=f"${summary_results['npv_std']:,.0f} std dev"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            "Peak EPE",
            f"${summary_results.get('peak_epe', 0):,.0f}",
            help="Expected Positive Exposure"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            "Volatility",
            f"{summary_results['volatility']*100:.1f}%"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            "Effective Funding Rate",
            f"{summary_results['effective_funding_rate']*100:.2f}%"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # NPV Percentiles
    st.markdown("### 📊 NPV Distribution Percentiles")
    st.markdown("<br>", unsafe_allow_html=True)
    
    percentiles = summary_results['npv_percentiles']
    col1, col2, col3, col4, col5 = st.columns(5)
    
    percentile_labels = {
        '5th': '5th Percentile',
        '25th': '25th Percentile',
        '50th': '50th (Median)',
        '75th': '75th Percentile',
        '95th': '95th Percentile'
    }
    
    for idx, (key, label) in enumerate([('5th', '5th'), ('25th', '25th'), 
                                         ('50th', '50th (Median)'), 
                                         ('75th', '75th'), ('95th', '95th')]):
        with [col1, col2, col3, col4, col5][idx]:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric(label, f"${percentiles[key]:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Visualizations
    st.markdown("### 📈 Visualizations")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Display plots in tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Price Paths", 
        "📊 NPV Distribution", 
        "📉 EPE Profile", 
        "💰 Cash Flow Analysis"
    ])
    
    with tab1:
        st.markdown("""
            <div style="background: white; padding: 1.5rem; border-radius: 8px; 
                         box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1); margin-bottom: 1rem;">
        """, unsafe_allow_html=True)
        st.pyplot(figures[0], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.caption("📊 Simulated stock price paths over time with mean path overlay")
    
    with tab2:
        st.markdown("""
            <div style="background: white; padding: 1.5rem; border-radius: 8px; 
                         box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1); margin-bottom: 1rem;">
        """, unsafe_allow_html=True)
        st.pyplot(figures[1], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.caption("📊 Distribution of Net Present Value across all simulations")
    
    with tab3:
        st.markdown("""
            <div style="background: white; padding: 1.5rem; border-radius: 8px; 
                         box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1); margin-bottom: 1rem;">
        """, unsafe_allow_html=True)
        st.pyplot(figures[2], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.caption("📊 Expected Positive Exposure profile over time")
    
    with tab4:
        st.markdown("""
            <div style="background: white; padding: 1.5rem; border-radius: 8px; 
                         box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1); margin-bottom: 1rem;">
        """, unsafe_allow_html=True)
        st.pyplot(figures[3], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.caption("📊 Net cash flow analysis across sample simulation paths")
    
    # Action buttons
    st.divider()
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🔄 Run New Simulation", use_container_width=True, type="secondary"):
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
    <div class="footer">
        <p style="margin: 0;">
            <strong>TRS Pricing Simulator</strong> | Built with ❤️ using Streamlit
        </p>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem;">
            Total Return Swap Pricing with Monte Carlo Simulation
        </p>
    </div>
""", unsafe_allow_html=True)
