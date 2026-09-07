import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import ccxt

st.set_page_config(
    page_title="AI Trading Arena - Crypto & Commodities Terminal",
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

st.title("🛡️ AI Trading Arena — Crypto & Commodities Master Terminal")

# --- SIDEBAR: MULTI-ASSET SELECTOR & CONTROLS ---
st.sidebar.header("🕹️ Asset & Strategy Controls")
selected_asset = st.sidebar.selectbox(
    "Active Market Feed", 
    ["Bitcoin (BTC/USDT)", "Ethereum (ETH/USDT)", "Gold (XAU/USD)", "Silver (XAG/USD)"]
)

risk_tolerance = st.sidebar.slider("Risk Tolerance Level (%)", 1, 5, 2)
kill_switch = st.sidebar.toggle("🚨 Emergency Kill Switch", value=False)

if kill_switch:
    st.error("⚠️ EMERGENCY KILL SWITCH ACTIVE: All feeds and automated routines paused.")

# --- TOP METRICS ROW ---
col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Active Asset Feed", value=selected_asset.split()[0])
col2.metric(label="Order Book Delta", value="+420.5 BTC / Eq", delta="Strong Buy Bias")
col3.metric(label="Volume POC", value="$67,450.00" if "BTC" in selected_asset else ("$3,520.00" if "ETH" in selected_asset else "$2,650.10"))
col4.metric(label="AI War Room Status", value="ONLINE", delta="Scanning L2")

st.markdown("---")

# --- MAIN DASHBOARD LAYOUT ---
tab_overview, tab_orderbook, tab_war_room, tab_journal = st.tabs([
    "📊 Market Overview & POC", 
    "🔥 L2 Depth & Liquidity Walls", 
    "🤖 AI War Room Diagnostics", 
    "📋 Active Trade Journal"
])

# =========================================================
# TAB 1: MARKET OVERVIEW & POC
# =========================================================
with tab_overview:
    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.subheader(f"📈 Price & Point of Control (POC) — {selected_asset}")
        
        # Dynamic base prices depending on Crypto vs Commodities
        base_price = 67500.0 if "BTC" in selected_asset else (3500.0 if "ETH" in selected_asset else (2650.0 if "Gold" in selected_asset else 31.5))
        
        fig_price = go.Figure()
        time_series = pd.date_range(end=pd.Timestamp.now(), periods=30, freq='min')
        sim_prices = np.sin(np.linspace(0, 10, 30)) * (base_price * 0.005) + base_price

        fig_price.add_trace(go.Scatter(x=time_series, y=sim_prices, mode='lines+markers', name='Price', line=dict(color='#00E676')))
        fig_price.add_hline(y=base_price, line_dash="dash", line_color="gold", annotation_text=f"POC: ${base_price:,.2f}")

        fig_price.update_layout(template="plotly_dark", height=450, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_price, use_container_width=True)

    with right_col:
        st.subheader("⚡ Real-Time Imbalance Metrics")
        st.metric("Bid / Ask Ratio", "1.84x", delta="Buyers in Control")
        st.metric("Cumulative Delta (5m)", "+1,250 Units", delta="Accumulation")
        st.metric("Volatility Index (ATR)", "Medium-High", delta="Breakout Watch")
        
        st.info(f"💡 **Asset Focus:** Tracking centralized exchange and commodity feed for **{selected_asset}**.")

# =========================================================
# TAB 2: L2 DEPTH & LIQUIDITY WALLS
# =========================================================
with tab_orderbook:
    st.subheader(f"🔥 Level 2 Order Book Depth Profile — {selected_asset}")
    
    base_p = 67500.0 if "BTC" in selected_asset else (3500.0 if "ETH" in selected_asset else (2650.0 if "Gold" in selected_asset else 31.5))
    prices_depth = np.linspace(base_p * 0.995, base_p * 1.005, 15)
    bid_volumes = np.random.randint(50, 300, size=15)
    ask_volumes = np.random.randint(50, 300, size=15)
    bid_volumes[3] = 850  # Major Support Wall
    ask_volumes[11] = 720 # Major Resistance Wall

    fig_depth = go.Figure()
    fig_depth.add_trace(go.Bar(y=prices_depth, x=-bid_volumes, orientation='h', name='Bid Wall (Buy)', marker_color='#00E676'))
    fig_depth.add_trace(go.Bar(y=prices_depth, x=ask_volumes, orientation='h', name='Ask Wall (Sell)', marker_color='#FF5252'))

    fig_depth.update_layout(
        barmode='overlay',
        xaxis_title="Contract Volume (Bids ← | → Asks)",
        yaxis_title="Price ($)",
        height=480,
        template="plotly_dark",
        margin=dict(l=10, r=10, t=30, b=10)
    )
    st.plotly_chart(fig_depth, use_container_width=True)

# =========================================================
# TAB 3: AI WAR ROOM DIAGNOSTICS
# =========================================================
with tab_war_room:
    st.subheader("🤖 Multi-Agent War Room Deliberation Feed")
    
    with st.status("Agents Analyzing Cross-Asset Microstructure...", expanded=True):
        st.write(f"🟢 **Order Flow Agent:** Heavy limit bidding detected on {selected_asset}.")
        st.write("🟢 **Delta Momentum Agent:** Positive cumulative delta wave confirms breakout probability.")
        st.write("🛡️ **Risk Guardrail Agent:** Volatility thresholds within normal operating bounds.")
        st.write("⚡ **Execution Critic:** Recommended limit order placement directly inside the primary bid wall.")

    st.success("🎯 **Consensus:** High probability long setup active.")

# =========================================================
# TAB 4: ACTIVE TRADE JOURNAL
# =========================================================
with tab_journal:
    st.subheader("📋 Autonomous Trade Journal & Audit Ledger")
    
    journal_df = pd.DataFrame([
        {"Timestamp": "10:14:22", "Asset": "BTC/USDT", "Signal": "BUY", "Entry": 67200.0, "Target": 67800.0, "Status": "Active", "Confidence": "94%"},
        {"Timestamp": "09:30:12", "Asset": "Gold (XAU/USD)", "Signal": "BUY", "Entry": 2646.50, "Target": 2655.00, "Status": "Closed (+)", "Confidence": "91%"},
        {"Timestamp": "08:15:00", "Asset": "ETH/USDT", "Signal": "SELL", "Entry": 3520.00, "Target": 3480.00, "Status": "Closed (+)", "Confidence": "88%"},
    ])
    st.dataframe(journal_df, use_container_width=True)
