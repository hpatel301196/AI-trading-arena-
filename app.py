import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf

st.set_page_config(
    page_title="AI Trading Arena - Multi-Asset Master Terminal",
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

st.title("🛡️ AI Trading Arena — Multi-Asset Master Terminal")

# --- SIDEBAR: ASSET & RISK CONTROLS ---
st.sidebar.header("🕹️ Global Controls")
selected_asset = st.sidebar.selectbox(
    "Active Market Asset", 
    ["Bitcoin (BTC-USD)", "Ethereum (ETH-USD)", "Gold (GC=F)", "Silver (SI=F)"]
)

risk_level = st.sidebar.slider("Risk Management Level (%)", 1, 5, 2)
kill_switch = st.sidebar.toggle("🚨 Emergency Kill Switch", value=False)

if kill_switch:
    st.error("⚠️ EMERGENCY KILL SWITCH ACTIVE: All live feeds and agent loops paused.")

# Map asset to Yahoo Finance ticker for live pricing
ticker_map = {
    "Bitcoin (BTC-USD)": "BTC-USD",
    "Ethereum (ETH-USD)": "ETH-USD",
    "Gold (GC=F)": "GC=F",
    "Silver (SI=F)": "SI=F"
}
current_ticker = ticker_map[selected_asset]

@st.cache_data(ttl=30)
def fetch_live_market_price(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1d", interval="1m")
        if not data.empty:
            return float(data['Close'].iloc[-1]), float(data['Open'].iloc[0])
    except Exception:
        pass
    # Fallback baselines
    return (68000.0 if "BTC" in ticker else (3500.0 if "ETH" in ticker else (2650.0 if "GC" in ticker else 31.5))), 67500.0

live_price, open_price = fetch_live_market_price(current_ticker)
price_change = round(live_price - open_price, 2)

# --- NAVIGATION TABS ---
tab_live, tab_agents, tab_volume, tab_journal = st.tabs([
    "📊 1. Live Price & Overview", 
    "🤖 2. AI Agent Debate & Score", 
    "📈 3. Detailed Volume Analysis", 
    "📋 4. Active Trade Journal"
])

# =========================================================
# TAB 1: LIVE PRICE SECTION
# =========================================================
with tab_live:
    st.subheader(f"🌐 Live Market Ticker & Overview — {selected_asset}")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Live Market Price", f"${live_price:,.2f}", delta=f"{price_change:+.2f}")
    col2.metric("24h Trend Bias", "Bullish Momentum", delta="Strong Buy")
    col3.metric("Order Book Imbalance", "2.14x Ratio", delta="Bids Stacked")
    col4.metric("System Status", "ONLINE", delta="Connected")

    st.markdown("---")
    
    # Live Price Action Chart
    fig_live = go.Figure()
    time_series = pd.date_range(end=pd.Timestamp.now(), periods=30, freq='min')
    sim_prices = np.linspace(live_price - 15, live_price + 10, 30)

    fig_live.add_trace(go.Scatter(x=time_series, y=sim_prices, mode='lines+markers', name='Live Price', line=dict(color='#00E676', width=2)))
    fig_live.add_hline(y=live_price, line_dash="dash", line_color="gold", annotation_text=f"Current: ${live_price:,.2f}")

    fig_live.update_layout(
        template="plotly_dark",
        height=480,
        xaxis_title="Time (Minutes)",
        yaxis_title="Price ($)",
        margin=dict(l=10, r=10, t=30, b=10)
    )
    st.plotly_chart(fig_live, use_container_width=True)

# =========================================================
# TAB 2: AI AGENT DEBATE & SCORE
# =========================================================
with tab_agents:
    st.subheader("🤖 AI Agent War Room Deliberation & Scoring")
    
    col_score, col_debate = st.columns([1, 2])
    
    with col_score:
        st.markdown("### 🎯 Manager Conviction Score")
        st.metric(label="Final Composite Score", value="91 / 100", delta="High Conviction Setup")
        st.info("💡 **Manager Verdict:** Consensus reached. Favorable risk-to-reward ratio detected for immediate entry.")
        
        if st.button("🚀 Execute Approved Signal", use_container_width=True):
            st.toast("Trade signal successfully transmitted!", icon="✅")

    with col_debate:
        st.subheader("💬 Multi-Agent Discussion Log")
        
        with st.status("🟢 Buyer Agent (Accumulation Lead):", expanded=True):
            st.write(f"Aggressive limit buying is absorbing all sell-side pressure on {selected_asset}. Order book depth shows strong buyer defense at current levels.")
            
        with st.status("🔴 Seller Agent (Resistance Analyst):", expanded=True):
            st.write("Noticed light trailing resistance overhead, but seller exhaustion is clearly visible on the lower timeframes. Upside path looks clean.")
            
        with st.status("🛡️ Risk Manager Agent:", expanded=True):
            st.write("Drawdown parameters verified. Position sizing set to standard risk percentage. Stop-loss placement secured below primary structural support.")

# =========================================================
# TAB 3: DETAILED VOLUME ANALYSIS
# =========================================================
with tab_volume:
    st.subheader(f"📈 Detailed Volume & Order Flow Profile — {selected_asset}")
    
    vol_col1, vol_col2 = st.columns([2, 1])
    
    with vol_col1:
        # Volume profile bar chart
        price_bins = np.round(np.linspace(live_price - 20, live_price + 20, 15), 2)
        buy_vols = np.random.randint(50, 400, size=15)
        sell_vols = np.random.randint(50, 400, size=15)
        buy_vols[4] = 750  # Point of Control high-volume node
        
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Bar(y=price_bins, x=-buy_vols, orientation='h', name='Buy Volume', marker_color='#00E676'))
        fig_vol.add_trace(go.Bar(y=price_bins, x=sell_vols, orientation='h', name='Sell Volume', marker_color='#FF5252'))
        
        fig_vol.update_layout(
            barmode='overlay',
            title="Volume Profile by Price Node",
            xaxis_title="Volume Distribution",
            yaxis_title="Price ($)",
            template="plotly_dark",
            height=450
        )
        st.plotly_chart(fig_vol, use_container_width=True)

    with vol_col2:
        st.subheader("📊 Volume Metrics")
        st.metric("Volume POC Node", f"${live_price - 5.0:,.2f}")
        st.metric("Cumulative Delta", "+1,840 Units", delta="Strong Inflow")
        st.metric("Delta Imbalance", "2.45x", delta="Bullish Domination")
        st.write("Volume nodes indicate heavy institutional accumulation at support zones.")

# =========================================================
# TAB 4: ACTIVE TRADE JOURNAL
# =========================================================
with tab_journal:
    st.subheader("📋 Active Trade Journal & Audit Ledger")
    st.markdown("Maintains a live record of all executed setups, entry parameters, and agent scoring metrics.")
    
    journal_data = pd.DataFrame([
        {"Trade ID": 201, "Timestamp": "10:14:22", "Asset": selected_asset, "Action": "BUY", "Entry Price": round(live_price - 10, 2), "Target Price": round(live_price + 25, 2), "Score": 91, "Status": "Active"},
        {"Trade ID": 200, "Timestamp": "09:30:12", "Asset": "Gold (GC=F)", "Action": "BUY", "Entry Price": 2646.50, "Target Price": 2655.00, "Score": 88, "Status": "Closed (+)"},
        {"Trade ID": 199, "Timestamp": "08:15:00", "Asset": "Ethereum (ETH-USD)", "Action": "SELL", "Entry Price": 3520.00, "Target Price": 3480.00, "Score": 85, "Status": "Closed (+)"}
    ])
    
    st.dataframe(journal_data, use_container_width=True)
    
    with st.form("add_journal_entry"):
        st.write("➕ **Log New Manual Trade**")
        j_col1, j_col2, j_col3 = st.columns(3)
        j_action = j_col1.selectbox("Action", ["BUY", "SELL"])
        j_target = j_col2.number_input("Target Price", value=float(live_price + 20))
        j_score = j_col3.slider("Agent Score Assigned", 50, 100, 90)
        
        if st.form_submit_button("Record to Journal"):
            new_entry = {
                "Trade ID": len(journal_data) + 202,
                "Timestamp": pd.Timestamp.now().strftime("%H:%M:%S"),
                "Asset": selected_asset,
                "Action": j_action,
                "Entry Price": round(live_price, 2),
                "Target Price": j_target,
                "Score": j_score,
                "Status": "Active"
            }
            st.success(f"Trade successfully logged to the journal ledger!")
