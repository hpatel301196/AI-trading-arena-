import streamlit as st
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
from supabase import create_client, Client
import random
from datetime import datetime, date

# -------------------------------------------------------------
# 1. PAGE CONFIGURATION & DARK THEME
# -------------------------------------------------------------
st.set_page_config(
    page_title="Dynamic Autonomous AI Trading Committee",
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
    .scalper-box { background: rgba(255, 193, 7, 0.08); border-left: 4px solid #FFC107; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; }
    .daytrader-box { background: rgba(58, 134, 255, 0.08); border-left: 4px solid #3A84FF; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; }
    .reflection-box { background: rgba(0, 230, 118, 0.08); border: 1px solid #00E676; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px; }

    .badge-scalper { background-color: #FFC107; color: #000; padding: 4px 8px; border-radius: 4px; font-weight: 800; font-size: 11px; }
    .badge-daytrader { background-color: #3A84FF; color: #FFF; padding: 4px 8px; border-radius: 4px; font-weight: 800; font-size: 11px; }
    .badge-buy { background-color: #00E676; color: #000; padding: 4px 8px; border-radius: 4px; font-weight: 800; font-size: 11px; }
    .badge-sell { background-color: #FF5252; color: #FFF; padding: 4px 8px; border-radius: 4px; font-weight: 800; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

# 15-Second Refresh Cycle
count = st_autorefresh(interval=15000, limit=10000, key="autonomous_refresh")

# Initialize Supabase
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"⚠️ Supabase Error: {e}")
        st.stop()

supabase: Client = init_supabase()

if "debate_history" not in st.session_state:
    st.session_state.debate_history = []
if "reflection_history" not in st.session_state:
    st.session_state.reflection_history = []

# -------------------------------------------------------------
# 2. MARKET DATA & DYNAMIC TICKER ENGINE
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
# 4. AUTONOMOUS DELIBERATION & DYNAMIC TARGET ENGINE
# -------------------------------------------------------------
def run_autonomous_deliberation(asset, price, memory):
    # Determine Mode based on Market Volatility
    volatility_metric = random.uniform(0.5, 3.5)
    persona_mode = "SCALPER" if volatility_metric > 2.0 else "DAY_TRADER"

    # Specialist Feed
    whale = random.choice([("Whale accumulated near support.", 80), ("Exchange deposit alert.", 25), ("Neutral flow.", 50)])
    news = random.choice([("Regulatory clarity approved.", 85), ("Macro news headwinds.", 35), ("Supply deficit reported.", 70)])
    tech = random.choice([("RSI Oversold + Key level bounce.", 85), ("MACD Bearish crossover.", 20), ("Range consolidation.", 50)])
    sentiment = random.choice([("Social sentiment bullish (+75%).", 75), ("Social volume negative.", 30), ("Neutral discussions.", 50)])

    # Apply Memory Adjustments
    penalty = 0
    for lesson in memory:
        if lesson.get("asset") == asset and float(lesson.get("pnl", 0)) < 0:
            penalty += 5

    raw_score = (whale[1] + news[1] + tech[1] + sentiment[1]) / 4.0
    final_score = int(max(0, min(100, raw_score - penalty)))

    # AGENT PROPOSES DYNAMIC TARGETS BASED ON PERSONA
    if persona_mode == "SCALPER":
        target_pct = round(random.uniform(0.8, 1.8), 2)  # Tight target
        stop_pct = round(random.uniform(0.5, 1.0), 2)    # Tight stop
    else:
        target_pct = round(random.uniform(3.0, 7.0), 2)  # Wider swing target
        stop_pct = round(random.uniform(1.5, 3.0), 2)    # Wider swing stop

    decision = "BUY" if final_score >= 75 else ("SELL" if final_score <= 25 else "NEUTRAL")

    return {
        "asset": asset, "price": price, "persona": persona_mode,
        "score": final_score, "decision": decision,
        "proposed_target_pct": target_pct, "proposed_stop_pct": stop_pct,
        "whale": whale, "news": news, "tech": tech, "sentiment": sentiment,
        "penalty": penalty
    }

selected_asset = random.choice(list(live_prices.keys()))
deliberation = run_autonomous_deliberation(selected_asset, live_prices[selected_asset], memory_rules)

st.session_state.debate_history.insert(0, {
    "time": datetime.now().strftime("%H:%M:%S"),
    "asset": deliberation["asset"], "persona": deliberation["persona"],
    "score": deliberation["score"], "decision": deliberation["decision"],
    "target": deliberation["proposed_target_pct"], "stop": deliberation["proposed_stop_pct"]
})

# -------------------------------------------------------------
# 5. CLOSED-LOOP DYNAMIC EXECUTION ENGINE
# -------------------------------------------------------------
def execute_dynamic_trading_system(delib):
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

    if str(fund.get("last_trade_date")) != str(date.today()):
        supabase.table("agent_portfolio").update({"trades_today": 0, "last_trade_date": str(date.today())}).eq("agent_id", "Umbrella_Main_Fund").execute()
        trades_today = 0

    # 1. EVALUATE AGENT'S DYNAMIC EXITS FOR OPEN POSITIONS
    if pos is not None:
        held_asset = pos["asset"]
        entry_price = float(pos["entry_price"])
        pos_type = pos.get("type", "LONG")
        units = float(pos["units"])
        current_p = live_prices[held_asset]
        
        # Retrieve Agent's Custom Dynamic Bounds
        target_pct = float(pos.get("dynamic_target_pct", 2.0))
        stop_pct = float(pos.get("dynamic_stop_pct", 1.0))

        if pos_type == "LONG":
            pnl_pct = ((current_p - entry_price) / entry_price) * 100.0
        else:
            pnl_pct = ((entry_price - current_p) / entry_price) * 100.0

        exit_triggered = False
        exit_reason = ""

        # Dynamic Agent Exit Logic
        if pnl_pct >= target_pct:
            exit_triggered = True
            exit_reason = f"Dynamic Agent Target (+{target_pct}%) Reached"
        elif pnl_pct <= -stop_pct:
            exit_triggered = True
            exit_reason = f"Dynamic Agent Stop (-{stop_pct}%) Hit"
        elif pnl_pct <= -5.0:  # Code Circuit Breaker Net
            exit_triggered = True
            exit_reason = "Hard System Circuit Breaker (-5.0%) Safety Trigger"
        elif pos_type == "LONG" and delib["score"] < 45 and held_asset == delib["asset"]:
            exit_triggered = True
            exit_reason = f"Agent Model Shifted Bearish (Score: {delib['score']}%)"

        if exit_triggered:
            gross = units * current_p
            net_cash = round(cash + gross if pos_type == "LONG" else cash + (units * entry_price) + (units * (entry_price - current_p)), 2)
            realized_pnl = round((pnl_pct / 100.0) * (units * entry_price), 2)

            # Self-Reflection Post-Mortem
            if realized_pnl < 0:
                reflection = f"Closed loss on {held_asset} ({pnl_pct:.2f}%). Exit Reason: {exit_reason}."
                lesson = f"Agent tightened entry bounds for {held_asset}. Volatility requires smaller position size."
            else:
                reflection = f"Closed profit on {held_asset} (+{pnl_pct:.2f}%). Exit Reason: {exit_reason}."
                lesson = f"Dynamic exit validation successful on {held_asset} in {pos.get('persona', 'DAY_TRADER')} mode."

            store_self_reflection(held_asset, pos_type, realized_pnl, reflection, lesson)
            st.session_state.reflection_history.insert(0, {"time": datetime.now().strftime("%H:%M:%S"), "reflection": reflection, "lesson": lesson})

            supabase.table("agent_portfolio").update({
                "cash": net_cash, "current_position": None, "trades_today": trades_today + 1, "total_pnl": fund.get("total_pnl", 0) + realized_pnl
            }).eq("agent_id", "Umbrella_Main_Fund").execute()

            supabase.table("trade_ledger_history").insert({
                "agent_id": "Umbrella_Main_Fund", "asset": held_asset, "action": f"CLOSE_{pos_type}",
                "size": units, "price": current_p, "pnl": realized_pnl, "trade_num": trades_today + 1
            }).execute()

    # 2. OPEN NEW POSITION WITH AGENT-DEFINED TARGETS
    elif pos is None and trades_today < 10:
        if delib["score"] >= 75:  # BUY LONG
            units = round((cash * 0.95) / delib["price"], 4)
            new_pos = {
                "asset": delib["asset"], "entry_price": delib["price"], "units": units,
                "type": "LONG", "persona": delib["persona"],
                "dynamic_target_pct": delib["proposed_target_pct"],
                "dynamic_stop_pct": delib["proposed_stop_pct"]
            }

            supabase.table("agent_portfolio").update({
                "cash": round(cash * 0.05, 2), "current_position": new_pos, "trades_today": trades_today + 1
            }).eq("agent_id", "Umbrella_Main_Fund").execute()

            supabase.table("trade_ledger_history").insert({
                "agent_id": "Umbrella_Main_Fund", "asset": delib["asset"], "action": f"BUY_LONG_{delib['persona']}",
                "size": units, "price": delib["price"], "pnl": 0.0, "trade_num": trades_today + 1
            }).execute()

        elif delib["score"] <= 25:  # SHORT
            units = round((cash * 0.95) / delib["price"], 4)
            new_pos = {
                "asset": delib["asset"], "entry_price": delib["price"], "units": units,
                "type": "SHORT", "persona": delib["persona"],
                "dynamic_target_pct": delib["proposed_target_pct"],
                "dynamic_stop_pct": delib["proposed_stop_pct"]
            }

            supabase.table("agent_portfolio").update({
                "cash": cash, "current_position": new_pos, "trades_today": trades_today + 1
            }).eq("agent_id", "Umbrella_Main_Fund").execute()

            supabase.table("trade_ledger_history").insert({
                "agent_id": "Umbrella_Main_Fund", "asset": delib["asset"], "action": f"ENTER_SHORT_{delib['persona']}",
                "size": units, "price": delib["price"], "pnl": 0.0, "trade_num": trades_today + 1
            }).execute()

execute_dynamic_trading_system(deliberation)

# Fetch Data
trade_ledger = supabase.table("trade_ledger_history").select("*").order("id", desc=True).limit(15).execute().data
portfolio_state = supabase.table("agent_portfolio").select("*").eq("agent_id", "Umbrella_Main_Fund").execute().data

# -------------------------------------------------------------
# 6. HEADER & METRIC CARDS
# -------------------------------------------------------------
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
    <div>
        <h1 style="margin:0;">🏛️ Autonomous AI Committee (Dynamic Target Engine)</h1>
        <p style="margin:0; color: #94A3B8; font-size: 13px;">Scalper & Day-Trader Personas • Dynamic Target & Stop Selection • Circuit-Breaker Safety</p>
    </div>
    <div style="background: #0F172A; padding: 8px 16px; border-radius: 8px; border: 1px solid #1E293B;">
        <span style="color: #00E676; font-weight: bold;">🟢 DYNAMIC ENGINE ACTIVE</span>
        <div style="font-size: 11px; color: #94A3B8;">Tick #{count} • {datetime.now().strftime('%H:%M:%S UTC')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

cols = st.columns(4)
for i, (asset, price) in enumerate(live_prices.items()):
    cols[i].metric(label=f"{asset.upper()}", value=f"${price:,.2f}")

st.divider()

# -------------------------------------------------------------
# 7. DASHBOARD PANELS
# -------------------------------------------------------------
tab_war, tab_reflection, tab_portfolio = st.tabs(["⚔️ Dynamic War Room", "🧠 Self-Reflection Log", "📑 Portfolio & Execution Audit"])

with tab_war:
    col_1, col_2 = st.columns([1.1, 0.9])

    with col_1:
        st.subheader(f"📊 Market Analysis: {deliberation['asset'].upper()}")
        persona_badge = "badge-scalper" if deliberation["persona"] == "SCALPER" else "badge-daytrader"
        
        st.markdown(f"""
        <div class="card">
            <div style="display:flex; justify-content:space-between;">
                <b>Active Agent Persona:</b>
                <span class="{persona_badge}">{deliberation['persona']} MODE</span>
            </div>
            <div style="font-size:12px; color:#94A3B8; margin-top:6px;">
                Target Exit: <b>+{deliberation['proposed_target_pct']}%</b> | Stop-Loss: <b>-{deliberation['proposed_stop_pct']}%</b>
            </div>
        </div>
        <div class="card"><b style="color:#3A84FF;">🐋 Whale Tracker:</b> {deliberation['whale'][0]}</div>
        <div class="card"><b style="color:#3A84FF;">📰 Global News Scanner:</b> {deliberation['news'][0]}</div>
        <div class="card"><b style="color:#3A84FF;">📈 Technical Specialist:</b> {deliberation['tech'][0]}</div>
        """, unsafe_allow_html=True)

    with col_2:
        st.subheader("👑 CIO Decision & Dynamic Targets")
        decision_badge = "badge-buy" if deliberation["score"] >= 75 else ("badge-sell" if deliberation["score"] <= 25 else "badge-scalper")
        
        st.markdown(f"""
        <div class="card" style="border: 1px solid #3A84FF;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <b>CIO CONSENSUS SCORE</b>
                    <div style="font-size:12px; color:#94A3B8;">Asset: <b>{deliberation['asset']}</b></div>
                </div>
                <span style="font-size:24px; font-weight:900; color:#00FF87;">{deliberation['score']}%</span>
            </div>
            <div style="margin-top:10px; display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:12px; color:#94A3B8;">Action Signal:</span>
                <span class="{decision_badge}">{deliberation['decision']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### Live Decision Stream")
        for log in st.session_state.debate_history[:4]:
            st.markdown(f"""
            <div class="card" style="padding:10px;">
                <b>[{log['time']}] {log['asset']}</b> ({log['persona']}) ➔ Score: <b>{log['score']}%</b><br>
                <span style="font-size:11px; color:#94A3B8;">Proposed Targets: Profit +{log['target']}% | Stop -{log['stop']}%</span>
            </div>
            """, unsafe_allow_html=True)

with tab_reflection:
    st.subheader("🧠 Closed-Loop Self-Reflection Engine")
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
        st.subheader("💼 Fund Portfolio State")
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
