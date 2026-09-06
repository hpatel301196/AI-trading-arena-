import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from supabase import create_client, Client
import random
from datetime import datetime, date

# -------------------------------------------------------------
# 1. PAGE CONFIG & MODERN CSS INJECTION
# -------------------------------------------------------------
st.set_page_config(
    page_title="Autonomous AI Trading Arena",
    page_icon="⚡",
    layout="wide"
)

# Advanced CSS Injection for Glassmorphic Terminal Theme
st.markdown("""
<style>
    /* Dark Theme Core */
    .stApp {
        background-color: #090C10;
        color: #E6EDF3;
    }
    
    /* Clean Typography & High Contrast Headers */
    h1, h2, h3, h4, h5 {
        color: #FFFFFF !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-weight: 700 !important;
    }

    /* Metric Cards Custom Styling */
    div[data-testid="stMetric"] {
        background: rgba(22, 27, 34, 0.75);
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stMetric"] label {
        color: #8B949E !important;
        font-weight: 600;
        font-size: 13px;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 24px;
        font-weight: 800;
    }

    /* Custom Glassmorphic Card Containers */
    .terminal-card {
        background: rgba(22, 27, 34, 0.6);
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        backdrop-filter: blur(8px);
    }

    /* Signal Badges */
    .badge-buy { background-color: rgba(0, 230, 118, 0.15); color: #00E676; border: 1px solid #00E676; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; }
    .badge-sell { background-color: rgba(255, 82, 82, 0.15); color: #FF5252; border: 1px solid #FF5252; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; }
    .badge-hold { background-color: rgba(139, 148, 158, 0.15); color: #8B949E; border: 1px solid #8B949E; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; }
    .badge-locked { background-color: rgba(255, 193, 7, 0.15); color: #FFC107; border: 1px solid #FFC107; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; }

    /* Live Pulse Indicator */
    .pulse-dot {
        height: 10px;
        width: 10px;
        background-color: #00E676;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 8px #00E676;
    }
</style>
""", unsafe_allow_html=True)

# 60-Second Auto Refresh Loop
count = st_autorefresh(interval=60000, limit=10000, key="arena_auto_refresh")

# Initialize Supabase
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"⚠️ Supabase Secrets Configuration Error: {e}")
        st.stop()

supabase: Client = init_supabase()

# -------------------------------------------------------------
# 2. PERSISTENT STATE & DATA LOADERS
# -------------------------------------------------------------
def load_db_state():
    response = supabase.table("agent_portfolio").select("*").execute()
    agents = {row["agent_id"]: row for row in response.data}
    
    # Auto-reset trade counter if calendar day changes
    today_str = str(date.today())
    for agent_id, data in agents.items():
        if str(data.get("last_trade_date")) != today_str:
            supabase.table("agent_portfolio").update({
                "trades_today": 0,
                "last_trade_date": today_str
            }).eq("agent_id", agent_id).execute()
            data["trades_today"] = 0
            
    return agents

def load_trade_ledger():
    response = supabase.table("trade_ledger_history").select("*").order("id", desc=True).limit(30).execute()
    return response.data

@st.cache_data(ttl=20)
def fetch_live_prices():
    tickers = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Gold": "GC=F", "Silver": "SI=F"}
    prices = {}
    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            prices[name] = round(t.fast_info['lastPrice'], 2)
        except:
            prices[name] = 1000.0
    return prices

live_prices = fetch_live_prices()
agent_db = load_db_state()

# -------------------------------------------------------------
# 3. TOP TERMINAL HEADER BAR
# -------------------------------------------------------------
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
    <div>
        <h1 style="margin: 0; font-size: 28px;">⚡ Autonomous AI Trading Arena</h1>
        <p style="margin: 0; color: #8B949E; font-size: 13px;">Multi-Agent Evolutionary Sandbox • Real-Time Paper Execution Engine</p>
    </div>
    <div style="text-align: right; background: rgba(22, 27, 34, 0.8); padding: 8px 16px; border-radius: 8px; border: 1px solid #30363D;">
        <span class="pulse-dot"></span> <b style="color: #00E676;">LIVE ENGINE</b>
        <div style="font-size: 11px; color: #8B949E;">Scan #{count} • {datetime.now().strftime('%H:%M:%S UTC')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Live Ticker Cards
cols = st.columns(4)
for i, (asset, price) in enumerate(live_prices.items()):
    cols[i].metric(label=f"{asset.upper()} / USD", value=f"${price:,.2f}", delta=f"{random.uniform(-0.6, 0.9):.2f}%")

st.divider()

# -------------------------------------------------------------
# 4. CONDITIONAL TRADING EXECUTION ENGINE
# -------------------------------------------------------------
def process_trading_cycle():
    asset_votes = {asset: {"BUY": 0, "SELL": 0, "HOLD": 0} for asset in live_prices.keys()}
    rationales = []
    
    # Decision rationale templates for UI visual feedback
    buy_reasons = ["RSI divergence detected (<30)", "Volume surge on 1-hour candle", "Macro news sentiment positive"]
    sell_reasons = ["Take-profit target reached", "MACD bearish cross", "Risk allocation limit hit"]

    for agent_id, data in agent_db.items():
        trades_today = data.get("trades_today", 0)
        current_pos = data.get("current_position")
        cash = float(data.get("cash", 100000.0))
        
        if trades_today >= 4:
            continue
            
        target_asset = random.choice(list(live_prices.keys()))
        market_price = live_prices[target_asset]
        
        # BUY Logic (Only if not holding an active position)
        if current_pos is None:
            decision = "BUY" if random.random() > 0.82 else "HOLD"
            asset_votes[target_asset][decision] += 1
            
            if decision == "BUY":
                units = round((cash * 0.98) / market_price, 4)
                new_pos = {"asset": target_asset, "entry_price": market_price, "units": units}
                reason = random.choice(buy_reasons)
                
                supabase.table("agent_portfolio").update({
                    "cash": 0.0, "current_position": new_pos, "trades_today": trades_today + 1
                }).eq("agent_id", agent_id).execute()
                
                supabase.table("trade_ledger_history").insert({
                    "agent_id": agent_id, "asset": target_asset, "action": "BUY",
                    "size": units, "price": market_price, "pnl": 0.0, "trade_num": trades_today + 1
                }).execute()
                
                rationales.append(f"<b>{agent_id.replace('_', ' ')}</b>: BUY <b>{target_asset}</b> @ ${market_price:,.2f} — <i>'{reason}'</i>")

        # SELL Logic (Only if position currently active)
        else:
            held_asset = current_pos["asset"]
            held_units = current_pos["units"]
            current_mkt_price = live_prices[held_asset]
            
            decision = "SELL" if random.random() > 0.78 else "HOLD"
            asset_votes[held_asset][decision] += 1
            
            if decision == "SELL":
                gross = held_units * current_mkt_price
                fee = gross * 0.001
                net_cash = round(gross - fee, 2)
                realized_pnl = round(net_cash - 100000.0, 2)
                reason = random.choice(sell_reasons)
                
                supabase.table("agent_portfolio").update({
                    "cash": net_cash, "current_position": None,
                    "trades_today": trades_today + 1, "total_pnl": realized_pnl
                }).eq("agent_id", agent_id).execute()
                
                supabase.table("trade_ledger_history").insert({
                    "agent_id": agent_id, "asset": held_asset, "action": "SELL",
                    "size": held_units, "price": current_mkt_price, "pnl": realized_pnl, "trade_num": trades_today + 1
                }).execute()
                
                rationales.append(f"<b>{agent_id.replace('_', ' ')}</b>: SELL <b>{held_asset}</b> (PnL: ${realized_pnl:,.2f}) — <i>'{reason}'</i>")

    return asset_votes, rationales

asset_consensus, latest_rationales = process_trading_cycle()
agent_db = load_db_state()
trade_ledger = load_trade_ledger()

# -------------------------------------------------------------
# 5. DASHBOARD LAYOUT & PANELS
# -------------------------------------------------------------
col1, col2 = st.columns([1, 1])

# --- PANEL 1: CONSENSUS SIGNALS & AI RATIONALE ---
with col1:
    st.subheader("🎯 Per-Asset Consensus Matrix")
    for asset, votes in asset_consensus.items():
        top_signal = max(votes, key=votes.get)
        badge_style = "badge-buy" if top_signal == "BUY" else ("badge-sell" if top_signal == "SELL" else "badge-hold")
        
        st.markdown(f"""
        <div class="terminal-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 16px; font-weight: 700;">{asset}</span>
                <span class="{badge_style}">{top_signal}</span>
            </div>
            <div style="font-size: 12px; color: #8B949E; margin-top: 6px;">
                Agent Consensus: <b style="color: #00E676;">{votes['BUY']} BUY</b> | <b style="color: #FF5252;">{votes['SELL']} SELL</b> | <b style="color: #8B949E;">{votes['HOLD']} HOLD</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    if latest_rationales:
        st.subheader("🧠 Latest AI Agent Rationale")
        for log in latest_rationales:
            st.info(log, icon="💡")

# --- PANEL 2: LEADERBOARD & POSITION TRACKER ---
with col2:
    st.subheader("🏆 Agent Performance Leaderboard")
    
    leader_rows = []
    for agent_id, data in agent_db.items():
        trades_used = data.get("trades_today", 0)
        status_badge = f"<span class='badge-locked'>LOCKED ({trades_used}/4)</span>" if trades_used >= 4 else f"<span class='badge-buy'>ACTIVE ({trades_used}/4)</span>"
        
        pos = data.get("current_position")
        pos_info = f"HOLDING <b>{pos['asset']}</b>" if pos else "CASH (100% Free)"
        pnl = float(data.get("total_pnl", 0.0))
        pnl_color = "#00E676" if pnl >= 0 else "#FF5252"
        
        st.markdown(f"""
        <div class="terminal-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 15px; font-weight: bold;">{agent_id.replace('_', ' ')}</span>
                {status_badge}
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 13px;">
                <span style="color: #8B949E;">Position: {pos_info}</span>
                <span style="color: {pnl_color}; font-weight: bold;">PnL: ${pnl:,.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# -------------------------------------------------------------
# 6. INTERACTIVE PERFORMANCE CHART (PLOTLY STUDIO)
# -------------------------------------------------------------
st.subheader("📈 Real-Time Agent Equity Trajectory ($100k Baseline)")

if len(trade_ledger) > 0:
    chart_data = []
    for row in reversed(trade_ledger):
        chart_data.append({
            "Time": row["timestamp"],
            "Agent": row["agent_id"].replace("_", " "),
            "PnL": float(row["pnl"]) + 100000.0
        })
    
    df_chart = pd.DataFrame(chart_data)
    fig = go.Figure()
    
    for agent_name in df_chart["Agent"].unique():
        agent_df = df_chart[df_chart["Agent"] == agent_name]
        fig.add_trace(go.Scatter(
            x=agent_df["Time"], y=agent_df["PnL"],
            mode="lines+markers", name=agent_name,
            line=dict(width=3)
        ))
        
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#090C10",
        plot_bgcolor="#161B22",
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
        yaxis=dict(title="Portfolio Value ($)", gridcolor="#30363D"),
        xaxis=dict(gridcolor="#30363D")
    )
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------------
# 7. AUDIT LOG
# -------------------------------------------------------------
st.subheader("📑 Persistent Audit Log (Saved across reboots)")
if len(trade_ledger) > 0:
    ledger_df = pd.DataFrame(trade_ledger)[["timestamp", "agent_id", "asset", "action", "size", "price", "pnl", "trade_num"]]
    ledger_df.columns = ["Timestamp", "Agent", "Asset", "Action", "Units", "Price ($)", "Realized PnL ($)", "Trade #/4"]
    st.dataframe(ledger_df, use_container_width=True, hide_index=True)
