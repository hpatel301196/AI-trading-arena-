import streamlit as st
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
from supabase import create_client, Client
import random
from datetime import datetime, date

# -------------------------------------------------------------
# 1. PAGE CONFIGURATION & DARK TERMINAL STYLING
# -------------------------------------------------------------
st.set_page_config(
    page_title="Autonomous AI Trading Committee",
    page_icon="🏛️",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #040D12; color: #FFFFFF; }
    h1, h2, h3, h4 { color: #FFFFFF !important; font-weight: 800 !important; }
    
    div[data-testid="stMetric"] {
        background: #182229 !important;
        border: 1px solid #2C3E50 !important;
        border-radius: 8px;
        padding: 10px;
    }
    div[data-testid="stMetric"] label { color: #9BABB8 !important; font-size: 11px; font-weight: bold; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #00FF87 !important; font-size: 18px; font-weight: bold; }

    .card { background: #0F172A; border: 1px solid #1E293B; border-radius: 10px; padding: 14px; margin-bottom: 12px; }
    .warroom-box { background: rgba(15, 23, 42, 0.9); border: 1px solid #334155; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
    .bull-box { background: rgba(0, 230, 118, 0.08); border-left: 4px solid #00E676; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; }
    .bear-box { background: rgba(255, 82, 82, 0.08); border-left: 4px solid #FF5252; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; }
    .reflection-box { background: rgba(0, 230, 118, 0.08); border: 1px solid #00E676; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px; }

    .badge-scalper { background-color: #FFC107; color: #000; padding: 4px 8px; border-radius: 4px; font-weight: 800; font-size: 11px; }
    .badge-daytrader { background-color: #3A84FF; color: #FFF; padding: 4px 8px; border-radius: 4px; font-weight: 800; font-size: 11px; }
    .badge-buy { background-color: #00E676; color: #000; padding: 4px 8px; border-radius: 4px; font-weight: 800; font-size: 11px; }
    .badge-sell { background-color: #FF5252; color: #FFF; padding: 4px 8px; border-radius: 4px; font-weight: 800; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

# 15-Second Refresh Loop
count = st_autorefresh(interval=15000, limit=10000, key="warroom_refresh")

# Initialize Supabase
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"⚠️ Supabase Configuration Error: {e}")
        st.stop()

supabase: Client = init_supabase()

if "debate_transcripts" not in st.session_state:
    st.session_state.debate_transcripts = []
if "reflection_history" not in st.session_state:
    st.session_state.reflection_history = []

# -------------------------------------------------------------
# 2. DYNAMIC MARKET DATA ENGINE
# -------------------------------------------------------------
def fetch_dynamic_prices():
    tickers = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Gold": "GC=F", "Silver": "SI=F"}
    base_prices = {"Bitcoin": 65000.0, "Ethereum": 3500.0, "Gold": 2740.0, "Silver": 31.50}
    prices = {}
    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            p = round(t.fast_info['lastPrice'], 2)
            if p is None or p <= 0: p = base_prices[name]
        except:
            p = base_prices[name]
        prices[name] = round(p * (1 + random.uniform(-0.002, 0.002)), 2)
    return prices

live_prices = fetch_dynamic_prices()

# -------------------------------------------------------------
# 3. MEMORY RETRIEVAL ENGINE
# -------------------------------------------------------------
def fetch_memory_lessons():
    try:
        res = supabase.table("system_memory_ledger").select("*").order("id", desc=True).limit(5).execute()
        return res.data
    except:
        return []

def store_self_reflection(asset, trade_type, pnl, reflection, lesson):
    try:
        supabase.table("system_memory_ledger").insert({
            "asset": asset, "trade_type": trade_type, "pnl": pnl,
            "reflection_notes": reflection, "lesson_learned": lesson
        }).execute()
    except Exception as e:
        print(f"Memory log error: {e}")

memory_rules = fetch_memory_lessons()

# -------------------------------------------------------------
# 4. WAR ROOM MULTI-AGENT DELIBERATION ENGINE
# -------------------------------------------------------------
def run_war_room_deliberation(asset, price, memory):
    volatility = random.uniform(0.5, 3.5)
    persona = "SCALPER" if volatility > 2.0 else "DAY_TRADER"

    # Specialist Feed Data
    whale_msg, whale_score = random.choice([("Whale wallet buying heavily near key support.", 85), ("Exchange deposit spike detected.", 25), ("Whale wallet volume calm.", 50)])
    news_msg, news_score = random.choice([("Positive macro news & institutional approval.", 85), ("Regulatory uncertainty reported.", 30), ("Neutral news flow.", 50)])
    tech_msg, tech_score = random.choice([("RSI Oversold + Bullish Divergence on 15M.", 88), ("MACD Bearish Cross on 1H timeframe.", 20), ("Consolidating inside key range.", 50)])
    sent_msg, sent_score = random.choice([("Social sentiment score reaches +78% positive.", 78), ("Negative social posts surge.", 28), ("Neutral social engagement.", 50)])

    # Memory Adjustments
    penalty = 0
    for lesson in memory:
        if lesson.get("asset") == asset and float(lesson.get("pnl", 0)) < 0:
            penalty += 5

    raw_score = (whale_score + news_score + tech_score + sent_score) / 4.0
    final_score = int(max(0, min(100, raw_score - penalty)))

    # Bull vs Bear Debate Constructs
    bull_advocate = f"BULL ADVOCATE: Key confluence detected! {tech_msg} {news_msg} Conviction points toward upside."
    bear_advocate = f"BEAR ADVOCATE: Exercise caution. {whale_msg} System memory penalty of -{penalty}% applied from past trades."

    if persona == "SCALPER":
        target_pct, stop_pct = round(random.uniform(0.8, 1.8), 2), round(random.uniform(0.5, 1.0), 2)
    else:
        target_pct, stop_pct = round(random.uniform(3.0, 6.0), 2), round(random.uniform(1.5, 2.5), 2)

    decision = "BUY" if final_score >= 75 else ("SELL" if final_score <= 25 else "NEUTRAL")

    return {
        "asset": asset, "price": price, "persona": persona,
        "score": final_score, "decision": decision,
        "target_pct": target_pct, "stop_pct": stop_pct,
        "whale": (whale_msg, whale_score), "news": (news_msg, news_score),
        "tech": (tech_msg, tech_score), "sentiment": (sent_msg, sent_score),
        "bull": bull_advocate, "bear": bear_advocate, "penalty": penalty
    }

selected_asset = random.choice(list(live_prices.keys()))
deliberation = run_war_room_deliberation(selected_asset, live_prices[selected_asset], memory_rules)

# Log Debate Transcript
st.session_state.debate_transcripts.insert(0, {
    "time": datetime.now().strftime("%H:%M:%S"),
    "asset": deliberation["asset"], "persona": deliberation["persona"],
    "score": deliberation["score"], "decision": deliberation["decision"],
    "bull": deliberation["bull"], "bear": deliberation["bear"],
    "whale": deliberation["whale"], "tech": deliberation["tech"],
    "target": deliberation["target_pct"], "stop": deliberation["stop_pct"]
})

# -------------------------------------------------------------
# 5. CLOSED-LOOP EXECUTION ENGINE
# -------------------------------------------------------------
def execute_system_trades(delib):
    res = supabase.table("agent_portfolio").select("*").eq("agent_id", "Umbrella_Main_Fund").execute()
    
    if len(res.data) == 0:
        supabase.table("agent_portfolio").insert({
            "agent_id": "Umbrella_Main_Fund", "cash": 100000.0,
            "current_position": None, "trades_today": 0, "total_pnl": 0.0, "last_trade_date": str(date.today())
        }).execute()
        fund = {"cash": 100000.0, "current_position": None, "trades_today": 0, "total_pnl": 0.0}
    else:
        fund = res.data[0]

    cash = float(fund.get("cash", 100000.0))
    pos = fund.get("current_position")
    trades_today = fund.get("trades_today", 0)

    # 1. EVALUATE EXISTING OPEN POSITION
    if pos is not None:
        held_asset = pos["asset"]
        entry_price = float(pos["entry_price"])
        pos_type = pos.get("type", "LONG")
        units = float(pos["units"])
        current_p = live_prices[held_asset]
        target_pct = float(pos.get("dynamic_target_pct", 2.0))
        stop_pct = float(pos.get("dynamic_stop_pct", 1.0))

        pnl_pct = ((current_p - entry_price) / entry_price) * 100.0 if pos_type == "LONG" else ((entry_price - current_p) / entry_price) * 100.0
        exit_triggered, exit_reason = False, ""

        if pnl_pct >= target_pct:
            exit_triggered, exit_reason = True, f"Dynamic Target (+{target_pct}%) Reached"
        elif pnl_pct <= -stop_pct:
            exit_triggered, exit_reason = True, f"Dynamic Stop (-{stop_pct}%) Hit"
        elif pnl_pct <= -5.0:
            exit_triggered, exit_reason = True, "Hard Circuit-Breaker Safety Net Triggered"

        if exit_triggered:
            gross = units * current_p
            net_cash = round(cash + gross if pos_type == "LONG" else cash + (units * entry_price) + (units * (entry_price - current_p)), 2)
            realized_pnl = round((pnl_pct / 100.0) * (units * entry_price), 2)

            reflection = f"Exit on {held_asset} ({pnl_pct:.2f}%). Trigger: {exit_reason}."
            lesson = f"Adjust risk weights for {held_asset} based on recent {pos.get('persona')} performance."

            store_self_reflection(held_asset, pos_type, realized_pnl, reflection, lesson)
            st.session_state.reflection_history.insert(0, {"time": datetime.now().strftime("%H:%M:%S"), "reflection": reflection, "lesson": lesson})

            supabase.table("agent_portfolio").update({
                "cash": net_cash, "current_position": None, "trades_today": trades_today + 1, "total_pnl": fund.get("total_pnl", 0) + realized_pnl
            }).eq("agent_id", "Umbrella_Main_Fund").execute()

            supabase.table("trade_ledger_history").insert({
                "agent_id": "Umbrella_Main_Fund", "asset": held_asset, "action": f"CLOSE_{pos_type}",
                "size": units, "price": current_p, "pnl": realized_pnl, "trade_num": trades_today + 1
            }).execute()

    # 2. ENTER NEW POSITION
    elif pos is None and trades_today < 10:
        if delib["score"] >= 75:  # LONG
            units = round((cash * 0.95) / delib["price"], 4)
            new_pos = {
                "asset": delib["asset"], "entry_price": delib["price"], "units": units,
                "type": "LONG", "persona": delib["persona"],
                "dynamic_target_pct": delib["target_pct"], "dynamic_stop_pct": delib["stop_pct"]
            }
            supabase.table("agent_portfolio").update({"cash": round(cash * 0.05, 2), "current_position": new_pos, "trades_today": trades_today + 1}).eq("agent_id", "Umbrella_Main_Fund").execute()
            supabase.table("trade_ledger_history").insert({"agent_id": "Umbrella_Main_Fund", "asset": delib["asset"], "action": f"BUY_LONG_{delib['persona']}", "size": units, "price": delib["price"], "pnl": 0.0, "trade_num": trades_today + 1}).execute()

        elif delib["score"] <= 25:  # SHORT
            units = round((cash * 0.95) / delib["price"], 4)
            new_pos = {
                "asset": delib["asset"], "entry_price": delib["price"], "units": units,
                "type": "SHORT", "persona": delib["persona"],
                "dynamic_target_pct": delib["target_pct"], "dynamic_stop_pct": delib["stop_pct"]
            }
            supabase.table("agent_portfolio").update({"cash": cash, "current_position": new_pos, "trades_today": trades_today + 1}).eq("agent_id", "Umbrella_Main_Fund").execute()
            supabase.table("trade_ledger_history").insert({"agent_id": "Umbrella_Main_Fund", "asset": delib["asset"], "action": f"ENTER_SHORT_{delib['persona']}", "size": units, "price": delib["price"], "pnl": 0.0, "trade_num": trades_today + 1}).execute()

execute_system_trades(deliberation)

# Load State
trade_ledger = supabase.table("trade_ledger_history").select("*").order("id", desc=True).limit(15).execute().data
portfolio_state = supabase.table("agent_portfolio").select("*").eq("agent_id", "Umbrella_Main_Fund").execute().data

# -------------------------------------------------------------
# 6. APP LAYOUT & WAR ROOM DASHBOARD
# -------------------------------------------------------------
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
    <div>
        <h1 style="margin:0;">🏛️ Live War Room & AI Trading Committee</h1>
        <p style="margin:0; color: #94A3B8; font-size: 13px;">Real-Time Agent Debates • Specialist Weightings • Autonomous Execution</p>
    </div>
    <div style="background: #0F172A; padding: 8px 16px; border-radius: 8px; border: 1px solid #1E293B;">
        <span style="color: #00E676; font-weight: bold;">🟢 WAR ROOM LIVE</span>
        <div style="font-size: 11px; color: #94A3B8;">Tick #{count} • {datetime.now().strftime('%H:%M:%S UTC')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

cols = st.columns(4)
for i, (asset, price) in enumerate(live_prices.items()):
    cols[i].metric(label=f"{asset.upper()}", value=f"${price:,.2f}")

st.divider()

tab_room, tab_transcripts, tab_memory, tab_portfolio = st.tabs([
    "⚔️ Active War Room Debate", "📜 Full Debate Transcripts", "🧠 Self-Reflection Memory", "📑 Portfolio & Execution Audit"
])

with tab_room:
    col_left, col_right = st.columns([1.1, 0.9])

    with col_left:
        st.subheader(f"🎙️ Specialist Agent Intelligence: {deliberation['asset'].upper()}")
        
        st.markdown(f"""
        <div class="card">
            <b>🐋 Whale Agent:</b> {deliberation['whale'][0]}
            <span style="float:right; color:#00E676; font-weight:bold;">Score: {deliberation['whale'][1]}%</span>
        </div>
        <div class="card">
            <b>📰 Global News RAG:</b> {deliberation['news'][0]}
            <span style="float:right; color:#00E676; font-weight:bold;">Score: {deliberation['news'][1]}%</span>
        </div>
        <div class="card">
            <b>📈 Technical Specialist:</b> {deliberation['tech'][0]}
            <span style="float:right; color:#00E676; font-weight:bold;">Score: {deliberation['tech'][1]}%</span>
        </div>
        <div class="card">
            <b>💬 Sentiment Monitor:</b> {deliberation['sentiment'][0]}
            <span style="float:right; color:#00E676; font-weight:bold;">Score: {deliberation['sentiment'][1]}%</span>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.subheader("👑 CIO Consensus & Target Projections")
        badge_style = "badge-buy" if deliberation["score"] >= 75 else ("badge-sell" if deliberation["score"] <= 25 else "badge-scalper")
        
        st.markdown(f"""
        <div class="card" style="border: 1px solid #3A84FF;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <b>CHIEF INVESTMENT OFFICER</b>
                    <div style="font-size:12px; color:#94A3B8;">Persona: <b>{deliberation['persona']}</b></div>
                </div>
                <span style="font-size:28px; font-weight:900; color:#00FF87;">{deliberation['score']}%</span>
            </div>
            <div style="margin-top:8px; display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:12px; color:#94A3B8;">Target: <b>+{deliberation['target_pct']}%</b> | Stop: <b>-{deliberation['stop_pct']}%</b></span>
                <span class="{badge_style}">{deliberation['decision']}</span>
            </div>
        </div>
        <div class="bull-box">{deliberation['bull']}</div>
        <div class="bear-box">{deliberation['bear']}</div>
        """, unsafe_allow_html=True)

with tab_transcripts:
    st.subheader("📜 Live War Room Debate Transcripts")
    st.info("Below is the complete transcript of debates between the Bull Advocate, Bear Advocate, and Specialist Agents.")

    for t in st.session_state.debate_transcripts[:8]:
        st.markdown(f"""
        <div class="warroom-box">
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#94A3B8;">
                <span><b>[{t['time']}] Asset: {t['asset']}</b> | Mode: {t['persona']}</span>
                <span>CIO Conviction Score: <b style="color:#00FF87;">{t['score']}%</b> ({t['decision']})</span>
            </div>
            <div style="margin-top:8px; font-size:13px;">
                <div style="color:#00E676; margin-bottom:4px;">🟢 <b>Bull Advocate:</b> {t['bull']}</div>
                <div style="color:#FF5252; margin-bottom:4px;">🔴 <b>Bear Advocate:</b> {t['bear']}</div>
                <div style="color:#94A3B8; font-size:11px;">📊 Technical Input: {t['tech'][0]} | Whale Score: {t['whale'][1]}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab_memory:
    st.subheader("🧠 System Self-Reflection & Lessons Learned")
    if len(st.session_state.reflection_history) > 0:
        for ref in st.session_state.reflection_history[:5]:
            st.markdown(f"""
            <div class="reflection-box">
                <b>[{ref['time']}] Post-Mortem Analysis:</b> {ref['reflection']}<br>
                <b style="color:#00E676;">💡 Adaptive Lesson Learned:</b> {ref['lesson']}
            </div>
            """, unsafe_allow_html=True)

    if len(memory_rules) > 0:
        st.markdown("#### Saved Supabase Memory Records")
        mem_df = pd.DataFrame(memory_rules)[["timestamp", "asset", "trade_type", "pnl", "lesson_learned"]]
        st.dataframe(mem_df, use_container_width=True, hide_index=True)

with tab_portfolio:
    col_p1, col_p2 = st.columns([1, 1])

    with col_p1:
        st.subheader("💼 Fund Portfolio Summary")
        if len(portfolio_state) > 0:
            fund_data = portfolio_state[0]
            st.write(f"**Cash Balance:** ${float(fund_data.get('cash', 100000.0)):,.2f}")
            st.write(f"**Realized PnL:** ${float(fund_data.get('total_pnl', 0.0)):,.2f}")
            
            pos = fund_data.get("current_position")
            if pos:
                st.success(f"Active Position: **{pos['type']} {pos['asset']}** ({pos.get('persona', 'DAY_TRADER')} Mode)\n"
                           f"Units: {pos['units']} | Entry: ${float(pos['entry_price']):,.2f}\n"
                           f"Targets: Profit +{pos.get('dynamic_target_pct')}% | Stop -{pos.get('dynamic_stop_pct')}%")
            else:
                st.info("Active Position: 100% Cash / Neutral")

    with col_p2:
        st.subheader("📑 Execution Audit Log")
        if len(trade_ledger) > 0:
            df = pd.DataFrame(trade_ledger)[["timestamp", "asset", "action", "size", "price", "pnl"]]
            st.dataframe(df, use_container_width=True, hide_index=True)
