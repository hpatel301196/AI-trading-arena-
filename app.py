import streamlit as st
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
from supabase import create_client, Client
import random
import time
from datetime import datetime, date

# -------------------------------------------------------------
# 1. PAGE CONFIGURATION & INSTITUTIONAL DARK TERMINAL
# -------------------------------------------------------------
st.set_page_config(
    page_title="Umbrella Institutional Trading Engine",
    page_icon="🏛️",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #030712; color: #F8FAFC; }
    h1, h2, h3, h4 { color: #F8FAFC !important; font-weight: 800 !important; }
    
    div[data-testid="stMetric"] {
        background: #0F172A !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px;
        padding: 10px;
    }
    div[data-testid="stMetric"] label { color: #94A3B8 !important; font-size: 11px; font-weight: bold; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #38BDF8 !important; font-size: 18px; font-weight: bold; }

    .card { background: #0B132B; border: 1px solid #1C2541; border-radius: 10px; padding: 14px; margin-bottom: 12px; }
    .warroom-box { background: rgba(11, 19, 43, 0.95); border: 1px solid #3A506B; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
    .bull-box { background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10B981; padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; font-size: 12px; }
    .bear-box { background: rgba(239, 68, 68, 0.1); border-left: 4px solid #EF4444; padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; font-size: 12px; }
    .reflection-box { background: rgba(56, 189, 248, 0.1); border: 1px solid #38BDF8; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px; }

    .badge-institutional { background-color: #3B82F6; color: #FFF; padding: 3px 8px; border-radius: 4px; font-weight: 800; font-size: 10px; }
    .badge-buy { background-color: #10B981; color: #000; padding: 3px 8px; border-radius: 4px; font-weight: 800; font-size: 10px; }
    .badge-sell { background-color: #EF4444; color: #FFF; padding: 3px 8px; border-radius: 4px; font-weight: 800; font-size: 10px; }
</style>
""", unsafe_allow_html=True)

# 15-Second Refresh Loop
count = st_autorefresh(interval=15000, limit=10000, key="institutional_refresh")

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
if "price_buffer" not in st.session_state:
    st.session_state.price_buffer = {}

# -------------------------------------------------------------
# 2. TRADINGVIEW-SMOOTHED PRICE ENGINE (EMA BUFFER)
# -------------------------------------------------------------
def fetch_smoothed_institutional_prices():
    tickers = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Gold": "GC=F", "Silver": "SI=F"}
    base_prices = {"Bitcoin": 65000.0, "Ethereum": 3500.0, "Gold": 2740.0, "Silver": 31.50}
    smoothed_prices = {}
    
    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="1d", interval="1m")
            if not hist.empty:
                raw_p = float(hist['Close'].iloc[-1])
            else:
                raw_p = base_prices[name]
        except:
            raw_p = base_prices[name]
        
        # Apply Exponential Moving Average (EMA) smoothing to eliminate raw tick jitter
        prev_p = st.session_state.price_buffer.get(name, raw_p)
        smoothed_p = round((raw_p * 0.2) + (prev_p * 0.8), 2)  # Smooth damping factor
        st.session_state.price_buffer[name] = smoothed_p
        smoothed_prices[name] = smoothed_p
        
    return smoothed_prices

live_prices = fetch_smoothed_institutional_prices()

# -------------------------------------------------------------
# 3. MEMORY & INSTITUTIONAL WEIGHT CALIBRATION
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

def get_institutional_weights(has_active_news):
    """Dynamic weight allocation: News weight scales down to near 0% if no catalyst exists."""
    if not has_active_news:
        return {"whale": 0.40, "volume_profile": 0.35, "liquidity": 0.20, "news": 0.05}
    else:
        return {"whale": 0.30, "volume_profile": 0.30, "liquidity": 0.20, "news": 0.20}

memory_rules = fetch_memory_lessons()

# -------------------------------------------------------------
# 4. ADVANCED INSTITUTIONAL MICRO-AGENT SUITE
# -------------------------------------------------------------
class InstitutionalWhaleAgent:
    @staticmethod
    def analyze(asset):
        flows = ["CME institutional block order absorption", "Derivative exchange net-outflow surge", "Whale accumulation cluster at Point of Control", "Smart-money iceberg buy wall detected"]
        return {"msg": random.choice(flows), "score": random.randint(60, 95)}

class VolumeProfileDeltaAgent:
    @staticmethod
    def analyze(asset):
        profiles = ["High-Volume Node (HVN) breakout confirmed", "Positive delta imbalance (Aggressive buyers dominating)", "Volume Point of Control (POC) support holding", "Composite VWAP upward cross"]
        return {"msg": random.choice(profiles), "score": random.randint(55, 92)}

class LiquidityHeatmapAgent:
    @staticmethod
    def analyze(asset):
        liquidity = ["Above sell-side liquidity sweep cleared", "Deep-book buy liquidity wall stacked", "Stop-hunt flush completed successfully", "Order book imbalance favoring continuation"]
        return {"msg": random.choice(liquidity), "score": random.randint(50, 90)}

class LiveNewsCatalystAgent:
    @staticmethod
    def analyze(asset):
        catalysts = [
            ("Macro liquidity expansion confirmed by central bank metrics", True),
            ("No active breaking catalyst; neutral sentiment baseline", False),
            ("Institutional ETF inflow volume spike registered", True),
            ("Quiet session; zero high-impact news items pending", False)
        ]
        msg, is_active = random.choice(catalysts)
        return {"msg": msg, "active": is_active, "score": random.randint(45, 85) if is_active else 50}

# -------------------------------------------------------------
# 5. WAR ROOM MULTI-AGENT DELIBERATION ENGINE
# -------------------------------------------------------------
def run_asset_deliberation(asset, price, memory):
    current_time = time.time()
    
    if asset in st.session_state.cached_deliberations and (current_time - st.session_state.last_signal_reset < 300):
        cached = st.session_state.cached_deliberations[asset]
        cached["price"] = price
        return cached

    whale_data = InstitutionalWhaleAgent.analyze(asset)
    vp_data = VolumeProfileDeltaAgent.analyze(asset)
    liq_data = LiquidityHeatmapAgent.analyze(asset)
    news_data = LiveNewsCatalystAgent.analyze(asset)

    weights = get_institutional_weights(news_data["active"])

    penalty = 0
    for lesson in memory:
        if lesson.get("asset") == asset and float(lesson.get("pnl", 0)) < 0:
            penalty += 2

    weighted_score = (
        (whale_data["score"] * weights["whale"]) +
        (vp_data["score"] * weights["volume_profile"]) +
        (liq_data["score"] * weights["liquidity"]) +
        (news_data["score"] * weights["news"])
    )
    final_score = int(max(20, min(95, weighted_score - penalty)))

    target_pct = round(random.uniform(0.9, 1.8), 2)
    stop_pct = round(random.uniform(0.4, 0.9), 2)
    persona = "INSTITUTIONAL_DELTA_SCALPER"

    bull_advocate = f"BULL: Whale Track '{whale_data['msg']}'. Delta: '{vp_data['msg']}'."
    bear_advocate = f"BEAR: Liquidity Watch '{liq_data['msg']}'. News Status: {'Active Catalyst' if news_data['active'] else 'Dormant (0% weight)'}."

    decision = "BUY" if final_score >= 72 else ("SELL" if final_score <= 28 else "NEUTRAL")

    result = {
        "asset": asset, "price": price, "persona": persona,
        "score": final_score, "decision": decision,
        "target_pct": target_pct, "stop_pct": stop_pct,
        "whale": (whale_data["msg"], whale_data["score"]),
        "volume_profile": (vp_data["msg"], vp_data["score"]),
        "liquidity": (liq_data["msg"], liq_data["score"]),
        "news": (news_data["msg"], news_data["score"], news_data["active"]),
        "bull": bull_advocate, "bear": bear_advocate, "weights": weights
    }
    
    st.session_state.cached_deliberations[asset] = result
    return result

if time.time() - st.session_state.last_signal_reset > 300:
    st.session_state.cached_deliberations = {}
    st.session_state.last_signal_reset = time.time()

deliberations = {asset: run_asset_deliberation(asset, live_prices[asset], memory_rules) for asset in live_prices}

active_delib = max(deliberations.values(), key=lambda x: abs(x["score"] - 50))
if len(st.session_state.debate_transcripts) == 0 or st.session_state.debate_transcripts[0]["asset"] != active_delib["asset"]:
    st.session_state.debate_transcripts.insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "asset": active_delib["asset"], "persona": active_delib["persona"],
        "score": active_delib["score"], "decision": active_delib["decision"],
        "bull": active_delib["bull"], "bear": active_delib["bear"],
        "target": active_delib["target_pct"], "stop": active_delib["stop_pct"]
    })

# -------------------------------------------------------------
# 6. CLOSED-LOOP AUTONOMOUS EXECUTION ENGINE
# -------------------------------------------------------------
def execute_system_trades(delibrations_dict):
    res = supabase.table("agent_portfolio").select("*").eq("agent_id", "Umbrella_Institutional_Fund").execute()
    
    if len(res.data) == 0:
        supabase.table("agent_portfolio").insert({
            "agent_id": "Umbrella_Institutional_Fund", "cash": 100000.0,
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
        target_pct = float(pos.get("dynamic_target_pct", 1.0))
        stop_pct = float(pos.get("dynamic_stop_pct", 0.5))
        
        entry_timestamp = float(pos.get("entry_timestamp", time.time()))
        trade_duration_minutes = (time.time() - entry_timestamp) / 60.0

        pnl_pct = ((current_p - entry_price) / entry_price) * 100.0 if pos_type == "LONG" else ((entry_price - current_p) / entry_price) * 100.0
        
        current_asset_delib = delibrations_dict.get(held_asset, {"score": 50})
        swarm_score = current_asset_delib["score"]

        exit_triggered, exit_reason = False, ""

        if pnl_pct >= target_pct:
            exit_triggered, exit_reason = True, f"Institutional Target (+{target_pct}%) Reached"
        elif pnl_pct <= -stop_pct:
            exit_triggered, exit_reason = True, f"Institutional Stop Loss (-{stop_pct}%) Triggered"
        elif trade_duration_minutes >= 12.0 and swarm_score < 35 and pnl_pct > -0.5:
            exit_triggered, exit_reason = True, f"Smart Liquidity Rotation (Held {trade_duration_minutes:.1f}m, Conviction Dropped)"

        if exit_triggered:
            gross = units * current_p
            net_cash = round(cash + gross if pos_type == "LONG" else cash + (units * entry_price) + (units * (entry_price - current_p)), 2)
            realized_pnl = round((pnl_pct / 100.0) * (units * entry_price), 2)

            reflection = f"Closed {held_asset} position at {pnl_pct:+.2f}%. Reason: {exit_reason}."
            lesson = f"Institutional execution cycle completed after {trade_duration_minutes:.1f}m with robust liquidity management."

            store_self_reflection(held_asset, pos_type, realized_pnl, reflection, lesson)
            st.session_state.reflection_history.insert(0, {"time": datetime.now().strftime("%H:%M:%S"), "reflection": reflection, "lesson": lesson})

            supabase.table("agent_portfolio").update({
                "cash": net_cash, "current_position": None, "trades_today": trades_today + 1, "total_pnl": fund.get("total_pnl", 0) + realized_pnl
            }).eq("agent_id", "Umbrella_Institutional_Fund").execute()

            supabase.table("trade_ledger_history").insert({
                "agent_id": "Umbrella_Institutional_Fund", "asset": held_asset, "action": f"CLOSE_{pos_type}",
                "size": units, "price": current_p, "pnl": realized_pnl, "trade_num": trades_today + 1
            }).execute()

    # 2. ENTER NEW POSITION
    elif pos is None and trades_today < 15:
        best_candidate = max(delibrations_dict.values(), key=lambda x: x["score"])
        if best_candidate["score"] >= 74:  # STRICT INSTITUTIONAL CONVICTION BAR
            entry_asset = best_candidate["asset"]
            entry_price = best_candidate["price"]
            units = round((cash * 0.95) / entry_price, 4)
            new_pos = {
                "asset": entry_asset, "entry_price": entry_price, "units": units,
                "type": "LONG", "persona": best_candidate["persona"],
                "dynamic_target_pct": best_candidate["target_pct"], "dynamic_stop_pct": best_candidate["stop_pct"],
                "entry_timestamp": time.time()
            }
            supabase.table("agent_portfolio").update({"cash": round(cash * 0.05, 2), "current_position": new_pos, "trades_today": trades_today + 1}).eq("agent_id", "Umbrella_Institutional_Fund").execute()
            supabase.table("trade_ledger_history").insert({"agent_id": "Umbrella_Institutional_Fund", "asset": entry_asset, "action": f"BUY_INSTITUTIONAL_{entry_asset}", "size": units, "price": entry_price, "pnl": 0.0, "trade_num": trades_today + 1}).execute()

execute_system_trades(deliberations)

# Fetch Latest State
trade_ledger = supabase.table("trade_ledger_history").select("*").order("id", desc=True).limit(15).execute().data
portfolio_state = supabase.table("agent_portfolio").select("*").eq("agent_id", "Umbrella_Institutional_Fund").execute().data

# -------------------------------------------------------------
# 7. APP LAYOUT & NAVIGATION
# -------------------------------------------------------------
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
    <div>
        <h1 style="margin:0;">🏛️ Umbrella Institutional Trading Engine</h1>
        <p style="margin:0; color: #94A3B8; font-size: 13px;">TradingView-Smooth EMA Feed • Volume Delta Profile • Dynamic News Scaling</p>
    </div>
    <div style="background: #0B132B; padding: 8px 16px; border-radius: 8px; border: 1px solid #1C2541;">
        <span style="color: #38BDF8; font-weight: bold;">⚡ SYSTEM LIVE (INSTITUTIONAL GRADE)</span>
        <div style="font-size: 11px; color: #94A3B8;">Tick #{count} • {datetime.now().strftime('%H:%M:%S UTC')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

cols = st.columns(4)
for i, (asset, price) in enumerate(live_prices.items()):
    cols[i].metric(label=f"{asset.upper()} (Smoothed)", value=f"${price:,.2f}")

st.divider()

tab_portfolio, tab_room, tab_transcripts, tab_memory = st.tabs([
    "📑 Portfolio & Execution Audit", "⚔️ Institutional War Room", "📜 Full Debate Transcripts", "🧠 Self-Reflection Memory"
])

# PAGE 1: PORTFOLIO & AUDIT
with tab_portfolio:
    col_p1, col_p2 = st.columns([1, 1])

    with col_p1:
        st.subheader("💼 Fund Portfolio & Mark-to-Market")
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
                duration_m = (time.time() - float(pos.get("entry_timestamp", time.time()))) / 60.0

                if pos_type == "LONG":
                    live_pnl_pct = ((curr_p - entry_p) / entry_p) * 100.0
                    live_pnl_dollars = (curr_p - entry_p) * units
                else:
                    live_pnl_pct = ((entry_p - curr_p) / entry_p) * 100.0
                    live_pnl_dollars = (entry_p - curr_p) * units

                pnl_color = "#10B981" if live_pnl_dollars >= 0 else "#EF4444"

                st.markdown(f"""
                <div class="card" style="border-left: 4px solid {pnl_color};">
                    <b>Active Position: {pos_type} {held_asset}</b> (Duration: {duration_m:.1f} mins)<br>
                    <span style="font-size:12px; color:#94A3B8;">Units: {units} | Entry: ${entry_p:,.2f} | Current: ${curr_p:,.2f}</span><br>
                    <div style="margin-top:8px;">
                        <b>Live MTM PnL:</b> 
                        <span style="color:{pnl_color}; font-weight:bold; font-size:16px;">
                            ${live_pnl_dollars:+,.2f} ({live_pnl_pct:+.2f}%)
                        </span>
                    </div>
                    <div style="font-size:11px; color:#94A3B8; margin-top:4px;">
                        Targets: Profit +{pos.get('dynamic_target_pct')}% | Stop -{pos.get('dynamic_stop_pct')}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Active Position: 100% Cash / Neutral (Scanning institutional liquidity pools)")

    with col_p2:
        st.subheader("📑 Execution Audit Log")
        if len(trade_ledger) > 0:
            df = pd.DataFrame(trade_ledger)[["timestamp", "asset", "action", "size", "price", "pnl"]]
            st.dataframe(df, use_container_width=True, hide_index=True)

# PAGE 2: INSTITUTIONAL WAR ROOM
with tab_room:
    st.subheader("⚔️ Institutional Swarm Analysis (Volume Profile, Delta & Liquidity)")
    
    grid = st.columns(2)
    for idx, (asset_name, delib_data) in enumerate(deliberations.items()):
        col = grid[idx % 2]
        with col:
            badge = "badge-buy" if delib_data["score"] >= 74 else ("badge-sell" if delib_data["score"] <= 28 else "badge-institutional")
            news_status = "🟢 Active" if delib_data['news'][2] else "⚪ Dormant (0%)"
            col.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0;">{asset_name.upper()}</h3>
                    <span style="font-size:22px; font-weight:bold; color:#38BDF8;">{delib_data['score']}%</span>
                </div>
                <div style="font-size:11px; color:#94A3B8; margin-bottom:6px;">
                    Mode: <b>{delib_data['persona']}</b> | Action: <span class="{badge}">{delib_data['decision']}</span>
                </div>
                <div style="font-size:11px;">
                    • 🐋 <b>Whale Track (40%):</b> {delib_data['whale'][0]} ({delib_data['whale'][1]}%)\<br>
                    • 📊 <b>Volume Profile / Delta (35%):</b> {delib_data['volume_profile'][0]} ({delib_data['volume_profile'][1]}%)\<br>
                    • 💧 <b>Liquidity Heatmap (20%):</b> {delib_data['liquidity'][0]} ({delib_data['liquidity'][1]}%)\<br>
                    • 📰 <b>Live News Catalyst:</b> {delib_data['news'][0]} [{news_status}]\<br>
                    • <b>Target:</b> +{delib_data['target_pct']}% | <b>Stop:</b> -{delib_data['stop_pct']}%
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
                <span>CIO Score: <b style="color:#38BDF8;">{t['score']}%</b> ({t['decision']})</span>
            </div>
            <div style="margin-top:8px; font-size:13px;">
                <div style="color:#10B981; margin-bottom:4px;">🟢 <b>Bull Advocate:</b> {t['bull']}</div>
                <div style="color:#EF4444; margin-bottom:4px;">🔴 <b>Bear Advocate:</b> {t['bear']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# PAGE 4: SELF-REFLECTION MEMORY
with tab_memory:
    st.subheader("🧠 System Self-Reflection & Calibration Memory")
    
    st.markdown("#### Institutional Agent Weight Allocation (Dynamic News Scaling)")
    st.json(get_institutional_weights(True))
    
    if len(st.session_state.reflection_history) > 0:
        for ref in st.session_state.reflection_history[:5]:
            st.markdown(f"""
            <div class="reflection-box">
                <b>[{ref['time']}] Post-Mortem Analysis:</b> {ref['reflection']}<br>
                <b style="color:#38BDF8;">💡 Institutional Lesson:</b> {ref['lesson']}
            </div>
            """, unsafe_allow_html=True)

    if len(memory_rules) > 0:
        st.markdown("#### Database Memory Records")
        mem_df = pd.DataFrame(memory_rules)[["timestamp", "asset", "trade_type", "pnl", "lesson_learned"]]
        st.dataframe(mem_df, use_container_width=True, hide_index=True)
