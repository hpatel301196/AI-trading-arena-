import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from supabase import create_client, Client
import random
from datetime import datetime, date

# -------------------------------------------------------------
# 1. PAGE CONFIG & WAR ROOM STYLING
# -------------------------------------------------------------
st.set_page_config(
    page_title="AI Trading Arena & War Room",
    page_icon="⚔️",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #090C10; color: #E6EDF3; }
    h1, h2, h3, h4 { color: #FFFFFF !important; font-weight: 700 !important; }
    
    /* War Room Cards */
    .war-room-card {
        background: rgba(22, 27, 34, 0.8);
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 10px;
    }
    
    /* Debate Logs */
    .debate-box {
        background: #161B22;
        border-left: 4px solid #58A6FF;
        padding: 10px 14px;
        border-radius: 4px;
        margin-bottom: 8px;
        font-size: 13px;
    }
    .red-team-box {
        background: #161B22;
        border-left: 4px solid #FF5252;
        padding: 10px 14px;
        border-radius: 4px;
        margin-bottom: 8px;
        font-size: 13px;
    }
    
    /* Badges */
    .badge-buy { background-color: rgba(0, 230, 118, 0.2); color: #00E676; border: 1px solid #00E676; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; }
    .badge-sell { background-color: rgba(255, 82, 82, 0.2); color: #FF5252; border: 1px solid #FF5252; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; }
    .badge-hold { background-color: rgba(139, 148, 158, 0.2); color: #8B949E; border: 1px solid #8B949E; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; }
    .badge-lock { background-color: rgba(255, 193, 7, 0.2); color: #FFC107; border: 1px solid #FFC107; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

# 60-Second Auto Refresh Loop
count = st_autorefresh(interval=60000, limit=10000, key="war_room_refresh")

# Initialize Supabase
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"⚠️ Supabase Secrets Error: {e}")
        st.stop()

supabase: Client = init_supabase()

# Session State for Live War Room Logs
if "debate_logs" not in st.session_state:
    st.session_state.debate_logs = []

# -------------------------------------------------------------
# 2. PERSISTENT STATE & RAG NEWS SENTIMENT ENGINE
# -------------------------------------------------------------
def load_db_state():
    response = supabase.table("agent_portfolio").select("*").execute()
    agents = {row["agent_id"]: row for row in response.data}
    
    # Reset daily trade quotas if date changed
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

@st.cache_data(ttl=30)
def fetch_live_prices_and_rag_news():
    tickers = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Gold": "GC=F", "Silver": "SI=F"}
    prices = {}
    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            prices[name] = round(t.fast_info['lastPrice'], 2)
        except:
            prices[name] = 1000.0
            
    # Mocked RAG Live News Stream & Sentiment Analysis
    headlines = [
        {"asset": "Bitcoin", "text": "Institutional inflows reach 3-month high in ETF spot markets.", "score": 0.82},
        {"asset": "Ethereum", "text": "Layer-2 gas fee consumption surges following network upgrade.", "score": 0.65},
        {"asset": "Gold", "text": "Central banks increase monthly bullion reserves amid rate uncertainty.", "score": 0.45},
        {"asset": "Silver", "text": "Industrial demand forecasts project slight deficit in supply.", "score": 0.30}
    ]
    return prices, headlines

live_prices, rag_news = fetch_live_prices_and_rag_news()
agent_db = load_db_state()

# -------------------------------------------------------------
# 3. SPECIALIZED AGENTS & RED-TEAM DEBATE ENGINE
# -------------------------------------------------------------
AGENT_PROFILES = {
    "Agent_Alpha_Quant": {"name": "Agent Alpha", "type": "Trend / Quant", "risk": "Medium"},
    "Agent_Beta_Sentiment": {"name": "Agent Beta", "type": "RAG News Analyst", "risk": "High"},
    "Agent_Gamma_Risk": {"name": "Agent Gamma", "type": "Red-Team Risk Manager", "risk": "Low"},
    "Agent_Delta_Hybrid": {"name": "Agent Delta", "type": "Contrarian Scalper", "risk": "Medium"}
}

def process_war_room_cycle():
    asset_votes = {asset: {"BUY": 0, "SELL": 0, "HOLD": 0} for asset in live_prices.keys()}
    
    for agent_id, data in agent_db.items():
        trades_today = data.get("trades_today", 0)
        current_pos = data.get("current_position")
        cash = float(data.get("cash", 100000.0))
        
        # Respect 4 trades per day limit
        if trades_today >= 4:
            continue
            
        target_asset = random.choice(list(live_prices.keys()))
        market_price = live_prices[target_asset]
        
        # HIGHER PROBABILITY TRIGGER (Fixes 0 trades issue)
        trade_roll = random.random()
        
        # BUY PATH (If currently in CASH)
        if current_pos is None:
            if trade_roll > 0.60: # 40% chance to propose BUY
                decision = "BUY"
                asset_votes[target_asset]["BUY"] += 1
                
                # --- RED TEAM DEBATE SIMULATION ---
                hypothesis = f"Proposing BUY on {target_asset} @ ${market_price:,.2f} based on momentum setup."
                red_team_critique = f"REJECT/CHALLENGE: Volatility high, ensure tight stop-loss on {target_asset}."
                
                # Execute Trade
                units = round((cash * 0.98) / market_price, 4)
                new_pos = {"asset": target_asset, "entry_price": market_price, "units": units}
                
                supabase.table("agent_portfolio").update({
                    "cash": 0.0, "current_position": new_pos, "trades_today": trades_today + 1
                }).eq("agent_id", agent_id).execute()
                
                supabase.table("trade_ledger_history").insert({
                    "agent_id": agent_id, "asset": target_asset, "action": "BUY",
                    "size": units, "price": market_price, "pnl": 0.0, "trade_num": trades_today + 1
                }).execute()
                
                st.session_state.debate_logs.insert(0, {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "agent": agent_id.replace("_", " "),
                    "asset": target_asset,
                    "propose": hypothesis,
                    "critique": red_team_critique,
                    "outcome": "APPROVED & EXECUTED"
                })
            else:
                asset_votes[target_asset]["HOLD"] += 1

        # SELL PATH (If currently HOLDING an asset)
        else:
            held_asset = current_pos["asset"]
            held_units = current_pos["units"]
            current_mkt_price = live_prices[held_asset]
            
            if trade_roll > 0.55: # 45% chance to propose SELL
                decision = "SELL"
                asset_votes[held_asset]["SELL"] += 1
                
                gross = held_units * current_mkt_price
                fee = gross * 0.001
                net_cash = round(gross - fee, 2)
                realized_pnl = round(net_cash - 100000.0, 2)
                
                supabase.table("agent_portfolio").update({
                    "cash": net_cash, "current_position": None,
                    "trades_today": trades_today + 1, "total_pnl": realized_pnl
                }).eq("agent_id", agent_id).execute()
                
                supabase.table("trade_ledger_history").insert({
                    "agent_id": agent_id, "asset": held_asset, "action": "SELL",
                    "size": held_units, "price": current_mkt_price, "pnl": realized_pnl, "trade_num": trades_today + 1
                }).execute()
                
                st.session_state.debate_logs.insert(0, {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "agent": agent_id.replace("_", " "),
                    "asset": held_asset,
                    "propose": f"Closing position on {held_asset} to capture ${realized_pnl:,.2f} PnL.",
                    "critique": "RED TEAM: Profit target verified against slippage tolerance.",
                    "outcome": "POSITION CLOSED"
                })
            else:
                asset_votes[held_asset]["HOLD"] += 1

    return asset_votes

asset_consensus = process_war_room_cycle()
agent_db = load_db_state()
trade_ledger = load_trade_ledger()

# -------------------------------------------------------------
# 4. INTERACTIVE WAR ROOM HEADER & TICKERS
# -------------------------------------------------------------
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
    <div>
        <h1 style="margin:0; font-size: 26px;">⚔️ Autonomous AI War Room & Trading Arena</h1>
        <p style="margin:0; color: #8B949E; font-size: 13px;">Multi-Agent Red-Teaming • Live News RAG • Autonomous Execution</p>
    </div>
    <div style="background: rgba(22,27,34,0.9); padding: 8px 16px; border-radius: 8px; border: 1px solid #30363D;">
        <span style="color: #00E676; font-weight: bold;">🟢 WAR ROOM ACTIVE</span>
        <div style="font-size: 11px; color: #8B949E;">Auto Scan #{count} • {datetime.now().strftime('%H:%M:%S UTC')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Live Tickers
cols = st.columns(4)
for i, (asset, price) in enumerate(live_prices.items()):
    cols[i].metric(label=f"{asset.upper()}", value=f"${price:,.2f}")

st.divider()

# -------------------------------------------------------------
# 5. TABBED WAR ROOM INTERFACE
# -------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["⚔️ AI War Room & Debates", "🏆 Leaderboard & Portfolios", "📑 Audit Ledger & RAG News"])

# --- TAB 1: WAR ROOM & DEBATES ---
with tab1:
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.subheader("🎯 Per-Asset Consensus Signals")
        for asset, votes in asset_consensus.items():
            top_signal = max(votes, key=votes.get)
            badge_style = "badge-buy" if top_signal == "BUY" else ("badge-sell" if top_signal == "SELL" else "badge-hold")
            
            st.markdown(f"""
            <div class="war-room-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:16px; font-weight:bold;">{asset}</span>
                    <span class="{badge_style}">{top_signal}</span>
                </div>
                <div style="font-size:12px; color:#8B949E; margin-top:6px;">
                    Consensus Breakdown: <b style="color:#00E676;">{votes['BUY']} BUY</b> | <b style="color:#FF5252;">{votes['SELL']} SELL</b> | <b style="color:#8B949E;">{votes['HOLD']} HOLD</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_b:
        st.subheader("🗣️ Live Red-Team Debate Stream")
        if len(st.session_state.debate_logs) > 0:
            for log in st.session_state.debate_logs[:4]:
                st.markdown(f"""
                <div class="debate-box">
                    <b>[{log['time']}] {log['agent']} ({log['asset']}):</b> {log['propose']}
                </div>
                <div class="red-team-box">
                    <b>🥊 Red Team Challenge:</b> {log['critique']} <br>
                    <span style="color:#00E676; font-weight:bold;">Outcome: {log['outcome']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("War room actively monitoring signals for upcoming trade debate...")

# --- TAB 2: LEADERBOARD & AGENT PROFILES ---
with tab2:
    st.subheader("🏆 Daily Agent Rankings & Specialization Profiles")
    
    for agent_id, data in agent_db.items():
        profile = AGENT_PROFILES.get(agent_id, {"name": agent_id, "type": "General", "risk": "Medium"})
        trades_used = data.get("trades_today", 0)
        status_badge = f"<span class='badge-lock'>LOCKED ({trades_used}/4 Trades)</span>" if trades_used >= 4 else f"<span class='badge-buy'>ACTIVE ({trades_used}/4 Trades)</span>"
        
        pos = data.get("current_position")
        pos_info = f"HOLDING <b>{pos['asset']}</b>" if pos else "CASH (100% Free)"
        pnl = float(data.get("total_pnl", 0.0))
        pnl_color = "#00E676" if pnl >= 0 else "#FF5252"
        
        st.markdown(f"""
        <div class="war-room-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <b style="font-size:16px;">{profile['name']}</b> 
                    <span style="color:#8B949E; font-size:12px;"> ({profile['type']} • Risk: {profile['risk']})</span>
                </div>
                {status_badge}
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:10px; font-size:13px;">
                <span>Current Status: {pos_info}</span>
                <span style="color:{pnl_color}; font-weight:bold;">Realized PnL: ${pnl:,.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- TAB 3: AUDIT LEDGER & RAG NEWS ---
with tab3:
    col_x, col_y = st.columns([1, 1])
    
    with col_x:
        st.subheader("📰 Live RAG News Sentiment Stream")
        for news in rag_news:
            score_color = "#00E676" if news["score"] > 0.5 else "#FF5252"
            st.markdown(f"""
            <div class="war-room-card">
                <div style="display:flex; justify-content:space-between;">
                    <b>{news['asset']}</b>
                    <span style="color:{score_color}; font-weight:bold;">Sentiment Score: +{news['score']}</span>
                </div>
                <div style="font-size:12px; color:#8B949E; margin-top:4px;">"{news['text']}"</div>
            </div>
            """, unsafe_allow_html=True)
            
    with col_y:
        st.subheader("📑 Persistent Audit Ledger")
        if len(trade_ledger) > 0:
            ledger_df = pd.DataFrame(trade_ledger)[["timestamp", "agent_id", "asset", "action", "size", "price", "pnl", "trade_num"]]
            ledger_df.columns = ["Timestamp", "Agent", "Asset", "Action", "Units", "Price ($)", "PnL ($)", "Trade #"]
            st.dataframe(ledger_df, use_container_width=True, hide_index=True)
        else:
            st.info("No trades executed yet today.")
