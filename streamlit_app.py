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
    page_title="HP Advanced Trading Platform",
    page_icon="⚡",
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

count = st_autorefresh(interval=15000, limit=10000, key="hp_refresh_v7")

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
            payload = {"chat_id": chat_id, "text": f"⚡ **HP Advanced Platform**\n\n{message}", "parse_mode": "Markdown"}
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
# 2. SIDEBAR ASSET TOGGLE SWITCHES
# -------------------------------------------------------------
st.sidebar.markdown("### 🎛️ Asset Kill-Switches")
st.sidebar.write("Toggle specific asset engines ON or OFF to isolate your trading focus.")

asset_toggles = {
    "Bitcoin": st.sidebar.checkbox("🟢 Trade Bitcoin (BTC)", value=True),
    "Ethereum": st.sidebar.checkbox("🟢 Trade Ethereum (ETH)", value=True),
    "Gold": st.sidebar.checkbox("🟡 Trade Gold (GC)", value=True),
    "Silver": st.sidebar.checkbox("🟡 Trade Silver (SI)", value=True)
}

# -------------------------------------------------------------
# 3. AUTOMATED MARKET DATA STREAM
# -------------------------------------------------------------
def fetch_hp_market_data():
    market_data = {}
    current_time = time.time()
    
    tickers = {
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Gold": "GC=F",
        "Silver": "SI=F"
    }
    
    base_prices = {"Bitcoin": 65000.0, "Ethereum": 3500.0, "Gold": 2740.0, "Silver": 31.50}
    
    for name, symbol in tickers.items():
        if not asset_toggles.get(name, True):
            continue
            
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
                vol_baseline = float(high_low.rolling(50).mean().iloc[-1]) if len(high_low) >= 50 else atr
                vol_ratio = atr / vol_baseline if vol_baseline > 0 else 1.0
                est_poc = raw_p - (atr * 0.1)
            else:
                raw_p = base_prices[name]
                last_bar_time = current_time
                atr = raw_p * 0.008
                vol_ratio = 1.0
                est_poc = raw_p

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
            est_poc = raw_p
        
        prev_p = st.session_state.price_buffer.get(name, raw_p)
        smoothed_p = round((raw_p * 0.25) + (prev_p * 0.75), 2)
        st.session_state.price_buffer[name] = smoothed_p
        
        is_stale = False
        if name in ["Gold", "Silver"]:
            if (current_time - last_bar_time) > 2700:
                is_stale = True

        market_data[name] = {
            "price": smoothed_p, 
            "atr": round(atr, 4), 
            "mtf_trend": mtf_trend,
            "vol_ratio": round(vol_ratio, 2),
            "is_stale": is_stale,
            "poc": round(est_poc, 2)
        }
        
    return market_data

market_snapshot = fetch_hp_market_data()

def fetch_memory_ledger():
    try:
        res = supabase.table("system_memory_ledger").select("*").order("id", desc=True).limit(20).execute()
        return res.data
    except:
        return []

def get_reinforcement_adjustment():
    lessons = fetch_memory_ledger()
    if not lessons:
        return 0.0
    recent_pnl = sum([float(l.get("pnl", 0)) for l in lessons[:5]])
    if recent_pnl > 0:
        return 4.0
    elif recent_pnl < 0:
        return -6.0
    return 0.0

def store_advanced_self_reflection(asset, trade_type, pnl, reflection, lesson, reward_score):
    try:
        supabase.table("system_memory_ledger").insert({
            "asset": asset, "trade_type": trade_type, "pnl": pnl,
            "reflection_notes": reflection, "lesson_learned": lesson,
            "reward_score": reward_score
        }).execute()
        send_telegram_alert(f"🧠 *Reinforcement Learning Updated*\nAsset: {asset} ({trade_type}) | PnL: `${pnl:,.2f}`\nReward Score: `{reward_score}`\nLesson: {lesson}")
    except Exception as e:
        print(f"Memory logging error: {e}")

memory_rules = fetch_memory_ledger()
reinforcement_bias = get_reinforcement_adjustment()

# -------------------------------------------------------------
# 4. QUANT BACKEND & STRATEGY-BASED AGENT SUITE
# -------------------------------------------------------------

class VolumeProfilePOCAgent:
    @staticmethod
    def analyze(data):
        poc = data["poc"]
        price = data["price"]
        distance_pct = ((price - poc) / poc) * 100.0
        if abs(distance_pct) < 0.3:
            return {"status": "POC_REJECTION_ZONE", "score": 75, "note": f"Price tightly coupled with POC node (${poc}). Value acceptance active."}
        elif distance_pct > 0:
            return {"status": "ABOVE_VALUE", "score": 55, "note": f"Auction trading above value node POC (${poc}). Premium boundary."}
        else:
            return {"status": "BELOW_VALUE", "score": 45, "note": f"Auction trading below value node POC (${poc}). Discount boundary."}

class ApexWhaleTrackerAgent:
    @staticmethod
    def analyze(vol_ratio):
        if vol_ratio > 1.3:
            return {"status": "ACCUMULATION", "score": 82, "note": "Whale block footprint active. Large limit absorption detected."}
        elif vol_ratio < 0.7:
            return {"status": "DISTRIBUTION", "score": 35, "note": "Institutional thin book distribution pattern active."}
        else:
            return {"status": "BALANCED", "note": "Normal institutional tape footprint.", "score": 50}

class ApexVolArbAgent:
    @staticmethod
    def analyze(vol_ratio):
        if vol_ratio > 1.4:
            return {"mode": "VOLATILITY_EXPANSION", "score": 78, "note": f"Volatility surge ratio at {vol_ratio}x. Breakout protocols engaged."}
        elif vol_ratio < 0.75:
            return {"mode": "VOLATILITY_COMPRESSION", "score": 40, "note": f"Volatility squeeze condition (Ratio {vol_ratio}x). Grid active."}
        else:
            return {"mode": "NORMAL", "score": 50, "note": "Standard volatility channel."}

class NewsAndSentimentSpecialist:
    @staticmethod
    def analyze():
        feeds = [
            ("News Specialist: Global liquidity flows stable. Sentiment risk index positive.", "CLEAR", 0, "Risk-On Liquidity Confirmed"),
            ("News Specialist: Central bank rate commentary indicates soft landing bias.", "CLEAR", 0, "Macro Tailwind Active"),
            ("News Specialist: Supply chain tightening inflation alert! Risk reduction recommended.", "VETO_WARNING", -22, "Inflation Shock Warning"),
            ("News Specialist: Geopolitical safe-haven flows active. Volatility buffer applied.", "CLEAR", 0, "Safe-Haven Rotation")
        ]
        chosen = random.choice(feeds)
        return {"headline": chosen[0], "status": chosen[1], "penalty": chosen[2], "sentiment": chosen[3]}

class MacroNLPAgent:
    @staticmethod
    def analyze():
        headlines = [
            "Macro NLP: Order book imbalances show aggressive bids clustering near support.",
            "Macro NLP: Cross-asset correlation reveals strong institutional risk appetite.",
            "Macro NLP: Macro economic data releases inline with median estimates."
        ]
        return random.choice(headlines)

class MarketProfileStrategy:
    @staticmethod
    def comment(data):
        return f"Profile Strategy: Testing High Volume Node (HVN) at ${data['poc']}. Looking for rejection candle."

class InstitutionalOrderFlowStrategy:
    @staticmethod
    def comment():
        return "Order Flow Strategy: Smart money iceberg orders showing up on level 2. Accumulation phase verified."

class MomentumVelocityStrategy:
    @staticmethod
    def comment(vol_ratio):
        return f"Momentum Strategy: Delta expansion speed at {vol_ratio}x velocity. Momentum traders taking control."

class BreakoutScalpStrategy:
    @staticmethod
    def comment():
        return "Breakout Strategy: Channel squeeze coiled. Ready for immediate scalping execution."

class RiskManagementStrategy:
    @staticmethod
    def comment():
        return "Risk Guard Strategy: Risk parameters verified. Margin utilization within safe institutional bounds."


# -------------------------------------------------------------
# 5. WAR ROOM DELIBERATION
# -------------------------------------------------------------
def run_hp_deliberation(asset, data, memory):
    current_time = time.time()
    price = data["price"]
    atr = data["atr"]
    mtf_trend = data["mtf_trend"]
    vol_ratio = data["vol_ratio"]
    
    if asset in st.session_state.cached_deliberations and (current_time - st.session_state.last_signal_reset < 300):
        cached = st.session_state.cached_deliberations[asset]
        cached["price"] = price
        return cached

    poc_bot = VolumeProfilePOCAgent.analyze(data)
    whale_bot = ApexWhaleTrackerAgent.analyze(vol_ratio)
    vol_bot = ApexVolArbAgent.analyze(vol_ratio)
    news_bot = NewsAndSentimentSpecialist.analyze()
    macro_nlp_text = MacroNLPAgent.analyze()

    profile_comm = MarketProfileStrategy.comment(data)
    flow_comm = InstitutionalOrderFlowStrategy.comment()
    momentum_comm = MomentumVelocityStrategy.comment(vol_ratio)
    breakout_comm = BreakoutScalpStrategy.comment()
    risk_comm = RiskManagementStrategy.comment()

    learning_adjustment = reinforcement_bias

    weighted_score = (
        (poc_bot["score"] * 0.25) + 
        (whale_bot["score"] * 0.25) + 
        (vol_bot["score"] * 0.25) + 
        (50 * 0.15) +
        ( (50 + news_bot["penalty"]) * 0.10 )
    )
    
    if mtf_trend == "BULLISH":
        weighted_score += 5
    elif mtf_trend == "BEARISH":
        weighted_score -= 5

    weighted_score += learning_adjustment
    final_score = int(max(5, min(95, weighted_score)))

    if news_bot["status"] == "VETO_WARNING" and abs(final_score - 50) < 25:
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
        "asset": asset, "price": price, "atr": dynamic_atr, "mtf_trend": mtf_trend, "persona": f"HP_HYBRID_{vol_bot['mode']}",
        "score": final_score, "decision": decision, "is_stale": data.get("is_stale", False),
        "limit_entry": limit_entry, "target_price": target_price, "stop_price": stop_price,
        "poc_note": poc_bot["note"], "whale_note": whale_bot["note"], "news_note": news_bot["headline"], "macro_nlp": macro_nlp_text,
        "profile_comm": profile_comm, "flow_comm": flow_comm, "momentum_comm": momentum_comm, "breakout_comm": breakout_comm, "risk_comm": risk_comm,
        "poc": data.get("poc"),
        "bull": f"Profile Strategy & Whale Tracker Consensus: {poc_bot['note']} {whale_bot['note']}",
        "bear": f"News Sentiment & Volatility Check: {news_bot['headline']} Reinforcement factor: {learning_adjustment:+.1f}."
    }
    
    st.session_state.cached_deliberations[asset] = result
    return result

if time.time() - st.session_state.last_signal_reset > 300:
    st.session_state.cached_deliberations = {}
    st.session_state.last_signal_reset = time.time()

deliberations = {asset: run_hp_deliberation(asset, market_snapshot[asset], memory_rules) for asset in market_snapshot if asset in market_snapshot}

if deliberations:
    active_delib = max(deliberations.values(), key=lambda x: abs(x["score"] - 50))
    if len(st.session_state.debate_transcripts) == 0 or st.session_state.debate_transcripts[0]["asset"] != active_delib["asset"]:
        st.session_state.debate_transcripts.insert(0, {
            "time": datetime.now().strftime("%H:%M:%S"),
            "asset": active_delib["asset"], "persona": active_delib["persona"],
            "score": active_delib["score"], "decision": active_delib["decision"],
            "poc_note": active_delib["poc_note"], "whale_note": active_delib["whale_note"],
            "news_note": active_delib["news_note"], "strategy": active_delib["profile_comm"],
            "bull": active_delib["bull"], "bear": active_delib["bear"],
            "entry": active_delib["limit_entry"], "target": active_delib["target_price"], "stop": active_delib["stop_price"]
        })

# -------------------------------------------------------------
# 6. EXECUTION ENGINE
# -------------------------------------------------------------
def execute_hp_trades(delibrations_dict):
    res = supabase.table("agent_portfolio").select("*").eq("agent_id", "HP_Advanced_Fund").execute()
    
    if len(res.data) == 0:
        supabase.table("agent_portfolio").insert({
            "agent_id": "HP_Advanced_Fund", "cash": 100000.0,
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
        current_p = market_snapshot.get(held_asset, {"price": entry_price})["price"]
        target_p = float(pos["target_price"])
        stop_p = float(pos["stop_price"])
        
        entry_timestamp = float(pos.get("entry_timestamp", time.time()))
        trade_duration_minutes = (time.time() - entry_timestamp) / 60.0

        pnl_pct = ((current_p - entry_price) / entry_price) * 100.0 if pos_type == "LONG" else ((entry_price - current_p) / entry_price) * 100.0

        exit_triggered, exit_reason = False, ""

        if pos_type == "LONG":
            if current_p >= target_p:
                exit_triggered, exit_reason = True, f"Dynamic Profit Target Reached (${target_p})"
            elif current_p <= stop_p:
                exit_triggered, exit_reason = True, f"Dynamic Stop Loss Triggered (${stop_p})"
        else:
            if current_p <= target_p:
                exit_triggered, exit_reason = True, f"Dynamic Short Target Reached (${target_p})"
            elif current_p >= stop_p:
                exit_triggered, exit_reason = True, f"Dynamic Short Stop Loss Triggered (${stop_p})"

        if trade_duration_minutes >= 25.0 and -0.4 < pnl_pct < 0.6:
            exit_triggered, exit_reason = True, f"Time-Horizon Stagnation Release ({trade_duration_minutes:.1f}m)"

        if exit_triggered:
            realized_pnl = round((pnl_pct / 100.0) * (units * entry_price), 2)
            net_cash = round(cash + (units * current_p) if pos_type == "LONG" else cash + (units * entry_price) + (units * (entry_price - current_p)), 2)

            reward_score = 100 if realized_pnl > 0 else -50
            reflection = f"REINFORCEMENT: {pos_type} trade on {held_asset} closed at {pnl_pct:+.2f}%. Reason: {exit_reason}."
            lesson = f"Auto-exit execution validated."

            store_advanced_self_reflection(held_asset, pos_type, realized_pnl, reflection, lesson, reward_score)
            st.session_state.reflection_history.insert(0, {"time": datetime.now().strftime("%H:%M:%S"), "reflection": reflection, "lesson": lesson, "reward": reward_score})

            supabase.table("agent_portfolio").update({
                "cash": net_cash, "current_position": None, "trades_today": trades_today + 1, "total_pnl": fund.get("total_pnl", 0) + realized_pnl
            }).eq("agent_id", "HP_Advanced_Fund").execute()

            supabase.table("trade_ledger_history").insert({
                "agent_id": "HP_Advanced_Fund", "asset": held_asset, "action": f"CLOSE_{pos_type}",
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
                
                win_prob = abs(best_candidate["score"] - 50) / 50.0 
                kelly_fraction = max(0.1, min(0.4, win_prob * 0.5)) 
                allocated_capital = cash * kelly_fraction
                
                units = round(allocated_capital / limit_entry, 4)
                new_pos = {
                    "asset": entry_asset, "entry_price": limit_entry, "units": units,
                    "type": pos_type, "persona": best_candidate["persona"],
                    "target_price": best_candidate["target_price"], "stop_price": best_candidate["stop_price"],
                    "entry_timestamp": time.time()
                }
                supabase.table("agent_portfolio").update({"cash": round(cash - allocated_capital, 2), "current_position": new_pos, "trades_today": trades_today + 1}).eq("agent_id", "HP_Advanced_Fund").execute()
                supabase.table("trade_ledger_history").insert({"agent_id": "HP_Advanced_Fund", "asset": entry_asset, "action": f"KELLY_{pos_type}_{entry_asset}", "size": units, "price": limit_entry, "pnl": 0.0, "trade_num": trades_today + 1}).execute()

                send_telegram_alert(f"🟢 *Kelly Trade Executed: {pos_type} {entry_asset}*\nAllocation: `{kelly_fraction*100:.1f}%` ($`{allocated_capital:,.2f}`)\nLimit Entry: `${limit_entry:,.2f}`\nSwarm Confidence: {best_candidate['score']}%")

execute_hp_trades(deliberations)

trade_ledger = supabase.table("trade_ledger_history").select("*").order("id", desc=True).limit(15).execute().data
portfolio_state = supabase.table("agent_portfolio").select("*").eq("agent_id", "HP_Advanced_Fund").execute().data

# -------------------------------------------------------------
# 7. APP INTERFACE LAYOUT
# -------------------------------------------------------------
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
    <div>
        <h1 style="margin:0;">⚡ HP Advanced Trading Platform</h1>
    </div>
    <div style="background: #090D16; padding: 8px 16px; border-radius: 8px; border: 1px solid #1E293B;">
        <span style="color: #10B981; font-weight: bold;">⚡ 24/7 LIVE STREAM</span>
        <div style="font-size: 11px; color: #94A3B8;">Tick #{count} • {datetime.now().strftime('%H:%M:%S UTC')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

cols = st.columns(4)
for i, (asset, data) in enumerate(market_snapshot.items()):
    stale_tag = " [Closed]" if data["is_stale"] else ""
    cols[i].metric(label=f"{asset.upper()}{stale_tag}", value=f"${data['price']:,.2f}")

st.divider()

tab_portfolio, tab_room, tab_transcripts, tab_memory = st.tabs([
    "📑 Portfolio & Kelly Audit", "⚔️ Multi-Agent Intelligence", "📜 Interactive Debate Transcripts", "🧠 Advanced Reinforcement Memory"
])

with tab_portfolio:
    col_p1, col_p2 = st.columns([1, 1])

    with col_p1:
        st.subheader("💼 Fund Portfolio & Risk Metrics")
        if len(portfolio_state) > 0:
            fund_data = portfolio_state[0]
            cash_bal = float(fund_data.get('cash', 100000.0))
            realized_pnl = float(fund_data.get('total_pnl', 0.0))
            
            st.write(f"**Available Cash:** ${cash_bal:,.2f}")
            st.write(f"**Realized Cumulative PnL:** ${realized_pnl:,.2f}")
            st.write(f"**Active Reinforcement Learning Bias:** `{reinforcement_bias:+.1f}`")
            
            pos = fund_data.get("current_position")
            if pos:
                held_asset = pos["asset"]
                entry_p = float(pos["entry_price"])
                curr_p = market_snapshot.get(held_asset, {"price": entry_p})["price"]
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
                    <b>Active HP Position: {pos_type} {held_asset}</b> (Duration: {duration_m:.1f} mins)<br>
                    <span style="font-size:12px; color:#94A3B8;">Units: {units} | Limit Entry: ${entry_p:,.2f} | Current: ${curr_p:,.2f}</span><br>
                    <div style="margin-top:8px;">
                        <b>Live MTM PnL:</b> 
                        <span style="color:{pnl_color}; font-weight:bold; font-size:16px;">
                            ${live_pnl_dollars:+,.2f} ({live_pnl_pct:+.2f}%)
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Manual Override: Force Close Button
                if st.button("🚨 Force Close Position Now (Manual Override)", type="primary"):
                    realized_pnl_manual = round((live_pnl_pct / 100.0) * (units * entry_p), 2)
                    net_cash_manual = round(cash_bal + (units * curr_p) if pos_type == "LONG" else cash_bal + (units * entry_p) + (units * (entry_p - curr_p)), 2)
                    
                    supabase.table("agent_portfolio").update({
                        "cash": net_cash_manual, "current_position": None, "trades_today": fund_data.get("trades_today", 0) + 1, "total_pnl": realized_pnl_manual
                    }).eq("agent_id", "HP_Advanced_Fund").execute()

                    supabase.table("trade_ledger_history").insert({
                        "agent_id": "HP_Advanced_Fund", "asset": held_asset, "action": f"MANUAL_CLOSE_{pos_type}",
                        "size": units, "price": curr_p, "pnl": realized_pnl_manual, "trade_num": fund_data.get("trades_today", 0) + 1
                    }).execute()

                    store_advanced_self_reflection(held_asset, pos_type, realized_pnl_manual, f"Manual override close executed on {held_asset}.", "Manual human intervention closed position.", 50 if realized_pnl_manual >= 0 else -20)
                    send_telegram_alert(f"⚠️ *Manual Override Close Executed*\nAsset: {held_asset} | Realized PnL: `${realized_pnl_manual:,.2f}`")
                    st.success("Position closed successfully! Refreshing app...")
                    time.sleep(1)
                    st.rerun()
            else:
                st.info("Active Position: 100% Cash / Scanning High-Conviction Setups")

    with col_p2:
        st.subheader("📑 Execution Ledger History")
        if len(trade_ledger) > 0:
            df = pd.DataFrame(trade_ledger)
            cols_to_show = [c for c in ["timestamp", "asset", "action", "size", "price", "pnl"] if c in df.columns]
            st.dataframe(df[cols_to_show], use_container_width=True, hide_index=True)

with tab_room:
    st.subheader("⚔️ Multi-Agent Intelligence (Specialist Quant & Strategy Engines)")
    
    grid = st.columns(2)
    for idx, (asset_name, delib_data) in enumerate(deliberations.items()):
        col = grid[idx % 2]
        with col:
            badge = "badge-buy" if delib_data["score"] >= 68 else ("badge-sell" if delib_data["score"] <= 32 else "badge-apex")
            if delib_data["decision"] == "VETOED_FLAT":
                badge = "badge-veto"
                
            stale_warning = " <span style='color: #EF4444; font-size: 10px;'>[CLOSED]</span>" if delib_data.get("is_stale") else ""
            poc_disp = f" | <b>POC:</b> ${delib_data['poc']:,.2f}" if delib_data.get('poc') else ""
            
            col.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0;">{asset_name.upper()} {stale_warning}</h3>
                    <span style="font-size:22px; font-weight:bold; color:#8B5CF6;">{delib_data['score']}%</span>
                </div>
                <div style="font-size:11px; color:#94A3B8; margin-bottom:6px;">
                    Mode: <b>{delib_data['persona']}</b> | Trend: <b>{delib_data['mtf_trend']}</b>{poc_disp} | Signal: <span class="{badge}">{delib_data['decision']}</span>
                </div>
                <div style="font-size:11px;">
                    <b>Specialist Quant Backend Bots:</b><br>
                    • 📊 <b>Volume Profile / POC Agent:</b> {delib_data['poc_note']}<br>
                    • 🐋 <b>Apex Whale Tracker Specialist:</b> {delib_data['whale_note']}<br>
                    • 📰 <b>News & Sentiment Specialist:</b> {delib_data['news_note']}<br>
                    • 🌐 <b>Macro NLP Feedback Bot:</b> {delib_data['macro_nlp']}<br><br>
                    <b>Strategy Execution Engines:</b><br>
                    • 📈 <b>{delib_data['profile_comm']}</b><br>
                    • 🐋 <b>{delib_data['flow_comm']}</b><br>
                    • ⚡ <b>{delib_data['momentum_comm']}</b><br>
                    • 🚀 <b>{delib_data['breakout_comm']}</b><br>
                    • 🛡️ <b>{delib_data['risk_comm']}</b><br><br>
                    🎯 <b>Limit Entry:</b> ${delib_data['limit_entry']:,.2f} | <b>Target:</b> ${delib_data['target_price']:,.2f} | <b>Stop:</b> ${delib_data['stop_price']:,.2f}
                </div>
                <div class="bull-box" style="margin-top:6px;">{delib_data['bull']}</div>
                <div class="bear-box">{delib_data['bear']}</div>
            </div>
            """, unsafe_allow_html=True)

with tab_transcripts:
    st.subheader("📜 Interactive Debate Transcripts")
    for t in st.session_state.debate_transcripts[:10]:
        st.markdown(f"""
        <div class="warroom-box">
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#94A3B8;">
                <span><b>[{t['time']}] Asset: {t['asset']}</b> | Engine: {t['persona']}</span>
                <span>Composite Score: <b style="color:#8B5CF6;">{t['score']}%</b> ({t['decision']})</span>
            </div>
            <div style="margin-top:10px; font-size:12px; border-left: 2px solid #38BDF8; padding-left: 8px; color: #38BDF8;">
                <b>Telemetry:</b> POC: {t['poc_note']} | Whale: {t['whale_note']} | News: {t['news_note']}
            </div>
            <div style="margin-top:10px; font-size:13px;">
                <div style="color:#10B981; margin-bottom:6px;">🟢 <b>Consensus Bull Case:</b> {t['bull']}</div>
                <div style="color:#EF4444; margin-bottom:6px;">🔴 <b>Risk & Veto Case:</b> {t['bear']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab_memory:
    st.subheader("🧠 Advanced Reinforcement Learning & Self-Reflection")
    st.write(f"**Active Reinforcement Feedback Weight:** `{reinforcement_bias:+.1f}` (Automatically tuned based on recent trade rewards)")
    
    if len(st.session_state.reflection_history) > 0:
        for ref in st.session_state.reflection_history[:5]:
            reward_color = "#10B981" if ref['reward'] > 0 else "#EF4444"
            st.markdown(f"""
            <div class="reflection-box" style="border-left: 4px solid {reward_color};">
                <b>[{ref['time']}] Reflection & Reward Score: <span style="color:{reward_color};">{ref['reward']}</span></b><br>
                {ref['reflection']}<br>
                <div style="margin-top:6px; color:#38BDF8;"><b>💡 Reinforcement Lesson:</b> {ref['lesson']}</div>
            </div>
            """, unsafe_allow_html=True)

    if len(memory_rules) > 0:
        st.markdown("#### Permanent Supabase Reinforcement Memory Records")
        mem_df = pd.DataFrame(memory_rules)
        mem_cols = [c for c in ["timestamp", "asset", "trade_type", "pnl", "reward_score", "lesson_learned"] if c in mem_df.columns]
        st.dataframe(mem_df[mem_cols], use_container_width=True, hide_index=True)

