import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from order_flow_engine import CommodityOrderFlowEngine

st.set_page_config(
    page_title="AI Trading Arena - Master Analytical Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PROFESSIONAL INSTITUTIONAL STYLING ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    div.stMetric {
        background-color: #161B22;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #30363D;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Institutional Order Flow & Analytics Terminal")

# --- SIDEBAR: ASSET & RISK MONITORING ---
st.sidebar.header("🕹️ Analytical Controls")
selected_symbol = st.sidebar.selectbox("Active Commodity Feed", ["MGC (Micro Gold)", "MCL (Micro Crude)", "SIL (Micro Silver)"])
max_daily_loss = st.sidebar.number_input("Lucid Max Daily Loss Limit ($)", value=1000, step=100)
refresh_interval = st.sidebar.slider("Data Refresh Interval (s)", 1, 10, 3)

# --- NAVIGATION TABS ---
tab_dashboard, tab_heatmap, tab_war_room, tab_risk = st.tabs([
    "📊 Core Microstructure", 
    "🔥 Order Book Heatmap", 
    "🤖 Agent Diagnostic Logs", 
    "🛡️ Prop Drawdown Monitor"
])

# =========================================================
# TAB 1: CORE MICROSTRUCTURE DASHBOARD
# =========================================================
with tab_dashboard:
    # --- TOP METRICS ROW ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Current Delta", value="+240 Contracts", delta="12% vs 5m Avg")
    col2.metric(label="Dominant Wall", value="$2,652.50", delta="180 Bids (Strong)")
    col3.metric(label="POC Price", value="$2,650.10")
    col4.metric(label="Prop Loss Cushion", value="$820.00 / $1,000", delta="-18%")

    st.markdown("---")

    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.subheader(f"📈 Price Chart with Institutional Walls & POC ({selected_symbol})")
        
        fig_price = go.Figure()
        time_series = pd.date_range(end=pd.Timestamp.now(), periods=30, freq='min')
        sim_prices = np.sin(np.linspace(0, 10, 30)) * 2 + 2650.0

        fig_price.add_trace(go.Scatter(x=time_series, y=sim_prices, mode='lines+markers', name='Price', line=dict(color='#00E676')))
        fig_price.add_hline(y=2650.10, line_dash="dash", line_color="gold", annotation_text="POC: $2,650.10")
        fig_price.add_hline(y=2646.00, line_color="#00E676", line_width=3, annotation_text="BUY WALL: $2,646.00")
        fig_price.add_hline(y=2653.50, line_color="#FF5252", line_width=3, annotation_text="SELL WALL: $2,653.50")

        fig_price.update_layout(template="plotly_dark", height=450, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_price, use_container_width=True)

    with right_col:
        st.subheader("📊 Level 2 Liquidity Depth")
        
        prices_depth = np.linspace(2645, 2655, 15)
        bid_volumes = np.random.randint(10, 120, size=15)
        ask_volumes = np.random.randint(10, 120, size=15)
        bid_volumes[3] = 310  
        ask_volumes[12] = 250 

        fig_depth = go.Figure()
        fig_depth.add_trace(go.Bar(y=prices_depth, x=-bid_volumes, orientation='h', name='Bids', marker_color='#00E676'))
        fig_depth.add_trace(go.Bar(y=prices_depth, x=ask_volumes, orientation='h', name='Asks', marker_color='#FF5252'))

        fig_depth.update_layout(
            barmode='overlay',
            xaxis_title="Volume (Bids ← | → Asks)",
            yaxis_title="Price ($)",
            height=450,
            template="plotly_dark",
            margin=dict(l=10, r=10, t=30, b=10)
        )
        st.plotly_chart(fig_depth, use_container_width=True)

# =========================================================
# TAB 2: ORDER BOOK HEATMAP
# =========================================================
with tab_heatmap:
    st.subheader("🔥 Time-Density Order Book Liquidity Heatmap")
    
    heatmap_prices = np.round(np.linspace(2645.0, 2655.0, 21), 2)
    timestamps = [f"T-{25 - i}s" for i in range(25)]
    
    np.random.seed(42)
    matrix = np.random.randint(10, 80, size=(len(heatmap_prices), 25))
    matrix[2, :] = np.random.randint(220, 310, size=25)  
    matrix[17, :] = np.random.randint(180, 250, size=25) 

    fig_hm = go.Figure(data=go.Heatmap(
        z=matrix,
        x=timestamps,
        y=heatmap_prices,
        colorscale='Viridis',
        colorbar=dict(title='Contract Density')
    ))

    fig_hm.add_hline(y=2650.10, line_dash="dash", line_color="white", annotation_text="POC")
    fig_hm.update_layout(height=480, template="plotly_dark", xaxis_title="Time Snapshots", yaxis_title="Price ($)")
    st.plotly_chart(fig_hm, use_container_width=True)

# =========================================================
# TAB 3: AGENT DIAGNOSTIC LOGS
# =========================================================
with tab_war_room:
    st.subheader("🤖 Multi-Agent Diagnostic Logs")
    
    with st.status("Active Agent Microstructure Evaluation...", expanded=True):
        st.write("🟢 **Order Flow Agent:** High passive bid density detected at $2,646.00.")
        st.write("🟢 **Microstructure Agent:** Positive Cumulative Delta (+240) confirms buyer absorption.")
        st.write("🛡️ **Risk Guardrail Agent:** Account equity cushion is healthy and within limits.")
        st.write("⚡ **Execution Critic:** Order book imbalance ratio (2.14x) favors long bias.")

    st.subheader("📋 Analytical Decision Ledger")
    logs = pd.DataFrame([
        {"Timestamp": "09:30:12", "Symbol": "MGC", "Signal": "BUY SETUP", "Price": 2646.50, "Status": "Optimal", "Agent Confidence": "91%"},
        {"Timestamp": "09:15:00", "Symbol": "MGC", "Signal": "NEUTRAL", "Price": 2650.00, "Status": "Monitoring", "Agent Confidence": "45%"},
        {"Timestamp": "09:02:44", "Symbol": "MCL", "Signal": "SELL SETUP", "Price": 68.40, "Status": "Optimal", "Agent Confidence": "84%"},
    ])
    st.dataframe(logs, use_container_width=True)

# =========================================================
# TAB 4: PROP FIRM DRAWDOWN MONITOR
# =========================================================
with tab_risk:
    st.subheader("🛡️ Prop Firm Drawdown & Trailing Cushion")
    
    r1, r2, r3 = st.columns(3)
    r1.metric("Max Daily Loss Limit", f"${max_daily_loss}")
    r2.metric("Current Session PnL", "+$320.00", delta="Profitable")
    r3.metric("Loss Cushion Remaining", f"${max_daily_loss - 180:.2f}")

    st.markdown("### 📈 Cumulative Equity & Trailing Drawdown Floor")
    
    equity_data = pd.DataFrame({
        "Trade": np.arange(1, 11),
        "Account Equity": [50000, 50120, 50080, 50250, 50190, 50340, 50280, 50450, 50390, 50500],
        "Trailing Drawdown Floor": [49000, 49120, 49120, 49250, 49250, 49340, 49340, 49450, 49450, 49500]
    })
    
    st.line_chart(equity_data.set_index("Trade"))
