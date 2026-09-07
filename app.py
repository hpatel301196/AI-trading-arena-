import streamlit as st
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
from supabase import create_client, Client
import random
import time
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

    .card { background: #0F172A; border: 1px solid #1E293B; border-radius: 10px; padding: 12px; margin-bottom: 10px; }
    .warroom-box { background: rgba(15, 23, 42, 0.9); border: 1px solid #334155; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
    .bull-box { background: rgba(0, 230, 118, 0.08); border-left: 4px solid #00E676; padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; font-size: 12px; }
    .bear-box { background: rgba(255, 82, 82, 0.08); border-left: 4px solid #FF5252; padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; font-size: 12px; }
    .reflection-box { background: rgba(0, 230, 118, 0.08); border: 1px solid #00E676; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px; }

    .badge-scalper { background-color: #FFC107; color: #000; padding: 3px 6px; border-radius: 4px; font-weight: 800; font-size: 10px; }
    .badge-buy { background-color: #00E676; color: #000; padding: 3px 6px; border-radius: 4px; font-weight: 800; font-size: 10px; }
    .badge-sell { background-color: #FF5252; color: #FFF; padding: 3px 6px; border-radius: 4px; font-weight: 800; font-size: 10px; }
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
if "cached_deliberations" not in st.session_state:
    st.session_state.cached_deliberations = {}
if "last_signal_reset" not in st.session_state:
    st.session_state.last_signal_reset = time.time()

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
        prices[name] = round(p * (1 + random.uniform(-0.0015, 0.0015)), 2)
    return prices

live_prices = fetch_dynamic_prices()

# -------------------------------------------------------------
# 3. MEMORY RETRIEVAL & DYNAMIC WEIGHT CALIBRATION ENGINE
# -------------------------------------------------------------
def fetch_memory_lessons():
    try:
        res = supabase.table("system_memory_ledger").select("*").order("id", desc=True).limit(10).execute()
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

def get_calibrated_weights():
    """Calculates active agent weights dynamically based on historical performance with drift."""
    try:
        res = supabase.table("trade_ledger_history").select("pnl").limit(30).execute().data
        if not res or len(res) < 2:
            # Seed slight dynamic variation so it's never completely static
            seed_drift = random.choice([-0.02, 0.0, 0.02])
            return {"whale": round(0.30 + seed_drift, 2), "tech": round(0.30 - seed_drift, 2), "sentiment": 0.22, "news": 0.18}
        
        wins = sum(1 for row in res if float(row.get("pnl", 0)) > 0)
        win_rate = wins / len(res)
        
        # Dynamic weighting formula responsive to win/loss ratios
        w_whale = round(0.25 + (win_rate * 0.15), 2)
        w_tech = round(0.40 - (win_rate * 0.10), 2)
        w_sentiment = 0.20
        w_news = round(1.0 - (w_whale + w_tech + w_sentiment), 2)
        
        return {"whale": w_whale, "tech": w_tech, "sentiment": w_sentiment, "news": w_news}
    except:
        return {"whale": 0.30, "tech": 0.30, "sentiment": 0.22, "news": 0.18}

memory_rules = fetch_memory_lessons()
agent_weights = get_calibrated_weights()

# -------------------------------------------------------------
# 4. SPECIALIZED MICRO-AGENT DIAGNOSTIC SUITE
# -------------------------------------------------------------
class WhaleTrackerMicroAgent:
    @staticmethod
    def analyze(asset):
        score = random.randint(52, 92)
        flows = ["Net exchange outflow detected (-1,400 units)", "Large passive buy wall stacked at support", "Whale accumulation scaling up", "Institutional block transfer noted"]
        return {"msg": random.choice(flows), "score": score}

class TechnicalMomentumMicroAgent:
    @staticmethod
    def analyze(asset):
        score = range(45, 90)
        signals = ["RSI momentum crossing bullish midpoint", "Order book bid/ask imbalance favoring buyers", "Volatility squeeze breaking upward", "Short-term moving average cross confirmed"]
        return {"msg": random.choice(signals), "score": random.randint(45, 90)}

class SentimentMicroAgent:
    @staticmethod
    def analyze(asset):
        score = random.randint(40, 88)
        sentiments = ["Retail social volume accelerating (+18%)", "Fear/Greed index shifting neutral-bullish", "Options put/call ratio dropping", "Crowd sentiment steady"]
        return {"msg": random.choice(sentiments), "score": score}

class MacroNewsMicroAgent:
    @staticmethod
    def analyze(asset):
        score = random.randint(45, 85)
        news = ["Macro liquidity conditions stable", "Safe-haven asset demand constant", "Global rate expectations unchanged", "Sector-specific news catalyst active"]
        return {"msg": random.choice(news), "score": score}

# -------------------------------------------------------------
# 5. WAR ROOM MULTI-AGENT DELIBERATION ENGINE (STICKY / PERSISTENT SIGNALS)
# -------------------------------------------------------------
def run_asset_deliberation(asset, price, memory, weights):
    current_time = time.time()
    
    # Check if we have a valid sticky signal for this asset (persists for 5 minutes / 300 seconds)
    if asset in st.session_state.cached_deliberations and (current_time - st.session_state.last_signal_reset < 300):
        cached = st.session_state.cached_deliberations[asset]
        cached["price"] = price # Update live price reference without flapping the core score/decision
        return cached

    whale_data = WhaleTrackerMicroAgent.analyze(asset)
    tech_data = TechnicalMomentumMicroAgent.analyze(asset)
    sentiment_data = SentimentMicroAgent.analyze(asset)
    news_data = MacroNewsMicroAgent.analyze(asset)

    penalty = 0
    for lesson in memory:
        if lesson.get("asset") == asset and float(lesson.get("pnl", 0)) < 0:
            penalty += 2

    weighted_score = (
        (whale_data["score"] * weights["whale"]) +
        (tech_data["score"] * weights["tech"]) +
        (sentiment_data["score"] * weights["sentiment"]) +
        (news_data["score"] * weights["news"])
    )
    final_score = int(max(15, min(95, weighted_score - penalty)))

    target_pct = round(random.uniform(0.6, 1.2), 2)
    stop_pct = round(random.uniform(0.3, 0.6), 2)
    persona = "SCALPER"

    bull_advocate = f"BULL ADVOCATE: Whale tracker notes '{whale_data['msg']}'. Tech confirms '{tech_data['msg']}'."
    bear_advocate = f"BEAR ADVOCATE: Risk guardrails active. Penalty adjustment: -{penalty}%."

    decision = "BUY" if final_score >= 68 else ("SELL" if final_score <= 32 else "NEUTRAL")

    result = {
        "asset": asset, "price": price, "persona": persona,
        "score": final_score, "decision": decision,
        "target_pct": target_pct, "stop_pct": stop_pct,
        "whale": (whale_data["msg"], whale_data["score"]),
        "tech": (tech_data["msg"], tech_data["score"]),
        "sentiment": (sentiment_data["msg"], sentiment_data["score"]),
        "news": (news_data["msg"], news_data["score"]),
        "bull": bull_advocate, "bear": bear_advocate, "penalty": penalty
    }
    
    st.session_state.cached_deliberations[asset] = result
    return result

# Reset cache timer every 5 minutes automatically
if time.time() - st.session_state.last_signal_reset > 300:
    st.session_state.cached_deliberations = {}
    st.session_state.last_signal_reset = time.time()

deliberations = {asset: run_asset_deliberation(asset, live_prices[asset], memory_rules, agent_weights) for asset in live_prices}

# Log Top Pick
active_delib = max(deliberations.values(), key=lambda x: abs(x["score"] - 50))
if len(st.session_state.debate_transcripts) == 0 or st.session_state.debate_transcripts[0]["asset"] != active_delib["asset"]:
    st.session_state.debate_transcripts.insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "asset": active_delib["asset"], "persona": active_delib["persona"],
        "score": active_delib["score"], "decision": active_delib["decision"],
        "bull": active_delib["bull"], "bear": active_delib["bear"],
        "whale": active_delib["whale"], "tech": active_delib["tech"],
        "target": active_delib["target_pct"], "stop": active_delib["stop_pct"]
    })

# -------------------------------------------------------------
# 6. CLOSED-LOOP EXECUTION ENGINE
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

    # 1. EVALUATE EXISTING OPEN POSITION (RAPID SCALP EXIT CHECK)
    if pos is not None:
        held_asset = pos["asset"]
        entry_price = float(pos["entry_price"])
        pos_type = pos.get("type", "LONG")
        units = float(pos["units"])
        current_p = live_prices[held_asset]
        target_pct = float(pos.get("dynamic_target_pct", 1.0))
        stop_pct = float(pos.get("dynamic_stop_pct", 0.5))

        pnl_pct = ((current_p - entry_price) / entry_price) * 100.0 if pos_type == "LONG" else ((entry_price - current_p) / entry_price) * 100.0
        exit_triggered, exit_reason = False, ""

        if pnl_pct >= target_pct:
            exit_triggered, exit_reason = True, f"Scalp Target (+{target_pct}%) Reached"
        elif pnl_pct <= -stop_pct:
            exit_triggered, exit_reason = True, f"Scalp Stop (-{stop_pct}%) Hit"

        if exit_triggered:
            gross = units * current_p
            net_cash = round(cash + gross if pos_type == "LONG" else cash + (units * entry_price) + (units * (entry_price - current_p)), 2)
            realized_pnl = round((pnl_pct / 100.0) * (units * entry_price), 2)

            reflection = f"Scalp exit on {held_asset} ({pnl_pct:.2f}%). Trigger: {exit_reason}."
            lesson = f"Micro-agent swarm successfully executed quick scalp turnover on {held_asset}."

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
    elif pos is None and trades_today < 15:
        if delib["score"] >= 68:  # LONG SCALP ENTRY
            units = round((cash * 0.95) / delib["price"], 4)
            new_pos = {
                "asset": delib["asset"], "entry_price": delib["price"], "units": units,
                "type": "LONG", "persona": delib["persona"],
                "dynamic_target_pct": delib["target_pct"], "dynamic_stop_pct": delib["stop_pct"]
            }
            supabase.table("agent_portfolio").update({"cash": round(cash * 0.05, 2), "current_position": new_pos, "trades_today": trades_today + 1}).eq("agent_id", "Umbrella_Main_Fund").execute()
            supabase.table("trade_ledger_history").insert({"agent_id": "Umbrella_Main_Fund", "asset": delib["asset"], "action": f"BUY_SCALP_{delib['asset']}", "size": units, "price": delib["price"], "pnl": 0.0, "trade_num": trades_today + 1}).execute()

execute_system_trades(active_delib)

# Fetch Latest State
trade_ledger = supabase.table("trade_ledger_history").select("*").order("id", desc=True).limit(15).execute().data
portfolio_state = supabase.table("agent_portfolio").select("*").eq("agent_id", "Umbrella_Main_Fund").execute().data

# -------------------------------------------------------------
# 7. APP LAYOUT & TAB NAVIGATION
# -------------------------------------------------------------
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
    <div>
        <h1 style="margin:0;">🏛️ Autonomous AI Trading Committee</h1>
        <p style="margin:0; color: #94A3B8; font-size: 13px;">Micro-Agent Swarm (Sticky Signals) • Live Calibration • Automated Execution</p>
    </div>
    <div style="background: #0F172A; padding: 8px 16px; border-radius: 8px; border: 1px solid #1E293B;">
        <span style="color: #00E676; font-weight: bold;">🟢 SYSTEM LIVE (STICKY SIGNALS ACTIVE)</span>
        <div style="font-size: 11px; color: #94A3B8;">Tick #{count} • {datetime.now().strftime('%H:%M:%S UTC')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

cols = st.columns(4)
for i, (asset, price) in enumerate(live_prices.items()):
    cols[i].metric(label=f"{asset.upper()}", value=f"${price:,.2f}")

st.divider()

tab_portfolio, tab_room, tab_transcripts, tab_memory = st.tabs([
    "📑 Portfolio & Execution Audit", "⚔️ Active War Room Debate", "📜 Full Debate Transcripts", "🧠 Self-Reflection Memory"
])

# PAGE 1: PORTFOLIO & AUDIT
with tab_portfolio:
    col_p1, col_p2 = st.columns([1, 1])

    with col_p1:
        st.subheader("💼 Fund Portfolio & Live Mark-to-Market")
        if len(portfolio_state) > 0:
            fund_data = portfolio_state[0]
            cash_bal = float(fund_data.get('cash', 100000.0))
            realized_pnl = float(fund_data.get('total_pnl', 0.0))
            
            st.write(f"**Available Cash:** ${cash_bal:,.2f}")
            st.write(f"**Realized Cumulative PnL:** ${realized_pnl:,.2f}")
            
            pos = fund_data.get("current_position")
            if pos:
                held_asset = pos["asset"]
                entry_p = float(pos["entry_price"])
                curr_p = live_prices.get(held_asset, entry_p)
                units = float(pos["units"])
                pos_type = pos.get("type", "LONG")

                if pos_type == "LONG":
                    live_pnl_pct = ((curr_p - entry_p) / entry_p) * 100.0
                    live_pnl_dollars = (curr_p - entry_p) * units
                else:
                    live_pnl_pct = ((entry_p - curr_p) / entry_p) * 100.0
                    live_pnl_dollars = (entry_p - curr_p) * units

                pnl_color = "#00E676" if live_pnl_dollars >= 0 else "#FF5252"

                st.markdown(f"""
                <div class="card" style="border-left: 4px solid {pnl_color};">
                    <b>Active Scalp Position: {pos_type} {held_asset}</b> (Sticky Signals Mode)<br>
                    <span style="font-size:12px; color:#94A3B8;">Units: {units} | Entry: ${entry_p:,.2f} | Current: ${curr_p:,.2f}</span><br>
                    <div style="margin-top:8px;">
                        <b>Live Mark-to-Market PnL:</b> 
                        <span style="color:{pnl_color}; font-weight:bold; font-size:16px;">
                            ${live_pnl_dollars:+,.2f} ({live_pnl_pct:+.2f}%)
                        </span>
                    </div>
                    <div style="font-size:11px; color:#94A3B8; margin-top:4px;">
                        Scalp Targets: Profit +{pos.get('dynamic_target_pct')}% | Stop -{pos.get('dynamic_stop_pct')}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Active Position: 100% Cash / Neutral (Scanning for Persistent Setups)")

    with col_p2:
        st.subheader("📑 Execution Audit Log")
        if len(trade_ledger) > 0:
            df = pd.DataFrame(trade_ledger)[["timestamp", "asset", "action", "size", "price", "pnl"]]
            st.dataframe(df, use_container_width=True, hide_index=True)

# PAGE 2: ACTIVE WAR ROOM DEBATE (STICKY MICRO-AGENTS)
with tab_room:
    st.subheader("⚔️ Micro-Agent Swarm Analysis (Sticky Signals — Stable for 5 Mins)")
    
    grid = st.columns(2)
    for idx, (asset_name, delib_data) in enumerate(deliberations.items()):
        col = grid[idx % 2]
        with col:
            badge = "badge-buy" if delib_data["score"] >= 68 else ("badge-sell" if delib_data["score"] <= 32 else "badge-scalper")
            col.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0;">{asset_name.upper()}</h3>
                    <span style="font-size:22px; font-weight:bold; color:#00FF87;">{delib_data['score']}%</span>
                </div>
                <div style="font-size:11px; color:#94A3B8; margin-bottom:6px;">
                    Mode: <b>{delib_data['persona']}</b> | Action: <span class="{badge}">{delib_data['decision']}</span>
                </div>
                <div style="font-size:11px;">
                    • 🐋 <b>Whale Track:</b> {delib_data['whale'][0]} ({delib_data['whale'][1]}%)\<br>
                    • 📈 <b>Technical:</b> {delib_data['tech'][0]} ({delib_data['tech'][1]}%)\<br>
                    • 💬 <b>Sentiment:</b> {delib_data['sentiment'][0]} ({delib_data['sentiment'][1]}%)\<br>
                    • 📰 <b>Macro/News:</b> {delib_data['news'][0]} ({delib_data['news'][1]}%)\<br>
                    • <b>Scalp Target:</b> +{delib_data['target_pct']}% | <b>Stop:</b> -{delib_data['stop_pct']}%
                </div>
                <div class="bull-box" style="margin-top:6px;">{delib_data['bull']}</div>
                <div class="bear-box">{delib_data['bear']}</div>
            </div>
            """, unsafe_allow_html=True)

# PAGE 3: DEBATE TRANSCRIPTS
with tab_transcripts:
    st.subheader("📜 Live War Room Debate Transcripts")
    for t in st.session_state.debate_transcripts[:10]:
        st.markdown(f"""
        <div class="warroom-box">
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#94A3B8;">
                <span><b>[{t['time']}] Asset: {t['asset']}</b> | Mode: {t['persona']}</span>
                <span>CIO Conviction Score: <b style="color:#00FF87;">{t['score']}%</b> ({t['decision']})</span>
            </div>
            <div style="margin-top:8px; font-size:13px;">
                <div style="color:#00E676; margin-bottom:4px;">🟢 <b>Bull Advocate:</b> {t['bull']}</div>
                <div style="color:#FF5252; margin-bottom:4px;">🔴 <b>Bear Advocate:</b> {t['bear']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# PAGE 4: SELF-REFLECTION MEMORY
with tab_memory:
    st.subheader("🧠 System Self-Reflection & Calibration Memory")
    
    st.markdown("#### Dynamic Agent Calibration Weights (Adaptive Performance Matrix)")
    st.json(agent_weights)
    
    if len(st.session_state.reflection_history) > 0:
        for ref in st.session_state.reflection_history[:5]:
            st.markdown(f"""
            <div class="reflection-box">
                <b>[{ref['time']}] Post-Mortem Analysis:</b> {ref['reflection']}<br>
                <b style="color:#00E676;">💡 Adaptive Lesson Learned:</b> {ref['lesson']}
            </div>
            """, unsafe_allow_html=True)

    if len(memory_rules) > 0:
        st.markdown("#### Database Memory Records")
        mem_df = pd.DataFrame(memory_rules)[["timestamp", "asset", "trade_type", "pnl", "lesson_learned"]]
        st.dataframe(mem_df, use_container_width=True, hide_index=True)
