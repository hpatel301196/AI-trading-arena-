import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from supabase import create_client, Client
import random
from datetime import datetime, date

# -------------------------------------------------------------
# 1. PAGE CONFIG & HIGH-CONTRAST DARK THEME
# -------------------------------------------------------------
st.set_page_config(page_title="AI Trading Arena", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    .main { background-color: #0E1117; }
    h1, h2, h3, h4, label, span { color: #FFFFFF !important; }
    .stMetric { background: #181C27; border: 1px solid #2B313F; border-radius: 8px; padding: 12px; }
    .stMetric label { color: #9A9FA8 !important; font-size: 14px; }
    .stMetric div { color: #FFFFFF !important; font-weight: bold; }
    .card-box { background-color: #181C27; border: 1px solid #2B313F; border-radius: 8px; padding: 15px; margin-bottom: 10px; }
    .badge-buy { background-color: #00E676; color: #000000; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-sell { background-color: #FF5252; color: #FFFFFF; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-hold { background-color: #454B54; color: #FFFFFF; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-lock { background-color: #FFB300; color: #000000; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 60-second auto-refresh
count = st_autorefresh(interval=60000, limit=10000, key="auto_refresh")

# Initialize Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_supabase()

# -------------------------------------------------------------
# 2. PERSISTENT DATABASE ENGINE
# -------------------------------------------------------------
def load_db_state():
    response = supabase.table("agent_portfolio").select("*").execute()
    agents = {row["agent_id"]: row for row in response.data}
    
    # Auto-reset daily trade count if new calendar day
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
    response = supabase.table("trade_ledger_history").select("*").order("id", desc=True).limit(50).execute()
    return response.data

# -------------------------------------------------------------
# 3. MARKET DATA INGESTION
# -------------------------------------------------------------
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

# Header Metrics
st.title("⚡ Autonomous AI Multi-Agent Trading Arena")
st.caption(f"Persistent Supabase Engine | Cycle #{count} | {datetime.now().strftime('%H:%M:%S UTC')}")

cols = st.columns(4)
for i, (asset, price) in enumerate(live_prices.items()):
    cols[i].metric(label=f"{asset}", value=f"${price:,.2f}")

st.divider()

# -------------------------------------------------------------
# 4. TRADING EXECUTION ENGINE (4 TRADES/DAY & CAPITAL LOCKING)
# -------------------------------------------------------------
def process_trading_cycle():
    asset_votes = {asset: {"BUY": 0, "SELL": 0, "HOLD": 0} for asset in live_prices.keys()}
    
    for agent_id, data in agent_db.items():
        trades_today = data.get("trades_today", 0)
        current_pos = data.get("current_position") # dict or None
        cash = float(data.get("cash", 100000.0))
        total_pnl = float(data.get("total_pnl", 0.0))
        
        # Max 4 Trades/Day Enforcement
        if trades_today >= 4:
            continue
            
        # Decision Matrix
        target_asset = random.choice(list(live_prices.keys()))
        market_price = live_prices[target_asset]
        
        # --- RULE 1: IF NO POSITION -> CAN ONLY BUY OR HOLD ---
        if current_pos is None:
            # 85% chance HOLD, 15% chance BUY
            decision = "BUY" if random.random() > 0.85 else "HOLD"
            asset_votes[target_asset][decision] += 1
            
            if decision == "BUY":
                # Lock entire cash capital into target asset
                units = round((cash * 0.99) / market_price, 4)
                new_pos = {"asset": target_asset, "entry_price": market_price, "units": units}
                
                # Update Supabase
                supabase.table("agent_portfolio").update({
                    "cash": 0.0,
                    "current_position": new_pos,
                    "trades_today": trades_today + 1
                }).eq("agent_id", agent_id).execute()
                
                # Log Trade
                supabase.table("trade_ledger_history").insert({
                    "agent_id": agent_id, "asset": target_asset, "action": "BUY",
                    "size": units, "price": market_price, "pnl": 0.0, "trade_num": trades_today + 1
                }).execute()
                
        # --- RULE 2: IF HOLDING A POSITION -> CAN ONLY SELL OR HOLD ---
        else:
            held_asset = current_pos["asset"]
            held_price = current_pos["entry_price"]
            held_units = current_pos["units"]
            current_mkt_price = live_prices[held_asset]
            
            # 80% chance HOLD, 20% chance SELL
            decision = "SELL" if random.random() > 0.80 else "HOLD"
            asset_votes[held_asset][decision] += 1
            
            if decision == "SELL":
                gross_proceeds = held_units * current_mkt_price
                fee = gross_proceeds * 0.001
                net_cash = round(gross_proceeds - fee, 2)
                realized_pnl = round(net_cash - 100000.0, 2) # Track against base capital
                
                # Update Supabase -> Position Cleared
                supabase.table("agent_portfolio").update({
                    "cash": net_cash,
                    "current_position": None,
                    "trades_today": trades_today + 1,
                    "total_pnl": realized_pnl
                }).eq("agent_id", agent_id).execute()
                
                # Log Trade
                supabase.table("trade_ledger_history").insert({
                    "agent_id": agent_id, "asset": held_asset, "action": "SELL",
                    "size": held_units, "price": current_mkt_price, "pnl": realized_pnl, "trade_num": trades_today + 1
                }).execute()

    return asset_votes

asset_consensus = process_trading_cycle()

# Reload fresh state after processing cycle
agent_db = load_db_state()
trade_ledger = load_trade_ledger()

# -------------------------------------------------------------
# 5. DASHBOARD LAYOUT
# -------------------------------------------------------------
col1, col2 = st.columns([1, 1])

# --- PANEL 1: CONSENSUS SIGNALS ---
with col1:
    st.subheader("🎯 Asset Consensus Signals")
    for asset, votes in asset_consensus.items():
        top_signal = max(votes, key=votes.get)
        badge_class = "badge-buy" if top_signal == "BUY" else ("badge-sell" if top_signal == "SELL" else "badge-hold")
        
        st.markdown(f"""
        <div class="card-box">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 16px; font-weight: bold;">{asset}</span>
                <span class="{badge_class}">{top_signal}</span>
            </div>
            <div style="font-size: 12px; color: #9A9FA8; margin-top: 5px;">
                BUY ({votes['BUY']}) | SELL ({votes['SELL']}) | HOLD ({votes['HOLD']})
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- PANEL 2: LEADERBOARD & POSITION TRACKER ---
with col2:
    st.subheader("🏆 Daily Leaderboard (Persistent)")
    
    leader_rows = []
    for agent_id, data in agent_db.items():
        trades_used = data.get("trades_today", 0)
        status_text = f"LOCKED ({trades_used}/4 Trades)" if trades_used >= 4 else f"ACTIVE ({trades_used}/4 Trades)"
        pos = data.get("current_position")
        pos_text = f"HOLDING {pos['asset']}" if pos else "CASH (100% Free)"
        
        leader_rows.append({
            "Agent": agent_id.replace("_", " "),
            "Trading Status": status_text,
            "Current Capital/Position": pos_text,
            "Realized PnL": f"${float(data.get('total_pnl', 0.0)):,.2f}"
        })
        
    st.dataframe(pd.DataFrame(leader_rows), use_container_width=True, hide_index=True)

st.divider()

# -------------------------------------------------------------
# 6. PERSISTENT TRANSACTION AUDIT LOG
# -------------------------------------------------------------
st.subheader("📑 Database Audit Log (Saved Across Refreshes)")

if len(trade_ledger) > 0:
    ledger_df = pd.DataFrame(trade_ledger)[["timestamp", "agent_id", "asset", "action", "size", "price", "pnl", "trade_num"]]
    ledger_df.columns = ["Timestamp", "Agent", "Asset", "Action", "Position Size", "Price ($)", "Realized PnL ($)", "Trade #/4"]
    
    st.dataframe(ledger_df, use_container_width=True, hide_index=True)
else:
    st.info("No trades executed yet today. Agents are evaluating market conditions...")
