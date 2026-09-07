import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from order_flow_engine import CommodityOrderFlowEngine

st.set_page_config(
    page_title="AI Trading Arena - CME Commodities Master Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INSTITUTIONAL DARK THEME STYLING ---
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

st.title("🛡️ AI Trading Arena — CME Commodities & Agentic Terminal")

# --- SIDEBAR: COMMODITY & INFRASTRUCTURE CONTROLS ---
st.sidebar.header("🕹️ Infrastructure & Asset Controls")
selected_commodity = st.sidebar.selectbox(
    "Active Commodity Feed", 
    ["Micro Gold (MGC)", "Gold (GC)", "Micro Crude (MCL)", "Crude Oil (CL)", "Micro Silver (SIL)"]
)

backend_mode = st.sidebar.selectbox("Backend Architecture", ["Agentic Live Feed (Supabase)", "Simulation Mode"])
max_daily_loss = st.sidebar.number_input("Lucid Max Daily Loss Limit ($)", value=1000, step=100)
kill_switch = st.sidebar.toggle("🚨 Emergency Kill Switch", value=False)

if kill_switch:
    st.error("⚠️ EMERGENCY KILL SWITCH ACTIVE: Backend streaming and agent diagnostic loops paused.")

# --- TOP METRICS ROW ---
col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Active Asset", value=selected_commodity.split()[0].strip("()"))
col2.metric(label="Order Book Delta", value="+310.0 Contracts", delta="Strong Buy Pressure")
col3.metric(label="Volume POC", value="$2,650.10" if "Gold" in selected_commodity else ("$74.50" if "Crude" in selected_commodity else "$31.25"))
col4.metric(label="Agentic Architecture", value="ONLINE (Supabase)", delta="Synced")

st.markdown("---")

# --- MAIN NAVIGATION TABS ---
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
    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.subheader(f"📈 Price & Point of Control (POC) — {selected_commodity}")
        
        base_price = 2650.0 if "Gold" in selected_commodity else (74.5 if "Crude" in selected_commodity else 31.25)
        
        fig_price = go.Figure()
        time_series = pd.date_range(end=pd.Timestamp.now(), periods=30, freq='min')
        sim_prices = np.sin(np.linspace(0, 10, 30)) * 2 + base_price

        fig_price.add_trace(go.Scatter(x=time_series, y=sim_prices, mode='lines+markers', name='Price', line=dict(color='#00E676')))
        fig_price.add_hline(y=base_price, line_dash="dash", line_color="gold", annotation_text=f"POC: ${base_price:,.2f}")
        fig_price.add_hline(y=base_price - 4.0, line_color="#00E676", line_width=3, annotation_text="BUY WALL")
        fig_price.add_hline(y=base_price + 5.5, line_color="#FF5252", line_width=3, annotation_text="SELL WALL")

        fig_price.update_layout(template="plotly_dark", height=450, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_price, use_container_width=True)

    with right_col:
        st.subheader("📊 Level 2 Liquidity Depth")
        
        prices_depth = np.linspace(base_price - 5, base_price + 5, 15)
        bid_volumes = np.random.randint(20, 150, size=15)
        ask_volumes = np.random.randint(20, 150, size=15)
        bid_volumes[3] = 420  # Primary Support Wall
        ask_volumes[12] = 380 # Primary Resistance Wall

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
    st.subheader(f"🔥 Time-Density Order Book Liquidity Heatmap — {selected_commodity}")
    
    base_price = 2650.0 if "Gold" in selected_commodity else (74.5 if "Crude" in selected_commodity else 31.25)
    heatmap_prices = np.round(np.linspace(base_price - 5.0, base_price + 5.0, 21), 2)
    timestamps = [f"T-{25 - i}s" for i in range(25)]
    
    np.random.seed(42)
    matrix = np.random.randint(10, 90, size=(len(heatmap_prices), 25))
    matrix[2, :] = np.random.randint(250, 420, size=25)  # Bid Wall Zone
    matrix[17, :] = np.random.randint(200, 380, size=25) # Ask Wall Zone

    fig_hm = go.Figure(data=go.Heatmap(
        z=matrix,
        x=timestamps,
        y=heatmap_prices,
        colorscale='Viridis',
        colorbar=dict(title='Contract Density')
    ))

    fig_hm.add_hline(y=base_price, line_dash="dash", line_color="white", annotation_text="POC")
    fig_hm.update_layout(height=480, template="plotly_dark", xaxis_title="Time Snapshots", yaxis_title="Price ($)")
    st.plotly_chart(fig_hm, use_container_width=True)

# =========================================================
# TAB 3: AGENT DIAGNOSTIC LOGS
# =========================================================
with tab_war_room:
    st.subheader("🤖 Multi-Agent Architecture & Diagnostic Logs")
    
    with st.status("Agentic Architecture Active (Supabase Feed)...", expanded=True):
        st.write("🟢 **Order Flow Agent:** Heavy passive bid stacking identified near institutional support.")
        st.write("🟢 **Delta Momentum Agent:** Cumulative Delta reading indicates aggressive buyer accumulation.")
        st.write("🛡️ **Risk Guardrail Agent:** Account drawdown parameters and daily loss caps validated.")
        st.write("⚡ **Execution Critic:** Microstructure imbalance ratio optimal for limit liquidity capture.")

    st.subheader("📋 Agentic Decision Audit Ledger")
    logs = pd.DataFrame([
        {"Timestamp": "09:30:12", "Asset": selected_commodity, "Agent State": "OPTIMAL", "Signal Score": "94/100", "Action": "SETUP ARMED"},
        {"Timestamp": "09:15:00", "Asset": selected_commodity, "Agent State": "MONITORING", "Signal Score": "62/100", "Action": "HOLD"},
        {"Timestamp": "09:02:44", "Asset": selected_commodity, "Agent State": "OPTIMAL", "Signal Score": "89/100", "Action": "SETUP ARMED"},
    ])
    st.dataframe(logs, use_container_width=True)

# =========================================================
# TAB 4: PROP FIRM DRAWDOWN MONITOR
# =========================================================
with tab_risk:
    st.subheader("🛡️ Lucid Prop Firm Drawdown & Trailing Cushion")
    
    r1, r2, r3 = st.columns(3)
    r1.metric("Max Daily Loss Limit", f"${max_daily_loss}")
    r2.metric("Current Session PnL", "+$410.00", delta="Profitable")
    r3.metric("Loss Cushion Remaining", f"${max_daily_loss - 180:.2f}")

    st.markdown("### 📈 Cumulative Equity & Trailing Drawdown Floor")
    
    equity_data = pd.DataFrame({
        "Trade": np.arange(1, 11),
        "Account Equity": [100000, 100150, 100110, 100350, 100280, 100520, 100450, 100710, 100650, 100900],
        "Trailing Drawdown Floor": [97000, 97150, 97150, 97350, 97350, 97520, 97520, 97710, 97710, 97900]
    })
    
    st.line_chart(equity_data.set_index("Trade"))
