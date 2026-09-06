import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import random
from datetime import datetime

# -------------------------------------------------------------
# PAGE CONFIGURATION & STYLING
# -------------------------------------------------------------
st.set_page_config(
    page_title="Autonomous AI Trading Arena",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Dark Theme & Card Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1E222D;
        border: 1px solid #2A2E39;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .status-badge-buy {
        background-color: #089981;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .status-badge-sell {
        background-color: #F23645;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .status-badge-hold {
        background-color: #787B86;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. AUTONOMOUS AUTO-REFRESH ENGINE (Every 60 Seconds)
# -------------------------------------------------------------
# Refreshes the app state automatically without manual button clicks
count = st_autorefresh(interval=60000, limit=1000, key="auto_eval_loop")

# Initialize persistent session states for history and logs
if "trade_ledger" not in st.session_state:
    st.session_state.trade_ledger = []
if "agent_balances" not in st.session_state:
    st.session_state.agent_balances = {
        "Agent_Alpha_Quant": {"cash": 100000.0, "pnl": 0.0, "trades": 0},
        "Agent_Beta_Sentiment": {"cash": 100000.0, "pnl": 0.0, "trades": 0},
        "Agent_Gamma_Risk": {"cash": 100000.0, "pnl": 0.0, "trades": 0},
        "Agent_Delta_Hybrid": {"cash": 100000.0, "pnl": 0.0, "trades": 0}
    }

# -------------------------------------------------------------
# 2. LIVE MARKET DATA ENGINE
# -------------------------------------------------------------
@st.cache_data(ttl=30)
def fetch_live_prices():
    tickers = {"BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "GC=F": "Gold", "SI=F": "Silver"}
    data = {}
    for symbol, name in tickers.items():
        try:
            t = yf.Ticker(symbol)
            price = t.fast_info['lastPrice']
            data[name] = round(price, 2)
        except:
            data[name] = 1000.0
    return data

live_prices = fetch_live_prices()

# --- HEADER SECTION ---
st.title("🤖 Autonomous AI Multi-Agent Trading Arena")
st.caption(f"⚡ Live System State | Cycle: #{count} | Last Auto-Scan: {datetime.now().strftime('%H:%M:%S')}")

# Top Metric Cards
cols = st.columns(4)
for i, (asset, price) in enumerate(live_prices.items()):
    cols[i].metric(label=f"Market {asset}", value=f"${price:,.2f}", delta=f"{random.uniform(-0.5, 0.8):.2f}%")

st.divider()

# -------------------------------------------------------------
# 3. AUTONOMOUS AGENT DECISION & BROKERAGE ENGINE
# -------------------------------------------------------------
def run_autonomous_cycle():
    votes = {"BUY": 0, "SELL": 0, "HOLD": 0}
    assets = list(live_prices.keys())
    
    for agent_id, state in st.session_state.agent_balances.items():
        # Agent Strategy Logic Simulation (Triggers decision every cycle)
        decision = random.choice(["BUY", "SELL", "HOLD", "HOLD"])  # Weighted toward patience
        votes[decision] += 1
        
        if decision in ["BUY", "SELL"]:
            selected_asset = random.choice(assets)
            market_price = live_prices[selected_asset]
            trade_amount = 0.1 if "Bitcoin" in selected_asset else 1.0
            
            # Simulated Friction Costs
            slippage = market_price * 0.0005
            effective_price = market_price + slippage if decision == "BUY" else market_price - slippage
            fee = (trade_amount * effective_price) * 0.001
            
            # Simulated Realized PnL on transaction completion
            realized_pnl = round(random.uniform(-150.0, 350.0), 2)
            
            # Update Agent Account State
            state["cash"] += realized_pnl - fee
            state["pnl"] += realized_pnl
            state["trades"] += 1
            
            # Log Trade Transaction Details
            trade_entry = {
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "Agent": agent_id.replace("_", " "),
                "Asset": selected_asset,
                "Action": decision,
                "Size": trade_amount,
                "Base Price": f"${market_price:,.2f}",
                "Effective Price": f"${effective_price:,.2f}",
                "Slippage/Fee": f"${(slippage + fee):,.2f}",
                "Realized PnL": realized_pnl
            }
            st.session_state.trade_ledger.insert(0, trade_entry)
            
    return votes

# Execute Autonomous Loop on Page Refresh Cycle
current_votes = run_autonomous_cycle()

# -------------------------------------------------------------
# 4. DASHBOARD PANELS
# -------------------------------------------------------------
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🎯 Ensemble Voting Consensus")
    top_consensus = max(current_votes, key=current_votes.get)
    
    st.info(f"**Current Consensus Signal:** `{top_consensus}` | Breakdown: {current_votes}")

with col_right:
    st.subheader("🏆 Leaderboard Rankings")
    leaderboard_df = pd.DataFrame([
        {
            "Agent": k.replace("_", " "),
            "Total Net Worth": f"${v['cash']:,.2f}",
            "Total PnL": f"${v['pnl']:,.2f}",
            "Executed Trades": v["trades"]
        } for k, v in st.session_state.agent_balances.items()
    ])
    st.dataframe(leaderboard_df, use_container_width=True, hide_index=True)

st.divider()

# -------------------------------------------------------------
# 5. DETAILED TRANSACTION AUDIT LEDGER
# -------------------------------------------------------------
st.subheader("📑 Live Agent Trade Audit Log")

if len(st.session_state.trade_ledger) > 0:
    ledger_df = pd.DataFrame(st.session_state.trade_ledger)
    
    # Highlight Profit / Loss colors
    def color_pnl(val):
        color = '#089981' if val > 0 else '#F23645' if val < 0 else 'white'
        return f'color: {color}; font-weight: bold;'

    st.dataframe(
        ledger_df.style.map(color_pnl, subset=['Realized PnL']),
        use_container_width=True,
        hide_index=True
    )
else:
    st.write("Awaiting initial trade executions from autonomous agents...")
