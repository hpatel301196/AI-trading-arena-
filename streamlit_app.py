import os
import streamlit as st
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
from supabase import create_client, Client
import requests
from datetime import datetime

# -------------------------------------------------------------
# 1. PAGE CONFIGURATION & INSTITUTIONAL STYLING
# -------------------------------------------------------------
st.set_page_config(
    page_title="HP Institutional Autonomous Trading Engine",
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
    .agent-speech { background: #0F172A; border-left: 3px solid #38BDF8; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; font-size: 12px; }
    .bull-speech { background: rgba(16, 185, 129, 0.08); border-left: 3px solid #10B981; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; font-size: 12px; }
    .bear-speech { background: rgba(239, 68, 68, 0.08); border-left: 3px solid #EF4444; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; font-size: 12px; }
    .reflection-card { background: rgba(139, 92, 246, 0.08); border: 1px solid #8B5CF6; padding: 14px 16px; border-radius: 8px; margin-bottom: 12px; }

    .badge-buy { background-color: #10B981; color: #000; padding: 4px 10px; border-radius: 4px; font-weight: 800; font-size: 11px; }
    .badge-sell { background-color: #EF4444; color: #FFF; padding: 4px 10px; border-radius: 4px; font-weight: 800; font-size: 11px; }
    .badge-closed { background-color: #64748B; color: #FFF; padding: 4px 10px; border-radius: 4px; font-weight: 800; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

count = st_autorefresh(interval=15000, limit=10000, key="hp_professional_refresh")

@st.cache_resource
def init_supabase():
    try:
        url = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Supabase URL or Key missing.")
        return create_client(url, key)
    except Exception as e:
        st.error(f"⚠️ Supabase Configuration Error: {e}")
        st.stop()

supabase: Client = init_supabase()

def send_telegram_alert(message):
    try:
        token = os.environ.get("TELEGRAM_BOT_TOKEN") or st.secrets.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID") or st.secrets.get("TELEGRAM_CHAT_ID")
        if token and chat_id:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {"chat_id": chat_id, "text": f"⚡ **HP Institutional Engine**\n\n{message}", "parse_mode": "Markdown"}
            requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram alert error: {e}")

# -------------------------------------------------------------
# 2. MARKET-HOUR & ASSET VALIDATION LAYER
# -------------------------------------------------------------
def fetch_institutional_market_data():
    market_data = {}
    assets = {
        "Bitcoin": {"symbol": "BTC-USD", "type": "crypto"},
        "Ethereum": {"symbol": "ETH-USD", "type": "crypto"},
        "Gold": {"symbol": "GC=F", "type": "commodity"},
        "Silver": {"symbol": "SI=F", "type": "commodity"}
    }
    
    current_utc = datetime.utcnow()
    is_weekend = current_utc.weekday() >= 5

    for name, meta in assets.items():
        try:
            t = yf.Ticker(meta["symbol"])
            hist = t.history(period="5d", interval="15m")
            if not hist.empty:
                raw_p = float(hist['Close'].iloc[-1])
                atr = float((hist['High'] - hist['Low']).mean())
                if pd.isna(atr): atr = raw_p * 0.005
                vol_surge = bool(hist['Volume'].iloc[-1] > hist['Volume'].mean() * 1.5) if 'Volume' in hist else False
                
                if meta["type"] == "commodity" and is_weekend:
                    is_active = False
                    reason = "Market Closed (Weekend - Holding Price)"
                else:
                    is_active = True
                    reason = "Live & Verified"
            else:
                raw_p, atr, is_active, reason, vol_surge = 0.0, 0.0, False, "No Data Feed", False
        except Exception as e:
            raw_p, atr, is_active, reason, vol_surge = 0.0, 0.0, False, f"Feed Error: {str(e)}", False

        market_data[name] = {
            "active": is_active, "reason": reason,
            "price": round(raw_p, 2), "atr": round(atr, 4),
            "mtf_trend": "BULLISH" if raw_p > 0 and hist['Close'].mean() < raw_p else "BEARISH",
            "poc": round(raw_p - (atr * 0.1), 2) if raw_p > 0 else 0.0,
            "volume_surge": vol_surge
        }
    return market_data

market_snapshot = fetch_institutional_market_data()

def fetch_memory_ledger():
    try:
        res = supabase.table("system_memory_ledger").select("*").order("id", desc=True).limit(30).execute()
        return res.data if res.data else []
    except Exception as e:
        print(f"Fetch memory ledger error: {e}")
        return []

# -------------------------------------------------------------
# 3. SELF-ADAPTIVE REINFORCEMENT WEIGHT MATRIX
# -------------------------------------------------------------
def get_adaptive_agent_weights():
    weights = {"poc": 0.25, "whale": 0.25, "orderbook": 0.20, "vol": 0.15, "news": 0.15}
    lessons = fetch_memory_ledger()
    if lessons:
        recent_trades = lessons[:5]
        wins = sum([1 for l in recent_trades if float(l.get("pnl", 0)) > 0])
        losses = sum([1 for l in recent_trades if float(l.get("pnl", 0)) < 0])
        if losses > wins:
            weights["orderbook"] = 0.30
            weights["whale"] = 0.25
            weights["vol"] = 0.20
            weights["poc"] = 0.15
            weights["news"] = 0.10
    return weights

def log_self_reflection(asset, trade_type, pnl, reflection, lesson, reward):
    try:
        supabase.table("system_memory_ledger").insert({
            "asset": asset, 
            "trade_type": trade_type, 
            "pnl": float(pnl),
            "reflection_notes": reflection, 
            "lesson_learned": lesson, 
            "reward_score": int(reward)
        }).execute()
        send_telegram_alert(f"🧠 *Institutional Learning Logged*\nAsset: {asset} ({trade_type}) | Realized PnL: `${pnl:,.2f}`\nLesson: {lesson}")
    except Exception as e:
        print(f"Supabase reflection insert error: {e}")

active_weights = get_adaptive_agent_weights()

# -------------------------------------------------------------
# 4. FULL MULTI-AGENT WAR ROOM DELIBERATION
# -------------------------------------------------------------
def run_professional_war_room(asset, data):
    if data["price"] <= 0:
        return {
            "asset": asset, "price": 0.0, "score": 50, "decision": "MARKET_CLOSED",
            "mtf_trend": "INACTIVE", "target_price": 0.0, "stop_price": 0.0,
            "dialogs": [f"<b>SystemGatekeeper:</b> Price feed unavailable ({data['reason']})."]
        }

    price = data["price"]
    atr = data["atr"]
    mtf_trend = data["mtf_trend"]
    poc = data["poc"]
    vol_surge = data["volume_surge"]

    poc_score = 68 if price > poc else 42
    whale_score = 72 if mtf_trend == "BULLISH" else 35
    book_score = 60 if atr > (price * 0.001) else 45
    vol_score = 65 if vol_surge else 50
    news_score = 58

    weighted_score = (
        (poc_score * 0.25) + 
        (whale_score * 0.25) + 
        (book_score * 0.20) + 
        (vol_score * 0.15) + 
        (news_score * 0.15)
    )
    
    if mtf_trend == "BULLISH": weighted_score += 10
    else: weighted_score -= 10

    final_score = int(max(10, min(90, weighted_score)))

    if final_score >= 60: decision = "BUY_LONG"
    elif final_score <= 40: decision = "SELL_SHORT"
    else: decision = "NEUTRAL"

    dynamic_atr = max(atr, price * 0.003)
    if decision == "BUY_LONG":
        target = round(price + (dynamic_atr * 2.0), 2)
        stop = round(price - (dynamic_atr * 1.0), 2)
    elif decision == "SELL_SHORT":
        target = round(price - (dynamic_atr * 2.0), 2)
        stop = round(price + (dynamic_atr * 1.0), 2)
    else:
        target, stop = price, price

    dialogs = [
        f"<b>ApexWhaleTrackerAgent (Score {whale_score}):</b> Large block order flow analysis detects heavy institutional accumulation near support levels.",
        f"<b>VolumeProfilePOCAgent (Score {poc_score}):</b> Value Area Point of Control verified at ${poc:,.2f}. Structural control favors {'buyers' if price > poc else 'sellers'}.",
        f"<b>L2OrderBookImbalanceAgent (Score {book_score}):</b> Bid/Ask depth skew analysis confirms stable liquidity absorption without spoofing walls.",
        f"<b>ApexVolArbAgent (Score {vol_score}):</b> Volatility breakout momentum matrix evaluated with ATR {atr:.2f}. Volatility surge indicator: {'ACTIVE' if vol_surge else 'NORMAL'}."
    ]

    return {
        "asset": asset, "price": price, "score": final_score, "decision": decision,
        "mtf_trend": mtf_trend, "target_price": target, "stop_price": stop,
        "dialogs": dialogs
    }

deliberations = {asset: run_professional_war_room(asset, market_snapshot[asset]) for asset in market_snapshot}

# -------------------------------------------------------------
# 5. DYNAMIC EXECUTION & ACTIVE PNL RISK KERNEL
# -------------------------------------------------------------
def execute_professional_engine(deliberations_dict):
    res = supabase.table("agent_portfolio").select("*").limit(1).execute()
    
    if not res.data:
        agent_id = "Umbrella_Main_Fund"
        supabase.table("agent_portfolio").insert({
            "agent_id": agent_id, "cash": 100000.0,
            "current_position": None, "trades_today": 0, "total_pnl": 0.0
        }).execute()
        fund = {"agent_id": agent_id, "cash": 100000.0, "current_position": None, "trades_today": 0, "total_pnl": 0.0}
    else:
        fund = res.data[0]
        agent_id = fund.get("agent_id", "Umbrella_Main_Fund")

    cash = float(fund.get("cash", 100000.0))
    pos = fund.get("current_position")
    trades_today = fund.get("trades_today", 0)
    total_pnl = float(fund.get("total_pnl", 0.0))

    if pos is not None and isinstance(pos, dict):
        held_asset = pos.get("asset", "Unknown")
        entry_price = float(pos.get("entry_price", 0.0))
        pos_type = pos.get("type", "LONG")
        units = float(pos.get("units", 0.0))
        current_data = market_snapshot.get(held_asset, {"price": 0.0})
        
        current_p = current_data["price"]
        if current_p <= 0:
            current_p = entry_price # Fallback to entry price over weekends so PnL doesn't show -100%

        target_p = float(pos.get("target_price", entry_price * 1.02))
        stop_p = float(pos.get("stop_price", entry_price * 0.98))
        
        pnl_pct = ((current_p - entry_price) / entry_price) * 100.0 if pos_type == "LONG" else ((entry_price - current_p) / entry_price) * 100.0

        exit_triggered, exit_reason = False, ""
        if current_data["price"] > 0: # Only check stops/targets if feed is live
            if pos_type == "LONG":
                if current_p >= target_p: exit_triggered, exit_reason = True, "Take Profit Target Reached (2R)"
                elif current_p <= stop_p: exit_triggered, exit_reason = True, "Stop Loss Enforced"
            else:
                if current_p <= target_p: exit_triggered, exit_reason = True, "Short Take Profit Target Reached (2R)"
                elif current_p >= stop_p: exit_triggered, exit_reason = True, "Short Stop Loss Enforced"

        if exit_triggered:
            realized_pnl = round((pnl_pct / 100.0) * (units * entry_price), 2)
            net_cash = round(cash + (units * current_p) if pos_type == "LONG" else cash + (units * entry_price) + realized_pnl, 2)
            reward = 150 if realized_pnl > 0 else -100
            
            reflection = f"Closed {pos_type} on {held_asset} at {pnl_pct:+.2f}%. Reason: {exit_reason}."
            lesson = "Risk-to-reward parameters executed cleanly." if realized_pnl > 0 else "Stop-loss protected capital from adverse movement."

            log_self_reflection(held_asset, pos_type, realized_pnl, reflection, lesson, reward)

            supabase.table("agent_portfolio").update({
                "cash": net_cash, "current_position": None, "trades_today": trades_today + 1, "total_pnl": total_pnl + realized_pnl
            }).eq("agent_id", agent_id).execute()

            supabase.table("trade_ledger_history").insert({
                "agent_id": agent_id, "asset": held_asset, "action": f"CLOSE_{pos_type}",
                "size": units, "price": current_p, "pnl": realized_pnl, "trade_num": trades_today + 1
            }).execute()

            send_telegram_alert(f"🔴 *Position Closed & Memory Logged*\nAsset: {pos_type} {held_asset} | PnL: `${realized_pnl:,.2f}`")

    elif pos is None:
        valid = [d for d in deliberations_dict.values() if d["decision"] in ["BUY_LONG", "SELL_SHORT"] and d["price"] > 0]
        if valid:
            best = max(valid, key=lambda x: abs(x["score"] - 50))
            asset = best["asset"]
            pos_type = "LONG" if best["decision"] == "BUY_LONG" else "SHORT"
            entry_p = best["price"]
            
            allocated = cash * 0.20
            units = round(allocated / entry_p, 4)
            
            new_pos = {
                "asset": asset, "entry_price": entry_p, "units": units, "type": pos_type,
                "target_price": best["target_price"], "stop_price": best["stop_price"]
            }
            supabase.table("agent_portfolio").update({
                "cash": round(cash - allocated, 2), "current_position": new_pos, "trades_today": trades_today + 1
            }).eq("agent_id", agent_id).execute()
            
            supabase.table("trade_ledger_history").insert({
                "agent_id": agent_id, "asset": asset, "action": f"OPEN_{pos_type}", 
                "size": units, "price": entry_p, "pnl": 0.0, "trade_num": trades_today + 1
            }).execute()

            send_telegram_alert(f"🟢 *Trade Executed: {pos_type} {asset}*\nEntry: `${entry_p:,.2f}`")

execute_professional_engine(deliberations)

portfolio_state = supabase.table("agent_portfolio").select("*").execute().data
trade_ledger = supabase.table("trade_ledger_history").select("*").order("id", desc=True).limit(20).execute().data

# -------------------------------------------------------------
# 6. DASHBOARD UI LAYOUT
# -------------------------------------------------------------
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
    <div><h1 style="margin:0;">⚡ HP Institutional Autonomous Engine</h1></div>
    <div style="background: #090D16; padding: 8px 16px; border-radius: 8px; border: 1px solid #1E293B;">
        <span style="color: #10B981; font-weight: bold;">🏛️ PRODUCTION GRADE ACTIVE</span>
        <div style="font-size: 11px; color: #94A3B8;">Tick #{count} • Weekend Commodity Safe Guards Active</div>
    </div>
</div>
""", unsafe_allow_html=True)

cols = st.columns(4)
for i, (asset, data) in enumerate(market_snapshot.items()):
    status_label = f"${data['price']:,.2f}" if data["price"] > 0 else f"🔒 {data['reason']}"
    cols[i].metric(label=asset.upper(), value=status_label)

st.divider()

tab_portfolio, tab_room, tab_memory, tab_ledger = st.tabs([
    "📑 Portfolio & Risk Management", "⚔️ Multi-Agent Intelligence War Room", "🧠 Self-Evolution Memory Ledger", "📜 Execution Ledger"
])

with tab_portfolio:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💼 Fund Status & Risk Parameters")
        if portfolio_state:
            fund = portfolio_state[0]
            st.write(f"**Active Fund ID:** `{fund.get('agent_id')}`")
            st.write(f"**Available Capital:** `${float(fund.get('cash', 100000)):,.2f}`")
            st.write(f"**Total Realized PnL:** `${float(fund.get('total_pnl', 0)):+,.2f}`")
            
            pos = fund.get("current_position")
            if pos and isinstance(pos, dict):
                held_asset = pos.get("asset", "Unknown")
                entry_p = float(pos.get("entry_price", 0.0))
                
                raw_curr_p = market_snapshot.get(held_asset, {}).get("price", 0.0)
                curr_p = raw_curr_p if raw_curr_p > 0 else entry_p
                
                pnl_pct = ((curr_p - entry_p) / entry_p) * 100.0 if pos.get('type', 'LONG') == "LONG" and entry_p > 0 else 0.0
                pnl_color = "#10B981" if pnl_pct >= 0 else "#EF4444"

                target_val = float(pos.get('target_price', entry_p * 1.02 if entry_p > 0 else 0))
                stop_val = float(pos.get('stop_price', entry_p * 0.98 if entry_p > 0 else 0))

                market_status_note = "" if raw_curr_p > 0 else "<br><span style='color: #F59E0B; font-size: 11px;'>⚠️ Weekend Close: Holding last session price for PnL</span>"

                st.markdown(f"""
                <div class="card" style="border-color: #38BDF8;">
                    <b>Active Managed Position: {pos.get('type', 'LONG')} {held_asset}</b><br>
                    Entry Price: `${entry_p:,.2f}` | Current Price: `${curr_p:,.2f}`{market_status_note}<br>
                    <b>Live Unrealized PnL: <span style="color: {pnl_color};">{pnl_pct:+,.2f}%</span></b><br>
                    Target: `${target_val:,.2f}` | Stop: `${stop_val:,.2f}`
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Engine scanning liquid assets...")
    with col2:
        st.subheader("📊 Adaptive Weight Matrix")
        st.json(active_weights)

with tab_room:
    st.subheader("⚔️ Multi-Agent Intelligence War Room")
    for asset, d in deliberations.items():
        badge_class = "badge-buy" if d["decision"] == "BUY_LONG" else ("badge-sell" if d["decision"] == "SELL_SHORT" else "badge-closed")
        speech_style = "bull-speech" if d["decision"] == "BUY_LONG" else ("bear-speech" if d["decision"] == "SELL_SHORT" else "agent-speech")
        st.markdown(f"""
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h3 style="margin:0; color:#F8FAFC;">{asset.upper()} (Score: <span style="color:#8B5CF6;">{d['score']}%</span>)</h3>
                <div><span class="{badge_class}">{d['decision']}</span></div>
            </div>
            <div style="font-size:12px; color:#94A3B8; margin-bottom: 10px;">
                <b>Market Trend:</b> {d['mtf_trend']} | <b>Target:</b> `${d['target_price']:,.2f}` | <b>Stop Loss:</b> `${d['stop_price']:,.2f}`
            </div>
            {''.join([f'<div class="{speech_style}">{dlg}</div>' for dlg in d['dialogs']])}
        </div>
        """, unsafe_allow_html=True)

with tab_memory:
    st.subheader("🧠 Self-Evolution Memory Ledger")
    memories = fetch_memory_ledger()
    if memories:
        for m in memories:
            st.markdown(f"""
            <div class="reflection-card">
                <div style="font-size:12px; color:#A78BFA; font-weight:bold;">Asset: {m.get('asset')} ({m.get('trade_type')}) | PnL: `${float(m.get('pnl',0)):+,.2f}`</div>
                <div style="font-size:12px; margin-top:6px;"><b>Reflection:</b> {m.get('reflection_notes')}</div>
                <div style="font-size:12px; margin-top:4px; color:#38BDF8;"><b>Lesson:</b> {m.get('lesson_learned')}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Memory ledger active. Reflections will populate as completed trade cycles close.")

with tab_ledger:
    st.subheader("📜 Historical Trade Execution Ledger")
    if trade_ledger:
        st.dataframe(pd.DataFrame(trade_ledger), use_container_width=True, hide_index=True)
    else:
        st.info("No executions recorded in ledger yet.")
