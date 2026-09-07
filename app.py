import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from order_flow_engine import CommodityOrderFlowEngine

st.set_page_config(
    page_title="AI War Room & Microstructure Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🛡️ Institutional Order Flow & AI War Room Terminal")

# --- SIDEBAR: GLOBAL STRATEGY & RISK CONTROLS ---
st.sidebar.header("🕹️ Strategy & Risk Controls")
selected_symbol = st.sidebar.selectbox("Active Asset", ["MGC (Micro Gold)", "MCL (Micro Crude)", "SIL (Micro Silver)"])
max_daily_loss = st.sidebar.number_input("Lucid Max Daily Loss ($)", value=1000, step=100)
kill_switch = st.sidebar.toggle("🚨 Emergency Kill Switch", value=False)

if kill_switch:
    st.error("⚠️ EMERGENCY KILL SWITCH ACTIVE: Trading Operations Paused.")

# --- TOP METRICS ROW (Original Badges + Live Metrics) ---
col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Order Book Imbalance", value="2.14x", delta="Bullish Bias")
col2.metric(label="Point of Control (POC)", value="$2,650.10")
col3.metric(label="Primary Buy Wall", value="$2,646.00", delta="310 Bids (Support)")
col4.metric(label="Primary Sell Wall", value="$2,653.50", delta="-250 Asks (Resistance)")

st.markdown("---")

# --- MAIN NAVIGATION TABS ---
tab_dashboard, tab_heatmap, tab_war_room, tab_risk = st.tabs([
    "📊 Core Microstructure Dashboard", 
    "🔥 Live Order Book Heatmap", 
    "🤖 AI War Room Diagnostics", 
    "🛡️ Prop Risk Guardrails"
])

# =========================================================
# TAB 1: ORIGINAL CORE DASHBOARD (Plots, POC, Walls, Depth)
# =========================================================
with tab_dashboard:
    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.subheader(f"📈 Price Chart with Institutional Walls & POC ({selected_symbol})")
        
        # Original Plotly Chart with Point of Control & Liquidity Lines
        fig_price = go.Figure()

        # Simulated Candle/Line Series
        time_series = pd.date_range(end=pd.Timestamp.now(), periods=30, freq='min')
        sim_prices = np.sin(np.linspace(0, 10, 30)) * 2 + 2650.0

        fig_price.add_trace(go.Scatter(x=time_series, y=sim_prices, mode='lines+markers', name='Price', line=dict(color='#00E676')))

        # Add POC Benchmark Line
        fig_price.add_hline(
            y=2650.10, 
            line_dash="dash", 
            line_color="gold", 
            annotation_text="POC: $2,650.10", 
            annotation_position="bottom right"
        )

        # Add Buy Wall Support Line
        fig_price.add_hline(
            y=2646.00, 
            line_color="#00E676", 
            line_width=3,
            annotation_text="BUY WALL: $2,646.00", 
            annotation_position="top left"
        )

        # Add Sell Wall Resistance Line
        fig_price.add_hline(
            y=2653.50, 
            line_color="#FF5252", 
            line_width=3,
            annotation_text="SELL WALL: $2,653.50", 
            annotation_position="bottom left"
        )

        fig_price.update_layout(
            template="plotly_dark",
            height=450,
            margin=dict(l=10, r=10, t=30, b=10)
        )
        st.plotly_chart(fig_price, use_container_width=True)

    with right_col:
        st.subheader("📊 Level 2 Liquidity Depth")
        
        # Original Horizontal Bid/Ask Liquidity Bar Chart
        prices_depth = np.linspace(2645, 2655, 15)
        bid_volumes = np.random.randint(10, 120, size=15)
        ask_volumes = np.random.randint(10, 120, size=15)
        bid_volumes[3] = 310  # Highlight Buy Wall
        ask_volumes[12] = 250 # Highlight Sell Wall

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
# TAB 2: NEW FEATURE — LIVE ORDER BOOK HEATMAP
# =========================================================
with tab_heatmap:
    st.subheader("🔥 Time-Density Order Book Liquidity Heatmap")
    
    heatmap_prices = np.round(np.linspace(2645.0, 2655.0, 21), 2)
    timestamps = [f"T-{25 - i}s" for i in range(25)]
    
    np.random.seed(42)
    matrix = np.random.randint(10, 80, size=(len(heatmap_prices), 25))
    matrix[2, :] = np.random.randint(220, 310, size=25)  # $2646.00 Wall
    matrix[17, :] = np.random.randint(180, 250, size=25) # $2653.50 Wall

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
# TAB 3: AI WAR ROOM & AGENT DIAGNOSTICS
# =========================================================
with tab_war_room:
    st.subheader("🤖 AI Agent Consensus & Reasoning")
    
    left_diag, right_feed = st.columns([2, 1])

    with left_diag:
        with st.status("Analyzing Market Microstructure...", expanded=True):
            st.write("🟢 **Order Flow Agent:** High passive bid density detected at $2,646.00.")
            st.write("🟢 **Microstructure Agent:** Positive Cumulative Delta (+240) confirms buyer absorption.")
            st.write("🛡️ **Risk Guardrail Agent:** Account equity cushion is healthy.")
            st.write("⚡ **Execution Critic:** Order book imbalance ratio (2.14x) favors long trades.")

        st.info("💡 **Consensus Strategy:** High probability Long setup near $2,646.00 support.")

    with right_feed:
        st.subheader("📋 Trade Parameters")
        st.write("**Asset:**", selected_symbol)
        st.write("**Entry Target:** $2,646.00")
        st.write("**Stop Loss:** $2,644.50")
        st.write("**Take Profit:** $2,653.00")
        
        if st.button("⚡ Manual Trade Approval", use_container_width=True):
            st.toast("Trade Signal logged into local session state!", icon="✅")

# =========================================================
# TAB 4: PROP FIRM RISK GUARDRAILS
# =========================================================
with tab_risk:
    st.subheader("🛡️ Lucid Prop Firm Drawdown & Equity Floor")
    
    r1, r2, r3 = st.columns(3)
    r1.metric("Max Daily Loss Limit", f"${max_daily_loss}")
    r2.metric("Current Daily PnL", "+$320.00", delta="Profitable")
    r3.metric("Loss Cushion Remaining", f"${max_daily_loss - 180:.2f}")

    st.markdown("### 📈 Cumulative Equity & Trailing Stop Threshold")
    
    equity_data = pd.DataFrame({
        "Trade": np.arange(1, 11),
        "Account Equity": [50000, 50120, 50080, 50250, 50190, 50340, 50280, 50450, 50390, 50500],
        "Trailing Drawdown Floor": [49000, 49120, 49120, 49250, 49250, 49340, 49340, 49450, 49450, 49500]
    })
    
    st.line_chart(equity_data.set_index("Trade"))
