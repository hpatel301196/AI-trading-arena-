import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time

st.set_page_config(
    page_title="AI Trading Terminal - Multi-Agent & Order Flow",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🛡️ Institutional Order Flow & War Room Terminal")

# --- SIDEBAR: GLOBAL CONTROLS & RISK SWITCH ---
st.sidebar.header("🕹️ Master Controls")
selected_symbol = st.sidebar.selectbox("Active Asset", ["MGC (Micro Gold)", "MCL (Micro Crude)", "SIL (Micro Silver)"])
max_daily_loss = st.sidebar.number_input("Lucid Max Daily Loss ($)", value=1000, step=100)
kill_switch = st.sidebar.toggle("🚨 Emergency Kill Switch", value=False)

if kill_switch:
    st.error("⚠️ EMERGENCY KILL SWITCH ACTIVE: Automatic & Manual Executions Paused.")

# --- NAVIGATION TABS ---
tab_war_room, tab_heatmap, tab_risk, tab_audit = st.tabs([
    "🤖 AI War Room", 
    "🔥 Order Book Heatmap", 
    "📊 Prop Risk Guardrails", 
    "📋 Execution Audit Log"
])

# ==========================================
# TAB 1: AI WAR ROOM COMMAND CENTER
# ==========================================
with tab_war_room:
    st.subheader("🤖 AI Agent Decision Engine")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Delta", "+240 Contracts", delta="12% vs 5m Avg")
    col2.metric("Dominant Bid Wall", "$2,646.00", delta="310 Bids (Strong)")
    col3.metric("Dominant Ask Wall", "$2,653.50", delta="-250 Asks")
    col4.metric("Strategy Confidence", "88%", delta="High Probability")
    
    st.markdown("---")
    
    left_diag, right_feed = st.columns([2, 1])
    
    with left_diag:
        st.subheader("🔍 Real-Time Microstructure Diagnostics")
        
        with st.status("Analyzing Live Order Book & Trades...", expanded=True):
            st.write("🟢 **Order Flow Agent:** Heavy passive buyers stacked at $2,646.00.")
            st.write("🟢 **Microstructure Agent:** Cumulative Delta shift is positive (+240).")
            st.write("🛡️ **Risk Guardrail Agent:** Current session loss is $180. Within $1,000 drawdown threshold.")
            st.write("⚡ **Execution Critic:** Order book imbalance ratio is 2.14 (Bullish Advantage).")

        st.info("💡 **AI Consensus:** High probability BUY setup near $2,646.00 support.")

    with right_feed:
        st.subheader("⚡ Quick Action")
        st.write("**Asset:**", selected_symbol)
        st.write("**Entry Zone:** $2,646.00 - $2,647.00")
        st.write("**Stop Loss:** $2,644.50 (3 Ticks)")
        st.write("**Take Profit:** $2,653.00 (14 Ticks)")
        
        if st.button("🚀 Trigger Manual Execution Signal", use_container_width=True):
            st.toast("BUY Signal sent to internal event bus!", icon="⚡")

# ==========================================
# TAB 2: ORDER BOOK HEATMAP
# ==========================================
with tab_heatmap:
    st.subheader("📊 Level 2 Market Depth Heatmap")
    
    # Generate Heatmap Matrix
    prices = np.round(np.linspace(2645.0, 2655.0, 21), 2)
    timestamps = [f"T-{25 - i}s" for i in range(25)]
    
    np.random.seed(42)
    matrix = np.random.randint(10, 80, size=(len(prices), 25))
    
    # Bid/Ask Walls
    matrix[2, :] = np.random.randint(220, 310, size=25)  # $2646.00
    matrix[17, :] = np.random.randint(180, 250, size=25) # $2653.50
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=timestamps,
        y=prices,
        colorscale='Viridis',
        colorbar=dict(title='Volume')
    ))
    
    fig.add_hline(y=2650.0, line_dash="dash", line_color="white", annotation_text="Mid Price")
    fig.update_layout(height=480, template="plotly_dark", xaxis_title="Time Buffer", yaxis_title="Price ($)")
    
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TAB 3: PROP RISK GUARDRAILS
# ==========================================
with tab_risk:
    st.subheader("🛡️ Lucid Prop Firm Drawdown & Trailing Cushion")
    
    r1, r2, r3 = st.columns(3)
    r1.metric("Max Daily Loss Limit", f"${max_daily_loss}")
    r2.metric("Current Daily PnL", "+$320.00", delta="Profitable")
    r3.metric("Remaining Buffer", f"${max_daily_loss - 180:.2f}")
    
    st.markdown("### 📈 Cumulative Equity & Trailing Stop Threshold")
    
    equity_data = pd.DataFrame({
        "Trade": np.arange(1, 11),
        "Account Equity": [50000, 50120, 50080, 50250, 50190, 50340, 50280, 50450, 50390, 50500],
        "Trailing Drawdown Floor": [49000, 49120, 49120, 49250, 49250, 49340, 49340, 49450, 49450, 49500]
    })
    
    st.line_chart(equity_data.set_index("Trade"))

# ==========================================
# TAB 4: EXECUTION AUDIT LOG
# ==========================================
with tab_audit:
    st.subheader("📋 System Trade & Signal Log")
    
    logs = pd.DataFrame([
        {"Timestamp": "09:30:12", "Symbol": "MGC", "Signal": "BUY", "Price": 2646.50, "Status": "Logged", "Agent Confidence": "91%"},
        {"Timestamp": "09:15:00", "Symbol": "MGC", "Signal": "HOLD", "Price": 2650.00, "Status": "Passed", "Agent Confidence": "45%"},
        {"Timestamp": "09:02:44", "Symbol": "MCL", "Signal": "SELL", "Price": 68.40, "Status": "Logged", "Agent Confidence": "84%"},
    ])
    
    st.dataframe(logs, use_container_width=True)
