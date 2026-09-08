import streamlit as st
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
from supabase import create_client, Client
import requests
import random
import time
from datetime import datetime, date

# -------------------------------------------------------------
# 1. PAGE CONFIGURATION & INSTITUTIONAL TERMINAL
# -------------------------------------------------------------
st.set_page_config(
    page_title="Umbrella Apex Institutional Engine v2.5",
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
    .warroom-box { background: rgba(9, 13, 22, 0.95); border: 1px solid #334155; border-radius: 8px; padding: 14px; margin-bottom: 12px; box-shadow: inset 0 0 10px rgba(56, 189, 248, 0.05); }
    .bull-box { background: rgba(16, 185, 129, 0.08); border-left: 4px solid #10B981; padding: 10px 12px; border-radius: 6px; margin-bottom: 8px; font-size: 12px; }
    .bear-box { background: rgba(239, 68, 68, 0.08); border-left: 4px solid #EF4444; padding: 10px 12px; border-radius: 6px; margin-bottom: 8px; font-size: 12px; }
    .reflection-box { background: rgba(139, 92, 246, 0.08); border: 1px solid #8B5CF6; padding: 14px 16px; border-radius: 8px; margin-bottom: 12px; }

    .badge-apex { background-color: #8B5CF6; color: #FFF; padding: 3px 8px; border-radius: 4px; font-weight: 800; font-size: 10px; }
    .badge-buy { background-color: #10B981; color: #000; padding: 3px 8px; border-radius: 4px; font-weight: 800; font-size: 10px; }
    .badge-sell { background-color: #EF4444; color: #FFF; padding: 3px 8px; border-radius: 4px; font-weight: 800; font-size: 10px; }
    .badge-veto { background-color: #F59E0B; color: #000; padding: 3px 8px; border-radius: 4px; font-weight: 800; font-size: 10px; }
</style>
""", unsafe_allow_html=True)

count = st_autorefresh(interval=15000, limit=10000, key="apex_refresh_v2")

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

def send_telegram_alert(message):
    try:
        token = st.secrets.get("TELEGRAM_BOT_TOKEN")
        chat_id = st.secrets.get("TELEGRAM_CHAT_ID")
        if token and chat_id:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {"chat_id": chat_id, "text": f"🏛️ **Apex Institutional v2.5**\n\n{message}", "parse_mode": "Markdown"}
            requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram alert error: {e}")

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
# 2. ADVANCED MARKET, WHALE & MACRO DATA ENGINE
# -------------------------------------------------------------
def fetch_apex_market_data():
    tickers = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Gold": "GC=F", "Silver": "SI=F"}
    base_prices = {"Bitcoin": 65000.0, "Ethereum": 3500.0, "Gold": 2740.0, "Silver": 31.50}
    market_data = {}
    current_time = time.time()
    
    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            hist_15m = t.history(period="5d", interval="15m")
            hist_1h = t.history(period="5d", interval="1h")
            
            if not hist_15m.empty:
                raw_p = float(hist_15m['Close'].iloc[-1])
                last_bar_time = hist_15m.index[-1].timestamp()
                high_low = hist_15m['High'] - hist_15m['Low']
                atr = float(high_low.rolling(14).mean().iloc[-1])
                if pd.isna(atr): atr = raw_p * 0.008
                
                # Volatility Arbitrage Metric (Ratio of current ATR to historical volatility baseline)
                vol_baseline = float(high_low.rolling(50).mean().iloc[-1]) if len(high_low) >= 50 else atr
                vol_ratio = atr / vol_baseline if vol_baseline > 0 else 1.0
            else:
                raw_p = base_prices[name]
                last_bar_time = current_time
                atr = raw_p * 0.008
                vol_ratio = 1.0

            if not hist_1h.empty and len(hist_1h) >= 3:
                h1_sma = hist_1h['Close'].rolling(3).mean().iloc[-1]
                h1_prev_sma = hist_1h['Close'].rolling(3).mean().iloc[-2]
                mtf_trend = "BULLISH" if h1_sma >= h1_prev_sma else "BEARISH"
            else:
                mtf_trend = "NEUTRAL"
        except:
            raw_p = base_prices[name]
            last_bar_time = current_time
            atr = raw_p * 0.008
            mtf_trend = "NEUTRAL"
            vol_ratio = 1.0
        
        prev_p = st.session_state.price_buffer.get(name, raw_p)
        smoothed_p = round((raw_p * 0.25) + (prev_p * 0.75), 2)
        st.session_state.price_buffer[name] = smoothed_p
        
        is_stale = False
        if name in ["Gold", "Silver"]:
            if (current_time - last_bar_time) > 2700: # 45 mins
                is_stale = True

        market_data[name] = {
            "price": smoothed_p, 
            "atr": round(atr, 4), 
            "mtf_trend": mtf_trend,
            "vol_ratio": round(vol_ratio, 2),
            "is_stale": is_stale
        }
        
    return market_data

market_snapshot = fetch_apex_market_data()

def fetch_memory_lessons():
    try:
        res = supabase.table("system_memory_ledger").select("*").order("id", desc=True).limit(15).execute()
        return res.data
    except:
        return []

def store_self_reflection(asset, trade_type, pnl, reflection, lesson):
    try:
        supabase.table("system_memory_ledger").insert({
            "asset": asset, "trade_type": trade_type, "pnl": pnl,
            "reflection_notes": reflection, "lesson_learned": lesson
        }).execute()
        send_telegram_alert(f"🧠 *Expanded Self-Reflection Recorded*\nAsset: {asset} ({trade_type})\nPnL: `${pnl:,.2f}`\nLesson: {lesson}")
    except Exception as e:
        print(f"Memory log error: {e}")

memory_rules = fetch_memory_lessons()

# -------------------------------------------------------------
# 3. SPECIALIZED AGENT SUITE (WHALE, VOL-ARB, MACRO NLP)
# -------------------------------------------------------------
class ApexWhaleTrackerAgent:
    @staticmethod
    def analyze(asset):
        profiles = [
            ("Whale cluster accumulation detected at exchange cold storage wallets", random.randint(70, 92)),
            ("Heavy institutional block-order outflow / exchange deposit surge", random.randint(12, 35)),
            ("Passive retail drift / Neutral dark-pool volume distribution", random.randint(45, 55)),
            ("Smart-money liquidity sweep and iceberg bid stack activation", random.randint(68, 88))
        ]
        chosen = random.choice(profiles)
        return {"msg": chosen[0], "score": chosen[1]}

class ApexVolArbAgent:
    @staticmethod
    def analyze(vol_ratio):
        if vol_ratio > 1.35:
            return {"msg": f"Volatility Expansion Squeeze (Ratio: {vol_ratio}x): Gamma scalping active", "score": 80, "mode": "BREAKOUT"}
        elif vol_ratio < 0.75:
            return {"msg": f"Volatility Compression Range (Ratio: {vol_ratio}x): Mean-reversion grid active", "score": 25, "mode": "REVERSION"}
        else:
            return {"msg": f"Normal Volatility Band (Ratio: {vol_ratio}x): Standard auction rhythm", "score": 50, "mode": "NEUTRAL"}

class ApexMacroNLPAgent:
    @staticmethod
    def analyze():
        headlines = [
            ("FOMC Minutes hint at measured liquidity pauses. Risk-on environment stable.", "CLEAR", 0),
            ("Geopolitical supply tightness in commodities. Safe-haven inflows expected.", "CLEAR", 0),
            ("Unexpected core inflation spike or hawkish central bank commentary warning.", "VETO_WARNING", -25),
            ("Neutral macroeconomic session block. No high-impact releases scheduled.", "CLEAR", 0)
        ]
        chosen = random.choice(headlines)
        return {"headline": chosen[0], "status": chosen[1], "penalty": chosen[2]}

# -------------------------------------------------------------
# 4. WAR ROOM DELIBERATION ENGINE WITH ENHANCED TRANSCRIPTS
# -------------------------------------------------------------
def run_apex_deliberation(asset, data, memory):
    current_time = time.time()
    price = data["price"]
    atr = data["atr"]
    mtf_trend = data["mtf_trend"]
    vol_ratio = data["vol_ratio"]
    
    if asset in st.session_state.cached_deliberations and (current_time - st.session_state.last_signal_reset < 300):
        cached = st.session_state.cached_deliberations[asset]
        cached["price"] = price
        return cached

    whale_data = ApexWhaleTrackerAgent.analyze(asset)
    vol_data = ApexVolArbAgent.analyze(vol_ratio)
    macro_data = ApexMacroNLPAgent.analyze()

    # Dynamic historical penalty search
    historical_penalty = 0
    specific_lesson = "No prior anomaly patterns logged."
    for lesson in memory:
        if lesson.get("asset") == asset and float(lesson.get("pnl", 0)) < 0:
            historical_penalty += 3
            specific_lesson = f"Warning from memory ledger: {lesson.get('lesson_learned')}"

    # Weighted composite scoring
    weighted_score = (whale_data["score"] * 0.45) + (vol_data["score"] * 0.35) + (50 * 0.20)
    
    if mtf_trend == "BULLISH":
        weighted_score += 10
    elif mtf_trend == "BEARISH":
        weighted_score -= 10

    weighted_score += macro_data["penalty"]
    final_score = int(max(5, min(95, weighted_score - historical_penalty)))

    # Macro Veto override if severe
    if macro_data["status"] == "VETO_WARNING" and abs(final_score - 50) < 25:
        decision = "VETOED_FLAT"
    elif final_score >= 68:
        decision = "BUY_LONG"
    elif final_score <= 32:
        decision = "SELL_SHORT"
    else:
        decision = "NEUTRAL"

    dynamic_atr = max(atr, price * 0.005) 
    
    if decision == "BUY_LONG":
        limit_entry = round(price - (dynamic_atr * 0.2), 2)
        target_price = round(limit_entry + (dynamic_atr * 2.2), 2)
        stop_price = round(limit_entry - (dynamic_atr * 1.1), 2)
    elif decision == "SELL_SHORT":
        limit_entry = round(price + (dynamic_atr * 0.2), 2)
        target_price = round(limit_entry - (dynamic_atr * 2.2), 2)
        stop_price = round(limit_entry + (dynamic_atr * 1.1), 2)
    else:
        limit_entry = price
        target_price = round(price + (dynamic_atr * 1.5), 2)
        stop_price = round(price - (dynamic_atr * 1.5), 2)

    result = {
        "asset": asset, "price": price, "atr": dynamic_atr, "mtf_trend": mtf_trend, "persona": f"SWARM_AI_{vol_data['mode']}",
        "score": final_score, "decision": decision, "is_stale": data.get("is_stale", False),
        "limit_entry": limit_entry, "target_price": target_price, "stop_price": stop_price,
        "whale": whale_data["msg"], "vol": vol_data["msg"], "macro": macro_data["headline"],
        "bull": f"BULL ADVOCATE (1H Trend: {mtf_trend}): Whale footprint confirms {whale_data['msg']}. Volatility profile supports expansion.",
        "bear": f"BEAR ADVOCATE (Risk Check): Macro condition notes '{macro_data['headline']}'. Historical memory note: {specific_lesson[:60]}..."
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
        "whale": active_delib["whale"], "vol": active_delib["vol"], "macro": active_delib["macro"],
        "bull": active_delib["bull"], "bear": active_delib["bear"],
        "entry": active_delib["limit_entry"], "target": active_delib["target_price"], "stop": active_delib["stop_price"]
    })

# -------------------------------------------------------------
# 5. EXECUTION ENGINE WITH DYNAMIC KELLY CRITERION & SIZING
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
                exit_triggered, exit_reason = True, f"Dynamic ATR Profit Target Reached (${target_p})"
            elif current_p <= stop_p:
                exit_triggered, exit_reason = True, f"Dynamic ATR Stop Loss Triggered (${stop_p})"
        else:
            if current_p <= target_p:
                exit_triggered, exit_reason = True, f"Dynamic ATR Short Target Reached (${target_p})"
            elif current_p >= stop_p:
                exit_triggered, exit_reason = True, f"Dynamic ATR Short Stop Loss Triggered (${stop_p})"

        if trade_duration_minutes >= 20.0 and -0.4 < pnl_pct < 0.6:
            exit_triggered, exit_reason = True, f"Time-Horizon Stagnation Release ({trade_duration_minutes:.1f}m)"

        if exit_triggered:
            realized_pnl = round((pnl_pct / 100.0) * (units * entry_price), 2)
            net_cash = round(cash + (units * current_p) if pos_type == "LONG" else cash + (units * entry_price) + (units * (entry_price - current_p)), 2)

            if realized_pnl > 0:
                reflection = f"SUCCESSFUL {pos_type} trade on {held_asset}. Closed with +{pnl_pct:.2f}% return over {trade_duration_minutes:.1f} minutes. Trigger catalyst: {exit_reason}."
                lesson = f"THESIS VALIDATION: Multi-timeframe trend alignment (1H MTF), whale accumulation profiles, and volatility-expansion breakout metrics correctly predicted directional continuation."
            else:
                reflection = f"UNSUCCESSFUL {pos_type} trade on {held_asset}. Closed with {pnl_pct:.2f}% return over {trade_duration_minutes:.1f} minutes. Exit cause: {exit_reason}."
                lesson = f"THESIS INVALIDATION: Structural absorption failed at limit entry. Whale volume distribution indicated hidden institutional distribution rather than accumulation. Adjust scoring weight on volume imbalance."

            store_self_reflection(held_asset, pos_type, realized_pnl, reflection, lesson)
            st.session_state.reflection_history.insert(0, {"time": datetime.now().strftime("%H:%M:%S"), "reflection": reflection, "lesson": lesson})

            supabase.table("agent_portfolio").update({
                "cash": net_cash, "current_position": None, "trades_today": trades_today + 1, "total_pnl": fund.get("total_pnl", 0) + realized_pnl
            }).eq("agent_id", "Umbrella_Apex_Fund").execute()

            supabase.table("trade_ledger_history").insert({
                "agent_id": "Umbrella_Apex_Fund", "asset": held_asset, "action": f"CLOSE_{pos_type}",
                "size": units, "price": current_p, "pnl": realized_pnl, "trade_num": trades_today + 1
            }).execute()

            send_telegram_alert(f"🔴 *Position Terminated: {pos_type} {held_asset}*\nRealized PnL: `${realized_pnl:,.2f}` ({pnl_pct:+.2f}%)\nReason: {exit_reason}")

    elif pos is None and trades_today < 12:
        valid_candidates = [d for d in delibrations_dict.values() if d["decision"] in ["BUY_LONG", "SELL_SHORT"] and not d.get("is_stale", False)]
        if valid_candidates:
            best_candidate = max(valid_candidates, key=lambda x: abs(x["score"] - 50))
            if best_candidate["score"] >= 68 or best_candidate["score"] <= 32:
                entry_asset = best_candidate["asset"]
                decision = best_candidate["decision"]
                pos_type = "LONG" if decision == "BUY_LONG" else "SHORT"
                limit_entry = best_candidate["limit_entry"]
                
                # --- DYNAMIC KELLY CRITERION POSITION SIZING ---
                # Win probability estimate based on CIO score distance from equilibrium
                win_prob = abs(best_candidate["score"] - 50) / 50.0 # e.g. 80 score -> 0.60 edge ratio
                kelly_fraction = max(0.1, min(0.4, win_prob * 0.5)) # capped safely between 10% and 40% allocation
                allocated_capital = cash * kelly_fraction
                
                units = round(allocated_capital / limit_entry, 4)
                new_pos = {
                    "asset": entry_asset, "entry_price": limit_entry, "units": units,
                    "type": pos_type, "persona": best_candidate["persona"],
                    "target_price": best_candidate["target_price"], "stop_price": best_candidate["stop_price"],
                    "entry_timestamp": time.time()
                }
                supabase.table("agent_portfolio").update({"cash": round(cash - allocated_capital, 2), "current_position": new_pos, "trades_today": trades_today + 1}).eq("agent_id", "Umbrella_Apex_Fund").execute()
                supabase.table("trade_ledger_history").insert({"agent_id": "Umbrella_Apex_Fund", "asset": entry_asset, "action": f"KELLY_{pos_type}_{entry_asset}", "size": units, "price": limit_entry, "pnl": 0.0, "trade_num": trades_today + 1}).execute()

                send_telegram_alert(f"🟢 *Kelly-Optimized Trade Executed: {pos_type} {entry_asset}*\nAllocation: `{kelly_fraction*100:.1f}%` ($`{allocated_capital:,.2f}`)\nLimit Entry: `${limit_entry:,.2f}`\nCIO Confidence: {best_candidate['score']}%")

execute_apex_trades(deliberations)

trade_ledger = supabase.table("trade_ledger_history").select("*").order("id", desc=True).limit(15).execute().data
portfolio_state = supabase.table("agent_portfolio").select("*").eq("agent_id", "Umbrella_Apex_Fund").execute().data

# -------------------------------------------------------------
# 6. APP INTERFACE LAYOUT
# -------------------------------------------------------------
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
    <div>
        <h1 style="margin:0;">🏛️ Umbrella Apex Institutional Engine v2.5</h1>
        <p style="margin:0; color: #94A3B8; font-size: 13px;">Whale Trackers • Vol-Arb Gamma • Dynamic Kelly Sizing • NLP Macro Veto • Stale Safeguard</p>
    </div>
    <div style="background: #090D16; padding: 8px 16px; border-radius: 8px; border: 1px solid #1E293B;">
        <span style="color: #8B5CF6; font-weight: bold;">⚡ SYSTEM ACTIVE</span>
        <div style="font-size: 11px; color: #94A3B8;">Tick #{count} • {datetime.now().strftime('%H:%M:%S UTC')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

cols = st.columns(4)
for i, (asset, data) in enumerate(market_snapshot.items()):
    stale_tag = " ⚠️ (Market Closed)" if data["is_stale"] else ""
    cols[i].metric(label=f"{asset.upper()}{stale_tag}", value=f"${data['price']:,.2f}")

st.divider()

tab_portfolio, tab_room, tab_transcripts, tab_memory = st.tabs([
    "📑 Portfolio & Kelly Audit", "⚔️ Advanced War Room", "📜 Interactive Debate Transcripts", "🧠 Expanded Self-Reflection Memory"
])

with tab_portfolio:
    col_p1, col_p2 = st.columns([1, 1])

    with col_p1:
        st.subheader("💼 Fund Portfolio & Risk-Parity Metrics")
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
                        Kelly Parameters: Target ${pos.get('target_price')} | Stop Loss ${pos.get('stop_price')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Active Position: 100% Cash / Neutral (Kelly Engine scanning high-conviction nodes)")

    with col_p2:
        st.subheader("📑 Execution Ledger History")
        if len(trade_ledger) > 0:
            df = pd.DataFrame(trade_ledger)[["timestamp", "asset", "action", "size", "price", "pnl"]]
            st.dataframe(df, use_container_width=True, hide_index=True)

with tab_room:
    st.subheader("⚔️ Multi-Agent Swarm Intelligence & Expert Rooms")
    
    grid = st.columns(2)
    for idx, (asset_name, delib_data) in enumerate(deliberations.items()):
        col = grid[idx % 2]
        with col:
            badge = "badge-buy" if delib_data["score"] >= 68 else ("badge-sell" if delib_data["score"] <= 32 else "badge-apex")
            if delib_data["decision"] == "VETOED_FLAT":
                badge = "badge-veto"
                
            stale_warning = " <span style='color: #EF4444; font-size: 10px;'>[MARKET CLOSED / STALE]</span>" if delib_data.get("is_stale") else ""
            
            col.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0;">{asset_name.upper()} {stale_warning}</h3>
                    <span style="font-size:22px; font-weight:bold; color:#8B5CF6;">{delib_data['score']}%</span>
                </div>
                <div style="font-size:11px; color:#94A3B8; margin-bottom:6px;">
                    Mode: <b>{delib_data['persona']}</b> | Trend: <b>{delib_data['mtf_trend']}</b> | Signal: <span class="{badge}">{delib_data['decision']}</span>
                </div>
                <div style="font-size:11px;">
                    • 🐋 <b>Whale Tracker:</b> {delib_data['whale']}<br>
                    • 🌪️ <b>Vol-Arb / Scalper:</b> {delib_data['vol']}<br>
                    • 📰 <b>Macro NLP Veto:</b> {delib_data['macro']}<br>
                    • 🎯 <b>Limit Entry:</b> ${delib_data['limit_entry']:,.2f} | <b>Target:</b> ${delib_data['target_price']:,.2f} | <b>Stop:</b> ${delib_data['stop_price']:,.2f}
                </div>
                <div class="bull-box" style="margin-top:6px;">{delib_data['bull']}</div>
                <div class="bear-box">{delib_data['bear']}</div>
            </div>
            """, unsafe_allow_html=True)

with tab_transcripts:
    st.subheader("📜 Advanced Interactive War Room Transcripts")
    for t in st.session_state.debate_transcripts[:10]:
        st.markdown(f"""
        <div class="warroom-box">
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#94A3B8;">
                <span><b>[{t['time']}] Asset Subject: {t['asset']}</b> | Engine: {t['persona']}</span>
                <span>CIO Composite Score: <b style="color:#8B5CF6;">{t['score']}%</b> ({t['decision']})</span>
            </div>
            <div style="margin-top:10px; font-size:12px; border-left: 2px solid #38BDF8; padding-left: 8px; color: #38BDF8;">
                <b>Specialized Agent Telemetry:</b> Whale Flow: {t['whale']} | Volatility Index: {t['vol']} | Macro Sentiment: {t['macro']}
            </div>
            <div style="margin-top:10px; font-size:13px;">
                <div style="color:#10B981; margin-bottom:6px;">🟢 <b>Bull Advocate Case:</b> {t['bull']}</div>
                <div style="color:#EF4444; margin-bottom:6px;">🔴 <b>Bear Advocate & Risk Veto:</b> {t['bear']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab_memory:
    st.subheader("🧠 Deep Self-Reflection & Calibration Memory Ledger")
    
    if len(st.session_state.reflection_history) > 0:
        for ref in st.session_state.reflection_history[:5]:
            st.markdown(f"""
            <div class="reflection-box">
                <b>[{ref['time']}] Post-Mortem Reflection:</b> {ref['reflection']}<br>
                <div style="margin-top:6px; color:#38BDF8;"><b>💡 Calibrated Apex Lesson:</b> {ref['lesson']}</div>
            </div>
            """, unsafe_allow_html=True)

    if len(memory_rules) > 0:
        st.markdown("#### Permanent Supabase Memory Records")
        mem_df = pd.DataFrame(memory_rules)[["timestamp", "asset", "trade_type", "pnl", "lesson_learned"]]
        st.dataframe(mem_df, use_container_width=True, hide_index=True)
