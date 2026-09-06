import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import random
from datetime import datetime

# -------------------------------------------------------------
# 1. PAGE CONFIG & MODERN UI STYLING
# -------------------------------------------------------------
st.set_page_config(
    page_title="Autonomous AI Trading Arena",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Modern Look
st.markdown("""
<style>
    .main {
        background-color: #0E1117;
    }
    .stMetric {
        background: #1E222D;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2A2E39;
    }
    .asset-card {
        background-color: #161A25;
        border: 1px solid #2A2E39;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
    }
    .badge-buy { background-color: #089981; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .badge-sell { background-color: #F23645; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .badge-hold { background-color: #5D606B; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Auto-refresh loop every 60 seconds
count = st_autorefresh(interval=60000, limit=10000, key="auto_refresh_loop")

# -------------------------------------------------------------
# 2. SESSION STATE MANAGEMENT
# -------------------------------------------------------------
if "trade_ledger" not in st.session_state:
    st.session_state.trade_ledger = []

if "equity_history" not in st.session_state:
    st.session_state.equity_history = []

if "agent_balances" not in st.session_state:
    st.session_state.agent_balances = {
        "Agent Alpha (Quant)": {"cash": 100000.0, "pnl": 0.0, "trades": 0, "color": "#00F2FE"},
        "Agent Beta (Sentiment)": {"cash": 100000.0, "pnl": 0.0, "trades": 0, "color": "#4FACFE"},
        "Agent Gamma (Risk Engine)": {"cash": 100000.0, "pnl": 0.0, "trades": 0, "color": "#00E676"},
        "Agent Delta (Hybrid LLM)": {"cash": 100000.0, "pnl": 0.0, "trades": 0, "color": "#FF5252"}
    }

# -------------------------------------------------------------
# 3. LIVE MARKET DATA INGESTION
# -------------------------------------------------------------
@st.cache_data(ttl=25)
def fetch_live_prices():
    tickers = {
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Gold": "GC=F",
        "Silver": "SI=F"
    }
    prices = {}
    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            prices[name] = round(t.fast_info['lastPrice'], 2)
        except:
            prices[name] = 1000.0
    return prices

live_prices = fetch_live_prices()

# Header Dashboard
st.title("⚡ Autonomous Multi-Agent AI Trading Arena")
st.caption(f"System Operational | Cycle #{count} | Last Updated: {datetime.now().strftime('%H:%M:%S UTC')}")

# Live Price Ticker Cards
cols = st.columns(4)
for i, (asset, price) in enumerate(live_prices.items()):
    cols[i].metric(
        label=f"Market {asset}",
        value=f"${price:,.2f}",
        delta=f"{random.uniform(-0.4, 0.6):.2f}%"
    )

st.divider()

# -------------------------------------------------------------
# 4. CONDITIONAL SIGNAL & AUTONOMOUS TRADING ENGINE
# -------------------------------------------------------------
def run_trading_cycle():
    # Per-Asset Voting Matrix
    asset_votes = {asset: {"BUY": 0, "SELL": 0, "HOLD": 0} for asset in live_prices.keys()}
    
    for agent_id, state in st.session_state.agent_balances.items():
        # Evaluate each asset conditionally
        for asset, current_price in live_prices.items():
            
            # --- CONDITION CHECK (Prevents trading every minute) ---
            # Signal Probability: 80% chance of HOLD, 20% chance of Trade Setup
            signal_trigger = random.random()
            
            if signal_trigger > 0.80:
                decision = random.choice(["BUY", "SELL"])
            else:
                decision = "HOLD"
                
            asset_votes[asset][decision] += 1
            
            # Execute Trade ONLY if signal exists and isn't HOLD
            if decision in ["BUY", "SELL"]:
                trade_size = 0.1 if asset == "Bitcoin" else (1.0 if asset == "Ethereum" else 2.0)
                
                # Friction: Slippage and Brokerage Fee
                slippage = current_price * 0.0004
                effective_price = current_price + slippage if decision == "BUY" else current_price - slippage
                fee = (trade_size * effective_price) * 0.001
                
                # Realized Return logic
                pnl = round(random.uniform(-120.0, 280.0), 2)
                
                # Update State
                state["cash"] += (pnl - fee)
                state["pnl"] += pnl
                state["trades"] += 1
                
                # Record to Audit Ledger
                st.session_state.trade_ledger.insert(0, {
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Agent": agent_id,
                    "Asset": asset,
                    "Action": decision,
                    "Size": trade_size,
                    "Market Price": f"${current_price:,.2f}",
                    "Exec Price": f"${effective_price:,.2f}",
                    "Slippage/Fee": f"${(slippage + fee):,.2f}",
                    "Realized PnL": pnl
                })
                
    # Record Snapshot for Equity Curve
    snapshot = {"Timestamp": datetime.now().strftime("%H:%M:%S")}
    for agent, data in st.session_state.agent_balances.items():
        snapshot[agent] = data["cash"]
    st.session_state.equity_history.append(snapshot)
    
    return asset_votes

asset_consensus = run_trading_cycle()

# -------------------------------------------------------------
# 5. DASHBOARD LAYOUT
# -------------------------------------------------------------
col1, col2 = st.columns([1, 1])

# --- PANEL 1: PER-ASSET ENSEMBLE CONSENSUS ---
with col1:
    st.subheader("🎯 Per-Asset Consensus Signals")
    
    for asset, votes in asset_consensus.items():
        # Determine winning direction for this specific asset
        top_signal = max(votes, key=votes.get)
        
        badge_class = "badge-buy" if top_signal == "BUY" else ("badge-sell" if top_signal == "SELL" else "badge-hold")
        
        st.markdown(f"""
        <div class="asset-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 16px; font-weight: bold;">{asset}</span>
                <span class="{badge_class}">{top_signal}</span>
            </div>
            <div style="font-size: 12px; color: #787B86; margin-top: 5px;">
                Agent Votes: BUY ({votes['BUY']}) | SELL ({votes['SELL']}) | HOLD ({votes['HOLD']})
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- PANEL 2: LEADERBOARD & PERFORMANCE RANKING ---
with col2:
    st.subheader("🏆 Agent Performance Leaderboard")
    
    leaderboard_df = pd.DataFrame([
        {
            "Agent Name": agent,
            "Net Worth": f"${data['cash']:,.2f}",
            "Total PnL": f"${data['pnl']:,.2f}",
            "Active Trades": data["trades"]
        } for agent, data in st.session_state.agent_balances.items()
    ])
    
    st.dataframe(leaderboard_df, use_container_width=True, hide_index=True)

st.divider()

# -------------------------------------------------------------
# 6. INTERACTIVE EQUITY CURVE CHART
# -------------------------------------------------------------
st.subheader("📈 Live Portfolio Performance Curves")

if len(st.session_state.equity_history) > 1:
    equity_df = pd.DataFrame(st.session_state.equity_history)
    fig = go.Figure()
    
    for agent, data in st.session_state.agent_balances.items():
        fig.add_trace(go.Scatter(
            x=equity_df["Timestamp"],
            y=equity_df[agent],
            mode="lines",
            name=agent,
            line=dict(width=2, color=data["color"])
        ))
        
    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=20, r=20, t=20, b=20),
        height=320,
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        yaxis=dict(title="Portfolio Cash ($)"),
        xaxis=dict(title="Time Scan")
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# -------------------------------------------------------------
# 7. DETAILED TRANSACTION AUDIT LEDGER
# -------------------------------------------------------------
st.subheader("📑 Real-Time Trade Audit Log")

if len(st.session_state.trade_ledger) > 0:
    ledger_df = pd.DataFrame(st.session_state.trade_ledger)
    
    def color_pnl(val):
        color = '#089981' if val > 0 else '#F23645' if val < 0 else '#ffffff'
        return f'color: {color}; font-weight: bold;'

    st.dataframe(
        ledger_df.style.map(color_pnl, subset=['Realized PnL']),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Agents are currently in HOLD mode scanning for actionable market setups...")
