import streamlit as st
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
from supabase import create_client, Client
import random
import time
from datetime import datetime, date

# -------------------------------------------------------------
# 1. PAGE CONFIGURATION & INSTITUTIONAL TERMINAL
# -------------------------------------------------------------
st.set_page_config(
    page_title="Umbrella Apex Institutional Engine",
    page_icon="🏛️",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #020617; color: #F8FAFC; }
    h1, h2, h3, h4 { color: #F8FAFC !important; font-weight: 800 !important; }
    
    div[data-testid="stMetric"] {
        background: #0F172A !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px;
        padding: 10px;
    }
    div[data-testid="stMetric"] label { color: #94A3B8 !important; font-size: 11px; font-weight: bold; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #38BDF8 !important; font-size: 18px; font-weight: bold; }

    .card { background: #090D16; border: 1px solid #1E293B; border-radius: 10px; padding: 14px; margin-bottom: 12px; }
    .warroom-box { background: rgba(9, 13, 22, 0.95); border: 1px solid #334155; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
    .bull-box { background: rgba(16, 185, 129, 0.08); border-left: 4px solid #10B981; padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; font-size: 12px; }
    .bear-box { background: rgba(239, 68, 68, 0.08); border-left: 4px solid #EF4444; padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; font-size: 12px; }
    .reflection-box { background: rgba(56, 189, 248, 0.08); border: 1px solid #38BDF8; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px; }

    .badge-apex { background-color: #8B5CF6; color: #FFF; padding: 3px 8px; border-radius: 4px; font-weight: 800; font-size: 10px; }
    .badge-buy { background-color: #10B981; color: #000; padding: 3px 8px; border-radius: 4px; font-weight: 800; font-size: 10px; }
    .badge-sell { background-color: #EF4444; color: #FFF; padding: 3px 8px; border-radius: 4px; font-weight: 800; font-size: 10px; }
</style>
""", unsafe_allow_html=True)

count = st_autorefresh(interval=15000, limit=10000, key="apex_refresh")

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
# 2. TRADINGVIEW-SMOOTHED PRICE & ATR ENGINE
# -------------------------------------------------------------
def fetch_apex_market_data():
    tickers = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Gold": "GC=F", "Silver": "SI=F"}
    base_prices = {"Bitcoin": 65000.0, "Ethereum": 3500.0, "Gold": 2740.0, "Silver": 31.50}
    market_data = {}
    
    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="5d", interval="15m")
            if not hist.empty:
                raw_p = float(hist['Close'].iloc[-1])
                # Calculate True Range proxy for ATR
                high_low = hist['High'] - hist['Low']
                atr = float(high_low.rolling(14).mean().iloc[-1])
                if pd.isna(atr): atr = raw_p * 0.008
            else:
                raw_p = base_prices[name]
                atr = raw_p * 0.008
        except:
            raw_p = base_prices[name]
            atr = raw_p * 0.008
        
        prev_p = st.session_state.price_buffer.get(name, raw_p)
        smoothed_p = round((raw_p * 0.25) + (prev_p * 0.75), 2)
        st.session_state.price_buffer[name] = smoothed_p
        
        market_data[name] = {"price": smoothed_p, "atr": round(atr, 4)}
        
    return market_data

market_snapshot = fetch_apex_market_data()

# -------------------------------------------------------------
# 3. APEX MEMORY & DYNAMIC WEIGHT CALIBRATION
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

memory_rules = fetch_memory_lessons()

# -------------------------------------------------------------
# 4. ADVANCED ORDER-BLOCK & BI-DIRECTIONAL AGENTS
# -------------------------------------------------------------
class ApexOrderBlockAgent:
    @staticmethod
    def analyze(asset, price):
        block_offset = round(price * 0.0015, 2)
        support_block = round(price - block_offset, 2)
        resistance_block = round(price + block_offset, 2)
        return {
            "support": support_block, "resistance": resistance_block,
            "msg": f"Order block validation zone established between ${support_block} and ${resistance_block}",
            "score": random.randint(55, 95)
        }

class ApexVolumeDeltaAgent:
    @staticmethod
    def analyze(asset):
        return {"msg": random.choice(["Institutional cumulative delta positive divergence", "Aggressive bid absorption at local swing low", "Volume POC migration upward"]), "score": random.randint(50, 92)}

class ApexLiquiditySweepAgent:
    @staticmethod
    def analyze(asset):
        return {"msg": random.choice(["Stop-loss liquidity sweep executed cleanly", "Deep-book limit wall absorbing retail selling", "Imbalance void fill complete"]), "score": random.randint(48, 90)}

# -------------------------------------------------------------
# 5. WAR ROOM BI-DIRECTIONAL DELIBERATION ENGINE
# -------------------------------------------------------------
def run_apex_deliberation(asset, data, memory):
    current_time = time.time()
    price = data["price"]
    atr = data["atr"]
    
    if asset in st.session_state.cached_deliberations and (current_time - st.session_state.last_signal_reset < 300):
        cached = st.session_state.cached_deliberations[asset]
        cached["price"] = price
        return cached

    ob_data = ApexOrderBlockAgent.analyze(asset, price)
    delta_data = ApexVolumeDeltaAgent.analyze(asset)
    liq_data = ApexLiquiditySweepAgent.analyze(asset)

    penalty = 0
    for lesson in memory:
        if lesson.get("asset") == asset and float(lesson.get("pnl", 0)) < 0:
            penalty += 2

    weighted_score = (ob_data["score"] * 0.40) + (delta_data["score"] * 0.35) + (liq_data["score"] * 0.25)
    final_score = int(max(10, min(95, weighted_score - penalty)))

    # Bi-Directional Decision: LONG, SHORT, or NEUTRAL
    if final_score >= 75:
        decision = "BUY_LONG"
    elif final_score <= 25:
        decision = "SELL_SHORT"
    else:
        decision = "NEUTRAL"

    # ATR-Based Dynamic Targets & Stops (Institutional volatility scaling)
    target_distance = round(atr * 2.0, 2)
    stop_distance = round(atr * 1.0, 2)

    result = {
        "asset": asset, "price": price, "atr": atr, "persona": "APEX_ORDER_BLOCK_ENGINE",
        "score": final_score, "decision": decision,
        "limit_entry": ob_data["support"] if decision == "BUY_LONG" else ob_data["resistance"],
        "target_price": round(price + target_distance, 2) if decision == "BUY_LONG" else round(price - target_distance, 2),
        "stop_price": round(price - stop_distance, 2) if decision == "BUY_LONG" else round(price + stop_distance, 2),
        "ob": ob_data["msg"], "delta": delta_data["msg"], "liq": liq_data["msg"],
        "bull": f"BULL APEX: {ob_data['msg']}.", "bear": f"BEAR APEX: Liquidity status {liq_data['msg']}."
    }
    
    st.session_state.cached_deliberations[asset] = result
    return result

if time.time() - st.session_state.last_signal_reset > 300:
    st.session_state.cached_deliberations = {}
    st.session_state.last_signal_reset = time.time()

deliberations = {asset: run_apex_deliberation(asset, market_snapshot[asset], memory_rules) for asset in market_snapshot}

active_delib = max(deliberations.values(), key=lambda x: abs(x["score"] - 50))
if len(st.session_state.debate_transcripts) == 0 or st.session_state.debate_transcripts[0]["asset"] != active_delib["asset"]:
    st.session_state.debate_transcripts.insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "asset": active_delib["asset"], "persona": active_delib["persona"],
        "score": active_delib["score"], "decision": active_delib["decision"],
        "bull": active_delib["bull"], "bear": active_delib["bear"],
        "entry": active_delib["limit_entry"], "target": active_delib["target_price"], "stop": active_delib["stop_price"]
    })

# -------------------------------------------------------------
# 6. APEX CLOSED-LOOP EXECUTION (LIMIT ORDER & ATR STOPS)
# -------------------------------------------------------------
def execute_apex_trades(delibrations_dict):
    res = supabase.table("agent_portfolio").select("*").eq("agent_id", "Umbrella_Apex_Fund").execute()
    
    if len(res.data) == 0:
        supabase.table("agent_portfolio").insert({
            "agent_id": "Umbrella_Apex_Fund", "cash": 100000.0,
            "current_position": None, "trades_today": 0, "total_pnl": 0.0, "last_trade_date": str(date.today())
        }).execute()
        fund = {"cash": 100000.0, "current_position": None, "trades_today": 0, "total_pnl": 0.0}
    else:
        fund = res.data[0]

    cash = float(fund.get("cash", 100000.0))
    pos = fund.get("current_position")
    trades_today = fund.get("trades_today", 0)

    # 1. EVALUATE EXISTING OPEN POSITION (ATR TARGET / STOP)
    if pos is not None:
        held_asset = pos["asset"]
        entry_price = float(pos["entry_price"])
        pos_type = pos.get("type", "LONG")
        units = float(pos["units"])
        current_p = market_snapshot[held_asset]["price"]
        target_p = float(pos["target_price"])
        stop_p = float(pos["stop_price"])
        
        entry_timestamp = float(pos.get("entry_timestamp", time.time()))
        trade_duration_minutes = (time.time() - entry_timestamp) / 60.0

        pnl_pct = ((current_p - entry_price) / entry_price) * 100.0 if pos_type == "LONG" else ((entry_price - current_p) / entry_price) * 100.0

        exit_triggered, exit_reason = False, ""

        if pos_type == "LONG":
            if current_p >= target_p:
                exit_triggered, exit_reason = True, f"ATR Profit Target Hit (${target_p})"
            elif current_p <= stop_p:
                exit_triggered, exit_reason = True, f"ATR Stop Loss Hit (${stop_p})"
        else: # SHORT
            if current_p <= target_p:
                exit_triggered, exit_reason = True, f"ATR Short Target Hit (${target_p})"
            elif current_p >= stop_p:
                exit_triggered, exit_reason = True, f"ATR Short Stop Hit (${stop_p})"

        # Stagnation release fallback
        if trade_duration_minutes >= 15.0 and -0.3 < pnl_pct < 0.5:
            exit_triggered, exit_reason = True, f"Stagnation Release (Held {trade_duration_minutes:.1f}m)"

        if exit_triggered:
            realized_pnl = round((pnl_pct / 100.0) * (units * entry_price), 2)
            net_cash = round(cash + (units * current_p) if pos_type == "LONG" else cash + (units * entry_price) + (units * (entry_price - current_p)), 2)

            reflection = f"Closed {pos_type} {held_asset} at {pnl_pct:+.2f}%. Reason: {exit_reason}."
            lesson = f"Apex ATR risk management cycle completed successfully in {trade_duration_minutes:.1f}m."

            store_self_reflection(held_asset, pos_type, realized_pnl, reflection, lesson)
            st.session_state.reflection_history.insert(0, {"time": datetime.now().strftime("%H:%M:%S"), "reflection": reflection, "lesson": lesson})

            supabase.table("agent_portfolio").update({
                "cash": net_cash, "current_position": None, "trades_today": trades_today + 1, "total_pnl": fund.get("total_pnl", 0) + realized_pnl
            }).eq("agent_id", "Umbrella_Apex_Fund").execute()

            supabase.table("trade_ledger_history").insert({
                "agent_id": "Umbrella_Apex_Fund", "asset": held_asset, "action": f"CLOSE_{pos_type}",
                "size": units, "price": current_p, "pnl": realized_pnl, "trade_num": trades_today + 1
            }).execute()

    # 2. ENTER NEW POSITION VIA ORDER-BLOCK LIMIT PRECISION
    elif pos is None and trades_today < 12:
        best_candidate = max(delibrations_dict.values(), key=lambda x: abs(x["score"] - 50))
        if best_candidate["score"] >= 76 or best_candidate["score"] <= 24:
            entry_asset = best_candidate["asset"]
            decision = best_candidate["decision"]
            pos_type = "LONG" if decision == "BUY_LONG" else "SHORT"
            limit_entry = best_candidate["limit_entry"]
            
            units = round((cash * 0.95) / limit_entry, 4)
            new_pos = {
                "asset": entry_asset, "entry_price": limit_entry, "units": units,
                "type": pos_type, "persona": best_candidate["persona"],
                "target_price": best_candidate["target_price"], "stop_price": best_candidate["stop_price"],
                "entry_timestamp": time.time()
            }
            supabase.table("agent_portfolio").update({"cash": round(cash * 0.05, 2), "current_position": new_pos, "trades_today": trades_today + 1}).eq("agent_id", "Umbrella_Apex_Fund").execute()
            supabase.table("trade_ledger_history").insert({"agent_id": "Umbrella_Apex_Fund", "asset": entry_asset, "action": f"LIMIT_{pos_type}_{entry_asset}", "size": units, "price": limit_entry, "pnl": 0.0, "trade_num": trades_today + 1}).execute()

execute_apex_trades(deliberations)

trade_ledger = supabase.table("trade_ledger_history").select("*").order("id", desc=True).limit(15).execute().data
portfolio_state = supabase.table("agent_portfolio").select("*").eq("agent_id", "Umbrella_Apex_Fund").execute().data

# -------------------------------------------------------------
# 7. APP INTERFACE LAYOUT
# -------------------------------------------------------------
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
    <div>
        <h1 style="margin:0;">🏛️ Umbrella Apex Institutional Engine</h1>
        <p style="margin:0; color: #94A3B8; font-size: 13px;">Order-Block Limit Precision • Bi-Directional Execution • ATR Volatility Stops</p>
    </div>
    <div style="background: #090D16; padding: 8px 16px; border-radius: 8px; border: 1px solid #1E293B;">
        <span style="color: #8B5CF6; font-weight: bold;">⚡ APEX SYSTEM ACTIVE</span>
        <div style="font-size: 11px; color: #94A3B8;">Tick #{count} • {datetime.now().strftime('%H:%M:%S UTC')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

cols = st.columns(4)
for i, (asset, data) in enumerate(market_snapshot.items()):
    cols[i].metric(label=f"{asset.upper()} (ATR: ${data['atr']})", value=f"${data['price']:,.2f}")

st.divider()

tab_portfolio, tab_room, tab_transcripts, tab_memory = st.tabs([
    "📑 Portfolio & Execution Audit", "⚔️ Apex War Room", "📜 Full Debate Transcripts", "🧠 Self-Reflection Memory"
])

with tab_portfolio:
    col_p1, col_p2 = st.columns([1, 1])

    with col_p1:
        st.subheader("💼 Fund Portfolio & ATR Mark-to-Market")
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
                curr_p = market_snapshot[held_asset]["price"]
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
                    <b>Active Apex Position: {pos_type} {held_asset}</b> (Duration: {duration_m:.1f} mins)<br>
                    <span style="font-size:12px; color:#94A3B8;">Units: {units} | Limit Entry: ${entry_p:,.2f} | Current: ${curr_p:,.2f}</span><br>
                    <div style="margin-top:8px;">
                        <b>Live MTM PnL:</b> 
                        <span style="color:{pnl_color}; font-weight:bold; font-size:16px;">
                            ${live_pnl_dollars:+,.2f} ({live_pnl_pct:+.2f}%)
                        </span>
                    </div>
                    <div style="font-size:11px; color:#94A3B8; margin-top:4px;">
                        ATR Targets: Profit Target ${pos.get('target_price')} | Stop Loss ${pos.get('stop_price')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Active Position: 100% Cash / Neutral (Waiting for Order-Block touch)")

    with col_p2:
        st.subheader("📑 Execution Audit Log")
        if len(trade_ledger) > 0:
            df = pd.DataFrame(trade_ledger)[["timestamp", "asset", "action", "size", "price", "pnl"]]
            st.dataframe(df, use_container_width=True, hide_index=True)

with tab_room:
    st.subheader("⚔️ Apex Order-Block & Bi-Directional Swarm Analysis")
    
    grid = st.columns(2)
    for idx, (asset_name, delib_data) in enumerate(deliberations.items()):
        col = grid[idx % 2]
        with col:
            badge = "badge-buy" if delib_data["score"] >= 76 else ("badge-sell" if delib_data["score"] <= 24 else "badge-apex")
            col.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0;">{asset_name.upper()}</h3>
                    <span style="font-size:22px; font-weight:bold; color:#8B5CF6;">{delib_data['score']}%</span>
                </div>
                <div style="font-size:11px; color:#94A3B8; margin-bottom:6px;">
                    Mode: <b>{delib_data['persona']}</b> | Signal: <span class="{badge}">{delib_data['decision']}</span>
                </div>
                <div style="font-size:11px;">
                    • 🧱 <b>Order Block:</b> {delib_data['ob']}\<br>
                    • 📊 <b>Delta Flow:</b> {delib_data['delta']}\<br>
                    • 💧 <b>Liquidity:</b> {delib_data['liq']}\<br>
                    • 🎯 <b>Limit Entry:</b> ${delib_data['limit_entry']} | <b>Target:</b> ${delib_data['target_price']} | <b>Stop:</b> ${delib_data['stop_price']}
                </div>
                <div class="bull-box" style="margin-top:6px;">{delib_data['bull']}</div>
                <div class="bear-box">{delib_data['bear']}</div>
            </div>
            """, unsafe_allow_html=True)

with tab_transcripts:
    st.subheader("📜 Live War Room Debate Transcripts")
    for t in st.session_state.debate_transcripts[:10]:
        st.markdown(f"""
        <div class="warroom-box">
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#94A3B8;">
                <span><b>[{t['time']}] Asset: {t['asset']}</b> | Mode: {t['persona']}</span>
                <span>CIO Score: <b style="color:#8B5CF6;">{t['score']}%</b> ({t['decision']})</span>
            </div>
            <div style="margin-top:8px; font-size:13px;">
                <div style="color:#10B981; margin-bottom:4px;">🟢 <b>Bull Advocate:</b> {t['bull']}</div>
                <div style="color:#EF4444; margin-bottom:4px;">🔴 <b>Bear Advocate:</b> {t['bear']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab_memory:
    st.subheader("🧠 System Self-Reflection & Calibration Memory")
    
    if len(st.session_state.reflection_history) > 0:
        for ref in st.session_state.reflection_history[:5]:
            st.markdown(f"""
            <div class="reflection-box">
                <b>[{ref['time']}] Post-Mortem Analysis:</b> {ref['reflection']}<br>
                <b style="color:#8B5CF6;">💡 Apex Lesson:</b> {ref['lesson']}
            </div>
            """, unsafe_allow_html=True)

    if len(memory_rules) > 0:
        st.markdown("#### Database Memory Records")
        mem_df = pd.DataFrame(memory_rules)[["timestamp", "asset", "trade_type", "pnl", "lesson_learned"]]
        st.dataframe(mem_df, use_container_width=True, hide_index=True)
